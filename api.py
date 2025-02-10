import os
import httpx
from fastapi import HTTPException
from dotenv import load_dotenv


load_dotenv()


async def send_post(payload):
    headers = {
        "x-api-key": str(os.getenv("API_KEY")),
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(str(os.getenv("API_URL")), json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)


class User:
    def __init__(self):
        self.user_data = None
        self.response = None

    async def get_user_by_id(self, user_id: int):
        payload = {
            "data": {
                "method": "get_user_by_id",
                "user_id": user_id
            }
        }

        self.user_data = await send_post(payload)
        return self.user_data

    async def get_user_by_telegram_id(self, telegram_id):
        payload = {
            "data": {
                "method": "get_user_by_telegram_id",
                "telegram_id": telegram_id
            }
        }

        self.user_data = await send_post(payload)
        return self.user_data

    async def get_user_by_email(self, email):
        payload = {
            "data": {
                "method": "get_user_by_email",
                "email": email
            }
        }

        self.user_data = await send_post(payload)
        return self.user_data

    async def get_user_by_token(self, token):
        payload = {
            "data": {
                "method": "get_user_by_token",
                "token": token
            }
        }

        self.user_data = await send_post(payload)
        return self.user_data

    async def send_confirm_email(self, telegram_id, email):
        payload = {
            "data": {
                "method": "send_confirm_email",
                "telegram_id": telegram_id,
                "email": email
            }
        }

        self.response = await send_post(payload)
        return self.response

    async def confirm_profile(self, telegram_id, token):
        payload = {
            "data": {
                "method": "confirm_profile",
                "telegram_id": telegram_id,
                "token": token
            }
        }

        self.response = await send_post(payload)
        return self.response


class Appeals:
    def __init__(self):
        self.appeals = None
        self.response = None

    async def get_user_appeals(self, user_id: int):
        payload = {
            "data": {
                "method": "get_user_appeals",
                "user_id": user_id
            }
        }

        self.appeals = await send_post(payload)
        return self.appeals

    async def get_appeal_configuration(self, user_id):
        payload = {
            "data": {
                "method": "get_appeal_configuration",
                "user_id": user_id
            }
        }

        self.response = await send_post(payload)
        return self.response

    async def create_new_appeal(self, data):
        payload = {
            "data": data
        }

        self.response = await send_post(payload)
        return self.response

    async def execute_appeal_command(self, command_id, appeal_id):
        payload = {
            "data": {
                "method": "execute_appeal_command",
                "command_id": command_id,
                "appeal_id": appeal_id
            }
        }

        self.response = await send_post(payload)
        return self.response

    async def call_procedure(self, procedure):
        payload = {
            "data": {
                "method": "call_procedure",
                "procedure": procedure
            }
        }

        self.response = await send_post(payload)
        return self.response


class Events:
    def __init__(self):
        self.response = None

    async def create_event(self, clarification: dict):
        payload = {
            "data": {
                "method": "create_event",
                "clarification": clarification
            }
        }

        self.response = await send_post(payload)
        return self.response



