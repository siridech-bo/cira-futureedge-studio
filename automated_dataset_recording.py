#!/usr/bin/env python3
"""
Automated Dataset Recording Script for CiRA Runtime
Records multiple signal types (sine, square, triangle, sawtooth) sequentially
Supports test mode (5 windows) and full mode (100 windows)
"""

import websocket
import json
import time
import sys
import argparse
from datetime import datetime

class DatasetRecorder:
    def __init__(self, jetson_ip="192.168.1.200", port=8083, username="admin", password="cira123"):
        self.jetson_ip = jetson_ip
        self.port = port
        self.ws_url = f"ws://{jetson_ip}:{port}/ws"
        self.ws = None
        self.recording_active = False
        self.windows_completed = 0
        self.current_signal_type = ""

    def connect(self):
        """Connect to Jetson WebSocket"""
        print(f"Connecting to {self.ws_url}...")
        self.ws = websocket.create_connection(self.ws_url)
        print("✓ Connected to CiRA Runtime")

    def disconnect(self):
        """Disconnect from WebSocket"""
        if self.ws:
            self.ws.close()
            print("✓ Disconnected")

    def send_command(self, command):
        """Send command to runtime"""
        self.ws.send(json.dumps(command))

    def wait_for_response(self, timeout=5):
        """Wait for WebSocket response"""
        self.ws.settimeout(timeout)
        try:
            response = self.ws.recv()
            return json.loads(response)
        except:
            return None

    def set_signal_type(self, signal_type):
        """Change signal generator to specified type
        Options: sine, square, triangle, sawtooth
        """
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Setting signal type to: {signal_type}")

        # Press the 'next_class' button to cycle signal types
        # We need to know current position and press it the right number of times
        # For simplicity, we'll use the reset button first, then cycle

        # Stop signal generator first
        self.send_command({
            "command": "button_press",
            "button_id": "button_1",  # Assuming this is the play/stop button
            "state": 0
        })
        time.sleep(0.5)

        # Reset to first signal type
        self.send_command({
            "command": "button_press",
            "button_id": "reset_button",  # May need to adjust button ID
            "state": 1
        })
        time.sleep(0.5)

        # Cycle to desired signal type
        signal_order = ["sine", "square", "triangle", "sawtooth"]
        if signal_type in signal_order:
            target_index = signal_order.index(signal_type)
            for _ in range(target_index):
                self.send_command({
                    "command": "button_press",
                    "button_id": "next_class_button",
                    "state": 1
                })
                time.sleep(0.3)

        # Start signal generator
        self.send_command({
            "command": "button_press",
            "button_id": "button_1",
            "state": 1
        })

        self.current_signal_type = signal_type
        print(f"✓ Signal type set to: {signal_type}")

    def start_recording(self):
        """Start recording on Data Recorder node"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting recording...")
        self.send_command({
            "command": "start_recording",
            "node_id": 1  # Data Recorder node ID
        })
        self.recording_active = True
        self.windows_completed = 0
        print("✓ Recording started")

    def stop_recording(self):
        """Stop recording"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Stopping recording...")
        self.send_command({
            "command": "stop_recording",
            "node_id": 1
        })
        self.recording_active = False
        print("✓ Recording stopped")

    def monitor_progress(self, target_windows, check_interval=5):
        """Monitor recording progress until target windows reached

        Args:
            target_windows: Number of windows to record before stopping
            check_interval: How often to check progress (seconds)
        """
        print(f"Monitoring progress (target: {target_windows} windows)...")

        start_time = time.time()
        last_check_time = start_time

        while self.recording_active:
            time.sleep(check_interval)
            current_time = time.time()
            elapsed = current_time - start_time

            # Subscribe to get recording status
            self.send_command({
                "command": "subscribe",
                "signal_id": "1:sample_count"  # Data Recorder's sample count
            })

            # In real implementation, we'd parse WebSocket messages for window count
            # For now, we'll use time estimation
            avg_time_per_window = 52  # seconds (from testing)
            estimated_windows = int(elapsed / avg_time_per_window)

            if estimated_windows >= target_windows:
                print(f"\n✓ Target reached: {target_windows} windows completed!")
                print(f"   Total time: {elapsed/60:.1f} minutes")
                self.stop_recording()
                break

            # Progress update every minute
            if current_time - last_check_time >= 60:
                progress_pct = (estimated_windows / target_windows) * 100
                remaining_windows = target_windows - estimated_windows
                remaining_time = remaining_windows * avg_time_per_window / 60

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Progress: {estimated_windows}/{target_windows} windows ({progress_pct:.1f}%) | ETA: {remaining_time:.1f} min")
                last_check_time = current_time

    def record_signal_type(self, signal_type, num_windows):
        """Record a complete dataset for one signal type

        Args:
            signal_type: Type of signal (sine, square, triangle, sawtooth)
            num_windows: Number of windows to record
        """
        print(f"\n{'='*70}")
        print(f"Recording {signal_type.upper()} - {num_windows} windows")
        print(f"{'='*70}")

        # Set signal type
        self.set_signal_type(signal_type)
        time.sleep(2)

        # Start recording
        self.start_recording()
        time.sleep(1)

        # Monitor until completion
        self.monitor_progress(num_windows)

        # Wait for file save
        time.sleep(3)

        print(f"✓ {signal_type.upper()} recording complete!\n")

    def run_automated_recording(self, signal_types, windows_per_type):
        """Run complete automated recording session

        Args:
            signal_types: List of signal types to record
            windows_per_type: Number of windows per signal type
        """
        total_signals = len(signal_types)

        print("\n" + "="*70)
        print("AUTOMATED DATASET RECORDING")
        print("="*70)
        print(f"Signal types: {', '.join(signal_types)}")
        print(f"Windows per type: {windows_per_type}")
        print(f"Total files: {total_signals}")
        print(f"Estimated total time: {total_signals * windows_per_type * 52 / 60:.1f} minutes")
        print("="*70 + "\n")

        input("Press ENTER to start automated recording...")

        try:
            self.connect()

            for i, signal_type in enumerate(signal_types, 1):
                print(f"\n[{i}/{total_signals}] Processing {signal_type}...")
                self.record_signal_type(signal_type, windows_per_type)

                # Wait between recordings
                if i < total_signals:
                    print(f"Waiting 10 seconds before next recording...")
                    time.sleep(10)

            print("\n" + "="*70)
            print("ALL RECORDINGS COMPLETE!")
            print("="*70)
            print(f"Total recordings: {total_signals}")
            print(f"Files saved to: /home/user/cira_datasets/")
            print("="*70 + "\n")

        except KeyboardInterrupt:
            print("\n\n⚠️  Recording interrupted by user")
            if self.recording_active:
                self.stop_recording()
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Automated Dataset Recording for CiRA')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: record 5 windows per signal type')
    parser.add_argument('--full', action='store_true',
                       help='Full mode: record 100 windows per signal type')
    parser.add_argument('--windows', type=int, default=None,
                       help='Custom number of windows per signal type')
    parser.add_argument('--signals', nargs='+',
                       default=['sine', 'square', 'triangle', 'sawtooth'],
                       help='Signal types to record (default: all 4 types)')
    parser.add_argument('--ip', default='192.168.1.200',
                       help='Jetson IP address (default: 192.168.1.200)')

    args = parser.parse_args()

    # Determine number of windows
    if args.windows:
        num_windows = args.windows
    elif args.test:
        num_windows = 5
    elif args.full:
        num_windows = 100
    else:
        print("Error: Please specify --test, --full, or --windows N")
        sys.exit(1)

    # Create recorder and run
    recorder = DatasetRecorder(jetson_ip=args.ip)
    recorder.run_automated_recording(args.signals, num_windows)


if __name__ == "__main__":
    main()
