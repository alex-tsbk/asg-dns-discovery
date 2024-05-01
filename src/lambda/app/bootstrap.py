import importlib.util
import os
from importlib.machinery import ModuleSpec

from app.contexts.instance_lifecycle_context import InstanceLifecycleContext
from app.contexts.runtime_context import RUNTIME_CONTEXT
from app.contexts.scaling_group_lifecycle_context import ScalingGroupLifecycleContext
from app.domain.handlers.handler_base import HandlerBase
from app.utils.di import DIContainer, DILifetimeScope
from app.utils.logging import get_logger

logger = get_logger()


def __build_di_container() -> DIContainer:
    """Builds the dependency injection container.

    Returns:
        DIContainer: Dependency injection container
    """
    return DIContainer()


def __register_essential_dependencies(di_container: DIContainer) -> None:
    """Any default dependencies that are not component-specific should be registered here.
    Also any dependencies that have no other dependencies should be registered here as well.
    Ones used during DI container initialization should also be registered here.

    Args:
        di_container (DIContainer): Dependency injection container
    """
    from app.config.env_configuration_service import EnvironmentConfigurationService
    from app.config.sg_configuration_service import ScalingGroupConfigurationsService

    # Configuration services
    di_container.register_as_self(ScalingGroupConfigurationsService)
    di_container.register_as_self(EnvironmentConfigurationService)
    if not RUNTIME_CONTEXT.is_test_context:  # Use caching configuration in non-test contexts
        from app.config.env_configuration_service import CachedEnvironmentConfigurationService

        di_container.decorate(EnvironmentConfigurationService, CachedEnvironmentConfigurationService)


def __register_aws_dependencies(di_container: DIContainer) -> None:
    """Registers AWS-specific dependencies.

    Args:
        di_container (DIContainer): Dependency injection container
    """
    # AWS Clients and Services
    from app.components.persistence.database_repository_interface import DatabaseRepositoryInterface
    from app.integrations.aws.services.cloudwatch_service import CloudWatchService
    from app.integrations.aws.services.dynamodb_repository import DynamoDbTableRepository
    from app.integrations.aws.services.ec2_asg_service import Ec2AutoScalingService
    from app.integrations.aws.services.ec2_service import Ec2Service
    from app.integrations.aws.services.route53_service import Route53Service
    from app.integrations.aws.services.sqs_service import SqsService

    di_container.register_as_self(CloudWatchService)
    di_container.register_as_self(Ec2AutoScalingService)
    di_container.register_as_self(Ec2Service)
    di_container.register_as_self(Route53Service)
    di_container.register_as_self(SqsService)
    di_container.register(DatabaseRepositoryInterface, DynamoDbTableRepository, name="dynamodb")

    # Event Handlers
    from app.handlers.aws.scaling_group_lifecycle_event_handler import AwsScalingGroupLifecycleEventHandler

    di_container.register_as_self(AwsScalingGroupLifecycleEventHandler)


def __register_handlers(di_container: DIContainer) -> None:
    """Registers handlers.

    Args:
        di_container (DIContainer): Dependency injection container
    """
    from app.workflows.instance_lifecycle.handlers.instance_discovery_handler import InstanceDiscoveryHandler
    from app.workflows.instance_lifecycle.handlers.instance_health_check_handler import InstanceHealthCheckHandler
    from app.workflows.instance_lifecycle.handlers.instance_readiness_handler import InstanceReadinessHandler
    from app.workflows.scaling_group_lifecycle.handlers.scaling_group_lifecycle_init_handler import (
        ScalingGroupLifecycleInitHandler,
    )
    from app.workflows.scaling_group_lifecycle.handlers.scaling_group_lifecycle_metadata_handler import (
        ScalingGroupLifecycleMetadataHandler,
    )

    # Scaling group lifecycle
    di_container.register(HandlerBase[ScalingGroupLifecycleContext], ScalingGroupLifecycleInitHandler, name="init", lifetime=DILifetimeScope.TRANSIENT)  # fmt: skip
    di_container.register(HandlerBase[ScalingGroupLifecycleContext], ScalingGroupLifecycleMetadataHandler, name="metadata", lifetime=DILifetimeScope.TRANSIENT)  # fmt: skip
    # Instance lifecycle
    di_container.register(HandlerBase[InstanceLifecycleContext], InstanceDiscoveryHandler, name="discovery", lifetime=DILifetimeScope.TRANSIENT)  # fmt: skip
    di_container.register(HandlerBase[InstanceLifecycleContext], InstanceHealthCheckHandler, name="health-check", lifetime=DILifetimeScope.TRANSIENT)  # fmt: skip
    di_container.register(HandlerBase[InstanceLifecycleContext], InstanceReadinessHandler, name="readiness", lifetime=DILifetimeScope.TRANSIENT)  # fmt: skip


