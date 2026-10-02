import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import certifi

async def test():
    uri = "mongodb+srv://vishnuyarra794_db_user:Vishnu123@vishnucluster.7ij6mcj.mongodb.net/?appName=Vishnucluster"
    client2 = AsyncIOMotorClient(uri, tls=True, tlsCAFile=certifi.where())
    try:
        info = await client2.server_info()
        print("SUCCESS TLSCAFILE KWARGS")
    except Exception as e:
        print("ERROR TLSCAFILE KWARGS:", type(e).__name__, e)

if __name__ == "__main__":
    asyncio.run(test())

