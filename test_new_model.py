import numpy as np
import onnxruntime as ort

# Load the NEW model
session = ort.InferenceSession("output/StandardWave2/models/timesnet_model.onnx")

# Test with different waveforms
def test_waveform(waveform_type, data, expected_class_id):
    # Create 3-channel input (all channels same)
    input_data = np.stack([data, data, data], axis=1)  # Shape: (300, 3)
    input_data = np.expand_dims(input_data, axis=0).astype(np.float32)  # Shape: (1, 300, 3)

    # Run inference
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    result = session.run([output_name], {input_name: input_data})

    logits = result[0][0]
    predicted_class = np.argmax(logits)
    confidence = np.exp(logits[predicted_class]) / np.sum(np.exp(logits))

    class_names = ["sawtooth", "sine", "square", "triangular"]
    status = "[OK]" if predicted_class == expected_class_id else "[FAIL]"

    print(f"{status} {waveform_type:12s}: Predicted={predicted_class} ({class_names[predicted_class]:12s}), "
          f"Expected={expected_class_id} ({class_names[expected_class_id]:12s}), "
          f"Confidence={confidence:.3f}")
    print(f"   Logits: {logits}")
    return predicted_class == expected_class_id

# Generate test waveforms (300 samples each)
t = np.linspace(0, 10, 300)

# Test 1: Sine wave (class_id=1)
sine_wave = np.sin(2 * np.pi * 1.0 * t)

# Test 2: Sawtooth wave (class_id=0)
sawtooth_wave = 2 * (t % 1.0) - 1.0

# Test 3: Square wave (class_id=2)
square_wave = np.sign(np.sin(2 * np.pi * 1.0 * t))

# Test 4: Triangular wave (class_id=3)
triangular_wave = 2 * np.abs(2 * (t % 1.0) - 1.0) - 1.0

print("="*80)
print("Testing NEW model (StandardWave2) with correct class IDs")
print("="*80)

results = []
results.append(test_waveform("Sine", sine_wave, 1))
print()
results.append(test_waveform("Sawtooth", sawtooth_wave, 0))
print()
results.append(test_waveform("Square", square_wave, 2))
print()
results.append(test_waveform("Triangular", triangular_wave, 3))

print("\n" + "="*80)
if all(results):
    print("[SUCCESS] All waveforms correctly classified!")
else:
    print(f"[FAILURE] {sum(results)}/4 waveforms correctly classified")
print("="*80)
