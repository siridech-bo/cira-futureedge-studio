# CiRA FutureEdge Studio - Complete Project Specification

## Table of Contents
1. [Project Overview](#project-overview)
2. [Core Philosophy](#core-philosophy)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [LLM Feature Engineering](#llm-feature-engineering)
6. [Development Phases](#development-phases)
7. [Deliverables](#deliverables)
8. [Constraints & Compliance](#constraints--compliance)
9. [Success Metrics](#success-metrics)

---

## Project Overview

**CiRA FutureEdge Studio** is a fully offline Windows desktop application for end-to-end anomaly detection on embedded devices. It guides users through data ingestion, intelligent feature engineering (using local LLM), model training, and deployment to resource-constrained edge devices—all without cloud dependencies.

### Key Differentiators
- **100% Offline Operation**: No internet required, no cloud APIs, no telemetry
- **LLM as Feature Engineer**: Local small language model (SLM) intelligently selects optimal features for embedded deployment
- **Multi-Source Data**: CSV, databases, APIs, streaming sensors
- **Advanced ML Stack**: tsfresh (700+ features), PySR (symbolic regression), PyOD (45+ anomaly algorithms)
- **Edge Impulse SDK Compatible**: Generates C++ code that integrates with the official inferencing-sdk-cpp
- **Professional Studio UX**: Modern UI inspired by Edge Impulse Studio workflow

---

## Core Philosophy

> **"LLM as Feature Engineer, Edge as Efficient Executor"**

The studio uses a **local LLM/SLM as a design-time tool** to intelligently engineer features that run on resource-constrained MCUs. This is **not** LLM-at-inference, but **LLM-for-feature-discovery**.

### Workflow Philosophy
1. **Comprehensive Feature Extraction**: Extract 700+ candidate features using tsfresh, PySR, and custom DSP
2. **Intelligent Selection**: Local LLM analyzes features with physical domain knowledge and selects optimal subset (typically 5 features)
3. **Efficient Deployment**: Generate minimal C++ code that computes only selected features on MCU
4. **Anomaly Detection**: Train lightweight model (PCA, LOF, etc.) on selected features
5. **Embedded Execution**: Compile firmware with Edge Impulse SDK for on-device inference

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│         CiRA FutureEdge Studio (Windows Desktop)                │
│                    100% Offline Operation                       │
│                   Built with CustomTkinter                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   1. DATA INGESTION (Multi-Source)      │
        │   • CSV, SQLite, PostgreSQL, REST API   │
        │   • Mock streaming for testing          │
        │   • Windowing: nominal/off/anomaly      │
        │   • Multi-axis time-series viz          │
        │   • Data quality checks                 │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   2. FEATURE EXTRACTION (Comprehensive) │
        │   • tsfresh: 700+ statistical features  │
        │   • PySR: symbolic regression formulas  │
        │   • Custom DSP: FFT, wavelets, filters  │
        │   • Output: Candidate feature matrix    │
        │   • Metadata: Cohen's d, variance, MI   │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   3. LLM-ASSISTED FEATURE SELECTION     │
        │   ┌───────────────────────────────────┐ │
        │   │ Local SLM (4-bit quantized)      │ │
        │   │ Primary: Llama-3.2-3B-Instruct   │ │
        │   │   (~2.5 GB, Q4_K_M quantization) │ │
        │   │ Alternative: Qwen2.5-7B (higher) │ │
        │   │ Fallback: Phi-3.5-mini (lighter) │ │
        │   └───────────────────────────────────┘ │
        │                                         │
        │   Prompt Engineering:                   │
        │   → Candidate features + metadata       │
        │   → Physical constraints (motor physics)│
        │   → Anomaly detection goals             │
        │   ← JSON: Top-K features + reasoning    │
        │                                         │
        │   Fallback: Cohen's d + MI ranking      │
        │   + Physical heuristics                 │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   4. ANOMALY MODEL TRAINING (PyOD)      │
        │   • 45+ algorithms available:           │
        │     - PCA, LOF, COPOD, IsolationForest  │
        │     - HBOS, KNN, AutoEncoder, OCSVM     │
        │   • Train on LLM-selected features only │
        │   • Cross-validation, ROC/AUC metrics   │
        │   • Hyperparameter grid search          │
        │   • Export model parameters as JSON     │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   5. C++ DSP CODE GENERATION            │
        │   • Edge Impulse SDK-compatible         │
        │   • Only computes Top-K features        │
        │   • Uses SDK utilities:                 │
        │     - numpy:: (RMS, mean, scale)        │
        │     - spectral:: (FFT, filters)         │
        │     - signal:: (processing)             │
        │   • Inline model scoring (PCA/LOF...)   │
        │   • Generated files:                    │
        │     - custom_dsp.cpp/.h                 │
        │     - model_params.h                    │
        │     - main.cpp                          │
        │     - CMakeLists.txt                    │
        └─────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   6. FIRMWARE COMPILATION               │
        │   • CMake + MinGW-w64 (Windows x86)     │
        │   • Optional: ARM GCC (Cortex-M)        │
        │   • Links inferencing-sdk-cpp           │
        │   • Apache 2.0 compliance (LICENSE gen) │
        │   • Output: .exe / .elf / .bin          │
        └─────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Edge Device    │
                    │  (Cortex-M/ESP) │
                    │  • 5 features   │
                    │  • <10 KB model │
                    │  • <1 ms infer  │
                    └─────────────────┘
```

---

## Technology Stack

### UI Framework
- **CustomTkinter** (Primary choice)
  - Modern Material Design-inspired widgets
  - Dark/light theme support
  - Lightweight (~5 MB vs PyQt6 ~50 MB)
  - Easy debugging (pure Python, no C++ meta-objects)
  - Excellent matplotlib/plotly integration
  - MIT License

### Data Processing
- **pandas**: Data manipulation and CSV handling
- **numpy**: Numerical operations
- **sqlalchemy**: Database connectivity (SQLite, PostgreSQL)
- **requests**: REST API data ingestion

### Feature Engineering
- **tsfresh** (v0.20+): Time-series feature extraction (700+ features)
  - Statistical: mean, variance, skewness, kurtosis
  - Spectral: FFT coefficients, spectral entropy
  - Complexity: approximate entropy, sample entropy
  - Autocorrelation: lag features, partial autocorrelation
- **PySR** (v0.16+): Symbolic regression for interpretable formulas
  - Discovers mathematical relationships (e.g., `sqrt(accX^2 + accY^2) * temp`)
  - Evolutionary algorithm-based
  - Returns human-readable equations
- **scipy**: Signal processing (filtering, transforms)
- **librosa**: Audio feature extraction (if audio support added)

### Machine Learning
- **PyOD** (v1.1+): 45+ anomaly detection algorithms
  - Probabilistic: ECOD, ABOD, COPOD, MAD
  - Linear: PCA, KPCA, MCD, OCSVM
  - Proximity: LOF, COF, KNN, HBOS
  - Neural: AutoEncoder, VAE, DeepSVDD
- **scikit-learn**: Model utilities, preprocessing, metrics

### Local LLM
- **llama-cpp-python** (v0.2.0+): Python bindings for llama.cpp
  - CPU-only inference (AVX2/AVX512 optimized)
  - 4-bit quantization (Q4_K_M) for memory efficiency
  - Thread control for multi-core systems
- **Recommended Models:**
  1. **Llama-3.2-3B-Instruct-Q4_K_M** (Primary)
     - Size: ~2.5 GB
     - RAM: ~4 GB during inference
     - Best instruction-following, JSON reliability
  2. **Qwen2.5-7B-Instruct-Q4_K_M** (High-end)
     - Size: ~4.5 GB
     - RAM: ~6 GB
     - Superior reasoning, code-aware
  3. **Phi-3.5-mini-instruct-Q4_K_M** (Fallback)
     - Size: ~2.8 GB
     - RAM: ~3.5 GB
     - Microsoft-optimized, efficient

### Edge Compilation
- **inferencing-sdk-cpp**: Edge Impulse C++ inference SDK
  - Source: https://github.com/edgeimpulse/inferencing-sdk-cpp
  - License: Apache 2.0 (BSD 3-Clause Clear for some components)
  - Includes: CMSIS-DSP, TensorFlow Lite Micro, signal processing utilities
- **CMake** (v3.20+): Build system
- **MinGW-w64**: GCC compiler for Windows
- **ARM GCC** (Optional): Cross-compilation for Cortex-M

### Visualization
- **matplotlib**: Static plots, feature importance charts
- **plotly**: Interactive time-series visualization
- **pyqtgraph** (Optional): Real-time streaming data plots

### Packaging
- **PyInstaller** (v5.0+): Single-file executable bundling
- **NSIS**: Windows installer creation
- **UPX** (Optional): Executable compression

---

## LLM Feature Engineering

### Recommended SLM Comparison

| **Model** | **Size** | **Quantization** | **RAM (CPU)** | **Strengths** | **Use Case** |
|-----------|----------|------------------|---------------|---------------|-------------|
| **Llama-3.2-3B-Instruct** | 3B params | Q4_K_M | ~2.5 GB | Best instruction-following, JSON reliability | **Primary choice** |
| **Qwen2.5-7B-Instruct** | 7B params | Q4_K_M | ~4.5 GB | Strong reasoning, Chinese+English, code-aware | High-end workstations |
| **Phi-3.5-mini-instruct** | 3.8B params | Q4_K_M | ~2.8 GB | Efficient, Microsoft-optimized | Good balance |
| **TinyLlama-1.1B** | 1.1B params | Q4_K_M | ~1 GB | Ultra-fast, lower accuracy | Low-spec PCs |
| **Mistral-7B-Instruct-v0.3** | 7B params | Q4_K_M | ~4.5 GB | Strong generalist, long context | Complex multi-sensor |

### Prompt Engineering Specification

**Structured Prompt Template:**

```python
PROMPT_TEMPLATE = """
You are an industrial anomaly detection expert specializing in feature engineering for embedded systems.

## CONTEXT
- **Domain**: {domain}  # e.g., "Rotating machinery (motors, pumps, bearings)"
- **Sensors**: {sensors}  # e.g., ["accX", "accY", "accZ", "temp", "current"]
- **Sampling Rate**: {sampling_rate} Hz
- **Window Size**: {window_size} samples
- **Available Data Labels**: nominal (healthy operation), off (powered down)
- **Goal**: Detect future anomalies (imbalance, bearing wear, overheating) even though training data only has nominal/off.

## CANDIDATE FEATURES (Extracted by tsfresh + PySR)
{features_json}
# Example:
# [
#   {{"name": "accZ__fft_coefficient__coeff_4", "type": "spectral_power_bin", "value_nominal": 0.023, "value_off": 0.001, "cohens_d": 4.2}},
#   {{"name": "temp__mean", "type": "statistical", "value_nominal": 45.3, "value_off": 22.1, "cohens_d": 12.5}},
#   {{"name": "sqrt(accX^2 + accY^2 + accZ^2)", "type": "pysr_formula", "value_nominal": 1.234, "value_off": 0.05, "cohens_d": 8.9}}
# ]

## CONSTRAINTS
1. **Select exactly {max_features} features** (max 5 for embedded deployment)
2. **Allowed feature types**: rms, mean_derivative, spectral_power_bin, zero_crossing_rate, pysr_formula
3. **Prioritize features that:**
   - Show **large separation between nominal/off** (high Cohen's d > 2.0)
   - Have **low intra-class variance** (stable under normal operation)
   - Are **physically interpretable** (e.g., "bearing resonance frequency", "thermal gradient")
   - Capture **cross-sensor interactions** if relevant (e.g., "vibration correlates with temperature rise")

## PHYSICAL INTUITION
For rotating machinery:
- **Vibration spectrum (2-10 Hz)**: Imbalance, misalignment
- **High-frequency harmonics (>50 Hz)**: Bearing defects
- **Temperature trends**: Overheating, friction
- **Current spikes**: Motor overload

## OUTPUT FORMAT (JSON ONLY, NO MARKDOWN)
Return a valid JSON array with exactly {max_features} features, ranked by importance:

[
  {{
    "rank": 1,
    "feature": "accZ__fft_coefficient__coeff_4",
    "type": "spectral_power_bin",
    "reasoning": "Captures rotor imbalance signature at ~4 Hz (2x rotation frequency). High Cohen's d (4.2) ensures nominal/off separation.",
    "physical_meaning": "Rotor eccentricity or coupling misalignment",
    "edge_cost": "low"
  }},
  {{
    "rank": 2,
    "feature": "temp__mean_derivative",
    "type": "mean_derivative",
    "reasoning": "Temperature rise rate detects thermal anomalies before absolute temp threshold. Stable in nominal mode.",
    "physical_meaning": "Bearing friction or insufficient lubrication",
    "edge_cost": "low"
  }},
  ...
]

## VALIDATION RULES
- Each feature MUST have: rank, feature, type, reasoning, physical_meaning, edge_cost
- Do NOT include features with Cohen's d < 1.5 (weak discriminators)
- Prefer features with "edge_cost": "low" (simple math, no heavy FFT if avoidable)

Now, select the optimal {max_features} features from the candidates above.
"""
```

### Fallback Strategy (No LLM Available)

If LLM initialization fails or produces invalid JSON:

1. **Cohen's d ranking** (statistical discriminator between nominal/off)
   - Formula: `d = (mean_nominal - mean_off) / pooled_std`
   - Select top 5 features with highest |d|
2. **Mutual Information** (captures non-linear dependencies)
   - Use `sklearn.feature_selection.mutual_info_classif`
3. **Variance Threshold** (remove low-variance features)
   - Remove features with variance < 0.01
4. **Physical Heuristics:**
   - Always include at least 1 spectral feature (FFT bin with highest energy)
   - Always include 1 time-domain feature (RMS, zero-crossing)
   - Prefer cross-axis features (e.g., 3D magnitude: `sqrt(x² + y² + z²)`)
   - Include 1 derivative feature if available (rate of change)

---

## Development Phases

### Phase 1: Foundation & UI Shell (Week 1-2)

**Deliverables:**
- [x] CustomTkinter main window with "CiRA FutureEdge Studio" branding
- [x] Left sidebar navigation with 6 stages:
  1. 📊 Data Sources
  2. 🔬 Feature Extraction
  3. 🤖 LLM Selection
  4. 🎯 Anomaly Training
  5. ⚙️ DSP Generation
  6. 🚀 Build Firmware
- [x] Project manager (New/Open/Save `.ciraproject` files)
- [x] Dark/light theme toggle
- [x] Multi-panel layout: data preview, logs, results
- [x] Status bar with progress indicators
- [x] Threading infrastructure (QThread equivalent for background tasks)

**Key Files:**
- `main.py`: Application entry point
- `ui/main_window.py`: Main window class
- `ui/navigation.py`: Sidebar navigation
- `ui/theme.py`: Theme management
- `core/project.py`: Project state management

---

### Phase 2: Multi-Source Data Ingestion (Week 2-3)

**Deliverables:**
- [x] Data source plugins:
  - CSV loader (pandas-based)
  - SQLite connector
  - PostgreSQL connector (sqlalchemy)
  - REST API poller (configurable endpoint, polling interval)
  - Mock streaming simulator (for testing real-time data)
- [x] Windowing engine:
  - Configurable window size (default: 100 samples)
  - Configurable overlap (default: 0%, non-overlapping)
  - Configurable sampling rate (default: 50 Hz)
  - Label assignment: nominal (0), off (1), anomaly (2)
- [x] Time-series visualization:
  - Multi-axis plots (matplotlib/plotly)
  - Zoom, pan, cursor tracking
  - Window boundary indicators
- [x] Data quality checks:
  - Missing value detection
  - Outlier detection (IQR method)
  - Sampling rate validation
  - Signal clipping detection
- [x] Export windowed data to internal format (HDF5 or Parquet)

**Key Files:**
- `data_sources/csv_loader.py`
- `data_sources/db_connector.py`
- `data_sources/api_poller.py`
- `data_sources/stream_simulator.py`
- `core/windowing.py`
- `ui/data_panel.py`

---

### Phase 3: Comprehensive Feature Extraction (Week 3-4)

**Deliverables:**
- [x] **tsfresh integration:**
  - Extract 700+ features from windowed signals
  - Support multiple axes (accX, accY, accZ, temp, etc.)
  - Configurable feature sets (minimal, efficient, comprehensive)
  - Feature metadata: name, type, value_nominal, value_off
- [x] **PySR symbolic regression:**
  - Discover interpretable mathematical relationships
  - Generate custom feature formulas (e.g., `sqrt(accX^2 + accY^2) * temp`)
  - Configurable complexity limits (max 3 operators)
  - Export formulas as Python/C++ code
- [x] **Custom DSP features:**
  - FFT bins (configurable frequency ranges)
  - Wavelet coefficients (Daubechies, Haar)
  - Zero-crossing rate
  - Peak detection
- [x] **Statistical ranking:**
  - Cohen's d (effect size between nominal/off)
  - Mutual information (non-linear dependency)
  - ANOVA F-score (variance ratio)
  - Variance threshold
- [x] **Feature matrix output:**
  - DataFrame: rows=windows, cols=features
  - Metadata: feature name, type, Cohen's d, variance
  - Export to CSV/HDF5 for inspection

**Key Files:**
- `feature_extraction/tsfresh_extractor.py`
- `feature_extraction/pysr_engine.py`
- `feature_extraction/custom_dsp.py`
- `feature_extraction/ranker.py`
- `ui/feature_panel.py`

**Future Enhancement (Post-Phase 7):**
- **LLM-Assisted Custom Features:**
  - LLM suggests domain-specific feature formulas based on sensor type and application
  - User reviews and approves suggested features
  - System generates Python/C++ code for approved features
  - Integrates into tsfresh extraction pipeline
  - Benefits: Combines LLM domain knowledge with deterministic feature extraction

---

### Phase 4: LLM-Assisted Feature Selection (Week 4-5)

**Deliverables:**
- [x] **Model loader:**
  - Download GGUF models from HuggingFace (if not present)
  - Default: Llama-3.2-3B-Instruct-Q4_K_M (~2.5 GB)
  - Alternative models: Qwen2.5-7B, Phi-3.5-mini
  - Model caching in `models/` directory
  - CPU thread configuration (default: 4 threads)
- [x] **Prompt engine:**
  - Structured template with physical constraints
  - Domain-specific prompt variants (rotating machinery, thermal systems, etc.)
  - Feature metadata injection (Cohen's d, variance, physical units)
  - Max tokens: 2048, temperature: 0.3 (deterministic)
- [x] **JSON parser:**
  - Validate output against schema
  - Handle malformed JSON (retry with simplified prompt)
  - Extract: rank, feature, type, reasoning, physical_meaning, edge_cost
- [x] **Fallback mechanism:**
  - Detect LLM failure (timeout, invalid JSON, low confidence)
  - Trigger statistical ranking (Cohen's d + MI + heuristics)
  - Log fallback reason for user inspection
- [x] **UI features:**
  - Display LLM reasoning for each selected feature
  - Feature importance bar chart
  - Physical explanations panel
  - Edit/override LLM selections manually
  - Export LLM prompt/response for debugging

**Key Files:**
- `llm/model_loader.py`
- `llm/prompt_engine.py`
- `llm/feature_selector.py`
- `llm/fallback.py`
- `ui/llm_panel.py`

---

### Phase 5: PyOD Anomaly Model Training (Week 5-6)

**Deliverables:**
- [x] **PyOD model selector UI:**
  - Dropdown with 45+ algorithms categorized:
    - Probabilistic: ECOD, ABOD, COPOD, MAD
    - Linear: PCA, KPCA, MCD, OCSVM
    - Proximity: LOF, COF, KNN, HBOS
    - Neural: AutoEncoder, VAE, DeepSVDD
  - Algorithm description and complexity info
- [x] **Hyperparameter tuning:**
  - Dynamic hyperparameter panel (changes per algorithm)
  - Grid search support (e.g., PCA: n_components=[2,3,5])
  - Cross-validation (k-fold, stratified)
  - ROC/AUC metrics, confusion matrix
- [x] **Training workflow:**
  - Fit on feature matrix from Phase 4 (LLM-selected features only)
  - Validation split (80/20)
  - Display training progress (epochs for neural models)
  - Early stopping for AutoEncoder
- [x] **Model export:**
  - Save scikit-learn/PyOD model as pickle
  - Extract model parameters as JSON (for C++ code gen):
    - PCA: components, mean, explained_variance, threshold
    - LOF: neighbor_distances, local_outlier_factors, threshold
    - COPOD: empirical_cdf, tail_probabilities, threshold
  - Export inline C++ scoring function template
- [x] **Evaluation metrics:**
  - ROC curve, AUC score
  - Precision-recall curve
  - Confusion matrix (if anomaly data available)
  - Feature importance (for tree-based models)

**Key Files:**
- `anomaly_detection/pyod_trainer.py`
- `anomaly_detection/hyperparameter_tuner.py`
- `anomaly_detection/model_exporter.py`
- `ui/training_panel.py`

---

### Phase 6: Edge Impulse SDK Code Generation (Week 6-7)

**Deliverables:**
- [x] **C++ code generator:**
  - Template-based generation (Jinja2)
  - Generate `custom_dsp.cpp` with `extract_custom_features()` function
  - Use SDK utilities: `numpy::rms()`, `spectral::processing::fft()`, etc.
  - Implement only LLM-selected features (typically 5)
  - Example features to implement:
    - RMS (use `numpy::rms`)
    - FFT spectral power bin (use `numpy::rfft` + bin selection)
    - Zero-crossing rate (custom implementation)
    - Mean derivative (diff + mean)
    - PySR formulas (translate to C++ math)
- [x] **Model parameter headers:**
  - `pca_model.h`: PCA components as 2D array, mean vector, threshold
  - `lof_model.h`: neighbor distances, LOF scores, k_neighbors
  - `copod_model.h`: empirical CDF tables
  - Inline scoring function (e.g., `float pca_anomaly_score(float* features, int n_features)`)
- [x] **Main inference loop:**
  - `main.cpp` with example usage:
    ```cpp
    #include "edge-impulse-sdk/classifier/ei_run_classifier.h"
    #include "custom_dsp.h"
    #include "pca_model.h"

    int main() {
        signal_t signal;
        signal.total_length = WINDOW_SIZE * N_AXES;
        signal.get_data = &get_sensor_data;

        ei_impulse_result_t result;
        run_classifier(&signal, &result);

        float anomaly_score = pca_anomaly_score(result.classification, N_FEATURES);
        printf("Anomaly score: %.3f\n", anomaly_score);
    }
    ```
- [x] **CMakeLists.txt generation:**
  - Link inferencing-sdk-cpp (as submodule or prebuilt lib)
  - Compiler flags: `-O3 -mcpu=cortex-m4 -mfloat-abi=hard`
  - Include paths: `inferencing-sdk-cpp/`, `CMSIS/DSP/Include/`
  - Output target: `anomaly_detector.elf`
- [x] **Apache 2.0 compliance:**
  - Auto-generate LICENSE file (copy from SDK)
  - Generate NOTICE file listing SDK components
  - Add attribution comments in generated C++ files

**Key Files:**
- `codegen/dsp_generator.py`
- `codegen/model_headers.py`
- `codegen/cmake_generator.py`
- `codegen/templates/custom_dsp.cpp.j2`
- `codegen/templates/pca_model.h.j2`
- `codegen/templates/CMakeLists.txt.j2`
- `ui/dsp_panel.py`

---

### Phase 7: Firmware Build System (Week 7-8)

**Deliverables:**
- [x] **inferencing-sdk-cpp integration:**
  - Bundle SDK as Git submodule in `sdk/` directory
  - Provide option to use system-installed SDK
  - SDK version pinning (recommend v1.0.0+)
- [x] **CMake configuration:**
  - Detect MinGW-w64 on Windows (check `gcc --version`)
  - Optional: detect ARM GCC for cross-compilation
  - Set compiler flags:
    - `-std=c++11`
    - `-O3` (optimization)
    - `-Wall -Wextra` (warnings)
    - `-DEIDSP_QUANTIZE_FILTERBANK=0` (disable filterbank quantization)
  - Link libraries: CMSIS-DSP, inferencing SDK
- [x] **Build automation:**
  - One-click "Compile Firmware" button in UI
  - Run CMake configure step
  - Run CMake build step (with progress bar)
  - Real-time build log viewer with error highlighting
  - Parse GCC errors and provide actionable hints
- [x] **Output artifacts:**
  - Standalone `.exe` for x86 testing
  - `.elf` for ARM Cortex-M flashing
  - `.bin` / `.hex` for direct MCU programming
  - Memory usage report (RAM, Flash)
- [x] **Validation:**
  - Test inference on sample data
  - Compare Python anomaly scores vs. C++ output
  - Measure inference latency (profile with `ei_profiler`)

**Key Files:**
- `build/cmake_wrapper.py`
- `build/compiler_detector.py`
- `build/build_runner.py`
- `build/validator.py`
- `ui/build_panel.py`

---

### Phase 8: Testing & Validation (Week 8-9)

**Deliverables:**
- [x] **Example datasets:**
  - NASA bearing dataset (vibration, temperature)
  - CWRU bearing fault dataset
  - Pump cavitation dataset
  - Synthetic anomaly generator (inject faults into nominal data)
- [x] **End-to-end workflow tests:**
  - Test 1: CSV → tsfresh → LLM → PCA → C++ generation → build
  - Test 2: Database → PySR → LOF → deployment
  - Test 3: Streaming → fallback ranking → AutoEncoder → inference
- [x] **Accuracy validation:**
  - Compare Python anomaly scores vs. C++ output (tolerance: <1% difference)
  - Measure false positive rate on nominal data
  - Measure detection rate on injected anomalies
- [x] **Performance profiling:**
  - RAM usage during feature extraction (target: <2 GB)
  - LLM inference time (target: <30 seconds)
  - C++ inference latency (target: <1 ms per window)
  - Firmware size (target: <100 KB Flash, <10 KB RAM)
- [x] **Unit tests:**
  - Feature extraction correctness (compare with tsfresh reference)
  - LLM prompt/response parsing
  - C++ code generation (syntax validation)
  - Model parameter export (numerical accuracy)

**Key Files:**
- `tests/test_feature_extraction.py`
- `tests/test_llm_selector.py`
- `tests/test_codegen.py`
- `tests/test_e2e_workflow.py`
- `tests/datasets/` (example data)

---

### Phase 9: Packaging & Distribution (Week 9-10)

**Deliverables:**
- [x] **PyInstaller bundle:**
  - Single executable: `CiRAStudio.exe`
  - Embed Python runtime (no external Python required)
  - Include libraries: CustomTkinter, tsfresh, PyOD, llama-cpp-python
  - Bundle Llama-3.2-3B-Instruct-Q4_K_M model (~2.5 GB)
  - Include MinGW-w64 toolchain (portable, ~500 MB)
  - Package inferencing-sdk-cpp source (~50 MB)
  - Total size: ~3.5 GB (compressed: ~1.5 GB with UPX)
- [x] **NSIS installer:**
  - Professional installer UI
  - Desktop shortcut, Start Menu integration
  - File association for `.ciraproject` files
  - Optional: install CMake if not present
  - Optional: install ARM GCC for embedded targets
  - Uninstaller
- [x] **Dependencies check:**
  - Auto-detect: CMake, GCC, Python (for advanced users)
  - Display system requirements on first run
  - Provide download links for missing tools
- [x] **Version management:**
  - Semantic versioning (v1.0.0)
  - Update checker (optional, respects offline mode)
  - Changelog viewer in UI

**Key Files:**
- `build_scripts/pyinstaller_spec.py`
- `build_scripts/nsis_installer.nsi`
- `build_scripts/package.sh` (automation script)

---

### Phase 10: Documentation & Polish (Week 10-11)

**Deliverables:**
- [x] **User guide (Markdown/HTML):**
  - Getting started: "Predictive Maintenance in 10 Minutes"
  - Data ingestion tutorial (CSV, database, API)
  - Feature engineering best practices
  - LLM prompt customization guide
  - Model selection guide (when to use PCA vs. LOF vs. AutoEncoder)
  - Deployment workflow (MCU flashing, validation)
  - Troubleshooting common errors
- [x] **API documentation:**
  - Extending data sources (plugin API)
  - Custom feature extractors
  - Custom anomaly algorithms (PyOD wrapper)
  - C++ code generation templates
- [x] **Example projects:**
  1. Motor vibration anomaly detection (bearing wear)
  2. Temperature-based fault detection (overheating)
  3. Multi-sensor fusion (vibration + current + temp)
  4. Pump cavitation detection
- [x] **Video tutorials (optional):**
  - Installation and setup (5 min)
  - End-to-end workflow walkthrough (15 min)
  - Advanced: Custom feature engineering (10 min)
- [x] **UI polish:**
  - Tooltips for all buttons/fields
  - Keyboard shortcuts (Ctrl+N: New Project, Ctrl+O: Open, etc.)
  - Error messages with actionable hints
  - Progress indicators for long operations
  - Multi-threading: feature extraction and LLM inference in background
  - Responsive layout (resize-friendly)
- [x] **Performance optimization:**
  - Lazy loading for large datasets
  - Feature extraction parallelization (use all CPU cores)
  - LLM inference caching (reuse results for similar prompts)
  - C++ compilation caching (ccache integration)

**Key Files:**
- `docs/user_guide.md`
- `docs/api_reference.md`
- `docs/examples/` (project files)
- `docs/videos/` (optional)

---

## Deliverables

### Software Components

1. **CiRA FutureEdge Studio Application**
   - Windows desktop executable (`CiRAStudio.exe`)
   - Full offline operation (no internet required)
   - Modern UI with dark/light themes
   - Multi-stage workflow: Data → Features → LLM → Training → Deployment

2. **Backend Scripts**
   - `feature_extractor.py`: tsfresh + PySR + custom DSP
   - `llm_feature_selector.py`: Local LLM-based feature engineering
   - `anomaly_trainer.py`: PyOD model training
   - `dsp_generator.py`: C++ code generation for Edge Impulse SDK
   - `cmake_wrapper.py`: Build system automation

3. **Generated Edge Code**
   - `custom_dsp.cpp/.h`: Feature extraction implementation
   - `model_params.h`: Anomaly model parameters (PCA/LOF/etc.)
   - `main.cpp`: Inference loop example
   - `CMakeLists.txt`: Build configuration
   - `LICENSE` and `NOTICE`: Apache 2.0 compliance

4. **SDK Integration**
   - Bundled `inferencing-sdk-cpp` (v1.0.0+)
   - CMSIS-DSP libraries
   - Example projects for Cortex-M4, ESP32

5. **Packaging Assets**
   - PyInstaller spec file
   - NSIS installer script
   - Bundled models: Llama-3.2-3B-Instruct-Q4_K_M
   - Bundled toolchain: MinGW-w64
   - Documentation (HTML/PDF)

### Documentation

1. **User Guide**
   - Installation and setup
   - End-to-end workflow tutorial
   - Feature engineering best practices
   - Model selection guide
   - Deployment and validation

2. **API Reference**
   - Data source plugin API
   - Custom feature extractor API
   - Anomaly algorithm wrapper API
   - Code generation template API

3. **Example Projects**
   - Motor vibration anomaly detection
   - Temperature fault detection
   - Multi-sensor fusion
   - Pump cavitation detection

4. **Video Tutorials (Optional)**
   - Installation (5 min)
   - Workflow walkthrough (15 min)
   - Advanced feature engineering (10 min)

---

## Constraints & Compliance

### Functional Constraints

1. **Strictly Offline Operation**
   - No Edge Impulse Studio integration
   - No cloud APIs (all processing local)
   - No runtime internet access
   - No telemetry or usage tracking
   - Optional: update checker (respects offline mode)

2. **Feature Limits**
   - Maximum 5 output features (embedded deployment constraint)
   - Allowed feature types: `rms`, `mean_derivative`, `spectral_power_bin`, `zero_crossing_rate`, `pysr_formula`
   - Physical interpretability required (no black-box features)

3. **Hardware Requirements**
   - Minimum: Windows 10, 8 GB RAM, 4-core CPU, 10 GB storage
   - Recommended: Windows 11, 16 GB RAM, 8-core CPU, 20 GB storage
   - LLM inference: AVX2 instruction set (most modern CPUs)
   - Optional: NVIDIA GPU for llama.cpp acceleration (via CUDA)

### Licensing & Compliance

1. **Apache 2.0 License (inferencing-sdk-cpp)**
   - Include LICENSE file in all distributions
   - Include NOTICE file listing SDK components
   - Attribute Edge Impulse in generated code comments
   - Do NOT remove copyright notices from SDK files
   - Reference: https://github.com/edgeimpulse/inferencing-sdk-cpp/blob/main/LICENSE

2. **BSD 3-Clause Clear License (CMSIS components)**
   - Some SDK components use BSD 3-Clause Clear
   - Include separate LICENSE file for CMSIS
   - Reference: https://github.com/edgeimpulse/inferencing-sdk-cpp/blob/main/LICENSE.3-clause-bsd-clear

3. **CiRA FutureEdge Studio License**
   - Recommend: Apache 2.0 or MIT (compatible with SDK)
   - Clearly separate studio code from SDK code
   - Include attribution in About dialog

4. **Model Licenses**
   - Llama-3.2: Meta Llama 3.2 Community License (permissive, commercial use allowed)
   - Qwen2.5: Apache 2.0
   - Phi-3.5: MIT License
   - All recommended models allow commercial use

### Prohibited Items

1. **No Edge Impulse Cloud Integration**
   - Do NOT use Edge Impulse Studio APIs
   - Do NOT generate `.eim` files (Edge Impulse export format)
   - Do NOT integrate with Edge Impulse account system
   - Studio operates 100% independently

2. **No Credential Harvesting**
   - Do NOT collect user credentials
   - Do NOT scan for SSH keys, browser cookies, or wallets
   - Only access data explicitly provided by user (CSV, database connection strings)

3. **No Malicious Code**
   - Do NOT create backdoors or remote access tools
   - Do NOT implement keyloggers or screen capture
   - All code must be defensive security-focused (anomaly detection for legitimate use cases)

---

## Success Metrics

### Performance Targets

1. **Feature Extraction Speed**
   - 1000 windows (100 samples each) in <60 seconds
   - tsfresh: <30 seconds for 700+ features
   - PySR: <90 seconds for symbolic regression

2. **LLM Inference Time**
   - Feature selection prompt: <30 seconds on 4-core CPU
   - Llama-3.2-3B: ~10 tokens/sec on AVX2 CPU

3. **Model Training Time**
   - PCA: <5 seconds on 10,000 samples
   - LOF: <30 seconds on 10,000 samples
   - AutoEncoder: <5 minutes on GPU, <30 minutes on CPU

4. **C++ Compilation Time**
   - MinGW build: <60 seconds for complete firmware
   - ARM GCC cross-compile: <90 seconds

5. **Edge Inference Performance**
   - Latency: <1 ms per window (5 features, PCA scoring)
   - RAM: <10 KB (feature buffer + model params)
   - Flash: <100 KB (code + model)

### User Experience Targets

1. **Workflow Completion Time**
   - Beginner (with tutorial): <30 minutes from CSV to deployed firmware
   - Expert: <10 minutes

2. **UI Responsiveness**
   - Button click response: <100 ms
   - Panel switch: <200 ms
   - Long operations: background thread with progress bar

3. **Error Handling**
   - Clear error messages (no cryptic stack traces to user)
   - Actionable hints ("Install CMake from https://cmake.org")
   - Graceful degradation (fallback to statistical ranking if LLM fails)

### Quality Targets

1. **Accuracy**
   - Feature extraction: 100% match with tsfresh reference implementation
   - Python vs. C++ inference: <1% numerical difference
   - False positive rate: <5% on nominal data

2. **Reliability**
   - Crash rate: <0.1% (no crashes during normal operation)
   - LLM fallback trigger rate: <10% (most prompts succeed)

3. **Compatibility**
   - Windows 10/11: 100% support
   - Edge Impulse SDK versions: 1.0.0 to latest
   - MCU targets: Cortex-M4, M7, ESP32, ESP32-S3

---

## Development Timeline

| **Phase** | **Duration** | **Key Milestones** |
|-----------|-------------|-------------------|
| Phase 1: Foundation | 2 weeks | UI shell, project manager, navigation |
| Phase 2: Data Ingestion | 1 week | Multi-source loaders, windowing, visualization |
| Phase 3: Feature Extraction | 2 weeks | tsfresh, PySR, custom DSP, ranking |
| Phase 4: LLM Selection | 2 weeks | Model loader, prompt engine, fallback |
| Phase 5: Model Training | 2 weeks | PyOD integration, hyperparameter tuning |
| Phase 6: Code Generation | 2 weeks | C++ DSP blocks, model headers, templates |
| Phase 7: Build System | 1 week | CMake, MinGW/ARM GCC, SDK integration |
| Phase 8: Testing | 2 weeks | End-to-end tests, validation, profiling |
| Phase 9: Packaging | 1 week | PyInstaller, NSIS installer |
| Phase 10: Documentation | 1 week | User guide, API docs, examples |
| **Total** | **16 weeks** | **~4 months for MVP** |

---

## Appendix A: Key File Structure

```
CiRA-FutureEdge-Studio/
├── main.py                          # Application entry point
├── requirements.txt                 # Python dependencies
├── README.md                        # Project overview
├── LICENSE                          # Studio license (Apache 2.0)
├── ui/
│   ├── main_window.py               # Main window (CustomTkinter)
│   ├── navigation.py                # Sidebar navigation
│   ├── theme.py                     # Dark/light themes
│   ├── data_panel.py                # Data ingestion UI
│   ├── feature_panel.py             # Feature extraction UI
│   ├── llm_panel.py                 # LLM selection UI
│   ├── training_panel.py            # Model training UI
│   ├── dsp_panel.py                 # Code generation UI
│   └── build_panel.py               # Build system UI
├── core/
│   ├── project.py                   # Project state management
│   ├── windowing.py                 # Time-series windowing
│   └── config.py                    # Application configuration
├── data_sources/
│   ├── csv_loader.py                # CSV data loader
│   ├── db_connector.py              # Database connector
│   ├── api_poller.py                # REST API poller
│   └── stream_simulator.py          # Mock streaming
├── feature_extraction/
│   ├── tsfresh_extractor.py         # tsfresh wrapper
│   ├── pysr_engine.py               # PySR wrapper
│   ├── custom_dsp.py                # Custom DSP features
│   └── ranker.py                    # Statistical ranking
├── llm/
│   ├── model_loader.py              # GGUF model loader
│   ├── prompt_engine.py             # Prompt template engine
│   ├── feature_selector.py          # LLM-based selection
│   └── fallback.py                  # Statistical fallback
├── anomaly_detection/
│   ├── pyod_trainer.py              # PyOD wrapper
│   ├── hyperparameter_tuner.py      # Grid search
│   └── model_exporter.py            # Export to JSON/C++
├── codegen/
│   ├── dsp_generator.py             # C++ DSP code generator
│   ├── model_headers.py             # Model parameter headers
│   ├── cmake_generator.py           # CMakeLists.txt generator
│   └── templates/                   # Jinja2 templates
│       ├── custom_dsp.cpp.j2
│       ├── pca_model.h.j2
│       └── CMakeLists.txt.j2
├── build/
│   ├── cmake_wrapper.py             # CMake automation
│   ├── compiler_detector.py         # Detect MinGW/ARM GCC
│   ├── build_runner.py              # Build execution
│   └── validator.py                 # Output validation
├── tests/
│   ├── test_feature_extraction.py
│   ├── test_llm_selector.py
│   ├── test_codegen.py
│   ├── test_e2e_workflow.py
│   └── datasets/                    # Example datasets
├── models/                          # LLM models (downloaded)
│   └── llama-3.2-3b-instruct-q4_k_m.gguf
├── sdk/                             # inferencing-sdk-cpp (submodule)
├── toolchain/                       # MinGW-w64 (bundled)
├── docs/
│   ├── user_guide.md
│   ├── api_reference.md
│   └── examples/
├── build_scripts/
│   ├── pyinstaller_spec.py          # PyInstaller configuration
│   ├── nsis_installer.nsi           # NSIS installer script
│   └── package.sh                   # Automation script
└── output/                          # Generated firmware projects
    └── example_project/
        ├── custom_dsp.cpp
        ├── custom_dsp.h
        ├── pca_model.h
        ├── main.cpp
        ├── CMakeLists.txt
        ├── LICENSE
        └── NOTICE
```

---

## Appendix B: LLM Model Download Instructions

**For Llama-3.2-3B-Instruct-Q4_K_M:**

1. Visit HuggingFace: https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF
2. Download file: `Llama-3.2-3B-Instruct-Q4_K_M.gguf` (~2.5 GB)
3. Place in `models/` directory
4. Studio will auto-detect on startup

**Programmatic download (llm/model_loader.py):**
```python
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(
    repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
    filename="Llama-3.2-3B-Instruct-Q4_K_M.gguf",
    local_dir="./models",
    local_dir_use_symlinks=False
)
```

---

## Appendix C: Edge Impulse SDK Integration

**SDK Repository:**
- URL: https://github.com/edgeimpulse/inferencing-sdk-cpp
- License: Apache 2.0 (some components BSD 3-Clause Clear)
- Version: Pin to v1.0.0 or later

**Integration Methods:**

1. **Git Submodule (Recommended):**
   ```bash
   git submodule add https://github.com/edgeimpulse/inferencing-sdk-cpp sdk/inferencing-sdk-cpp
   git submodule update --init --recursive
   ```

2. **Manual Bundle:**
   - Clone SDK repository
   - Copy to `sdk/inferencing-sdk-cpp/`
   - Update `CMakeLists.txt` to point to local path

**CMake Integration:**
```cmake
# CMakeLists.txt (generated)
cmake_minimum_required(VERSION 3.20)
project(anomaly_detector)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -Wall -Wextra")

# Edge Impulse SDK
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/sdk/inferencing-sdk-cpp)

# Your custom DSP and model
add_executable(anomaly_detector
    main.cpp
    custom_dsp.cpp
)

target_include_directories(anomaly_detector PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/sdk/inferencing-sdk-cpp
)

target_link_libraries(anomaly_detector
    ei_inference_sdk
    cmsis_dsp
)
```

---

## Appendix D: Physical Intuition Examples

**Rotating Machinery:**
- **Imbalance:** Vibration peak at 1x rotation frequency
- **Misalignment:** Vibration at 2x, 3x rotation frequency
- **Bearing wear:** High-frequency harmonics (>50 Hz), bearing pass frequencies
- **Looseness:** Broad-spectrum vibration increase

**Thermal Systems:**
- **Overheating:** Gradual temperature rise (mean derivative > threshold)
- **Thermal shock:** Rapid temperature change (high standard deviation)
- **Insufficient cooling:** Temperature correlates with load but exceeds nominal range

**Electrical Systems:**
- **Motor overload:** Current spikes, power factor decrease
- **Voltage sag:** RMS voltage below nominal
- **Harmonic distortion:** FFT shows odd harmonics (3rd, 5th, 7th)

---

## Appendix E: Recommended Reading

**Feature Engineering:**
- Christ, M. et al. (2018). "Time Series FeatuRe Extraction on basis of Scalable Hypothesis tests (tsfresh)." Neurocomputing.
- Cranmer, M. (2023). "Interpretable Machine Learning for Science with PySR and SymbolicRegression.jl." arXiv:2305.01582.

**Anomaly Detection:**
- Zhao, Y. et al. (2019). "PyOD: A Python Toolbox for Scalable Outlier Detection." JMLR.
- Chandola, V. et al. (2009). "Anomaly detection: A survey." ACM Computing Surveys.

**Edge ML:**
- Edge Impulse. (2024). "Embedded Machine Learning with Edge Impulse." Online documentation.
- Warden, P. & Situnayake, D. (2019). "TinyML: Machine Learning with TensorFlow Lite on Arduino and Ultra-Low-Power Microcontrollers." O'Reilly.

**LLM for Engineering:**
- Radford, A. et al. (2021). "Learning Transferable Visual Models From Natural Language Supervision." ICML.
- Meta. (2024). "Llama 3.2: Open Foundation Models." Technical Report.

---

## Document Version

- **Version:** 1.0
- **Date:** 2025-01-11
- **Authors:** Project Team
- **Status:** Final Specification for Development

---

## Revision History

| **Version** | **Date** | **Changes** | **Author** |
|------------|---------|-----------|---------|
| 0.1 | 2025-01-10 | Initial draft | Team |
| 0.5 | 2025-01-10 | Added LLM specification | Team |
| 0.8 | 2025-01-11 | Added CustomTkinter decision | Team |
| 1.0 | 2025-01-11 | Final specification | Team |

---

**END OF SPECIFICATION**
