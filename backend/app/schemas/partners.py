from datetime import time
from decimal import Decimal
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field
from ulid import ULID

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
    lat: float
    lon: float


class Address(BaseModel):
    country: str
    city: str
    location: Location


class Service(BaseModel):
    name: str = Field(max_length=50)
    price: Decimal
    currency: CurrencyEnum


class Staffer(BaseModel):
    first_name: str = Field(max_length=50)
    last_name: str = Field(max_length=50)


class PartnerCreate(BaseModel):
    name: str
    address: Address
    working_hours: WorkingHours
    services: list[Service] = Field(default_factory=lambda: [])
    staff: list[Staffer] = Field(default_factory=lambda: [])


class PartnerPublic(PartnerCreate):
    id: ULID
    is_active: bool
