"""
License Key Generator Tool

Generates license keys for CiRA FutureEdge Studio.

Usage:
    python tools/license_generator.py --tier PRO --expiry-days 365 --name "John Doe"
"""

import sys
import argparse
import binascii
import secrets
from datetime import date, timedelta
from pathlib import Path
from typing import Optional, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.license import TIERS


class LicenseKeyGenerator:
    """
    Generate license keys with encryption and validation.

    Key Format: XXXX-XXXX-XXXX-XXXX-XXXX
    - Segment 1: Product code (CF3A)
    - Segment 2: Tier + seats
    - Segment 3: Expiry date
    - Segment 4: Feature flags
    - Segment 5: Checksum
    """

    SECRET_SALT = "CiRA_FES_2025_SECRET_KEY_v1.0"
    PRODUCT_CODE = "CF3A"

    def generate_key(
        self,
        tier: str = "PRO",
        expiry_days: Optional[int] = None,
        seats: int = 1,
        custom_features: Optional[Dict[str, bool]] = None
    ) -> str:
        """
        Generate a license key.

        Args:
            tier: License tier (FREE, PRO, ENTERPRISE)
            expiry_days: Days until expiry (None = lifetime, -1 = trial)
            seats: Number of seats (1-15)
            custom_features: Custom feature overrides

        Returns:
            License key string
        """
        if tier not in TIERS:
            raise ValueError(f"Invalid tier: {tier}. Must be one of {list(TIERS.keys())}")

        if seats < 1 or seats > 15:
            raise ValueError(f"Seats must be between 1 and 15, got {seats}")

        # Segment 1: Product Code (fixed)
        seg1 = self.PRODUCT_CODE

        # Segment 2: License Type (tier + seats + random salt)
        tier_byte = {"FREE": "8", "PRO": "9", "ENTERPRISE": "A"}[tier]
        seats_byte = f"{seats:X}"  # Hex digit 1-F
        random_salt = secrets.token_hex(1).upper()  # 2 random hex chars
        seg2 = f"{tier_byte}{seats_byte}{random_salt}"

        # Segment 3: Expiry Date
        if expiry_days is None:
            seg3 = "0000"  # Lifetime
        elif expiry_days == -1:
            seg3 = "FFFF"  # Trial (30 days from activation)
        else:
            expiry_date = date.today() + timedelta(days=expiry_days)
            days_since_epoch = (expiry_date - date(2025, 1, 1)).days

            if days_since_epoch < 0 or days_since_epoch > 0xFFFE:
                raise ValueError(f"Expiry date out of range: {expiry_date}")

            seg3 = f"{days_since_epoch:04X}"

        # Segment 4: Feature Flags
        tier_config = TIERS[tier]

        # Use tier defaults or custom overrides
        if custom_features:
            features = custom_features
        else:
            features = {
                "ml": tier_config.ml_algorithms,
                "dl": tier_config.deep_learning,
                "onnx": tier_config.onnx_export,
                "llm": tier_config.llm_features,
                "unlimited_projects": tier_config.max_projects == -1,
                "unlimited_samples": tier_config.max_samples == -1,
            }

        # Encode as bit flags
        feature_bits = 0
        if features.get("ml"): feature_bits |= (1 << 0)
        if features.get("dl"): feature_bits |= (1 << 1)
        if features.get("onnx"): feature_bits |= (1 << 2)
        if features.get("llm"): feature_bits |= (1 << 3)
        if features.get("unlimited_projects"): feature_bits |= (1 << 4)
        if features.get("unlimited_samples"): feature_bits |= (1 << 5)

        seg4 = f"{feature_bits:04X}"

        # Segment 5: Checksum
        seg5 = self._calculate_checksum(seg1, seg2, seg3, seg4)

        # Combine segments
        key = f"{seg1}-{seg2}-{seg3}-{seg4}-{seg5}"

        return key

    def _calculate_checksum(self, s1: str, s2: str, s3: str, s4: str) -> str:
        """Calculate CRC16 checksum."""
        data = f"{s1}{s2}{s3}{s4}{self.SECRET_SALT}"
        crc = binascii.crc_hqx(data.encode(), 0xFFFF)
        return f"{crc:04X}"

    def decode_key(self, key: str) -> dict:
        """
        Decode a license key to show its components.

        Args:
            key: License key

        Returns:
            Dictionary with decoded information
        """
        segments = key.strip().upper().split('-')
        if len(segments) != 5:
            raise ValueError("Invalid key format")

        s1, s2, s3, s4, s5 = segments

        # Decode tier
        tier_map = {"8": "FREE", "9": "PRO", "A": "ENTERPRISE"}
        tier = tier_map.get(s2[0], "UNKNOWN")

        # Decode seats
        seats = int(s2[1], 16)

        # Decode expiry
        if s3 == "0000":
            expiry = "Lifetime"
        elif s3 == "FFFF":
            expiry = "Trial (30 days)"
        else:
            days = int(s3, 16)
            expiry_date = date(2025, 1, 1) + timedelta(days=days)
            expiry = expiry_date.strftime("%Y-%m-%d")

        # Decode features
        feature_bits = int(s4, 16)
        features = {
            "ML Algorithms": bool(feature_bits & (1 << 0)),
            "Deep Learning": bool(feature_bits & (1 << 1)),
            "ONNX Export": bool(feature_bits & (1 << 2)),
            "LLM Features": bool(feature_bits & (1 << 3)),
            "Unlimited Projects": bool(feature_bits & (1 << 4)),
            "Unlimited Samples": bool(feature_bits & (1 << 5)),
        }

        # Verify checksum
        expected_checksum = self._calculate_checksum(s1, s2, s3, s4)
        checksum_valid = (s5 == expected_checksum)

        return {
            "key": key,
            "product_code": s1,
            "tier": tier,
            "seats": seats,
            "expiry": expiry,
            "features": features,
            "checksum_valid": checksum_valid,
        }


