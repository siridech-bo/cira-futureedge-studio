"""
License Management - Data Structures and Tier Definitions

Handles software licensing, feature gating, and activation.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, date
from enum import Enum


class LicenseStatus(Enum):
    """License validation status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALID = "invalid"
    TRIAL = "trial"
    NOT_ACTIVATED = "not_activated"


@dataclass
class LicenseTier:
    """
    License tier configuration.

    Defines what features and limits each tier has.
    """
    name: str
    display_name: str

    # Feature flags
    ml_algorithms: bool
    deep_learning: bool
    onnx_export: bool
    llm_features: bool
    multi_user: bool
    api_access: bool

    # Limits
    max_projects: int  # -1 = unlimited
    max_samples: int   # -1 = unlimited

    # Metadata
    description: str = ""

    def has_feature(self, feature_name: str) -> bool:
        """Check if tier has a specific feature."""
        feature_map = {
            "ml": self.ml_algorithms,
            "dl": self.deep_learning,
            "onnx": self.onnx_export,
            "llm": self.llm_features,
            "multi_user": self.multi_user,
            "api": self.api_access,
        }
        return feature_map.get(feature_name, False)


# Predefined tier configurations
TIER_FREE = LicenseTier(
    name="FREE",
    display_name="🆓 FREE (Community)",
    ml_algorithms=True,
    deep_learning=False,
    onnx_export=False,
    llm_features=False,
    multi_user=False,
    api_access=False,
    max_projects=1,
    max_samples=1000,
    description="Free tier for learning and small projects"
)

TIER_PRO = LicenseTier(
    name="PRO",
    display_name="💼 PROFESSIONAL",
    ml_algorithms=True,
    deep_learning=True,
    onnx_export=True,
    llm_features=True,
    multi_user=False,
    api_access=False,
    max_projects=-1,  # unlimited
    max_samples=-1,   # unlimited
    description="Professional tier with all features"
)

TIER_ENTERPRISE = LicenseTier(
    name="ENTERPRISE",
    display_name="🏢 ENTERPRISE",
    ml_algorithms=True,
    deep_learning=True,
    onnx_export=True,
    llm_features=True,
    multi_user=True,
    api_access=True,
    max_projects=-1,
    max_samples=-1,
    description="Enterprise tier with multi-user and API access"
)

# Tier registry
TIERS: Dict[str, LicenseTier] = {
    "FREE": TIER_FREE,
    "PRO": TIER_PRO,
    "ENTERPRISE": TIER_ENTERPRISE,
}


@dataclass
class License:
    """
    Active license information.

    Represents a validated and activated license.
    """
    tier: LicenseTier
    key: str

    # Dates
    issued_date: datetime
    expiry_date: Optional[datetime]
    activated_date: Optional[datetime] = None

    # User info (populated during activation)
    hardware_id: str = ""
    licensed_to: str = ""
    organization: str = ""
    email: str = ""

    # Metadata
    seats: int = 1
    is_trial: bool = False

    # Usage tracking (FREE tier only)
    dl_training_count: int = 0
    llm_analysis_count: int = 0

    @property
    def status(self) -> LicenseStatus:
        """Get current license status."""
        if not self.activated_date:
            return LicenseStatus.NOT_ACTIVATED

        if self.expiry_date and datetime.now() > self.expiry_date:
            return LicenseStatus.EXPIRED

        if self.is_trial:
            return LicenseStatus.TRIAL

        return LicenseStatus.ACTIVE

    @property
    def is_valid(self) -> bool:
        """Check if license is currently valid."""
        return self.status in [LicenseStatus.ACTIVE, LicenseStatus.TRIAL]

    @property
    def days_remaining(self) -> Optional[int]:
        """Get days remaining until expiry (None if lifetime)."""
        if not self.expiry_date:
            return None  # Lifetime license

        delta = self.expiry_date - datetime.now()
        return max(0, delta.days)

    def has_feature(self, feature_name: str) -> bool:
        """
        Check if license has a specific feature.

        Args:
            feature_name: Feature identifier (ml, dl, onnx, llm, etc.)

        Returns:
            True if feature is enabled and license is valid
        """
        if not self.is_valid:
            return False

        return self.tier.has_feature(feature_name)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "tier": self.tier.name,
            "key": self.key,
            "issued_date": self.issued_date.isoformat(),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "activated_date": self.activated_date.isoformat() if self.activated_date else None,
            "hardware_id": self.hardware_id,
            "licensed_to": self.licensed_to,
            "organization": self.organization,
            "email": self.email,
            "seats": self.seats,
            "is_trial": self.is_trial,
            "dl_training_count": self.dl_training_count,
            "llm_analysis_count": self.llm_analysis_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "License":
        """Create License from dictionary."""
        tier = TIERS.get(data["tier"], TIER_FREE)

        return cls(
            tier=tier,
            key=data["key"],
            issued_date=datetime.fromisoformat(data["issued_date"]),
            expiry_date=datetime.fromisoformat(data["expiry_date"]) if data.get("expiry_date") else None,
            activated_date=datetime.fromisoformat(data["activated_date"]) if data.get("activated_date") else None,
            hardware_id=data.get("hardware_id", ""),
            licensed_to=data.get("licensed_to", ""),
            organization=data.get("organization", ""),
            email=data.get("email", ""),
            seats=data.get("seats", 1),
            is_trial=data.get("is_trial", False),
            dl_training_count=data.get("dl_training_count", 0),
            llm_analysis_count=data.get("llm_analysis_count", 0),
        )


def get_default_license() -> License:
    """
    Get default FREE license.

    Returns:
        License object with FREE tier
    """
    return License(
        tier=TIER_FREE,
        key="",
        issued_date=datetime.now(),
        expiry_date=None,  # Free tier never expires
        activated_date=datetime.now(),
        is_trial=False,
    )
