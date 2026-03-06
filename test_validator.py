import os
import sys

sys.path.append(os.path.abspath(r"d:\Python\ASO Agent\aso-python-app"))
from validator import validate_aso_text

test_output = """
--- STEP 1: COMPETITOR ANALYSIS ---
Top 10 Related Games:
1. Pegasus Flying Horse
2. Wild Horse Simulator

--- STEP 2: KEYWORD BRAINSTORMING ---
Top 50 Keywords:
horse,fly,pegasus,wings,sky,adventure

--- STEP 3: FINAL USA METADATA ---
--------------------USA-----------------------------
App Title:          Pegasus Game
Sub Title:          Flying Horse Sim
Keywords:           horse,fly,pegasus,wings,sky,adventure
"""

data, warnings = validate_aso_text(test_output)

print("PARSED DATA:")
for locale, fields in data.items():
    print(f"[{locale}]")
    for k, v in fields.items():
        print(f"  {k}: {v}")
        
print("\nWARNINGS:")
for w in warnings:
    print(f"  {w}")
