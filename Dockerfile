FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

COPY VectorFlow/ /app/
COPY .env /app/

ENV PYTHONPATH=/app

RUN groupadd -r vectorflow && \
    useradd -r -g vectorflow vectorflow && \
    chown -R vectorflow:vectorflow /app
USER vectorflow

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"] 