"""Comprehensive AI assistant module for intelligent hostel search and recommendations.
Uses advanced keyword matching, scoring, location awareness, and marketplace integration.
"""
import re
import json
import sqlite3
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional
from datetime import datetime

from akwaaba_store import init_store, get_gps_coordinates, _haversine

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'akwaaba.db'

# Advanced search keywords
PRICE_KEYWORDS = {'cheap', 'affordable', 'budget', 'expensive', 'premium', 'luxury', 'under', 'below', 'less than', 'maximum', 'max'}
LOCATION_KEYWORDS = {'near', 'close', 'far', 'distance', 'campus', 'legon', 'accra', 'kumasi', 'takoradi', 'cape coast'}
QUALITY_KEYWORDS = {'best', 'top', 'rated', 'excellent', 'good', 'nice', 'amazing', 'great', 'fantastic', 'popular'}
AMENITY_KEYWORDS = ['wifi', 'ac', 'aircon', 'hot water', 'kitchen', 'laundry', 'parking', 'breakfast', 'security', 'gym', 'pool', 'study room', 'lounge']


def _similar(a: str, b: str) -> float:
    """Calculate string similarity."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _parse_price(query: str) -> Optional[float]:
    """Extract price threshold from query."""
    m = re.search(r"(under|less than|below|<|max|maximum)\s*(?:GHS)?\s*([0-9,]+(?:\.[0-9]+)?)", query, re.I)
    if not m:
        m = re.search(r"([0-9,]+)\s*(?:GHS|ghs)?", query)
    if m:
        try:
            num = m.groups()[-1]
            return float(num.replace(',', ''))
        except (ValueError, IndexError):
            return None
    return None


def _extract_amenities(query: str) -> List[str]:
    """Extract requested amenities from query."""
    found = []
    q = query.lower()
    for a in AMENITY_KEYWORDS:
        if a in q:
            found.append(a)
    return list(set(found))


def _extract_quality_level(query: str) -> str:
    """Determine if user wants best/rated/premium hostels."""
    q = query.lower()
    if any(kw in q for kw in ['best', 'top', 'rated', 'excellent', 'premium']):
        return 'premium'
    return 'any'


def _extract_university(query: str) -> Optional[str]:
    """Extract university name/code from query."""
    universities = {'ttu', 'takoradi', 'legon', 'ug', 'university of ghana', 'knust', 'kumasi'}
    q = query.lower()
    for uni in universities:
        if uni in q:
            return uni
    return None


def _score_hostel(
    hostel: Dict[str, Any],
    price_goal: Optional[float],
    amenities: List[str],
    query: str,
    quality_level: str = 'any'
) -> float:
    """Advanced scoring function with multiple factors."""
    score = 0.0
    
    # Name/description similarity
    name_sim = _similar(hostel.get('name', ''), query)
    desc_sim = _similar(hostel.get('description', ''), query)
    score += (name_sim * 0.3 + desc_sim * 0.1) * 0.3
    
    # Price scoring
    hprice = hostel.get('price')
    if hprice is not None and price_goal is not None:
        if hprice <= price_goal:
            score += 0.5
        else:
            diff_ratio = (hprice - price_goal) / max(1, price_goal)
            score += max(0, 0.2 - diff_ratio * 0.05)
    elif price_goal is None:
        score += 0.1  # Small bonus if no price constraint
    
    # Amenities matching
    hostel_amenities = [a.lower() for a in (hostel.get('amenities', []) or [])]
    hostel_amenities.extend([r.lower() for r in (hostel.get('rules', []) or [])])
    
    if amenities:
        matches = 0
        for req_amenity in amenities:
            for has_amenity in hostel_amenities:
                if req_amenity in has_amenity or has_amenity in req_amenity:
                    matches += 1
                    break
        score += (matches / len(amenities)) * 0.4
    
    # Quality/rating bonus
    if quality_level == 'premium':
        score += 0.2  # Prefer higher-rated hostels
    
    # Availability bonus
    if hostel.get('available_slots', 0) > 5:
        score += 0.1
    
    # Verified badge bonus
    if hostel.get('verified'):
        score += 0.15
    
    return min(1.0, score)  # Cap at 1.0


def _load_from_sqlite(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    """Load hostels from SQLite database."""
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute('''
            SELECT id, university_code, campus_name, name, description, price, amenities, 
                   image_urls, gps_lat, gps_lon, available_slots, room_types, verified, 
                   manager_name, contact_phone, whatsapp, email
            FROM hostels
        ''')
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        hostels = []
        for r in rows:
            rec = dict(zip(cols, r))
            # Parse JSON fields
            for j in ('amenities', 'image_urls', 'room_types'):
                if rec.get(j):
                    try:
                        rec[j] = json.loads(rec[j])
                    except (json.JSONDecodeError, TypeError):
                        rec[j] = []
                else:
                    rec[j] = []
            hostels.append(rec)
        conn.close()
        return hostels
    except Exception as e:
        print(f"SQLite load error: {e}")
        return []


def _load_from_json() -> List[Dict[str, Any]]:
    """Load hostels from JSON data."""
    try:
        data = init_store()
        results = []
        for uni in data.get('universities', []):
            ucode = uni.get('code', 'UNKNOWN')
            for campus in uni.get('campuses', []):
                cname = campus.get('name', 'Unknown Campus')
                for h in campus.get('hostels', []):
                    rec = dict(h)
                    rec['university_code'] = ucode
                    rec['campus_name'] = cname
                    rec['price'] = rec.get('price')
                    rec['amenities'] = rec.get('amenities', [])
                    rec['image_urls'] = rec.get('image_urls', []) or rec.get('image_paths', [])
                    coords = rec.get('gps_coordinates') or {}
                    rec['gps_lat'] = coords.get('latitude')
                    rec['gps_lon'] = coords.get('longitude')
                    rec['verified'] = rec.get('verified', False)
                    rec['manager_name'] = rec.get('manager_name', '')
                    rec['contact_phone'] = rec.get('contact_phone', '')
                    rec['whatsapp'] = rec.get('whatsapp', '')
                    rec['email'] = rec.get('email', '')
                    results.append(rec)
        return results
    except Exception as e:
        print(f"JSON load error: {e}")
        return []


def search_hostels(query: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """Advanced hostel search with natural language understanding."""
    # Extract search parameters from query
    price_goal = _parse_price(query)
    amenities = _extract_amenities(query)
    quality_level = _extract_quality_level(query)
    
    # Load candidates
    hostels = _load_from_sqlite() + _load_from_json()
    
    # Remove duplicates (keep SQLite version if both exist)
    seen_names = set()
    unique_hostels = []
    for h in hostels:
        name = h.get('name', '')
        if name not in seen_names:
            unique_hostels.append(h)
            seen_names.add(name)
    
    # Score and filter
    scored = []
    for h in unique_hostels:
        # Skip fully booked unless explicitly looking for all
        if h.get('available_slots', 0) == 0 and 'all' not in query.lower():
            continue
        
        score = _score_hostel(h, price_goal, amenities, query, quality_level)
        h_copy = dict(h)
        h_copy['_score'] = score
        scored.append(h_copy)
    
    # Sort by score
    scored.sort(key=lambda x: x['_score'], reverse=True)
    return scored[:max_results]


def get_hostel_comparison(hostel_names: List[str]) -> Dict[str, Any]:
    """Get comparison data for multiple hostels."""
    hostels = _load_from_sqlite() + _load_from_json()
    
    comparison = {
        'hostels': [],
        'summary': {}
    }
    
    for name in hostel_names:
        for h in hostels:
            if _similar(h.get('name', ''), name) > 0.8:
                comparison['hostels'].append(h)
                break
    
    return comparison


def get_hostel_details_comprehensive(hostel_name: str) -> Dict[str, Any]:
    """Get comprehensive information about a specific hostel."""
    hostels = _load_from_sqlite() + _load_from_json()
    
    for h in hostels:
        if _similar(h.get('name', ''), hostel_name) > 0.8:
            # Add marketplace data if available
            from marketplace import get_hostel_rating, get_hostel_reviews
            
            rating, review_count = get_hostel_rating(h.get('name', ''))
            reviews = get_hostel_reviews(h.get('name', ''))
            
            return {
                **h,
                'rating': rating,
                'review_count': review_count,
                'recent_reviews': reviews[-3:] if reviews else [],
                'timestamp': datetime.now().isoformat()
            }
    
    return {}


def search_nearby(campus_lat: float, campus_lon: float, max_distance_km: float = 2.0) -> List[Dict[str, Any]]:
    """Find hostels near a specific location."""
    hostels = _load_from_sqlite() + _load_from_json()
    
    nearby = []
    for h in hostels:
        if h.get('gps_lat') and h.get('gps_lon'):
            distance = _haversine(campus_lat, campus_lon, h['gps_lat'], h['gps_lon'])
            if distance <= max_distance_km:
                h_copy = dict(h)
                h_copy['distance_km'] = distance
                h_copy['_score'] = 1.0 - (distance / max_distance_km) * 0.5
                nearby.append(h_copy)
    
    nearby.sort(key=lambda x: x['distance_km'])
    return nearby
