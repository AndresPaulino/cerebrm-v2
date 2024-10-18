import base64
import aiohttp
import requests
import datetime
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from app.db.database import get_db

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('schwab_tokens.log', maxBytes=10000000, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Tokens:
    def __init__(self, user_id, app_key, app_secret, callback_url, update_tokens_auto=True):
        if app_key is None:
            logger.error("app_key cannot be None.")
            raise ValueError("app_key cannot be None.")
        if app_secret is None:
            logger.error("app_secret cannot be None.")
            raise ValueError("app_secret cannot be None.")
        if callback_url is None:
            logger.error("callback_url cannot be None.")
            raise ValueError("callback_url cannot be None.")
        if len(app_key) != 32 or len(app_secret) != 16:
            logger.error("App key or app secret invalid length.")
            raise ValueError("App key or app secret invalid length.")
        if not callback_url.startswith("https"):
            logger.error("callback_url must be https.")
            raise ValueError("callback_url must be https.")
        if callback_url.endswith("/"):
            logger.error("callback_url cannot end with '/'.")
            raise ValueError("callback_url cannot end with '/'.")

        self.user_id = user_id
        self._app_key = app_key
        self._app_secret = app_secret
        self._callback_url = callback_url

        self.access_token = None
        self.refresh_token = None
        self.id_token = None
        self._access_token_issued = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        self._refresh_token_issued = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        self._access_token_timeout = 1800
        self._refresh_token_timeout = 7 * 24 * 60 * 60

        self.db = get_db()

        asyncio.create_task(self._initialize_tokens(update_tokens_auto))

    async def _initialize_tokens(self, update_tokens_auto):
        try:
            if not await self._read_tokens():
                if update_tokens_auto:
                    await self.update_refresh_token()
            else:
                if update_tokens_auto:
                    await self.update_tokens()
                logger.info(f"Access token expires in {self._get_token_expiry_string(self._access_token_timeout)}")
                logger.info(f"Refresh token expires in {self._get_token_expiry_string(self._refresh_token_timeout)}")

            if update_tokens_auto:
                asyncio.create_task(self._token_update_checker())
            else:
                logger.warning("Tokens will not be updated automatically.")
        except Exception as e:
            logger.error(f"Error initializing tokens: {str(e)}")

    def _get_token_expiry_string(self, timeout):
        delta = timeout - (datetime.datetime.now(datetime.timezone.utc) - self._access_token_issued).total_seconds()
        return f"{'-' if delta < 0 else ''}{int(abs(delta) / 3600):02}H:{int((abs(delta) % 3600) / 60):02}M:{int((abs(delta) % 60)):02}S"

    async def _token_update_checker(self):
        while True:
            await self.update_tokens()
            await asyncio.sleep(30)

    async def _post_oauth_token(self, grant_type: str, code: str):
        headers = {
            'Authorization': f'Basic {base64.b64encode(bytes(f"{self._app_key}:{self._app_secret}", "utf-8")).decode("utf-8")}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        if grant_type == 'authorization_code':
            data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': self._callback_url
            }
        elif grant_type == 'refresh_token':
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': code
            }
        else:
            logger.error(f"Invalid grant type: {grant_type}")
            raise ValueError("Invalid grant type; options are 'authorization_code' or 'refresh_token'")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post('https://api.schwabapi.com/v1/oauth/token', headers=headers, data=data) as response:
                    return await response.json() if response.status == 200 else None
        except Exception as e:
            logger.error(f"Error in _post_oauth_token: {str(e)}")
            return None

    async def _write_tokens(self, at_issued: datetime, rt_issued: datetime, token_dictionary: dict):
        self.access_token = token_dictionary.get("access_token")
        self.refresh_token = token_dictionary.get("refresh_token")
        self.id_token = token_dictionary.get("id_token")
        self._access_token_issued = at_issued
        self._refresh_token_issued = rt_issued

        try:
            await self.db.execute("""
                UPDATE api_keys 
                SET access_token = :access_token, 
                    refresh_token = :refresh_token, 
                    last_used = :last_used
                WHERE user_id = :user_id AND key_name = 'schwab'
            """, {
                "user_id": self.user_id,
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "last_used": datetime.datetime.now(datetime.UTC)
            })
            logger.info("Tokens successfully written to database")
        except Exception as e:
            logger.error(f"Error writing tokens to database: {str(e)}")

    async def _read_tokens(self):
        try:
            credentials = await self.db.fetch_one(
                "SELECT * FROM api_keys WHERE user_id = :user_id AND key_name = 'schwab'",
                {"user_id": self.user_id}
            )
            if credentials:
                self.access_token = credentials['access_token']
                self.refresh_token = credentials['refresh_token']
                self._access_token_issued = credentials['last_used']
                self._refresh_token_issued = credentials['created_at']
                return True
            return False
        except Exception as e:
            logger.error(f"Error reading tokens from database: {str(e)}")
            return False

    async def update_tokens(self, force=False):
        rt_delta = self._refresh_token_timeout - (datetime.datetime.now(datetime.timezone.utc) - self._refresh_token_issued).total_seconds()
        if rt_delta < 43200:
            logger.warning(f"The refresh token will expire soon! ({self._get_token_expiry_string(rt_delta)} remaining)")

        if (rt_delta < 3600) or force:
            logger.warning("The refresh token has expired!")
            await self.update_refresh_token()
        elif (self._access_token_timeout - (datetime.datetime.now(datetime.timezone.utc) - self._access_token_issued).total_seconds()) < 61:
            logger.info("The access token has expired, updating automatically.")
            await self.update_access_token()

    async def update_access_token(self):
        response = await self._post_oauth_token('refresh_token', self.refresh_token)
        if response:
            at_issued = datetime.datetime.now(datetime.timezone.utc)
            await self._write_tokens(at_issued, self._refresh_token_issued, response)
            logger.info(f"Access token updated: {self._access_token_issued}")
        else:
            logger.error("Could not get new access token, refresh_token probably expired")

    def get_refresh_token_auth_url(self):
        return f'https://api.schwabapi.com/v1/oauth/authorize?client_id={self._app_key}&redirect_uri={self._callback_url}'

    async def update_refresh_token_from_code(self, url_or_code):
        if url_or_code.startswith("https://"):
            code = f"{url_or_code[url_or_code.index('code=') + 5:url_or_code.index('%40')]}@"
        else:
            code = url_or_code

        response = await self._post_oauth_token('authorization_code', code)
        if response:
            now = datetime.datetime.now(datetime.timezone.utc)
            await self._write_tokens(now, now, response)
            logger.info("Refresh and Access tokens updated")
        else:
            logger.error("Could not get new refresh and access tokens")

    async def update_refresh_token(self):
        auth_url = self.get_refresh_token_auth_url()
        logger.info(f"Open to authenticate: {auth_url}")
        # Note: In a web application, you would redirect the user to this URL
        # and handle the callback. For now, we'll use input for demonstration.
        response_url = input("After authorizing, paste the address bar url here: ")
        await self.update_refresh_token_from_code(response_url)