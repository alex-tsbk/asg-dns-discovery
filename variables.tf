variable "environment" {
  description = "Name of the integration environment. Example: dev, stage, prod, etc."
  type        = string
}

variable "resource_suffix" {
  description = "Value to be appended to the resource names."
  type        = string
  default     = "sg-dns-discovery"
}

variable "tags" {
  description = "Additional tags to be applied to all resources created by this module."
  type        = map(string)
  default = {
  }
}

variable "records" {
  description = "List of configuration objects describing how exactly each Scaling Group instances should be translated to DNS."
  type = list(object({
    # ###
    # GENERAL SETTINGS
    # ###

    # Name of the Scaling Group that is the target of the DNS Discovery
    scaling_group_name = string

    # Determines how exactly to proceed with making DNS changes in the situations
    # when Scaling Group has multiple configurations, but not all of them are 'operational' (passing readiness and health checks).
    # Supported values:
    # * 'ALL_OPERATIONAL' - will proceed with DNS changes only when all configurations are operational.
    # * 'SELF_OPERATIONAL' - will proceed with DNS changes if current configuration is operational.
    #
    # Example:
    #  * You have 2 configurations for the same ASG, one tracks 'public ip' and updates Cloudflare DNS,
    #    and another tracks 'private ip' and updates Route53 DNS (private hosted zone).
    #    Presumably configuration for Cloudflare is 'operational', but for Route53 - not.
    #
    #    The Clouflare configuration (healthy) in the example above will:
    #    - if set to 'ALL_OPERATIONAL' - DNS changes will not proceed (Route53 config for same ASG is failing).
    #    - if set to 'SELF_OPERATIONAL' - DNS changes will proceed for this config only (Even though Route53 config for same ASG is failing).
    #
    #    The Route53 configuration (failing) in the example above will:
    #    - if set to 'ALL_OPERATIONAL' - DNS changes will not proceed.
    #    - if set to 'SELF_OPERATIONAL' - DNS changes will not proceed.
    #
    # Default is 'ALL_OPERATIONAL' (all SG DNS configs for same Scaling Groups must be considered 'operational').
    #
    # IMPORTANT:
    # Unless you have a specific use-case, it is recommended to keep the default value. If instance is not considered
    # 'operational' by readiness/health checks, it is likely that it will be terminated by ASG, and thus not be available
    # for DNS resolution. This setting is mostly useful when you have multiple configurations for the same ASG, and you
    # want to proceed with DNS changes even if some of the configurations are failing readiness/health checks, knowing that
    # ASG will not terminate the instance, as your application has a different readiness/health check mechanism in place.
    # Having this setting set to 'SELF_OPERATIONAL' will always complete ASG lifecycle actions with 'CONTINUE' result,
    # regardless of the actual ASG lifecycle hook configuration, to avoid accidental instance termination.
    multiple_config_proceed_mode = optional(string, "SELF_OPERATIONAL")

    # "What If" mode. Defaults to false.
    # When `true`, application will only log what it would do, without making any changes.
    # This setting is respected during reconciliation.
    # It is recommended that you run application in this mode first to see what would happen,
    # and ensure changes proposed are as what you would expected. All lifecycle actions will be submitted with
    # 'CONTINUE' result regardless of the actual ASG lifecycle hook configuration, to avoid accidental instance termination.
    # Readiness and health checks will be performed as usual, however no DNS changes will be made.
    what_if = optional(bool, false)

    # ###
    # DNS SETTINGS
    # ###

    dns_config = object({
      # Name of DNS provider. Default: 'route53'
      # Supported values:
      # * route53
      # * cloudflare
      provider = optional(string, "route53")

      # Describes how to handle DNS record values registration.
      #
      # MULTIVALUE:
      #   Multiple records are created for the same record name.
      # Example:
      #   * domain.com resolves to multiple IP addresses, thus having multiple A records,
      #     (or single A record with multiple IP addresses):
      #     ;; subdomain.example.com A 12.82.13.83, 12.82.13.84, 12.82.14.80
      #
      # SINGLE:
      #   Single value resolved from value_source used from latest Instance as DNS record value.
      # Value is resolved to the most-recently-launched Instance in Scaling Group
      # that is considered 'ready' and 'healthy'.
      # Example:
      #   * domain.com resolves to a single IP address, thus having a single A record with single value:
      #     ;; subdomain.example.com A 12.82.13.83
      #
      # IMPORTANT:
      #   This is only applicable to record types that support multiple values (A, AAAA, SRV, TXT).
      mode = optional(string, "MULTIVALUE")

      # Describes how system should resolve situation when there is no value to set for the DNS record.
      # Typically, this might be the case when scaling down to 0 instances, and there is no value to set.
      # Supported values:
      # * 'KEEP' - when there is no value to set will keep the existing record(s) intact.
      # * 'DELETE' - will delete the DNS record if there is no value to set it to.
      # * 'FIXED:<value>' - will set the DNS record to the specified value if there is no value to set.
      #    Note, that this value will be used as-is, without any interpolation. It's your responsibility
      #    to ensure that the value is correct for the specified record type (if record type is 'A' -
      #    then this value must be a valid IP v4 address).
      empty_mode = optional(string, "KEEP")

      # Value to use as the source for the DNS record. 'ip:v4:private' is default.
      # Supported values:
      # * 'ip:v4:public|private' - will use public/private IP v4 of the instance.
      # * 'ip:v6:public|private' - will use public/private IP v6 of the instance.
      # * 'dns:public|private' - will use public/private DNS name of the instance
      # * 'tag:[<case_comparison_type>]:<tag_name>' - where <tag_name> is the name of the tag to
      #     use as the source for the DNS record value. '<comparison_type>' - Specifies whether to
      #     perform case sensitive or insestitive tag key match. Use 'cs' for case sensitive match.
      #     Use 'ci' or omit parameter for case insensitive match. Default is case insensitive ('ci').
      # IMPORTANT:
      # * If you're using private IPs, resolver function must be on the same network as Instance.
      #   For AWS this means lambda being deployed to the same VPC as the ASG(s) it's runnign check against.
      value_source = optional(string, "ip:v4:private")

      # ID of the 'hosted zone'.
      # For AWS - 'Hosted zone ID' of the domain. You can find this in Route53 console.
      dns_zone_id = string

      # Name of the DNS record. If your domain is 'example.com', and you want to
      # create a DNS record for 'subdomain.example.com', then the value of this field
      # should be 'subdomain'
      record_name = string

      # Time to live for DNS record
      record_ttl = optional(number, 60)

      # Type of DNS record. Default is 'A'
      record_type = optional(string, "A")

      # Priority of the DNS record. Used in SRV only. Default is 0
      srv_priority = optional(number, 0)

      # Weight of the DNS record. Used in SRV only. Default is 0
      srv_weight = optional(number, 0)

      # Port of the DNS record. Used in SRV only. Default is 0.
      srv_port = optional(number, 0)
    })

    # ###
    # READINESS
    # ###

    # Scaling Group specific readiness check. If set, will override global readiness check.
    # This is handy when you have different readiness criteria for different ASGs,
    # or you want to disable readiness check for specific ASG, while having it enabled globally.
    readiness = optional(object({
      # If true, the readiness check will be enabled. Disabled by default.
      enabled = optional(bool, false)
      # Tag key to look for
      tag_key = string
      # Tag value to look for
      tag_value = string
      # Timeout in seconds. If the tag is not set within this time, the lambda will fail.
      timeout_seconds = optional(number, 300)
      # Interval in seconds to check for the tag. Default is 5 seconds.
      interval_seconds = optional(number, 5)
    }), null)

    # ###
    # HEALTHCHECK
    # ###

    # Health check to perform before adding instance to DNS record.
    # Set to null to disable healthcheck overall.
    health_check = optional(object({
      # If true, the health check will be enabled. Disabled by default.
      enabled = optional(bool, false)
      # Value to use as the source for the health check. If not provided, then the value from `dns_config.value_source` will be used.
      # Supported values:
      # * 'ip:v4:public|private' - will use public/private IP v4 of the instance.
      # * 'ip:v6:public|private' - will use public/private IP v6 of the instance.
      # * 'dns:public|private' - will use public/private DNS name of the instance
      # * 'tag:[<case_comparison_type>]:<tag_name>' - where <tag_name> is the name of the tag to
      #     use as the source for the DNS record value. '<comparison_type>' - Specifies whether to
      #     perform case sensitive or insestitive tag key match. Use 'cs' for case sensitive match.
      #     Use 'ci' or omit parameter for case insensitive match. Default is case insensitive ('ci').
      # IMPORTANT:
      # * Ensure that the health check source is accessible from the resolver function (for AWS - from Lambda).
      endpoint_source = optional(string, "ip:v4:private")
      port            = number
      protocol        = string
      timeout_seconds = number
      # Path is required for HTTP/HTTPS health checks
      path = optional(string, "")
    }), null)
  }))

  default = []
}

