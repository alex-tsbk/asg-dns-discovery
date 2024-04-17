resource "aws_iam_role" "dns_discovery_lambda" {
  name               = "${local.resource_prefix}-lambda"
  assume_role_policy = data.aws_iam_policy_document.dns_discovery_lambda_assume_role.json

  tags = local.tags
}

data "aws_iam_policy_document" "dns_discovery_lambda_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.${local.aws_dns_suffix}"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role_policy" "dns_discovery_lambda" {
  name   = "${local.resource_prefix}-lambda"
  role   = aws_iam_role.dns_discovery_lambda.id
  policy = data.aws_iam_policy_document.dns_discovery_lambda_permissions.json
}

data "aws_iam_policy_document" "dns_discovery_lambda_permissions" {
  statement {
    sid    = "Logs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:PutRetentionPolicy"
    ]
    resources = [
      "${aws_cloudwatch_log_group.dns_discovery_lambda_lifecycle_handler.arn}*",
      "${aws_cloudwatch_log_group.dns_discovery_lambda_reconciliation.arn}*",
      "arn:${local.aws_partition}:logs:*:*:*"
    ]
  }

  statement {
    sid    = "DescribeAsg"
    effect = "Allow"
    actions = [
      "autoscaling:DescribeAutoScalingGroups"
    ]
    resources = [
      "*"
    ]
  }

  statement {
    sid    = "CompleteLifecycleAction"
    effect = "Allow"
    actions = [
      "autoscaling:CompleteLifecycleAction",
    ]
    resources = [
      for asg_name in local.asg_names : "arn:${local.aws_partition}:autoscaling:${local.aws_region}:${local.aws_account_id}:autoScalingGroup:*:autoScalingGroupName/${asg_name}"
    ]
  }

  statement {
    sid    = "DescribeEc2"
    effect = "Allow"
    actions = [
      "ec2:Describe*",
      "ec2:Get*",
      "ec2:List*",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "Route53"
    effect = "Allow"
    actions = [
      "route53:ChangeResourceRecordSets",
      "route53:ListResourceRecordSets",
      "route53:GetHostedZone",
      "route53:ListHostedZones",
    ]
    resources = [
      for zone_id in local.hosted_zones_ids : "arn:${local.aws_partition}:route53:::hostedzone/${zone_id}"
    ]
  }

  statement {
    sid    = "Route53Change"
    effect = "Allow"
    actions = [
      "route53:GetChange",
    ]
    resources = [
      for zone_id in local.hosted_zones_ids : "arn:${local.aws_partition}:route53:::change/*"
    ]
  }

  statement {
    sid    = "DynamoDB"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:DescribeTable",
    ]
    resources = [
      aws_dynamodb_table.dns_discovery_table.arn
    ]
  }

  dynamic "statement" {
    # Required to allow lambda to create ENI in VPC
    for_each = length(var.lambda_settings.subnets) > 0 ? [1] : []
    content {
      sid    = "LambdaVPC"
      effect = "Allow"
      actions = [
        "ec2:CreateNetworkInterface",
        "ec2:DescribeNetworkInterfaces",
        "ec2:DeleteNetworkInterface",
        "ec2:DescribeInstances",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeVpcs"
      ]
      resources = [
        "*"
      ]
    }

  }
}
