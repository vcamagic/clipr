from collections.abc import Sequence

from boto3.dynamodb.table import BatchWriter
from mypy_boto3_dynamodb import DynamoDBServiceResource

from app.core.config import settings
from app.models.dynamodb.partners import Partner, PartnerChild, Service, Staffer
from app.schemas.partners import PartnerCreate


def create_partner(
    dynamodb_service_resource: DynamoDBServiceResource, partner_in: PartnerCreate
) -> Partner:
    dynamodb_table = dynamodb_service_resource.Table(settings.DYNAMODB_TABLE_NAME)
    partner = to_model(partner_in)

    with dynamodb_table.batch_writer() as batch_writer:
        batch_writer.put_item(
            Item=partner.to_dynamodb_item(exclude={"services", "staff"})
        )
        put_children(batch_writer, partner.services)
        put_children(batch_writer, partner.staff)

    return partner


def get_partner(
    dynamodb_service_resource: DynamoDBServiceResource, partner_id: str
) -> Partner | None:
    dynamodb_table = dynamodb_service_resource.Table(settings.DYNAMODB_TABLE_NAME)
    response = dynamodb_table.query(
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


def put_children(batch_writer: BatchWriter, children: Sequence[PartnerChild]):
    for child in children:
        batch_writer.put_item(Item=child.to_dynamodb_item())


def to_model(partner_in: PartnerCreate) -> Partner:
    partner = Partner.model_validate(partner_in.model_dump())
    partner.services = [
        Service(**service.model_dump(), partner_id=partner.id)
        for service in partner_in.services
    ]
    partner.staff = [
        Staffer(**staffer.model_dump(), partner_id=partner.id)
        for staffer in partner_in.staff
    ]
    return partner
