provider "aws" {
  region = "us-east-1"
}

variable "gemini_api_key" {
  description = "Gemini API Key"
  type        = string
  sensitive   = true
}

resource "aws_secretsmanager_secret" "gemini_api_key" {
  name        = "gemini-api-key"
  description = "Gemini API key for cicd-ai-copilot"
}

resource "aws_secretsmanager_secret_version" "gemini_api_key_value" {
  secret_id     = aws_secretsmanager_secret.gemini_api_key.id
  secret_string = jsonencode({
    GEMINI_API_KEY = var.gemini_api_key
  })
}

resource "aws_lambda_function" "cicd-ai-copilot" {
  function_name = "cicd-ai-copilot"
  filename      = "lambda.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.lambda_role.arn
  timeout       = 60

  depends_on = [
    aws_secretsmanager_secret_version.gemini_api_key_value,
    aws_iam_role_policy_attachment.lambda_secrets_attach,
    aws_iam_role_policy_attachment.basic_logs
  ]
}