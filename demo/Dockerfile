FROM python:3.12-slim

WORKDIR /app

# Install nfo from local source
COPY pyproject.toml VERSION README.md LICENSE /nfo-src/
COPY nfo/ /nfo-src/nfo/
RUN pip install --no-cache-dir /nfo-src

# Install demo dependencies
COPY demo/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy demo app
COPY demo/app.py /app/app.py

EXPOSE 8000 9090

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
