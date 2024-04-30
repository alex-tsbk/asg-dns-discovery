import pytest
from app.utils.di import DIContainer, DILifetimeScope, Injectable, NamedInjectable


class Foo:
    def __init__(self):
        pass


class Bar:
    def __init__(self, foo: Foo):
        self.foo = foo


@pytest.fixture
def di_container():
    di_container = DIContainer()
    yield di_container
    di_container._scoped_instances.clear()


def test_resolve_transient_instance(di_container: DIContainer):
    di_container.register(Foo, Foo, lifetime=DILifetimeScope.TRANSIENT)
    foo = di_container.resolve(Foo)
    assert isinstance(foo, Foo)


def test_resolve_transient_instance_with_name(di_container: DIContainer):
    di_container.register(Foo, Foo, lifetime=DILifetimeScope.TRANSIENT, name="foo1")
    foo = di_container.resolve(Foo, name="foo1")
    assert isinstance(foo, Foo)


def test_resolve_transient_instance_with_names(di_container: DIContainer):
    di_container.register(Foo, Foo, lifetime=DILifetimeScope.TRANSIENT, name="foo1")
    di_container.register(Foo, Foo, lifetime=DILifetimeScope.TRANSIENT, name="foo2")
    foo1 = di_container.resolve(Foo, name="foo1")
    foo2 = di_container.resolve(Foo, name="foo2")
    assert foo1 is not foo2


def test_resolve_scoped_instance(di_container: DIContainer):
    di_container.register(Foo, Foo, lifetime=DILifetimeScope.SCOPED)
    foo1 = di_container.resolve(Foo)
    foo2 = di_container.resolve(Foo)
    assert foo1 is foo2


def test_resolve_with_dependency(di_container: DIContainer):
    di_container.register(Foo, Foo, lifetime=DILifetimeScope.SCOPED)
    di_container.register(Bar, Bar, lifetime=DILifetimeScope.TRANSIENT)
    bar = di_container.resolve(Bar)
    assert isinstance(bar, Bar)
    assert isinstance(bar.foo, Foo)


def test_resolve_with_dependency_raises_error_when_service_not_registered(di_container: DIContainer):
    with pytest.raises(ValueError):
        di_container.resolve(Bar)


def test_register_instance(di_container: DIContainer):
    foo_instance = Foo()
    di_container.register_instance(foo_instance)
    resolved_instance = di_container.resolve(Foo)
    assert resolved_instance is foo_instance


def test_register_instance_with_name(di_container: DIContainer):
    foo_instance = Foo()
    di_container.register_instance(foo_instance, name="foo_instance")
    resolved_instance = di_container.resolve(Foo, name="foo_instance")
    assert resolved_instance is foo_instance


def test_register_instance_with_same_name_raises_error_when_allow_override_is_false(di_container: DIContainer):
    foo_instance1 = Foo()
    foo_instance2 = Foo()
    di_container.register_instance(foo_instance1, name="foo_instance")
    with pytest.raises(ValueError):
        di_container.register_instance(foo_instance2, name="foo_instance", allow_override=False)


def test_register_instance_with_same_name_allows_override_when_allow_override_is_true(di_container: DIContainer):
    foo_instance1 = Foo()
    foo_instance2 = Foo()
    di_container.register_instance(foo_instance1, name="foo_instance")
    di_container.register_instance(foo_instance2, name="foo_instance", allow_override=True)
    resolved_instance = di_container.resolve(Foo, name="foo_instance")
    assert resolved_instance is foo_instance2


def test_register_raises_error_when_attempting_to_register_non_overridable_service_twice(di_container: DIContainer):
    di_container.register(Foo, Foo, lifetime=DILifetimeScope.SCOPED, overridable=False)
    with pytest.raises(ValueError):
        di_container.register(Foo, Foo, lifetime=DILifetimeScope.SCOPED, overridable=False)


def test_resolve_should_be_able_to_resolve_itself(di_container: DIContainer):
    container = di_container.resolve(DIContainer)
    assert container == di_container


class Baz:
    pass


class QuxI:
    def __init__(self, foo: Injectable[Foo, "Foo"]):
        self.foo = foo


class QuxNI:
    def __init__(self, foo: Injectable[Foo, NamedInjectable("foo")]):
        self.foo: Foo = foo


def test_resolve_explicit_injectable(di_container: DIContainer):
    di_container.register(Foo, Baz, lifetime=DILifetimeScope.SCOPED)
    di_container.register(QuxI, QuxI, lifetime=DILifetimeScope.TRANSIENT)
    qux = di_container.resolve(QuxI)
    assert isinstance(qux.foo, Baz)


def test_resolve_annotated_type_should_inject_correct_named_registered_instance(di_container: DIContainer):
    di_container.register(Foo, Baz, lifetime=DILifetimeScope.SCOPED)
    di_container.register(Foo, Foo, lifetime=DILifetimeScope.SCOPED, name="foo")
    di_container.register(QuxNI, QuxNI, lifetime=DILifetimeScope.TRANSIENT)
    qux = di_container.resolve(QuxNI)
    assert isinstance(qux.foo, Foo)


class CorgeInterface:
    def name(self):
        return "CorgeInterface"


class Corge(CorgeInterface):

    def name(self):
        return "Corge"


class Grault(CorgeInterface):

    def __init__(self, underlying: CorgeInterface):
        self.underlying = underlying

    def name(self):
        return f"{self.underlying.name()}->Grault"


def test_resolve_interface_type_should_inject_correct_instance_when_decorated(di_container: DIContainer):
    di_container.register(CorgeInterface, Corge, lifetime=DILifetimeScope.SCOPED)
    di_container.decorate(CorgeInterface, Grault)
    corge = di_container.resolve(CorgeInterface)
    assert corge.name() == "Corge->Grault"


def test_resolve_interface_type_should_raise_when_trying_to_decorated_named_registration_without_name(
    di_container: DIContainer,
):
    di_container = DIContainer()
    di_container.register(CorgeInterface, Corge, name="grault", lifetime=DILifetimeScope.SCOPED)
    with pytest.raises(ValueError):
        di_container.decorate(CorgeInterface, Grault)


def test_resolve_interface_type_should_inject_correct_instance_when_decorated_with_name(di_container: DIContainer):
    di_container.register(CorgeInterface, Corge, name="corge", lifetime=DILifetimeScope.SCOPED)
    di_container.decorate(CorgeInterface, Grault, name="corge")
    corge = di_container.resolve(CorgeInterface, name="corge")
    assert corge.name() == "Corge->Grault"


class GarplyInterface:
    pass


class Garply(GarplyInterface):
    pass


def test_resolve_interface_type_should_raise_when_trying_to_decorate_registration_with_different_type(
    di_container: DIContainer,
):
    di_container.register(CorgeInterface, Corge, lifetime=DILifetimeScope.SCOPED)
    with pytest.raises(ValueError):
        di_container.decorate(CorgeInterface, Garply)


class Waldo(GarplyInterface):
    pass


def test_resolve_should_raise_when_trying_to_decorate_registration_and_not_accepting_implementation(
    di_container: DIContainer,
):
    di_container.register(GarplyInterface, Garply, lifetime=DILifetimeScope.SCOPED)
    with pytest.raises(ValueError):
        di_container.decorate(GarplyInterface, Waldo)
