import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

COMMON_RULES = """CRITICAL APP STORE GUIDELINES YOU MUST FOLLOW:
1. App Title: MAXIMUM 30 characters.
2. Sub Title: MAXIMUM 30 characters.
3. Keywords Length: YOU MUST MAXIMIZE THIS BUDGET. The strict App Store maximum is 100 characters. You MUST generate between 90 and 99 characters of keywords. If your string is 60 characters, YOU HAVE FAILED. Brainstorm MORE unique keywords until you perfectly hit 90-99 characters (without going over 100).
4. Keywords Formatting: 
   - Comma-separated ONLY. DO NOT include spaces after commas (e.g., word1,word2,word3).
   - MUST BE ON A SINGLE LINE. Do NOT add newlines before, during, or after the keyword list. It must print on the same exact line as "Keywords:".
   - CRITICAL: "Keywords:           word1,word2..." DO NOT output "Keywords: \n word1,word2..."
5. ABSOLUTELY NO REPETITION & WORD NORMALIZATION (WITH ONE EXCEPTION): 
   - EXCEPTION: You MUST repeat or strongly reference the core subject word (e.g. "Cat", "Dog") in both the App Title and Sub Title to ensure the Sub Title remains highly relevant and doesn't sound generic.
   - OTHER THAN THE CORE SUBJECT, DO NOT repeat ANY word across the App Title, Sub Title, and Keywords. Every other word plotted across all three fields MUST be unique.
   - Word Normalization: Treat singular/plural and variations as the SAME word. Do not repeat variations.
   - For example: If the title is "Pegasus Flying Game", the word "Pegasus" SHOULD be in the Subtitle, but "Flying" and "Game" CANNOT appear anywhere else. 
6. BANNED WORDS (STRICT):
   - NEVER use these generic/marketing words: fun, free, best, new, app, apps, games, top, offline, online, play, player.
7. STOP-WORDS HANDLING:
   - Do NOT include stop words like "a", "an", "the", "for", "with", "of" in the Keywords list (they waste space).
8. NO GENERIC DICTIONARY NAMES:
   - Do NOT use generic names like "Dog Simulator", "Car Parking", "Hotel Manager", "Animal Life".
9. TITLE & SUBTITLE FORMULAS:
   - Perfect Title Formula: [Descriptive Adjective] + [Core Subject/Intent] (e.g. "Wild Cat Simulator" or "City Racing Manager"). 
   - CRITICAL TITLE/SUBTITLE RULE: The Title AND Subtitle MUST contain clear indicators of the actual physical subject of the app (e.g., "Cat", "Dog", "Car", "Gun"). DO NOT use overly abstract synonyms (like "Feline", "Creature", or "Vehicle") because nobody searches for those. Do NOT make the Subtitle sound like a generic game disconnected from the subject matter (e.g., if the game is about a Cat, "Explore City Life" is bad. "Cat Simulator City Life" is good).
   - Subtitle Formula: [Action] + [Environment/Target] (e.g. "Survive the Jungle Hunt" or "Cat Sim: City Survival")
10. TRAFFIC INTENT BUCKETS & KEYWORD RULES:
   - Mix keywords from these 3 buckets:
     - Bucket 1 (Gameplay Action): hunt, escape, build, drive, survive, craft, chase, explore, fight, etc.
     - Bucket 2 (Player Fantasy): predator, tycoon, driver, keeper, rider, beast, warden, etc.
     - Bucket 3 (Environment/Theme): jungle, forest, city, island, zoo, desert, ocean, etc.
   - Selection Rules: Action verbs > adjectives. Nouns > marketing words. Long-tail intent > generic terms.
   - VOCABULARY RULE: Only use COMMON, conversational English words that a normal person would actually type into a search bar. Do NOT use overly literary, academic, or obscure synonyms (e.g. use "Hunter", do not use "Prowler" or "Stalker")."""

PLAY_STORE_RULES = """CRITICAL GOOGLE PLAY STORE GUIDELINES YOU MUST FOLLOW:
1. App Title: MAXIMUM 30 characters. MUST include your primary keyword. Avoid keyword stuffing. No ALL CAPS, emojis, or misleading text.
2. Short Description: MAXIMUM 80 characters. Heavily indexed for keywords. Clear value proposition.
3. Long Description: MAXIMUM 4,000 characters. Keywords are indexed by Google Play, but DO NOT keyword stuff. Avoid repetition spam. Write naturally.
4. BANNED WORDS (STRICT):
   - NEVER use these generic/marketing words: fun, free, best, new, app, apps, games, top, offline, online, play, player.
5. NO GENERIC DICTIONARY NAMES:
   - Do NOT use generic names like "Dog Simulator", "Car Parking", "Hotel Manager", "Animal Life".
6. TITLE FORMULA:
   - Perfect Title Formula: [Descriptive Adjective] + [Core Subject/Intent] (e.g. "Wild Cat Simulator" or "City Racing Manager"). 
   - CRITICAL TITLE RULE: The Title MUST contain the actual physical subject of the app. DO NOT use overly abstract synonyms in the title. Stick to simple, high-traffic descriptive words.
7. VOCABULARY RULE: Only use COMMON, conversational English words that a normal person would actually type into a search bar."""

