# TimesNet - Visual Testing Guide with Expected Screenshots

**Purpose:** Visual reference guide for UI testing
**Time:** Follow along with testing guide
**Format:** Descriptions of what you should see at each step

---

## 📸 Screenshot Reference Guide

---

## STEP 1: Pipeline Mode Selector (Data Sources Panel)

### What You Should See:

```
┌─────────────────────────────────────────────────────────┐
│ Data Sources Panel                                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Pipeline Mode                                           │
│ ┌─────────────────────┬─────────────────────┐          │
│ │  Traditional ML     │   Deep Learning     │          │  ← Segmented button
│ └─────────────────────┴─────────────────────┘          │
│                                                          │
│ ℹ️ ML: Feature-based classification                     │  ← Info label
│ ⚠️ Mode can be locked after windowing                   │  ← Warning label
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Visual Indicators:**
- Segmented button with 2 sections
- Currently selected section has highlighted/darker background
- Info label changes based on selection:
  - ML: "ML: Feature-based classification"
  - DL: "DL: Neural network learns features automatically"

---

## STEP 2: Deep Learning Mode Selected

### What You Should See:

```
┌─────────────────────────────────────────────────────────┐
│ Data Sources Panel                                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Pipeline Mode                                           │
│ ┌─────────────────────┬─────────────────────┐          │
│ │  Traditional ML     │   Deep Learning █   │  ← DL highlighted
│ └─────────────────────┴─────────────────────┘          │
│                                                          │
│ ℹ️ DL: Neural network learns features automatically     │
│ ⚠️ Mode can be locked after windowing                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Key Visual Changes:**
- "Deep Learning" section has darker/highlighted background
- "Traditional ML" section has normal/lighter background
- Info text changed to mention "Neural network"

---

## STEP 3: After Windows Created - Mode LOCKED

### What You Should See:

```
┌─────────────────────────────────────────────────────────┐
│ Data Sources Panel                                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Pipeline Mode                                           │
│ ┌─────────────────────┬─────────────────────┐          │
│ │  Traditional ML  ░░ │ Deep Learning █  ░░ │  ← GRAYED/DISABLED
│ └─────────────────────┴─────────────────────┘          │
│                                                          │
│ ℹ️ DL: Neural network learns features automatically     │
│ 🔒 Mode locked: Deep Learning                           │  ← LOCKED warning
│                                                          │
│ Windowing Configuration                                 │
│ Created 10 windows from data                            │  ← Success message
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Critical Visual Indicators:**
- Segmented button appears grayed out / semi-transparent
- Lock icon (🔒) in warning message
- "Mode locked: Deep Learning" text replaces "can be locked"
- Button may show disabled cursor when hovering

---

## STEP 4: Sidebar Navigation - DL Mode

### What You Should See:

```
╔════════════════════════════════╗
║ CiRA FutureEdge Studio         ║
╠════════════════════════════════╣
║                                ║
║ 📊 Data Sources        ✓       ║  ← Active (green/highlighted)
║                                ║
║ 📈 Feature Extraction   ⊘      ║  ← GRAYED OUT (dim text)
║                                ║
║ 🔍 Feature Filtering    ⊘      ║  ← GRAYED OUT (dim text)
║                                ║
║ 🤖 LLM Selection        ⊘      ║  ← GRAYED OUT (dim text)
║                                ║
║ 🧠 Training            ✓       ║  ← Active (normal text)
║                                ║
║ ⚙️ Embedded Code       ✓       ║  ← Active (renamed from DSP)
║                                ║
║ 🔨 Build Firmware      ✓       ║  ← Active (normal text)
║                                ║
╚════════════════════════════════╝
```

**Visual Characteristics:**
- **Grayed tabs:** Text color is dim/light gray, icon may be faded
- **Active tabs:** Normal text color (white/black), bright icons
- **Current tab:** Has background highlight (green/blue)
- **Disabled cursor:** Hovering over grayed tabs shows "not-allowed" cursor

---

## STEP 5: Educational Dialog When Clicking Grayed Tab

### What You Should See:

```
┌──────────────────────────────────────────────────────┐
│ ℹ️ Deep Learning Mode                        ╳       │
├──────────────────────────────────────────────────────┤
│                                                       │
│  Feature Extraction is not needed for Deep           │
│  Learning.                                           │
│                                                       │
│  TimesNet learns features automatically from raw     │
│  time series data.                                   │
│                                                       │
│                                                       │
│                         ┌──────────┐                 │
│                         │    OK    │                 │
│                         └──────────┘                 │
│                                                       │
└──────────────────────────────────────────────────────┘
```

**Dialog Elements:**
- Title: "Deep Learning Mode" with info icon (ℹ️)
- Clear explanation of why tab is disabled
- Single "OK" button to close
- Modal overlay (background dimmed)

---

## STEP 6: Training Panel - Algorithm Tab (DL Mode)

### What You Should See:

```
┌─────────────────────────────────────────────────────────┐
│ Training Panel                                          │
│ ┌─────────────┬──────────────┬────────────┐           │
│ │  Algorithm  │   Training   │ Evaluation │           │
│ └─────────────┴──────────────┴────────────┘           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Model Architecture                                      │
│ Architecture: TimesNet                                  │
│ Description: Temporal 2D-variation modeling             │
│                                                          │
│ Model Complexity                                        │
│ ┌──────────┬────────────┬────────────────┐             │
│ │ Minimal  │ Efficient  │ Comprehensive  │             │
│ └──────────┴────────────┴────────────────┘             │
│                                                          │
│ ℹ️ Efficient (recommended):                             │
│    ~200K parameters, balanced speed/accuracy           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**What You Should NOT See:**
- ❌ Algorithm dropdown (Isolation Forest, Random Forest, etc.)
- ❌ Contamination factor slider
- ❌ Any sklearn/PyOD references

