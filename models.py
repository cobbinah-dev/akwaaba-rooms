from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from .database import Base
from datetime import date


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
