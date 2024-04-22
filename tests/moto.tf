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

    lambda      = "http://moto-server:5000"
    dynamodb    = "http://moto-server:5000"
    sns         = "http://moto-server:5000"
    sqs         = "http://moto-server:5000"
    route53     = "http://moto-server:5000"
    cloudwatch  = "http://moto-server:5000"
    eventbridge = "http://moto-server:5000"
    sts         = "http://moto-server:5000"
    iam         = "http://moto-server:5000"
    ec2         = "http://moto-server:5000"
    autoscaling = "http://moto-server:5000"
    logs        = "http://moto-server:5000"
  }
}
