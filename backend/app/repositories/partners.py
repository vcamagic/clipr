from collections.abc import Sequence

from boto3.dynamodb.table import BatchWriter
from mypy_boto3_dynamodb import DynamoDBServiceResource

from app.api.deps import Session
from app.app_models.dynamodb.partners import Partner, PartnerChild, Service, Staffer
from app.core.config import settings


class PartnersRepository:
    def __init__(
        self, session: Session, dynamodb_resource: DynamoDBServiceResource
    ) -> None:
        self.session = session
        self.dynamodb_resource = dynamodb_resource
        self.dynamodb_table = dynamodb_resource.Table(settings.DYNAMODB_TABLE_NAME)

    def create_partner(self, partner: Partner) -> Partner:
        with self.dynamodb_table.batch_writer() as batch_writer:
            batch_writer.put_item(Item=partner.to_dynamodb_item())
            self._put_children(batch_writer, partner.services)
            self._put_children(batch_writer, partner.staff)
        return partner

    def get_partner(self, partner_id: str) -> Partner | None:
        response = self.dynamodb_table.query(
            KeyConditionExpression="#pk=:pk",
            ExpressionAttributeNames={"#pk": "pk"},
            ExpressionAttributeValues={":pk": f"PARTNER#{partner_id}"},
        )
        staff: list[Staffer] = []
        services: list[Service] = []
        partner: Partner | None = None
        for item in response.get("Items", []):
            if item["item_type"] == "STAFFER":
                staff.append(Staffer.model_validate(item))
                continue

            if item["item_type"] == "SERVICE":
                services.append(Service.model_validate(item))
                continue

            partner = Partner.model_validate(item)

        if not partner:
            return None

        partner.staff = staff
        partner.services = services
        return partner

    def _put_children(
        self, batch_writer: BatchWriter, children: Sequence[PartnerChild]
    ):
        for child in children:
            batch_writer.put_item(Item=child.to_dynamodb_item())
