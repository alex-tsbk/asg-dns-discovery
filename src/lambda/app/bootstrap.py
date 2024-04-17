import importlib.util
import os
from importlib.machinery import ModuleSpec

from app.utils.di import DIContainer, DILifetimeScope
from context import RUNTIME_CONTEXT


def __build_di_container() -> DIContainer:
    """Builds the dependency injection container.

    Returns:
        DIContainer: Dependency injection container
    """
    return DIContainer()


def __register_default_dependencies(di_container: DIContainer) -> None:
    """Any default dependencies that are not component-specific should be registered here.

    Args:
        di_container (DIContainer): Dependency injection container
    """
    pass


def __register_aws_dependencies(di_container: DIContainer) -> None:
    """Registers AWS-specific dependencies.

    Args:
        di_container (DIContainer): Dependency injection container
    """
    from app.infrastructure.aws.handlers.scaling_group_lifecycle_handler import AwsScalingGroupLifecycleHandler

    di_container.register(
        AwsScalingGroupLifecycleHandler, AwsScalingGroupLifecycleHandler, lifetime=DILifetimeScope.SCOPED
    )


def __register_components_dependencies(components_directory: str, di_container: DIContainer) -> None:
    """Registers dependencies for all components in the specified directory.

    Args:
        components_directory (str): Directory containing the components
        di_container (DIContainer): Dependency injection container
    """

    for component_name in os.listdir(components_directory):
        component_path = os.path.join(components_directory, component_name)
        if os.path.isdir(component_path):
            registrar_path = os.path.join(component_path, "dependency_registrar.py")
            if os.path.exists(registrar_path):
                spec: ModuleSpec | None = importlib.util.spec_from_file_location(
                    f"{component_name}.dependency_registrar", registrar_path
                )
                if spec is None:
                    raise Exception(f"Could not load module spec for {registrar_path}")
                if spec.loader is None:
                    raise Exception(f"Could not load loader for {registrar_path}")

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                module.register_dependencies(di_container)


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
    # Register default dependencies
    __register_default_dependencies(di_container)
    # Then register any dependencies specific to the cloud provider
    if RUNTIME_CONTEXT.is_aws:
        __register_aws_dependencies(di_container)
    # Finally, register dependencies for all components
    # TODO: Figure out relative path correctly...
    __register_components_dependencies("src/lambda/app/components", di_container)
    # Mark container as final so no new registrations can be made
    di_container.finalize()
    # Return the DI container
    return di_container
