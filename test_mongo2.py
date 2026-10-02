import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test():
    uri = "mongodb+srv://vishnuyarra794_db_user:Vishnu123@vishnucluster.7ij6mcj.mongodb.net/?appName=Vishnucluster"
    client = AsyncIOMotorClient(uri)
    try:
        info = await client.server_info()
        print("SUCCESS NO KWARGS")
    except Exception as e:
        print("ERROR NO KWARGS:", type(e).__name__)
    
    client2 = AsyncIOMotorClient(uri, tls=True, tlsCAFile=certifi.where())
    try:
        info = await client2.server_info()
        print("SUCCESS TLS KWARGS")
    except Exception as e:
        print("ERROR TLS KWARGS:", type(e).__name__)

if __name__ == "__main__":
    asyncio.run(test())

