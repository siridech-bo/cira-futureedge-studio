"""
Label Extractor Utility

Extracts class labels from filenames for supervised classification tasks.
Supports multiple patterns: prefix, suffix, folder-based, and regex.
"""

import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from collections import Counter
from loguru import logger


class LabelExtractor:
    """Extract class labels from filenames and analyze class distributions."""

    SUPPORTED_PATTERNS = ["prefix", "suffix", "folder", "regex"]

    @staticmethod
    def extract_from_filename(
        filename: str,
        pattern: str = "prefix",
        separator: str = ".",
        custom_regex: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract class label from filename.

        Args:
            filename: Filename (with or without extension)
            pattern: Extraction pattern - "prefix", "suffix", "folder", "regex"
            separator: Separator character for prefix/suffix patterns (default: ".")
            custom_regex: Custom regex pattern (only used if pattern="regex")

        Returns:
            Extracted class label or None if extraction fails

        Examples:
            >>> LabelExtractor.extract_from_filename("idle.1.cbor", "prefix", ".")
            "idle"

            >>> LabelExtractor.extract_from_filename("sample_001_snake.cbor", "suffix", "_")
            "snake"

            >>> LabelExtractor.extract_from_filename("ingestion-042.json", "prefix", "-")
            "ingestion"
        """
        if not filename:
            return None

        # Remove file extension
        stem = Path(filename).stem

        if pattern == "prefix":
            # Split by separator and take first part
            # Replace common separators with the chosen one
            normalized = stem.replace("_", separator).replace("-", separator)
            parts = normalized.split(separator)
            return parts[0] if parts else None

        elif pattern == "suffix":
            # Split by separator and take last part
            normalized = stem.replace("_", separator).replace("-", separator)
            parts = normalized.split(separator)
            return parts[-1] if parts else None

        elif pattern == "folder":
            # This will be handled by extract_from_path
            logger.warning("Use extract_from_path() for folder-based extraction")
            return None

        elif pattern == "regex":
            if not custom_regex:
                logger.error("Regex pattern requires custom_regex parameter")
                return None

            match = re.search(custom_regex, stem)
            if match:
                # Return first group if groups exist, otherwise full match
                return match.group(1) if match.groups() else match.group(0)
            return None

        else:
            logger.error(f"Unknown pattern: {pattern}. Use one of {LabelExtractor.SUPPORTED_PATTERNS}")
            return None

    @staticmethod
    def extract_from_path(file_path: Path, pattern: str = "prefix") -> Optional[str]:
        """
        Extract class label from full file path.

        Args:
            file_path: Path object pointing to the file
            pattern: "folder" extracts from parent directory name, others use filename

        Returns:
            Extracted class label

        Examples:
            >>> LabelExtractor.extract_from_path(Path("/data/idle/sample1.cbor"), "folder")
            "idle"

            >>> LabelExtractor.extract_from_path(Path("/data/snake.7.cbor"), "prefix")
            "snake"
        """
        if pattern == "folder":
            # Extract from parent folder name
            return file_path.parent.name

        else:
            # Use filename-based extraction
            return LabelExtractor.extract_from_filename(file_path.name, pattern)

    @staticmethod
    def detect_classes_in_files(
        file_paths: List[Path],
        pattern: str = "prefix",
        separator: str = ".",
        custom_regex: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Scan multiple files and build class distribution.

        Args:
            file_paths: List of file paths to analyze
            pattern: Label extraction pattern
            separator: Separator for prefix/suffix patterns
            custom_regex: Custom regex (if pattern="regex")

        Returns:
            Dictionary mapping class names to file counts

        Example:
            >>> files = [Path("idle.1.cbor"), Path("idle.2.cbor"), Path("snake.1.cbor")]
            >>> LabelExtractor.detect_classes_in_files(files, "prefix")
            {"idle": 2, "snake": 1}
        """
        labels = []

        for file_path in file_paths:
            if pattern == "folder":
                label = LabelExtractor.extract_from_path(file_path, "folder")
            else:
                label = LabelExtractor.extract_from_filename(
                    file_path.name,
                    pattern,
                    separator,
                    custom_regex
                )

            if label:
                labels.append(label)

        # Count occurrences
        class_distribution = dict(Counter(labels))

        logger.info(f"Detected {len(class_distribution)} classes from {len(file_paths)} files")
        for class_name, count in sorted(class_distribution.items()):
            logger.info(f"  • {class_name}: {count} files")

        return class_distribution

    @staticmethod
    def create_class_mapping(class_names: List[str]) -> Dict[str, int]:
        """
        Create integer mapping for class names (sorted alphabetically).

        Args:
            class_names: List of unique class names

        Returns:
            Dictionary mapping class name to integer ID

        Example:
            >>> LabelExtractor.create_class_mapping(["snake", "idle", "ingestion"])
            {"idle": 0, "ingestion": 1, "snake": 2}
        """
        sorted_classes = sorted(set(class_names))
        mapping = {name: idx for idx, name in enumerate(sorted_classes)}

        logger.info(f"Created class mapping with {len(mapping)} classes:")
        for name, idx in mapping.items():
            logger.info(f"  {idx}: {name}")

        return mapping

    @staticmethod
    def validate_class_distribution(
        class_distribution: Dict[str, int],
        min_samples_per_class: int = 10,
        imbalance_ratio_threshold: float = 10.0
    ) -> Tuple[bool, List[str]]:
        """
        Validate that class distribution is suitable for training.

        Args:
            class_distribution: Dict mapping class names to sample counts
            min_samples_per_class: Minimum samples required per class
            imbalance_ratio_threshold: Max ratio between largest and smallest class

        Returns:
            Tuple of (is_valid, list_of_warnings)

        Example:
            >>> dist = {"idle": 500, "snake": 300, "error": 5}
            >>> valid, warnings = LabelExtractor.validate_class_distribution(dist)
            >>> print(warnings)
            ["Class 'error' has only 5 samples (minimum: 10)"]
        """
        warnings = []

        if not class_distribution:
            return False, ["No classes detected"]

        if len(class_distribution) < 2:
            warnings.append("Only 1 class detected. Classification requires at least 2 classes.")
            return False, warnings

        counts = list(class_distribution.values())
        max_count = max(counts)
        min_count = min(counts)

        # Check minimum samples
        for class_name, count in class_distribution.items():
            if count < min_samples_per_class:
                warnings.append(
                    f"Class '{class_name}' has only {count} samples (minimum: {min_samples_per_class})"
                )

        # Check class imbalance
        if min_count > 0:
            imbalance_ratio = max_count / min_count
            if imbalance_ratio > imbalance_ratio_threshold:
                max_class = max(class_distribution, key=class_distribution.get)
                min_class = min(class_distribution, key=class_distribution.get)
                warnings.append(
                    f"Severe class imbalance detected: '{max_class}' ({max_count}) vs "
                    f"'{min_class}' ({min_count}). Ratio: {imbalance_ratio:.1f}:1"
                )

        is_valid = len(warnings) == 0

        if is_valid:
            logger.info("✓ Class distribution is valid for training")
        else:
            logger.warning(f"⚠ Class distribution has {len(warnings)} issues:")
            for warning in warnings:
                logger.warning(f"  - {warning}")

        return is_valid, warnings

    @staticmethod
    def suggest_pattern(filenames: List[str]) -> str:
        """
        Analyze filenames and suggest best extraction pattern.

        Args:
            filenames: List of filenames to analyze

        Returns:
            Suggested pattern ("prefix", "suffix", or "folder")

        Example:
            >>> files = ["idle.1.cbor", "snake.2.cbor", "ingestion.3.cbor"]
            >>> LabelExtractor.suggest_pattern(files)
            "prefix"
        """
        if not filenames:
            return "prefix"

        # Try prefix pattern
        prefix_labels = [
            LabelExtractor.extract_from_filename(f, "prefix") for f in filenames
        ]
        prefix_unique = len(set([l for l in prefix_labels if l]))

        # Try suffix pattern
        suffix_labels = [
            LabelExtractor.extract_from_filename(f, "suffix", "_") for f in filenames
        ]
        suffix_unique = len(set([l for l in suffix_labels if l]))

        # Prefer the pattern that yields more unique classes (2-20 range is reasonable)
        if 2 <= prefix_unique <= 20:
            logger.info(f"Suggested pattern: 'prefix' ({prefix_unique} classes detected)")
            return "prefix"
        elif 2 <= suffix_unique <= 20:
            logger.info(f"Suggested pattern: 'suffix' ({suffix_unique} classes detected)")
            return "suffix"
        else:
            logger.info("Suggested pattern: 'prefix' (default)")
            return "prefix"
