"""
Quick test script for Phase 1 implementation.

Tests core functionality without GUI.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.project import Project, ProjectManager
from loguru import logger


def test_config():
    """Test configuration management."""
    print("\n=== Testing Configuration ===")

    # Create config
    config = Config()
    print(f"✓ Config created: {config.app_name} v{config.version}")

    # Save config
    test_config_path = Path("test_config.json")
    config.save(test_config_path)
    print(f"✓ Config saved to {test_config_path}")

    # Load config
    loaded_config = Config.load(test_config_path)
    print(f"✓ Config loaded: {loaded_config.app_name}")

    # Cleanup
    test_config_path.unlink()
    print("✓ Cleanup complete")

    return True


def test_project():
    """Test project management."""
    print("\n=== Testing Project Management ===")

    # Create project manager
    pm = ProjectManager()
    print("✓ Project manager created")

    # Create new project
    workspace = Path("test_workspace")
    workspace.mkdir(exist_ok=True)

    project = pm.new_project("Test Project", "rotating_machinery", workspace)
    print(f"✓ Project created: {project.name}")
    print(f"  Project ID: {project.project_id}")
    print(f"  Domain: {project.get_domain_description()}")

    # Save project
    project.save()
    print(f"✓ Project saved to {project.project_path}")

    # Load project
    loaded_project = Project.load(Path(project.project_path))
    print(f"✓ Project loaded: {loaded_project.name}")

    # Test project operations
    project.mark_stage_completed("data")
    print(f"✓ Stage marked as completed: data")
    print(f"  Completed stages: {project.completed_stages}")

    # Test project directories
    data_dir = project.get_data_dir()
    models_dir = project.get_models_dir()
    output_dir = project.get_output_dir()
    print(f"✓ Project directories created:")
    print(f"  Data: {data_dir}")
    print(f"  Models: {models_dir}")
    print(f"  Output: {output_dir}")

    # Cleanup
    import shutil
    shutil.rmtree(workspace)
    print("✓ Cleanup complete")

    return True


def test_imports():
    """Test that all required modules can be imported."""
    print("\n=== Testing Module Imports ===")

    try:
        import customtkinter
        print(f"✓ customtkinter: {customtkinter.__version__}")
    except ImportError as e:
        print(f"✗ customtkinter: {e}")
        return False

    try:
        import pandas
        print(f"✓ pandas: {pandas.__version__}")
    except ImportError as e:
        print(f"✗ pandas: {e}")
        return False

    try:
        import numpy
        print(f"✓ numpy: {numpy.__version__}")
    except ImportError as e:
        print(f"✗ numpy: {e}")
        return False

    try:
        import sklearn
        print(f"✓ scikit-learn: {sklearn.__version__}")
    except ImportError as e:
        print(f"✗ scikit-learn: {e}")
        return False

    try:
        from loguru import logger
        print(f"✓ loguru: imported successfully")
    except ImportError as e:
        print(f"✗ loguru: {e}")
        return False

    # Optional: test heavy dependencies (won't fail if missing)
    try:
        import tsfresh
        print(f"✓ tsfresh: {tsfresh.__version__}")
    except ImportError:
        print(f"⚠ tsfresh: not installed (optional for Phase 1)")

    try:
        from llama_cpp import Llama
        print(f"✓ llama-cpp-python: imported successfully")
    except ImportError:
        print(f"⚠ llama-cpp-python: not installed (optional for Phase 1)")

    try:
        import pyod
        print(f"✓ pyod: {pyod.__version__}")
    except ImportError:
        print(f"⚠ pyod: not installed (optional for Phase 1)")

    return True


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
        print(f"✗ Module imports failed: {e}")
        results.append(("Module Imports", False))

    # Test configuration
    try:
        results.append(("Configuration", test_config()))
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        results.append(("Configuration", False))

    # Test project management
    try:
        results.append(("Project Management", test_project()))
    except Exception as e:
        print(f"✗ Project management test failed: {e}")
        results.append(("Project Management", False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Phase 1 is ready.")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. Create a new project and explore the UI")
        print("3. Proceed to Phase 2 implementation")
        return 0
    else:
        print("\n⚠ Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
