from fastapi import APIRouter, status

from app.api.deps import CurrentSuperUser, CurrentUser, PartnersServiceDep
from app.schemas.partners import PartnerCreate, PartnerPublic

router = APIRouter()


@router.post("/", response_model=PartnerPublic, status_code=status.HTTP_201_CREATED)
def crate_partner(
    _: CurrentSuperUser,
    partner_in: PartnerCreate,
    partners_service: PartnersServiceDep,
):
    return partners_service.create_partner(partner_in)


@router.get(
    "/{partner_id}", response_model=PartnerPublic, status_code=status.HTTP_200_OK
)
def get_partner(
    _: CurrentUser,
    partner_id: str,
    partners_service: PartnersServiceDep,
):
    return partners_service.get_partner(partner_id)
