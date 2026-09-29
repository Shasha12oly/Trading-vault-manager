"""
Quick test to verify Discord token works
"""
import discord
import asyncio

# Test token
TOKEN = "MTU1NDA1NTIxMjE3NDY3MTg4Mg.G4pmlm.wxyAeXZ_Ew3XN4eYMdhkxQBGYSbMq5hO_YZfa8"

async def test_token():
    try:
        # Create a client with required intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"✅ Token is valid! Logged in as {client.user}")
            print(f"Bot ID: {client.user.id}")
            print(f"Bot Name: {client.user.name}")
            await client.close()
        
        await client.start(TOKEN)
    except discord.LoginFailure as e:
        print(f"❌ Token is invalid: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_token())
