// Book Tracker JavaScript
console.log("Book Tracker loaded successfully!");

let selectedBook = null;
let selectedRating = 0;
let isManualEntry = false;
let isEditMode = false;
let currentBookId = null;
let lastSearchResults = []; // Store last search results

// Rating descriptions
const ratingDescriptions = {
  0.5: "One of the worst I've read",
  1: "I hated this book",
  1.5: "Occasional sections that were enjoyable",
  2: "Boring, hard to finish; wouldn't recommend",
  2.5: "Some good parts",
  3: "Average; I liked it okay",
  3.5: "Better than average, but not great",
  4: "Very good & well written; I enjoyed it",
  4.5: "Great writing and plot",
  5: "Amazing; I couldn't put it down",
};

const searchInput = document.getElementById("bookSearch");
const searchForm = document.getElementById("searchForm");
const resultsContainer = document.getElementById("searchResults");
const booksListContainer = document.getElementById("booksList");
const messageArea = document.getElementById("messageArea");

const searchModal = document.getElementById("searchModal");
const searchModalClose = document.getElementById("searchModalClose");
const addBookBtn = document.getElementById("addBookBtn");
const searchByTitleBtn = document.getElementById("searchByTitleBtn");
const manualAddBtnModal = document.getElementById("manualAddBtnModal");
const searchModalSearch = document.getElementById("searchModalSearch");
const searchModalOptions = document.querySelector(".search-modal-options");

const modal = document.getElementById("addBookModal");
const modalClose = document.getElementById("modalClose");
const modalCancel = document.getElementById("modalCancel");
const modalSave = document.getElementById("modalSave");
const modalDelete = document.getElementById("modalDelete");
const starRating = document.getElementById("starRating");

const filterSearch = document.getElementById("filterSearch");
const filterStatus = document.getElementById("filterStatus");

let allBooks = []; // Store all books for filtering
let currentOffset = 0;
let isLoading = false;
let hasMore = true;
let currentSearchQuery = "";
let currentStatusFilter = "";

loadBooks();
initModal();
initSearchModal();
initFilters();
initInfiniteScroll();

function initSearchModal() {
  if (addBookBtn) {
    addBookBtn.addEventListener("click", openSearchModal);
  }

  if (searchModalClose) {
    searchModalClose.addEventListener("click", closeSearchModal);
  }

  if (searchByTitleBtn) {
    searchByTitleBtn.addEventListener("click", showSearchInput);
  }

  if (manualAddBtnModal) {
    manualAddBtnModal.addEventListener("click", () => {
      closeSearchModal();
      openManualEntryModal();
    });
  }

  searchModal.addEventListener("click", (e) => {
    if (e.target === searchModal) {
      closeSearchModal();
    }
  });
}

function openSearchModal() {
  searchModalOptions.style.display = "flex";
  searchModalSearch.style.display = "none";
  searchInput.value = "";
  resultsContainer.innerHTML = "";
  searchModal.classList.add("show");
  document.body.style.overflow = "hidden";
}

function closeSearchModal() {
  searchModal.classList.remove("show");
  document.body.style.overflow = "";
  searchModalOptions.style.display = "flex";
  searchModalSearch.style.display = "none";
  searchInput.value = "";
  resultsContainer.innerHTML = "";
}

function showSearchInput() {
  searchModalOptions.style.display = "none";
  searchModalSearch.style.display = "block";
  searchInput.focus();
}

if (searchForm) {
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = searchInput.value.trim();

    if (query.length < 2) {
      resultsContainer.innerHTML =
        '<div class="search-message">Please enter at least 2 characters</div>';
      return;
    }

    searchBooks(query);
  });
}

async function searchBooks(query) {
  resultsContainer.innerHTML = '<div class="search-loading">Searching...</div>';

  try {
    const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();

    if (data.docs && data.docs.length > 0) {
      displayResults(data.docs);
    } else {
      displayNoResults();
    }
  } catch (error) {
    console.error("Search error:", error);
    displayError();
  }
}

