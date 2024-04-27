from unittest.mock import MagicMock

from app.components.metadata.dependency_registrar import register_services
from app.components.metadata.instance_metadata_interface import InstanceMetadataInterface
from app.components.metadata.internal.instance_metadata_service import InstanceMetadataService
from app.utils.di import DILifetimeScope


def test_register_services():
    di_container = MagicMock()

    register_services(di_container)

    di_container.register.assert_any_call(InstanceMetadataInterface, InstanceMetadataService)
