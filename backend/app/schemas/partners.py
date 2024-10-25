from datetime import time
from decimal import Decimal
from enum import Enum
from typing import Any, Literal

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
    working_hours: list[WorkingHours]
    services: list[Service] = Field(default_factory=lambda: [])
    staff: list[Staffer] = Field(default_factory=lambda: [])

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        model_dump = super().model_dump(exclude={"services", "staff"})

        return {
            **model_dump,
            "working_hours": [
                {
                    "day": working_day.day,
                    "shifts": [
                        {"start": str(shift.start), "end": str(shift.end)}
                        for shift in working_day.shifts
                    ],
                }
                for working_day in self.working_hours
            ],
        }


class PartnerPublic(PartnerCreate):
    id: ULID
    is_active: bool
