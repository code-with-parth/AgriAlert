import asyncio
import os
import sys
import logging
from dotenv import load_dotenv
from livekit import api
from livekit.api import LiveKitAPI

load_dotenv(".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbound_alert")

async def trigger_call(lkapi: LiveKitAPI, phone_number: str, max_retries: int = 1):
    trunk_id = os.getenv("SIP_TRUNK_ID")
    if not trunk_id:
        logger.error("SIP_TRUNK_ID is not set in .env.local")
        return
        
    for attempt in range(max_retries + 1):
        logger.info(f"Initiating outbound call to {phone_number} (Attempt {attempt + 1})")
        try:
            # Note: Depending on the SDK version, AMD (Answering Machine Detection) can be enabled.
            import re
            safe_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', phone_number)
            # Using standard fields for CreateSIPParticipantRequest
            request = api.CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=phone_number,
                room_name="agrialert-room",
                participant_identity=f"farmer_{safe_id}",
                play_ringtone=True
            )
            
            # Initiate the SIP participant call
            participant_info = await lkapi.sip.create_sip_participant(request)
            logger.info(f"SIP Participant created: {participant_info}")
            
            # If the call is dispatched successfully without immediate error, break out.
            # (LiveKit will raise an exception on immediate SIP errors like 404, 486 Busy, etc.)
            logger.info("Call successfully dispatched to SIP trunk.")
            break
            
        except Exception as e:
            err_msg = str(e).lower()
            logger.warning(f"Call attempt failed: {e}")
            
            # Check for common SIP failure reasons (e.g. USER_UNAVAILABLE, USER_REJECTED)
            if "busy" in err_msg or "unavailable" in err_msg or "timeout" in err_msg or "no answer" in err_msg or "rejected" in err_msg:
                if attempt < max_retries:
                    logger.info("Status: Busy/No Answer. Waiting 2 minutes before retrying...")
                    await asyncio.sleep(120)  # Wait 2 minutes
                else:
                    logger.error("Max retries reached. Could not complete the call.")
            else:
                # Other generic error, do not retry
                logger.error("Unhandled error occurred. Aborting.")
                break

async def main():
    phone_number = os.getenv("PHONE_NUMBER_TO_CALL")
    if not phone_number:
        logger.error("PHONE_NUMBER_TO_CALL is not set in .env.local. Please set it to your mobile number (e.g., +919876543210).")
        sys.exit(1)
        
    lkapi = LiveKitAPI(
        os.getenv("LIVEKIT_URL"),
        os.getenv("LIVEKIT_API_KEY"),
        os.getenv("LIVEKIT_API_SECRET")
    )
    
    try:
        await trigger_call(lkapi, phone_number)
    finally:
        await lkapi.aclose()

if __name__ == "__main__":
    asyncio.run(main())
