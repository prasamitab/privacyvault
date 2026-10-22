"""
Database models for PrivacyVault
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Employee(Base):
    """Employee model - stores encrypted salary data"""
    
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    
    # Encrypted salary data (stored as hex string)
    encrypted_salary = Column(Text, nullable=False)
    encryption_context = Column(Text, nullable=False)  # Store context info
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    computations = relationship("ComputationResult", back_populates="employee")


class ComputationResult(Base):
    """Store computation results on encrypted data"""
    
    __tablename__ = "computation_results"
    
    id = Column(Integer, primary_key=True, index=True)
    computation_type = Column(String(50), nullable=False)  # sum, average, min, max, etc.
    
    # Encrypted result (if computation was on encrypted data)
    encrypted_result = Column(Text, nullable=True)
    
    # Decrypted result (only stored for authorized views)
    decrypted_result = Column(Float, nullable=True)
    
    # Metadata
    department = Column(String(100), nullable=True)
    employee_count = Column(Integer, nullable=True)
    computation_time_ms = Column(Float, nullable=True)
    privacy_score = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    employee_id = Column(Integer, ForeignKey("employees.id"))
    employee = relationship("Employee", back_populates="computations")


class Organization(Base):
    """Organization model for multi-org analytics"""
    
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    org_name = Column(String(100), unique=True, nullable=False)
    org_code = Column(String(20), unique=True, nullable=False)
    
    # Encrypted aggregate data
    encrypted_total_salary = Column(Text, nullable=True)
    employee_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, server_default=func.now())