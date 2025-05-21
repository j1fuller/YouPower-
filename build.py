import subprocess
import sys

def build_exe():
    print("Building YouPower PG&E Scraper executable...")
    try:
        subprocess.check_call([
            'pyinstaller',
            '--onefile',
            '--noconsole',
            '--icon=icon.ico',
            '--name=YouPowerPGE',
            'youpower_pge.py'
        ])
        print("Build successful! Executable is in the dist folder.")
    except Exception as e:
        print(f"Build failed: {e}")

if __name__ == "__main__":
    build_exe()
