from dataclasses import dataclass
from typing import Self, override

from app.utils.dataclass import DataclassBase


@dataclass
class DbConfig(DataclassBase):
    provider: str
    table_name: str
    # ID of the key in the repository that stores the configuration item generated out of terraform
    iac_config_item_key_id: str
    # ID of the key in the repository that stores the configuration item operated externally
    external_config_item_key_id: str

    @override
    @classmethod
    def from_dict(cls, data: dict[str, str]) -> Self:
        """
        Converts dictionary to DbConfig object

        Example:
        {
            "provider": "<name_of_db_provider>",
            "table_name": "<table_name>",
            "iac_config_item_key_id": "<key_id_for_terraform_generated_config>",
            "manual_config_item_key": "<key_id_for_manually_operated_config>",
        }
        """
        return cls(**data)
