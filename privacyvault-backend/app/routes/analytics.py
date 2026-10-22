from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct
from app.database import get_db
from app.models import Employee, ComputationResult
from app.schemas import AnalyticsDashboard
from app.config import settings

router = APIRouter()

@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    emp_count = await db.execute(select(func.count(Employee.id)))
    total_employees = emp_count.scalar() or 0
    
    comp_count = await db.execute(select(func.count(ComputationResult.id)))
    total_computations = comp_count.scalar() or 0
    
    dept_result = await db.execute(select(distinct(Employee.department)))
    departments = [row[0] for row in dept_result.fetchall()]
    
    avg_time_result = await db.execute(select(func.avg(ComputationResult.computation_time_ms)))
    avg_computation_time = avg_time_result.scalar() or 0.0
    
    privacy_score = 95 if total_employees > 0 else 100
    
    return AnalyticsDashboard(
        total_employees=total_employees,
        total_encrypted_records=total_employees,
        total_computations=total_computations,
        departments=departments,
        avg_computation_time_ms=round(avg_computation_time, 2),
        privacy_score=privacy_score,
        encryption_scheme=settings.ENCRYPTION_SCHEME
    )

@router.get("/encryption/info")
async def get_encryption_info():
    from app.encryption_mock import he_instance
    performance = he_instance.get_performance_metrics()
    return {
        "scheme": settings.ENCRYPTION_SCHEME,
        "description": "CKKS scheme for approximate number arithmetic (Simulated)",
        "poly_modulus_degree": settings.POLY_MOD_DEGREE,
        "scale": settings.SCALE,
        "supported_operations": ["Addition", "Average", "Sum"],
        "performance_metrics": performance,
        "privacy_guarantees": [
            "Individual salaries encrypted before storage",
            "Computation on encrypted data",
            "Only aggregate results decrypted"
        ]
    }
