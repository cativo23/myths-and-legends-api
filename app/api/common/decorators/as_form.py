import inspect
from typing import Type, get_origin

from fastapi import Form
from pydantic import BaseModel
from pydantic.fields import FieldInfo


def as_form(cls: Type[BaseModel]):
    new_parameters = []

    for field_name, field_info in cls.model_fields.items():
        field_info: FieldInfo  # type: ignore

        # Get the actual type annotation
        annotation = field_info.annotation
        if get_origin(annotation) is not None:
            # Handle Optional and other generic types
            pass

        new_parameters.append(
            inspect.Parameter(
                field_info.alias or field_name,
                inspect.Parameter.POSITIONAL_ONLY,
                default=(
                    Form(...) if field_info.is_required() else Form(field_info.default)
                ),
                annotation=annotation,
            )
        )

    async def as_form_func(**data):
        return cls(**data)

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    setattr(cls, "as_form", as_form_func)
    return cls
