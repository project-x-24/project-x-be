import src.config as config

from google.oauth2 import service_account

scopes = ["https://www.googleapis.com/auth/cloud-platform"]
sa_credentials = service_account.Credentials.from_service_account_file(
    config.GOOGLE_APPLICATION_CREDENTIALS, scopes=scopes
)
# sa_credentials = None
