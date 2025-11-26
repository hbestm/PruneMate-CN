FROM python:3.12-slim

WORKDIR /app

# Copy app files
COPY prunemate.py /app/prunemate.py
COPY templates /app/templates
COPY static /app/static


# Install Python dependencies (incl. Docker SDK, Gunicorn, and file-based locking)
RUN pip install --no-cache-dir Flask APScheduler docker gunicorn filelock

EXPOSE 8080

CMD ["python", "prunemate.py"]
