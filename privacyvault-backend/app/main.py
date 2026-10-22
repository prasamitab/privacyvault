from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from app.config import settings
from app.database import init_db
from app.routes import employees, computations, analytics
from app.routes import real_he

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("✅ Database initialized")
    print(f"🔐 Encryption: {settings.ENCRYPTION_SCHEME} (Simulated)")
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Privacy-Preserving Computation Playground with Homomorphic Encryption",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router, prefix=f"{settings.API_PREFIX}/employees", tags=["Employees"])
app.include_router(computations.router, prefix=f"{settings.API_PREFIX}/computations", tags=["Computations"])
app.include_router(analytics.router, prefix=f"{settings.API_PREFIX}/analytics", tags=["Analytics"])
app.include_router(
    real_he.router,
    prefix=f"{settings.API_PREFIX}/real-he",
    tags=["Real HE Demo"],
)


@app.get("/")
async def root():
    return {
        "message": "Welcome to PrivacyVault",
        "version": settings.APP_VERSION,
        "encryption_scheme": settings.ENCRYPTION_SCHEME,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "encryption_ready": True, "database": "connected"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
