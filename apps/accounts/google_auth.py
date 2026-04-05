import logging
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

def verify_google_token(token: str) -> dict:
    """
    Verifies a Google ID token or an access token and returns the decoded payload.
    Raises ValueError if the token is invalid or expired.
    """
    try:
        # Check if token is a JWT (has 3 parts separated by dots)
        if len(token.split('.')) == 3:
            # Specify the CLIENT_ID of the app that accesses the backend:
            client_id = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)
            
            if not client_id:
                logger.error("GOOGLE_OAUTH2_CLIENT_ID is not set in Django settings")
                raise ValueError(_("Server authentication configuration error"))

            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                client_id
            )
            return idinfo
        else:
            # It's likely an access_token, verify via userinfo endpoint
            import requests as req
            response = req.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers={'Authorization': f'Bearer {token}'}
            )
            if response.status_code != 200:
                logger.warning(f"Failed to verify access_token: {response.text}")
                raise ValueError(_("Invalid Google token"))
                
            idinfo = response.json()
            # Ensure it has email
            if 'email' not in idinfo:
                raise ValueError(_("Email not provided by Google"))
                
            return idinfo


        # If auth request is from a G Suite domain:
        # if idinfo['hd'] != GSUITE_DOMAIN_NAME:
        #     raise ValueError('Wrong hosted domain.')

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        return idinfo
    except ValueError as e:
        # Invalid token
        logger.warning(f"Invalid Google token: {str(e)}")
        raise ValueError(_("Invalid Google token"))
    except Exception as e:
        # Other errors (e.g., network issues with Google verifier)
        logger.error(f"Error verifying Google token: {str(e)}")
        raise ValueError(_("Failed to verify Google token"))
