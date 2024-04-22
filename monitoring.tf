locals {
  should_use_cloudwatch_logs = var.monitoring.metrics_enabled && var.monitoring.metrics_provider == "cloudwatch"
}

resource "aws_iam_policy" "cloudwatch_custom_metrics" {
  count = local.should_use_cloudwatch_logs ? 1 : 0
  name  = "${local.resource_prefix}-push-custom-metrics"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "cloudwatch:PutMetricData",
      "Effect": "Allow",
      "Resource": "*",
      "Condition": {
          "StringEquals": {
            "cloudwatch:namespace": "${var.monitoring.metrics_namespace}"
          }
      }
    }
  ]
}
EOF
}

# Lambda(s)
resource "aws_iam_role_policy_attachment" "cloudwatch_custom_metrics" {
  count = local.should_use_cloudwatch_logs ? 1 : 0

  role       = aws_iam_role.dns_discovery_lambda.id
  policy_arn = aws_iam_policy.cloudwatch_custom_metrics[count.index].arn
}
