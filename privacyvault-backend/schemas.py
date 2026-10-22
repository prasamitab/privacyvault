"""
Pydantic schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Employee Schemas
class EmployeeBase(BaseModel):
    """Base employee schema"""
    employee_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    department: str = Field(..., min_length=1, max_length=100)
    position: str = Field(..., min_length=1, max_length=100)
    salary: float = Field(..., gt=0)


class EmployeeCreate(EmployeeBase):
    """Schema for creating an employee"""
    pass


class EmployeeResponse(BaseModel):
    """Schema for employee response (without sensitive data)"""
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
    """Schema for list of employees"""
    employees: List[EmployeeResponse]
    total_count: int
    encrypted_count: int


# Computation Schemas
class ComputationRequest(BaseModel):
    """Schema for computation requests"""
    operation: str = Field(..., description="Operation type: sum, average, min, max, count, weighted_average")
    department: Optional[str] = Field(None, description="Filter by department")
    employee_ids: Optional[List[str]] = Field(None, description="Specific employee IDs to include")
    weights: Optional[List[float]] = Field(None, description="Weights for weighted average")


class ComputationResult(BaseModel):
    """Schema for computation result"""
    computation_type: str
    decrypted_result: float
    encrypted_result_preview: str
    employee_count: int
    computation_time_ms: float
    privacy_score: int
    department: Optional[str] = None


class ComputationHistory(BaseModel):
    """Schema for computation history"""
    id: int
    computation_type: str
    decrypted_result: float
    employee_count: int
    computation_time_ms: float
    privacy_score: int
    created_at: datetime


# Analytics Schemas
class AnalyticsDashboard(BaseModel):
    """Schema for analytics dashboard"""
    total_employees: int
    total_encrypted_records: int
    total_computations: int
    departments: List[str]
    avg_computation_time_ms: float
    privacy_score: int
    encryption_scheme: str


class DepartmentStats(BaseModel):
    """Schema for department statistics"""
    department: str
    employee_count: int
    avg_salary: float
    min_salary: float
    max_salary: float
    total_salary: float


class PrivacyScoreBreakdown(BaseModel):
    """Schema for privacy score breakdown"""
    overall_score: int
    data_encrypted: bool
    individual_values_hidden: bool
    computation_on_ciphertext: bool
    only_aggregate_decrypted: bool
    final_result_authorized: bool
    recommendations: List[str]


# Multi-Organization Schemas
class OrganizationCreate(BaseModel):
    """Schema for creating an organization"""
    org_name: str
    org_code: str


class OrganizationResponse(BaseModel):
    """Schema for organization response"""
    id: int
    org_name: str
    org_code: str
    employee_count: int
    encrypted_total_salary: str
    
    class Config:
        from_attributes = True


class MultiOrgAnalytics(BaseModel):
    """Schema for multi-organization analytics"""
    organizations: List[OrganizationResponse]
    combined_avg_salary: float
    combined_total_employees: int
    privacy_preserved: bool