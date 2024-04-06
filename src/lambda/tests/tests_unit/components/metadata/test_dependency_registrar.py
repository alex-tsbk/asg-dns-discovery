from unittest.mock import MagicMock

from app.components.metadata.dependency_registrar import register_services
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.components.metadata.internal.instance_metadata_service import InstanceMetadataService


def test_register_services():
    di_container = MagicMock()

    register_services(di_container, MagicMock())

    di_container.register.assert_any_call(InstanceMetadataInterface, InstanceMetadataService, lifetime="scoped")
