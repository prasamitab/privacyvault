"""
Employee management routes
Handles encrypted salary data storage and retrieval
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
import uuid

from database import get_db
from models import Employee
from schemas import EmployeeCreate, EmployeeResponse, EmployeeListResponse
from encryption import he_instance


router = APIRouter()


@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new employee with encrypted salary
    
    The salary is encrypted using homomorphic encryption before storage.
    Individual salaries are never stored in plaintext.
    """
    # Check if employee_id already exists
    result = await db.execute(
        select(Employee).where(Employee.employee_id == employee_data.employee_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee ID {employee_data.employee_id} already exists",
        )
    
    # Encrypt the salary
    encrypted_salary, encryption_metadata = he_instance.encrypt_salary(employee_data.salary)
    
    # Create employee record with encrypted salary
    employee = Employee(
        employee_id=employee_data.employee_id,
        name=employee_data.name,
        department=employee_data.department,
        position=employee_data.position,
        encrypted_salary=encrypted_salary,
        encryption_context=str(encryption_metadata),
    )
    
    db.add(employee)
    await db.flush()
    await db.refresh(employee)
    
    return EmployeeResponse(
        id=employee.id,
        employee_id=employee.employee_id,
        name=employee.name,
        department=employee.department,
        position=employee.position,
        encrypted_salary=employee.encrypted_salary,
        created_at=employee.created_at,
    )


@router.get("/", response_model=EmployeeListResponse)
async def list_employees(
    department: str = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    List all employees (encrypted data only)
    
    Returns only encrypted salary data. Individual salaries cannot be viewed.
    """
    query = select(Employee)
    
    if department:
        query = query.where(Employee.department == department)
    
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    employees = result.scalars().all()
    
    # Get total count
    count_query = select(func.count(Employee.id))
    if department:
        count_query = count_query.where(Employee.department == department)
    
    total_result = await db.execute(count_query)
    total_count = total_result.scalar()
    
    employee_responses = [
        EmployeeResponse(
            id=emp.id,
            employee_id=emp.employee_id,
            name=emp.name,
            department=emp.department,
            position=emp.position,
            encrypted_salary=emp.encrypted_salary,
            created_at=emp.created_at,
        )
        for emp in employees
    ]
    
    return EmployeeListResponse(
        employees=employee_responses,
        total_count=total_count,
        encrypted_count=total_count,  # All are encrypted
    )


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific employee by ID
    
    Returns encrypted salary data only.
    """
    result = await db.execute(
        select(Employee).where(Employee.employee_id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )
    
    return EmployeeResponse(
        id=employee.id,
        employee_id=employee.employee_id,
        name=employee.name,
        department=employee.department,
        position=employee.position,
        encrypted_salary=employee.encrypted_salary,
        created_at=employee.created_at,
    )


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete an employee record
    
    This removes the encrypted data permanently.
    """
    result = await db.execute(
        select(Employee).where(Employee.employee_id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee {employee_id} not found",
        )
    
    await db.delete(employee)
    await db.flush()