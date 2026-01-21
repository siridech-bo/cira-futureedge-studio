"""
Fix CBOR dataset by removing value repetitions and reshaping to proper format.

Current: 300 values = 100 values/channel with each repeated 3x = only 33 unique samples/channel
Target: 300 values = 300 samples per channel (need to interpolate)

Since we can't create data that doesn't exist, we'll:
1. Extract the 33 unique samples per channel
2. Interpolate to 300 samples per channel
3. Reshape and save
"""

import cbor2
import numpy as np
from pathlib import Path
from scipy import interpolate

def remove_repetitions(arr):
    """Remove consecutive duplicate values"""
    unique_vals = [arr[0]]
    for i in range(1, len(arr)):
        if abs(arr[i] - arr[i-1]) > 1e-6:  # Different value
            unique_vals.append(arr[i])
    return np.array(unique_vals)

def fix_cbor_file(input_path, output_path, target_samples=300):
    """Fix a single CBOR file"""
    print(f"Processing: {input_path.name}")

    with open(input_path, 'rb') as f:
        data = cbor2.load(f)

    fixed_samples = []

    for sample in data['samples']:
        window = np.array(sample['data'])

        # Remove repetitions from channel-by-channel format
        # Expected: 100 values per channel, but each repeated 3x
        samples_per_channel = len(window) // 3  # 100

        channels = []
        for ch in range(3):
            ch_data = window[ch * samples_per_channel : (ch+1) * samples_per_channel]
            unique_data = remove_repetitions(ch_data)

            # Interpolate from ~33 samples to target_samples
            if len(unique_data) < target_samples:
                x_old = np.linspace(0, 1, len(unique_data))
                x_new = np.linspace(0, 1, target_samples)
                f = interpolate.interp1d(x_old, unique_data, kind='cubic')
                interpolated = f(x_new)
                channels.append(interpolated)
            else:
                # Downsample if somehow we have more
                channels.append(unique_data[:target_samples])

        # Reshape: [ch0_all, ch1_all, ch2_all] format (channel-by-channel)
        fixed_data = np.concatenate(channels).tolist()

        fixed_sample = {
            'timestamp': sample['timestamp'],
            'class_name': sample['class_name'],
            'class_id': sample['class_id'],
            'data': fixed_data
        }
        fixed_samples.append(fixed_sample)

    # Save fixed data
    fixed_data = {'samples': fixed_samples}

    with open(output_path, 'wb') as f:
        cbor2.dump(fixed_data, f)

    print(f"  [OK] Fixed {len(fixed_samples)} samples")
    print(f"    Original window size: {len(data['samples'][0]['data'])}")
    print(f"    Fixed window size: {len(fixed_data['samples'][0]['data'])}")
    return True

def fix_dataset_directory(input_dir, output_dir):
    """Fix all CBOR files in a directory"""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        print(f"ERROR: Input directory not found: {input_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"Fixing dataset: {input_dir}")
    print(f"Output to: {output_dir}")
    print(f"{'='*80}\n")

    cbor_files = list(input_dir.glob("*.cbor"))
    cbor_files = [f for f in cbor_files if not str(f).endswith('.backup')]

    print(f"Found {len(cbor_files)} CBOR files\n")

    for cbor_file in cbor_files:
        output_file = output_dir / cbor_file.name
        fix_cbor_file(cbor_file, output_file)

    print(f"\n{'='*80}")
    print(f"Fixed {len(cbor_files)} files")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    # Fix train dataset
    fix_dataset_directory(
        "D:/CiRA FES/Dataset/StandardWave/train",
        "D:/CiRA FES/Dataset/StandardWave_Fixed/train"
    )

    # Fix test dataset
    fix_dataset_directory(
        "D:/CiRA FES/Dataset/StandardWave/test",
        "D:/CiRA FES/Dataset/StandardWave_Fixed/test"
    )

    print("\n" + "="*80)
    print("DATASET FIXED!")
    print("="*80)
    print("New dataset location: D:/CiRA FES/Dataset/StandardWave_Fixed/")
    print("\nNext steps:")
    print("1. Create new project in CiRA Studio")
    print("2. Point it to StandardWave_Fixed dataset")
    print("3. Train model")
    print("="*80)
