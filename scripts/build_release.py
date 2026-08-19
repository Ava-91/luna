from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    subprocess.run([sys.executable,"-m","pip","install","--upgrade","build"],cwd=ROOT,check=True)
    subprocess.run([sys.executable,"-m","build","--sdist","--wheel"],cwd=ROOT,check=True)
    print(f"Release artifacts written to {ROOT/'dist'}")

if __name__=="__main__": main()
