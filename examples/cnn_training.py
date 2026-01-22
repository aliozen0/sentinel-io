"""
Lightweight CNN Training Script
Good for testing with smaller VRAM requirements
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms

# Configuration
BATCH_SIZE = 64
EPOCHS = 5
LEARNING_RATE = 0.001

class SimpleCNN(nn.Module):
    """
    Simple CNN for MNIST/CIFAR
    Requires: ~2GB VRAM
    """
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on: {device}")
    
    model = SimpleCNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    for epoch in range(EPOCHS):
        # Simulated batch
        data = torch.randn(BATCH_SIZE, 1, 28, 28).to(device)
        target = torch.randint(0, 10, (BATCH_SIZE,)).to(device)
        
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        
        print(f"Epoch {epoch+1}: Loss = {loss.item():.4f}")
    
    print("✅ Training complete!")


if __name__ == "__main__":
    train()
