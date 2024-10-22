from typing import Any

from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code, detail, headers)


class NotFoundException(AppException):
    def __init__(
        self,
        entity: str = "Entity",
        id: str = "not specified",
        headers: dict[str, str] | None = None,
    ) -> None:
        MSG_TEMPLATE = "{entity} with id {id} does not exist."
        super().__init__(
            status.HTTP_404_NOT_FOUND,
            {
                "message": MSG_TEMPLATE.format(entity=entity, id=id),
                "status_code": status.HTTP_404_NOT_FOUND,
            },
            headers,
        )
