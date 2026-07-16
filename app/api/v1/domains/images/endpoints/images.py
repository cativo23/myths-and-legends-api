from fastapi import APIRouter, HTTPException
from os import getcwd
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(tags=["images"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}


@router.get(
    "/{name_file}",
    summary="Get Image",
    description="Retrieve an image file from the server.",
    responses={
        200: {"description": "Image file returned", "content": {"image/*": {}}},
        400: {"description": "Invalid filename or extension"},
        404: {"description": "Image not found"},
    },
)
def get_file(name_file: str):
    """
    Serve image files from the /app/images/ directory.

    Security: Validates filename to prevent path traversal attacks.
    """
    # Reject path traversal attempts
    if ".." in name_file or "/" in name_file or "\\" in name_file:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Validate file extension
    file_ext = Path(name_file).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file extension. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Build safe path
    images_dir = Path(getcwd()) / "app" / "images"
    file_path = images_dir / name_file

    # Ensure resolved path is still within images directory
    try:
        resolved_path = file_path.resolve(strict=True)
        if not str(resolved_path).startswith(str(images_dir.resolve())):
            raise HTTPException(status_code=400, detail="Invalid filename")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(path=str(resolved_path))