# IMportant: it is responsibility of your application to set the tag on the instance
# to the value specified here once instance is fully bootstrapped with your application/deploy scripts.
# You can override this behavior on per-ASG basis by specifying `readiness` object in the `records` list.
variable "instance_readiness_default" {
  description = "Default configuration for readiness check. If enabled, SG DNS discovery will not proceed until readiness criteria are met."

  type = object({
    # If true, the readiness check will be enabled. Disabled by default.
    enabled = optional(bool, true)
    # Tag key to look for
    tag_key = string
    # Tag value to look for
    tag_value = string
    # Timeout in seconds. If the tag is not set within this time, the lambda will fail.
    timeout_seconds = optional(number, 300)
    # Interval in seconds to check for the tag. Default is 5 seconds.
    interval_seconds = optional(number, 5)
  })

  default = {
    enabled   = false
    tag_key   = "app:readiness:status"
    tag_value = "ready"
  }
}

variable "reconciliation" {
  description = "Configuration for reconciliation of DNS records that are enabled for Service Discovery."

  type = object({
    # ###
    # RUNTIME BEHAVIOR
    # ###

    # List of valid states for the scaling group to consider for reconciliation. Cloud provider specific.
    # * AWS: https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-lifecycle.html
    scaling_group_valid_states = optional(list(string), ["Pending", "Pending:Wait", "Pending:Proceed", "InService"])

    # Maximum number of concurrent reconciliations. Default is 2.
    # AWS:
    #   In AWS this is maximum concurrency for Amazon SQS event sources. Value must be between 2 and 1000.
    #   Setting this to more than number of ASGs being managed will not have any effect.
    #   Read more: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html#events-sqs-max-concurrency
    max_concurrency = optional(number, 2)

    # ###
    # INFRASTRUCTURE SETTINGS
    # ###

    # When set to `true` will enable running reconciliation on schedule.
    # When set to `false`, will still create event bridge rule to run the lambda on a schedule,
    # but in 'disabled' state. Default is `false`.
    schedule_enabled = optional(bool, false)

    # Interval in minutes between reconciliation runs. Default is 5 minutes.
    # In AWS can't go below once per minute.
    schedule_interval_minutes = optional(number, 5)

    # ###
    # MESSAGE BROKER SETTINGS
    # ###

    # Configuration for message broker integration.
    # Using message broker allows running scaling group reconciliations in parallel,
    # handling single Scaling Group reconciliation per lambda invocation.
    # Supported values:
    # * 'sqs' - AWS SQS
    # * 'internal' - In-Memory message broker (for testing purposes/localhost environments)
    message_broker = optional(string, "sqs")

    # Message broker queue URL.
    # When using SQS, leave blank to use the default queue created by the module.
    message_broker_url = optional(string, "")
  })

  default = {
    what_if                   = false
    max_concurrency           = 2
    schedule_enabled          = true
    schedule_interval_minutes = 5
    message_broker            = "sqs"
    message_broker_url        = ""
  }
}

