import httpx

async def send_request_to_webhook(url: str, timeout: float = 10.0):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            return await client.post(url)
        except httpx.HTTPError:
            return None


