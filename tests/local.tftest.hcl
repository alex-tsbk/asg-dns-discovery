mock_provider "aws" {
  alias  = "fake"
  source = "./tests/mocks"
}

variables {

  environment = "test"

  resource_suffix = "sg-dns-discovery"

  tags = {
    "custom-tag-key" = "custom-tag-value"
  }

  instance_readiness_default = {
    enabled          = true
    interval_seconds = 60
    timeout_seconds  = 300
    tag_key          = "sg-dns-discovery"
    tag_value        = "ready"
  }

  reconciliation = {
    scaling_group_valid_states = ["InService"]
    what_if                    = false
    max_concurrency            = 1
    schedule_enabled           = true
    schedule_interval_minutes  = 5
    message_broker             = "sqs"
    message_broker_url         = "" # Leave empty to use the default SQS queue
  }

  monitoring = {
    metrics_enabled                 = true
    metrics_provider                = "cloudwatch"
    metrics_namespace               = "SGDNSDiscovery"
    alarms_enabled                  = true
    alarms_notification_destination = "arn:aws:sns:us-east-1:123456789012:my-sns-topic"
  }
}

# Bootstraps infrastructure that is required for the module to function,
# such as Route53 hosted zone, EC2 Auto Scaling group, and required VPC/Network configurations.
run "setup" {
  providers = {
    aws = aws.fake
  }

  command = apply

  # Addressing problem:
  # Error: "launch_template.0.id" must begin with 'lt-' and be comprised of only alphanumeric characters: 78zbt5ma
  # Notes: `terraform test` setting random values for launch template id, which don't match the expected pattern
  override_resource {
    target = aws_launch_template.test
    values = {
      id = "lt-1234567890"
    }
  }

  module {
    source = "./tests/setup"
  }
}

run "execute" {
  providers = {
    aws = aws.fake
  }

  command = apply

  variables {
    records = [
      {
        scaling_group_name           = run.setup.test_asg_name
        multiple_config_proceed_mode = "ALL_OPERATIONAL"
        dns_config = {
          record_name = "test"
          provider    = "route53"
          dns_zone_id = run.setup.tests_route53_zone_id
        }
      }
    ]

    lambda_settings = {
      python_runtime            = "python3.8"
      log_identifier            = "sg-dns-discovery"
      lifecycle_timeout_seconds = 300
      subnets = [
        run.setup.test_public_subnet_id
      ]
    }

  }

  assert {
    condition     = length(keys(aws_autoscaling_lifecycle_hook.lch_ec2_register)) == 1
    error_message = "Expected 1 lifecycle hook for EC2 instance registration to be created"
  }

  assert {
    condition     = length(keys(aws_autoscaling_lifecycle_hook.lch_ec2_drain)) == 1
    error_message = "Expected 1 lifecycle hook for EC2 instance draining to be created"
  }

  # Expect "aws_lambda_function.dns_discovery_lambda_lifecycle_handler" to have vpc_config block
  assert {
    condition     = length(aws_lambda_function.dns_discovery_lambda_lifecycle_handler.vpc_config) > 0
    error_message = "Expected lambda function to have VPC configuration"
  }
}

