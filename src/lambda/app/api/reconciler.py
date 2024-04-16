# from __future__ import annotations

# from multiprocessing import Pipe, Process

# from app.models.configs.asg_dns_config import AsgDnsConfigItem
# from app.observability.logging import get_logger, to_json
# from app.services.configuration_service import ConfigurationService
# from app.services.reconciliation_service import ReconciliationService


# def lambda_handler(event: dict, context):
#     """Lambda handler for the ASG DNS reconciliation process.

#     Args:
#         event (dict): For manual reconciliation, the event should contain the following keys:
#             {
#                 "manual_sync": "true",
#                 "asg_name": "ASG_NAME",
#                 "hosted_zone_id": "HOSTED_ZONE_ID",
#                 "record_name": "RECORD_NAME",
#                 "record_type": "RECORD_TYPE"
#             }
#         context: Lambda context object.
#     """
#     logger = get_logger()
#     logger.debug(f"Received event: {to_json(event)}")
#     configuration_service = ConfigurationService()
#     # See if we need to start a manual reconciliation
#     if _is_manual_sync(event):
#         asg_name, hosted_zone_id, record_name, record_type = _extract_manual_sync_params(event)
#         logger.info(f"Starting manual reconciliation for: {asg_name}/{hosted_zone_id}/{record_name}/{record_type}")
#         asg_dns_configs = configuration_service.get_asg_dns_configs()
#         # Check if the manual sync request is for a valid ASG DNS configuration
#         asg_dns_config = next(
#             filter(
#                 lambda c: c.asg_name == asg_name
#                 and c.hosted_zone_id == hosted_zone_id
#                 and c.record_name == record_name
#                 and c.record_type == record_type,
#                 asg_dns_configs.items,
#             ),
#             None,
#         )
#         if not asg_dns_config:
#             logger.error(f"Invalid manual sync request for: {asg_name}/{hosted_zone_id}/{record_name}/{record_type}.")
#             return {
#                 "statusCode": 400,
#                 "body": "Invalid manual sync request. No ASG configuration found matching the request parameters.",
#             }
#         asg_name, asg_error_message = _start_single_reconciliation([asg_dns_config], None)
#         if asg_error_message:
#             logger.error(f"Error processing configuration for: {asg_name} -> {asg_error_message}")
#             return {
#                 "statusCode": 500,
#                 "body": f"Error processing configuration for: {asg_name} -> {asg_error_message}",
#             }
#         return {
#             "statusCode": 200,
#             "body": "Reconciliation process finished for arguments provided.",
#         }

#     # Otherwise, start the bulk reconciliation process
#     _start_bulk_reconciliation(configuration_service)
#     return {"statusCode": 200, "body": "Reconciliation process finished."}


# def _start_bulk_reconciliation(configuration_service: ConfigurationService):
#     """Starts the bulk reconciliation process for all ASG DNS configurations.

#     Args:
#         configuration_service (ConfigurationService): _description_
#     """
#     logger = get_logger()
#     # Load managed ASG DNS configuration
#     asg_dns_configs = configuration_service.get_asg_dns_configs()
#     # Group by ASG name
#     asg_dns_configs_by_asg_name = {
#         asg_dns_config_item.asg_name: asg_dns_configs.for_asg_name(asg_dns_config_item.asg_name)
#         for asg_dns_config_item in asg_dns_configs.items
#     }
#     # Process each ASG DNS configuration in parallel
#     max_concurrency = configuration_service.get_reconciliation_config().max_concurrency
#     # Limit the number of processes to the maximum concurrency
#     concurrency = min(len(asg_dns_configs_by_asg_name.keys()), max_concurrency)
#     # Start the reconciliation process in parallel
#     # create a list to keep all processes
#     processes: list[Process] = []
#     # create a list to keep connections
#     parent_connections = []
#     for asg_dns_configs_items in asg_dns_configs_by_asg_name.values():
#         # create a pipe for communication
#         parent_conn, child_conn = Pipe()
#         parent_connections.append(parent_conn)

#         # create the process, pass instance and connection
#         process = Process(
#             target=_start_single_reconciliation,
#             args=(
#                 asg_dns_configs_items,
#                 child_conn,
#             ),
#         )
#         processes.append(process)

#     # start 'concurrency' processes and wait for them to finish
#     # partition the list into 'concurrency' chunks
#     for i in range(0, len(processes), concurrency):
#         for process in processes[i : i + concurrency]:
#             process.start()
#         for process in processes[i : i + concurrency]:
#             process.join()

#     for parent_connection in parent_connections:
#         received_items = parent_connection.recv()
#         asg_name = received_items[0]
#         asg_error_message = received_items[1]
#         if asg_error_message:
#             logger.error(f"Error processing configuration for: {asg_name} -> {asg_error_message}")
#         else:
#             logger.info(f"Finished processing configuration for: {asg_name}")


# def _start_single_reconciliation(asg_dns_configs: list[AsgDnsConfigItem], pipe_connection=None) -> tuple[str, str]:
#     """Starts the reconciliation process for the ASG DNS configuration.

#     Args:
#         asg_dns_config (list[AsgDnsConfigItem]): List of ASG DNS configuration items for the same ASG.

#     Returns:
#         tuple[str, str]:
#             [0] The ASG DNS configuration item string representation.
#             [1] Exception message, if any. Otherwise, None.
#     """
#     logger = get_logger()
#     # Extract ASG name, it'll be the same for all items
#     asg_name = asg_dns_configs[0].asg_name
#     # Ensure all configs are for the same ASG
#     if not all(c.asg_name == asg_name for c in asg_dns_configs):
#         raise ValueError("Invalid ASG DNS configuration items. ASG names do not match in all items.")

#     logger.info(f"Starting reconciliation for: '{asg_name}' ({len(asg_dns_configs)} items)")
#     asg_error_message = ""
#     reconciliation_service = ReconciliationService()
#     try:
#         reconciliation_service.reconcile(asg_dns_configs)
#     except Exception as e:
#         # TODO: Send data point to CloudWatch
#         asg_error_message = f"Error reconciling ASG DNS configuration: {str(e)}"

#     if pipe_connection:
#         pipe_connection.send([asg_name, asg_error_message])
#         pipe_connection.close()

#     return asg_name, asg_error_message


# def _is_manual_sync(event: dict) -> bool:
#     """Determines if the event is a manual sync request.

#     Args:
#         event (dict): Lambda event object.

#     Returns:
#         bool: True if the event is a manual sync request, otherwise False.
#     """
#     return str(event.get("manual_sync", False)).lower() == "true"


# def _extract_manual_sync_params(event: dict) -> tuple[str, str, str, str]:
#     """Extracts the ASG DNS configuration parameters from the event.

#     Args:
#         event (dict): The event object.

#     Returns:
#         tuple[str, str, str, str]:
#             [0] ASG name
#             [1] Hosted zone ID
#             [2] Record name
#             [3] Record type
#     """
#     return (
#         event.get("asg_name"),
#         event.get("hosted_zone_id"),
#         event.get("record_name"),
#         event.get("record_type"),
#     )
