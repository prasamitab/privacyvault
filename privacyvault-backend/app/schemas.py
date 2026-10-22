from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class EmployeeBase(BaseModel):
    employee_id: str
    name: str
    department: str
    position: str
    salary: float

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(BaseModel):
    id: int
    employee_id: str
    name: str
    department: str
    position: str
    encrypted_salary: str
    created_at: datetime
    class Config:
        from_attributes = True

class EmployeeListResponse(BaseModel):
    employees: List[EmployeeResponse]
    total_count: int
    encrypted_count: int

class ComputationRequest(BaseModel):
    operation: str
    department: Optional[str] = None

class ComputationResult(BaseModel):
    computation_type: str
    decrypted_result: float
    encrypted_result_preview: str
    employee_count: int
    computation_time_ms: float
    privacy_score: int
    department: Optional[str] = None

class AnalyticsDashboard(BaseModel):
    total_employees: int
    total_encrypted_records: int
    total_computations: int
    departments: List[str]
    avg_computation_time_ms: float
    privacy_score: int
    encryption_scheme: str
