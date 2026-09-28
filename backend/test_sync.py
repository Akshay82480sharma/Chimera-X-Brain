import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://127.0.0.1:8000/v1/models/sync")
            print("Status:", res.status_code)
            print("Response:", res.text)
        except Exception as e:
            print("Error:", str(e))

asyncio.run(main())
