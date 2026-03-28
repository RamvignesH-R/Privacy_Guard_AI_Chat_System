import re
import requests
import os
import torch
from bilstm_model import load_model

class RegexDetector:
    def detect(self, text):
        entities = []
        # Email
        for match in re.finditer(r'[\w\.-]+@[\w\.-]+', text):
            entities.append((match.start(), match.end(), 'EMAIL', 1.0, 'Regex'))
        # Phone (simple format & 10 digit format)
        for match in re.finditer(r'\b(\d{3}[-.]?\d{3}[-.]?\d{4}|\d{10})\b', text):
            entities.append((match.start(), match.end(), 'PHONE', 1.0, 'Regex'))
        # Extracted Age context (e.g. age is 31)
        for match in re.finditer(r'\b(age is |I am )(\d{1,3})\b', text, flags=re.IGNORECASE):
            digits = match.group(2)
            start = match.start(2)
            end = match.end(2)
            entities.append((start, end, 'AGE', 1.0, 'Regex'))
        # Specific alphanumeric IDs
        for match in re.finditer(r'\b\d{2}[a-zA-Z]{2}\d{2}\b', text):
            entities.append((match.start(), match.end(), 'ID', 1.0, 'Regex'))
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
        
        idxs = [self.word_to_ix.get(w, self.word_to_ix["<UNK>"]) for w in words]
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

            if word not in self.word_to_ix:
                # OOV word. Our dummy BiLSTM model will heavily hallucinate phones for OOV, so we skip.
                continue
            
            tag = self.ix_to_tag.get(preds[i], 'O')
            if tag != 'O':
                label = tag.split('-')[-1] 
                entities.append((start, end, label, 0.8, 'BiLSTM'))
                
        return entities

class BERTDetector:
    def __init__(self, token):
        self.api_url = "https://router.huggingface.co/hf-inference/models/dslim/bert-base-NER"
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
        
    def detect(self, text):
        if not self.api_url or not self.headers.get("Authorization") or self.headers["Authorization"] == "Bearer ":
            return []
            
        try:
            response = requests.post(self.api_url, headers=self.headers, json={"inputs": text})
            if response.status_code == 200:
                results = response.json()
                if not isinstance(results, list): return []
                entities = []
                for res in results:
                    label = res.get('entity_group', res.get('entity', 'UNK'))
                    if label.startswith('B-') or label.startswith('I-'):
                        label = label[2:]
                    if label == 'PER': label = 'NAME'
                    elif label == 'LOC': label = 'ADDRESS'
                    elif label == 'ORG': label = 'ORG'
                    
                    entities.append((res['start'], res['end'], label, res['score'], 'BERT'))
                return entities
            else:
                print(f"BERT API Error: {response.text}")
                return []
        except Exception as e:
            print(f"BERT Fetch Exception: {e}")
            return []

class PrivacyGuard:
    def __init__(self):
        self.regex_detector = RegexDetector()
        self.bilstm_detector = BiLSTMDetector()
        hf_token = os.environ.get("HF_API_TOKEN", "")
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
            
        priority = {'BERT': 3, 'BiLSTM': 2, 'Regex': 1}
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
