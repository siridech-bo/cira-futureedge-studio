#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fully Automated Overnight Dataset Recording
Records all signal types unattended via REST API control
"""

import requests
import time
import sys
import argparse
import json
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


class OvernightRecorder:
    def __init__(self, jetson_ip="192.168.1.200", port=8083):
        self.jetson_ip = jetson_ip
        self.port = port
        self.base_url = f"http://{jetson_ip}:{port}"

    def start_recording(self, node_id=1):
        """Start recording via WebSocket API"""
        try:
            url = f"{self.base_url}/api/websocket/command"
            payload = {"command": "start_recording", "node_id": node_id}
            response = requests.post(url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False

    def stop_recording(self, node_id=1):
        """Stop recording via WebSocket API"""
        try:
            url = f"{self.base_url}/api/websocket/command"
            payload = {"command": "stop_recording", "node_id": node_id}
            response = requests.post(url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return False

    def set_signal_type(self, signal_type, node_id=3):
        """Prompt user to manually change signal type"""
        print(f"\n⚠️  MANUAL ACTION REQUIRED:")
        print(f"   1. Open Pipeline Builder")
        print(f"   2. Select Signal Generator node")
        print(f"   3. Change 'signal_type' to: {signal_type}")
        print(f"   4. Click 'Save' (do NOT click Setup Device)")
        return True  # User will handle this manually

    def get_window_count(self):
        """Parse logs to get current window count"""
        try:
            response = requests.get(f"{self.base_url}/api/logs", timeout=5)
            if response.status_code != 200:
                return 0

            logs = response.json()
            for log in reversed(logs):
                msg = log.get("message", "")
                if "Window" in msg and "saved" in msg:
                    # Extract window number from "Window 5/100 saved"
                    try:
                        parts = msg.split()
                        for i, part in enumerate(parts):
                            if part == "Window" and i+1 < len(parts):
                                window_str = parts[i+1].split('/')[0]
                                return int(window_str)
                    except:
                        pass
            return 0
        except:
            return 0

    def wait_for_windows(self, target_windows, signal_type, poll_interval=10):
        """Wait until target windows are recorded"""
        print(f"\n{'='*70}")
        print(f"Recording {signal_type.upper()} - Target: {target_windows} windows")
        print(f"{'='*70}")

        last_count = 0
        start_time = time.time()

        while True:
            current_count = self.get_window_count()

            if current_count != last_count:
                elapsed = time.time() - start_time
                if current_count > 0:
                    rate = elapsed / current_count
                    eta = rate * (target_windows - current_count)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Windows: {current_count}/{target_windows} | "
                          f"ETA: {eta/60:.1f} min")
                last_count = current_count

            if current_count >= target_windows:
                print(f"\n✓ Target reached: {current_count} windows")
                return True

            time.sleep(poll_interval)

    def record_signal_type(self, signal_type, num_windows):
        """Record a single signal type"""
        print(f"\n{'#'*70}")
        print(f"RECORDING: {signal_type.upper()}")
        print(f"{'#'*70}")

        # Set signal type
        print(f"Setting signal type to {signal_type}...")
        if not self.set_signal_type(signal_type):
            print("✗ Failed to set signal type")
            return False

        time.sleep(2)  # Wait for signal generator to update

        # Start recording
        print("Starting recording...")
        if not self.start_recording():
            print("✗ Failed to start recording")
            return False

        time.sleep(2)  # Wait for recording to initialize

        # Wait for completion
        success = self.wait_for_windows(num_windows, signal_type)

        # Stop recording
        print("Stopping recording...")
        self.stop_recording()
        time.sleep(2)

        return success

    def run_overnight_batch(self, signal_types, num_windows):
        """Run complete overnight batch recording"""
        total_signals = len(signal_types)

        print("\n" + "="*70)
        print("OVERNIGHT BATCH RECORDING")
        print("="*70)
        print(f"Signal types: {', '.join(signal_types)}")
        print(f"Windows per type: {num_windows}")
        print(f"Total recordings: {total_signals}")
        print(f"Estimated time per recording: {num_windows * 52 / 60:.1f} minutes")
        print(f"Estimated total time: {total_signals * num_windows * 52 / 60:.1f} minutes")
        print("="*70)

        start_time = time.time()
        completed = []
        failed = []

        for i, signal_type in enumerate(signal_types, 1):
            print(f"\n\n[{i}/{total_signals}] Starting {signal_type}...")

            if self.record_signal_type(signal_type, num_windows):
                completed.append(signal_type)
                print(f"✓ {signal_type} completed successfully")
            else:
                failed.append(signal_type)
                print(f"✗ {signal_type} FAILED")

        # Summary
        total_time = (time.time() - start_time) / 60
        print("\n" + "="*70)
        print("BATCH RECORDING COMPLETE")
        print("="*70)
        print(f"Completed: {len(completed)}/{total_signals}")
        print(f"Failed: {len(failed)}/{total_signals}")
        print(f"Total time: {total_time:.1f} minutes")

        if completed:
            print(f"\n✓ Success: {', '.join(completed)}")
        if failed:
            print(f"\n✗ Failed: {', '.join(failed)}")

        print("="*70)


def main():
    parser = argparse.ArgumentParser(description='Automated overnight dataset recording')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: 5 windows per signal (~4 min each)')
    parser.add_argument('--full', action='store_true',
                       help='Full mode: 100 windows per signal (~87 min each)')
    parser.add_argument('--windows', type=int,
                       help='Custom number of windows')
    parser.add_argument('--signals', nargs='+',
                       default=['sine', 'square', 'triangle', 'sawtooth'],
                       help='Signal types to record (default: all)')
    parser.add_argument('--ip', default='192.168.1.200',
                       help='Jetson IP address')

    args = parser.parse_args()

    # Determine window count
    if args.test:
        num_windows = 5
    elif args.full:
        num_windows = 100
    elif args.windows:
        num_windows = args.windows
    else:
        print("Error: Must specify --test, --full, or --windows N")
        sys.exit(1)

    recorder = OvernightRecorder(jetson_ip=args.ip)
    recorder.run_overnight_batch(args.signals, num_windows)


if __name__ == "__main__":
    main()
