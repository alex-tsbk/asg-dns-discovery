import socket
import urllib.request

from app.components.healthcheck.health_check_interface import HealthCheckInterface
from app.components.healthcheck.models.health_check_result_model import HealthCheckResultModel
from app.config.models.health_check_config import HealthCheckConfig, HealthCheckProtocol
from app.utils import instrumentation
from app.utils.logging import get_logger


class HealthCheckService(HealthCheckInterface):
    """Service for performing health check."""

    def __init__(self):
        self.logger = get_logger()

    def check(self, destination: str, health_check_config: HealthCheckConfig) -> HealthCheckResultModel:
        """
        Performs a health check on a destination in accordance with the given health check configuration.

        Args:
            destination (str): The address of the resource to run health check against. Can be IP, DNS name, etc.
            health_check_config (HealthCheckConfig): The health check configuration to use.


        Returns:
            HealthCheckResultModel: The model that represents the result of the health check.
        """
        protocol: HealthCheckProtocol = health_check_config.protocol
        port: int = health_check_config.port
        path: str = health_check_config.path
        timeout_seconds: int = health_check_config.timeout_seconds

        match protocol:
            case HealthCheckProtocol.TCP:
                return self._tcp_check(destination, port, timeout_seconds)
            case HealthCheckProtocol.HTTP | HealthCheckProtocol.HTTPS:
                scheme = health_check_config.protocol.value.lower()
                return self._http_check(destination, scheme, port, path, timeout_seconds)
            case _:  # type: ignore
                raise ValueError("Unsupported protocol. Only 'TCP' and 'HTTP(S)' are supported.")

    def _tcp_check(
        self,
        ip: str,
        port: int,
        timeout_seconds: int,
    ) -> HealthCheckResultModel:
        """
        Performs a TCP health check.

        Args:
            ip (str): The IP address to connect to.
            port (int): The port number to connect to.
            timeout_seconds (int): Connection timeout in seconds.

        Returns:
            HealthCheckResultModel: Model representing the result of the health check.
        """
        self.logger.info(f"Performing TCP health check on {ip}:{port}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout_seconds)

        @instrumentation.measure_time_taken
        def _instrumented_connect(address: tuple[str, int]):
            return sock.connect_ex(address)

        try:
            result, time_taken_ms = _instrumented_connect((ip, port))
            return HealthCheckResultModel(
                healthy=result == 0,
                protocol="TCP",
                endpoint=f"{ip}:{port}",
                time_taken_ms=time_taken_ms,
            )
        except socket.error as e:
            msg = f"Socket error: {e}"
            self.logger.error(msg)
            return HealthCheckResultModel(
                healthy=False,
                protocol="TCP",
                endpoint=f"{ip}:{port}",
                message=msg,
            )
        finally:
            sock.close()

    def _http_check(
        self,
        ip: str,
        scheme: str,
        port: int,
        path: str,
        timeout_seconds: int,
    ) -> HealthCheckResultModel:
        """
        Performs an HTTP health check.

        Args:
            ip (str): The IP address to send the request to.
            scheme (str): The HTTP scheme to use ('http' or 'https').
            port (str): The port number to send the request to.
            path (str): The HTTP path to request.
            timeout_seconds (int): Request timeout in seconds.

        Returns:
            HealthCheckResultModel: Model representing the result of the health check.
        """
        url = f"{scheme}://{ip}:{port}{path}"
        self.logger.info(f"Sending HTTP request to {url}")

        @instrumentation.measure_time_taken
        def _instrumented_urlopen(url: str, timeout: int):
            return urllib.request.urlopen(url, timeout=timeout)

        try:
            response, time_taken_ms = _instrumented_urlopen(url, timeout=timeout_seconds)
            return HealthCheckResultModel(
                healthy=response.getcode() == 200,
                endpoint=ip,
                protocol=scheme,
                status=response.getcode(),
                time_taken_ms=time_taken_ms,
            )
        except Exception as e:
            self.logger.error(f"HTTP check failed: {e}")
            return HealthCheckResultModel(False, ip, scheme, message=str(e))
