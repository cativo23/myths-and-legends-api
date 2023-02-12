import time
from typing import Any

from fastapi import APIRouter, Depends, Form, UploadFile
from fastapi.params import Path, Body, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..schemas import CharacterCreate, CharacterUpdate, Character as CharacterSchema
from ..services import character as character_service, image_service
from ...common.pagination.json_api_page import JsonApiPage
from ...common.responses import not_found, found, updated, created, deleted
from ....api import deps

router = APIRouter()


@router.get("/", response_model=JsonApiPage[CharacterSchema])
def list_characters(
        *,
        db: Session = Depends(deps.get_db),
        relations: str = None,
) -> Any:
    """
        Lists all characters.
    """
    relations = relations.split(',') if relations else []
    all_countries = character_service.get_all(db, relations=relations)
    return all_countries


@router.post("/")
async def add_character(
        db: Session = Depends(deps.get_db),
        image_file: UploadFile = File(...),
        character: CharacterCreate = Depends(CharacterCreate.as_form),
) -> JSONResponse:
    """
        Add a Character.
    """

    character_created = character_service.create(db, obj_in=character, image_file=image_file)

    return created(obj_name="Character", obj=character_created)


@router.get("/{character_id}")
def get_character(
        db: Session = Depends(deps.get_db),
        character_id: int = Path(...),
        relations: str = None
) -> JSONResponse:
    relations = relations.split(',') if relations else []

    character = character_service.get(db, item_id=character_id, relations=relations)

    if not character:
        return not_found(obj_name="Character")

    return found(obj_name="Character", obj=character)


@router.put("/{character_id}", response_model=CharacterSchema)
def update_character(*,
                     db: Session = Depends(deps.get_db),
                     character_id: int,
                     image_file: UploadFile = File(...),
                     character_in: CharacterUpdate = Depends(CharacterUpdate.as_form),
                     ) -> JSONResponse:
    """
    Update a character.
    """
    character = character_service.get(db, item_id=character_id)

    if not character:
        return not_found(obj_name="Character")

    character = character_service.update(db, db_obj=character, obj_in=character_in)

    return updated(obj_name="Character", obj=character)


@router.delete("/{character_id}", response_model=Any)
def delete_character(*,
                     db: Session = Depends(deps.get_db),
                     character_id: int
                     ) -> Any:
    """
    Delete a character.
    """
    character = character_service.get(db, item_id=character_id)

    if not character:
        return not_found(obj_name="Character")

    character_service.remove(db, item_id=character_id)

    return deleted(obj_name="Character")


@router.get("/search/")
def search_characters(db: Session = Depends(deps.get_db), term: str = None) -> JSONResponse:
    character = character_service.search(db, term=term)

    if not character:
        return not_found(obj_name="Character")

    return found(obj_name="Character", obj=character)
