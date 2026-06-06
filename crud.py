import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data.json"


def _default_store():
    return {
        "blocks": [],
        "rooms": [],
        "students": [],
        "allocations": [],
    }


def _ensure_data_file():
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        save_data(_default_store())


def load_data():
    _ensure_data_file()
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
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
    block = {"id": _next_id(data["blocks"]), "name": name}
    data["blocks"].append(block)
    save_data(data)
    return block


def create_room(data, number, capacity, block):
    room = {
        "id": _next_id(data["rooms"]),
        "number": number,
        "capacity": int(capacity),
        "block_id": block["id"],
    }
    data["rooms"].append(room)
    save_data(data)
    return room


def create_student(data, student_number, name, year):
    student = {
        "id": _next_id(data["students"]),
        "student_number": student_number,
        "name": name,
        "year": int(year),
    }
    data["students"].append(student)
    save_data(data)
    return student


def get_room_by_id(data, room_id):
    for room in data["rooms"]:
        if room["id"] == int(room_id):
            return room
    return None


def room_allocations(data, room):
    today = date.today().isoformat()
    return [
        alloc
        for alloc in data["allocations"]
        if alloc["room_id"] == room["id"]
        and (alloc.get("end_date") is None or alloc.get("end_date") >= today)
    ]


def occupied_count(data, room):
    return len(room_allocations(data, room))


def available_slots(data, room):
    return max(room["capacity"] - occupied_count(data, room), 0)


def allocate_student(student, room, start_date=None, end_date=None, data=None):
    if data is None:
        data = load_data()
        auto_save = True
    else:
        auto_save = False

    if start_date is None:
        start_date = date.today().isoformat()

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

    if auto_save:
        save_data(data)

    return alloc


def generate_room_summary_report(data=None):
    if data is None:
        data = load_data()

    report = []
    today = date.today().isoformat()
    for room in data["rooms"]:
        current_students = []
        for alloc in data["allocations"]:
            if alloc["room_id"] == room["id"] and (
                alloc.get("end_date") is None or alloc.get("end_date") >= today
            ):
                student = next((s for s in data["students"] if s["id"] == alloc["student_id"]), None)
                if student:
                    current_students.append(student["name"])

        block = next((b for b in data["blocks"] if b["id"] == room["block_id"]), {"name": "Unknown"})
        report.append({
            "room_id": room["id"],
            "room_number": room["number"],
            "block_name": block["name"],
            "capacity": room["capacity"],
            "assigned_count": len(current_students),
            "students": current_students,
        })
    return report


def find_student_assignment(student_name, data=None):
    if data is None:
        data = load_data()

    name_lower = student_name.strip().lower()
    student = next((s for s in data["students"] if name_lower in s["name"].lower()), None)
    if student is None:
        return None

    today = date.today().isoformat()
    for alloc in data["allocations"]:
        if alloc["student_id"] == student["id"] and (
            alloc.get("end_date") is None or alloc.get("end_date") >= today
        ):
            room = next((r for r in data["rooms"] if r["id"] == alloc["room_id"]), None)
            block = next((b for b in data["blocks"] if b["id"] == room["block_id"]), None) if room else None
            if room and block:
                return {"room_number": room["number"], "block_name": block["name"]}
    return None


def check_out_student(student_name, data=None):
    if data is None:
        data = load_data()
        auto_save = True
    else:
        auto_save = False

    name_lower = student_name.strip().lower()
    student = next((s for s in data["students"] if name_lower in s["name"].lower()), None)
    if student is None:
        return None

    today = date.today().isoformat()
    removed = []
    allocations = [
        alloc
        for alloc in data["allocations"]
        if alloc["student_id"] == student["id"]
        and (alloc.get("end_date") is None or alloc.get("end_date") >= today)
    ]

    for alloc in allocations:
        room = next((r for r in data["rooms"] if r["id"] == alloc["room_id"]), None)
        block = next((b for b in data["blocks"] if b["id"] == room["block_id"]), None) if room else None
        removed.append({
            "room_number": room["number"] if room else "Unknown",
            "block_name": block["name"] if block else "Unknown",
        })
        data["allocations"].remove(alloc)

    if removed and auto_save:
        save_data(data)

    return removed
