"""Marketplace features: ratings, reviews, favorites, price alerts, contact info."""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

ROOT = Path(__file__).resolve().parent
MARKETPLACE_DB = ROOT / "marketplace.json"


def _load_marketplace():
    if not MARKETPLACE_DB.exists():
        _save_marketplace({"reviews": [], "favorites": {}, "price_alerts": []})
    with MARKETPLACE_DB.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_marketplace(data):
    with MARKETPLACE_DB.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def add_review(hostel_name: str, student_name: str, rating: float, comment: str) -> bool:
    """Add a student review (1-5 stars)."""
    if not (1 <= rating <= 5):
        return False
    data = _load_marketplace()
    review = {
        "hostel_name": hostel_name,
        "student_name": student_name,
        "rating": rating,
        "comment": comment,
        "timestamp": datetime.now().isoformat(),
    }
    data["reviews"].append(review)
    _save_marketplace(data)
    return True


def get_hostel_reviews(hostel_name: str) -> List[Dict[str, Any]]:
    """Get all reviews for a hostel."""
    data = _load_marketplace()
    return [r for r in data["reviews"] if r["hostel_name"] == hostel_name]


def get_hostel_rating(hostel_name: str) -> tuple:
    """Return (average_rating, review_count) for a hostel."""
    reviews = get_hostel_reviews(hostel_name)
    if not reviews:
        return 0.0, 0
    avg = sum(r["rating"] for r in reviews) / len(reviews)
    return round(avg, 1), len(reviews)


def add_favorite(student_id: str, hostel_name: str) -> bool:
    """Save hostel to student's favorites."""
    data = _load_marketplace()
    if student_id not in data["favorites"]:
        data["favorites"][student_id] = []
    if hostel_name not in data["favorites"][student_id]:
        data["favorites"][student_id].append(hostel_name)
        _save_marketplace(data)
    return True


def remove_favorite(student_id: str, hostel_name: str) -> bool:
    """Remove hostel from favorites."""
    data = _load_marketplace()
    if student_id in data["favorites"] and hostel_name in data["favorites"][student_id]:
        data["favorites"][student_id].remove(hostel_name)
        _save_marketplace(data)
    return True


def is_favorite(student_id: str, hostel_name: str) -> bool:
    """Check if hostel is in student's favorites."""
    data = _load_marketplace()
    return student_id in data["favorites"] and hostel_name in data["favorites"][student_id]


def get_favorites(student_id: str) -> List[str]:
    """Get student's favorite hostels."""
    data = _load_marketplace()
    return data["favorites"].get(student_id, [])


def add_price_alert(hostel_name: str, price_threshold: float, student_email: str) -> bool:
    """Set up a price alert when price drops below threshold."""
    data = _load_marketplace()
    alert = {
        "hostel_name": hostel_name,
        "price_threshold": price_threshold,
        "student_email": student_email,
        "created_at": datetime.now().isoformat(),
        "triggered": False,
    }
    data["price_alerts"].append(alert)
    _save_marketplace(data)
    return True


def get_price_alerts(hostel_name: str) -> List[Dict[str, Any]]:
    """Get all price alerts for a hostel."""
    data = _load_marketplace()
    return [a for a in data["price_alerts"] if a["hostel_name"] == hostel_name and not a["triggered"]]


def check_and_trigger_price_alerts(hostel_name: str, current_price: float) -> List[str]:
    """Check if current price triggers any alerts. Returns list of emails to notify."""
    alerts = get_price_alerts(hostel_name)
    triggered_emails = []
    if current_price < alerts[0]["price_threshold"] if alerts else False:
        for alert in alerts:
            if current_price < alert["price_threshold"]:
                triggered_emails.append(alert["student_email"])
    # TODO: Actually send email notifications here
    return triggered_emails


def get_availability_status(available_slots: int) -> tuple:
    """Return (status_text, css_color) for availability display."""
    if available_slots == 0:
        return "Full", "#dc3545"  # red
    elif available_slots <= 2:
        return f"Limited ({available_slots})", "#ffc107"  # yellow
    else:
        return f"Available ({available_slots})", "#28a745"  # green


def format_distance(distance_km: Optional[float]) -> str:
    """Format distance nicely for display."""
    if distance_km is None:
        return ""
    if distance_km < 0.1:
        return "On campus"
    elif distance_km < 1:
        return f"{distance_km * 1000:.0f}m away"
    else:
        return f"{distance_km:.1f}km away"


def get_star_html(rating: float) -> str:
    """Generate star rating HTML (★)."""
    stars = int(rating)
    half = 1 if (rating - stars) >= 0.5 else 0
    empty = 5 - stars - half
    html = "★" * stars
    if half:
        html += "½"
    html += "☆" * empty
    return f'<span style="color:#ffc107;font-size:14px;">{html}</span>'
