locals {
  # AWS target environment shortcuts
  aws_account_id = data.aws_caller_identity.current.account_id
  aws_region     = data.aws_region.current.name
  aws_partition  = data.aws_partition.current.partition
  aws_dns_suffix = data.aws_partition.current.dns_suffix
  # Distinct Route53 hosted zone IDs
  hosted_zones_ids = toset([for record in var.records : record.dns_config.dns_zone_id if record.dns_config.provider == "route53"])
  # Distinct auto scaling group names
  asg_names = toset([for record in var.records : record.scaling_group_name])
  # DynamoDB key id for sg dns discovery configuration
  dynamo_db_iac_config_item_key_id = "sg-dns-discovery-iac-config"
  # DynamoDB key id for externally-managed sg dns discovery configuration
  dynamo_db_external_config_item_key_id = "sg-dns-discovery-external-config"
  # Resource prefix
  resource_prefix = "${var.environment}-${var.resource_suffix}"
  # Resource tags
  tags = merge(
    {
      "sg-dns-discovery:module"  = "sg-dns-discovery"
      "sg-dns-discovery:version" = "1.0.0"
    },
    var.tags,
  )
  # Determine whether any 'private' ip's are being assessed
  resolves_private_ips = length([for record in var.records : record.dns_config.value_source if startswith(record.dns_config.value_source, "ip") && endswith(record.dns_config.value_source, "private")])
}
