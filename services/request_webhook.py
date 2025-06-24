import httpx

async def send_request_to_webhook(url:str):
    async with httpx.AsyncClient() as client:
        await client.post(url)


