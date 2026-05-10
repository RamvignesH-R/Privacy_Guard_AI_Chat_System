# Privacy Guard AI Chat System

An AI-powered privacy protection platform that masks Personally Identifiable Information (PII) from user conversations and uploaded documents before cloud processing.

## Live Demo

Frontend Application: [https://privacy-guard-ai-chat-system-2tmzwgyo5-ramvignesh-rs-projects.vercel.app/](https://privacy-guard-ai-chat-system-2tmzwgyo5-ramvignesh-rs-projects.vercel.app/)

## Features

### AI Chat Privacy Protection

* Real-time PII masking before sending data to cloud AI models
* Sensitive information detection and anonymization
* Gemini AI integration
* Interactive chat interface
* Active learning feedback system for improving masking quality

### Document OCR + Masking

* Upload and process:

  * PDF
  * TXT
  * PNG
  * JPG
  * JPEG
  * DOCX
* OCR support using Tesseract
* Automatic sensitive data masking
* Secure document processing

### Deep Learning Engine

* BiLSTM-based custom masking model
* Transformer-based NER pipeline
* Continuous learning workflow
* Known entities memory storage

---

# Tech Stack

## Frontend

* React.js
* Vite
* Lucide React
* CSS
* Vercel Deployment

## Backend

* FastAPI
* Uvicorn
* SQLAlchemy
* Pydantic
* Python

## AI / Machine Learning

* PyTorch
* HuggingFace Transformers
* BiLSTM
* TorchCRF
* Scikit-learn
* SpaCy
* Gemini API

## OCR / Document Processing

* Tesseract OCR
* PyMuPDF
* pdf2image
* Pillow
* python-docx

## Deployment

* Vercel (Frontend)
* Railway (Backend + OCR Services)
* Docker

---

# System Architecture

```text
Frontend (Vercel)
    ↓
Chat Backend (Railway + FastAPI)
    ↓
PII Detection & Masking
    ↓
Gemini AI Processing

Document OCR Service (Railway + Flask)
    ↓
OCR Extraction
    ↓
PII Masking
```

---

# Project Structure

```text
Privacy_Guard_AI_Chat_System/
│
├── backend/
│   ├── model_output/
│   ├── main.py
│   ├── pii_pipeline.py
│   ├── bilstm_model.py
│   ├── database.py
│   ├── models.py
│   ├── requirements.txt
│   └── .env
│
├── DocumentMasker/
│   ├── utils/
│   │   └── ocr_extractor.py
│   ├── web/
│   │   ├── app.py
│   │   └── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
└── README.md
```

---

# Installation Guide

## 1. Clone Repository

```bash
git clone https://github.com/Ramvignesh-R/Privacy_Guard_AI_Chat_System.git

cd Privacy_Guard_AI_Chat_System
```

---

# Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

# Backend Setup

## Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## Create .env File

```env
GOOGLE_API_KEY=your_gemini_api_key
```

## Run Backend

```bash
uvicorn main:app --reload
```

Backend runs on:

```text
http://localhost:8000
```

---

# OCR Service Setup

## Install Dependencies

```bash
cd DocumentMasker/web
pip install -r requirements.txt
```

## Install OCR Requirements

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils
```

### macOS

```bash
brew install tesseract poppler
```

### Windows

Install:

* Tesseract OCR
* Poppler

## Run OCR Service

```bash
python app.py
```

OCR service runs on:

```text
http://localhost:5000
```

---

# Environment Variables

## Frontend (.env)

```env
VITE_CHAT_API_URL=http://localhost:8000
VITE_OCR_API_URL=http://localhost:5000
```

## Production Environment Variables

```env
VITE_CHAT_API_URL=https://your-railway-chat-url.up.railway.app
VITE_OCR_API_URL=https://your-railway-ocr-url.up.railway.app
```

---

# Deployment

## Frontend Deployment (Vercel)

1. Push frontend code to GitHub
2. Import repository into Vercel
3. Set Root Directory:

```text
frontend
```

4. Add environment variables
5. Deploy

---

## Backend Deployment (Railway)

1. Create Railway project
2. Connect GitHub repository
3. Set Root Directory:

```text
backend
```

4. Add environment variables
5. Deploy FastAPI service

---

## OCR Service Deployment (Railway)

1. Create second Railway project
2. Set Root Directory:

```text
DocumentMasker
```

3. Use Docker deployment
4. Deploy OCR service

---

# API Endpoints

## Chat Endpoint

```http
POST /chat
```

### Request

```json
{
  "text": "My phone number is 9876543210"
}
```

---

## Feedback Endpoint

```http
POST /report_bad_masking
```

---

# Screenshots

## Chat Interface

* Real-time PII masking
* Gemini integration
* Secure AI interaction

## Document OCR

* Upload documents
* OCR extraction
* Masked output generation

---

# Security Highlights

* Sensitive information masking before AI processing
* Privacy-first architecture
* Local preprocessing workflow
* Entity masking pipeline
* Active learning retraining system

---

# Future Improvements

* Multi-language OCR support
* Speech-to-text privacy masking
* Real-time voice anonymization
* Advanced entity detection
* User authentication system
* Analytics dashboard
* PDF export support

---

# Contributors

## Ramvignesh R and Ritujaa BG

Integrated M.Sc Data Science PSG College of Technology

---

# License

This project is developed for educational and research purposes.

---

# Acknowledgements

* Google Gemini API
* HuggingFace Transformers
* PyTorch
* FastAPI
* Railway
* Vercel
* Tesseract OCR
