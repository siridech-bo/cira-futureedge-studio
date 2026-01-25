# Automated Dataset Recording Guide

## Quick Start

### Test Mode (5 windows per signal - ~4 minutes each)
```bash
python simple_automated_recording.py --test
```

### Full Mode (100 windows per signal - ~87 minutes each)
```bash
python simple_automated_recording.py --full
```

### Custom Windows
```bash
python simple_automated_recording.py --windows 10
```

---

## How It Works

The script **monitors** the recording progress by watching the runtime logs. You still use the dashboard to control recording, but the script:
- ✅ Tracks window completion progress
- ✅ Shows estimated time remaining
- ✅ Notifies when target reached
- ✅ Guides you through multi-signal recording

---

## Step-by-Step: Recording All 4 Signal Types

### 1. Start the monitoring script
```bash
cd "D:\CiRA FES"
python simple_automated_recording.py --test
```

### 2. Follow the prompts

**For FIRST signal (sine):**
1. Open dashboard: http://192.168.1.200:8083
2. Verify signal type is "sine" in Pipeline Builder
3. Click **"Start Recording"** button
4. Script will monitor progress automatically

**When script shows "TARGET REACHED":**
1. Click **"Stop"** button in dashboard
2. File will be saved automatically
3. Script waits 10 seconds

**For NEXT signals (square, triangle, sawtooth):**
1. Script prompts you to change signal type
2. In Pipeline Builder: Select Signal Generator node
3. Change `signal_type` to next type (e.g., "square")
4. Click **"Deploy"** to update
5. Press ENTER in script
6. Click **"Start Recording"** in dashboard
7. Repeat

---

## Recording Session Examples

### Quick Test (20 minutes total)
```bash
python simple_automated_recording.py --test
```
- 5 windows × 4 signals = 20 windows total
- ~52 seconds per window = ~17 minutes
- Good for verifying the dataset format

### Full Dataset (6 hours total)
```bash
python simple_automated_recording.py --full
```
- 100 windows × 4 signals = 400 windows total
- ~52 seconds per window = ~5.8 hours
- Ready for TimesNet training

### Single Signal Test
```bash
python simple_automated_recording.py --windows 10 --signals square
```
- Only records square wave
- 10 windows = ~9 minutes

---

## Output Progress Display

```
[20:45:32] Window 5/100 (5.0%) | Elapsed: 4.3min | ETA: 82.1min
[20:46:24] Window 6/100 (6.0%) | Elapsed: 5.2min | ETA: 81.3min
...
[22:12:15] Window 100/100 (100.0%) | Elapsed: 86.7min | ETA: 0.0min

======================================================================
✓ TARGET REACHED: 100 windows completed!
  Total time: 86.7 minutes
  Avg time per window: 52.0 seconds
======================================================================

Click 'Stop' button in dashboard to save the file.
```

---

## Troubleshooting

### Script shows "Waiting for recording to start..."
- Make sure you clicked **"Start Recording"** in dashboard
- Check that Signal Generator is running (green LED)

### Recording stopped prematurely
- Script will ask if you want to retry
- Check Jetson didn't run out of disk space
- Check runtime didn't crash

### Window count not updating
- Refresh the script's connection
- Check `/api/logs` endpoint is accessible
- Verify recording is actually progressing in dashboard

---

## File Naming

Files are saved as:
```
/home/user/cira_datasets/[signal_type].[timestamp].cbor
```

Examples:
- `square.1.cbor.69760f8a.user-desktop.cbor`
- `sine.2.cbor.12345abc.user-desktop.cbor`

Download them from the dashboard or via SCP:
```bash
scp user@192.168.1.200:/home/user/cira_datasets/*.cbor "D:\CiRA FES\Dataset\"
```

---

## Performance Tips

1. **Close extra browser tabs** - Reduces HTTP polling overhead
2. **Run overnight** - Full dataset takes ~6 hours
3. **Monitor first recording** - Verify timing before leaving it
4. **Check disk space** - Each file is ~400KB

---

## Advanced: Modifying Signal Types

If you want to add more signal types or change the order:

```bash
python simple_automated_recording.py --test --signals sine triangle square
```

Only records sine, triangle, and square (skips sawtooth).

---

## Next Steps After Recording

1. **Download files** from Jetson to your PC
2. **Verify dataset** with verification script
3. **Train TimesNet** model in CiRA Studio
4. **Deploy model** back to Jetson for real-time inference

---

## Questions?

- Runtime not responding? Check `ssh user@192.168.1.200` and restart runtime
- Slow performance? Close extra browser tabs and HTTP connections
- Script errors? Check Python websocket library: `pip install websocket-client requests`