function displayResults(books) {
  lastSearchResults = books; // Store the search results
  resultsContainer.innerHTML = "";

  books.forEach((book) => {
    const resultItem = createResultItem(book);
    resultsContainer.appendChild(resultItem);
  });
}

function createResultItem(book) {
  const div = document.createElement("div");
  div.className = "search-result-item";

  const coverUrl = book.cover_i
    ? `https://covers.openlibrary.org/b/id/${book.cover_i}-S.jpg`
    : "/static/images/no-cover.svg";

  const authors = book.author_name
    ? book.author_name.join(", ")
    : "Unknown Author";
  const year = book.first_publish_year ? `(${book.first_publish_year})` : "";

  div.innerHTML = `
        <div class="book-cover-thumb">
            <img src="${coverUrl}" alt="${book.title}" onerror="this.src='/static/images/no-cover.svg'">
        </div>
        <div class="book-info">
            <div class="book-title">${book.title}</div>
            <div class="book-author">${authors} ${year}</div>
        </div>
    `;

  div.addEventListener("click", () => {
    selectBook(book);
  });

  return div;
}

function selectBook(book) {
  console.log("Selected book:", book);
  selectedBook = book;
  closeSearchModal();
  openModal(book);
}

function displayNoResults() {
  resultsContainer.innerHTML =
    '<div class="search-message">No books found</div>';
}

function displayError() {
  resultsContainer.innerHTML =
    '<div class="search-error">Error searching books. Please try again.</div>';
}

function showMessage(text, type = "success") {
  messageArea.innerHTML = `<div class="message ${type}">${text}</div>`;
  setTimeout(() => {
    messageArea.innerHTML = "";
  }, 5000);
}

async function loadBooks(reset = true) {
  if (isLoading) return;
  if (!hasMore && !reset) return;

  isLoading = true;

  if (reset) {
    currentOffset = 0;
    allBooks = [];
    booksListContainer.innerHTML =
      '<div class="loading">Loading your books...</div>';
  } else {
    // Show loading indicator at bottom
    const loadingDiv = document.createElement("div");
    loadingDiv.className = "loading";
    loadingDiv.id = "loadingMore";
    loadingDiv.textContent = "Loading more books...";
    booksListContainer.appendChild(loadingDiv);
  }

  try {
    const params = new URLSearchParams({
      limit: "20",
      offset: currentOffset.toString(),
    });

    if (currentSearchQuery) {
      params.append("search", currentSearchQuery);
    }
    if (currentStatusFilter) {
      params.append("status", currentStatusFilter);
    }

    const response = await fetch(`/api/books?${params}`);
    const data = await response.json();

    // Remove loading indicator
    const loadingMore = document.getElementById("loadingMore");
    if (loadingMore) {
      loadingMore.remove();
    }

    if (data.books && data.books.length > 0) {
      allBooks = reset ? data.books : [...allBooks, ...data.books];
      hasMore = data.has_more;
      currentOffset = data.offset + data.books.length;

      if (reset) {
        displayBooks(allBooks);
      } else {
        // Append new books to existing list
        data.books.forEach((book) => {
          const bookCard = createBookCard(book);
          booksListContainer.appendChild(bookCard);
        });
      }
    } else if (reset) {
      allBooks = [];
      hasMore = false;
      displayEmptyState();
    } else {
      hasMore = false;
    }
  } catch (error) {
    console.error("Error loading books:", error);
    const loadingMore = document.getElementById("loadingMore");
    if (loadingMore) {
      loadingMore.remove();
    }
    if (reset) {
      booksListContainer.innerHTML =
        '<div class="loading">Error loading books. Please refresh the page.</div>';
    }
  } finally {
    isLoading = false;
  }
}

function displayBooks(books) {
  booksListContainer.innerHTML = "";

  books.forEach((book) => {
    const bookCard = createBookCard(book);
    booksListContainer.appendChild(bookCard);
  });
}

