import numpy as np
import onnxruntime as ort

# Load model
session = ort.InferenceSession("output/StandardWave1/models/timesnet_model.onnx")

# Generate sine wave (300 samples, 3 channels, all identical)
t = np.linspace(0, 10, 300)  # 10 seconds at 30 Hz
sine_wave = np.sin(2 * np.pi * 1.0 * t)  # 1 Hz sine wave

# Create 3-channel input (all channels same)
input_data = np.stack([sine_wave, sine_wave, sine_wave], axis=1)  # Shape: (300, 3)
input_data = np.expand_dims(input_data, axis=0).astype(np.float32)  # Shape: (1, 300, 3)

print(f"Input shape: {input_data.shape}")
print(f"Input range: [{input_data.min():.3f}, {input_data.max():.3f}]")
print(f"First 10 values (flattened): {input_data.flatten()[:10]}")

# Run inference
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name
result = session.run([output_name], {input_name: input_data})

logits = result[0][0]
predicted_class = np.argmax(logits)
class_names = ["sawtooth", "sine", "square", "triangular"]

print(f"\nLogits: {logits}")
print(f"Predicted class: {predicted_class} ({class_names[predicted_class]})")
print(f"Expected: Class 1 (sine)")