brainstorming_template = f"""You are an expert App Store Optimization (ASO) specialist. 
Your task is to analyze the market and brainstorm high-traffic concepts exclusively for the USA English market based on a short description.

{{common_rules}}

App Concept / Description:
{{app_concept}}

To ensure the highest quality results, you MUST follow this 2-step reasoning process:

--- STEP 1: COMPETITOR ANALYSIS ---
List the top 10 most successful related games/apps that currently exist based on this concept.
CRITICAL FORMATTING INSTRUCTION for Step 1: Output ONLY the 10 game titles. DO NOT write descriptions, do not write explanations or evaluations. Just a simple numbered list of the game titles in PLAIN TEXT. No Markdown formatting. No bold (**). Use standard numbering (1. 2. 3.).

--- STEP 2: KEYWORD BRAINSTORMING ---
List the top 50 most suitable, high-traffic keywords based on the intent buckets and competitor analysis.
CRITICAL FORMATTING INSTRUCTION for Step 2: You must output these 50 keywords as a single, comma-separated string (e.g. word1,word2,word3). DO NOT use bullet points. DO NOT generate the App Title or Sub Title yet—only output the 50 keywords!
"""

usa_generation_template = f"""You are an expert App Store Optimization (ASO) specialist. 
Your task is to generate optimized ASO metadata exclusively for the USA English market.

{{common_rules}}

App Concept / Description:
{{app_concept}}

Brainstormed Keywords / Competitor Data:
{{brainstormed_text}}

--- STEP 3: FINAL USA METADATA ---
Using the data from the brainstormed text provided above, generate the final optimized metadata.
CRITICAL WORD BANK RULE: You MUST treat the 50 keywords provided in the brainstorming text as a strict "Word Bank". Every single word you choose for the Title, Subtitle, and Keyword list MUST be pulled directly from that list. Do not invent new words in this step.

The output for this step MUST be formatted exactly like this example template (replace the data, keep the dashes and spacing):

--------------------USA-----------------------------
App Title:          [Title Here]
Sub Title:          [Sub Title Here]
Keywords:           [comma separated translated keywords without spaces]
"""

translate_aso_template = f"""You are an expert App Store Optimization (ASO) native localization specialist. 
Your task is to take an already optimized USA English ASO metadata set and natively localize it for other regions.

{{common_rules}}

CRITICAL LOCALIZATION RULES: 
1. Do NOT just directly translate the English words. For each locale, generate natively localized keywords that capture how people in that specific country actually search for these concepts, including regional slang and high-volume local terminology.
2. ONLY translate the specific fields provided in the "USA Original Metadata". If a field (like "Sub Title") is MISSING from the USA Original Metadata, DO NOT generate it for the other locales. Your output structure MUST perfectly match the input structure.

USA Original Metadata:
{{usa_metadata}}

Requested Locales:
{{locales_str}}

Generate the output now, with a section for every locale requested. Format it exactly like the input, but translated:
"""

play_generation_template = f"""You are an expert App Store Optimization (ASO) specialist. 
Your task is to generate optimized ASO metadata exclusively for the USA English Google Play Store market.

{{play_rules}}

App Concept / Description:
{{app_concept}}

Brainstormed Keywords / Competitor Data:
{{brainstormed_text}}

--- STEP 3: FINAL USA METADATA ---
Using the data from the brainstormed text provided above, generate the final optimized Google Play metadata.
You MUST integrate the 50 keywords provided in the brainstorming text naturally into your Long Description.

The output for this step MUST be formatted exactly like this example template (replace the data, keep the dashes and spacing):

--------------------USA-----------------------------
App Title:          [Title Here]
Short Description:  [Short Description Here]
Long Description:   [Write your Long Description beautifully here. Ensure it naturally utilizes the 50 intent-driven brainstormed keywords.]
"""

translate_play_template = f"""You are an expert App Store Optimization (ASO) native localization specialist for Google Play. 
Your task is to take an already optimized USA English ASO metadata set and natively localize it for other regions.

{{play_rules}}

CRITICAL LOCALIZATION RULES: 
1. Do NOT just directly translate the English words. For each locale, generate natively localized text that captures how people in that specific country actually search for these concepts, including regional slang and high-volume local terminology.
2. ONLY translate the specific fields provided in the "USA Original Metadata". If a field (like "Short Description") is MISSING from the USA Original Metadata, DO NOT generate it for the other locales. Your output structure MUST perfectly match the input structure.

USA Original Metadata:
{{usa_metadata}}

Requested Locales:
{{locales_str}}

Generate the output now, with a section for every locale requested. Format it exactly like the input, but translated:
"""

