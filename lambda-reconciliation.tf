locals {
  dns_discovery_lambda_reconciliation_name = "${local.resource_prefix}-reconciliation"
}

resource "aws_lambda_function" "dns_discovery_lambda_reconciliation" {
  function_name = local.dns_discovery_lambda_reconciliation_name
  filename      = local.lambda_code
  role          = aws_iam_role.dns_discovery_lambda.arn
  handler       = "app.reconciler.lambda_handler"
  timeout       = 15 * 60 # 15 minutes - maximum allowed by AWS
  description   = "SG DNS Discovery: ensures that DNS records are in sync with Instances in Scaling Groups."
  memory_size   = 128

  # Ensure log group is created prior to lambda
  depends_on = [aws_cloudwatch_log_group.dns_discovery_lambda_reconciliation]

  source_code_hash = data.archive_file.sg_dns_discovery_lambda_source.output_base64sha256

  runtime = local.lambda_runtime

  dynamic "vpc_config" {
    for_each = length(var.lambda_settings.subnets) > 0 ? [1] : []
    content {
      security_group_ids = var.lambda_settings.security_groups
      subnet_ids         = var.lambda_settings.subnets
    }
  }

  environment {
    variables = local.lambda_envrionment_variables
  }

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "dns_discovery_lambda_reconciliation" {
  name              = "/aws/lambda/${local.dns_discovery_lambda_reconciliation_name}"
  retention_in_days = var.lambda_settings.log_retention_in_days

  tags = local.tags
}

resource "aws_cloudwatch_event_rule" "dns_discovery_lambda_reconciliation" {
  name                = local.dns_discovery_lambda_reconciliation_name
  description         = "Triggers ${local.dns_discovery_lambda_reconciliation_name} run at specified ('${var.reconciliation.schedule_interval_minutes}m') rate."
  schedule_expression = local.reconciler_schedule_expression
  state               = var.reconciliation.schedule_enabled ? "ENABLED" : "DISABLED"

  tags = local.tags
}

resource "aws_cloudwatch_event_target" "dns_discovery_lambda_reconciliation" {
  rule      = aws_cloudwatch_event_rule.dns_discovery_lambda_reconciliation.name
  target_id = var.environment
  arn       = aws_lambda_function.dns_discovery_lambda_reconciliation.arn
}

resource "aws_lambda_permission" "dns_discovery_lambda_reconciliation" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dns_discovery_lambda_reconciliation.arn
  principal     = "events.${local.aws_dns_suffix}"
  source_arn    = aws_cloudwatch_event_rule.dns_discovery_lambda_reconciliation.arn
}
