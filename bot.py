import asyncio
import aiohttp
import json
import os
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
USER_CHAT_ID = int(os.environ.get("USER_CHAT_ID", 0))
WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")

LAT = 51.5204
LON = 30.7571

WEATHER_MAP = {
    "Clear": ("Ясно", "☀️"),
    "Clouds": ("Облачно", "☁️"),
    "Rain": ("Дождь", "🌧️"),
    "Drizzle": ("Небольшой дождь", "🌦️"),
    "Thunderstorm": ("Гроза", "🌩️"),
    "Snow": ("Снег", "❄️"),
    "Mist": ("Туман", "🌫️"),
    "Fog": ("Густой туман", "🌫️"),
    "Wind": ("Ветрено", "💨")
}

async def fetch_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    temp = f"{round(data['main']['temp'])}°C"
                    main_condition = data['weather'][0]['main']
                    
                    if data['wind']['speed'] > 8.0:
                        status_text, icon = "Ветрено", "💨"
                    else:
                        status_text, icon = WEATHER_MAP.get(main_condition, (data['weather'][0]['description'].capitalize(), "🌡️"))

                    current_time = datetime.now().strftime("%d.%m %H:%M")

                    return {
                        "city": "Славутич",
                        "date": current_time,
                        "temp": temp,
                        "status": status_text,
                        "icon": icon
                    }
        except Exception as e:
            print(f"Ошибка запроса погоды: {e}")
            return None

async def send_initial_widget(session, html_content, weather_data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendWidget"
    payload = {
        "chat_id": USER_CHAT_ID,
        "html": html_content,
        "chat_data": json.dumps(weather_data)
    }
    async with session.post(url, json=payload) as resp:
        res = await resp.json()
        if res.get("ok"):
            print("Виджет успешно отправлен в Telegram!")
            return res["result"]["message_id"]
        else:
            print("Ошибка отправки виджета:", res)
            return None

async def update_widget_data(session, message_id, weather_data):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageWidgetData"
    payload = {
        "chat_id": USER_CHAT_ID,
        "message_id": message_id,
        "chat_data": json.dumps(weather_data)
    }
    async with session.post(url, json=payload) as resp:
        res = await resp.json()
        if res.get("ok"):
            print(f"[{weather_data['date']}] Виджет обновлен.")
        else:
            print("Ошибка обновления виджета:", res)

async def main():
    with open("widget.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    async with aiohttp.ClientSession() as session:
        weather_data = await fetch_weather()
        if not weather_data:
            print("Не удалось получить данные при старте. Повтор через 10 секунд...")
            await asyncio.sleep(10)
            return await main()

        message_id = await send_initial_widget(session, html_content, weather_data)
        if not message_id:
            return

        while True:
            await asyncio.sleep(900)  # Пауза 15 минут (900 сек)
            new_weather = await fetch_weather()
            if new_weather:
                await update_widget_data(session, message_id, new_weather)

if __name__ == "__main__":
    asyncio.run(main())
