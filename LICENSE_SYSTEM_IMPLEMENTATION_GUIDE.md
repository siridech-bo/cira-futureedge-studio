# License System Implementation Guide
## CiRA FutureEdge Studio - License Management

---

## 🎯 NEW: FREE Tier Trial Usage

**Update (2025-12-15)**: The license system now includes trial limits for FREE tier users!

**Trial Limits**:
- 🧠 **Deep Learning (TimesNet)**: 10 training sessions
- 🤖 **LLM Feature Selection**: 10 analyses
- ✅ **ML Algorithms**: Unlimited (always free)

**Benefits**:
- Users can try premium features before buying
- Usage indicators show remaining trials
- Clear upgrade prompts when limit reached
- Seamless experience for paid users (unlimited)

👉 See [FREE_TIER_TRIAL_USAGE.md](FREE_TIER_TRIAL_USAGE.md) for complete details!

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [File Distribution](#file-distribution)
4. [Security Model](#security-model)
5. [Workflow](#workflow)
6. [Implementation Status](#implementation-status)
7. [Next Steps](#next-steps)

---

## 🔍 Overview

### What's INCLUDED in the Application (Customer Side):

✅ **License Validator & Manager** (`core/license_manager.py`)
- Built INTO the CiRA Studio application
- Runs when the app starts
- Validates license keys entered by users
- Checks features when user tries to use them
- Stores activated license locally (encrypted)

✅ **License Data Structures** (`core/license.py`)
- License tier definitions (FREE, PRO, ENTERPRISE)
- Feature flags and limits
- License status tracking

✅ **User Activation UI** (Settings → License tab)
- Part of the CiRA Studio UI
- User enters license key
- App validates and activates
- Shows current license status and features

### What's SEPARATE (Vendor Side Only):

❌ **License Key Generator** (`tools/license_generator.py`)
- **This is YOUR tool** (the software vendor/developer)
- **NOT distributed** to customers
- You run it to generate license keys
- You give/sell keys to customers
- Kept secret and secure on your system

---

## 📊 Architecture - How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  VENDOR SIDE (You - Software Developer)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: Customer purchases PRO license                     │
│                                                              │
│  Step 2: You run the generator tool:                        │
│    $ python tools/license_generator.py \                    │
│             --tier PRO \                                     │
│             --expiry-days 365 \                              │
│             --name "Customer Name"                           │
│                                                              │
│  Step 3: Tool generates key:                                │
│    CF3A-9121-02C9-003F-AC84                                 │
│                                                              │
│  Step 4: You send key to customer via email                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘

                         ⬇️ Email/Delivery

┌─────────────────────────────────────────────────────────────┐
│  CUSTOMER SIDE (End User - CiRA Studio App)                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: Opens CiRA Studio application                      │
│                                                              │
│  Step 2: Goes to: Settings → License tab                    │
│                                                              │
│  Step 3: Enters license key:                                │
│    CF3A-9121-02C9-003F-AC84                                 │
│                                                              │
│  Step 4: Clicks "Activate License" button                   │
│                                                              │
│  App validates (offline - no internet required):            │
│    ✓ Checksum correct?                                      │
│    ✓ Product code matches?                                  │
│    ✓ Not expired?                                           │
│    ✓ Tier recognized?                                       │
│                                                              │
│  Step 5: ✅ License Activated Successfully!                  │
│                                                              │
│  User now has PRO features:                                 │
│    ✓ Deep Learning (TimesNet)                               │
│    ✓ ONNX Export                                            │
│    ✓ LLM Feature Selection                                  │
│    ✓ Unlimited Projects & Samples                           │
│                                                              │
│  License stored encrypted at:                               │
│    Windows: %APPDATA%\CiRA Studio\license.dat               │
│    Linux/Mac: ~/.local/share/CiRA Studio/license.dat        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 File Distribution

### Files Distributed to Customers (Included in App):

```
CiRA FutureEdge Studio/
├── core/
│   ├── license.py              ✅ INCLUDE - License data structures
│   ├── license_manager.py      ✅ INCLUDE - Validation logic
│   ├── config.py
│   ├── project.py
│   └── ...
├── ui/
│   ├── settings_dialog.py      ✅ INCLUDE - With License tab
│   ├── main_window.py
│   └── ...
├── main.py                      ✅ INCLUDE - App entry point
└── README.md
```

### Files Kept on YOUR Server/Computer (DO NOT DISTRIBUTE):

```
Your Development Environment/
├── tools/
│   └── license_generator.py    ❌ DO NOT DISTRIBUTE - Key generator
├── LICENSE_SYSTEM_IMPLEMENTATION_GUIDE.md  ⚠️  Internal docs
└── LICENSE_KEYS_README.md      ⚠️  Internal docs (or give to customers without test keys)
```

**IMPORTANT:**
- Add `tools/license_generator.py` to `.gitignore` if distributing via public repository
- Keep generator on secure, private machine
- Back up generator tool in case of system failure
- Never include test keys in public documentation

---

## 🔐 Security Model

### What Customers Get:

✅ **License Validator** (can check if a key is valid)
- Cannot generate new keys
- Cannot modify the secret salt (hardcoded in compiled app)
- Can only activate keys you provide

### What You Keep Secret:

❌ **License Generator** (can create new keys)
- The SECRET_SALT constant
- The key encoding algorithm
- The checksum calculation method

### How It's Secure:

```python
# In core/license_manager.py (distributed to customers)
SECRET_SALT = "CiRA_FES_2025_SECRET_KEY_v1.0"

# Customer can see this in the code, but:
# ✓ They don't have the generator tool
# ✓ Even if they know the salt, they can't generate valid keys
# ✓ The CRC16 checksum requires the exact encoding algorithm
# ✓ You can change the salt and recompile before distribution
# ✓ Hardware ID binding prevents key sharing
```

### Additional Security Measures (Recommended):

1. **Change SECRET_SALT before release:**
   ```python
   # Make it unique and complex
   SECRET_SALT = "YourCompany_SecretKey_2025_RandomString_XyZ987"
   ```

2. **Compile to executable** (PyInstaller):
   ```bash
   pyinstaller --onefile --windowed main.py
   ```
   - Harder to extract SECRET_SALT from compiled binary
   - Users can't easily read Python source code

3. **Code obfuscation** (optional):
   - Use tools like PyArmor
   - Makes reverse engineering more difficult

4. **Online validation** (future enhancement):
   - Periodic check with license server
   - Detect if too many activations with same key
   - Revoke stolen/shared keys

---

## 💼 Workflow

### Production Setup (Before Release):

#### 1. Change SECRET_SALT (CRITICAL):

**File 1:** `core/license_manager.py` (line 26)
```python
SECRET_SALT = "YourUniqueSecret_2025_XyZ987"  # Change this!
```

**File 2:** `tools/license_generator.py` (line 30)
```python
SECRET_SALT = "YourUniqueSecret_2025_XyZ987"  # Must match!
```

⚠️ **IMPORTANT:** Both must match exactly, or validation will fail!

#### 2. Test Key Generation and Validation:

```bash
# Generate test key
python tools/license_generator.py --tier PRO --expiry-days 365

# Example output: CF3A-9ABC-01D2-003F-7E4F

# Test in app:
# - Open CiRA Studio
# - Settings → License
# - Enter key
# - Verify activation works
```

#### 3. Secure the Generator:

```bash
# Option A: Add to .gitignore
echo "tools/license_generator.py" >> .gitignore

# Option B: Keep in separate private repository
# Option C: Store on encrypted USB drive
```

#### 4. Build Distribution:

```bash
# Clean build
rm -rf dist/ build/

# Compile to executable
pyinstaller --onefile --windowed \
            --name "CiRA Studio" \
            --icon="assets/icon.ico" \
            main.py

# Distribute dist/CiRA Studio.exe
```

---

### Selling Licenses:

#### Scenario 1: Customer Purchases PRO License

```bash
# Generate 1-year PRO license
python tools/license_generator.py \
       --tier PRO \
       --expiry-days 365 \
       --name "John Doe" \
       --count 1

# Output:
# CF3A-9121-02C9-003F-AC84

# Send email to customer:
---
Subject: Your CiRA Studio PRO License Key

Dear John Doe,

Thank you for purchasing CiRA FutureEdge Studio PRO!

Your license key: CF3A-9121-02C9-003F-AC84

To activate:
1. Open CiRA Studio
2. Go to Settings → License
3. Enter your key
4. Click "Activate License"

Valid for: 1 year (expires 2026-12-15)

Features included:
✓ ML Algorithms
✓ Deep Learning (TimesNet)
✓ ONNX Export
✓ LLM Feature Selection
✓ Unlimited Projects & Samples

Support: support@yourcompany.com

Best regards,
CiRA Team
---
```

#### Scenario 2: Enterprise Customer (Multiple Seats)

```bash
# Generate 2-year ENTERPRISE license with 10 seats
python tools/license_generator.py \
       --tier ENTERPRISE \
       --expiry-days 730 \
       --seats 10 \
       --name "Acme Corporation"

# Output:
# CF3A-A5B2-0433-003F-1A9C
```

#### Scenario 3: Trial License

```bash
# Generate 30-day trial (activated on first use)
python tools/license_generator.py \
       --tier PRO \
       --expiry-days -1 \
       --name "Trial User"

# Output:
# CF3A-91FF-FFFF-003F-2D7E
```

#### Scenario 4: Lifetime License

```bash
# Generate lifetime PRO license (no expiry)
python tools/license_generator.py \
       --tier PRO \
       --name "VIP Customer"
# (omit --expiry-days for lifetime)

# Output:
# CF3A-9180-0000-003F-8C3D
```

---

### Decoding Keys (Verification):

```bash
# Decode a key to see what it contains
python tools/license_generator.py \
       --decode "CF3A-9121-02C9-003F-AC84"

# Output:
# ============================================================
# LICENSE KEY DECODER
# ============================================================
#
# Key:           CF3A-9121-02C9-003F-AC84
# Product Code:  CF3A
# Tier:          PRO
# Seats:         1
# Expiry:        2026-12-15
# Checksum:      VALID
#
# Features Enabled:
#   [YES] ML Algorithms
#   [YES] Deep Learning
#   [YES] ONNX Export
#   [YES] LLM Features
#   [YES] Unlimited Projects
#   [YES] Unlimited Samples
```

---

## 📦 Implementation Status

### ✅ Completed (Phase 1):

- [x] License data structures (`core/license.py`)
- [x] License validation logic (`core/license_manager.py`)
- [x] License key generator tool (`tools/license_generator.py`)
- [x] Hardware ID generation
- [x] Encrypted license storage
- [x] CRC16 checksum validation
- [x] Test license keys for all tiers
- [x] Documentation (LICENSE_KEYS_README.md)

### 🔄 In Progress:

- [ ] Settings → License tab UI
- [ ] License activation flow
- [ ] License status display
- [ ] Feature-locked dialogs

### ⏳ Pending (Phase 2):

- [ ] Add license checks to Deep Learning training
- [ ] Add license checks to ONNX export
- [ ] Add license checks to LLM features
- [ ] Add license checks to project creation (FREE tier limit)
- [ ] Add upgrade prompts when features are locked
- [ ] Display license status in main window
- [ ] Add "Upgrade to PRO" marketing messages

---

## 🚀 Next Steps

### Phase 2: UI Integration

1. **Add License Tab to Settings Dialog:**
   ```
   Settings → License
   ├── Current License Status (FREE/PRO/ENTERPRISE)
   ├── Expiry Date / Days Remaining
   ├── License Key Input Field
   ├── Activate License Button
   ├── Features List (enabled/disabled)
   ├── Hardware ID Display
   └── Deactivate License Button
   ```

2. **Feature Gating Implementation:**
   ```python
   # In ui/model_panel.py
   def _start_training_dl(self):
       from core.license_manager import get_license_manager

       if not get_license_manager().has_feature("dl"):
           messagebox.showerror(
               "Feature Locked 🔒",
               "Deep Learning requires Professional license.\n\n"
               "Current tier: FREE\n\n"
               "Upgrade to unlock:\n"
               "  ✓ Deep Learning (TimesNet)\n"
               "  ✓ ONNX Export\n"
               "  ✓ LLM Feature Selection\n"
               "  ✓ Unlimited Projects\n\n"
               "Activate license: Settings → License"
           )
           return

       # Proceed with training...
   ```

3. **License Status in Main Window:**
   ```
   Status Bar: [FREE] CiRA Studio v1.0 | 15 days trial remaining
   ```

4. **Upgrade Prompts:**
   - Show on app startup (FREE tier only)
   - "Start 30-day PRO trial" button
   - "Upgrade to PRO" in locked feature dialogs

---

## 📊 License Tiers Summary

| Feature | FREE | PRO | ENTERPRISE |
|---------|------|-----|------------|
| **ML Algorithms** | ✅ | ✅ | ✅ |
| **Deep Learning** | ❌ | ✅ | ✅ |
| **ONNX Export** | ❌ | ✅ | ✅ |
| **LLM Features** | ❌ | ✅ | ✅ |
| **Max Projects** | 1 | ∞ | ∞ |
| **Max Samples** | 1000 | ∞ | ∞ |
| **Multi-user** | ❌ | ❌ | ✅ |
| **API Access** | ❌ | ❌ | ✅ |
| **Support** | Community | Email | Priority + Phone |
| **Price** | Free | $299/year | Contact Sales |

---

## 🔑 Test License Keys

**⚠️ FOR TESTING ONLY - Change SECRET_SALT before production!**

### FREE Tier (Lifetime)
```
Key: CF3A-81A9-0000-0001-0B28
```
- ML Algorithms only
- Max 1 project, 1000 samples
- Never expires

### PRO Tier (1 year - expires 2026-12-15)
```
Key: CF3A-9121-02C9-003F-AC84
```
- All features enabled
- Unlimited projects and samples
- 1 seat

### ENTERPRISE Tier (2 years - expires 2027-12-15)
```
Key: CF3A-A567-0436-003F-2423
```
- All features enabled
- Unlimited projects and samples
- 5 seats
- Multi-user support

---

## 📝 License Key Format Reference

```
Format: XXXX-XXXX-XXXX-XXXX-XXXX
Example: CF3A-9121-02C9-003F-AC84

┌─────────────────────────────────────────────────────────┐
│ Segment 1: CF3A                                         │
│   Product Code (fixed for CiRA FutureEdge)              │
│   - CF = CiRA FutureEdge                                │
│   - 3A = Version identifier                             │
│                                                          │
│ Segment 2: 9121                                         │
│   License Type + Seats + Random Salt                    │
│   - 9 = Tier (8=FREE, 9=PRO, A=ENTERPRISE)             │
│   - 1 = Seats (1-F in hex = 1-15 seats)                │
│   - 21 = Random salt (prevents pattern detection)      │
│                                                          │
│ Segment 3: 02C9                                         │
│   Expiry Date (days since 2025-01-01)                   │
│   - 0000 = Lifetime license                             │
│   - FFFF = Trial (30 days from activation)             │
│   - 02C9 = 713 days = 2026-12-15                       │
│                                                          │
│ Segment 4: 003F                                         │
│   Feature Flags (16-bit bitmap)                         │
│   - Bit 0 (0x01): ML Algorithms                        │
│   - Bit 1 (0x02): Deep Learning                        │
│   - Bit 2 (0x04): ONNX Export                          │
│   - Bit 3 (0x08): LLM Features                         │
│   - Bit 4 (0x10): Unlimited Projects                   │
│   - Bit 5 (0x20): Unlimited Samples                    │
│   - 003F = 0x3F = All features enabled                 │
│                                                          │
│ Segment 5: AC84                                         │
│   CRC16 Checksum                                        │
│   - Calculated from segments 1-4 + SECRET_SALT         │
│   - Prevents key tampering and forgery                  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🛡️ Security Best Practices

### For Developers:

1. **Change SECRET_SALT immediately** before any public release
2. **Never commit** `tools/license_generator.py` to public repositories
3. **Backup** the generator tool in a secure location
4. **Use strong salts** - random, long, unique
5. **Consider obfuscation** for extra protection
6. **Monitor key usage** - detect if keys are being shared

### For Distribution:

1. **Compile to binary** - harder to reverse engineer
2. **Sign executables** - prove authenticity
3. **Use installers** - professional appearance
4. **Include EULA** - legal protection
5. **Provide support** - help with activation issues

### For Operations:

1. **Track issued keys** - database of customers
2. **Revocation mechanism** - cancel stolen keys (future enhancement)
3. **Usage analytics** - understand customer behavior
4. **Renewal reminders** - email before expiry
5. **Volume discounts** - encourage upgrades

---

## 🆘 Troubleshooting

### Common Issues:

**Issue:** "Invalid checksum" error
- **Cause:** SECRET_SALT mismatch between generator and validator
- **Fix:** Ensure both files use identical SECRET_SALT

**Issue:** "License expired" even though it's valid
- **Cause:** System date is wrong
- **Fix:** Check computer date/time settings

**Issue:** Key won't activate on second computer
- **Cause:** Hardware ID binding
- **Fix:** Deactivate on first computer, then activate on second (or use multi-seat ENTERPRISE)

**Issue:** Generator tool import error
- **Cause:** Wrong Python path
- **Fix:** Run from project root: `python tools/license_generator.py`

---

## 📞 Support

For questions about this implementation:
1. Check `LICENSE_KEYS_README.md` for usage examples
2. Review `core/license_manager.py` for validation logic
3. Examine `tools/license_generator.py` for key generation

---

**Last Updated:** 2025-12-15
**Version:** 1.0
**Status:** Phase 1 Complete - Core Implementation Done

---

## 🎯 Quick Reference

### Generate a Key:
```bash
python tools/license_generator.py --tier PRO --expiry-days 365 --name "Customer"
```

### Decode a Key:
```bash
python tools/license_generator.py --decode "CF3A-XXXX-XXXX-XXXX-XXXX"
```

### Activate in App:
```
Settings → License → Enter Key → Activate License
```

### Check Feature Access:
```python
from core.license_manager import get_license_manager
if get_license_manager().has_feature("dl"):
    # Feature available
```

---

**END OF GUIDE**
