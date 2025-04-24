"""
Helper script to build the server binary using PyInstaller.
"""

import os
import platform
import shutil
import subprocess
import sys

sep = ";" if platform.system() == "Windows" else ":"


def get_os_triple():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        if machine == "amd64" or machine == "x86_64":
            return "x86_64-pc-windows-msvc"
        elif machine == "arm64" or machine == "aarch64":
            return "aarch64-pc-windows-msvc"
    elif system == "darwin":
        if machine == "x86_64":
            return "x86_64-apple-darwin"
        elif machine == "arm64" or machine == "aarch64":
            return "aarch64-apple-darwin"
    elif system == "linux":
        if machine == "x86_64":
            return "x86_64-unknown-linux-gnu"
        elif machine == "arm64" or machine == "aarch64":
            return "aarch64-unknown-linux-gnu"

    return f"{machine}-{system}"


os_triple = get_os_triple()
output_name = f"shadowpuppet-server-{os_triple}"

cmd = [
    "pyinstaller",
    f"--add-data=../frontend/build{sep}frontend/build",
    "--onefile",
    f"--name={output_name}",
    "server.py",
]

print(f"Building for OS triple: {os_triple}")
print(f"Command: {' '.join(cmd)}")

result = subprocess.run(cmd)

if result.returncode == 0:
    print(
        f"Build successful! Binary created as dist/{output_name}{'.exe' if platform.system() == 'Windows' else ''}"
    )

    cleanup_paths = ["build", f"{output_name}.spec", "__pycache__"]
    for path in cleanup_paths:
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Removed directory: {path}")
        elif os.path.isfile(path):
            os.remove(path)
            print(f"Removed file: {path}")

    print("PyInstaller cleanup completed")
else:
    print("Build failed!")
    sys.exit(1)