function createBookCard(book) {
  const div = document.createElement("div");
  div.className = "book-card clickable";

  const coverUrl = book.cover_id
    ? `https://covers.openlibrary.org/b/id/${book.cover_id}-M.jpg`
    : "/static/images/no-cover.svg";

  const author = book.author_name || "Unknown Author";
  const year = book.first_publish_year ? book.first_publish_year : "";

  const statusLabel = getStatusLabel(book.status);
  const ratingStars = getRatingStars(book.rating);

  const metaParts = [];
  if (year) metaParts.push(`<span class="book-card-year">${year}</span>`);
  if (book.status)
    metaParts.push(
      `<span class="book-card-status" data-status="${book.status}">${statusLabel}</span>`,
    );
  if (book.rating) {
    const ratingDescription = ratingDescriptions[book.rating] || "";
    metaParts.push(
      `<span class="book-card-rating" title="${book.rating} stars - ${ratingDescription}">${ratingStars}</span>`,
    );
  }

  const dateAdded = book.added_at ? formatDate(book.added_at) : "";

  div.innerHTML = `
    <div class="book-card-cover">
      <img src="${coverUrl}" alt="${book.title}" onerror="this.src='/static/images/no-cover.svg'">
    </div>
    <div class="book-card-info">
      <div class="book-card-title">${book.title}</div>
      <div class="book-card-author">${author}</div>
      ${metaParts.length > 0 ? `<div class="book-card-meta">${metaParts.join("")}</div>` : ""}
    </div>
    ${dateAdded ? `<div class="book-card-date">Added ${dateAdded}</div>` : ""}
  `;

  div.addEventListener("click", () => openEditModal(book));

  return div;
}

function getStatusLabel(status) {
  const statusMap = {
    want_to_read: "Want to read",
    reading: "Currently reading",
    finished: "Finished",
    did_not_finish: "Didn't finish",
  };
  return statusMap[status] || status;
}

function formatDate(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffTime = Math.abs(now - date);
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 0) {
    return "today";
  } else if (diffDays === 1) {
    return "yesterday";
  } else if (diffDays < 7) {
    return `${diffDays} days ago`;
  } else if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} week${weeks > 1 ? "s" : ""} ago`;
  } else if (diffDays < 365) {
    const months = Math.floor(diffDays / 30);
    return `${months} month${months > 1 ? "s" : ""} ago`;
  } else {
    const years = Math.floor(diffDays / 365);
    return `${years} year${years > 1 ? "s" : ""} ago`;
  }
}

function getRatingStars(rating) {
  if (!rating) return "";

  let stars = "";
  const fullStars = Math.floor(rating);
  const hasHalfStar = rating % 1 !== 0;

  for (let i = 0; i < fullStars; i++) {
    stars += "★";
  }
  if (hasHalfStar) {
    stars += "½";
  }

  return stars;
}

async function deleteBook(bookId) {
  if (
    !confirm("Are you sure you want to remove this book from your library?")
  ) {
    return;
  }

  try {
    const response = await fetch(`/api/books/${bookId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      showMessage("Book removed from your library", "success");
      loadBooks();
    } else {
      showMessage("Error removing book", "error");
    }
  } catch (error) {
    console.error("Error deleting book:", error);
    showMessage("Error removing book. Please try again.", "error");
  }
}

function displayEmptyState() {
  booksListContainer.innerHTML = `
    <div class="empty-state">
      <p>No books in your library yet</p>
      <small>Search for a book above to get started</small>
    </div>
  `;
}

// Modal Functions
function initModal() {
  modalClose.addEventListener("click", () => {
    if (isEditMode) {
      closeModal();
    } else {
      returnToSearch();
    }
  });

  modalCancel.addEventListener("click", () => {
    if (isEditMode) {
      closeModal();
    } else {
      returnToSearch();
    }
  });

  modalSave.addEventListener("click", saveOrUpdateBook);
  modalDelete.addEventListener("click", deleteBookFromModal);

  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      if (isEditMode) {
        closeModal();
      } else {
        returnToSearch();
      }
    }
  });

  initStarRating();
}

