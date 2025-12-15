"""
License Manager - Validation and Activation

Handles license key validation, activation, and storage.
"""

import re
import binascii
import hashlib
import platform
import uuid
import json
import base64
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime, date, timedelta
from loguru import logger

from core.license import License, LicenseTier, TIERS, get_default_license, LicenseStatus


class LicenseManager:
    """
    Manages software licensing and validation.

    Features:
    - License key validation with checksum
    - Hardware ID generation and binding
    - License activation and deactivation
    - Feature access control
    - License persistence
    """

    # Secret salt for checksum validation (CHANGE IN PRODUCTION!)
    SECRET_SALT = "CiRA_FES_2025_SECRET_KEY_v1.0"

    # Product code (fixed)
    PRODUCT_CODE = "CF3A"

    # License storage location
    LICENSE_FILE = Path.home() / "AppData" / "Roaming" / "CiRA Studio" / "license.dat"

    def __init__(self):
        """Initialize license manager."""
        self._current_license: Optional[License] = None
        self._load_license()

    def get_current_license(self) -> License:
        """
        Get current active license.

        Returns:
            License object (defaults to FREE if no license activated)
        """
        if self._current_license is None:
            self._current_license = get_default_license()

        return self._current_license

    def has_feature(self, feature_name: str) -> bool:
        """
        Check if current license has a feature.

        Args:
            feature_name: Feature identifier (ml, dl, onnx, llm, etc.)

        Returns:
            True if feature is available
        """
        license = self.get_current_license()
        return license.has_feature(feature_name)

    def validate_key(self, key: str) -> Tuple[bool, Optional[dict], Optional[str]]:
        """
        Validate license key format and checksum.

        Args:
            key: License key in format XXXX-XXXX-XXXX-XXXX-XXXX

        Returns:
            Tuple of (is_valid, license_info_dict, error_message)
        """
        # Step 1: Format validation
        key = key.strip().upper()
        if not re.match(r'^[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$', key):
            return False, None, "Invalid key format. Expected: XXXX-XXXX-XXXX-XXXX-XXXX"

        # Step 2: Split segments
        segments = key.split('-')
        s1, s2, s3, s4, s5 = segments

        # Step 3: Verify product code
        if s1 != self.PRODUCT_CODE:
            return False, None, f"Invalid product code. Expected {self.PRODUCT_CODE}, got {s1}"

        # Step 4: Verify checksum
        expected_checksum = self._calculate_checksum(s1, s2, s3, s4)
        if s5 != expected_checksum:
            return False, None, "Invalid checksum. Key may be tampered or incorrect."

        # Step 5: Decode license info
        try:
            tier_map = {"8": "FREE", "9": "PRO", "A": "ENTERPRISE"}
            tier_code = s2[0]

            if tier_code not in tier_map:
                return False, None, f"Invalid tier code: {tier_code}"

            tier_name = tier_map[tier_code]
            seats = int(s2[1], 16)

            # Decode expiry
            expiry_hex = s3
            if expiry_hex == "0000":
                expiry_date = None  # Lifetime
                is_trial = False
            elif expiry_hex == "FFFF":
                expiry_date = datetime.now() + timedelta(days=30)  # Trial
                is_trial = True
            else:
                days_since_epoch = int(expiry_hex, 16)
                expiry_date = datetime.combine(
                    date(2025, 1, 1) + timedelta(days=days_since_epoch),
                    datetime.min.time()
                )
                is_trial = False

            # Decode features
            feature_bits = int(s4, 16)
            features = {
                "ml": bool(feature_bits & (1 << 0)),
                "dl": bool(feature_bits & (1 << 1)),
                "onnx": bool(feature_bits & (1 << 2)),
                "llm": bool(feature_bits & (1 << 3)),
                "unlimited_projects": bool(feature_bits & (1 << 4)),
                "unlimited_samples": bool(feature_bits & (1 << 5)),
            }

            # Step 6: Check expiry
            if expiry_date and datetime.now() > expiry_date:
                return False, None, f"License expired on {expiry_date.strftime('%Y-%m-%d')}"

            # Step 7: Build license info
            license_info = {
                "tier": tier_name,
                "seats": seats,
                "expiry_date": expiry_date,
                "is_trial": is_trial,
                "features": features,
            }

            return True, license_info, None

        except Exception as e:
            logger.error(f"Error decoding license key: {e}")
            return False, None, f"Failed to decode license key: {str(e)}"

    def activate_license(
        self,
        key: str,
        licensed_to: str = "",
        organization: str = "",
        email: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """
        Activate a license key.

        Args:
            key: License key
            licensed_to: User name
            organization: Organization name
            email: Contact email

        Returns:
            Tuple of (success, error_message)
        """
        # Validate key
        is_valid, license_info, error = self.validate_key(key)
        if not is_valid:
            return False, error

        # Get tier configuration
        tier = TIERS.get(license_info["tier"], TIERS["FREE"])

        # Generate hardware ID
        hardware_id = self.generate_hardware_id()

        # Create license object
        license = License(
            tier=tier,
            key=key,
            issued_date=datetime.now(),
            expiry_date=license_info["expiry_date"],
            activated_date=datetime.now(),
            hardware_id=hardware_id,
            licensed_to=licensed_to,
            organization=organization,
            email=email,
            seats=license_info["seats"],
            is_trial=license_info["is_trial"],
        )

        # Save license
        self._current_license = license
        self._save_license()

        logger.info(f"License activated: {tier.display_name} for {licensed_to or 'unnamed user'}")

        return True, None

    def deactivate_license(self) -> None:
        """Deactivate current license and revert to FREE."""
        self._current_license = get_default_license()
        self._save_license()
        logger.info("License deactivated, reverted to FREE tier")

    def generate_hardware_id(self) -> str:
        """
        Generate unique hardware identifier.

        Combines machine name, processor, and MAC address.

        Returns:
            Hardware ID in format XXXX-XXXX-XXXX-XXXX
        """
        try:
            # Combine multiple hardware identifiers
            machine_id = platform.node()  # Computer name
            processor = platform.processor()
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff)
                                   for i in range(0, 8 * 6, 8)][::-1])

            # Hash them together
            combined = f"{machine_id}-{processor}-{mac_address}"
            hw_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]

            # Format as XXXX-XXXX-XXXX-XXXX
            return '-'.join([hw_hash[i:i + 4].upper() for i in range(0, 16, 4)])

        except Exception as e:
            logger.error(f"Failed to generate hardware ID: {e}")
            # Fallback to random ID
            return "0000-0000-0000-0000"

    def _calculate_checksum(self, s1: str, s2: str, s3: str, s4: str) -> str:
        """
        Calculate CRC16 checksum for license key segments.

        Args:
            s1, s2, s3, s4: Key segments

        Returns:
            4-character hex checksum
        """
        data = f"{s1}{s2}{s3}{s4}{self.SECRET_SALT}"
        crc = binascii.crc_hqx(data.encode(), 0xFFFF)
        return f"{crc:04X}"

    def _save_license(self) -> None:
        """Save license to disk (encrypted)."""
        try:
            # Ensure directory exists
            self.LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Serialize license
            if self._current_license:
                data = json.dumps(self._current_license.to_dict())
            else:
                data = json.dumps(get_default_license().to_dict())

            # Simple XOR encryption + base64
            encrypted = self._encrypt(data)

            # Write to file
            with open(self.LICENSE_FILE, 'w') as f:
                f.write(encrypted)

            logger.debug(f"License saved to {self.LICENSE_FILE}")

        except Exception as e:
            logger.error(f"Failed to save license: {e}")

    def _load_license(self) -> None:
        """Load license from disk."""
        try:
            if not self.LICENSE_FILE.exists():
                logger.debug("No license file found, using default FREE license")
                self._current_license = get_default_license()
                return

            # Read encrypted data
            with open(self.LICENSE_FILE, 'r') as f:
                encrypted = f.read()

            # Decrypt
            data = self._decrypt(encrypted)

            # Deserialize
            license_dict = json.loads(data)
            self._current_license = License.from_dict(license_dict)

            # Validate license is still valid
            if not self._current_license.is_valid:
                logger.warning("Loaded license is expired or invalid, reverting to FREE")
                self._current_license = get_default_license()
            else:
                logger.info(f"License loaded: {self._current_license.tier.display_name}")

        except Exception as e:
            logger.error(f"Failed to load license: {e}")
            self._current_license = get_default_license()

    def _encrypt(self, data: str) -> str:
        """Simple XOR encryption + base64."""
        key = self.SECRET_SALT.encode()
        encrypted = bytearray()

        for i, char in enumerate(data.encode()):
            encrypted.append(char ^ key[i % len(key)])

        return base64.b64encode(bytes(encrypted)).decode()

    def _decrypt(self, encrypted: str) -> str:
        """Simple XOR decryption."""
        key = self.SECRET_SALT.encode()
        encrypted_bytes = base64.b64decode(encrypted.encode())
        decrypted = bytearray()

        for i, byte in enumerate(encrypted_bytes):
            decrypted.append(byte ^ key[i % len(key)])

        return bytes(decrypted).decode()


# Global license manager instance
_license_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    """Get global license manager instance."""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager
