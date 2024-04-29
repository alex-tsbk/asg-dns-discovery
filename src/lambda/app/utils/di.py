from enum import Enum
from inspect import signature
from typing import Annotated, Any, Hashable, Type

# Type alias for Annotated type to try and hide internal implementation
Injectable = Annotated


class NamedInjectable:
    """Metadata class instructing DI container to resolve a named dependency from DI container,
    rather than the default one (unnamed). Must be used together with Injectable annotation.

    Example:
        ```python
        class FooInterface(ABC):
            pass

        class Foo(FooInterface):
            def __init__(self):
                pass

        class FooNamed(FooInterface):
            def __init__(self):
                pass

        class BarInterface(ABC):
            pass

        class Bar(BarInterface):
            def __init__(self, foo: Injectable[FooInterface, NamedInjectable("foo-named")]):
                self.foo = foo

        container = DIContainer()
        container.register(FooInterface, Foo, lifetime="scoped")
        container.register(FooInterface, FooNamed, lifetime="scoped", name="foo-named")
        container.register(BarInterface, Bar, lifetime="transient")
        bar = container.resolve(BarInterface)
        assert isinstance(bar.foo, FooNamed)
        ```
    """

    def __init__(self, name: str) -> None:
        self.name = name


class DILifetimeScope(Enum):
    """Lifetime scopes for dependency injection container."""

    # Transient lifetime - new instance will be created every time it's resolved.
    # Every class get's it's own instance of dependency.
    TRANSIENT = "transient"
    # Scoped lifetime - single instance will be created and reused for the lifetime of the container.
    # Every class gets the same instance.
    SCOPED = "scoped"


# Lifetime Scopes names for internal use only
_LTS_TRANSIENT = "transient"
_LTS_SCOPED = "scoped"
_LTS_INSTANCE = "instance"

# Types to ensure compatibility
type _DI_SERVICE_KEY = tuple[Annotated[Type[Any], "Interface Type"], Annotated[str, "Registration Name"]]
type _DI_SERVICE_IMPL = tuple[Annotated[Type[Any], "Implementation Type"], Annotated[str, "Lifetime Scope"]]
type _DI_INSTANCE = tuple[Annotated[Any, "Implementation Instance"], Annotated[str, "Lifetime Scope: instance"]]


