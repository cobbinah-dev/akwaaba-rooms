import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "akwaaba_data.json"

DEFAULT_DATA = {
    "universities": [
        {
            "code": "TTU",
            "name": "Takoradi Technical University",
            "campuses": [
                {
                    "name": "Main Campus",
                    "gps_coordinates": {"latitude": 4.8933, "longitude": -1.7652},
                    "hostels": [
                        {
                            "name": "Akwaaba Hall",
                            "description": "Comfortable hostel close to the main lecture halls.",
                            "rules": [
                                "No loud music after 10pm",
                                "Keep the area clean",
                                "Visitors must sign in at reception"
                            ],
                            "room_types": [
                                {"type": "Single", "price": 1200, "available": 2},
                                {"type": "Double", "price": 1800, "available": 2}
                            ],
                            "available_slots": 4,
                            "gps_coordinates": {"latitude": 4.8937, "longitude": -1.7649},
                            "image_paths": [],
                        },
                        {
                            "name": "Ocean View Residence",
                            "description": "Scenic views with easy campus access.",
                            "rules": [
                                "No smoking indoors",
                                "Maintain quiet hours between 11pm and 6am"
                            ],
                            "room_types": [
                                {"type": "Single", "price": 1400, "available": 1},
                                {"type": "Executive", "price": 2200, "available": 1}
                            ],
                            "available_slots": 2,
                            "gps_coordinates": {"latitude": 4.894, "longitude": -1.767},
                            "image_paths": [],
                        }
                    ]
                }
            ]
        },
        {
            "code": "UG",
            "name": "University of Ghana",
            "campuses": [
                {
                    "name": "Legon Campus",
                    "gps_coordinates": {"latitude": 5.65, "longitude": -0.1869},
                    "hostels": [
                        {
                            "name": "Legon Lodge",
                            "description": "Quiet and secure accommodation inside Legon.",
                            "rules": [
                                "Respect curfew times",
                                "No pets allowed"
                            ],
                            "room_types": [
                                {"type": "Standard", "price": 1500, "available": 3},
                                {"type": "Premium", "price": 1900, "available": 1}
                            ],
                            "available_slots": 3,
                            "gps_coordinates": {"latitude": 5.6512, "longitude": -0.1865},
                            "image_paths": [],
                        },
                        {
                            "name": "Edu Suites",
                            "description": "Modern rooms close to campus services.",
                            "rules": [
                                "Keep your room tidy",
                                "Use common areas respectfully"
                            ],
                            "room_types": [
                                {"type": "Single", "price": 1700, "available": 1}
                            ],
                            "available_slots": 1,
                            "gps_coordinates": {"latitude": 5.6495, "longitude": -0.1878},
                            "image_paths": [],
                        }
                    ]
                }
            ]
        },
        {
            "code": "KNUST",
            "name": "Kwame Nkrumah University of Science and Technology",
            "campuses": [
                {
                    "name": "Main Campus",
                    "gps_coordinates": {"latitude": 6.6667, "longitude": -1.5833},
                    "hostels": [
                        {
                            "name": "Science Residence",
                            "description": "Spacious rooms with a quiet study environment.",
                            "rules": [
                                "Study areas must remain quiet",
                                "Report any damage immediately"
                            ],
                            "room_types": [
                                {"type": "Standard", "price": 1300, "available": 4},
                                {"type": "Deluxe", "price": 1800, "available": 1}
                            ],
                            "available_slots": 5,
                            "gps_coordinates": {"latitude": 6.6672, "longitude": -1.584},
                            "image_paths": [],
                        },
                        {
                            "name": "Tech Towers",
                            "description": "Premium accommodation near KNUST academic blocks.",
                            "rules": [
                                "Authorized visitors only",
                                "No cooking in rooms"
                            ],
                            "room_types": [
                                {"type": "Executive", "price": 1600, "available": 2}
                            ],
                            "available_slots": 2,
                            "gps_coordinates": {"latitude": 6.666, "longitude": -1.5825},
                            "image_paths": [],
                        }
                    ]
                }
            ]
        }
    ]
}