def main():
    """Command-line interface for key generation."""
    parser = argparse.ArgumentParser(
        description="Generate license keys for CiRA FutureEdge Studio"
    )

    parser.add_argument(
        "--tier",
        choices=["FREE", "PRO", "ENTERPRISE"],
        default="PRO",
        help="License tier (default: PRO)"
    )

    parser.add_argument(
        "--expiry-days",
        type=int,
        help="Days until expiry (omit for lifetime, -1 for trial)"
    )

    parser.add_argument(
        "--seats",
        type=int,
        default=1,
        help="Number of seats/users (1-15, default: 1)"
    )

    parser.add_argument(
        "--name",
        help="Licensed to (for display purposes)"
    )

    parser.add_argument(
        "--decode",
        help="Decode an existing key"
    )

    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of keys to generate (default: 1)"
    )

    args = parser.parse_args()

    generator = LicenseKeyGenerator()

    # Decode mode
    if args.decode:
        print(f"\n{'=' * 60}")
        print("LICENSE KEY DECODER")
        print(f"{'=' * 60}\n")

        try:
            info = generator.decode_key(args.decode)

            print(f"Key:           {info['key']}")
            print(f"Product Code:  {info['product_code']}")
            print(f"Tier:          {info['tier']}")
            print(f"Seats:         {info['seats']}")
            print(f"Expiry:        {info['expiry']}")
            print(f"Checksum:      {'VALID' if info['checksum_valid'] else 'INVALID'}")
            print(f"\nFeatures Enabled:")
            for feature, enabled in info['features'].items():
                status = "[YES]" if enabled else "[NO]"
                print(f"  {status} {feature}")

        except Exception as e:
            print(f"Error: {e}")

        return

    # Generate mode
    print(f"\n{'=' * 60}")
    print("LICENSE KEY GENERATOR")
    print(f"{'=' * 60}\n")

    print(f"Tier:          {args.tier}")
    print(f"Seats:         {args.seats}")

    if args.expiry_days is None:
        print(f"Expiry:        Lifetime")
    elif args.expiry_days == -1:
        print(f"Expiry:        Trial (30 days)")
    else:
        expiry_date = date.today() + timedelta(days=args.expiry_days)
        print(f"Expiry:        {expiry_date.strftime('%Y-%m-%d')} ({args.expiry_days} days)")

    if args.name:
        print(f"Licensed to:   {args.name}")

    print(f"\n{'=' * 60}")
    print(f"GENERATED KEYS:")
    print(f"{'=' * 60}\n")

    for i in range(args.count):
        key = generator.generate_key(
            tier=args.tier,
            expiry_days=args.expiry_days,
            seats=args.seats
        )
        print(f"{i + 1}. {key}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
