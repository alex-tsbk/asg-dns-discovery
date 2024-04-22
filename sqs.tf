resource "aws_sqs_queue" "reconciliation_queue" {
  name = "${local.resource_prefix}.fifo"

  # Deliver immediately
  delay_seconds             = 0
  receive_wait_time_seconds = 0

  # Ensure that messages are processed in the order they are received
  fifo_queue = true

  # Retain messages just enough to allow for reconciliation to pick up the message
  message_retention_seconds = var.reconciliation.schedule_interval_minutes * 60
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.reconciliation_queue_deadletter.arn
    maxReceiveCount     = 4
  })

  tags = local.tags
}

resource "aws_sqs_queue" "reconciliation_queue_deadletter" {
  name = "${local.resource_prefix}-dlq.fifo"

  fifo_queue = true

  tags = local.tags
}

resource "aws_lambda_event_source_mapping" "reconciliation_lifecycle_handler" {
  enabled          = true
  event_source_arn = aws_sqs_queue.reconciliation_queue.arn
  function_name    = aws_lambda_function.dns_discovery_lambda_reconciliation.arn
  # It's required that we reconcile one Scaling Group at a time
  batch_size = 1

  scaling_config {
    # Ensures that number of reconciliations does not exceed the maximum concurrency specified
    maximum_concurrency = var.reconciliation.max_concurrency <= 2 ? 2 : var.reconciliation.max_concurrency
  }
}
