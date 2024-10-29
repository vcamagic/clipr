import logging
import os

from boto3.exceptions import Boto3Error
from mypy_boto3_cognito_idp import CognitoIdentityProviderClient

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMP_PASSWORD = "G#7x!Kqv2P%Zj9&LnB"
PERMANENT_PASSWORD = "Bb7x!Kqv2P%Zj9&LnB"

def create_user_pool():
    



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

        cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=settings.EMAIL_TEST_USER,
            UserAttributes=[
                {"Name": "email_verified", "Value": "true"},
                {"Name": "email", "Value": settings.EMAIL_TEST_USER},
            ],
            MessageAction="SUPPRESS",
            TemporaryPassword=TEMP_PASSWORD
        )
        response = cognito_client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            ClientId=client_id,
            AuthParameters={"USERNAME": settings.EMAIL_TEST_USER, "PASSWORD": TEMP_PASSWORD},
        )
        session = response["Session"]
        response = cognito_client.respond_to_auth_challenge(
            ClientId=client_id,
            ChallengeName="NEW_PASSWORD_REQUIRED",
            Session=session,
            ChallengeResponses={
                "USERNAME": settings.EMAIL_TEST_USER,
                "NEW_PASSWORD": PERMANENT_PASSWORD,
            },
        )
        logger.info(f"User confirmed: {response}")
    except Boto3Error as e:
        logger.error(f"Failed to create user pool: {e}")
