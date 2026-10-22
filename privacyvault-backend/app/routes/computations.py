from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import time
from app.database import get_db
from app.models import Employee, ComputationResult
from app.schemas import ComputationRequest, ComputationResult as ComputationResultSchema
from app.encryption_mock import he_instance

router = APIRouter()

def calculate_privacy_score(operation: str, employee_count: int) -> int:
    base_score = 95
    if employee_count >= 10:
        base_score += 5
    if employee_count < 3:
        base_score -= 10
    return min(100, max(0, base_score))

@router.post("/compute", response_model=ComputationResultSchema)
async def perform_computation(request: ComputationRequest, db: AsyncSession = Depends(get_db)):
    query = select(Employee)
    if request.department:
        query = query.where(Employee.department == request.department)
    result = await db.execute(query)
    employees = result.scalars().all()
    
    if not employees:
        raise HTTPException(status_code=404, detail="No employees found")
    
    encrypted_salaries = [emp.encrypted_salary for emp in employees]
    employee_count = len(encrypted_salaries)
    start_time = time.time()
    
    try:
        if request.operation == "sum":
            encrypted_result, _ = he_instance.compute_sum_encrypted(encrypted_salaries)
            decrypted_result, _ = he_instance.decrypt_salary(encrypted_result)
        elif request.operation == "average":
            encrypted_result, _ = he_instance.compute_average_encrypted(encrypted_salaries)
            decrypted_result, _ = he_instance.decrypt_salary(encrypted_result)
        elif request.operation == "count":
            encrypted_result = None
            decrypted_result = float(employee_count)
        else:
            raise HTTPException(status_code=400, detail="Unsupported operation")
        
        computation_time = (time.time() - start_time) * 1000
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Computation failed: {str(e)}")
    
    privacy_score = calculate_privacy_score(request.operation, employee_count)
    comp_result = ComputationResult(
        computation_type=request.operation,
        encrypted_result=encrypted_result,
        decrypted_result=decrypted_result,
        department=request.department,
        employee_count=employee_count,
        computation_time_ms=computation_time,
        privacy_score=privacy_score
    )
    db.add(comp_result)
    await db.flush()
    
    return ComputationResultSchema(
        computation_type=request.operation,
        decrypted_result=decrypted_result,
        encrypted_result_preview=encrypted_result[:50] + "..." if encrypted_result else "N/A",
        employee_count=employee_count,
        computation_time_ms=computation_time,
        privacy_score=privacy_score,
        department=request.department
    )

@router.get("/performance")
async def get_performance_metrics():
    metrics = he_instance.get_performance_metrics()
    return {
        "encryption_scheme": metrics["encryption_scheme"],
        "poly_modulus_degree": metrics["poly_modulus_degree"],
        "avg_encryption_time_ms": round(metrics["avg_encryption_time_ms"], 2),
        "avg_decryption_time_ms": round(metrics["avg_decryption_time_ms"], 2),
        "encrypted_computation_time_ms": round(metrics["encrypted_computation_time_ms"], 2),
        "plaintext_computation_time_ms": round(metrics["plaintext_computation_time_ms"], 4),
        "overhead_ratio": round(metrics["overhead_ratio"], 2),
        "privacy_benefit": "Individual salaries never exposed during computation"
    }
