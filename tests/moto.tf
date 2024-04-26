provider "aws" {
  // Moto Endpoints
  // Read more at: https://docs.getmoto.org/en/latest/docs/server_mode.html#example-usage
  region                      = "us-east-1"
  access_key                  = "testing"
  secret_key                  = "testing"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    # Note - port must match $MOTO_PORT environment variable set in the Makefile
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
