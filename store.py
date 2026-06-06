import json
from pathlib import Path
from datetime import date, datetime

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data.json"


def _today_iso():
    return date.today().isoformat()


def init_store():
    if not DATA_FILE.exists():
        data = {
            "blocks": [],
            "rooms": [],
            "students": [],
            "allocations": [],
        }
        _save(data)
    return _load()


def _load():
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _next_id(items):
    if not items:
        return 1
    return max(item["id"] for item in items) + 1


def find_block(data, name):
    for b in data["blocks"]:
        if b["name"] == name:
            return b
    return None


def create_block(data, name):
    existing = find_block(data, name)
    if existing:
        return existing
    b = {"id": _next_id(data["blocks"]), "name": name}
    data["blocks"].append(b)
    _save(data)
    return b


def create_room(data, number, capacity, block):
    room = {
        "id": _next_id(data["rooms"]),
        "number": number,
        "capacity": int(capacity),
        "block_id": block["id"],
    }
    data["rooms"].append(room)
    _save(data)
    return room


def create_student(data, student_number, name, year):
    s = {
        "id": _next_id(data["students"]),
        "student_number": student_number,
        "name": name,
        "year": year,
    }
    data["students"].append(s)
    _save(data)
    return s


def get_room_by_id(data, room_id):
    for r in data["rooms"]:
        if r["id"] == int(room_id):
            return r
    return None


def room_allocations(data, room):
    today = date.today().isoformat()
    allocs = [a for a in data["allocations"] if a["room_id"] == room["id"] and (a.get("end_date") is None or a.get("end_date") >= today)]
    return allocs


def occupied_count(data, room):
    return len(room_allocations(data, room))


def available_slots(data, room):
    return max(room["capacity"] - occupied_count(data, room), 0)


def allocate_student(data, student, room, start_date=None, end_date=None):
    if start_date is None:
        start_date = _today_iso()
    if available_slots(data, room) <= 0:
        raise ValueError("Room has no available slots")
    alloc = {
        "id": _next_id(data["allocations"]),
        "student_id": student["id"],
        "room_id": room["id"],
        "start_date": start_date,
        "end_date": end_date,
    }
    data["allocations"].append(alloc)
    _save(data)
    return alloc


def list_available_rooms(data):
    return [r for r in data["rooms"] if available_slots(data, r) > 0]


def generate_room_summary_report(data):
    report = []
    today = date.today().isoformat()
    for room in data["rooms"]:
        current_students = []
        for alloc in data["allocations"]:
            if alloc["room_id"] == room["id"] and (alloc.get("end_date") is None or alloc.get("end_date") >= today):
                sid = alloc["student_id"]
                student = next((s for s in data["students"] if s["id"] == sid), None)
                if student:
                    current_students.append(student["name"])
        block = next((b for b in data["blocks"] if b["id"] == room["block_id"]), {"name": "?"})
        report.append({
            "room_id": room["id"],
            "room_number": room["number"],
            "block_name": block["name"],
            "capacity": room["capacity"],
            "assigned_count": len(current_students),
            "students": current_students,
        })
    return report


def find_student_assignment(data, student_name):
    name_lower = student_name.strip().lower()
    # partial and case-insensitive
    student = next((s for s in data["students"] if name_lower in s["name"].lower()), None)
    if student is None:
        return None
    today = date.today().isoformat()
    for alloc in data["allocations"]:
        if alloc["student_id"] == student["id"] and (alloc.get("end_date") is None or alloc.get("end_date") >= today):
            room = next((r for r in data["rooms"] if r["id"] == alloc["room_id"]), None)
            block = next((b for b in data["blocks"] if b["id"] == room["block_id"]), None) if room else None
            return {"room_number": room["number"], "block_name": block["name"]} if room and block else None
    return None


def check_out_student(data, student_name):
    name_lower = student_name.strip().lower()
    student = next((s for s in data["students"] if name_lower in s["name"].lower()), None)
    if student is None:
        return None
    today = date.today().isoformat()
    removed = []
    allocs = [a for a in data["allocations"] if a["student_id"] == student["id"] and (a.get("end_date") is None or a.get("end_date") >= today)]
    for a in allocs:
        room = next((r for r in data["rooms"] if r["id"] == a["room_id"]), None)
        block = next((b for b in data["blocks"] if b["id"] == room["block_id"]), None) if room else None
        removed.append({"room_number": room["number"], "block_name": block["name"]})
        data["allocations"].remove(a)
    if removed:
        _save(data)
    return removed
