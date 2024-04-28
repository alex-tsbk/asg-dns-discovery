mock_data "aws_availability_zones" {
  defaults = {
    names = ["us-east-1a", "us-east-1b", "us-east-1c"]
  }
}

mock_data "aws_caller_identity" {
  defaults = {
    account_id = "123456789012"
  }
}

mock_data "aws_region" {
  defaults = {
    name = "us-east-1"
  }
}

mock_data "aws_partition" {
  defaults = {
    partition  = "aws"
    dns_suffix = "amazonaws.com"
  }
}

# Addressing terraform test bug?:
# Error: "policy" contains an invalid JSON: invalid character 'v' looking for beginning of value
# Notes: `terraform test` can't evaluate dynamic policy document syntax
mock_data "aws_iam_policy_document" {
  defaults = {
    json = <<EOF
        {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Effect": "Allow",
              "Principal": {
                "Service": "*"
              },
              "Action": "sts:AssumeRole"
            }
          ]
        }
      EOF
  }
}