def post_process_aso_output(output_text: str) -> str:
    # --- POST-PROCESSING: Enforce strict limits and formatting ---
    
    # 1. Clean accidental markdown blocks or bolding
    output_text = output_text.replace("```markdown", "").replace("```text", "").replace("```", "")
    output_text = output_text.replace("**", "").replace("__", "").replace("*", "")
    
    # 2. Strip conversational filler before the first real block
    if "---" in output_text:
        # Find the first occurrence of a block divider
        first_divider = output_text.find("---")
        # Find the start of the line containing the first divider
        start_of_data = output_text.rfind('\n', 0, first_divider) + 1
        if start_of_data == 0:  # If it's on the very first line
            start_of_data = 0
        output_text = output_text[start_of_data:]
        
    # Also strip out any mid-text conversational filler during translation looping
    # E.g. "Here is the text:"
    clean_lines = []
    for line in output_text.split('\n'):
        if line.strip().lower().startswith("here is") or line.strip().lower().startswith("here are"):
            continue
        clean_lines.append(line)
    output_text = '\n'.join(clean_lines)

    processed_lines = []
    
    # Improved state machine to catch drifted keywords across lines
    in_keywords_block = False
    current_kw_string = ""
    
    for line in output_text.split('\n'):
        
        # Hard cap Short Description at 80 characters (Google Play)
        if line.startswith('Short Description:'):
            desc_text = line.split('Short Description:', 1)[1].strip()
            if len(desc_text) > 80:
                # Truncate and try not to chop words in half
                truncated = desc_text[:80]
                last_space = truncated.rfind(' ')
                if last_space > 0:
                    desc_text = truncated[:last_space]
                else:
                    desc_text = truncated
            processed_lines.append(f"Short Description:  {desc_text}")
            continue
            
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
    
    return final_output


def generate_competitor_and_keyword_analysis(app_concept: str, custom_rules: str = None) -> str:
    """
    Generates the Step 1 (Competitors) and Step 2 (Keywords) brainstorming text.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    rules_to_use = custom_rules if custom_rules else COMMON_RULES
    
    prompt = PromptTemplate(
        input_variables=["app_concept", "common_rules"],
        template=brainstorming_template
    )
    
    formatted_prompt = prompt.format(
        app_concept=app_concept,
        common_rules=rules_to_use
    )
    
    response = llm.invoke(formatted_prompt)
    text = response.content
    
    # Strip markdown symbols so it appears cleanly in a plain text area
    text = text.replace("**", "").replace("__", "").replace("```markdown", "").replace("```text", "").replace("```", "")
    return text

def generate_usa_baseline_from_brainstorm(app_concept: str, brainstormed_text: str, custom_rules: str = None) -> str:
    """
    Generates the final USA ASO metadata using the previously generated brainstorming text as a strict word bank.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    rules_to_use = custom_rules if custom_rules else COMMON_RULES
    
    prompt = PromptTemplate(
        input_variables=["app_concept", "brainstormed_text", "common_rules"],
        template=usa_generation_template
    )
    
    formatted_prompt = prompt.format(
        app_concept=app_concept,
        brainstormed_text=brainstormed_text,
        common_rules=rules_to_use
    )
    
    response = llm.invoke(formatted_prompt)
    output_text = response.content
    
    return post_process_aso_output(output_text)

def translate_aso_metadata(usa_metadata: str, locales: list[str], custom_rules: str = None) -> str:
    """
    Takes the USA baseline metadata and generates localized versions for other requested locales.
    """
    if not locales:
        return ""
        
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    rules_to_use = custom_rules if custom_rules else COMMON_RULES
    
    prompt = PromptTemplate(
        input_variables=["usa_metadata", "locales_str", "common_rules"],
        template=translate_aso_template
    )
    
    locales_str = ", ".join(locales)
    
    formatted_prompt = prompt.format(
        usa_metadata=usa_metadata, 
        locales_str=locales_str,
        common_rules=rules_to_use
    )
    
    response = llm.invoke(formatted_prompt)
    output_text = response.content
    
    return post_process_aso_output(output_text)

def generate_play_baseline_from_brainstorm(app_concept: str, brainstormed_text: str, custom_play_rules: str = None) -> str:
    """
    Generates the final USA Google Play ASO metadata.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    rules_to_use = custom_play_rules if custom_play_rules else PLAY_STORE_RULES
    
    prompt = PromptTemplate(
        input_variables=["app_concept", "brainstormed_text", "play_rules"],
        template=play_generation_template
    )
    
    formatted_prompt = prompt.format(
        app_concept=app_concept,
        brainstormed_text=brainstormed_text,
        play_rules=rules_to_use
    )
    
    response = llm.invoke(formatted_prompt)
    return post_process_aso_output(response.content)

def translate_play_metadata(usa_metadata: str, locales: list[str], custom_play_rules: str = None) -> str:
    """
    Takes the USA baseline Play Store metadata and generates localized versions.
    """
    if not locales:
        return ""
        
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    rules_to_use = custom_play_rules if custom_play_rules else PLAY_STORE_RULES
    
    prompt = PromptTemplate(
        input_variables=["usa_metadata", "locales_str", "play_rules"],
        template=translate_play_template
    )
    
    locales_str = ", ".join(locales)
    
    formatted_prompt = prompt.format(
        usa_metadata=usa_metadata, 
        locales_str=locales_str,
        play_rules=rules_to_use
    )
    
    response = llm.invoke(formatted_prompt)
    return post_process_aso_output(response.content)
