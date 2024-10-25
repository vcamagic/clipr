from collections.abc import Generator
from typing import Annotated

import boto3
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from mypy_boto3_dynamodb import DynamoDBServiceResource
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models.sql.models import TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_boto3_session() -> boto3.Session:
    if settings.ENVIRONMENT == "local":
        return boto3.Session(
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
        )

    return boto3.Session(region_name=settings.AWS_REGION)


Boto3SessionDep = Annotated[boto3.Session, Depends(get_boto3_session)]


async def get_dynamodb_service_resource(
    session: Boto3SessionDep,
) -> DynamoDBServiceResource:
    if settings.ENVIRONMENT == "local":
        return session.resource("dynamodb", endpoint_url=settings.DYNAMODB_URL)

    return session.resource("dynamodb")


DynamoDbServiceResourceDep = Annotated[
    DynamoDBServiceResource, Depends(get_dynamodb_service_resource)
]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


CurrentSuperUser = Annotated[User, Depends(get_current_active_superuser)]
