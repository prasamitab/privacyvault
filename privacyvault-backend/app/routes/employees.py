from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models import Employee
from app.schemas import EmployeeCreate, EmployeeResponse, EmployeeListResponse
from app.encryption_mock import he_instance

router = APIRouter()

@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
async def create_employee(employee_data: EmployeeCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.employee_id == employee_data.employee_id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    encrypted_salary, metadata = he_instance.encrypt_salary(employee_data.salary)
    employee = Employee(
        employee_id=employee_data.employee_id,
        name=employee_data.name,
        department=employee_data.department,
        position=employee_data.position,
        encrypted_salary=encrypted_salary,
        encryption_context=str(metadata)
    )
    db.add(employee)
    await db.flush()
    await db.refresh(employee)
    return EmployeeResponse.model_validate(employee)

@router.get("/", response_model=EmployeeListResponse)
async def list_employees(department: str = None, limit: int = 100, db: AsyncSession = Depends(get_db)):
    query = select(Employee)
    if department:
        query = query.where(Employee.department == department)
    result = await db.execute(query.offset(0).limit(limit))
    employees = result.scalars().all()
    count_query = select(func.count(Employee.id))
    if department:
        count_query = count_query.where(Employee.department == department)
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    return EmployeeListResponse(
        employees=[EmployeeResponse.model_validate(e) for e in employees],
        total_count=total_count,
        encrypted_count=total_count
    )
