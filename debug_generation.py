import os
import sys
sys.path.append(os.path.abspath(r"d:\Python\ASO Agent\aso-python-app"))
from agent import generate_usa_baseline_metadata

print("Generating USA Baseline...")
output = generate_usa_baseline_metadata("Pegasus Game - A flying horse simulator")
print("\n--- RAW OUTPUT ---")
print(output)
