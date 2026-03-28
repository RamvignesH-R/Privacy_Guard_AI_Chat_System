import torch
import torch.nn as nn
import json
import os

class BiLSTM_PII_Tagger(nn.Module):
    def __init__(self, vocab_size, tag_to_ix, embedding_dim=64, hidden_dim=64):
        super(BiLSTM_PII_Tagger, self).__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.vocab_size = vocab_size
        self.tag_to_ix = tag_to_ix
        self.target_size = len(tag_to_ix)
        
        self.word_embeddings = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim // 2, num_layers=1, bidirectional=True, batch_first=True)
        self.hidden2tag = nn.Linear(hidden_dim, self.target_size)

    def forward(self, sentence):
        embeds = self.word_embeddings(sentence)
        lstm_out, _ = self.lstm(embeds)
        tag_space = self.hidden2tag(lstm_out)
        return tag_space

def load_model(model_dir="."):
    with open(os.path.join(model_dir, 'bilstm_vocab.json'), 'r') as f:
        data = json.load(f)
        word_to_ix = data['word_to_ix']
        tag_to_ix = data['tag_to_ix']
        
    ix_to_tag = {v: k for k, v in tag_to_ix.items()}
    vocab_size = len(word_to_ix)
    
    model = BiLSTM_PII_Tagger(vocab_size, tag_to_ix, embedding_dim=64, hidden_dim=64)
    model.load_state_dict(torch.load(os.path.join(model_dir, 'bilstm_weights.pth'), map_location=torch.device('cpu')))
    model.eval()
    return model, word_to_ix, ix_to_tag
