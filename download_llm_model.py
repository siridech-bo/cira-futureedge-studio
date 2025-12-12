"""
Download Llama-3.2-3B model from HuggingFace
"""

from huggingface_hub import hf_hub_download
from pathlib import Path
import sys

def download_model():
    """Download the LLM model with progress tracking."""
    print("=" * 60)
    print("Downloading Llama-3.2-3B-Instruct Model")
    print("=" * 60)
    print()
    print("Repository: bartowski/Llama-3.2-3B-Instruct-GGUF")
    print("File: Llama-3.2-3B-Instruct-Q4_K_M.gguf")
    print("Size: ~2.5 GB")
    print()
    print("This may take 10-30 minutes depending on your connection...")
    print()

    try:
        # Download model
        model_path = hf_hub_download(
            repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
            filename="Llama-3.2-3B-Instruct-Q4_K_M.gguf",
            local_dir=str(Path(__file__).parent / "models"),
            local_dir_use_symlinks=False,
            resume_download=True  # Resume if interrupted
        )

        print()
        print("=" * 60)
        print("✓ Download complete!")
        print("=" * 60)
        print(f"Model saved to: {model_path}")
        print()
        print("You can now use the LLM in CiRA FutureEdge Studio!")
        print()

        return 0

    except KeyboardInterrupt:
        print("\n\n[Interrupted] Download can be resumed by running this script again.")
        return 1

    except Exception as e:
        print(f"\n\n[Error] Download failed: {e}")
        print("\nPlease check:")
        print("1. Internet connection")
        print("2. Disk space (need ~3 GB free)")
        print("3. HuggingFace is accessible")
        return 1

if __name__ == "__main__":
    sys.exit(download_model())