function openModal(book) {
  isManualEntry = false;
  isEditMode = false;

  const coverUrl = book.cover_i
    ? `https://covers.openlibrary.org/b/id/${book.cover_i}-M.jpg`
    : "/static/images/no-cover.svg";

  const authors = book.author_name
    ? book.author_name.join(", ")
    : "Unknown Author";
  const year = book.first_publish_year ? book.first_publish_year : "";

  document.getElementById("modalCover").src = coverUrl;
  document.getElementById("modalTitle").value = book.title || "";
  document.getElementById("modalAuthor").value = authors || "";
  document.getElementById("modalYear").value = year || "";

  // Show/hide date added (only for editing existing books)
  document.getElementById("modalDateAdded").style.display = "none";

  document.getElementById("modalBookInfo").style.display = "flex";

  document.getElementById("bookStatus").value = "";
  selectedRating = 0;
  updateStarDisplay();

  modalSave.textContent = "Add to Library";
  modalDelete.style.display = "none";

  // Fetch and display summary if book has key
  if (book.key) {
    fetchBookSummary(book.key);
  } else {
    document.getElementById("modalSummary").style.display = "none";
  }

  modal.classList.add("show");
  document.body.style.overflow = "hidden";
}

function openManualEntryModal() {
  isManualEntry = true;
  isEditMode = false;
  selectedBook = null;

  document.getElementById("modalCover").src = "/static/images/no-cover.svg";
  document.getElementById("modalTitle").value = "";
  document.getElementById("modalAuthor").value = "";
  document.getElementById("modalYear").value = "";

  document.getElementById("modalDateAdded").style.display = "none";
  document.getElementById("modalBookInfo").style.display = "flex";

  document.getElementById("bookStatus").value = "";
  selectedRating = 0;
  updateStarDisplay();

  modalSave.textContent = "Add to Library";
  modalDelete.style.display = "none";

  document.getElementById("modalSummary").style.display = "none";

  modal.classList.add("show");
  document.body.style.overflow = "hidden";
}

function openEditModal(book) {
  isEditMode = true;
  isManualEntry = false;
  currentBookId = book.id;
  selectedBook = book;

  const coverUrl = book.cover_id
    ? `https://covers.openlibrary.org/b/id/${book.cover_id}-M.jpg`
    : "/static/images/no-cover.svg";

  const authors = book.author_name || "Unknown Author";
  const year = book.first_publish_year ? book.first_publish_year : "";

  document.getElementById("modalCover").src = coverUrl;
  document.getElementById("modalTitle").value = book.title || "";
  document.getElementById("modalAuthor").value = authors || "";
  document.getElementById("modalYear").value = year || "";

  // Show date added for existing books
  const dateAdded = book.added_at ? formatDate(book.added_at) : "";
  const dateAddedElement = document.getElementById("modalDateAdded");
  if (dateAdded) {
    dateAddedElement.textContent = `Added ${dateAdded}`;
    dateAddedElement.style.display = "block";
  } else {
    dateAddedElement.style.display = "none";
  }

  document.getElementById("modalBookInfo").style.display = "flex";

  document.getElementById("bookStatus").value = book.status || "want_to_read";
  selectedRating = book.rating || 0;
  updateStarDisplay();

  modalSave.textContent = "Update Book";
  modalDelete.style.display = "block";

  // Fetch and display summary if book has openlibrary_key
  if (book.openlibrary_key && !book.openlibrary_key.startsWith("manual_")) {
    fetchBookSummary(book.openlibrary_key);
  } else {
    document.getElementById("modalSummary").style.display = "none";
  }

  modal.classList.add("show");
  document.body.style.overflow = "hidden";
}

