import re
import requests
import os
import json
import torch
from transformers import pipeline
from bilstm_model import load_model

class RegexDetector:
    def detect(self, text):
        entities = []
        
        rules = [
            ('EMAIL', r'[\w\.-]+@[\w\.-]+'),
            ('PHONE', r'\b(\+?\d{1,3}[\s\-\.]?)?(\(?\d{2,4}\)?[\s\-\.]?)?\d{3,5}[\s\-\.]?\d{3,5}\b'),
            ('ID NUMBER', r'(?i)\b[STFGM]\d{7}[A-Z]\b'), # Singapore NRIC
            ('ID NUMBER', r'(?i)\b[A-Z0-9]{5,10}\b(?=\s*(?:mcr|nric|fin|passport))'), # Contextual MCR
            ('MRN', r'(?i)\bMRN[\-\s]?\d{4,10}\b'),
            ('AADHAAR', r'\b\d{4}[\s\-]\d{4}[\s\-]\d{4}\b'),
            ('DATE', r'\b(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}|\d{4}[\/\-\.]\d{2}[\/\-\.]\d{2})\b'),
            ('NAME', r'\b(?:Mr|Mrs|Ms|Miss|Dr|Mdm|Prof)\.?\s+[A-Z][a-zA-Z\'\-]+(?:\s+[A-Z][a-zA-Z\'\-]+){0,3}\b'),
        ]
        
        for label, pattern in rules:
            for match in re.finditer(pattern, text):
                entities.append((match.start(), match.end(), label, 1.0, 'Regex'))
                
        # Contextual Rules (Label: Value)
        contextual_rules = [
            ('ID NUMBER', r'(?i)(?:mcr|nric|fin|passport)(?:[\s/]*no\.?|[\s/]*number)?(?:[\s/]*of\s*(?:patient|doctor))?\s*[:\.]\s*([A-Za-z0-9]{5,15})\b'),
        ]
        for label, pattern in contextual_rules:
            for match in re.finditer(pattern, text):
                start, end = match.start(1), match.end(1)
                entities.append((start, end, label, 1.0, 'Regex'))
                
        # Contextual Age rule
        for match in re.finditer(r'\b(?:age is |I am |aged? )(\d{1,3})\b', text, flags=re.IGNORECASE):
            start = match.start(1)
            end = match.end(1)
            entities.append((start, end, 'AGE', 1.0, 'Regex'))
            
        # Active Learning Memory rule
        try:
            with open('model_output/known_entities.json', 'r') as f:
                known = json.load(f)
            for name, label in known.items():
                if len(name) < 2: continue
                # Match whole words (case insensitive)
                pattern = r'\b' + re.escape(name) + r'\b'
                for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                    entities.append((match.start(), match.end(), label, 1.0, 'Memory'))
        except Exception as e:
            pass
            
        return entities

class BiLSTMDetector:
    def __init__(self):
        try:
            self.model, self.word_to_ix, self.ix_to_tag = load_model('model_output')
        except Exception as e:
            print(f"Warning: BiLSTM model not found. Expected in model_output/. Run train_bilstm.py. Error: {e}")
            self.model = None

    def detect(self, text):
        if not self.model:
            return []
        
        words = text.split()
        if not words: return []
        
        # Strip trailing/leading punctuation for dictionary lookup
        clean_words = []
        for w in words:
            cw = w.strip(".,;:!'\"?")
            if cw.lower().endswith("'s") or cw.lower().endswith("’s"):
                cw = cw[:-2]
            clean_words.append(cw)
        
        idxs = [self.word_to_ix.get(cw.lower(), self.word_to_ix["<UNK>"]) for cw in clean_words]
        sentence_in = torch.tensor(idxs, dtype=torch.long).unsqueeze(0)
        
        with torch.no_grad():
            tag_scores = self.model(sentence_in)
            preds = torch.argmax(tag_scores, dim=2)[0].tolist()
        
        entities = []
        char_idx = 0
        for i, word in enumerate(words):
            start = text.find(word, char_idx)
            if start == -1: 
                start = char_idx
            end = start + len(word)
            char_idx = end

            clean_word = clean_words[i]
            if clean_word.lower() not in self.word_to_ix:
                # OOV word. Our dummy BiLSTM model will heavily hallucinate phones for OOV, so we skip.
                continue
            
            tag = self.ix_to_tag.get(preds[i], 'O')
            if tag != 'O':
                label = tag.split('-')[-1] 
                entities.append((start, end, label, 0.8, 'BiLSTM'))
                
        return entities

class BERTDetector:
    def __init__(self, token=None):
        print("Loading local BERT model...")
        try:
            self.pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
            self.is_loaded = True
        except Exception as e:
            print(f"Failed to load local BERT model: {e}")
            self.is_loaded = False
        
    def detect(self, text):
        if not self.is_loaded:
            return []
            
        try:
            results = self.pipeline(text)
            entities = []
            for res in results:
                label = res['entity_group']
                if label == 'PER': label = 'NAME'
                elif label == 'LOC': label = 'ADDRESS'
                elif label == 'ORG': label = 'ORG'
                
                # Convert numpy float32 to python float for json serialization
                score = float(res['score'])
                entities.append((res['start'], res['end'], label, score, 'BERT'))
            return entities
        except Exception as e:
            print(f"BERT Local Inference Error: {e}")
            return []

class PrivacyGuard:
    def __init__(self):
        self.regex_detector = RegexDetector()
        self.bilstm_detector = BiLSTMDetector()
        hf_token = os.environ.get("HF_API_TOKEN", "")
        if os.environ.get("DISABLE_BERT", "false").lower() == "true":
            self.bert_detector = None
            print("BERT loading disabled for low-memory deployment.")
        else:
            self.bert_detector = BERTDetector(hf_token)
        
    def reload_model(self):
        print("Reloading BiLSTM model from updated weights...")
        self.bilstm_detector = BiLSTMDetector()
        
    def process(self, text):
        all_entities = []
        all_entities.extend(self.regex_detector.detect(text))
        all_entities.extend(self.bilstm_detector.detect(text))
        # BERT isolated for Feedback Loop retraining only
        # if os.environ.get("HF_API_TOKEN"):
        #     all_entities.extend(self.bert_detector.detect(text))
            
        priority = {'Memory': 4, 'BERT': 3, 'BiLSTM': 2, 'Regex': 1}
        all_entities.sort(key=lambda x: (x[0], -priority[x[4]]))
        
        merged_entities = []
        covered_indices = set()
        
        for entity in all_entities:
            start, end, label, score, source = entity
            overlap = False
            for i in range(start, end):
                if i in covered_indices:
                    overlap = True
                    break
            if not overlap:
                merged_entities.append(entity)
                for i in range(start, end):
                    covered_indices.add(i)
                    
        merged_entities.sort(key=lambda x: x[0], reverse=True)
        masked_text = text
        logs = []
        
        for start, end, label, score, source in merged_entities:
            original_str = masked_text[start:end]
            place_holder = f"[{label}]"
            masked_text = masked_text[:start] + place_holder + masked_text[end:]
            logs.append({"original": original_str, "masked": place_holder, "label": label, "score": score, "source": source})
            
        return masked_text, logs