variable "monitoring" {
  description = "Configures monitoring for the Scaling Group DNS discovery."

  type = object({
    # When set to true - enables metrics for the DNS discovery.
    metrics_enabled = optional(bool, false)
    # Metrics provider
    metrics_provider = optional(string, "cloudwatch")
    # Metrics namespace
    metrics_namespace = optional(string, "sg-dns-discovery")
    # When set to true - enables sending alarms to specified destination. Default is false.
    alarms_enabled = optional(bool, false)
    # SNS topic ARN to send alarms notifications to.
    # This is typically an SNS topic ARN used by your organization.
    # It is your responsibility to ensure that the topic is correctly configured and has necessary permissions.
    # You can obtain the ARN of Lambda role via "lambda_iam_role_arn" output of the module,
    # and attach necessary permissions. Automatic wire-up is omitted on purpose to avoid accidental misconfiguration.
    alarms_notification_destination = optional(string, "")
  })

  default = {
    metrics_enabled   = true
    metrics_provider  = "cloudwatch"
    metrics_namespace = "sg-dns-discovery"
    alarms_enabled    = false
  }

}

# ###
# AWS Specific settings
# ###

variable "lambda_settings" {
  description = "Lambda configuration."

  type = object({
    # Runtime version. Requires Python 3.12 or higher.
    python_runtime = optional(string, "python3.12")
    # Timeout for the lambda function. Default is 15 minutes.
    lifecycle_timeout_seconds = optional(number, 15 * 60)
    # Subnets where the lambda will be deployed.
    # Must be set if the lambda needs to access resources in the VPC - health checks on private IPs.
    subnets         = optional(list(string), [])
    security_groups = optional(list(string), [])
    # IAM - extra policies to attach to the lambda role.
    # It's your responsibility to ensure that the policies are correct and have the necessary permissions.
    extra_iam_policies_arns = optional(list(string), [])
    # Log settings for the lambda runtime
    log_identifier        = optional(string, "sg-dns-discovery")
    log_level             = optional(string, "INFO")
    log_retention_in_days = optional(number, 90)
  })

  default = {
    python_runtime            = "python3.12"
    lifecycle_timeout_seconds = 15 * 60
    subnets                   = []
    security_groups           = []
    extra_iam_policies_arns   = []
    log_identifier            = "sg-dns-discovery"
    log_level                 = "INFO"
    log_retention_in_days     = 90
  }
}

