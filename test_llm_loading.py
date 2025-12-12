"""
Test LLM model loading
"""

from pathlib import Path
import sys

def test_llm_loading():
    """Test loading the LLM model."""
    print("=" * 60)
    print("Testing LLM Model Loading")
    print("=" * 60)
    print()

    model_path = Path("models/Llama-3.2-3B-Instruct-Q4_K_M.gguf")

    if not model_path.exists():
        print(f"[FAIL] Model file not found: {model_path}")
        return 1

    print(f"[OK] Model file found: {model_path}")
    print(f"[INFO] Size: {model_path.stat().st_size / 1024 / 1024:.1f} MB")
    print()

    try:
        from llama_cpp import Llama
        print("[OK] llama-cpp-python imported successfully")
    except ImportError as e:
        print(f"[FAIL] Failed to import llama-cpp-python: {e}")
        return 1

    print()
    print("Loading model (this may take 10-30 seconds)...")
    print()

    try:
        llm = Llama(
            model_path=str(model_path),
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )
        print("[OK] Model loaded successfully!")
        print()

        # Test inference
        print("Testing inference...")
        response = llm("Hello, ", max_tokens=10, temperature=0.7)
        print(f"[OK] Inference test: '{response['choices'][0]['text']}'")
        print()

        print("=" * 60)
        print("[SUCCESS] LLM is ready to use!")
        print("=" * 60)
        return 0

    except Exception as e:
        print(f"[FAIL] Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(test_llm_loading())
