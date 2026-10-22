"""
PrivacyVault: Privacy-Preserving Computation Playground
FastAPI Backend Application
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from database import init_db, get_db
from routes import employees, computations, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    await init_db()
    print("✅ Database initialized")
    print(f"🔐 Encryption Scheme: {settings.ENCRYPTION_SCHEME}")
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## PrivacyVault: Privacy-Preserving Computation Playground
    
    An interactive platform demonstrating **Homomorphic Encryption** for private computation on sensitive data.
    
    ### Key Features
    
    - 🔐 **Homomorphic Encryption**: Compute on encrypted data without decryption
    - 📊 **Private Salary Analytics**: Calculate statistics without exposing individual salaries
    - 🎮 **Computation Playground**: Interactive interface for encrypted operations
    - 🛡️ **Privacy Attack Simulator**: Visual comparison of encrypted vs. traditional systems
    - 📈 **Real-Time Dashboard**: Monitor privacy metrics and performance
    
    ### Encryption Scheme
    
    Using **CKKS** (Cheon-Kim-Kim-Song) scheme via Pyfhel for approximate number arithmetic.
    Perfect for salary calculations and financial computations.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(employees.router, prefix=f"{settings.API_PREFIX}/employees", tags=["Employees"])
app.include_router(computations.router, prefix=f"{settings.API_PREFIX}/computations", tags=["Computations"])
app.include_router(analytics.router, prefix=f"{settings.API_PREFIX}/analytics", tags=["Analytics"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to PrivacyVault: Privacy-Preserving Computation Playground",
        "version": settings.APP_VERSION,
        "encryption_scheme": settings.ENCRYPTION_SCHEME,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "encryption_ready": True,
        "database": "connected",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )