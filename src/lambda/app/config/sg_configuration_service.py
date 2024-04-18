import base64
import json
from typing import Any

from app.components.persistence.database_repository_interface import DatabaseRepositoryInterface
from app.config.env_configuration_service import EnvironmentConfigurationService
from app.config.models.scaling_group_config import ScalingGroupConfiguration, ScalingGroupConfigurations
from app.utils.exceptions import BusinessException
from app.utils.logging import get_logger


class ScalingGroupConfigurationsService:
    """Service class for resolving scaling groups configurations from repository."""

    def __init__(
        self,
        repository: DatabaseRepositoryInterface,
        environment_config: EnvironmentConfigurationService,
    ):
        # Cache placeholder
        self._cache: dict[str, Any] = {}
        self.logger = get_logger()
        self.repository = repository
        self.environment_config = environment_config

    def get_configs(self) -> ScalingGroupConfigurations:
        """Resolves Scaling Groups configurations for all Scaling Groups from repository.

        Returns:
            ScalingGroupConfigurations: Object containing all Scaling Group configurations.
        """
        CONFIG_CACHE_KEY = "cached_sg_configs"

        if cached_item := self._cache.get(CONFIG_CACHE_KEY, None):
            return cached_item

        # Keys that we'll be loading configuration from
        iac_config_item_key_id: str = self.environment_config.db_config.iac_config_item_key_id
        external_config_item_key_id: str = self.environment_config.db_config.external_config_item_key_id

        # Placeholder for configuration items
        config_items: list[dict[str, Any]] = []

        # First load items from IAC (infrastructure as code, terraform-generated) - these are critical to have to operate
        try:
            iac_config_items = self._load_scaling_group_configs(iac_config_item_key_id)
            config_items.extend(iac_config_items)
            self.logger.info(f"Successfully loaded {len(iac_config_items)} IAC configurations")
        except BusinessException as e:
            raise BusinessException(f"Failed to load IAC configurations: {str(e)}")

        # Load external configurations if available
        try:
            external_config_items = self._load_scaling_group_configs(external_config_item_key_id)
            config_items.extend(external_config_items)
            self.logger.info(f"Successfully loaded {len(external_config_items)} external Scaling Group configurations")
        except BusinessException as e:
            self.logger.warning(
                f"""Failed to load external Scaling Group configurations: {str(e)}.
                External Scaling Group configurations will not be used. This is not a critical failure, however
                if you are expecting to use external Scaling Group configurations, please ensure that the
                configuration is available in the repository and is correctly formatted and base64 encoded."""
            )

        # Convert to ScalingGroupConfiguration objects
        sg_config_items: list[ScalingGroupConfiguration] = [
            ScalingGroupConfiguration.from_dict(item) for item in config_items
        ]

        # Cache and return
        self._cache[CONFIG_CACHE_KEY] = ScalingGroupConfigurations(config_items=sg_config_items)
        return self._cache[CONFIG_CACHE_KEY]

    def _load_scaling_group_configs(self, config_item_id: str) -> list[dict[str, Any]]:
        """Load Scaling Group configurations from repository.

        Args:
            config_item_id (str): ID of the configuration item in the repository.

        Returns:
            list[dict[str, Any]]: List of Scaling Group configurations.
        """

        # Retrieve configuration from repository
        config_definition = self.repository.get(config_item_id)
        if not config_definition:
            raise BusinessException(
                f"Scaling Group configuration not found in repository using key provided: '{config_item_id}'"
            )

        config_item_base64: str = config_definition.get("config", "")
        if not config_item_base64:
            raise BusinessException(
                f"Unable to find 'config' property of Scaling Group configuration object using key provided '{config_item_id}'"
            )

        # Decode base64
        config_items: list[dict[str, Any]] = json.loads(base64.b64decode(config_item_base64).decode("utf-8"))
        if not config_items:
            raise BusinessException("Unable to decode and deserialize Scaling Groups configuration")

        return config_items
