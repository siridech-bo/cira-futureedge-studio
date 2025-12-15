# License Key Generator - Standalone Application Prompt

## Overview
Create a standalone Windows desktop application for generating license keys for CiRA FutureEdge Studio. This tool is for **vendor use only** and will NOT be distributed to customers.

## Technical Requirements

### Platform & Framework
- **Language**: Python 3.10+
- **GUI Framework**: CustomTkinter (modern, native-looking UI)
- **OS**: Windows (primary), cross-platform compatible
- **Architecture**: Standalone executable using PyInstaller

### Core Functionality

The generator must create license keys in this format:
```
XXXX-XXXX-XXXX-XXXX-XXXX
```

#### Key Structure (5 segments):

**Segment 1: Product Code** (4 chars)
- Fixed value: `CF3A` (CiRA FutureEdge Studio 3.x, Algorithm)
- Identifies the product

**Segment 2: Tier + Seats + Salt** (4 chars)
- Byte 1: License Tier
  - `8` = FREE
  - `9` = PRO
  - `A` = ENTERPRISE
- Byte 2: Number of seats (hex: 1-F)
- Bytes 3-4: Random salt (2 hex chars)

**Segment 3: Expiry Date** (4 chars)
- `0000` = Lifetime license (never expires)
- `FFFF` = Trial (30 days)
- Otherwise: Days since 2025-01-01 (in hex)
- Example: 365 days from now = calculate days from 2025-01-01

**Segment 4: Feature Flags** (4 chars)
- Bit-encoded features (4 hex chars = 16 bits)
- Bit 0 (0x0001): ML Algorithms
- Bit 1 (0x0002): Deep Learning
- Bit 2 (0x0004): ONNX Export
- Bit 3 (0x0008): LLM Features
- Bit 4 (0x0010): Multi-User
- Bit 5 (0x0020): API Access
- Bits 6-15: Reserved for future features

**Segment 5: Checksum** (4 chars)
- CRC16-CCITT checksum
- Calculated from: segments 1-4 concatenated + SECRET_SALT
- SECRET_SALT: `"CiRA_FES_2025_SECRET_KEY_v1.0"` (MUST match the application!)
- Use Python's `binascii.crc_hqx()` function

### Algorithm Implementation

```python
import binascii
import secrets
from datetime import date, timedelta

SECRET_SALT = "CiRA_FES_2025_SECRET_KEY_v1.0"  # MUST match license_manager.py
PRODUCT_CODE = "CF3A"
EPOCH_DATE = date(2025, 1, 1)

def calculate_checksum(s1, s2, s3, s4):
    """Calculate CRC16 checksum for validation."""
    data = f"{s1}{s2}{s3}{s4}{SECRET_SALT}"
    crc = binascii.crc_hqx(data.encode(), 0xFFFF)
    return f"{crc:04X}"

def generate_license_key(tier, seats, expiry_days, features):
    """
    Generate a license key.

    Args:
        tier: "FREE", "PRO", or "ENTERPRISE"
        seats: 1-15 (number of seats)
        expiry_days: None (lifetime), -1 (trial), or positive int (days from today)
        features: dict with keys: ml, dl, onnx, llm, multi_user, api

    Returns:
        License key string (XXXX-XXXX-XXXX-XXXX-XXXX)
    """
    # Segment 1: Product Code
    seg1 = PRODUCT_CODE

    # Segment 2: Tier + Seats + Random Salt
    tier_map = {"FREE": "8", "PRO": "9", "ENTERPRISE": "A"}
    tier_byte = tier_map[tier]
    seats_byte = f"{seats:X}"
    random_salt = secrets.token_hex(1).upper()
    seg2 = f"{tier_byte}{seats_byte}{random_salt}"

    # Segment 3: Expiry Date
    if expiry_days is None:
        seg3 = "0000"  # Lifetime
    elif expiry_days == -1:
        seg3 = "FFFF"  # Trial
    else:
        target_date = date.today() + timedelta(days=expiry_days)
        days_since_epoch = (target_date - EPOCH_DATE).days
        seg3 = f"{days_since_epoch:04X}"

    # Segment 4: Feature Flags
    feature_bits = 0
    if features.get('ml', False): feature_bits |= (1 << 0)
    if features.get('dl', False): feature_bits |= (1 << 1)
    if features.get('onnx', False): feature_bits |= (1 << 2)
    if features.get('llm', False): feature_bits |= (1 << 3)
    if features.get('multi_user', False): feature_bits |= (1 << 4)
    if features.get('api', False): feature_bits |= (1 << 5)
    seg4 = f"{feature_bits:04X}"

    # Segment 5: Checksum
    seg5 = calculate_checksum(seg1, seg2, seg3, seg4)

    return f"{seg1}-{seg2}-{seg3}-{seg4}-{seg5}"
```

## UI Requirements

### Main Window Layout

**Window Properties**:
- Title: "🔑 CiRA Studio - License Key Generator"
- Size: 800x600 (fixed, centered)
- Theme: Dark mode with blue accent (matching main app)
- Icon: Use a key icon if available

