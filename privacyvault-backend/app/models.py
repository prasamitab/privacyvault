from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    encrypted_salary = Column(Text, nullable=False)
    encryption_context = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class ComputationResult(Base):
    __tablename__ = "computation_results"
    id = Column(Integer, primary_key=True, index=True)
    computation_type = Column(String(50), nullable=False)
    encrypted_result = Column(Text, nullable=True)
    decrypted_result = Column(Float, nullable=True)
    department = Column(String(100), nullable=True)
    employee_count = Column(Integer, nullable=True)
    computation_time_ms = Column(Float, nullable=True)
    privacy_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
