resource "aws_autoscaling_lifecycle_hook" "lch_ec2_register" {
  for_each = local.asg_names

  name                   = "${local.resource_prefix}-register"
  autoscaling_group_name = each.key
  default_result         = var.asg_lifecycle_hooks_settings.launch_default_result
  heartbeat_timeout      = var.asg_lifecycle_hooks_settings.launch_timeout_seconds
  lifecycle_transition   = "autoscaling:EC2_INSTANCE_LAUNCHING"

  notification_target_arn = aws_sns_topic.asg_dns_discovery.arn
  role_arn                = aws_iam_role.lch_ec2.arn
}

resource "aws_autoscaling_lifecycle_hook" "lch_ec2_drain" {
  for_each = local.asg_names

  name                   = "${local.resource_prefix}-drain"
  autoscaling_group_name = each.key
  default_result         = var.asg_lifecycle_hooks_settings.drain_default_result
  heartbeat_timeout      = var.asg_lifecycle_hooks_settings.drain_timeout_seconds
  lifecycle_transition   = "autoscaling:EC2_INSTANCE_TERMINATING"

  notification_target_arn = aws_sns_topic.asg_dns_discovery.arn
  role_arn                = aws_iam_role.lch_ec2.arn
}

resource "aws_iam_role" "lch_ec2" {
  name               = "${local.resource_prefix}-lch-role"
  assume_role_policy = data.aws_iam_policy_document.lch_ec2.json

  tags = local.tags
}

data "aws_iam_policy_document" "lch_ec2" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["autoscaling.${local.aws_dns_suffix}"]
    }
  }
}

resource "aws_iam_role_policy" "lch_ec2_policy" {
  name   = "${local.resource_prefix}-lch-policy"
  role   = aws_iam_role.lch_ec2.id
  policy = data.aws_iam_policy_document.lch_ec2_policy.json
}

data "aws_iam_policy_document" "lch_ec2_policy" {
  statement {
    sid    = "LCH"
    effect = "Allow"
    actions = [
      "sns:Publish",
      "autoscaling:CompleteLifecycleAction",
    ]
    resources = [
      aws_sns_topic.asg_dns_discovery.arn
    ]
  }
}
