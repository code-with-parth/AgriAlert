import asyncio
import os
import sys
import re

# Ensure the script can import from backend's virtual env
backend_dir = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.append(backend_dir)
env_path = os.path.join(backend_dir, '.env.local')

try:
    from dotenv import load_dotenv
    from livekit import api
except ImportError:
    print("Please run this script using the backend virtual environment:")
    print("cd backend && uv run python ../scripts/setup_outbound_trunk.py")
    sys.exit(1)

load_dotenv(env_path)

async def main():
    url = os.getenv("LIVEKIT_URL")
    key = os.getenv("LIVEKIT_API_KEY")
    secret = os.getenv("LIVEKIT_API_SECRET")
    
    if not url or not key or not secret:
        print("Error: Missing LiveKit credentials (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET) in backend/.env.local")
        sys.exit(1)
        
    print(f"Connecting to LiveKit API at {url}...")
    lkapi = api.LiveKitAPI(url, key, secret)
    
    try:
        # Check existing trunks
        req = api.ListSIPOutboundTrunkRequest()
        res = await lkapi.sip.list_sip_outbound_trunk(req)
        
        trunks = res.items
        
        if not trunks:
            print("No SIP Outbound Trunks found in your LiveKit project.")
            print("Attempting to create a new SIP Trunk using Twilio credentials...")
            
            tw_sid = os.getenv("TWILIO_ACCOUNT_SID")
            tw_token = os.getenv("TWILIO_AUTH_TOKEN")
            tw_number = os.getenv("TWILIO_PHONE_NUMBER")
            
            if not tw_sid or not tw_token or not tw_number:
                print("\nError: Missing Twilio credentials in backend/.env.local.")
                print("You can either:")
                print("1. Add TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER to .env.local")
                print("2. Create the trunk manually in the LiveKit Dashboard (https://cloud.livekit.io/) under 'SIP'")
                sys.exit(1)
                
            print("\nTo use Twilio for outbound SIP, you must have a Termination SIP Domain created in your Twilio Console.")
            print("For example: 'agrialert.sip.twilio.com' or 'agrialert.pstn.twilio.com'")
            sip_domain = input("Please enter your exact Twilio SIP Domain: ").strip()
            
            if not sip_domain:
                print("SIP Domain is required. Exiting.")
                sys.exit(1)
                
            # Construct a trunk info object
            trunk_info = api.SIPOutboundTrunkInfo(
                name="AgriAlert Twilio Trunk",
                address=sip_domain,
                numbers=[tw_number],
                auth_username=tw_sid,
                auth_password=tw_token
            )
            
            create_req = api.CreateSIPOutboundTrunkRequest(trunk=trunk_info)
            new_trunk = await lkapi.sip.create_sip_outbound_trunk(create_req)
            
            print(f"\nCreated new SIP Trunk! ID: {new_trunk.sip_trunk_id}")
            trunk_id = new_trunk.sip_trunk_id
        else:
            print("\nFound existing SIP Outbound Trunks:")
            for t in trunks:
                print(f" - Name: {t.name}, ID: {t.sip_trunk_id}, Numbers: {t.numbers}")
            
            trunk_id = trunks[0].sip_trunk_id
            print(f"\nUsing Trunk ID: {trunk_id}")
            
        # Update .env.local with the SIP_TRUNK_ID
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        new_content = re.sub(r'SIP_TRUNK_ID=.*', f'SIP_TRUNK_ID={trunk_id}', content)
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"\nSuccessfully updated backend/.env.local with SIP_TRUNK_ID={trunk_id}")
            
    except Exception as e:
        print(f"\nError interacting with LiveKit API: {e}")
        print("\nTo manually get your SIP Trunk ID:")
        print("1. Go to https://cloud.livekit.io/")
        print("2. Select your project")
        print("3. Click on 'SIP' in the left menu")
        print("4. Copy the ID of your Outbound Trunk (starts with 'ST_...')")
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())