**Key Features:**
- "TimesNet" is displayed (not selectable)
- 3-option complexity selector
- Info text explaining selected complexity
- Clean, simple interface

---

## STEP 7: Training Panel - Training Tab (DL Mode)

### What You Should See:

```
┌─────────────────────────────────────────────────────────┐
│ Training Panel                                          │
│ ┌────────────┬─────────────┬────────────┐             │
│ │ Algorithm  │  Training █ │ Evaluation │             │
│ └────────────┴─────────────┴────────────┘             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Training Configuration                                  │
│                                                          │
│ Epochs: [   50    ]                                     │  ← Number entry
│                                                          │
│ Batch Size: [ 32  ▼]                                    │  ← Dropdown
│                                                          │
│ Learning Rate: [ 0.001  ]                               │  ← Decimal entry
│                                                          │
│                                                          │
│         ┌────────────────────┐                          │
│         │  Start Training    │                          │  ← Big button
│         └────────────────────┘                          │
│                                                          │
│ Training Log                                            │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Training timesnet deep learning model              │ │
│ │ Windows shape: (10, 100, 3)                        │ │
│ │ 🖥️  Training Device: CPU (10 threads)              │ │  ← Device info
│ │ Model has 187,234 parameters                       │ │
│ │ Starting training for 50 epochs...                 │ │
│ │ Epoch 1/50: [███░░░░░░░] 30% | loss=1.234         │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Critical Element:**
- **🖥️ Training Device:** line MUST appear in log
- Shows "GPU: [name]" or "CPU (N threads)"
- This is one of the 3 main requirements!

---

## STEP 8: Training in Progress

### What You Should See in Log:

```
┌────────────────────────────────────────────────────┐
│ Training Log                                       │
├────────────────────────────────────────────────────┤
│ Training timesnet deep learning model              │
│ Windows shape: (10, 100, 3)                        │
│ Detected 4 classes: ['normal', 'anomaly_A', ...]   │
│ Auto-detected and using CPU (10 threads)           │  ← Auto-detection
│ 🖥️  Training Device: CPU (10 threads)              │  ← Report to user
│ Model has 187,234 parameters                       │
│ Starting training for 50 epochs...                 │
│                                                     │
│ Epoch 1/50: 100%|████████| 2/2 [00:01, 1.2it/s]   │  ← Progress bar
│ Epoch 1/50 - Train Loss: 1.3234, Train Acc: 0.45, │
│              Val Loss: 1.2876, Val Acc: 0.50       │
│                                                     │
│ Epoch 2/50: 100%|████████| 2/2 [00:01, 1.3it/s]   │
│ Epoch 2/50 - Train Loss: 1.2456, Train Acc: 0.52, │
│              Val Loss: 1.1876, Val Acc: 0.55       │
│                                                     │
│ ... (epochs 3-49) ...                              │
│                                                     │
│ Epoch 50/50: 100%|███████| 2/2 [00:01, 1.5it/s]   │
│ Epoch 50/50 - Train Loss: 0.2123, Train Acc: 0.95,│
│               Val Loss: 0.3456, Val Acc: 0.89      │
│                                                     │
│ Training Results - Accuracy: 0.890, Precision:     │
│ 0.885, Recall: 0.890, F1: 0.887                    │
│                                                     │
│ Per-class F1 scores:                               │
│   normal: 0.950                                    │
│   anomaly_A: 0.870                                 │
│   anomaly_B: 0.860                                 │
│   anomaly_C: 0.870                                 │
│                                                     │
│ Model saved to .../timesnet_model.pth              │
│ Label encoder saved to .../timesnet_encoder.pkl    │
│ ONNX model exported to .../timesnet_model.onnx     │  ← CRITICAL!
│ Results saved to .../timesnet_results.json         │
│                                                     │
│ ✓ Training completed successfully                  │
└────────────────────────────────────────────────────┘
```

**Key Visual Elements:**
- Progress bars showing epoch completion
- Loss and accuracy improving over time
- **ONNX export message** (requirement #2!)
- Clear completion message

---

## STEP 9: Evaluation Tab - Results Display

### What You Should See:

```
┌─────────────────────────────────────────────────────────┐
│ Training Panel                                          │
│ ┌────────────┬────────────┬──────────────┐            │
│ │ Algorithm  │  Training  │ Evaluation █ │            │
│ └────────────┴────────────┴──────────────┘            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Model Information                                       │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Algorithm:       TimesNet                          │ │
│ │ Device Used:     CPU (10 threads)                  │ │  ← Shows device!
│ │ Parameters:      187,234                           │ │
│ │ Complexity:      efficient                         │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ Performance Metrics                                     │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Accuracy:        0.890 (89.0%)                     │ │
│ │ Precision:       0.885 (88.5%)                     │ │
│ │ Recall:          0.890 (89.0%)                     │ │
│ │ F1 Score:        0.887 (88.7%)                     │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ Per-Class Metrics                                       │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Class       │ Precision │ Recall │ F1    │ Support│ │
│ │─────────────┼───────────┼────────┼───────┼────────│ │
│ │ normal      │ 0.960     │ 0.940  │ 0.950 │   50   │ │
│ │ anomaly_A   │ 0.850     │ 0.890  │ 0.870 │   25   │ │
│ │ anomaly_B   │ 0.840     │ 0.880  │ 0.860 │   25   │ │
│ │ anomaly_C   │ 0.890     │ 0.850  │ 0.870 │   30   │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
│ Saved Files                                             │
│ ┌────────────────────────────────────────────────────┐ │
│ │ Model Path:    .../timesnet_model.pth              │ │
│ │ Encoder Path:  .../timesnet_encoder.pkl            │ │
│ │ ONNX Path:     .../timesnet_model.onnx             │ │  ← CRITICAL!
│ │ Results Path:  .../timesnet_results.json           │ │
│ └────────────────────────────────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Critical Visual Checks:**
1. **"Device Used"** field shows correct device (requirement #1)
2. **"ONNX Path"** field is present and shows path (requirement #2)
3. All metrics are displayed with reasonable values (0.0-1.0)
4. Per-class table shows all classes from your data

---

## STEP 10: File Explorer - Model Files

### What You Should See:

```
📁 projects/
  └─ 📁 test_dl_project/
      └─ 📁 models/
          ├─ 📄 timesnet_model.pth          (200 KB - 2 MB)
          ├─ 📄 timesnet_encoder.pkl        (1-5 KB)
          ├─ 📄 timesnet_model.onnx         (200 KB - 2 MB)  ← CRITICAL!
          └─ 📄 timesnet_results.json       (2-5 KB)
```

**Visual Verification:**
- All 4 files present
- File sizes > 0 bytes
- Timestamps are recent (just created)
- **ONNX file** is present (requirement #2)

---

## STEP 11: Sidebar Navigation - Embedded Code Tab

### What You Should See:

```
╔════════════════════════════════╗
║ CiRA FutureEdge Studio         ║
╠════════════════════════════════╣
║                                ║
║ 📊 Data Sources        ✓       ║
║ 📈 Feature Extraction   ⊘      ║
║ 🔍 Feature Filtering    ⊘      ║
║ 🤖 LLM Selection        ⊘      ║
║ 🧠 Training            ✓       ║
║                                ║
║ ⚙️ Embedded Code       ✓       ║  ← NEW NAME (not "DSP")
║                                ║
║ 🔨 Build Firmware      ✓       ║
║                                ║
╚════════════════════════════════╝
```

**Critical Check:**
- Tab is labeled **"Embedded Code Generation"**
- NOT "DSP Generation"
- This verifies requirement #3!

---

## STEP 12: Traditional ML Mode (Comparison)

### What You Should See (for comparison):

**Sidebar in ML Mode:**
```
╔════════════════════════════════╗
║ CiRA FutureEdge Studio         ║
╠════════════════════════════════╣
║ 📊 Data Sources        ✓       ║
║ 📈 Feature Extraction  ✓       ║  ← ENABLED (not grayed)
║ 🔍 Feature Filtering   ✓       ║  ← ENABLED
║ 🤖 LLM Selection       ✓       ║  ← ENABLED
║ 🧠 Training            ✓       ║
║ ⚙️ Embedded Code       ✓       ║
║ 🔨 Build Firmware      ✓       ║
╚════════════════════════════════╝
```

**Training Panel in ML Mode:**
```
┌─────────────────────────────────────────────────────────┐
│ Algorithm Tab                                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Classification Algorithm                                │
│ ┌────────────────────────────────────────┐             │
│ │ Random Forest                      ▼   │  ← Dropdown │
│ └────────────────────────────────────────┘             │
│ (Isolation Forest, One-Class SVM, etc.)                │
│                                                          │
│ Contamination Factor: [0.1] ━━━━━━━━━━━━━ 0.1          │  ← Slider
│                                                          │
└─────────────────────────────────────────────────────────┘
```

**Comparison:**
- ML mode shows dropdown with sklearn algorithms
- ML mode shows contamination slider
- ML mode does NOT show TimesNet complexity selector
- All tabs are enabled in ML mode

---

## 🎨 Color/Style Reference

### Navigation States
- **Active Tab:** Green/blue highlight background, white text
- **Inactive Tab:** Transparent background, normal text color
- **Grayed Tab:** Dim text (gray #888), faded icon, disabled cursor
- **Hover (enabled):** Slight background color change
- **Hover (disabled):** No visual change, "not-allowed" cursor

### Pipeline Mode Selector
- **Selected:** Darker/highlighted background, bolder text
- **Not Selected:** Lighter background, normal text
- **Locked (disabled):** Semi-transparent, grayed text, no hover effect

### Status Messages
- **Info (ℹ️):** Blue icon, informational text
- **Warning (⚠️):** Yellow/orange icon, warning text
- **Lock (🔒):** Red/orange icon, status text
- **Success (✓):** Green icon, success text

---

## 📊 Visual Checklist

Use this to verify visual elements during testing:

### Data Sources Panel
- [ ] Pipeline mode selector visible
- [ ] Two buttons: "Traditional ML" and "Deep Learning"
- [ ] Info label changes when mode changes
- [ ] Warning label shows before locking
- [ ] Lock icon (🔒) appears after windowing
- [ ] Selector becomes disabled/grayed after locking

### Navigation Sidebar
- [ ] 7 tabs total visible
- [ ] In DL mode: 3 tabs grayed (Features, Filtering, LLM)
- [ ] In DL mode: 4 tabs enabled (Data, Training, Code, Build)
- [ ] "Embedded Code Generation" name visible (not "DSP")
- [ ] Clicking grayed tab shows educational dialog

### Training Panel - DL Mode
- [ ] "TimesNet" architecture displayed
- [ ] Complexity selector with 3 options visible
- [ ] Epochs field visible (number entry)
- [ ] Batch Size dropdown visible
- [ ] Learning Rate field visible
- [ ] NO sklearn algorithm dropdown
- [ ] NO contamination slider

### Training Log
- [ ] Device detection message visible (🖥️)
- [ ] Shows "GPU: ..." or "CPU (...)"
- [ ] Epoch progress bars visible
- [ ] Loss/accuracy values updating
- [ ] ONNX export message appears
- [ ] Success message at end

### Evaluation Tab
- [ ] "Device Used" field shows device
- [ ] "ONNX Path" field shows path
- [ ] Metrics displayed (accuracy, precision, recall, F1)
- [ ] Per-class metrics table visible
- [ ] All classes listed in table

---

## 🎯 Quick Visual Verification (30 seconds)

**Fast check for all 3 requirements:**

1. **Look at sidebar:**
   - ✅ Says "Embedded Code Generation" (requirement #3)

2. **Open Evaluation tab:**
   - ✅ "Device Used" field shows "GPU:..." or "CPU..." (requirement #1)
   - ✅ "ONNX Path" field shows path to .onnx file (requirement #2)

**If all 3 visible → All requirements met! ✅**

---

**Last Updated:** 2025-12-14
**For:** Visual UI verification during testing
