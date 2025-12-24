#!/usr/bin/env python3
"""
CiRA Block Runtime - Block Test Script

This script tests all compiled blocks by loading them and running basic tests.
Works on both Windows (.dll) and Linux (.so)
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text):
    symbol = "[OK]" if platform.system() == "Windows" else "✓"
    print(f"{Colors.GREEN}{symbol}{Colors.END} {text}")

def print_error(text):
    symbol = "[FAIL]" if platform.system() == "Windows" else "✗"
    print(f"{Colors.RED}{symbol}{Colors.END} {text}")

def print_info(text):
    symbol = "[INFO]" if platform.system() == "Windows" else "ℹ"
    print(f"{Colors.YELLOW}{symbol}{Colors.END} {text}")

def find_blocks(build_dir):
    """Find all block libraries in the build directory"""
    ext = ".dll" if platform.system() == "Windows" else ".so"
    blocks = []

    for root, dirs, files in os.walk(build_dir):
        for file in files:
            if file.endswith(ext) and not file.startswith("lib"):
                full_path = os.path.join(root, file)
                # Extract block category from path
                path_parts = Path(root).parts
                if "sensors" in path_parts:
                    category = "Sensor"
                elif "processing" in path_parts:
                    category = "Processing"
                elif "ai" in path_parts:
                    category = "AI/Model"
                elif "outputs" in path_parts:
                    category = "Output"
                else:
                    category = "Unknown"

                blocks.append({
                    "name": file.replace(ext, ""),
                    "path": full_path,
                    "category": category,
                    "size": os.path.getsize(full_path)
                })

    return sorted(blocks, key=lambda x: (x["category"], x["name"]))

def check_block_symbols(block_path):
    """Check if block has required symbols (CreateBlock, DestroyBlock)"""
    try:
        if platform.system() == "Windows":
            # On Windows, use dumpbin or objdump
            result = subprocess.run(
                ["objdump", "-p", block_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout
            has_create = "CreateBlock" in output
            has_destroy = "DestroyBlock" in output
        else:
            # On Linux, use nm
            result = subprocess.run(
                ["nm", "-D", block_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            output = result.stdout
            has_create = "CreateBlock" in output
            has_destroy = "DestroyBlock" in output

        return has_create and has_destroy
    except Exception as e:
        print_info(f"Could not check symbols: {e}")
        return None

def test_block_loading(block):
    """Test if block can be loaded"""
    if platform.system() == "Windows":
        try:
            import ctypes
            lib = ctypes.CDLL(block["path"])
            return True
        except Exception as e:
            return False
    else:
        try:
            import ctypes
            lib = ctypes.CDLL(block["path"], ctypes.RTLD_LAZY)
            return True
        except Exception as e:
            return False

def main():
    print_header("CiRA Block Runtime - Test Suite")

    # Determine build directory
    script_dir = Path(__file__).parent
    build_dir = script_dir.parent / "build" / "blocks"

    if len(sys.argv) > 1:
        build_dir = Path(sys.argv[1])

    if not build_dir.exists():
        print_error(f"Build directory not found: {build_dir}")
        print_info("Run 'cmake --build build' first to compile blocks")
        return 1

    print_info(f"Scanning for blocks in: {build_dir}")

    # Find all blocks
    blocks = find_blocks(str(build_dir))

    if not blocks:
        print_error("No blocks found!")
        return 1

    print_success(f"Found {len(blocks)} blocks")

    # Test each block
    results = {"passed": 0, "failed": 0, "warning": 0}

    print_header("Testing Blocks")

    current_category = None
    for block in blocks:
        # Print category header
        if block["category"] != current_category:
            current_category = block["category"]
            print(f"\n{Colors.BOLD}{current_category} Blocks:{Colors.END}")

        # Print block info
        size_kb = block["size"] / 1024
        print(f"\n  {Colors.BOLD}{block['name']}{Colors.END}")
        print(f"    Path: {block['path']}")
        print(f"    Size: {size_kb:.1f} KB")

        # Check symbols
        has_symbols = check_block_symbols(block["path"])
        if has_symbols is True:
            print_success("    Exports: CreateBlock, DestroyBlock found")
        elif has_symbols is False:
            print_error("    Exports: Missing required functions")
            results["failed"] += 1
            continue
        else:
            print_info("    Exports: Could not verify (tools not available)")
            results["warning"] += 1

        # Test loading
        if test_block_loading(block):
            print_success("    Loading: Block loads successfully")
            results["passed"] += 1
        else:
            print_error("    Loading: Failed to load block")
            results["failed"] += 1

    # Print summary
    print_header("Test Summary")

    total = results["passed"] + results["failed"] + results["warning"]
    success_rate = (results["passed"] / total * 100) if total > 0 else 0

    print(f"Total blocks tested: {total}")
    print_success(f"Passed: {results['passed']}")
    if results["warning"] > 0:
        print_info(f"Warnings: {results['warning']}")
    if results["failed"] > 0:
        print_error(f"Failed: {results['failed']}")

    print(f"\nSuccess rate: {success_rate:.1f}%")

    if results["failed"] == 0:
        print_success("\nAll blocks passed basic tests!")
        return 0
    else:
        print_error(f"\n{results['failed']} block(s) failed tests")
        return 1

if __name__ == "__main__":
    sys.exit(main())
