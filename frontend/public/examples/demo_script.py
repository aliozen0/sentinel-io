"""
GPU Training Test Script
Test this with io-Guard Analyze feature
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from transformers import AutoModel, AutoTokenizer
import numpy as np

# Configuration
MODEL_NAME = "bert-base-uncased"
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 2e-5
MAX_LENGTH = 512

class SentimentClassifier(nn.Module):
    """
    BERT-based Sentiment Analysis Model
    Requires: ~8GB VRAM for training
    """
    def __init__(self, n_classes=3):
        super().__init__()
        self.bert = AutoModel.from_pretrained(MODEL_NAME)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(self.bert.config.hidden_size, n_classes)
    
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.pooler_output
        dropped = self.dropout(pooled)
        return self.fc(dropped)


def train_model():
    # Device setup
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using device: {device}")
    
    # Model
    model = SentimentClassifier(n_classes=3)
    model = model.to(device)
    
    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()
    
    # Simulated training loop
    for epoch in range(EPOCHS):
        model.train()
        
        # Simulated batch
        batch_size = BATCH_SIZE
        seq_len = MAX_LENGTH
        
        # Random data (replace with real DataLoader)
        input_ids = torch.randint(0, 30000, (batch_size, seq_len)).to(device)
        attention_mask = torch.ones(batch_size, seq_len).to(device)
        labels = torch.randint(0, 3, (batch_size,)).to(device)
        
        # Forward pass
        outputs = model(input_ids, attention_mask)
        loss = criterion(outputs, labels)
        
        # Backward pass
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Metrics
        acc = (outputs.argmax(dim=1) == labels).float().mean()
        print(f"[EPOCH {epoch+1}/{EPOCHS}] Loss: {loss.item():.4f} | Accuracy: {acc.item()*100:.1f}%")
    
    print("[SUCCESS] Training completed!")
    return model


if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Starting BERT Sentiment Analysis Training")
    print("=" * 50)
    trained_model = train_model()
