"""
Quick test script for Phase 1 implementation (Windows-safe).

Tests core functionality without GUI.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.project import Project, ProjectManager


def test_config():
    """Test configuration management."""
    print("\n=== Testing Configuration ===")

    # Create config
    config = Config()
    print(f"[OK] Config created: {config.app_name} v{config.version}")

    # Save config
    test_config_path = Path("test_config.json")
    config.save(test_config_path)
    print(f"[OK] Config saved to {test_config_path}")

    # Load config
    loaded_config = Config.load(test_config_path)
    print(f"[OK] Config loaded: {loaded_config.app_name}")

    # Cleanup
    test_config_path.unlink()
    print("[OK] Cleanup complete")

    return True


def test_project():
    """Test project management."""
    print("\n=== Testing Project Management ===")

    # Create project manager
    pm = ProjectManager()
    print("[OK] Project manager created")

    # Create new project
    workspace = Path("test_workspace")
    workspace.mkdir(exist_ok=True)

    project = pm.new_project("Test Project", "rotating_machinery", workspace)
    print(f"[OK] Project created: {project.name}")
    print(f"     Project ID: {project.project_id}")
    print(f"     Domain: {project.get_domain_description()}")

    # Save project
    project.save()
    print(f"[OK] Project saved to {project.project_path}")

    # Load project
    loaded_project = Project.load(Path(project.project_path))
    print(f"[OK] Project loaded: {loaded_project.name}")

    # Test project operations
    project.mark_stage_completed("data")
    print(f"[OK] Stage marked as completed: data")
    print(f"     Completed stages: {project.completed_stages}")

    # Test project directories
    data_dir = project.get_data_dir()
    models_dir = project.get_models_dir()
    output_dir = project.get_output_dir()
    print(f"[OK] Project directories created:")
    print(f"     Data: {data_dir}")
    print(f"     Models: {models_dir}")
    print(f"     Output: {output_dir}")

    # Cleanup
    import shutil
    shutil.rmtree(workspace)
    print("[OK] Cleanup complete")

    return True


def test_imports():
    """Test that all required modules can be imported."""
    print("\n=== Testing Module Imports ===")
    all_ok = True

    try:
        import customtkinter
        print(f"[OK] customtkinter: {customtkinter.__version__}")
    except ImportError as e:
        print(f"[FAIL] customtkinter: {e}")
        all_ok = False

    try:
        import pandas
        print(f"[OK] pandas: {pandas.__version__}")
    except ImportError as e:
        print(f"[FAIL] pandas: {e}")
        all_ok = False

    try:
        import numpy
        print(f"[OK] numpy: {numpy.__version__}")
    except ImportError as e:
        print(f"[FAIL] numpy: {e}")
        all_ok = False

    try:
        import sklearn
        print(f"[OK] scikit-learn: {sklearn.__version__}")
    except ImportError as e:
        print(f"[FAIL] scikit-learn: {e}")
        all_ok = False

    try:
        from loguru import logger
        print(f"[OK] loguru: imported successfully")
    except ImportError as e:
        print(f"[FAIL] loguru: {e}")
        all_ok = False

    # Optional: test heavy dependencies (won't fail if missing)
    try:
        import tsfresh
        print(f"[OK] tsfresh: {tsfresh.__version__}")
    except ImportError:
        print(f"[INFO] tsfresh: not installed (optional for Phase 1)")

    try:
        from llama_cpp import Llama
        print(f"[OK] llama-cpp-python: imported successfully")
    except ImportError:
        print(f"[INFO] llama-cpp-python: not installed (optional for Phase 1)")

    try:
        import pyod
        print(f"[OK] pyod: {pyod.__version__}")
    except ImportError:
        print(f"[INFO] pyod: not installed (optional for Phase 1)")

    return all_ok


def main():
    """Run all tests."""
    print("=" * 60)
    print("CiRA FutureEdge Studio - Phase 1 Test Suite")
    print("=" * 60)

    results = []

    # Test imports
    try:
        results.append(("Module Imports", test_imports()))
    except Exception as e:
        print(f"[FAIL] Module imports failed: {e}")
        results.append(("Module Imports", False))

    # Test configuration
    try:
        results.append(("Configuration", test_config()))
    except Exception as e:
        print(f"[FAIL] Configuration test failed: {e}")
        results.append(("Configuration", False))

    # Test project management
    try:
        results.append(("Project Management", test_project()))
    except Exception as e:
        print(f"[FAIL] Project management test failed: {e}")
        results.append(("Project Management", False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n*** All tests passed! Phase 1 is ready. ***")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. Create a new project and explore the UI")
        print("3. Proceed to Phase 2 implementation")
        return 0
    else:
        print("\n*** Some tests failed. Please check the output above. ***")
        return 1


if __name__ == "__main__":
    sys.exit(main())
