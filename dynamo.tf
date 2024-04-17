resource "aws_dynamodb_table" "dns_discovery_table" {
  name         = local.resource_prefix
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = local.tags
}

resource "aws_dynamodb_table_item" "dns_discovery_table" {
  table_name = aws_dynamodb_table.dns_discovery_table.name
  hash_key   = aws_dynamodb_table.dns_discovery_table.hash_key

  item = <<ITEM
{
  "id": {"S": "${local.dynamo_db_iac_config_item_key_id}"},
  "config": {"S": "${base64encode(jsonencode(var.records))}" }
}
ITEM
}
