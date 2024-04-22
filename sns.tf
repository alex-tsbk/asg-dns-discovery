resource "aws_sns_topic" "asg_dns_discovery" {
  name = local.resource_prefix

  policy = data.aws_iam_policy_document.asg_dns_discovery.json

  tags = local.tags
}

data "aws_iam_policy_document" "asg_dns_discovery" {
  statement {
    actions = ["sns:Publish"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    effect = "Allow"

    resources = ["arn:${local.aws_partition}:sns:*:*:${local.resource_prefix}"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_lambda_permission" "dns_discovery_lambda_lifecycle_landler" {
  statement_id  = "AsgEc2LifecycleHandling"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dns_discovery_lambda_lifecycle_handler.arn
  principal     = "sns.${local.aws_dns_suffix}"
  source_arn    = aws_sns_topic.asg_dns_discovery.arn

  depends_on = [
    aws_lambda_function.dns_discovery_lambda_lifecycle_handler
  ]
}

resource "aws_sns_topic_subscription" "dns_discovery_lambda_lifecycle_landler" {
  topic_arn = aws_sns_topic.asg_dns_discovery.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.dns_discovery_lambda_lifecycle_handler.arn

  depends_on = [
    aws_lambda_permission.dns_discovery_lambda_lifecycle_landler
  ]
}
