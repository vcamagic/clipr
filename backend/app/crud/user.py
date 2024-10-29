import uuid
from typing import Any

import boto3
import boto3.exceptions
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.sql.models import Item, ItemCreate, User, UserCreate, UserUpdate


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(
    *, cognito_idp_client: CognitoIdentityProviderClient, email: str, password: str
) -> str | None:
    try:
        initiate_auth_response = cognito_idp_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            ClientId=settings.CLIENT_ID,
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password,
            },
        )
        return initiate_auth_response["AuthenticationResult"].get("AccessToken", "")
    except boto3.exceptions.Boto3Error as error:
        print(f"Auth not successful: {error}")
        return None


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
