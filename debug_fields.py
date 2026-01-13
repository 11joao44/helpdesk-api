
import asyncio
from httpx import AsyncClient
from app.core.config import settings

async def main():
    async with AsyncClient() as client:
        response = await client.get(f"{settings['BITRIX_INBOUND_URL']}/crm.deal.userfield.list.json")
        data = response.json()
        target = "UF_CRM_1763985609"
        for field in data["result"]:
            if field["FIELD_NAME"] == target:
                print(f"FIELD: {target}")
                print(f"EDIT_FORM_LABEL: {field.get('EDIT_FORM_LABEL')}")
                print(f"LIST_COLUMN_LABEL: {field.get('LIST_COLUMN_LABEL')}")
                return
        print("Campo não encontrado")

if __name__ == "__main__":
    asyncio.run(main())
