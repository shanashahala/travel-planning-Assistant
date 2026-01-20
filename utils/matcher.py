import json
from typing import List, Dict, Any

def calculate_similarity_score(preferences: Dict[str, Any], package: Dict[str, Any]) -> float:
    """
    Calculates a similarity score between user preferences and a travel package.
    
    Scores are based on:
    - Destination match: 100 points
    - Package type match: 50 points
    - Budget match: up to 40 points
    - Duration match: up to 30 points
    - Activity match: 15 points per matching activity
    """
    score = 0.0
    
    # 1. Destination match (High priority)
    pref_dest = str(preferences.get('destination') or '').lower().strip()
    pkg_dest = str(package.get('destination') or '').lower().strip()
    if pref_dest and pref_dest in pkg_dest:
        score += 100
    
    # 2. Package type match
    pref_type = str(preferences.get('package_type') or '').lower().strip()
    pkg_type = str(package.get('package_type') or '').lower().strip()
    if pref_type and pref_type == pkg_type:
        score += 50
    elif pref_type and (pref_type in pkg_type or pkg_type in pref_type):
        score += 25
        
    # 3. Budget match
    # budget is usually a total or per person limit. 
    # Packages.json has prices for solo, couple, family_4
    traveler_type = str(preferences.get('traveler_type') or 'solo').lower()
    budget = preferences.get('budget')
    
    # Normalize traveler type for price lookup
    price_key = traveler_type
    if 'couple' in traveler_type:
        price_key = 'couple'
    elif 'family' in traveler_type:
        price_key = 'family_4'
    elif 'solo' in traveler_type:
        price_key = 'solo'
        
    pkg_prices = package.get('price', {})
    if isinstance(pkg_prices, (int, float)):
        pkg_price = pkg_prices
    elif isinstance(pkg_prices, dict):
        pkg_price = pkg_prices.get(price_key)
        if pkg_price is None:
            # Fallback to solo if specific type not found
            pkg_price = pkg_prices.get('solo')
    else:
        pkg_price = None
        
    if budget is not None and pkg_price is not None:

        try:
            budget_val = float(budget)
            pkg_price_val = float(pkg_price)
            if pkg_price_val <= budget_val:
                score += 40
            elif pkg_price_val <= budget_val * 1.2: # within 20%
                score += 20
            elif pkg_price_val <= budget_val * 1.5: # within 50%
                score += 10
        except (ValueError, TypeError):
            pass
            
    # 4. Duration match
    pref_duration = preferences.get('duration_days')
    # Some older code might use 'duration'
    if pref_duration is None:
        pref_duration = preferences.get('duration')
        
    pkg_duration = package.get('duration_days')
    
    if pref_duration is not None and pkg_duration is not None:
        try:
            pref_dur_val = int(pref_duration)
            pkg_dur_val = int(pkg_duration)
            diff = abs(pref_dur_val - pkg_dur_val)
            if diff == 0:
                score += 30
            elif diff == 1:
                score += 15
            elif diff == 2:
                score += 5
        except (ValueError, TypeError):
            pass
            
    # 5. Activity match
    pref_activities = preferences.get('activities', [])
    if isinstance(pref_activities, str):
        pref_activities = [pref_activities]
        
    if pref_activities:
        pkg_days = package.get('day_plans', [])
        pkg_activities_text = ""
        for day in pkg_days:
            pkg_activities_text += " " + day.get('primary_plan', '').lower()
            pkg_activities_text += " " + " ".join([a.lower() for a in day.get('alternative_plans', [])])
            
        for act in pref_activities:
            if str(act).lower() in pkg_activities_text:
                score += 15
            
    return score

def get_most_similar_packages(preferences: Dict[str, Any], all_packages: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    """
    Returns the top N packages that match the user preferences based on similarity scoring.
    """
    scored_packages = []
    for pkg in all_packages:
        score = calculate_similarity_score(preferences, pkg)
        scored_packages.append((score, pkg))
    
    # Sort by score descending
    scored_packages.sort(key=lambda x: x[0], reverse=True)
    
    # Return top N packages with score > 0
    results = []
    for score, pkg in scored_packages[:limit]:
        if score > 0:
            pkg_copy = pkg.copy()
            pkg_copy['match_score'] = score
            results.append(pkg_copy)
            
    return results
