import torch
import torchvision.models as models

# SCENARIO 1: Lightweight Computer Vision Model
# Expectation: APPROVED (Fits easily on 24GB)

def train():
    # Model: ResNet50 (Approx 25M params -> ~100MB weights)
    model = models.resnet50(pretrained=False)
    
    # Configuration
    BATCH_SIZE = 64
    PRECISION = "fp32" 
    IMAGE_SIZE = 224
    
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    print(f"Training ResNet50 with batch {BATCH_SIZE}...")

if __name__ == "__main__":
    train()
