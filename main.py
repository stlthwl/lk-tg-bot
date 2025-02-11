from fastapi import FastAPI, HTTPException

import bot
from bot import start_bot
from api import User

app = FastAPI()
user_service = User()


@app.on_event("startup")
async def startup_event():
    start_bot()


@app.get("/")
async def read_root():
    return {"message": "server is running"}


@app.post("/users/{user_id}")
async def get_user_by_id(user_id: int):
    try:
        user_data = await user_service.get_user_by_id(user_id)
        return user_data
    except Exception as e:
        print(e)
        return {"message": "error when getting user data"}


@app.get("/register/telegram/{telegram_id}/{token}")
async def register_telegram(telegram_id: int, token: str):
    try:
        await user_service.confirm_profile(telegram_id, token)
        await bot_send_message(telegram_id, "Профиль успешно подтвержден")
        return {
            "message": f"telegram_id {telegram_id} is being processed!"
        }
    except Exception as e:
        print(e)
        return {"message": "registration error"}


@app.post('bot/send_message')
async def bot_send_message(telegram_id: int, message: str):
    try:
        await bot.send_msg(telegram_id, message)
        return {"message": "message sent successfully"}
    except Exception as e:
        print(e)
        return {"message": "failed to send message"}

