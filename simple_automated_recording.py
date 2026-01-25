#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Automated Dataset Recording Script
Monitors recording progress and notifies when complete
User manually changes signal type between recordings
"""

import requests
import time
import sys
import argparse
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class SimpleRecorder:
    def __init__(self, jetson_ip="192.168.1.200", port=8083):
        self.jetson_ip = jetson_ip
        self.port = port
        self.base_url = f"http://{jetson_ip}:{port}"

    def get_datasets(self):
        """Get list of saved datasets"""
        try:
            response = requests.get(f"{self.base_url}/api/datasets", timeout=5)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def get_logs(self):
        """Get runtime logs"""
        try:
            response = requests.get(f"{self.base_url}/api/logs", timeout=5)
            if response.status_code == 200:
                return response.text
            return ""
        except:
            return ""

    def monitor_recording(self, target_windows, signal_type="unknown"):
        """Monitor recording progress by watching logs

        Args:
            target_windows: Number of windows to wait for
            signal_type: Name of signal being recorded (for display)
        """
        print(f"\n{'='*70}")
        print(f"MONITORING: {signal_type.upper()} - Target: {target_windows} windows")
        print(f"{'='*70}")
        print("Waiting for recording to start...")
        print("(Click 'Start Recording' button in dashboard now)")
        print()

        start_time = time.time()
        last_window_count = 0
        recording_started = False
        completed_windows = 0

        while True:
            time.sleep(5)  # Check every 5 seconds

            # Get logs and look for window completion messages
            logs = self.get_logs()

            # Look for window completion in logs
            for line in logs.split('\n'):
                if "Window" in line and "completed" in line:
                    # Extract window number from log line
                    # Example: "=== [DataRecorder] Window 5/100 completed (class: square, id: 2) ==="
                    try:
                        parts = line.split("Window")[1].split("/")
                        current_window = int(parts[0].strip())
                        if current_window > completed_windows:
                            completed_windows = current_window
                            if not recording_started:
                                recording_started = True
                                print(f"✓ Recording started!\n")

                            # Progress update
                            elapsed = time.time() - start_time
                            progress_pct = (completed_windows / target_windows) * 100
                            avg_time_per_window = elapsed / completed_windows if completed_windows > 0 else 52
                            remaining_windows = target_windows - completed_windows
                            remaining_time = remaining_windows * avg_time_per_window / 60

                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Window {completed_windows}/{target_windows} ({progress_pct:.1f}%) | "
                                  f"Elapsed: {elapsed/60:.1f}min | ETA: {remaining_time:.1f}min")

                            if completed_windows >= target_windows:
                                print(f"\n{'='*70}")
                                print(f"✓ TARGET REACHED: {target_windows} windows completed!")
                                print(f"  Total time: {elapsed/60:.1f} minutes")
                                print(f"  Avg time per window: {avg_time_per_window:.1f} seconds")
                                print(f"{'='*70}\n")
                                print("Click 'Stop' button in dashboard to save the file.")
                                return True
                    except:
                        pass

            # Check if recording stopped prematurely
            if recording_started and "RECORDING STOPPED" in logs:
                if completed_windows < target_windows:
                    print(f"\n⚠️  Recording stopped at {completed_windows}/{target_windows} windows")
                    return False

    def run_multi_signal_recording(self, signal_types, windows_per_type):
        """Guide user through recording multiple signal types

        Args:
            signal_types: List of signal types to record
            windows_per_type: Number of windows per type
        """
        total_files = len(signal_types)

        print("\n" + "="*70)
        print("MULTI-SIGNAL DATASET RECORDING")
        print("="*70)
        print(f"Signal types to record: {', '.join(signal_types)}")
        print(f"Windows per type: {windows_per_type}")
        print(f"Total recordings: {total_files}")
        print(f"Estimated time per recording: {windows_per_type * 52 / 60:.1f} minutes")
        print(f"Estimated total time: {total_files * windows_per_type * 52 / 60:.1f} minutes")
        print("="*70)
        print("\nINSTRUCTIONS:")
        print("1. This script will monitor each recording")
        print("2. You manually start/stop recording via dashboard")
        print("3. Between recordings, change signal type in Pipeline Builder")
        print("4. Script will notify when target windows reached")
        print("="*70 + "\n")

        input("Press ENTER to begin...")

        for i, signal_type in enumerate(signal_types, 1):
            print(f"\n\n{'#'*70}")
            print(f"RECORDING {i}/{total_files}: {signal_type.upper()}")
            print(f"{'#'*70}")

            if i > 1:
                print(f"\n⚠️  SETUP REQUIRED:")
                print(f"   1. Stop previous recording if still running")
                print(f"   2. Change signal type to: {signal_type}")
                print(f"   3. Press ENTER when ready to start {signal_type} recording")
                input("\nReady? Press ENTER...")

            # Monitor this recording
            success = self.monitor_recording(windows_per_type, signal_type)

            if success:
                print(f"✓ {signal_type.upper()} complete")

                if i < total_files:
                    print(f"\nNext: {signal_types[i]}")
                    print("Waiting 10 seconds...")
                    time.sleep(10)
            else:
                print(f"❌ {signal_type.upper()} incomplete")
                retry = input("Retry this signal type? (y/n): ")
                if retry.lower() == 'y':
                    i -= 1  # Retry same signal

        print("\n" + "="*70)
        print("✓ ALL RECORDINGS COMPLETE!")
        print("="*70)
        print(f"Recorded {total_files} signal types")
        print(f"Check files at: http://{self.jetson_ip}:{self.port}")
        print("="*70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Simple Automated Recording Monitor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode - 5 windows each
  python simple_automated_recording.py --test

  # Full mode - 100 windows each
  python simple_automated_recording.py --full

  # Custom - 10 windows each
  python simple_automated_recording.py --windows 10

  # Single signal type
  python simple_automated_recording.py --test --signals square

  # Specific signals only
  python simple_automated_recording.py --full --signals sine square
        """
    )

    parser.add_argument('--test', action='store_true',
                       help='Test mode: 5 windows per signal')
    parser.add_argument('--full', action='store_true',
                       help='Full mode: 100 windows per signal')
    parser.add_argument('--windows', type=int,
                       help='Custom number of windows per signal')
    parser.add_argument('--signals', nargs='+',
                       default=['sine', 'square', 'triangle', 'sawtooth'],
                       help='Signal types to record (default: all 4)')
    parser.add_argument('--ip', default='192.168.1.200',
                       help='Jetson IP (default: 192.168.1.200)')

    args = parser.parse_args()

    # Determine windows count
    if args.windows:
        num_windows = args.windows
    elif args.test:
        num_windows = 5
    elif args.full:
        num_windows = 100
    else:
        print("Error: Specify --test, --full, or --windows N")
        print("Run with --help for examples")
        sys.exit(1)

    # Run recorder
    recorder = SimpleRecorder(jetson_ip=args.ip)
    try:
        recorder.run_multi_signal_recording(args.signals, num_windows)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
