resource "aws_dynamodb_table" "dns_discovery_state_lock_table" {
  name         = "${local.resource_prefix}-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "resource_id"

  attribute {
    name = "resource_id"
    type = "S"
  }

  tags = local.tags
}

resource "aws_dynamodb_table_item" "dns_discovery_state_lock_table" {
  table_name = aws_dynamodb_table.dns_discovery_state_lock_table.name
  hash_key   = aws_dynamodb_table.dns_discovery_state_lock_table.hash_key

  item = <<ITEM
{
  "resource_id": {"S": "${local.dynamo_db_iac_config_item_key_id}"},
  "config": {"S": "${base64encode(jsonencode(var.records))}" }
}
ITEM
}
