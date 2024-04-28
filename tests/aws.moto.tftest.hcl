# IMPORTANT: This file is used to configure the AWS provider to use Moto endpoints
# for testing. MOTO must be running in server mode for this to work. The endpoints
# must match the $MOTO_PORT environment variable set in the Makefile.
# Read more at: https://docs.getmoto.org/en/latest/docs/server_mode.html#example-usage

provider "aws" {
  region                      = "us-east-1"
  access_key                  = "testing"
  secret_key                  = "testing"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    # Note - port must match $MOTO_PORT environment variable set in the Makefile
    # List of all available endpoints:
    # https://registry.terraform.io/providers/hashicorp/aws/latest/docs/guides/custom-service-endpoints#available-endpoint-customizations
    lambda      = "http://localhost:5000"
    dynamodb    = "http://localhost:5000"
    sns         = "http://localhost:5000"
    sqs         = "http://localhost:5000"
    route53     = "http://localhost:5000"
    cloudwatch  = "http://localhost:5000"
    eventbridge = "http://localhost:5000"
    sts         = "http://localhost:5000"
    iam         = "http://localhost:5000"
    ec2         = "http://localhost:5000"
    autoscaling = "http://localhost:5000"
    logs        = "http://localhost:5000"
  }
}
