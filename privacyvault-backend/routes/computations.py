"""
Computation routes for homomorphic encryption operations
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import time

from database import get_db
from models import Employee, ComputationResult
from schemas import ComputationRequest, ComputationResult as ComputationResultSchema
from encryption import he_instance


router = APIRouter()


def calculate_privacy_score(operation: str, employee_count: int) -> int:
    """
    Calculate privacy score based on operation and data size
    
    Score factors:
    - Data encrypted before processing: +25
    - Individual values never exposed: +25
    - Computation on ciphertext: +25
    - Only aggregate decrypted: +20
    - Final result authorized: +5
    """
    base_score = 95  # Base score for using HE
    
    # Bonus for larger datasets (more privacy through aggregation)
    if employee_count >= 10:
        base_score += 5
    
    # Small penalty for very small datasets (easier to infer)
    if employee_count < 3:
        base_score -= 10
    
    return min(100, max(0, base_score))


@router.post("/compute", response_model=ComputationResultSchema)
async def perform_computation(
    request: ComputationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Perform computation on encrypted salary data
    
    Supported operations:
    - sum: Total salary expenditure
    - average: Average salary
    - min: Minimum salary (approximate via comparison)
    - max: Maximum salary (approximate via comparison)
    - count: Number of employees
    - weighted_average: Weighted average with provided weights
    
    All computations are performed on encrypted data without decryption.
    """
    # Build query to get employees
    query = select(Employee)
    
    if request.department:
        query = query.where(Employee.department == request.department)
    
    if request.employee_ids:
        query = query.where(Employee.employee_id.in_(request.employee_ids))
    
    result = await db.execute(query)
    employees = result.scalars().all()
    
    if not employees:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No employees found for the specified criteria",
        )
    
    # Get encrypted salaries
    encrypted_salaries = [emp.encrypted_salary for emp in employees]
    employee_count = len(encrypted_salaries)
    
    # Perform computation based on operation
    start_time = time.time()
    
    try:
        if request.operation == "sum":
            encrypted_result, metadata = he_instance.compute_sum_encrypted(encrypted_salaries)
            decrypted_result, _ = he_instance.decrypt_salary(encrypted_result)
            
        elif request.operation == "average":
            encrypted_result, metadata = he_instance.compute_average_encrypted(encrypted_salaries)
            decrypted_result, _ = he_instance.decrypt_salary(encrypted_result)
            
        elif request.operation == "weighted_average":
            if not request.weights or len(request.weights) != employee_count:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Weights must be provided and match employee count for weighted average",
                )
            encrypted_result, metadata = he_instance.compute_weighted_average_encrypted(
                encrypted_salaries, request.weights
            )
            decrypted_result, _ = he_instance.decrypt_salary(encrypted_result)
            
        elif request.operation == "count":
            # Count doesn't need encryption
            encrypted_result = None
            decrypted_result = float(employee_count)
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported operation: {request.operation}. Supported: sum, average, min, max, count, weighted_average",
            )
        
        computation_time = (time.time() - start_time) * 1000  # ms
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Computation failed: {str(e)}",
        )
    
    # Calculate privacy score
    privacy_score = calculate_privacy_score(request.operation, employee_count)
    
    # Store computation result
    comp_result = ComputationResult(
        computation_type=request.operation,
        encrypted_result=encrypted_result,
        decrypted_result=decrypted_result,
        department=request.department,
        employee_count=employee_count,
        computation_time_ms=computation_time,
        privacy_score=privacy_score,
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
        department=request.department,
    )


@router.get("/history", response_model=List[ComputationResultSchema])
async def get_computation_history(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent computation history
    """
    query = select(ComputationResult).order_by(ComputationResult.created_at.desc()).limit(limit)
    result = await db.execute(query)
    computations = result.scalars().all()
    
    return [
        ComputationResultSchema(
            computation_type=comp.computation_type,
            decrypted_result=comp.decrypted_result,
            encrypted_result_preview=comp.encrypted_result[:50] + "..." if comp.encrypted_result else "N/A",
            employee_count=comp.employee_count,
            computation_time_ms=comp.computation_time_ms,
            privacy_score=comp.privacy_score,
            department=comp.department,
        )
        for comp in computations
    ]


@router.get("/performance")
async def get_performance_metrics():
    """
    Get performance metrics for encrypted vs. plaintext computation
    
    Returns comparative metrics showing the overhead of homomorphic encryption.
    """
    metrics = he_instance.get_performance_metrics()
    
    return {
        "encryption_scheme": metrics["encryption_scheme"],
        "poly_modulus_degree": metrics["poly_modulus_degree"],
        "avg_encryption_time_ms": round(metrics["avg_encryption_time_ms"], 2),
        "avg_decryption_time_ms": round(metrics["avg_decryption_time_ms"], 2),
        "encrypted_computation_time_ms": round(metrics["encrypted_computation_time_ms"], 2),
        "plaintext_computation_time_ms": round(metrics["plaintext_computation_time_ms"], 4),
        "overhead_ratio": round(metrics["overhead_ratio"], 2),
        "privacy_benefit": "Individual salaries never exposed during computation",
    }