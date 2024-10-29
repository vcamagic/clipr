import logging

from boto3 import client

from app.core.cognito import init_cognito
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if settings.ENVIRONMENT == "local":
    cognito_client = client(
        "cognito-idp",
        region_name=settings.REGION_NAME,
        endpoint_url="http://cognito-local:9229",
    )
else:
    cognito_client = client("cognito-idp", region_name=settings.REGION_NAME)


def main() -> None:
    logger.info("Creating initial cognito resources and users")
    init_cognito(cognito_client)
    logger.info("Initial cognito setup completed")


if __name__ == "__main__":
    main()
