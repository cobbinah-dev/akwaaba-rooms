"""Simple AI assistant module to search hostels from JSON and SQLite.
It uses keyword matching and simple scoring to return ranked results.
"""
import re
import json
import sqlite3
from pathlib import Path
from difflib import SequenceMatcher
from typing import List, Dict, Any, Optional

from akwaaba_store import init_store, get_gps_coordinates, _haversine

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'akwaaba.db'


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _parse_price(query: str) -> Optional[float]:
    m = re.search(r"(under|less than|<)\s*GHS?\s*([0-9,]+(?:\.[0-9]+)?)", query, re.I)
    if not m:
        m = re.search(r"([0-9,]+)\s*(GHS|ghs)?", query)
    if m:
        num = m.groups()[-1]
        try:
            return float(num.replace(',', ''))
        except Exception:
            return None
    return None


COMMON_AMENITIES = ['wifi', 'ac', 'aircon', 'hot water', 'kitchen', 'laundry', 'parking', 'breakfast', 'breakfast included']


def _extract_amenities(query: str) -> List[str]:
    found = []
    q = query.lower()
    for a in COMMON_AMENITIES:
        if a in q:
            found.append(a)
    # also pick comma separated tokens
    tokens = [t.strip() for t in re.split('[,;]', query) if t.strip()]
    for t in tokens:
        if len(t) <= 2:
            continue
        if t not in found and any(word in t for word in COMMON_AMENITIES):
            found.append(t)
    return found


def _score_hostel(hostel: Dict[str, Any], price_goal: Optional[float], amenities: List[str], name_query: str) -> float:
    score = 0.0
    # name similarity
    if name_query:
        score += _similar(hostel.get('name', ''), name_query) * 0.5
    # price proximity
    hprice = hostel.get('price')
    if hprice is not None and price_goal is not None:
        # the closer to price_goal the better (lower is better if goal is max)
        if hprice <= price_goal:
            score += 0.4
        else:
            score += max(0, 0.2 - (hprice - price_goal) / (price_goal + 1e-6) * 0.1)
    # amenities match
    had = [a.lower() for a in (hostel.get('amenities') or hostel.get('rules') or [])]
    match_count = 0
    for a in amenities:
        for h in had:
            if a in h:
                match_count += 1
                break
    if amenities:
        score += (match_count / max(1, len(amenities))) * 0.6
    return score


def _load_from_sqlite(db_path: Path = DB_PATH) -> List[Dict[str, Any]]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute('SELECT id,university_code,campus_name,name,description,price,amenities,image_urls,gps_lat,gps_lon,available_slots,room_types FROM hostels')
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    hostels = []
    for r in rows:
        rec = dict(zip(cols, r))
        # parse JSON fields
        for j in ('amenities', 'image_urls', 'room_types'):
            if rec.get(j):
                try:
                    rec[j] = json.loads(rec[j])
                except Exception:
                    rec[j] = []
            else:
                rec[j] = []
        hostels.append(rec)
    conn.close()
    return hostels


def _load_from_json() -> List[Dict[str, Any]]:
    data = init_store()
    results = []
    for uni in data.get('universities', []):
        ucode = uni.get('code')
        for campus in uni.get('campuses', []):
            cname = campus.get('name')
            for h in campus.get('hostels', []):
                rec = dict(h)
                rec['university_code'] = ucode
                rec['campus_name'] = cname
                # normalize fields
                rec['price'] = rec.get('price')
                rec['amenities'] = rec.get('amenities', [])
                rec['image_urls'] = rec.get('image_urls', []) or rec.get('image_paths', [])
                coords = rec.get('gps_coordinates') or {}
                rec['gps_lat'] = coords.get('latitude')
                rec['gps_lon'] = coords.get('longitude')
                results.append(rec)
    return results


def search_hostels(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Search hostels using lightweight parsing and scoring.
    Returns a list of hostels ordered by score.
    """
    price_goal = _parse_price(query)
    amenities = _extract_amenities(query)
    name_query = query

    # load candidates from sqlite then json
    hostels = _load_from_sqlite() + _load_from_json()

    scored = []
    for h in hostels:
        if h.get('available_slots', 0) == 0:
            # skip fully booked
            continue
        score = _score_hostel(h, price_goal, amenities, name_query)
        h_copy = dict(h)
        h_copy['_score'] = score
        scored.append(h_copy)

    scored.sort(key=lambda x: x['_score'], reverse=True)
    return scored[:max_results]
