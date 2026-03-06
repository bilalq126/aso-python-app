import requests
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

def check_keyword_feasibility(keyword: str, country_code: str = 'us'):
    """
    Queries the public iTunes Search API to calculate Traffic and Difficulty scores 
    for a given keyword, based on the top 10 ranked apps.
    """
    # iTunes API endpoint for software
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(keyword)}&country={country_code}&entity=software&limit=10"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        apps = data.get('results', [])
        
        if not apps:
            return {"keyword": keyword, "trafficScore": 0, "difficultyScore": 0, "error": "No apps found"}
            
        # 1. Traffic Score: Based on average review count of top 10 apps
        total_reviews = sum(app.get('userRatingCount', 0) for app in apps)
        avg_reviews = total_reviews / len(apps)
        
        import math
        max_reviews_cap = 1_000_000 # Cap for logarithmic scale (from AppAgent)
        traffic_score = min(10.0, (math.log10(avg_reviews + 1) / math.log10(max_reviews_cap + 1)) * 10)
        
        # 2. Difficulty Score: Based on average rating of top 10 apps
        total_ratings = sum(app.get('averageUserRating', 0) for app in apps)
        avg_rating = total_ratings / len(apps)
        difficulty_score = (avg_rating / 5.0) * 10.0
        
        return {
            "keyword": keyword,
            "trafficScore": round(traffic_score, 2),
            "difficultyScore": round(difficulty_score, 2)
        }
        
    except Exception as e:
        return {"keyword": keyword, "trafficScore": 0, "difficultyScore": 0, "error": str(e)}

def batch_check_keywords(keywords: list[str], country_code: str = 'us'):
    """
    Checks a batch of keywords concurrently.
    """
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(check_keyword_feasibility, kw, country_code) for kw in keywords]
        for future in futures:
            results.append(future.result())
    return results

def validate_aso_text(generated_text: str):
    """
    Parses the generated text, checks character limits, and validates rules.
    Returns the parsed data and any warnings.
    """
    warnings = []
    locales_data = {}
    
    current_locale = None
    current_attribute = None
    
    for line in generated_text.split('\n'):
        # Keep original line for long description to preserve spacing later, but use strip for checks
        stripped_line = line.strip()
        if not stripped_line:
            continue
            
        # Detect locale header (e.g. "--------------------USA-----------------------------")
        if '---' in stripped_line and any(c.isalpha() for c in stripped_line) and not ':' in stripped_line:
            current_locale = "".join(c for c in stripped_line if c.isalpha()).title()
            if current_locale:
                locales_data[current_locale] = {'Title': '', 'Sub Title': '', 'Keywords': '', 'Short Description': '', 'Long Description': ''}
            current_attribute = None
            continue
            
        if not current_locale:
            # Pre-locale section (e.g., Chain of Thought reasoning)
            continue
            
        if stripped_line.startswith('App Title:'):
            locales_data[current_locale]['Title'] = stripped_line.split('App Title:', 1)[1].strip()
            current_attribute = 'Title'
                
        elif stripped_line.startswith('Sub Title:'):
            locales_data[current_locale]['Sub Title'] = stripped_line.split('Sub Title:', 1)[1].strip()
            current_attribute = 'Sub Title'
                
        elif stripped_line.startswith('Keywords:'):
            locales_data[current_locale]['Keywords'] = stripped_line.split('Keywords:', 1)[1].strip()
            current_attribute = 'Keywords'

        elif stripped_line.startswith('Short Description:'):
            locales_data[current_locale]['Short Description'] = stripped_line.split('Short Description:', 1)[1].strip()
            current_attribute = 'Short Description'
            
        elif stripped_line.startswith('Long Description:'):
            locales_data[current_locale]['Long Description'] = stripped_line.split('Long Description:', 1)[1].strip()
            current_attribute = 'Long Description'
            
        elif current_attribute == 'Long Description':
            locales_data[current_locale]['Long Description'] += "\n" + line # Keep original spacing for Long Desc
            

    # Run validations post-parsing
    for locale, data in locales_data.items():
        title = data.get('Title', '')
        if len(title) > 30:
            warnings.append(f"[{locale}] App Title exceeds 30 characters: '{title}' ({len(title)} chars)")
            
        subtitle = data.get('Sub Title', '')
        if subtitle and len(subtitle) > 30:
            warnings.append(f"[{locale}] Sub Title exceeds 30 characters: '{subtitle}' ({len(subtitle)} chars)")
            
        keywords_str = data.get('Keywords', '')
        if keywords_str:
            if len(keywords_str) > 100:
                warnings.append(f"[{locale}] Keywords exceed 100 characters combined ({len(keywords_str)} chars)")
            if ', ' in keywords_str:
                warnings.append(f"[{locale}] Keywords contain spaces after commas, violating App Store best practices.")
                
        short_desc = data.get('Short Description', '')
        if short_desc and len(short_desc) > 80:
            warnings.append(f"[{locale}] Short Description exceeds 80 characters: '{short_desc}' ({len(short_desc)} chars)")
            
        long_desc = data.get('Long Description', '')
        if long_desc and len(long_desc) > 4000:
            warnings.append(f"[{locale}] Long Description exceeds 4000 characters ({len(long_desc)} chars)")
            
    return locales_data, warnings
