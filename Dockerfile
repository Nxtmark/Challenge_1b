FROM python:3.10

WORKDIR /app

COPY analyze.py /app/analyze.py
COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libgomp1 \
    git \
    apertium \
    apertium-en-es \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "analyze.py"]
