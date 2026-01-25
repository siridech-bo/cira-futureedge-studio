#!/usr/bin/env python3
"""
Convert sample-by-sample CBOR files to windowed format for CiRA Studio
"""

import cbor2
import os
import glob
from collections import defaultdict

def convert_to_windows(input_file, output_file, window_size=300):
    """
    Convert sample-by-sample CBOR to windowed CBOR

    Input format: samples[i]['data'] = [ch0_value, ch1_value, ch2_value]
    Output format: samples[i]['data'] = [ch0_s0...ch0_s299, ch1_s0...ch1_s299, ch2_s0...ch2_s299]
    """

    # Load input file
    with open(input_file, 'rb') as f:
        input_data = cbor2.load(f)

    samples = input_data['samples']

    if len(samples) < window_size:
        print(f"  [WARNING] File has only {len(samples)} samples, need {window_size} for one window")
        return False

    # Group by class
    class_samples = defaultdict(list)
    for sample in samples:
        class_name = sample['class_name']
        class_id = sample['class_id']
        data_values = sample['data']  # [ch0, ch1, ch2]
        class_samples[class_name].append({
            'class_id': class_id,
            'data': data_values,
            'timestamp': sample.get('timestamp', 0)
        })

    # Create windows for each class
    output_samples = []

    for class_name, samples_list in class_samples.items():
        num_channels = len(samples_list[0]['data'])
        class_id = samples_list[0]['class_id']

        # Create sliding windows
        for start_idx in range(0, len(samples_list) - window_size + 1, window_size):
            window_samples = samples_list[start_idx:start_idx + window_size]

            # Reshape to channel-by-channel layout
            window_data = []
            for ch in range(num_channels):
                for sample in window_samples:
                    window_data.append(sample['data'][ch])

            output_samples.append({
                'class_name': class_name,
                'class_id': class_id,
                'data': window_data,
                'timestamp': window_samples[0]['timestamp']
            })

    # Save output file
    output_data = {'samples': output_samples}
    with open(output_file, 'wb') as f:
        cbor2.dump(output_data, f)

    print(f"  Created {len(output_samples)} windows from {len(samples)} samples")
    return True

def convert_directory(input_dir, output_dir, window_size=300):
    """Convert all CBOR files in a directory"""

    os.makedirs(output_dir, exist_ok=True)

    cbor_files = glob.glob(os.path.join(input_dir, "*.cbor"))

    print(f"Converting {len(cbor_files)} files from {input_dir} to {output_dir}")
    print(f"Window size: {window_size}")
    print()

    for input_file in cbor_files:
        filename = os.path.basename(input_file)
        output_file = os.path.join(output_dir, filename)

        print(f"Processing: {filename}")
        convert_to_windows(input_file, output_file, window_size)

    print()
    print("[DONE] Conversion complete!")

if __name__ == "__main__":
    # Convert train and test datasets
    base_dir = r"D:\CiRA FES\Dataset\StandardWave_new"
    output_base = r"D:\CiRA FES\Dataset\StandardWave_Windowed"

    # Convert train
    convert_directory(
        os.path.join(base_dir, "train"),
        os.path.join(output_base, "train"),
        window_size=300
    )

    # Convert test
    convert_directory(
        os.path.join(base_dir, "test"),
        os.path.join(output_base, "test"),
        window_size=300
    )
