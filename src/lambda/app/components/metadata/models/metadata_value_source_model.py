from dataclasses import dataclass

from app.utils.dataclass import DataclassBase


@dataclass(kw_only=True)
class MetadataValueSourceModel(DataclassBase):
    """Model representing the source of the metadata value.

    Example:
        "tag:Name" -> type: tag, attribute: Name
        "ip:v4:public" -> type: ip, sub_type: v4, attribute: public
    """

    type: str
    sub_type: str
    attribute: str

    def __str__(self) -> str:
        """Get string representation of the model."""
        _sub_type = f":{self.sub_type}" if self.sub_type else ""
        return f"{self.type}{_sub_type}:{self.attribute}"

    def __post_init__(self):
        self.type = self.type.lower()
        self.sub_type = self.sub_type.lower()

    @classmethod
    def from_string(cls, source: str) -> "MetadataValueSourceModel":
        """Create MetadataValueSourceModel instance from string.

        Args:
            source (str): The source string.

        Returns:
            MetadataValueSourceModel: The instance of MetadataValueSourceModel.
        """
        parts = source.split(":")
        parts_len = len(parts)
        if parts_len < 1 or parts_len > 3:
            raise ValueError(f"Invalid source format: {source}")
        if parts_len == 1:
            return cls(type=parts[0], sub_type="", attribute="")
        if parts_len == 2:
            return cls(type=parts[0], sub_type="", attribute=parts[1])
        return cls(type=parts[0], sub_type=parts[1], attribute=parts[2])
