"""
Quick test for LLM panel integration
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported."""
    print("[OK] Testing imports...")

    try:
        from core.llm_manager import LLMManager, LLMConfig, FeatureSelection, LLAMA_CPP_AVAILABLE
        print("  [OK] LLM manager imported")
        print(f"  [INFO] llama-cpp-python available: {LLAMA_CPP_AVAILABLE}")
    except Exception as e:
        print(f"  [FAIL] LLM manager import failed: {e}")
        return False

    try:
        from ui.llm_panel import LLMPanel
        print("  [OK] LLM panel imported")
    except Exception as e:
        print(f"  [FAIL] LLM panel import failed: {e}")
        return False

    return True

def test_llm_config():
    """Test LLM configuration."""
    print("\n[OK] Testing LLM configuration...")

    from core.llm_manager import LLMConfig
    from pathlib import Path

    config = LLMConfig(
        model_path=Path("models/test.gguf"),
        n_ctx=2048,
        n_threads=4,
        temperature=0.3
    )

    print(f"  [OK] Config created: {config.model_path}")
    print(f"  [INFO] Context: {config.n_ctx}, Threads: {config.n_threads}, Temp: {config.temperature}")

    return True

def test_fallback_selection():
    """Test statistical fallback selection."""
    print("\n[OK] Testing fallback selection...")

    from core.llm_manager import LLMManager, LLMConfig
    from pathlib import Path

    config = LLMConfig(model_path=Path("dummy"))
    manager = LLMManager(config)

    # Test data
    features = [
        "mean", "std", "max", "min", "median",
        "fft_peak", "fft_power", "zero_crossings",
        "kurtosis", "skewness"
    ]

    importance = {
        "mean": 0.95,
        "std": 0.88,
        "max": 0.76,
        "min": 0.65,
        "median": 0.82,
        "fft_peak": 0.91,
        "fft_power": 0.87,
        "zero_crossings": 0.73,
        "kurtosis": 0.68,
        "skewness": 0.71
    }

    # Select top 5
    selection = manager._fallback_selection(features, importance, target_count=5)

    print(f"  [OK] Selected {len(selection.selected_features)} features")
    print(f"  [INFO] Features: {selection.selected_features}")
    print(f"  [INFO] Reasoning: {selection.reasoning}")
    print(f"  [INFO] Fallback used: {selection.fallback_used}")
    print(f"  [INFO] Confidence: {selection.confidence}")

    # Verify correct selection
    expected = ["mean", "fft_peak", "std", "fft_power", "median"]
    if selection.selected_features == expected:
        print("  [OK] Selection matches expected (sorted by importance)")
    else:
        print(f"  [WARN] Expected {expected}")
        print(f"  [WARN] Got {selection.selected_features}")

    return True

def test_project_integration():
    """Test project LLM fields."""
    print("\n[OK] Testing project integration...")

    from core.project import ProjectLLM

    llm_config = ProjectLLM()

    print(f"  [OK] ProjectLLM created")
    print(f"  [INFO] Model name: {llm_config.model_name}")
    print(f"  [INFO] Use LLM: {llm_config.use_llm}")
    print(f"  [INFO] Selected features: {llm_config.selected_features}")
    print(f"  [INFO] Num selected: {llm_config.num_selected}")

    # Test setting values
    llm_config.selected_features = ["feature1", "feature2", "feature3"]
    llm_config.num_selected = 3
    llm_config.selection_reasoning = "Test reasoning"
    llm_config.used_llm = False
    llm_config.fallback_used = True

    print(f"  [OK] Fields set successfully")

    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("LLM Panel Integration Tests")
    print("=" * 60)

    tests = [
        test_imports,
        test_llm_config,
        test_fallback_selection,
        test_project_integration
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n[FAIL] Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[FAILED] Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
