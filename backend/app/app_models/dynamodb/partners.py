from abc import ABC
from datetime import time
from decimal import Decimal
from enum import Enum
from typing import Any, ClassVar, Literal

from fastapi.types import IncEx
from pydantic import BaseModel, Field
from ulid import ULID

from app.app_models.dynamodb.base import (
    BaseItem,
    UpdateExpression,
    get_id,
    normalize_string,
)

DaysInWeek = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]


class TimeRange(BaseModel):
    start: time
    end: time


class WorkingHours(BaseModel):
    day: DaysInWeek
    shifts: list[TimeRange] = Field(min_length=1)


class CurrencyEnum(str, Enum):
    RSD = "RSD"


class Location(BaseModel):
    address: str
    lat: Decimal
    lon: Decimal


class Address(BaseModel):
    country: str = Field(max_length=56)
    city: str = Field(max_length=100)
    location: Location


class PartnerChild(BaseItem, ABC):
    id: ULID = Field(default_factory=get_id)
    partner_id: ULID

    parent_entity: ClassVar[str] = "PARTNER"

    @property
    def pk(self) -> str:
        return f"{self.parent_entity}#{self.partner_id}"

    def to_dynamodb_item(self, exclude: IncEx | None = None) -> dict[str, Any]:
        item = super().to_dynamodb_item(exclude=exclude)
        item.update({"id": str(self.id), "partner_id": str(self.partner_id)})
        return item

    def to_update_expression(self) -> UpdateExpression:
        return super().to_update_expression()

    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> BaseItem:
        return super().from_dynamodb_item(item)


class Service(PartnerChild):
    name: str = Field(max_length=50)
    price: Decimal
    currency: CurrencyEnum

    entity_type: ClassVar[str] = "SERVICE"

    @property
    def sk(self) -> str:
        return f"{self.entity_type}#{self.id}"


class Staffer(PartnerChild):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)

    entity_type: ClassVar[str] = "STAFFER"

    @property
    def sk(self) -> str:
        return f"{self.entity_type}#{self.id}"


class Partner(BaseItem):
    id: ULID = Field(default_factory=get_id)
    name: str = Field(max_length=50)
    is_active: bool = Field(default_factory=lambda: True)
    address: Address
    working_hours: WorkingHours

    services: list[Service] = Field(default_factory=lambda: [])
    staff: list[Staffer] = Field(default_factory=lambda: [])

    parent_entity: ClassVar[str] = "PARTNER"
    entity_type: ClassVar[str] = "PARTNER"

    @property
    def pk(self) -> str:
        return f"{self.parent_entity}#{self.id}"

    @property
    def sk(self) -> str:
        return f"{self.entity_type}#{self.id}"

    @property
    def gsi_sk(self) -> str:
        return f"{self.entity_type}#{normalize_string(self.name)}"

    def to_dynamodb_item(self, exclude: IncEx | None = None) -> dict[str, Any]:
        item = super().to_dynamodb_item(exclude)
        item.update(
            {
                "id": str(self.id),
                "gsi_sk": self.gsi_sk,
            }
        )
        return item

    def to_update_expression(self) -> UpdateExpression:
        return super().to_update_expression()

    @classmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> BaseItem:
        return super().from_dynamodb_item(item)