def __register_workflows(di_container: DIContainer) -> None:
    """Registers workflows.

    Args:
        di_container (DIContainer): Dependency injection container
    """
    from app.workflows.instance_lifecycle.instance_lifecycle_workflow import InstanceLifecycleWorkflow
    from app.workflows.scaling_group_lifecycle.scaling_group_lifecycle_workflow import ScalingGroupLifecycleWorkflow
    from app.workflows.workflow_interface import WorkflowInterface

    # Workflow for handling Scaling Group lifecycle events
    di_container.register(WorkflowInterface[ScalingGroupLifecycleContext], ScalingGroupLifecycleWorkflow)
    # Workflow for handling Instance lifecycle events - Discovery, Health Check, Readiness, etc.
    di_container.register(WorkflowInterface[InstanceLifecycleContext], InstanceLifecycleWorkflow)


def __register_components_dependencies(
    components_directory: str, component_base_prefix: str, di_container: DIContainer
) -> None:
    """Registers dependencies for all components in the specified directory.

    Args:
        components_directory (str): Directory containing the components
        component_base_prefix (str): Base prefix for the components: 'app.components'
        di_container (DIContainer): Dependency injection container
    """

    for component_name in os.listdir(components_directory):
        component_path = os.path.join(components_directory, component_name)
        if os.path.isdir(component_path):
            component_path = os.path.join(component_path, "dependency_registrar.py")
            if os.path.exists(component_path):
                component_name = f"{component_base_prefix}.{component_name}.dependency_registrar"
                spec: ModuleSpec | None = importlib.util.spec_from_file_location(component_name, component_path)
                if spec is None:
                    raise Exception(f"Could not load module spec for {component_path}")
                if spec.loader is None:
                    raise Exception(f"Could not load loader for {component_path}")

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.register_services(di_container)
                logger.debug(f"Registered dependencies from component: {component_name} ('{component_path}')")


def bootstrap() -> DIContainer:
    """Bootstraps the application and returns the dependency injection container.

    Returns:
        DIContainer: Dependency injection container with all dependencies registered.

    Remarks:
        This function is called from the main entry point of the application and is responsible for
        registering all dependencies needed by the application. This function should ideally be called
        only once during the application lifecycle.
    """
    di_container = __build_di_container()
    # Register essential dependencies
    __register_essential_dependencies(di_container)
    # Then register any dependencies specific to the cloud provider
    if RUNTIME_CONTEXT.is_aws:
        __register_aws_dependencies(di_container)
    # Build the path to the components directory
    current_directory = os.path.dirname(os.path.abspath(__file__))
    components_directory = os.path.join(current_directory, "components")
    # Register dependencies for all components
    __register_components_dependencies(components_directory, "app.components", di_container)
    # Register handlers
    __register_handlers(di_container)
    # Register workflows
    __register_workflows(di_container)
    # Mark container as final so no new registrations can be made
    di_container.finalize()
    # Return the DI container
    return di_container
