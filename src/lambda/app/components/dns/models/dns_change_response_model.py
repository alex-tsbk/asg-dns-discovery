from dataclasses import dataclass, field

from app.utils.dataclass import DataclassBase


@dataclass
class DnsChangeResponseModel(DataclassBase):
    """Represents the response of a DNS change request"""

    success: bool
    message: str = field(default="")

    @classmethod
    def Success(cls):
        return cls(success=True)

    @classmethod
    def Failure(cls):
        return cls(success=False)
