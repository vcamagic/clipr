from app.app_models.dynamodb.partners import Partner, Service, Staffer
from app.exceptions import NotFoundException
from app.repositories.partners import PartnersRepository
from app.schemas.partners import PartnerCreate, PartnerPublic


class PartnersService:
    def __init__(self, partners_repository: PartnersRepository) -> None:
        self.partners_repository = partners_repository

    def create_partner(self, partner_in: PartnerCreate) -> PartnerPublic:
        partner = PartnersService.to_model(partner_in)
        partner = self.partners_repository.create_partner(partner)
        return PartnersService.from_model(partner)

    def get_partner(self, partner_id: str) -> PartnerPublic:
        partner = self.partners_repository.get_partner(partner_id)

        if not partner:
            raise NotFoundException("Partner", partner_id)

        return PartnersService.from_model(partner)

    @staticmethod
    def to_model(partner_in: PartnerCreate) -> Partner:
        partner = Partner.model_validate(
            {"name": partner_in.name, "address": partner_in.address.model_dump()}
        )
        partner.services = [
            Service(**service.model_dump(), partner_id=partner.id)
            for service in partner_in.services
        ]
        partner.staff = [
            Staffer(**staffer.model_dump(), partner_id=partner.id)
            for staffer in partner_in.staff
        ]
        return partner

    @staticmethod
    def from_model(partner: Partner) -> PartnerPublic:
        return PartnerPublic.model_validate(partner.model_dump())
