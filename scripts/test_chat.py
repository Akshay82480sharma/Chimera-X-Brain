import httpx
import asyncio

async def main():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post("http://localhost:8000/v1/chat/completions", json={
                "messages": [{"role": "user", "content": "hey"}],
                "stream": True,
                "model": "auto"
            })
            print(f"Status: {res.status_code}")
            print(f"Response: {res.text}")
        except Exception as e:
            print(f"Exception repr: {repr(e)}")

if __name__ == "__main__":
    asyncio.run(main())