function closeModal() {
  modal.classList.remove("show");
  document.body.style.overflow = "";
  selectedBook = null;
  selectedRating = 0;
  isManualEntry = false;
  isEditMode = false;
  currentBookId = null;
  modalSave.textContent = "Add to Library";
  modalDelete.style.display = "none";
  document.getElementById("modalSummary").style.display = "none";
}

function returnToSearch() {
  closeModal();

  // If we have search results, reopen the search modal and show them
  if (lastSearchResults.length > 0) {
    searchModalOptions.style.display = "none";
    searchModalSearch.style.display = "block";
    displayResults(lastSearchResults);
    searchModal.classList.add("show");
    document.body.style.overflow = "hidden";
  }
}

function initStarRating() {
  const stars = starRating.querySelectorAll(".star");

  stars.forEach((star) => {
    star.addEventListener("click", () => {
      selectedRating = parseFloat(star.dataset.rating);
      updateStarDisplay();
    });

    star.addEventListener("mouseenter", () => {
      const rating = parseFloat(star.dataset.rating);
      highlightStars(rating);
    });
  });

  starRating.addEventListener("mouseleave", () => {
    updateStarDisplay();
  });
}

function highlightStars(rating) {
  const stars = starRating.querySelectorAll(".star");
  stars.forEach((star) => {
    const starRating = parseFloat(star.dataset.rating);
    star.classList.remove("active", "half");

    if (starRating <= rating) {
      if (starRating % 1 === 0.5 && starRating === rating) {
        star.classList.add("half");
      } else {
        star.textContent = "★";
        star.classList.add("active");
      }
    } else {
      star.textContent = "☆";
    }
  });

  // Update rating display with description
  const ratingDisplay = document.getElementById("ratingDisplay");
  if (rating === 0) {
    ratingDisplay.textContent = "No rating";
  } else {
    const description = ratingDescriptions[rating] || "";
    ratingDisplay.textContent = `${rating} star${rating !== 1 ? "s" : ""} - ${description}`;
  }
}

function updateStarDisplay() {
  highlightStars(selectedRating);
}

async function saveOrUpdateBook() {
  if (isEditMode) {
    await updateBook();
  } else {
    await saveBook();
  }
}

async function saveBook() {
  const status = document.getElementById("bookStatus").value;
  const rating = selectedRating;

  const title = document.getElementById("modalTitle").value.trim();
  const author = document.getElementById("modalAuthor").value.trim();
  const year = document.getElementById("modalYear").value.trim();

  if (!title) {
    showMessage("Please enter a book title", "error");
    return;
  }

  if (!status) {
    showMessage("Please select a reading status", "error");
    return;
  }

  let bookData;

  if (isManualEntry || !selectedBook) {
    bookData = {
      title: title,
      author_name: author,
      first_publish_year: year ? parseInt(year) : null,
      status: status,
      rating: rating,
      manual: true,
    };
  } else {
    bookData = {
      ...selectedBook,
      title: title,
      author_name: author,
      first_publish_year: year ? parseInt(year) : null,
      status: status,
      rating: rating,
    };
  }

  try {
    const response = await fetch("/api/books", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(bookData),
    });

    const data = await response.json();

    if (response.ok) {
      showMessage("Book added to your library!", "success");
      searchInput.value = "";
      closeModal();
      loadBooks();
    } else if (response.status === 409) {
      showMessage("This book is already in your library", "error");
      closeModal();
    } else {
      showMessage(data.error || "Error adding book", "error");
    }
  } catch (error) {
    console.error("Error saving book:", error);
    showMessage("Error adding book. Please try again.", "error");
  }
}

