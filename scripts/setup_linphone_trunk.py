import asyncio
import os
import sys
import re

backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_dir)
env_path = os.path.join(backend_dir, '.env.local')

from dotenv import load_dotenv
from livekit import api

load_dotenv(env_path)

async def main():
    url = os.getenv("LIVEKIT_URL")
    key = os.getenv("LIVEKIT_API_KEY")
    secret = os.getenv("LIVEKIT_API_SECRET")
    
    lkapi = api.LiveKitAPI(url, key, secret)
    
    try:
        trunk_info = api.SIPOutboundTrunkInfo(
            name="Linphone Trunk",
            address="sip.linphone.org",
            numbers=["parthdeshpande"]
        )
        create_req = api.CreateSIPOutboundTrunkRequest(trunk=trunk_info)
        
        # Use create_outbound_trunk per latest SDK deprecation warnings
        try:
            new_trunk = await lkapi.sip.create_outbound_trunk(create_req)
        except AttributeError:
            new_trunk = await lkapi.sip.create_sip_outbound_trunk(create_req)
            
        trunk_id = new_trunk.sip_trunk_id
        print(f"Created Linphone Trunk: {trunk_id}")
        
        # Update .env.local
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = re.sub(r'SIP_TRUNK_ID=.*', f'SIP_TRUNK_ID={trunk_id}', content)
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())
