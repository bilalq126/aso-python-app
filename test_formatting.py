import os
import sys

# Add the app directory to the path so we can import from it
sys.path.append(os.path.abspath(r"d:\Python\ASO Agent\aso-python-app"))

from agent import aso_template

# Let's test the post-processing logic directly to ensure it handles the exact Spanish output format 
# that the user provided.

test_llm_output = """
--------------------USA-----------------------------
App Title:          Croc Chomper Fun
Sub Title:          Jungle Predator Hunt Quest
Keywords: 
          crocodile,game,alligator,reptile,simulator,action,kids,family,swamp,river,water,attack,bite,survive

--------------------Spain-----------------------------
App Title:          Croc Salvaje Juego
Sub Title:          Depredador Selva Caza
Keywords:
          cocodrilo,caiman,reptil,simulador,accion,niños,familia,pantano,rio,agua,ataque,mordisco,sobrevivir,aventura,animal
"""

print("--- Original LLM Output ---")
print(test_llm_output)
print("-" * 40)

# Simulate the post-processing block from agent.py
output_text = test_llm_output
processed_lines = []

# Improved state machine to catch drifted keywords across lines
in_keywords_block = False
current_kw_string = ""

for line in output_text.split('\n'):
    
    if line.startswith('Keywords:'):
        in_keywords_block = True
        # Try to grab anything that might already be on this line
        current_kw_string = line.replace('Keywords:', '').strip()
        continue # Skip appending this line immediately, we build it up
        
    elif in_keywords_block:
        # Check if we hit the next section divider or a new attribute
        if line.startswith('---') or ':' in line:
            in_keywords_block = False
            
            # Flush the built-up keyword string
            current_kw_string = current_kw_string.replace(' ', '') # remove ALL spaces inside the string just in case
            current_kw_string = current_kw_string.replace(',,', ',') # clean double commas
            
            if len(current_kw_string) > 100:
                truncated = current_kw_string[:100]
                last_comma = truncated.rfind(',')
                if last_comma != -1:
                    current_kw_string = truncated[:last_comma]
                else:
                    current_kw_string = truncated
                    
            processed_lines.append(f"Keywords:           {current_kw_string}")
            current_kw_string = ""
            
            # Now append the current line that broke us out
            processed_lines.append(line)
        else:
            # We are inside the keywords block, accumulate text
            cleaned_part = line.strip()
            if cleaned_part:
                if current_kw_string and not current_kw_string.endswith(','):
                    current_kw_string += "," + cleaned_part
                else:
                    current_kw_string += cleaned_part
            
    else:
        # Normal line
        processed_lines.append(line)

# Flush at the end of the file if we were still in a block
if in_keywords_block:
    current_kw_string = current_kw_string.replace(' ', '')
    current_kw_string = current_kw_string.replace(',,', ',')
    if len(current_kw_string) > 100:
        truncated = current_kw_string[:100]
        last_comma = truncated.rfind(',')
        if last_comma != -1:
            current_kw_string = truncated[:last_comma]
        else:
            current_kw_string = truncated
    processed_lines.append(f"Keywords:           {current_kw_string}")

final_output = '\n'.join(processed_lines)

print("--- Processed Output ---")
print(final_output)

# Verify
for line in final_output.split('\n'):
    if 'Keywords:' in line:
        kw = line.split('Keywords:')[1].strip()
        print(f"Verified Length: {len(kw)}")
