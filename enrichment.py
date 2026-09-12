"""External metadata enrichment: OpenLibrary first, iTunes Books as fallback.

OpenLibrary provides canonical work identity and (sometimes) a description.
The keyless iTunes Search API fills the gaps with publisher blurbs and cover
art.  Both are best-effort: any failure degrades to "no data", never an error.
"""

import html
import re
from difflib import SequenceMatcher

import requests

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"
OPENLIBRARY_WORK_URL = "https://openlibrary.org{key}.json"
REQUEST_TIMEOUT = 8

# Below this length an OpenLibrary description is treated as a stub (often a
# single sentence) and iTunes is preferred when it has a fuller blurb.
MIN_OPENLIBRARY_DESCRIPTION = 250

# iTunes returns artworkUrl100; swap the size token for a larger render.
_ARTWORK_SIZE_TOKEN = re.compile(r"\d+x\d+bb")


def clean_html(text):
    """Turn an iTunes blurb (HTML-escaped, tag-laden) into plain text."""
    if not text:
        return None
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() or None


def _normalize(value):
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _title_matches(query, candidate):
    a, b = _normalize(query), _normalize(candidate)
    if not a or not b:
        return False
    if a in b or b in a:
        return True
    return SequenceMatcher(None, a, b).ratio() >= 0.75


def _author_matches(query, candidate):
    """True when any of the query's authors appears in the candidate's."""
    if not query:
        return True
    query_norm = _normalize(query)
    for part in re.split(r"[,/&]| and ", candidate or ""):
        part_norm = _normalize(part)
        if part_norm and (part_norm in query_norm or query_norm in part_norm):
            return True
    return False


def _fetch_openlibrary_description(openlibrary_key):
    try:
        response = requests.get(
            OPENLIBRARY_WORK_URL.format(key=openlibrary_key), timeout=REQUEST_TIMEOUT
        )
        if response.status_code != 200:
            return None
        description = response.json().get("description")
        if not description:
            return None
        text = description if isinstance(description, str) else description.get("value")
        return text.strip() if text and text.strip() else None
    except (requests.RequestException, ValueError):
        return None


def _search_itunes(title, author):
    try:
        response = requests.get(
            ITUNES_SEARCH_URL,
            params={
                "term": f"{title} {author or ''}".strip(),
                "entity": "ebook",
                "limit": 8,
                "country": "US",
            },
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            return []
        return response.json().get("results", [])
    except (requests.RequestException, ValueError):
        return []


def _best_itunes_match(results, title, author):
    """First result whose title and author plausibly match the book.

    iTunes is product/edition level and surfaces "Summary of ..." knockoffs and
    foreign editions, so never trust the first hit blindly.
    """
    for result in results:
        if _title_matches(title, result.get("trackName")) and _author_matches(
            author, result.get("artistName")
        ):
            artwork = result.get("artworkUrl100")
            if artwork:
                artwork = _ARTWORK_SIZE_TOKEN.sub("600x600bb", artwork)
            description = clean_html(result.get("description"))
            if description or artwork:
                return {"description": description, "artwork": artwork}
    return None


def enrich(title, author="", openlibrary_key=None, want_cover=False):
    """Resolve the best available description, and optionally a cover candidate.

    Description: OpenLibrary when it is substantial, otherwise an iTunes blurb.
    Cover: an iTunes artwork URL, only when explicitly requested and only as a
    candidate for the client to preview/save.
    """
    description = None
    description_source = None

    openlibrary_description = None
    if openlibrary_key and openlibrary_key.startswith("/works/"):
        openlibrary_description = _fetch_openlibrary_description(openlibrary_key)
    if openlibrary_description:
        description, description_source = openlibrary_description, "openlibrary"

    needs_description = (
        not openlibrary_description
        or len(openlibrary_description) < MIN_OPENLIBRARY_DESCRIPTION
    )

    itunes_match = None
    if (needs_description or want_cover) and title:
        itunes_match = _best_itunes_match(
            _search_itunes(title, author), title, author
        )

    if needs_description and itunes_match and itunes_match["description"]:
        description, description_source = itunes_match["description"], "itunes"

    cover_url = None
    cover_source = None
    if want_cover and itunes_match and itunes_match["artwork"]:
        cover_url, cover_source = itunes_match["artwork"], "itunes"

    return {
        "description": description,
        "description_source": description_source,
        "cover_url": cover_url,
        "cover_source": cover_source,
    }
