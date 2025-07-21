FROM python:3.10-slim
WORKDIR /app
COPY app.py .
RUN pip install --no-cache-dir psycopg2-binary requests
CMD ["python", "app.py"]