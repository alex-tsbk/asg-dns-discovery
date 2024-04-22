locals {
  dns_discovery_lambda_lifecycle_handler_name = "${local.resource_prefix}-lifecycle-handler"
}

resource "aws_lambda_function" "dns_discovery_lambda_lifecycle_handler" {
  function_name = local.dns_discovery_lambda_lifecycle_handler_name
  filename      = local.lambda_code
  role          = aws_iam_role.dns_discovery_lambda.arn
  handler       = "app.main.event_request_handler"
  timeout       = var.lambda_settings.lifecycle_timeout_seconds
  description   = "SG DNS Discovery: handles lifecycle events for Scaling Groups and updates tracked DNS records accordingly."
  memory_size   = 128

  # Ensure log group is created prior to lambda
  depends_on = [aws_cloudwatch_log_group.dns_discovery_lambda_lifecycle_handler]

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

resource "aws_cloudwatch_log_group" "dns_discovery_lambda_lifecycle_handler" {
  name = "/aws/lambda/${local.dns_discovery_lambda_lifecycle_handler_name}"

  retention_in_days = var.lambda_settings.log_retention_in_days

  tags = local.tags
}
