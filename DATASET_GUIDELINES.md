# Dataset Guidelines for CiRA FES

## Overview
This document provides guidelines for preparing datasets to work optimally with CiRA FES, particularly for Edge Impulse JSON/CBOR formats.

## Known Issues

### Issue: Source File Display Confusion with Mixed-Label Files

**Problem:**
When viewing windows in the Preview tab with class filtering enabled, users may see confusing source file information. For example:
- Filter set to: `idle`
- Window shows: `Window 1/17803 - idle | File: grind.1.json`

This appears contradictory but is actually correct behavior.

**Root Cause:**
Some Edge Impulse datasets (e.g., Coffee Machine dataset) contain **continuous recordings** where the class label changes over time within a single file. For example, `grind.1.json` might contain:
- Samples 0-1000: `idle` (before grinding starts)
- Samples 1000-5000: `grind` (actual grinding activity)
- Samples 5000-6000: `idle` (after grinding stops)

When windowing this data:
- Windows from samples 0-1000 are labeled `idle` but came from `grind.1.json`
- Windows from samples 1000-5000 are labeled `grind` from `grind.1.json`
- Windows from samples 5000-6000 are labeled `idle` from `grind.1.json`

**Impact:**
- Source file tracking is **technically correct** but may confuse users
- Users expect files named `idle.X.json` to only contain `idle` class data
- Class filtering works correctly, but source file display seems wrong

## Recommended Dataset Format

### Option 1: Single-Label Files (Recommended)
Each file should contain data from **only one class label**. This provides the clearest user experience.

**Example:**
```
training/
├── idle.1.json          # Contains ONLY idle data
├── idle.2.json          # Contains ONLY idle data
├── grind.1.json         # Contains ONLY grind data
└── grind.2.json         # Contains ONLY grind data
```

**Advantages:**
- Source file information is intuitive and clear
- Easy to understand which file contains which class
- No confusion when viewing filtered windows

### Option 2: Mixed-Label Files (Current Coffee Machine Dataset)
Files contain continuous recordings with multiple class labels over time.

**Example:**
```
training/
├── grind.1.json         # Contains idle + grind + idle segments
├── idle.1.json          # May contain only idle, or mixed segments
└── idle.2.json          # May contain only idle, or mixed segments
```

**Advantages:**
- Represents real-world continuous recordings
- Preserves temporal context between classes

**Disadvantages:**
- Source file display appears confusing to users
- File names don't accurately represent content
- Harder to debug data issues

## How to Prepare Your Dataset

### For Edge Impulse JSON Format

If you have mixed-label files and want to convert to single-label files:

1. **Load the JSON file** and parse the label information
2. **Segment by label** - split the data into separate chunks based on label changes
3. **Save each segment** as a new file named `{label}.{number}.json`
4. **Verify** that each file contains only one class label

### Example Restructuring Script

See `Dataset/restructure_coffee_dataset.py` for an example of how to convert mixed-label files to single-label format.

## Future Improvements

Potential solutions to improve user experience with mixed-label files:

1. **Add warning indicator** when source file contains mixed labels
2. **Display format:** `Source: grind.1.json (contains multiple classes)`
3. **Configuration option** to hide source file when class doesn't match filename
4. **Validation tool** to check dataset format and warn about mixed-label files

## Related Files

- `/Dataset/Coffee-Machine-Cleaned/` - Example of restructured single-label dataset
- `/Dataset/restructure_coffee_dataset.py` - Script to restructure datasets
- `/DATASET_RESTRUCTURING_SUMMARY.md` - Details about Coffee Machine dataset restructuring

## Summary

**For the best user experience:**
- Use **single-label files** where each file contains data from only one class
- Name files according to their class: `{classname}.{number}.{ext}`
- Keep source files focused and easy to understand

**If using mixed-label files:**
- Be aware that source file display may appear confusing
- Understand this is correct behavior showing actual data provenance
- Consider restructuring for clearer user experience
