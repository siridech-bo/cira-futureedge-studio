"""
Test project creation functionality
"""

from pathlib import Path
from core.config import Config
from core.project import ProjectManager

def test_project_creation():
    """Test creating a new project"""
    print("=" * 60)
    print("Testing Project Creation")
    print("=" * 60)

    try:
        # Initialize config
        print("\n[1/4] Initializing config...")
        config = Config()
        print(f"[OK] Config initialized")
        print(f"      Output dir: {config.output_dir}")
        print(f"      Output dir exists: {config.output_dir.exists()}")

        # Initialize project manager
        print("\n[2/4] Creating project manager...")
        pm = ProjectManager()
        print(f"[OK] Project manager created")

        # Create test project
        print("\n[3/4] Creating new project...")
        project_name = "Test Project"
        domain = "rotating_machinery"
        workspace = config.output_dir

        print(f"      Name: {project_name}")
        print(f"      Domain: {domain}")
        print(f"      Workspace: {workspace}")

        project = pm.new_project(project_name, domain, workspace)
        print(f"[OK] Project created")
        print(f"      Project ID: {project.project_id}")
        print(f"      Project path: {project.project_path}")

        # Save project
        print("\n[4/4] Saving project...")
        project.save()
        print(f"[OK] Project saved to: {project.project_path}")

        # Verify file exists
        project_file = Path(project.project_path)
        if project_file.exists():
            print(f"[OK] Project file verified: {project.project_path}")
            print(f"      File size: {project_file.stat().st_size} bytes")
        else:
            print(f"[FAIL] Project file not found: {project.project_path}")
            return False

        print("\n" + "=" * 60)
        print("[SUCCESS] All tests passed!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_project_creation()
