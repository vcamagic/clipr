from fastapi import APIRouter, status

from app.api.deps import (
    CurrentSuperUser,
    CurrentUser,
    DynamoDbServiceResourceDep,
)
from app.crud import partner as partner_crud
from app.schemas.partners import PartnerCreate, PartnerPublic

router = APIRouter()


@router.post("/", response_model=PartnerPublic, status_code=status.HTTP_201_CREATED)
def crate_partner(
    _: CurrentSuperUser,
    partner_in: PartnerCreate,
    dynamodb_service_resource: DynamoDbServiceResourceDep,
):
    return partner_crud.create_partner(dynamodb_service_resource, partner_in)


@router.get(
    "/{partner_id}", response_model=PartnerPublic, status_code=status.HTTP_200_OK
)
def get_partner(
    _: CurrentUser,
    partner_id: str,
    dynamodb_service_resource: DynamoDbServiceResourceDep,
):
    return partner_crud.get_partner(dynamodb_service_resource, partner_id)
