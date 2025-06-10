#!/usr/bin/env python
"""
Bishop Bot - Setup Verification Tool
Last updated: 2025-05-31 15:56:17 UTC by Bioku87
"""
import os
import sys
import importlib
import subprocess
import platform
from pathlib import Path

def print_header(text):
    print("\n" + "=" * 50)
    print(f" {text} ".center(50, "="))
    print("=" * 50)

def print_status(name, status, details=None):
    status_color = "\033[92m" if status else "\033[91m"  # Green for OK, Red for ERROR
    reset_color = "\033[0m"
    
    status_text = "OK" if status else "ERROR"
    
    # Handle Windows terminal that doesn't support ANSI colors
    if platform.system() == "Windows":
        print(f"{name}: {status_text}")
    else:
        print(f"{name}: {status_color}{status_text}{reset_color}")
        
    if not status and details:
        print(f"  → {details}")

def check_python_version():
    required_version = (3, 9)
    current_version = sys.version_info
    
    version_ok = current_version >= required_version
    details = f"Found Python {current_version.major}.{current_version.minor}.{current_version.micro}, required {required_version[0]}.{required_version[1]}+"
    
    return version_ok, details

def check_pip():
    try:
        import pip
        return True, f"pip {pip.__version__} installed"
    except ImportError:
        return False, "pip is not installed or not in PATH"

def check_module(module_name):
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unknown version")
        return True, f"{module_name} {version} installed"
    except ImportError as e:
        return False, f"Module not found: {e}"
    except Exception as e:
        return False, f"Error checking module: {e}"

def check_dependencies():
    dependencies = [
        "discord",
        "aiosqlite",
        "dotenv",
        "PIL",
        "requests",
        "asyncio",
        "numpy",
        "matplotlib",
    ]
    
    optional_deps = [
        "speech_recognition", 
        "pyaudio",
        "whisper",
        "openai",
    ]
    
    results = []
    
    print_header("Checking Required Dependencies")
    all_required_ok = True
    
    for dep in dependencies:
        status, details = check_module(dep)
        print_status(dep, status, details)
        if not status:
            all_required_ok = False
        results.append({"name": dep, "status": status, "details": details})
    
    print_header("Checking Optional Dependencies")
    
    for dep in optional_deps:
        status, details = check_module(dep)
        print_status(dep, status, details)
        results.append({"name": dep, "status": status, "details": details})
    
    return all_required_ok, results

def check_file_structure():
    required_dirs = [
        "src",
        "src/bot",
        "src/bot/commands",
        "src/voice",
        "src/database",
        "src/characters",
        "data",
        "logs",
    ]
    
    required_files = [
        "src/main.py",
        "src/bot/__init__.py",
        "src/bot/commands/__init__.py",
        "src/voice/__init__.py",
        ".env",
        "requirements.txt",
    ]
    
    all_ok = True
    
    print_header("Checking Directory Structure")
    
    for directory in required_dirs:
        exists = os.path.isdir(directory)
        print_status(directory, exists)
        if not exists:
            all_ok = False
    
    print_header("Checking Required Files")
    
    for file in required_files:
        exists = os.path.isfile(file)
        print_status(file, exists)
        if not exists:
            all_ok = False
    
    return all_ok

def check_env_file():
    env_file = ".env"
    required_vars = [
        "DISCORD_TOKEN",
    ]
    
    optional_vars = [
        "VOICE_API_KEY",
        "OPENAI_API_KEY",
    ]
    
    if not os.path.isfile(env_file):
        print_status(env_file, False, "File not found")
        return False
    
    print_header("Checking Environment Variables")
    
    all_required_ok = True
    env_vars = {}
    
    # Read .env file
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # Check required variables
    for var in required_vars:
        has_var = var in env_vars and env_vars[var] and env_vars[var] != "your_token_here"
        print_status(var, has_var)
        if not has_var:
            all_required_ok = False
    
    # Check optional variables
    for var in optional_vars:
        has_var = var in env_vars and env_vars[var]
        print_status(var, has_var, "Optional" if not has_var else None)
    
    return all_required_ok

def main():
    print("\n" + "#" * 60)
    print("#" + " Bishop Bot Setup Verification Tool ".center(58) + "#")
    print("#" + f" Python {sys.version.split()[0]} on {platform.system()} ".center(58) + "#")
    print("#" * 60)
    
    # Check Python version
    python_ok, python_details = check_python_version()
    print_status("Python Version", python_ok, python_details)
    
    # Check pip
    pip_ok, pip_details = check_pip()
    print_status("pip", pip_ok, pip_details)
    
    # Check dependencies
    deps_ok, _ = check_dependencies()
    
    # Check file structure
    structure_ok = check_file_structure()
    
    # Check env file
    env_ok = check_env_file()
    
    # Final status
    print_header("Summary")
    all_ok = python_ok and pip_ok and deps_ok and structure_ok and env_ok
    
    if all_ok:
        print("\nAll checks passed! You're ready to run Bishop Bot.")
        print("\nTo start the bot, run:")
        print("  python src/main.py")
    else:
        print("\nSome checks failed. Please fix the issues before running the bot.")
        print("\nTo install missing dependencies, run:")
        print("  pip install -r requirements.txt")
        
        if not env_ok:
            print("\nMake sure your .env file contains a valid DISCORD_TOKEN.")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())