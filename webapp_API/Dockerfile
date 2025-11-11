FROM python:3.10-slim

# Install Python dependencies and Gunicorn
ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn
RUN groupadd -r app && useradd -r -g app app

# Copy the rest of the codebase into the image
COPY --chown=app:app . ./
USER app

CMD exec gunicorn --bind :$PORT --log-level info --workers 1 --threads 8 --timeout 0 app:app --preload