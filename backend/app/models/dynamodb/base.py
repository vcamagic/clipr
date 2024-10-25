from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar

from fastapi.types import IncEx
from pydantic import BaseModel
from ulid import ULID

from app.utils import now_iso_format


@dataclass
class GSI:
    column_name: str
    value: str


@dataclass
class UpdateExpression:
    update_expression: str
    expression_attribute_names: dict[str, str]
    expression_attribute_values: dict[str, str]

    def update_gsis(self, gsis: list[GSI]) -> None:
        for index, gsi in enumerate(gsis):
            name = f"#GSI{index or ''}sk"
            value = f":GSI{index or ''}sk"
            self.update_expression += f", {name} = {value}"
            self.expression_attribute_names[name] = gsi.column_name
            self.expression_attribute_values[value] = gsi.value


class BaseItem(BaseModel, ABC):
    """Base item model for all items/rows in the table."""

    parent_entity: ClassVar[str] = ""
    entity_type: ClassVar[str] = ""

    @property
    @abstractmethod
    def pk(self) -> str:
        """Returns primary key value"""
        raise NotImplementedError

    @property
    @abstractmethod
    def sk(self) -> str:
        """Returns sort key value"""
        raise NotImplementedError

    @abstractmethod
    def to_dynamodb_item(self, exclude: IncEx | None = None) -> dict[str, Any]:
        """Converts model to a DynamoDb compatible dict."""
        return {
            "pk": self.pk,
            "sk": self.sk,
            "item_type": self.entity_type,
            **self.model_dump(exclude=exclude),
        }

    @classmethod
    @abstractmethod
    def from_dynamodb_item(cls, item: dict[str, Any]) -> "BaseItem":
        """Converts Dynamodb item to app class model."""
        return cls.model_validate(item)

    @abstractmethod
    def to_update_expression(self) -> UpdateExpression:
        """Returns update expression for updating the item in DynamoDb."""
        update_expression: list[str] = []
        expression_attribute_names: dict[str, str] = {}
        expression_attribute_values: dict[str, str] = {}

        for key, value in self.model_dump().items():
            attribute_name = f"#{key}"
            if key == "updatedAt":
                update_expression.append(f"{attribute_name} = :{key}")
                expression_attribute_names[attribute_name] = key
                expression_attribute_values[f":{key}"] = now_iso_format()
                continue

            update_expression.append(f"{attribute_name} = :{key}")
            expression_attribute_names[attribute_name] = key
            expression_attribute_values[f":{key}"] = value

        return UpdateExpression(
            update_expression="SET " + ", ".join(update_expression),
            expression_attribute_names=expression_attribute_names,
            expression_attribute_values=expression_attribute_values,
        )


def get_id() -> ULID:
    return str(ULID())


def normalize_string(value: str) -> str:
    return value.strip().upper()
