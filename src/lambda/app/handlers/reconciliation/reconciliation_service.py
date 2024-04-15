# from __future__ import annotations

# from functools import reduce

# from app.aws.asg import AutoScalingService
# from app.aws.dynamo import DynamoDBRepository
# from app.aws.ec2 import Ec2Service
# from app.aws.route53 import Route53Service
# from app.models.configs.asg_dns_config import AsgDnsConfigItem
# from app.models.dns_change_model import DnsChangeRequestModel
# from app.observability.logging import get_logger
# from app.services.configuration_service import ConfigurationService
# from app.services.dns_management_service import DnsManagementService
# from app.services.healthcheck_service import Ec2HealthCheckService
# from app.services.mutex_service import MutexService


# class ReconciliationService:
#     """Service class for reconciling Scaling Group state and update DNS records."""

#     def __init__(self):
#         self.logger = get_logger()
#         self.configuration_service = ConfigurationService()
#         self.autoscaling_service = AutoScalingService()
#         self.ec2_service = Ec2Service()
#         self.dns_management_service = DnsManagementService(Route53Service())
#         self.ec2_health_check_service = Ec2HealthCheckService()
#         self.dynamodb_repository = DynamoDBRepository(self.configuration_service.get_dynamo_config().table_name)
#         self.mutex_service = MutexService(self.dynamodb_repository)

#     def reconcile(self, asg_dns_configs: list[AsgDnsConfigItem]) -> None:
#         """Reconciles the ASG state and updates the DNS records.

#         Args:
#             asg_dns_configs (list[AsgDnsConfigItem]): The ASG DNS configuration items.
#                 Each item contains the ASG name and the DNS configuration. All items must be for the same ASG.

#         Raises:
#             ValueError: When the ASG DNS configuration items don't belong to the same ASG.
#         """
#         # Extract ASG name, it'll be the same for all items
#         asg_name = asg_dns_configs[0].asg_name
#         # Ensure all configs are for the same ASG
#         if not all(c.asg_name == asg_name for c in asg_dns_configs):
#             raise ValueError("Invalid ASG DNS configuration items. ASG names do not match in all items.")

#         # Acquire lock on all resources participating in the reconciliation process,
#         # before listing running EC2 instances
#         resource_locks = [a.lock_key for a in asg_dns_configs]
#         for resource_lock in resource_locks:
#             if not self.mutex_service.acquire_lock(resource_lock):
#                 raise ValueError(f"Failed to acquire lock for resource: {resource_lock}")

#         reconciliation_config = self.configuration_service.get_reconciliation_config()

#         try:
#             asg_instances_ids = self.autoscaling_service.list_running_ec2_instances([asg_name])
#             instances = self.ec2_service.get_instances(asg_instances_ids[asg_name])
#             self.logger.info(f"ASG: {asg_name} - Instances discovered: {len(instances)}")

#             readiness_config = self.configuration_service.get_readiness_config()
#             if readiness_config.enabled:
#                 # Filter out instances that don't have matching readiness tags
#                 instances = [
#                     instance
#                     for instance in instances
#                     if instance.tags
#                     and any(
#                         tag["Key"] == readiness_config.tag_key and tag["Value"] == readiness_config.tag_value
#                         for tag in instance.tags
#                     )
#                 ]
#                 self.logger.info(f"ASG: {asg_name} - Instances passed readiness check: {len(instances)}")

#             instance_public_ips = [i.public_ip_address for i in instances if i.public_ip_address]
#             instance_private_ips = [i.private_ip_address for i in instances if i.private_ip_address]

#             # Key is hosted zone ID, value is list of DNS change requests
#             dns_change_sets: dict[str, list[DnsChangeRequestModel]] = {}
#             # Loop through change requests, generate change sets
#             for asg_dns_config in asg_dns_configs:
#                 if asg_dns_config.hosted_zone_id not in dns_change_sets:
#                     dns_change_sets[asg_dns_config.hosted_zone_id] = []
#                 # Determine IPs to use based on the configuration
#                 ips = instance_public_ips if asg_dns_config.use_public_ip else instance_private_ips
#                 self.logger.info(f"ASG DNS Config: {asg_dns_config} - IPs: {ips}")
#                 # Filter out IPs that don't pass health check if health check is enabled
#                 if asg_dns_config.health_check_enabled:
#                     ips = [ip for ip in ips if self.ec2_health_check_service.check(ip, asg_dns_config)]
#                     self.logger.info(f"ASG DNS Config: {asg_dns_config} - IPs passed health check: {ips}")
#                 # Generate DNS change request
#                 change_request = self.dns_management_service.generate_change_request(
#                     asg_dns_config.hosted_zone_id,
#                     asg_dns_config.record_name,
#                     asg_dns_config.record_type,
#                     asg_dns_config.record_ttl,
#                     asg_dns_config.managed_dns_record,
#                     asg_dns_config.dns_mock_value,
#                     ips,
#                 )
#                 self.logger.debug(f"ASG DNS Config: {asg_dns_config} - extending change request with: {change_request}")
#                 dns_change_sets[asg_dns_config.hosted_zone_id].append(change_request)

#             # Update Route53 records
#             for hosted_zone_id, change_requests in dns_change_sets.items():
#                 # Generated lock key for all change requests for the same hosted zone
#                 self.logger.info(f"Applying change request for hosted zone: {hosted_zone_id} -> {change_requests}")
#                 if reconciliation_config.what_if:
#                     self.logger.info("Reconciliation is in what-if mode, skipping Route53 update")
#                     continue
#                 # Merge change requests and apply change request
#                 merged_change_request = reduce(lambda x, y: x << y, change_requests)
#                 self.logger.debug(f"Merged change request changes: {merged_change_request.changes}")
#                 self.dns_management_service.apply_change_request(hosted_zone_id, merged_change_request)
#         except Exception as e:
#             self.logger.error(f"Error occurred when performing updates during ASG DNS state reconciliation:\n{str(e)}")
#             raise e
#         finally:
#             # Release locks on all resources that were obtained.
#             for resource_lock in resource_locks:
#                 self.mutex_service.release_lock(resource_lock)

#         return