def _load():
    if not DATA_FILE.exists():
        _save(DEFAULT_DATA)
    with DATA_FILE.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save(data):
    with DATA_FILE.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def init_store():
    return _load()


def save_store(data):
    _save(data)


def get_university_options(data):
    return [f"{u['code']} - {u['name']}" for u in data["universities"]]


def find_university(data, selected_value):
    if selected_value is None:
        return None
    code = selected_value.split(" - ")[0]
    return next((u for u in data["universities"] if u["code"] == code), None)


def get_campus_options(university):
    return [c["name"] for c in university.get("campuses", [])]


def find_campus(university, campus_name):
    return next((c for c in university.get("campuses", []) if c["name"] == campus_name), None)


def get_hostels(campus):
    return campus.get("hostels", [])


def get_hostel(campus, hostel_name):
    return next((h for h in get_hostels(campus) if h["name"] == hostel_name), None)


def add_university(data, code, name):
    code = code.strip().upper()
    if not code or not name.strip():
        return False, "University code and name are required."
    if any(u["code"] == code for u in data["universities"]):
        return False, "A university with this code already exists."
    data["universities"].append({
        "code": code,
        "name": name.strip(),
        "campuses": [],
    })
    _save(data)
    return True, "University added successfully."


def add_campus(data, university_code, campus_name, latitude, longitude):
    university = next((u for u in data["universities"] if u["code"] == university_code), None)
    if university is None:
        return False, "University not found."
    if not campus_name.strip():
        return False, "Campus name is required."
    if any(c["name"] == campus_name for c in university.get("campuses", [])):
        return False, "A campus with this name already exists for this university."
    campus = {
        "name": campus_name.strip(),
        "gps_coordinates": {"latitude": latitude, "longitude": longitude},
        "hostels": [],
    }
    university["campuses"].append(campus)
    _save(data)
    return True, "Campus added successfully."


def add_hostel(data, university_code, campus_name, hostel_data):
    university = next((u for u in data["universities"] if u["code"] == university_code), None)
    if university is None:
        return False, "University not found."
    campus = next((c for c in university.get("campuses", []) if c["name"] == campus_name), None)
    if campus is None:
        return False, "Campus not found."
    if not hostel_data.get("name", "").strip():
        return False, "Hostel name is required."
    if get_hostel(campus, hostel_data["name"]):
        return False, "A hostel with this name already exists on this campus."
    hostel = {
        "name": hostel_data["name"].strip(),
        "description": hostel_data.get("description", ""),
        "rules": hostel_data.get("rules", []),
        "room_types": hostel_data.get("room_types", []),
        "available_slots": hostel_data.get("available_slots", 0),
        "gps_coordinates": hostel_data.get("gps_coordinates", {}),
        "image_paths": hostel_data.get("image_paths", []),
    }
    campus["hostels"].append(hostel)
    _save(data)
    return True, "Hostel added successfully."


def get_gps_coordinates(obj):
    coords = obj.get("gps_coordinates")
    if not coords:
        return None, None
    return coords.get("latitude"), coords.get("longitude")


def _haversine(lat1, lon1, lat2, lon2):
    # distance in kilometers
    r = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_nearby_hostels(campus, max_distance_km=3):
    lat, lon = get_gps_coordinates(campus)
    if lat is None or lon is None:
        return get_hostels(campus)
    nearby = []
    for hostel in get_hostels(campus):
        hlat, hlon = get_gps_coordinates(hostel)
        if hlat is None or hlon is None:
            continue
        distance = _haversine(lat, lon, hlat, hlon)
        if distance <= max_distance_km and hostel.get("available_slots", 0) > 0:
            nearby.append(hostel)
    if not nearby:
        return [h for h in get_hostels(campus) if h.get("available_slots", 0) > 0]
    return nearby


def get_directions_url(hostel):
    lat, lon = get_gps_coordinates(hostel)
    if lat is None or lon is None:
        return None
    return f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}"


def get_hostel_image_paths(hostel):
    return hostel.get("image_paths", [])


def get_hostel_room_types(hostel):
    return hostel.get("room_types", [])


def get_hostel_rules(hostel):
    return hostel.get("rules", [])
*** End Patch