async function updateBook() {
  const status = document.getElementById("bookStatus").value;
  const rating = selectedRating;

  try {
    const response = await fetch(`/api/books/${currentBookId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        status: status,
        rating: rating,
      }),
    });

    const data = await response.json();

    if (response.ok) {
      showMessage("Book updated successfully!", "success");
      closeModal();
      loadBooks();
    } else {
      showMessage(data.error || "Error updating book", "error");
    }
  } catch (error) {
    console.error("Error updating book:", error);
    showMessage("Error updating book. Please try again.", "error");
  }
}

async function deleteBookFromModal() {
  if (!currentBookId) return;

  if (
    !confirm("Are you sure you want to remove this book from your library?")
  ) {
    return;
  }

  try {
    const response = await fetch(`/api/books/${currentBookId}`, {
      method: "DELETE",
    });

    if (response.ok) {
      showMessage("Book removed from your library", "success");
      closeModal();
      loadBooks();
    } else {
      showMessage("Error removing book", "error");
    }
  } catch (error) {
    console.error("Error deleting book:", error);
    showMessage("Error removing book. Please try again.", "error");
  }
}

async function fetchBookSummary(openlibraryKey) {
  const summarySection = document.getElementById("modalSummary");
  const summaryContent = document.getElementById("summaryContent");

  summarySection.style.display = "block";
  summaryContent.innerHTML =
    '<div class="loading-summary">Loading summary...</div>';

  try {
    // Extract work ID from key (e.g., "/works/OL45804W" -> "OL45804W")
    const workId = openlibraryKey.split("/").pop();
    const response = await fetch(
      `https://openlibrary.org/works/${workId}.json`,
    );

    if (!response.ok) {
      throw new Error("Failed to fetch summary");
    }

    const data = await response.json();

    if (data.description) {
      const description =
        typeof data.description === "string"
          ? data.description
          : data.description.value;
      summaryContent.innerHTML = `<p>${description}</p>`;
    } else {
      summaryContent.innerHTML =
        '<p class="no-summary">No summary available for this book.</p>';
    }
  } catch (error) {
    console.error("Error fetching summary:", error);
    summaryContent.innerHTML =
      '<p class="no-summary">Could not load summary.</p>';
  }
}

// Filter Functions
function initFilters() {
  if (filterSearch) {
    let filterDebounceTimer;
    filterSearch.addEventListener("input", () => {
      clearTimeout(filterDebounceTimer);
      filterDebounceTimer = setTimeout(() => {
        applyFilters();
      }, 300);
    });
  }

  if (filterStatus) {
    filterStatus.addEventListener("change", applyFilters);
  }
}

function applyFilters() {
  const searchQuery = filterSearch ? filterSearch.value.trim() : "";
  const statusFilter = filterStatus ? filterStatus.value : "";

  // Update current filter state
  currentSearchQuery = searchQuery;
  currentStatusFilter = statusFilter;

  // Reset and reload with new filters
  hasMore = true;
  loadBooks(true);
}

function displayNoMatchingBooks() {
  booksListContainer.innerHTML = `
    <div class="empty-state">
      <p>No books match your filters</p>
      <small>Try adjusting your search or filters</small>
    </div>
  `;
}

// Infinite scroll implementation
function initInfiniteScroll() {
  const booksContainer = booksListContainer;

  // Use Intersection Observer for better performance
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !isLoading && hasMore) {
          loadBooks(false);
        }
      });
    },
    {
      root: null,
      rootMargin: "200px", // Load more books when 200px from bottom
      threshold: 0.1,
    },
  );

  // Create a sentinel element at the bottom
  const sentinel = document.createElement("div");
  sentinel.id = "scroll-sentinel";
  sentinel.style.height = "1px";

  // Observe the main container's scroll
  const checkAndAddSentinel = () => {
    const existingSentinel = document.getElementById("scroll-sentinel");
    if (existingSentinel) {
      existingSentinel.remove();
    }

    // Add sentinel to the parent container
    const mainElement = booksContainer.parentElement;
    if (mainElement) {
      mainElement.appendChild(sentinel);
      observer.observe(sentinel);
    }
  };

  // Initial setup
  setTimeout(checkAndAddSentinel, 100);

  // Re-add sentinel after books load
  const originalDisplayBooks = window.displayBooks;
  window.displayBooks = function (...args) {
    originalDisplayBooks.apply(this, args);
    setTimeout(checkAndAddSentinel, 100);
  };
}
