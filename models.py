from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import date

# Use JSON type where available; for SQLite SQLAlchemy maps JSON to TEXT under the hood.
try:
    from sqlalchemy import JSON
except Exception:
    JSON = SQLITE_JSON


class Block(Base):
    __tablename__ = "blocks"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    rooms = relationship("Room", back_populates="block", cascade="all, delete-orphan")


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True)
    number = Column(String, nullable=False)
    capacity = Column(Integer, default=1)
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=False)
    block = relationship("Block", back_populates="rooms")
    allocations = relationship("Allocation", back_populates="room", cascade="all, delete-orphan")

    def occupied_count(self):
        return len([a for a in self.allocations if (a.end_date is None or a.end_date >= date.today())])

    def available_slots(self):
        return max(self.capacity - self.occupied_count(), 0)


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    student_number = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    year = Column(Integer)

    allocations = relationship("Allocation", back_populates="student", cascade="all, delete-orphan")


class Allocation(Base):
    __tablename__ = "allocations"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    start_date = Column(Date, default=date.today)
    end_date = Column(Date, nullable=True)

    student = relationship("Student", back_populates="allocations")
    room = relationship("Room", back_populates="allocations")


class Hostel(Base):
    __tablename__ = "hostels"
    id = Column(Integer, primary_key=True)
    university_code = Column(String, nullable=True, index=True)
    campus_name = Column(String, nullable=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=True)
    amenities = Column(JSON, default=list)
    image_urls = Column(JSON, default=list)
    gps_lat = Column(Float, nullable=True)
    gps_lon = Column(Float, nullable=True)
    available_slots = Column(Integer, default=0)
    room_types = Column(JSON, default=list)

    def location(self):
        return (self.gps_lat, self.gps_lon)
