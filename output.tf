output "sns_topic_arn" {
  description = "The SNS topic used for handling SNS lifecycle events"
  value       = aws_sns_topic.asg_dns_discovery.arn
}

output "sqs_reconciliation_queue_arn" {
  description = "The SQS queue used for reconciliation messages"
  value       = aws_sqs_queue.reconciliation_queue.arn
}

output "sqs_reconciliation_queue_url" {
  description = "The SQS queue URL used for reconciliation messages"
  value       = aws_sqs_queue.reconciliation_queue.id

}
output "sqs_reconciliation_queue_deadletter_arn" {
  description = "The SQS deadletter queue used for reconciliation messages"
  value       = aws_sqs_queue.reconciliation_queue_deadletter.arn
}

output "sqs_reconciliation_queue_deadletter_url" {
  description = "The SQS deadletter queue URL used for reconciliation messages"
  value       = aws_sqs_queue.reconciliation_queue_deadletter.id
}

output "dynamodb_dns_discovery_table_arn" {
  description = "The DynamoDB table used for storing DNS records"
  value       = aws_dynamodb_table.dns_discovery_table.arn
}

output "dynamo_db_external_config_item_key_id" {
  description = "Id for the external configuration item in DynamoDB"
  value       = local.dynamo_db_external_config_item_key_id
}

output "lambda_lifecycle_handler_arn" {
  description = "Lambda function for handling lifecycle events"
  value       = aws_lambda_function.dns_discovery_lambda_lifecycle_handler.arn
}

output "lambda_reconciliation_handler_arn" {
  description = "Lambda function for handling reconciliation events"
  value       = aws_lambda_function.dns_discovery_lambda_reconciliation.arn
}

output "lambda_iam_role_arn" {
  description = "IAM role for the lambda function"
  value       = aws_iam_role.dns_discovery_lambda.arn
}

output "lambda_environment_variables" {
  description = "Environment variables used for the lambda function"
  value       = local.lambda_environment_variables
}
