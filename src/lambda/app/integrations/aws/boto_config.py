from botocore.config import Config

# Default boto3 configuration
CONFIG = Config(retries={"max_attempts": 10, "mode": "standard"})
