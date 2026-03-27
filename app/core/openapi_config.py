"""
OpenAPI configuration for public and admin documentation.

This module provides custom OpenAPI schema generation to separate
public endpoints (GET/list) from admin endpoints (POST/PUT/DELETE).
"""

from typing import Any, Dict, List, Optional


# Tags that are considered "admin" operations
ADMIN_TAGS = {"users"}

# HTTP methods that are considered "admin" operations
ADMIN_METHODS = {"post", "put", "patch", "delete"}

# Specific paths that should be admin-only (all methods)
ADMIN_PATHS = {
    "/api/v1/users",  # All /api/v1/users/* paths are admin
    "/api/v1/auth/password-recovery",
    "/api/v1/auth/reset-password",
}

# Specific paths that are public (all methods, including POST for login)
PUBLIC_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/me",
    "/api/v1/images",  # All /api/v1/images/* paths are public
}

# Base resource paths where GET is public and POST/PUT/DELETE are admin
RESOURCE_PATHS = {
    "/api/v1/entities",
    "/api/v1/countries",
    "/api/v1/categories",
    "/api/v1/entity-types",
    "/api/v1/locations",
    "/api/v1/sources",
    "/api/v1/health",
}


def filter_openapi_schema(
    schema: Dict[str, Any],
    admin_only: bool = False,
) -> Dict[str, Any]:
    """
    Filter OpenAPI schema to show only public or admin endpoints.

    Args:
        schema: The full OpenAPI schema dictionary
        admin_only: If True, show only admin endpoints. If False, show only public.

    Returns:
        Filtered OpenAPI schema
    """
    import copy
    filtered = copy.deepcopy(schema)

    paths = filtered.get("paths", {})
    filtered_paths = {}

    for path, methods in paths.items():
        # Check if path is explicitly public or admin
        is_explicitly_public = any(
            path.startswith(pp) for pp in PUBLIC_PATHS
        )
        is_explicitly_admin = any(
            path.startswith(ap) for ap in ADMIN_PATHS
        )

        # Check if path is a resource path (GET=public, POST/PUT/DELETE=admin)
        is_resource_path = any(
            path.startswith(rp) for rp in RESOURCE_PATHS
        )

        filtered_methods = {}

        for method, details in methods.items():
            method_lower = method.lower()

            # Skip non-operation keys
            if method_lower in ("parameters", "servers"):
                filtered_methods[method] = details
                continue

            # Determine if this endpoint is admin
            is_admin = False

            # Check explicit rules first
            if is_explicitly_public and not is_explicitly_admin:
                is_admin = False
            elif is_explicitly_admin:
                is_admin = True
            # Check if it's a resource path (POST/PUT/DELETE/PATCH are admin)
            elif is_resource_path:
                if method_lower in ADMIN_METHODS:
                    is_admin = True
                else:
                    is_admin = False
            # Default: POST/PUT/DELETE/PATCH are considered admin
            elif method_lower in ADMIN_METHODS:
                is_admin = True

            # Filter based on mode
            if admin_only and is_admin:
                filtered_methods[method] = details
            elif not admin_only and not is_admin:
                filtered_methods[method] = details

        if filtered_methods:
            filtered_paths[path] = filtered_methods

    filtered["paths"] = filtered_paths
    return filtered


def get_public_openapi(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Get OpenAPI schema with only public endpoints."""
    return filter_openapi_schema(schema, admin_only=False)


def get_admin_openapi(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Get OpenAPI schema with only admin endpoints."""
    return filter_openapi_schema(schema, admin_only=True)
