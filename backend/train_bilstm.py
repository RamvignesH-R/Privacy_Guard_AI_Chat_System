import torch
import torch.nn as nn
import torch.optim as optim
import json
import os
import random
from bilstm_model import BiLSTM_PII_Tagger

DATASET_PATH = 'model_output/bilstm_dataset.json'

def prepare_sequence(seq, to_ix):
    idxs = [to_ix.get(w.lower(), to_ix["<UNK>"]) for w in seq]
    return torch.tensor(idxs, dtype=torch.long)

def init_default_dataset():
    training_data = []
    names = ["Prince Krishna Adhitiya", "Ramvignesh R", "John Doe", "Jane Smith", "Rahul Dravid", "Virat Kohli", "Karthik M", "Sneha K", "Vijay Kumar", "Ayesha Singh", "Vikram Sharma"]
    addresses = ["IIT Delhi, Delhi", "PSG college of Technology, Coimbatore", "Anna University, Chennai", "MIT Pune", "SRM University, Chennai", "Stanford University", "Bangalore, India", "New York City"]

    for name in names:
        name_tokens = name.split()
        name_tags = ["B-NAME"] + ["I-NAME"] * (len(name_tokens)-1)
        for addr in addresses:
            addr_tokens = addr.split()
            addr_tags = ["B-ADDRESS"] + ["I-ADDRESS"] * (len(addr_tokens)-1)
            
            words1 = ["Hi", "I", "am"] + name_tokens + ["from"] + addr_tokens + ["."]
            tags1 = ["O", "O", "O"] + name_tags + ["O"] + addr_tags + ["O"]
            training_data.append((words1, tags1))
            
            words2 = ["My", "name", "is"] + name_tokens + ["and", "I", "live", "in"] + addr_tokens + ["."]
            tags2 = ["O", "O", "O"] + name_tags + ["O", "O", "O", "O"] + addr_tags + ["O"]
            training_data.append((words2, tags2))

    static_data = [
        ("My age is 31 and my contact number to call is 4394539455 .".split(), ["O", "O", "O", "B-AGE", "O", "O", "O", "O", "O", "O", "O", "B-PHONE", "O"]),
        ("My roll no . is 2334BE34 .".split(), ["O", "O", "O", "O", "O", "B-ID", "O"]),
        ("Another test from IIT Delhi with id 44xy99 .".split(), ["O", "O", "O", "B-ADDRESS", "I-ADDRESS", "O", "O", "B-ID", "O"]),
        ("Contact Ramvignesh at his personal phone 555-0100 .".split(), ["O", "B-NAME", "O", "O", "O", "O", "B-PHONE", "O"])
    ]
    for _ in range(20):
        training_data.extend(static_data)
        
    os.makedirs('model_output', exist_ok=True)
    with open(DATASET_PATH, 'w') as f:
        json.dump(training_data, f)
        
    return training_data

def train_model(epochs=150):
    if not os.path.exists(DATASET_PATH):
        training_data = init_default_dataset()
    else:
        with open(DATASET_PATH, 'r') as f:
            training_data = json.load(f)

    word_to_ix = {"<PAD>": 0, "<UNK>": 1}
    for sentence, tags in training_data:
        for word in sentence:
            w_lower = word.lower()
            if w_lower not in word_to_ix:
                word_to_ix[w_lower] = len(word_to_ix)

    tag_to_ix = {"O": 0, "B-NAME": 1, "I-NAME": 2, "B-PHONE": 3, "B-EMAIL": 4, "B-ADDRESS": 5, "I-ADDRESS": 6, "B-AGE": 7, "B-ID": 8}

    model = BiLSTM_PII_Tagger(len(word_to_ix), tag_to_ix, embedding_dim=64, hidden_dim=64)
    loss_function = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.1)

    print(f"Training BiLSTM model on {len(training_data)} sentences for {epochs} epochs ...")
    for epoch in range(epochs):
        total_loss = 0
        for sentence, tags in training_data:
            model.zero_grad()
            sentence_in = prepare_sequence(sentence, word_to_ix).unsqueeze(0)  
            targets = torch.tensor([tag_to_ix.get(t, 0) for t in tags], dtype=torch.long)
            
            tag_scores = model(sentence_in)
            loss = loss_function(tag_scores.view(-1, len(tag_to_ix)), targets)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1} loss: {total_loss}")

    print("Training complete! Final epoch loss:", total_loss)
    torch.save(model.state_dict(), 'model_output/bilstm_weights.pth')
    with open('model_output/bilstm_vocab.json', 'w') as f:
        json.dump({'word_to_ix': word_to_ix, 'tag_to_ix': tag_to_ix}, f)
        
def trigger_retraining(words, tags):
    # Appends new custom user feedback syntax
    if not os.path.exists(DATASET_PATH):
        training_data = init_default_dataset()
    else:
        with open(DATASET_PATH, 'r') as f:
            training_data = json.load(f)
            
    # Duplicating exactly 10 times to boost model's memory of this explicit feedback loop
    for _ in range(10): 
        training_data.append((words, tags))
        
    with open(DATASET_PATH, 'w') as f:
        json.dump(training_data, f)
        
    train_model(epochs=150)

if __name__ == "__main__":
    train_model(epochs=150)
