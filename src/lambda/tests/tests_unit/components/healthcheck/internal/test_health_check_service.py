from unittest.mock import MagicMock

import pytest
from app.components.healthcheck.internal.health_check_service import (
    HealthCheckProtocol,
    HealthCheckResultModel,
    HealthCheckService,
)


@pytest.fixture
def health_check_service():
    return HealthCheckService()


def test_tcp_check_success(health_check_service: HealthCheckService, monkeypatch: pytest.MonkeyPatch):
    ip = "127.0.0.1"
    port = 8080
    timeout_seconds = 5

    monkeypatch.setattr("socket.socket.connect_ex", lambda *args: 0)

    result = health_check_service._tcp_check(ip, port, timeout_seconds)

    assert result.healthy


def test_tcp_check_failure(health_check_service: HealthCheckService):
    ip = "127.0.0.1"
    port = 8888
    timeout_seconds = 5

    result = health_check_service._tcp_check(ip, port, timeout_seconds)

    assert result.healthy is False


def test_http_check_success(health_check_service: HealthCheckService, monkeypatch: pytest.MonkeyPatch):
    ip = "127.0.0.1"
    scheme = "http"
    port = "8080"
    path = "/health"
    timeout_seconds = "5"

    mock_urlopen = MagicMock()
    mock_urlopen.return_value.getcode.return_value = 200
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    result = health_check_service._http_check(ip, scheme, port, path, timeout_seconds)

    assert result.healthy is True


def test_http_check_failure(health_check_service: HealthCheckService, monkeypatch: pytest.MonkeyPatch):
    ip = "127.0.0.1"
    scheme = "http"
    port = "8888"
    path = "/health"
    timeout_seconds = "5"

    mock_urlopen = MagicMock()
    mock_urlopen.side_effect = Exception("Request failed")
    monkeypatch.setattr("urllib.request.urlopen", mock_urlopen)

    result = health_check_service._http_check(ip, scheme, port, path, timeout_seconds)

    assert result.healthy is False


def test_check_tcp_protocol(health_check_service: HealthCheckService, monkeypatch: pytest.MonkeyPatch):
    destination = "127.0.0.1"
    port = 8080
    timeout_seconds = 5
    sg_dns_config = MagicMock()
    sg_dns_config.health_check_config.protocol = HealthCheckProtocol.TCP
    sg_dns_config.health_check_config.port = port
    sg_dns_config.health_check_config.timeout_seconds = timeout_seconds

    mock_tcp_check = MagicMock()
    mock_tcp_check.return_value = HealthCheckResultModel(True)
    monkeypatch.setattr(health_check_service, "_tcp_check", mock_tcp_check)

    result = health_check_service.check(destination, sg_dns_config)

    assert result.healthy is True


def test_check_http_protocol(health_check_service: HealthCheckService, monkeypatch: pytest.MonkeyPatch):
    destination = "127.0.0.1"
    scheme = "http"
    port = 8080
    path = "/health"
    timeout_seconds = 5
    sg_dns_config = MagicMock()
    sg_dns_config.health_check_config.protocol = HealthCheckProtocol.HTTP
    sg_dns_config.health_check_config.port = port
    sg_dns_config.health_check_config.path = path
    sg_dns_config.health_check_config.timeout_seconds = timeout_seconds

    mock_http_check = MagicMock()
    mock_http_check.return_value = HealthCheckResultModel(True)
    monkeypatch.setattr(health_check_service, "_http_check", mock_http_check)

    result = health_check_service.check(destination, sg_dns_config)

    assert result.healthy


def test_check_unsupported_protocol(health_check_service: HealthCheckService):
    destination = "127.0.0.1"
    sg_dns_config = MagicMock()
    sg_dns_config.health_check_config.protocol = "FTP"

    with pytest.raises(ValueError):
        health_check_service.check(destination, sg_dns_config)
