FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cases/ cases/
COPY scripts/ scripts/
COPY tests/ tests/

RUN python3 scripts/validate.py

ENTRYPOINT ["python3", "scripts/evaluate.py"]
