import os
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from database import engine, Base, get_db
from models import ChatLog
from pii_pipeline import PrivacyGuard
import train_bilstm

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
if api_key:
    genai.configure(api_key=api_key)

privacy_guard = PrivacyGuard()

class ChatRequest(BaseModel):
    text: str

@app.post("/chat")
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    original_input = request.text
    
    # 1. Mask Input
    masked_input, input_logs = privacy_guard.process(original_input)
    
    # 2. Call Gemini
    raw_gemini_response = "Waiting for model configuration."
    if api_key:
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            print("Valid Models for this Key:", available_models)
            
            chosen_model = "models/gemini-1.5-flash"
            if available_models:
                for m in available_models:
                    if 'gemini-1.5-flash' in m:
                        chosen_model = m
                        break
                    elif 'gemini-1.0-pro' in m:
                        chosen_model = m
                        break
                if chosen_model not in available_models:
                    chosen_model = available_models[0]
                    
            model = genai.GenerativeModel(chosen_model) 
            response = model.generate_content(masked_input)
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
    
    bert_entities = privacy_guard.bert_detector.detect(text)
    if not bert_entities:
        return {"status": "error", "message": "BERT failed to detect robust entities or is still loading."}
        
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
    try:
        train_bilstm.trigger_retraining(words, tags)
    except Exception as e:
        return {"status": "error", "message": f"BiLSTM Retraining failed: {str(e)}"}
        
    privacy_guard.reload_model()
    return {"status": "success", "message": "Model retrained using BERT templates."}