### UI Sections

#### 1. **Customer Information Panel** (Top)
```
┌─ Customer Details ────────────────────────┐
│ Name:        [_________________________] │
│ Organization: [_________________________] │
│ Email:       [_________________________] │
│ Hardware ID: [_________________________] │
│              [Copy from Customer] button  │
└───────────────────────────────────────────┘
```

#### 2. **License Configuration Panel** (Middle Left)
```
┌─ License Configuration ───────────────────┐
│ License Tier: ( ) FREE                    │
│               (•) PRO                      │
│               ( ) ENTERPRISE               │
│                                            │
│ Seats: [1▼] (1-15)                        │
│                                            │
│ Expiry:  ( ) Lifetime                     │
│          (•) 1 Year (365 days)            │
│          ( ) 2 Years (730 days)           │
│          ( ) Custom: [___] days           │
│          ( ) 30-Day Trial                 │
└───────────────────────────────────────────┘
```

#### 3. **Feature Selection Panel** (Middle Right)
```
┌─ Features ────────────────────────────────┐
│ [✓] ML Algorithms                         │
│ [✓] Deep Learning                         │
│ [✓] ONNX Export                           │
│ [✓] LLM Features                          │
│ [✓] Multi-User Support                    │
│ [✓] API Access                            │
│                                            │
│ Quick Presets:                            │
│ [All Features] [PRO Standard] [Basic]     │
└───────────────────────────────────────────┘
```

#### 4. **Generated Key Panel** (Bottom)
```
┌─ Generated License Key ───────────────────┐
│                                            │
│  CF3A-9121-02C9-003F-AC84                 │
│                                            │
│  [Generate Key] [Copy Key] [Decode Key]   │
│                                            │
│  Key Details:                              │
│  • Tier: PRO                              │
│  • Seats: 1                               │
│  • Expires: 2026-12-15                    │
│  • Features: All enabled                  │
│  • Checksum: Valid ✓                      │
└───────────────────────────────────────────┘
```

#### 5. **Action Buttons** (Very Bottom)
```
[Save to File] [Export to CSV] [Clear Form] [About]
```

### Feature Details

#### Quick Presets
1. **All Features**: Enable all checkboxes
2. **PRO Standard**: ML + DL + ONNX + LLM (typical PRO license)
3. **Basic**: ML only (FREE tier features)

#### Tier-Specific Auto-Configuration
When user selects a tier, auto-configure typical features:
- **FREE**: ML only, 1 seat, lifetime
- **PRO**: All features except Multi-User/API, 1-5 seats, 1 year
- **ENTERPRISE**: All features, 1-15 seats, 2 years

#### Key Decoding Feature
Add a "Decode Key" function that:
1. Takes an existing key as input
2. Validates checksum
3. Displays all decoded information:
   - Product code
   - Tier
   - Seats
   - Expiry date
   - Enabled features
   - Checksum status

#### Export Functionality

**Save to File**:
- Creates a `.txt` file with:
  ```
  CiRA FutureEdge Studio - License Key
  ===================================

  Customer: John Doe
  Organization: Acme Corp
  Email: john@acme.com

  License Key: CF3A-9121-02C9-003F-AC84

  License Details:
  - Tier: PRO
  - Seats: 1
  - Issued: 2025-12-15
  - Expires: 2026-12-15

  Features Included:
  - ML Algorithms
  - Deep Learning
  - ONNX Export
  - LLM Features

  ===================================
  IMPORTANT: Keep this license key secure.
  Do not share with unauthorized users.
  ```

**Export to CSV**:
- Append to `licenses.csv` for record keeping:
  ```csv
  Date,Customer,Email,Organization,Key,Tier,Seats,Expiry,Features
  2025-12-15,John Doe,john@acme.com,Acme Corp,CF3A-...,PRO,1,2026-12-15,"ML,DL,ONNX,LLM"
  ```

### Validation & Error Handling

1. **Customer Name Required**: Show warning if empty
2. **Seat Count Validation**: 1-15 only
3. **Custom Days Validation**: Positive integer, max 3650 (10 years)
4. **Duplicate Key Warning**: If generating same configuration twice
5. **Checksum Verification**: Always validate generated keys before displaying

### Additional Features

#### Batch Generation
Add a menu option: `File → Batch Generate`
- Generate multiple keys at once
- CSV import for customer list
- Bulk export to file

#### License History
- Keep history of generated keys in local database (SQLite)
- Search/filter by customer, date, tier
- Export history to Excel

#### Security Features
1. **Password Protection**: Require password to launch (optional)
2. **Audit Log**: Log all key generation with timestamp
3. **Watermark**: Add vendor name to UI
4. **Disclaimer**: Show on first launch about vendor-only use

## File Structure

