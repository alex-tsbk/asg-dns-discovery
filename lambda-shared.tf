locals {
  # Lambda function source code
  lambda_code = "${path.module}/src/lambda.zip"
  # Lambda function runtime version
  lambda_runtime = var.lambda_settings.python_runtime
  # Environment variables for the lambda function
  lambda_envrionment_variables = {
    # Cloud Provider
    cloud_provider = "aws"
    # Lambda logging
    log_identifier = var.lambda_settings.log_identifier
    log_level      = var.lambda_settings.log_level
    # Readiness check
    instance_readiness_enabled          = var.instance_readiness_default.enabled
    instance_readiness_interval_seconds = var.instance_readiness_default.interval_seconds
    instance_readiness_timeout_seconds  = max(min(var.instance_readiness_default.timeout_seconds, var.lambda_settings.timeout_seconds), var.instance_readiness.interval_seconds)
    instance_readiness_tag_key          = var.instance_readiness_default.tag_key
    instance_readiness_tag_value        = var.instance_readiness_default.tag_value
    # Configuration for database. Used for distributed locking and retrieval of configuration items.
    db_provider           = "dynamodb"
    db_table_name         = aws_dynamodb_table.dns_discovery_state_lock_table.name
    db_config_item_key_id = local.dynamo_db_config_item_key_id
    # Reconciliation
    reconciliation_what_if                    = var.reconciliation.what_if
    reconciliation_max_concurrency            = var.reconciliation.max_concurrency
    reconciliation_scaling_group_valid_states = join(",", var.reconciliation.scaling_group_valid_states)
    # Custom metrics and alarms
    monitoring_metrics_enabled                 = var.monitoring.metrics_enabled
    monitoring_metrics_provider                = var.monitoring.metrics_provider
    monitoring_metrics_namespace               = var.monitoring.metrics_namespace
    monitoring_alarms_enabled                  = var.monitoring.alarms_enabled
    monitoring_alarms_notification_destination = var.monitoring.alarms_notification_destination
  }

  # AWS is very picky about the schedule expression format
  reconciler_schedule_rate_suffix = var.reconciliation.schedule_interval_minutes > 1 ? "minutes" : "minute"
  reconciler_schedule_expression  = "rate(${var.reconciliation.schedule_interval_minutes} ${local.reconciler_schedule_rate_suffix})"
}

data "archive_file" "dns_discovery_lambda_source" {
  type             = "zip"
  source_dir       = "${path.module}/src/lambda"
  output_file_mode = "0666"
  output_path      = local.lambda_code
}
