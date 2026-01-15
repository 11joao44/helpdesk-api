
import asyncio
import httpx
from app.core.config import settings

async def test_bitrix_deal_get():
    # settings behaves like a dict or has .get()
    url = settings.get("BITRIX_INBOUND_URL")
    if not url:
        print("BITRIX_INBOUND_URL not found")
        # Try finding it in environment just in case
        import os
        url = os.environ.get("BITRIX_INBOUND_URL")
        if not url:
             print("Still not found.")
             return

    deal_id = 8089 # The ID from the log
    
    print(f"Testing with URL base: {url}")

    async with httpx.AsyncClient() as client:
        # Test 1: Lowercase id
        print("\n--- Test 1: lowercase 'id' ---")
        try:
            resp = await client.get(f"{url}/crm.deal.get.json", params={"id": deal_id})
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

        # Test 2: Uppercase ID
        print("\n--- Test 2: uppercase 'ID' ---")
        try:
            resp = await client.get(f"{url}/crm.deal.get.json", params={"ID": deal_id})
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_bitrix_deal_get())