```
license_generator/
├── main.py                 # Entry point
├── generator.py           # Core key generation logic
├── ui/
│   ├── main_window.py    # Main UI window
│   ├── decode_dialog.py  # Key decoder dialog
│   └── batch_dialog.py   # Batch generation dialog
├── database/
│   └── history.py        # License history database
├── assets/
│   └── icon.ico          # Application icon
├── config.py             # Configuration (SECRET_SALT, etc.)
├── requirements.txt      # Dependencies
└── build.spec            # PyInstaller build config
```

## Dependencies

```txt
customtkinter==5.2.0
Pillow==10.0.0
```

## Build Instructions

### Creating Standalone Executable

Use PyInstaller:
```bash
pyinstaller --onefile --windowed --name="CiRA_License_Generator" --icon=assets/icon.ico main.py
```

Options:
- `--onefile`: Single executable
- `--windowed`: No console window
- `--name`: Custom executable name
- `--icon`: Application icon

### Distribution Package

Create a folder structure:
```
CiRA_License_Generator/
├── CiRA_License_Generator.exe
├── README.txt
├── LICENSE_TEMPLATE.txt
└── licenses/              # Empty folder for exports
    └── .gitkeep
```

## Security Considerations

1. **SECRET_SALT Protection**:
   - NEVER commit to public repository
   - Store in encrypted config file
   - Change before production use

2. **Generator Security**:
   - Executable password protection
   - Encrypt SQLite database
   - No remote access/internet required

3. **Vendor-Only**:
   - Clear documentation that this is NOT for customers
   - Add warning in UI: "⚠️ VENDOR USE ONLY"
   - Include disclaimer in About dialog

## Testing Requirements

### Test Cases

1. **Key Generation**:
   - Generate FREE tier key
   - Generate PRO tier key (1 year)
   - Generate ENTERPRISE key (2 years, 5 seats)
   - Generate lifetime key
   - Generate trial key

2. **Key Validation**:
   - Validate checksum for each generated key
   - Decode and verify all fields match input

3. **Edge Cases**:
   - Maximum seats (15)
   - Maximum expiry (3650 days)
   - All features disabled
   - All features enabled

4. **UI Testing**:
   - Quick presets work correctly
   - Export to file/CSV succeeds
   - Decode existing keys accurately
   - Form validation prevents invalid input

## Example Usage Workflow

1. **Vendor receives order** for PRO license from customer
2. **Open generator application**
3. **Fill in customer details**:
   - Name: John Doe
   - Organization: Acme Corp
   - Email: john@acme.com
4. **Select PRO tier** (auto-selects standard features)
5. **Set expiry**: 1 Year
6. **Click "Generate Key"**
7. **Copy key**: CF3A-9121-02C9-003F-AC84
8. **Save to file** for customer records
9. **Email key to customer** with activation instructions

## Deliverables

1. ✅ Fully functional GUI application
2. ✅ Key generation with all specified features
3. ✅ Key decoding/validation tool
4. ✅ Export to file/CSV functionality
5. ✅ Standalone Windows executable
6. ✅ User manual (README)
7. ✅ Example license keys for testing

## Additional Notes

- The generated keys MUST work with the existing `core/license_manager.py` in the main application
- The SECRET_SALT must match exactly between generator and validator
- Test all generated keys in the actual application before distributing to customers
- Keep the generator tool in a secure location (not on customer-facing systems)

---

## Bonus Features (Optional)

1. **Email Integration**: Send keys directly via SMTP
2. **QR Code Generation**: Generate QR codes for easy mobile activation
3. **Cloud Sync**: Sync generated keys to secure cloud storage
4. **Expiry Reminders**: Track and notify when customer licenses are about to expire
5. **Revenue Dashboard**: Show total licenses sold by tier
6. **Customer Portal**: Generate customer-specific URLs for key retrieval

---

## Important References

### Existing Code to Match

The generator must be compatible with the validation code in `core/license_manager.py`:

**Checksum Calculation** (lines 245-253):
```python
def _calculate_checksum(self, s1: str, s2: str, s3: str, s4: str) -> str:
    """Calculate CRC16 checksum for license key validation."""
    data = f"{s1}{s2}{s3}{s4}{self.SECRET_SALT}"
    crc = binascii.crc_hqx(data.encode(), 0xFFFF)
    return f"{crc:04X}"
```

**Key Validation** (lines 73-165):
```python
def validate_key(self, key: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    # Format: XXXX-XXXX-XXXX-XXXX-XXXX
    # Segment 1: Product code (CF3A)
    # Segment 2: Tier + Seats + Salt
    # Segment 3: Expiry date
    # Segment 4: Feature flags
    # Segment 5: Checksum
```

### Test Keys Available

Use these keys from `LICENSE_KEYS_README.md` for testing compatibility:

**FREE Tier (Lifetime)**:
```
CF3A-81A9-0000-0001-0B28
```

**PRO Tier (1 year, all features)**:
```
CF3A-9121-02C9-003F-AC84
```

**ENTERPRISE Tier (2 years, 5 seats)**:
```
CF3A-A567-0436-003F-2423
```

---

This prompt provides everything needed to build a complete, professional license key generator application that is fully compatible with the CiRA FutureEdge Studio license validation system!
