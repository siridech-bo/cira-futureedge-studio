# License Key System - CiRA FutureEdge Studio

## Test License Keys

### FREE Tier (Lifetime)
```
Key: CF3A-81A9-0000-0001-0B28
```
Features:
- [YES] ML Algorithms
- [NO] Deep Learning
- [NO] ONNX Export
- [NO] LLM Features
- Max 1 project, 1000 samples

### PRO Tier (1 year - expires 2026-12-15)
```
Key: CF3A-9121-02C9-003F-AC84
```
Features:
- [YES] ML Algorithms
- [YES] Deep Learning
- [YES] ONNX Export
- [YES] LLM Features
- Unlimited projects and samples

### ENTERPRISE Tier (2 years - expires 2027-12-15, 5 seats)
```
Key: CF3A-A567-0436-003F-2423
```
Features:
- [YES] ML Algorithms
- [YES] Deep Learning
- [YES] ONNX Export
- [YES] LLM Features
- Unlimited projects and samples
- 5 user seats

## License Key Format

```
Format: XXXX-XXXX-XXXX-XXXX-XXXX
Example: CF3A-9121-02C9-003F-AC84

Segment Breakdown:
├─ Segment 1 (CF3A): Product Code
├─ Segment 2 (9121): Tier (9=PRO) + Seats (1) + Salt (21)
├─ Segment 3 (02C9): Expiry Date (713 days from 2025-01-01 = 2026-12-15)
├─ Segment 4 (003F): Feature Flags (0x3F = all features enabled)
└─ Segment 5 (AC84): CRC16 Checksum
```

## Generating License Keys

### Command Line Tool

```bash
# Generate PRO license (1 year)
python tools/license_generator.py --tier PRO --expiry-days 365 --name "Customer Name"

# Generate ENTERPRISE license (lifetime, 10 seats)
python tools/license_generator.py --tier ENTERPRISE --seats 10 --name "Company Inc"

# Generate Trial license (30 days from activation)
python tools/license_generator.py --tier PRO --expiry-days -1 --name "Trial User"

# Decode existing key
python tools/license_generator.py --decode "CF3A-9121-02C9-003F-AC84"
```

### Programmatic Generation

```python
from tools.license_generator import LicenseKeyGenerator

generator = LicenseKeyGenerator()

# Generate PRO license
key = generator.generate_key(
    tier="PRO",
    expiry_days=365,
    seats=1
)

print(f"Generated key: {key}")

# Decode key
info = generator.decode_key(key)
print(f"Tier: {info['tier']}")
print(f"Expiry: {info['expiry']}")
```

## License Validation

```python
from core.license_manager import get_license_manager

# Get license manager
license_mgr = get_license_manager()

# Validate and activate license
success, error = license_mgr.activate_license(
    key="CF3A-9121-02C9-003F-AC84",
    licensed_to="John Doe",
    organization="Acme Corp",
    email="john@acme.com"
)

if success:
    print("License activated successfully!")
else:
    print(f"Activation failed: {error}")

# Check features
if license_mgr.has_feature("dl"):
    print("Deep Learning is enabled")
else:
    print("Deep Learning requires PRO license")
```

## License Storage

License is stored encrypted at:
```
Windows: %APPDATA%\CiRA Studio\license.dat
Linux/Mac: ~/.local/share/CiRA Studio/license.dat
```

## Security Notes

**⚠️ IMPORTANT FOR PRODUCTION:**

1. **Change SECRET_SALT**: Update the secret in both:
   - `core/license_manager.py` (line 26)
   - `tools/license_generator.py` (line 30)

2. **Hardware Binding**: License is bound to hardware ID to prevent sharing

3. **Checksum Validation**: CRC16 checksum prevents key tampering

4. **Encryption**: License file is encrypted with XOR + base64 (simple but effective)

## Feature Gating

Add license checks before features:

```python
from core.license_manager import get_license_manager

def train_deep_learning():
    if not get_license_manager().has_feature("dl"):
        show_error("Deep Learning requires PRO license")
        return

    # Proceed with training...
```

## License Tiers Comparison

| Feature | FREE | PRO | ENTERPRISE |
|---------|------|-----|------------|
| ML Algorithms | ✅ | ✅ | ✅ |
| Deep Learning | ❌ | ✅ | ✅ |
| ONNX Export | ❌ | ✅ | ✅ |
| LLM Features | ❌ | ✅ | ✅ |
| Max Projects | 1 | ∞ | ∞ |
| Max Samples | 1000 | ∞ | ∞ |
| Multi-user | ❌ | ❌ | ✅ |
| API Access | ❌ | ❌ | ✅ |
| Price | Free | $299/year | Contact Sales |