class DIContainer:
    """Simple DI container. Supports transient and scoped lifetimes.

    Usage example:
        ```python
        class Foo:
            def __init__(self):
                pass

        class Bar:
            def __init__(self, foo: Foo):
                self.foo = foo

        container = DIContainer()
        container.register(Foo, Foo, lifetime="scoped")  # creates single instance of Foo and reuse it
        container.register(Bar, Bar, lifetime="transient")  # creates a new instance of Bar every time it's requested
        foo1 = container.resolve(Foo)
        foo2 = container.resolve(Foo)
        # foo1 and foo2 are the same instance
        bar1 = container.resolve(Bar)
        bar2 = container.resolve(Bar)
        # bar1 and bar2 are different instances
        ```
    """

    def __init__(self) -> None:
        self._services: dict[_DI_SERVICE_KEY, _DI_SERVICE_IMPL] = {}
        self._instances: dict[_DI_SERVICE_KEY, _DI_INSTANCE] = {}
        # Tracks services that cannot be overridden later
        self._non_overridable_services: dict[_DI_SERVICE_KEY, bool] = {}
        self._scoped_instances: dict[_DI_SERVICE_KEY, Any] = {}
        self._decorated_services: dict[Hashable, list[Type[Any]]] = {}
        # Allows marking container as final, so no more registrations can be done
        self.__final = False
        # Register self so it can be injected and resolved like any other service
        self.register_instance(self, allow_override=False)

    def register(
        self,
        interface: Type[Any],
        implementation: Type[Any],
        name: str = "",
        lifetime: DILifetimeScope = DILifetimeScope.SCOPED,
        overridable: bool = True,
    ):
        """Registers a an interface with an implementation in the container.

        Args:
            interface (Type): Type to register.
            implementation (Type): Type of the implementation to register. Will be constructed when resolved.
            name (str, optional): Name of the implementation, if need to support multiple. Defaults to None.
            lifetime (DILifetimeScope, optional): Lifetime scope of the implementation. Defaults to DILifetimeScope.SCOPED.
                TRANSIENT - new instance will be created every time it's resolved.
                SCOPED - single instance will be created and reused for the lifetime of the container.
            overridable (bool, optional): When set to True, allows overriding existing implementation. Defaults to True.

        Remarks:
            Type checking is not enforced for the implementation. It's up to the caller to ensure the implementation is correct subclass of the interface.
            This is so to allow dynamic implementation registration at runtime.
        """
        self.__guard_against_finalization()

        key = (interface, name)
        # Ensure we're not overriding non-overridable services
        if key in self._non_overridable_services:
            raise ValueError(f"Service {key} is marked as non-overridable.")
        # Check if service is marked as non-overridable
        if not overridable:
            self._non_overridable_services[key] = True
        # Register service
        self._services[key] = (implementation, lifetime.value)
        return self

    def register_as_self(
        self, implementation: Type[Any], name: str = "", lifetime: DILifetimeScope = DILifetimeScope.SCOPED
    ):
        """Registers an implementation as itself in the container. This is a shortcut
        for `register(...)` method when interface is the same as implementation.

        Args:
            implementation (Type): Type of the implementation to register.
            name (str, optional): Name of the implementation, if need to support multiple. Defaults to None.
            lifetime (DILifetimeScope, optional): Lifetime scope of the implementation. Defaults to DILifetimeScope.SCOPED.
                TRANSIENT - new instance will be created every time it's resolved.
                SCOPED - single instance will be created and reused for the lifetime of the container.
        """
        self.register(implementation, implementation, name, lifetime)
        return self

    def register_instance(self, instance: Any, name: str = "", allow_override: bool = False):
        """Registers an instance in the container.

        Args:
            instance (Any): Instance to register.
            name (str, optional): When provided, will be a named instance. Defaults to None.
            allow_override (bool, optional): When set to True, allows overriding existing instance. Defaults to False.

        Raises:
            ValueError: If instance with the same name is already registered and allow_override is False.
        """
        self.__guard_against_finalization()

        key: _DI_SERVICE_KEY = (type(instance), name)
        if key in self._instances and not allow_override:
            raise ValueError(f"Service {key} is already registered. Please set allow_override to True to override.")
        self._instances[key] = (instance, _LTS_INSTANCE)
        # Register in services container as well, to prevent resolving by type
        self._services[key] = (type(instance), _LTS_INSTANCE)
        return self

    def decorate(self, interface: Type[Any], implementation: Type[Any], name: str = ""):
        """Decorates an existing service with a new implementation.

        Remarks:
            The new implementation must be a subclass of the interface type.
            The service being decorated must be registered first.
            The decorated service will be resolved instead of the original one.
            The decorated service will have the same lifetime as the original one.
            The decorated service will receive the original service as a dependency, in the order decorators are declared.
        Args:
            interface (Type): Type to decorate.
            implementation (Type): Type of the new implementation.
            name (str, optional): If named instance is required, provide name. Defaults to None.
        """
        key = (interface, name)
        if key not in self._services:
            raise ValueError(f"Service {interface.__name__} not registered.")
        if not issubclass(implementation, interface):
            raise ValueError(f"Implementation {implementation.__name__} must be a subclass of {interface.__name__}.")
        if not hasattr(implementation, "__init__"):
            raise ValueError(f"Implementation {implementation.__name__} must have an __init__ method.")
        if not signature(implementation.__init__).parameters:
            raise ValueError(f"Implementation {implementation.__name__} must have at least one parameter in __init__.")
        if list(signature(implementation.__init__).parameters) == ["self", "args", "kwargs"]:
            raise ValueError(
                f"Implementation {implementation.__name__} must accept underlying implementation as explicit argument."
            )
        if key not in self._decorated_services:
            self._decorated_services[key] = []
        self._decorated_services[key].append(implementation)
        return self

    def resolve[T](self, interface: Type[T], name: str = "") -> T:
        """Resolves an instance of the given interface from the container.

        Args:
            interface (Type): Type of the interface to resolve.
            name (str, optional): If named instance is required, provide name. Defaults to None.

        Returns:
            Any: Instance of the given interface.
        """
        return self._build(interface, name)

    def _build[T](self, interface: Type[T], name: str = "") -> T:
        key = (interface, name)
        if key not in self._services:
            raise ValueError(f"Service {interface.__name__} not registered.")
        implementation, lifetime = self._services[key]

        if lifetime == _LTS_INSTANCE:
            return self._instances[key][0]

        if lifetime == _LTS_SCOPED:
            if key in self._scoped_instances:
                return self._scoped_instances[key]
            instance = self._create_instance(implementation)
            instance = self._build_decorated(interface, name, instance)
            self._scoped_instances[key] = instance
            return instance

        if lifetime == _LTS_TRANSIENT:
            instance = self._create_instance(implementation)
            instance = self._build_decorated(interface, name, instance)
            return instance

        raise ValueError(f"Unsupported lifetime {lifetime}.")

    def _build_decorated(self, interface: Type[Any], name: str, instance: Any) -> Any:
        key = (interface, name)
        if key not in self._decorated_services:
            return instance
        for decorator in self._decorated_services[key]:
            instance = decorator(instance)
        return instance

    def _create_instance(self, cls: Type[Any]) -> Any:
        """Creates an instance of the given class by resolving its dependencies.

        Args:
            cls (Type): Type of the class to create.

        Returns:
            Any: Instance of the given class.
        """
        # TODO: Add guard against circular dependencies

        constructor = signature(cls.__init__)
        kwargs = {}
        for name, param in constructor.parameters.items():
            # If name is one of the reserved names, skip
            if name in ["self", "args", "kwargs"]:
                continue
            param_type = param.annotation
            # If param type is not class - skip
            if not hasattr(param_type, "__name__"):
                continue

            # Check if param_type is Injectable
            if param_type.__name__ == Injectable.__name__:
                # In __metadata__ check if we have NamedInjectable instance
                named_injectable: NamedInjectable | None = next(
                    filter(lambda x: type(x) is NamedInjectable, param_type.__metadata__), None
                )
                actual_type = param_type.__origin__
                if named_injectable is not None:
                    kwargs[name] = self._build(actual_type, named_injectable.name)
                    continue
                # Ensure we update param_type to the actual type
                param_type = actual_type
            # By default resolve dependency without name
            kwargs[name] = self._build(param_type)
        return cls(**kwargs)

    def finalize(self):
        """Finalizes the container, preventing further registrations."""
        self.__final = True

    def __guard_against_finalization(self):
        if self.__final:
            raise ValueError("Container is finalized and no more registrations are allowed.")
