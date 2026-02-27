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
    
    for line in generated_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Detect locale header (e.g. "--------------------USA-----------------------------")
        if '---' in line and any(c.isalpha() for c in line) and not ':' in line:
            # Extract locale name by removing all non-alphabetic characters
            current_locale = "".join(c for c in line if c.isalpha()).title()
            if current_locale:
                locales_data[current_locale] = {'Title': '', 'Sub Title': '', 'Keywords': ''}
            continue
            
        if not current_locale:
            continue
            
        if line.startswith('App Title:'):
            title = line.split('App Title:', 1)[1].strip()
            locales_data[current_locale]['Title'] = title
            if len(title) > 30:
                warnings.append(f"[{current_locale}] App Title exceeds 30 characters: '{title}' ({len(title)} chars)")
                
        elif line.startswith('Sub Title:'):
            subtitle = line.split('Sub Title:', 1)[1].strip()
            locales_data[current_locale]['Sub Title'] = subtitle
            if len(subtitle) > 30:
                warnings.append(f"[{current_locale}] Sub Title exceeds 30 characters: '{subtitle}' ({len(subtitle)} chars)")
                
        elif line.startswith('Keywords:'):
            keywords_str = line.split('Keywords:', 1)[1].strip()
            locales_data[current_locale]['Keywords'] = keywords_str
            if len(keywords_str) > 100:
                warnings.append(f"[{current_locale}] Keywords exceed 100 characters combined ({len(keywords_str)} chars)")
                
            # Check for spaces after commas (which wastes characters)
            if ', ' in keywords_str:
                warnings.append(f"[{current_locale}] Keywords contain spaces after commas, violating ASO best practices.")
                
    return locales_data, warnings
