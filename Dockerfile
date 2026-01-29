FROM python:3.14-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY main.py .
COPY templates/ templates/
COPY static/ static/

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Create directory for SQLite database
RUN mkdir -p /app/data

EXPOSE 5000

CMD ["python", "main.py"]
