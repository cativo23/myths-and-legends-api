from fastapi import APIRouter
from os import getcwd
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/{name_file}")
def get_file(name_file: str):
    return FileResponse(path=getcwd() + "/app/images/" + name_file)
