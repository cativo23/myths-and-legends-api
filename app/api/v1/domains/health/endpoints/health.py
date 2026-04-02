"""
Health check endpoints for Kubernetes/cloud deployments.

Provides three levels of health checks:
- /health - Basic health check (is the service running?)
- /health/live - Liveness probe (is the service alive?)
- /health/ready - Readiness probe (is the service ready to accept traffic?)
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.shared.deps import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get(
    "",
    summary="Health Check",
    description="Basic health check endpoint. Returns service status and timestamp.",
    responses={
        200: {"description": "Service is healthy"},
    },
)
@router.get(
    "/",
    summary="Health Check",
    description="Basic health check endpoint. Returns service status and timestamp.",
    responses={
        200: {"description": "Service is healthy"},
    },
)
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns service status and uptime information.
    """
    return {
        "status": "healthy",
        "service": "myths-and-legends-api",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/live",
    summary="Liveness Probe",
    description="Kubernetes liveness probe. Returns healthy as long as the service is running.",
    responses={
        200: {"description": "Service is alive"},
    },
)
async def liveness_probe() -> dict[str, Any]:
    """
    Liveness probe endpoint.

    Kubernetes uses this to determine if the container should be restarted.
    Returns healthy as long as the service is running.
    """
    return {
        "status": "alive",
        "service": "myths-and-legends-api",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/ready",
    summary="Readiness Probe",
    description="Kubernetes readiness probe. Checks database connectivity and other dependencies.",
    responses={
        200: {"description": "Service is ready (all dependencies healthy)"},
        503: {"description": "Service not ready (dependency unavailable)"},
    },
    status_code=status.HTTP_200_OK,
)
async def readiness_probe(
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    Readiness probe endpoint.

    Kubernetes uses this to determine if the service is ready to accept traffic.
    Checks database connectivity and other dependencies.

    Returns:
    - 200: Service is ready (all dependencies healthy)
    - 503: Service not ready (dependency unavailable)
    """
    health_data = {
        "status": "ready",
        "service": "myths-and-legends-api",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {},
    }

    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_data["checks"]["database"] = {
            "status": "healthy",
            "latency_ms": 0,  # Could measure actual latency if needed
        }
    except Exception as e:
        health_data["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_data["status"] = "unhealthy"

    # Return 503 if any check failed
    if health_data["status"] != "ready":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_data,
        )

    return health_data
