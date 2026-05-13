import os
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import engine, Base, get_db
from models import ChatLog
from pii_pipeline import PrivacyGuard
import train_bilstm
import json

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    print("WARNING: GEMINI_API_KEY not set in .env file!")
else:
    genai.configure(api_key=api_key)
    print("Gemini initialized with API key.")

privacy_guard = PrivacyGuard()

class ChatRequest(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"message": "Privacy Guard AI Chat API is running smoothly."}

@app.post("/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    original_input = request.text
    
    # 1. Mask Input
    masked_input, input_logs = privacy_guard.process(original_input)
    
    # 2. Call Gemini
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured. Please add it to backend/.env")
    
    raw_gemini_response = ""
    try:
        model = genai.GenerativeModel("gemini-flash-latest")
        response = model.generate_content(
            masked_input,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        raw_gemini_response = response.text
    except Exception as e:
        raw_gemini_response = f"Error calling Gemini API: {e}"

        
    # 3. Mask Gemini response
    masked_response, output_logs = privacy_guard.process(raw_gemini_response)
    
    # 4. Save to DB
    new_log = ChatLog(
        original_input=original_input,
        masked_input=masked_input,
        gemini_response=raw_gemini_response,
        masked_response=masked_response
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    return {
        "original": original_input,
        "masked_input": masked_input,
        "gemini_response": raw_gemini_response,
        "masked_response": masked_response,
        "input_entities": input_logs,
        "output_entities": output_logs
    }

@app.post("/report_bad_masking")
def report_bad_masking(request: ChatRequest):
    text = request.text
    print(f"User flagged bad masking. Processing with BERT: {text}")
    
    # Title-case the text to help BERT detect lowercase names (e.g., 'ramvignesh' -> 'Ramvignesh')
    title_text = text.title()
    bert_entities = privacy_guard.bert_detector.detect(title_text)
    if privacy_guard.bert_detector is None:
        return {
            "status": "disabled",
            "message": "BERT retraining disabled in cloud deployment due to memory limits."
        }
    if not bert_entities and api_key:
        print("BERT failed to find entities, falling back to Gemini for ground-truth extraction...")
        try:
            model = genai.GenerativeModel("gemini-flash-latest")
            prompt = f"Extract all people names from the following text. Return ONLY a comma-separated list of names. If none, return 'NONE'. Text: '{text}'"
            response = model.generate_content(prompt)
            names = [n.strip() for n in response.text.split(',') if n.strip() and n.strip() != 'NONE']
            
            for name in names:
                start = text.find(name)
                if start != -1:
                    bert_entities.append((start, start + len(name), 'NAME', 1.0, 'GeminiFallback'))
        except Exception as e:
            print(f"Gemini fallback failed: {e}")
            
    if not bert_entities:
        return {"status": "error", "message": "BERT and Fallback failed to detect robust entities."}
        
    print(f"BERT detected entities: {bert_entities}")
    words = text.split()
    tags = ["O"] * len(words)
    
    char_idx = 0
    active_label = None
    for i, w in enumerate(words):
        start = text.find(w, char_idx)
        if start == -1: start = char_idx
        end = start + len(w)
        char_idx = end
        
        assigned = False
        for b_start, b_end, b_label, b_score, b_source in bert_entities:
            # Check overlap
            if max(start, b_start) < min(end, b_end):
                if active_label != b_label:
                    tags[i] = f"B-{b_label}"
                    active_label = b_label
                else:
                    tags[i] = f"I-{b_label}"
                assigned = True
                break
        if not assigned:
            active_label = None
            
    print(f"Constructed BiLSTM Tags array: {tags}")
    
    # Save to known_entities dictionary for immediate exact-match application
    known_path = 'model_output/known_entities.json'
    known = {}
    if os.path.exists(known_path):
        try:
            with open(known_path, 'r') as f:
                known = json.load(f)
        except: pass
        
    for start, end, label, score, source in bert_entities:
        entity_text = text[start:end]
        if entity_text.strip():
            known[entity_text.strip().lower()] = label
            
    os.makedirs('model_output', exist_ok=True)
    with open(known_path, 'w') as f:
        json.dump(known, f)

    try:
        train_bilstm.trigger_retraining(words, tags)
    except Exception as e:
        return {"status": "error", "message": f"BiLSTM Retraining failed: {str(e)}"}
        
    privacy_guard.reload_model()
    return {"status": "success", "message": "Model retrained using BERT templates."}

@app.post("/mask_document")
def mask_document_endpoint(request: ChatRequest):
    text = request.text
    masked_text, logs = privacy_guard.process(text)
    
    entities_found = {}
    for log in logs:
        # Standardize labels
        label = log['label']
        if label == 'PER': label = 'NAME'
        elif label == 'LOC': label = 'ADDRESS'
        elif label == 'ORG': label = 'HOSPITAL'
        
        bracket_label = f"[{label}]"
        entities_found[bracket_label] = entities_found.get(bracket_label, 0) + 1
        
    return {
        "original": text,
        "masked": masked_text,
        "entities_found": entities_found,
        "total_redactions": len(logs)
    }
