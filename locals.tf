locals {
  MINUTE = 60
  # AWS target environment shortcuts
  aws_account_id = data.aws_caller_identity.current.account_id
  aws_region     = data.aws_region.current.name
  aws_partition  = data.aws_partition.current.partition
  aws_dns_suffix = data.aws_partition.current.dns_suffix
  # Distinct hosted zone IDs
  hosted_zones_ids = toset([for record in var.records : record.hosted_zone_id])
  # Distinct auto scaling group names
  asg_names = toset([for record in var.records : record.asg_name])
  # DynamoDB key id for service discovery configuration
  dynamo_db_iac_config_item_key_id = "service-discovery-iac-config"
  # DynamoDB key id for externally-managed configuration
  dynamo_db_external_config_item_key_id = "service-discovery-external-config"
  # Resource prefix
  resource_prefix = "${var.environment}-${var.resource_suffix}"
  # Resource tags
  tags = merge(
    {
      "dns-discovery:module"  = "dns-discovery"
      "dns-discovery:vendor"  = "third-party"
      "dns-discovery:version" = "1.0.0"
    },
    var.tags,
  )
}
