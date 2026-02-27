import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the Prompt Template
aso_template = """
You are an expert App Store Optimization (ASO) specialist. 
Your task is to generate localized ASO metadata (App Title, Sub Title, and Keywords) based on a short description or app concept.
The output MUST strictly match the exact text format shown below for the requested locales.

CRITICAL APP STORE GUIDELINES YOU MUST FOLLOW:
1. App Title: MAXIMUM 30 characters.
2. Sub Title: MAXIMUM 30 characters.
3. Keywords Length: YOU MUST MAXIMIZE THIS BUDGET. The strict App Store maximum is 100 characters. You MUST generate between 90 and 99 characters of keywords. If your string is 60 characters, YOU HAVE FAILED. Brainstorm MORE unique keywords until you perfectly hit 90-99 characters (without going over 100).
4. Keywords Formatting: 
   - Comma-separated ONLY. DO NOT include spaces after commas (e.g., word1,word2,word3).
   - MUST BE ON A SINGLE LINE. Do NOT add newlines before, during, or after the keyword list. It must print on the same exact line as "Keywords:".
   - CRITICAL: "Keywords:           word1,word2..." DO NOT output "Keywords: \n word1,word2..."
5. ABSOLUTELY NO REPETITION: 
   - DO NOT repeat ANY word across the App Title, Sub Title, and Keywords. 
   - Every single word plotted across all three fields MUST be unique.
   - For example: If the title is "Pegasus Flying Horse", the words "Pegasus", "Flying", and "Horse" CANNOT appear in the Sub Title or Keywords. Maximum unique search term coverage is the priority.

App Concept / Description:
{app_concept}

Requested Locales:
{locales_str}

Please generate the metadata. Translate the App Title, Sub Title and Keywords into the language appropriate for each locale.
Remember to count the characters! Shorten titles or keywords if they exceed the limits.

The output MUST be formatted exactly like this example template (replace the data, keep the dashes and spacing):

--------------------USA-----------------------------
App Title:          [Translated Title Here]
Sub Title:          [Translated Sub Tite Here]
Keywords:           [comma separated translated keywords without spaces]

--------------------Brazil -----------------------------
App Title:          [Translated Title Here]
Sub Title:          [Translated Sub Tite Here]
Keywords:           [comma separated translated keywords without spaces]

Generate the output now, with a section for every locale requested:
"""

def generate_aso_metadata(app_concept: str, locales: list[str]) -> str:
    """
    Generates ASO metadata using Gemini based on the provided concept and desired locales.
    """
    
    # Initialize the LLM (ensure GEMINI_API_KEY is in your .env or environment)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    
    prompt = PromptTemplate(
        input_variables=["app_concept", "locales_str"],
        template=aso_template
    )
    
    locales_str = ", ".join(locales)
    
    # Format the prompt
    formatted_prompt = prompt.format(
        app_concept=app_concept, 
        locales_str=locales_str
    )
    
    # Generate the response
    response = llm.invoke(formatted_prompt)
    output_text = response.content
    
    # --- POST-PROCESSING: Enforce strict limits and formatting ---
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
        processed_lines.append(f"Keywords:        {current_kw_string}")
    
    final_output = '\n'.join(processed_lines)
    
    return final_output
