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
      # TODO: Revisit this, because I would like to ensure that only necessary permissions are granted
      # "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:PutRetentionPolicy"
    ]
    resources = [
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
    sid    = "DescribeEc2"
    effect = "Allow"
    actions = [
      "ec2:Describe*",
      "ec2:Get*",
      "ec2:List*",
    ]
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = length(local.asg_names) > 0 ? [1] : []
    content {
      sid    = "CompleteLifecycleAction"
      effect = "Allow"
      actions = [
        "autoscaling:CompleteLifecycleAction",
      ]
      resources = [
        for asg_name in local.asg_names : "arn:${local.aws_partition}:autoscaling:${local.aws_region}:${local.aws_account_id}:autoScalingGroup:*:autoScalingGroupName/${asg_name}"
      ]
    }
  }

  dynamic "statement" {
    for_each = length(local.hosted_zones_ids) > 0 ? [1] : []
    content {
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
  }

  dynamic "statement" {
    for_each = length(local.hosted_zones_ids) > 0 ? [1] : []
    content {
      sid    = "Route53Change"
      effect = "Allow"
      actions = [
        "route53:GetChange",
      ]
      resources = [
        for zone_id in local.hosted_zones_ids : "arn:${local.aws_partition}:route53:::change/*"
      ]
    }

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

  statement {
    sid    = "SQS"
    effect = "Allow"
    actions = [
      "sqs:SendMessage",
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:GetQueueUrl",
    ]
    resources = [
      aws_sqs_queue.reconciliation_queue.arn,
      aws_sqs_queue.reconciliation_queue_deadletter.arn
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

resource "aws_iam_role_policy_attachment" "extra_dns_discovery_lambda_policies" {
  count = length(var.lambda_settings.extra_iam_policies_arns)

  policy_arn = var.lambda_settings.extra_iam_policies_arns[count.index]
  role       = aws_iam_role.dns_discovery_lambda.name
}
