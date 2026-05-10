FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && 
apt-get install -y tesseract-ocr poppler-utils && 
rm -rf /var/lib/apt/lists/*

COPY web/requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "web/app.py"]
