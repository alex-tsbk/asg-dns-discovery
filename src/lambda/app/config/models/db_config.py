from dataclasses import dataclass
from typing import override

from app.utils.dataclass import DataclassBase


@dataclass
class DbConfig(DataclassBase):
    provider: str
    table_name: str
    config_item_key_id: str

    @override
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "DbConfig":
        """
        Converts dictionary to DbConfig object

        Example:
        {
            "provider": "<name_of_db_provider>",
            "table_name": "<dynamo_table_name>",
            "config_item_key_id": "<dynamo_table_key_id>"
        }
        """
        return DbConfig(**data)
