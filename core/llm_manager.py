"""
LLM Manager for Feature Selection

Integrates llama-cpp-python for intelligent feature selection with:
- Local Llama-3.2-3B model
- Context-aware feature ranking
- Embedded system constraints
- Fallback to statistical methods
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import json
from dataclasses import dataclass
from loguru import logger

try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not available. LLM features will be disabled.")


@dataclass
class LLMConfig:
    """Configuration for LLM."""

    model_path: Path
    n_ctx: int = 2048  # Context length
    n_threads: int = 4  # CPU threads
    temperature: float = 0.3  # Low for deterministic output
    max_tokens: int = 1024
    top_p: float = 0.9
    top_k: int = 40


@dataclass
class FeatureSelection:
    """Result from LLM feature selection."""

    selected_features: List[str]
    reasoning: str
    confidence: float
    fallback_used: bool = False
    llm_response: Optional[str] = None


class LLMManager:
    """Manages LLM for intelligent feature selection."""

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM manager.

        Args:
            config: LLM configuration
        """
        self.config = config
        self.model: Optional[Llama] = None
        self.is_loaded = False

    def load_model(self) -> bool:
        """
        Load LLM model.

        Returns:
            True if successful, False otherwise
        """
        if not LLAMA_CPP_AVAILABLE:
            logger.error("llama-cpp-python not installed")
            return False

        if not self.config.model_path.exists():
            logger.error(f"Model file not found: {self.config.model_path}")
            return False

        try:
            logger.info(f"Loading LLM model from {self.config.model_path}")
            logger.info(f"Model size: {self.config.model_path.stat().st_size / 1024 / 1024:.1f} MB")

            self.model = Llama(
                model_path=str(self.config.model_path),
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                verbose=False
            )

            self.is_loaded = True
            logger.info("LLM model loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            return False

    def unload_model(self) -> None:
        """Unload model from memory."""
        if self.model:
            del self.model
            self.model = None
            self.is_loaded = False
            logger.info("LLM model unloaded")

    def select_features(
        self,
        features: List[str],
        feature_importance: Dict[str, float],
        domain: str,
        target_count: int = 5,
        platform_constraints: Optional[Dict[str, Any]] = None,
        custom_prompt_template: Optional[str] = None,
        feature_stats_per_class: Optional[Dict[str, Dict]] = None
    ) -> FeatureSelection:
        """
        Select best features using LLM.

        Args:
            features: List of feature names
            feature_importance: Dictionary of feature -> importance score
            domain: Application domain (e.g., "rotating_machinery")
            target_count: Number of features to select
            platform_constraints: Target platform constraints (memory, compute)

        Returns:
            FeatureSelection result
        """
        if not self.is_loaded:
            logger.warning("LLM not loaded, using fallback selection")
            return self._fallback_selection(
                features, feature_importance, target_count
            )

        try:
            # Build prompt (use custom template if provided)
            if custom_prompt_template:
                prompt = self._build_custom_prompt(
                    custom_prompt_template,
                    features,
                    feature_importance,
                    domain,
                    target_count,
                    platform_constraints,
                    feature_stats_per_class
                )
            else:
                prompt = self._build_selection_prompt(
                    features,
                    feature_importance,
                    domain,
                    target_count,
                    platform_constraints,
                    feature_stats_per_class
                )

            logger.info(f"Requesting LLM feature selection (top {target_count})")

            # Generate response
            response = self.model(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                stop=["</selection>", "\n\n\n"]
            )

            response_text = response['choices'][0]['text']

            # Parse response
            selected, reasoning = self._parse_selection_response(
                response_text, features
            )

            # Ensure we have the right number
            if len(selected) > target_count:
                selected = selected[:target_count]
            elif len(selected) < target_count:
                # Fill with top importance features
                logger.warning(f"LLM selected {len(selected)} features, filling to {target_count}")
                remaining = [f for f in features if f not in selected]
                remaining.sort(key=lambda x: feature_importance.get(x, 0), reverse=True)
                selected.extend(remaining[:target_count - len(selected)])

            logger.info(f"LLM selected {len(selected)} features")

            return FeatureSelection(
                selected_features=selected,
                reasoning=reasoning,
                confidence=0.8,  # TODO: Calculate from response
                fallback_used=False,
                llm_response=response_text
            )

        except Exception as e:
            logger.error(f"LLM feature selection failed: {e}")
            return self._fallback_selection(
                features, feature_importance, target_count
            )

    def _build_custom_prompt(
        self,
        template: str,
        features: List[str],
        importance: Dict[str, float],
        domain: str,
        target_count: int,
        constraints: Optional[Dict[str, Any]],
        feature_stats_per_class: Optional[Dict[str, Dict]] = None
    ) -> str:
        """Build prompt from custom template with variable substitution."""

        # Sort by importance
        sorted_features = sorted(
            features,
            key=lambda x: importance.get(x, 0),
            reverse=True
        )

        # Take top 30 for context (avoid token limit with rich stats)
        top_features = sorted_features[:30]

        # Build feature list with rich context
        feature_list = []
        for feat in top_features:
            imp = importance.get(feat, 0)
            feat_info = f"- {feat} (importance: {imp:.4f})"

            # Add per-class stats if available
            if feature_stats_per_class and feat in feature_stats_per_class:
                stats = feature_stats_per_class[feat]
                mi_score = stats.get('mi_score', 0)
                feat_info += f", MI: {mi_score:.4f}"

                # Add class means to show separation
                class_means = []
                for class_label, class_stat in stats.items():
                    if class_label != 'mi_score':
                        mean_val = class_stat['mean']
                        class_means.append(f"{class_label}={mean_val:.2f}")

                if class_means:
                    feat_info += f" [{', '.join(class_means)}]"

            feature_list.append(feat_info)

        feature_text = "\n".join(feature_list)

        # Domain context
        domain_context = {
            "rotating_machinery": "vibration and rotation patterns in motors, pumps, and bearings",
            "thermal_systems": "temperature patterns in heating and cooling systems",
            "electrical": "power, current, and voltage patterns",
            "custom": "general time-series patterns"
        }.get(domain, "general time-series patterns")

        # Platform constraints text
        constraints_text = ""
        if constraints:
            memory_kb = constraints.get('memory_kb', 256)
            mcu = constraints.get('mcu', 'Cortex-M4')
            constraints_text = f"""
Target Platform Constraints:
- MCU: {mcu}
- Available Memory: {memory_kb} KB
- Must be computationally efficient for embedded deployment
"""

        # Substitute variables in template
        prompt = template.format(
            target_count=target_count,
            domain_context=domain_context,
            domain=domain,
            constraints_text=constraints_text,
            feature_text=feature_text
        )

        return prompt

    def _build_selection_prompt(
        self,
        features: List[str],
        importance: Dict[str, float],
        domain: str,
        target_count: int,
        constraints: Optional[Dict[str, Any]],
        feature_stats_per_class: Optional[Dict[str, Dict]] = None
    ) -> str:
        """Build prompt for feature selection with rich feature context."""

        # Sort by importance
        sorted_features = sorted(
            features,
            key=lambda x: importance.get(x, 0),
            reverse=True
        )

        # Take top 30 for context (reduced from 50 due to richer stats)
        top_features = sorted_features[:30]

        # Build feature list with rich context
        feature_list = []
        for feat in top_features:
            imp = importance.get(feat, 0)
            feat_info = f"- {feat} (importance: {imp:.4f})"

            # Add per-class stats if available
            if feature_stats_per_class and feat in feature_stats_per_class:
                stats = feature_stats_per_class[feat]
                mi_score = stats.get('mi_score', 0)
                feat_info += f", MI: {mi_score:.4f}"

                # Add class means to show separation
                class_means = []
                for class_label, class_stat in stats.items():
                    if class_label != 'mi_score':
                        mean_val = class_stat['mean']
                        class_means.append(f"{class_label}={mean_val:.2f}")

                if class_means:
                    feat_info += f" [{', '.join(class_means)}]"

            feature_list.append(feat_info)

        feature_text = "\n".join(feature_list)

        # Domain context
        domain_context = {
            "rotating_machinery": "vibration and rotation patterns in motors, pumps, and bearings",
            "thermal_systems": "temperature patterns in heating and cooling systems",
            "electrical": "power, current, and voltage patterns",
            "custom": "general time-series patterns"
        }.get(domain, "general time-series patterns")

        # Platform constraints text
        constraints_text = ""
        if constraints:
            memory_kb = constraints.get('memory_kb', 256)
            mcu = constraints.get('mcu', 'Cortex-M4')
            constraints_text = f"""
Target Platform Constraints:
- MCU: {mcu}
- Available Memory: {memory_kb} KB
- Must be computationally efficient for embedded deployment
"""

        prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert in embedded systems and machine learning feature engineering. Your task is to select the most effective features for anomaly detection on resource-constrained embedded devices.

<|eot_id|><|start_header_id|>user<|end_header_id|>

I need to select the top {target_count} features for anomaly detection in {domain_context}.

Application Domain: {domain}
{constraints_text}
Available Features (sorted by statistical importance):
{feature_text}

Requirements:
1. Select exactly {target_count} features
2. Prioritize features that:
   - Are computationally efficient (avoid complex transforms)
   - Have high discriminative power
   - Are robust to noise
   - Complement each other (low correlation)
   - Are interpretable for embedded deployment

3. Consider:
   - Statistical features (mean, std, variance) are very fast
   - FFT and spectral features are moderately expensive
   - Time-domain features are generally fast
   - Avoid highly correlated features

Provide your selection in this format:
<selection>
1. feature_name_1
2. feature_name_2
...
{target_count}. feature_name_{target_count}
</selection>

Reasoning:
[Brief explanation of why these features were selected]

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

<selection>"""

        return prompt

    def _parse_selection_response(
        self,
        response: str,
        all_features: List[str]
    ) -> Tuple[List[str], str]:
        """
        Parse LLM response to extract selected features.

        Returns:
            Tuple of (selected_features, reasoning)
        """
        selected = []
        reasoning = ""

        lines = response.strip().split('\n')

        in_selection = True
        in_reasoning = False

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if '</selection>' in line.lower():
                in_selection = False
                continue

            if 'reasoning:' in line.lower():
                in_reasoning = True
                continue

            if in_selection:
                # Extract feature name (format: "1. feature_name" or just "feature_name")
                # Remove numbering
                feature = line
                for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '0.', '-', '*']:
                    if feature.startswith(prefix):
                        feature = feature[len(prefix):].strip()

                # Find matching feature from list
                feature_lower = feature.lower()
                for f in all_features:
                    if f.lower() == feature_lower or f.lower() in feature_lower:
                        if f not in selected:
                            selected.append(f)
                        break

            elif in_reasoning:
                reasoning += line + " "

        reasoning = reasoning.strip()

        logger.info(f"Parsed {len(selected)} features from LLM response")

        return selected, reasoning

    def _fallback_selection(
        self,
        features: List[str],
        importance: Dict[str, float],
        target_count: int
    ) -> FeatureSelection:
        """
        Fallback feature selection using statistical importance.

        Args:
            features: List of feature names
            importance: Dictionary of feature -> importance score
            target_count: Number of features to select

        Returns:
            FeatureSelection result
        """
        logger.info(f"Using fallback selection (top {target_count} by importance)")

        # Sort by importance
        sorted_features = sorted(
            features,
            key=lambda x: importance.get(x, 0),
            reverse=True
        )

        selected = sorted_features[:target_count]

        reasoning = f"Selected top {target_count} features by statistical importance (LLM not available)"

        return FeatureSelection(
            selected_features=selected,
            reasoning=reasoning,
            confidence=0.7,
            fallback_used=True
        )

    def explain_features(
        self,
        selected_features: List[str],
        domain: str
    ) -> str:
        """
        Generate explanation for selected features.

        Args:
            selected_features: List of selected feature names
            domain: Application domain

        Returns:
            Explanation text
        """
        if not self.is_loaded:
            return "LLM not available for feature explanation"

        try:
            prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are an expert in embedded systems and time-series feature engineering.

<|eot_id|><|start_header_id|>user<|end_header_id|>

Explain why these features are effective for anomaly detection in {domain}:

{', '.join(selected_features)}

Provide a brief, technical explanation of what each feature captures and why it's useful for detecting anomalies.

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""

            response = self.model(
                prompt,
                max_tokens=512,
                temperature=0.5
            )

            return response['choices'][0]['text'].strip()

        except Exception as e:
            logger.error(f"Feature explanation failed: {e}")
            return "Feature explanation not available"