variable "asg_lifecycle_hooks_settings" {
  description = "Configuration for ASG lifecycle hooks."

  type = object({
    # Maximum timeout to allow for the lifecycle hook to respond. Default is 10 minutes.
    # Read more:
    # https://docs.aws.amazon.com/autoscaling/ec2/userguide/lifecycle-hooks.html#lifecycle-hook-considerations
    launch_timeout_seconds = optional(number, 10 * 60)
    # Default result for the lifecycle hook. Allowed values: CONTINUE, ABANDON. Default is 'CONTINUE'.
    launch_default_result = optional(string, "CONTINUE")
    # Timeout for the drain lifecycle hook. Default is 5 minutes.
    drain_timeout_seconds = optional(number, 5 * 60)
    # Default result for the drain lifecycle hook. Default is 'CONTINUE'.
    #
    # Important remarks on hook consequences:
    # * If you set to CONTINUE, the Auto Scaling group can proceed with any remaining actions, such as other lifecycle hooks, before termination.
    # * If you set to ABANDON, the Auto Scaling group terminates the instance immediately.
    # No matter which option you choose, the instance will be terminated.
    #
    # Read more:
    # https://docs.aws.amazon.com/autoscaling/ec2/userguide/adding-lifecycle-hooks.html#adding-lifecycle-hooks-console
    drain_default_result = optional(string, "CONTINUE")
  })

  default = {
    launch_timeout_seconds = 10 * 60
    launch_default_result  = "CONTINUE"
    drain_timeout_seconds  = 2 * 60
    drain_default_result   = "CONTINUE"
  }
}
