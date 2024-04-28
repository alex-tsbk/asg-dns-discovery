# Making sure ARNs look decent
mock_resource "aws_iam_role" {
  defaults = {
    arn = "arn:aws:iam::123456789012:role/test"
  }
}

mock_resource "aws_iam_policy" {
  defaults = {
    arn = "arn:aws:iam::123456789012:policy/test"
  }
}

mock_resource "aws_sns_topic" {
  defaults = {
    arn = "arn:aws:sns:us-east-1:123456789012:my-sns-topic"
  }
}

mock_resource "aws_lambda_function" {
  defaults = {
    arn = "arn:aws:lambda:us-east-1:123456789012:function:sg-dns-discovery"
  }
}

mock_resource "aws_cloudwatch_event_rule" {
  defaults = {
    arn = "arn:aws:events:us-east-1:123456789012:rule/sg-dns-discovery"
  }
}
