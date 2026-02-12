FROM python:3.12-slim

WORKDIR /app

# Install nfo from local source
COPY pyproject.toml VERSION README.md LICENSE /nfo-src/
COPY nfo/ /nfo-src/nfo/
RUN pip install --no-cache-dir /nfo-src

# Install optional dependencies for HTTP service
RUN pip install --no-cache-dir fastapi uvicorn prometheus_client

# Copy examples and demo
COPY examples/ /app/examples/

EXPOSE 8080

CMD ["python", "examples/http_service.py"]
