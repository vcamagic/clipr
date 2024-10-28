import logging
import os

from boto3.exceptions import Boto3Error
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_cognito(cognito_client: CognitoIdentityProviderClient):
    response = cognito_client.list_user_pools(MaxResults=1)

    if len(response["UserPools"]) > 0:
        logger.info("User pool already created.")
        return

    try:
        user_pool_response = cognito_client.create_user_pool(
            PoolName=settings.USER_POOL_NAME,
            AutoVerifiedAttributes=["email"],
            Schema=[
                {
                    "Name": "email",
                    "AttributeDataType": "String",
                    "Mutable": False,
                    "Required": True,
                },
            ],
            Policies={
                "PasswordPolicy": {
                    "MinimumLength": 8,
                    "RequireUppercase": True,
                    "RequireLowercase": True,
                    "RequireNumbers": True,
                    "RequireSymbols": False,
                }
            },
            AdminCreateUserConfig={"AllowAdminCreateUserOnly": False},
        )
        user_pool_id = user_pool_response.get("UserPool", {}).get("Id", "")
        os.environ["USER_POOL_ID"] = user_pool_id
        logger.info(f"Created user pool: {user_pool_id}")

        response = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=settings.USER_POOL_CLIENT_NAME,
            ExplicitAuthFlows=[
                "ALLOW_ADMIN_USER_PASSWORD_AUTH",
                "ALLOW_CUSTOM_AUTH",
                "ALLOW_USER_SRP_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH",
                "ALLOW_USER_PASSWORD_AUTH",
            ],
            RefreshTokenValidity=365,
            AccessTokenValidity=1,
            AuthSessionValidity=15,
            TokenValidityUnits={
                "AccessToken": "days",
                "IdToken": "days",
                "RefreshToken": "days",
            },
        )
        client_id = response.get("UserPoolClient", {}).get("ClientId", "")
        os.environ["USER_POOL_CLIENT_ID"] = client_id
    except Boto3Error as e:
        logger.error(f"Failed to create user pool: {e}")
