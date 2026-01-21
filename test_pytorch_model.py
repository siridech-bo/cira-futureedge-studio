import numpy as np
import torch
import sys
sys.path.append('core')
from core.deep_models.timesnet import TimesNetClassifier

# Load PyTorch model
model = TimesNetClassifier(
    seq_len=300,
    input_channels=3,
    num_classes=4,
    d_model=32,
    d_ff=64,
    num_kernels=4,
    top_k=3,
    num_layers=2
)
model.load_state_dict(torch.load("output/StandardWave1/models/timesnet_model.pth", map_location='cpu'))
model.eval()

# Generate sine wave (300 samples, 3 channels)
t = np.linspace(0, 10, 300)
sine_wave = np.sin(2 * np.pi * 1.0 * t)
input_data = np.stack([sine_wave, sine_wave, sine_wave], axis=1)
input_data = np.expand_dims(input_data, axis=0).astype(np.float32)
input_tensor = torch.from_numpy(input_data)

print(f"Input shape: {input_tensor.shape}")
print(f"Input range: [{input_tensor.min():.3f}, {input_tensor.max():.3f}]")

# Run inference
with torch.no_grad():
    logits = model(input_tensor)
    predicted_class = torch.argmax(logits, dim=1).item()

class_names = ["sawtooth", "sine", "square", "triangular"]
print(f"\nLogits: {logits[0].numpy()}")
print(f"Predicted class: {predicted_class} ({class_names[predicted_class]})")
print(f"Expected: Class 1 (sine)")
