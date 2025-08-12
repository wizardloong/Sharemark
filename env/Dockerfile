FROM python:3.11-slim

WORKDIR /app

COPY env/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app
COPY env/ /env

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
