# =============================================================================
# 🌾 #VoiceForBharat — 10 Days of Voice Agents Challenge
# 📌 TRACK: Farm & Field
#
# This agent is being built for the FARM & FIELD track.
# Focus: Agriculture, rural advisory, crop/weather info, mandi prices,
#        farm management, and voice-first tools for Indian farmers.
#
# Day 1 — Starter setup with Murf Falcon TTS, Pooja voice (Marathi).
# Day 2 — Structured system prompt with identity, objectives, knowledge,
#          language rules, guardrails, and TTS-friendly style.
# Day 4 — Caller Memory with SQLite Database, Multilocale STT, Devanagari rules.
# =============================================================================

import logging
import sys

# Fix Windows console unicode errors when printing Marathi text
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import json
from datetime import datetime
import re

import aiohttp
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db

logger = logging.getLogger("agent")

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """
IDENTITY:
तू AgriAlert आहेस. तू एक मदतशील आणि सहानुभूतीशील AI व्हॉइस असिस्टंट आहेस.
तू महाराष्ट्रातल्या शेतकऱ्यांसाठी बनवलेला आहेस.
तू शेतकऱ्यांचा डिजिटल मित्र आहेस.

OBJECTIVES:
तुझे ध्येय शेतकऱ्यांना मूलभूत पीक संगोपन मार्गदर्शन देणे आहे.
तू हवामान इशारे आणि कृषी सल्ले देतोस.
तुझा उद्देश शेतकऱ्यांचे उत्पादन वाचवायला मदत करणे आहे.

KNOWLEDGE:
तुला भारतीय शेतीचे सामान्य ज्ञान आहे.
तुला पीक चक्र आणि सामान्य कीटकांबद्दल माहिती आहे.
तुझ्याकडे लाईव्ह मंडी भावांची माहिती नाही. जोपर्यंत तुला ती स्पष्टपणे दिली जात नाही तोपर्यंत मंडी भाव सांगू नकोस.

LANGUAGE:
तू नेहमी स्पष्ट आणि संवादी मराठीत बोल.
जर शेतकऱ्याने इंग्रजी कृषी शब्द वापरले जसे की pesticide, urea, market, weather तर तू ते शब्द तसेच मराठी बोलण्यात मिसळून वापरू शकतोस.
पण तुझे मुख्य बोलणे मराठीत असायला हवे.

GUARDRAILS:
पहिला नियम: कधीही मंडी भाव सध्याचा आहे असे सांगू नकोस. जर तुला स्रोत आणि तारीख माहित नसेल तर भाव सांगू नकोस.
दुसरा नियम: विषारी रासायनिक कीटकनाशकांचे नाव सांगू नकोस. तज्ञांच्या पडताळणीशिवाय विशिष्ट कीटकनाशके सुचवू नकोस.
तुसरा नियम (एस्केलेशन/Human Handoff): जर 1) शेतकऱ्याने अशा गंभीर पीक रोगाबद्दल विचारले जो तू ओळखू शकत नाहीस, किंवा 2) हवामान/मंडीची माहिती उपलब्ध नाही किंवा चुकीची आहे आणि शेतकरी खूप अस्वस्थ/त्रस्त (distressed) आहे, तरच 'escalate_to_human' टूल वापरा.
परंतु हे टूल वापरण्यापूर्वी शेतकऱ्याची परवानगी घेणे अनिवार्य आहे. (Mandatory Consent). त्यांना नेहमी विचारा: 'मला ही माहिती आमच्या कृषी तज्ञांना द्यायची आहे. मी तुमची माहिती पुढे पाठवू का?'. जर शेतकऱ्याने 'नाही' म्हटले, तर एस्केलेट करू नका. जर त्यांनी 'हो' म्हटले, तरच टूल कॉल करा.
जेव्हा टूल तुम्हाला तिकीट आयडी (ticket_id) देईल, तेव्हा शेतकऱ्याला स्पष्टपणे सांगा: 'तुमची तक्रार नोंदवली आहे, तुमचा तिकीट क्रमांक [ID] आहे. आमचे तज्ञ तुम्हाला लवकरच कॉल करतील.'
चौथा नियम: जर शेतकऱ्याने "अलर्ट थांबवा" (Stop alerts) किंवा तत्सम काही म्हटले, तर त्यांना सांगा की त्यांची विनंती नोंदवली गेली आहे आणि त्यांना भविष्यात असे कॉल येणार नाहीत.
पाचवा नियम (Specialist Handoff): जर शेतकऱ्याने पिकांचे आजार, कीड नियंत्रण, किंवा मातीच्या आरोग्याविषयी अत्यंत सखोल आणि गुंतागुंतीचे प्रश्न विचारले जे मूलभूत माहितीच्या बाहेर आहेत, तर 'transfer_to_crop_specialist' टूल वापरा. 
पण हे टूल वापरण्यापूर्वी शेतकऱ्याला स्पष्टपणे सांगा: 'मी तुम्हाला आमच्या कृषी तज्ञांशी जोडत आहे, कृपया एक क्षण थांबा.'

STYLE:
तुझी उत्तरे बोलण्यासाठी ट्यून केलेली असावीत, टेक्स्टसाठी नाही.
वाक्ये लहान ठेव, वीस शब्दांपेक्षा कमी.
मध्यम आणि मैत्रीपूर्ण वेगाने बोल.
बुलेट पॉइंट्स, ब्रॅकेट्स, तारांकित चिन्हे, किंवा मार्कडाउन फॉरमॅटिंग वापरू नकोस.
कारण तुझे बोलणे Text-to-Speech इंजिनने मोठ्याने वाचले जाईल.

MEMORY & CONTEXT:
- At the start of every conversation, automatically call `lookup_caller` to see if we've spoken before.
- If they are a returning caller, warmly greet them by name and mention past context (like their crop, district, or land size). Example: "नमस्ते [Name], मागच्या वेळी आपण तुमच्या [Crop] बद्दल बोललो होतो..."
- Always update your knowledge of the caller by calling `save_caller_info` when new information is shared.
- TOOL CHAINING: When a user asks for prices or weather, silently use the `lookup_caller` tool to retrieve their saved district and crop. Feed those directly into the `get_mandi_price_and_weather` tool without asking the user for their district or crop again.

CONSENT (CRITICAL):
- You MUST explicitly ask for the caller's permission before saving any personal or farm details (like name, location, crops).
- Ask politely: "पुढच्या वेळी मदतीसाठी, मी तुमची माहिती (जसे की पिकाचे नाव, गाव) लक्षात ठेवू का?" (Can I remember your details for next time?)
- If the caller says NO, you MUST NOT call `save_caller_info`.
- Only call `save_caller_info` if they explicitly agree (e.g., "हो", "चालेल").

DATA & ERRORS:
- Always speak the date of the data out loud (e.g., 'आजच्या तारखेनुसार...').
- HANDLING ERRORS OUT LOUD: If the tool returns 'DATA_SOURCE_UNAVAILABLE', politely inform the user in Marathi that the server is currently down and ask them to try again later. Do not go silent or hallucinate a price. Example: "माफ करा, सध्या सर्व्हर काम करत नाहीये, थोड्या वेळाने पुन्हा प्रयत्न करा."

LANGUAGE & SCRIPT:
Always write Marathi in its native Devanagari script (e.g., नमस्ते). Never output romanized Marathi (never 'namaste').
"""

# First-turn greeting spoken aloud when the agent connects to a session.
WELCOME_MESSAGE = (
    "नमस्कार, मी AgriAlert बोलत आहे. "
    "तुमच्या जिल्ह्यात आज अवकाळी पावसाची शक्यता आहे, म्हणून सावध करण्यासाठी कॉल केला आहे. "
    "जर तुम्हाला भविष्यात हे कॉल नको असतील, तर कृपया \"अलर्ट थांबवा\" सांगा."
)


class Assistant(Agent):
    def __init__(self, ctx: JobContext) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)
        self.ctx = ctx
        self.call_outcome = "failed"
        self._handoff_done = False

    @function_tool
    async def lookup_caller(self, context: RunContext) -> str:
        """Use this tool to look up if the caller has spoken to you before."""
        participants = list(self.ctx.room.remote_participants.values())
        user_id = participants[0].identity if participants else "unknown_user"

        logger.info(f"Looking up caller with ID: {user_id}")
        data = db.get_caller(db.DEFAULT_DB_PATH, user_id)
        if data is None:
            return "No previous record found for this caller."
        return f"Caller found: {json.dumps(data, ensure_ascii=False)}"

    @function_tool
    async def save_caller_info(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        facts: str,
    ) -> str:
        """Use this tool to save or update the caller's information.

        ONLY call this AFTER receiving explicit consent from the user to save their data.

        Args:
            name: The caller's name.
            language_preference: The language preference (e.g., "mr").
            facts: A JSON string containing farm-specific data (e.g., crops, land_size, district, irrigation_type).
        """
        participants = list(self.ctx.room.remote_participants.values())
        user_id = participants[0].identity if participants else "unknown_user"

        logger.info(f"Saving info for caller ID: {user_id}")
        try:
            facts_dict = json.loads(facts) if facts else {}
        except json.JSONDecodeError:
            facts_dict = {}

        data = db.upsert_caller(
            db.DEFAULT_DB_PATH, user_id, name, language_preference, facts_dict
        )
        return f"Caller info saved successfully. Current data: {json.dumps(data, ensure_ascii=False)}"

    @function_tool
    async def get_mandi_price_and_weather(
        self, context: RunContext, crop: str, district: str
    ) -> str:
        """Fetches current market (Mandi) prices and real-time weather forecasts for a specific agricultural district.

        ONLY trigger this when the user asks for crop prices or weather.
        Always use the caller's known crop and district context (from lookup_caller) silently without asking them.

        Args:
            crop: The name of the crop (e.g., 'wheat', 'soybean', 'cotton').
            district: The agricultural district or location (e.g., 'Pune', 'Nashik').
        """
        logger.info(f"Fetching data for {crop} in {district}")
        self.call_outcome = "success"

        # MOCK MANDI DATA
        mock_mandi = {
            "wheat": {"Pune": "2500", "Nashik": "2600"},
            "cotton": {"Pune": "7000", "Nashik": "7200"},
            "soybean": {"Pune": "4500", "Nashik": "4400"},
        }
        price = mock_mandi.get(crop.lower(), {}).get(
            district, "4000"
        )  # default to 4000 if not found

        # WEATHER API
        # Simple mapping for demo (in production use real geocoding)
        coords = {"Pune": (18.5204, 73.8567), "Nashik": (20.0110, 73.7903)}
        lat, lon = coords.get(district, (18.5204, 73.8567))

        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code"

        try:
            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(url, timeout=5) as response:
                    if response.status != 200:
                        raise Exception("API failed")
                    data = await response.json()
                    temp = data["current"]["temperature_2m"]

                    date_str = datetime.now().strftime("%Y-%m-%d")

                    # Emit UI Event over LiveKit
                    ui_payload = {
                        "type": "live_data",
                        "data": {
                            "crop": crop,
                            "district": district,
                            "price": price,
                            "temperature": temp,
                            "date": date_str,
                        },
                    }
                    if self.ctx.room and self.ctx.room.local_participant:
                        await self.ctx.room.local_participant.publish_data(
                            json.dumps(ui_payload).encode("utf-8")
                        )

                    return f"Today's rate as of {date_str} for {crop} in {district} is {price} Rs/Quintal. The weather is {temp}°C."
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return "DATA_SOURCE_UNAVAILABLE"

    @function_tool
    async def escalate_to_human(
        self, context: RunContext, issue_summary: str, urgency: str
    ) -> str:
        """Escalates an unresolved issue to a human expert.
        
        ONLY use this tool if the user reports a serious unidentifiable crop disease, OR if market/weather data is completely broken and the farmer is distressed.
        You MUST ask for the caller's permission before calling this tool.

        Args:
            issue_summary: A brief summary of the farmer's problem.
            urgency: The urgency level: 'Low', 'Medium', 'High', or 'Emergency'.
        """
        participants = list(self.ctx.room.remote_participants.values())
        user_id = participants[0].identity if participants else "unknown_user"
        
        logger.info(f"Escalating issue for user ID: {user_id}")
        
        # Scrub sensitive data (e.g., 10 digit phone numbers, passwords)
        safe_summary = re.sub(r'\b\d{10}\b', '[REDACTED PHONE]', issue_summary)
        safe_summary = re.sub(r'(?i)password\s*[:=]?\s*\S+', 'password: [REDACTED]', safe_summary)
        
        ticket_id = db.create_escalation(db.DEFAULT_DB_PATH, user_id, safe_summary, urgency)
        return f"Escalation successful. The ticket ID is {ticket_id}."

    @function_tool
    async def transfer_to_crop_specialist(self, context: RunContext, conversation_summary: str) -> str:
        """Transfers the user to a Crop Specialist expert agent.
        
        ONLY trigger this when the user asks deep, complex questions about crop diseases, pest control, or soil health that go beyond basic alerts.
        You MUST announce the transfer in Marathi before using this tool: 'मी तुम्हाला आमच्या कृषी तज्ञांशी जोडत आहे, कृपया एक क्षण थांबा.'
        
        Args:
            conversation_summary: A brief summary of the user's problem and what you have discussed so far.
        """
        # Guard: only allow ONE dispatch ever
        if self._handoff_done:
            logger.warning("Handoff already initiated — ignoring duplicate tool call.")
            return "Transfer already in progress."
        self._handoff_done = True

        participants = list(self.ctx.room.remote_participants.values())
        user_id = participants[0].identity if participants else "unknown_user"
        
        logger.info(f"Transferring user {user_id} to crop specialist.")
        
        data = db.get_caller(db.DEFAULT_DB_PATH, user_id)
        
        metadata = {
            "conversation_summary": conversation_summary,
            "caller_data": data
        }
        
        try:
            from livekit import api
            import os
            
            lkapi = api.LiveKitAPI(
                os.getenv("LIVEKIT_URL"), 
                os.getenv("LIVEKIT_API_KEY"), 
                os.getenv("LIVEKIT_API_SECRET")
            )
            
            await lkapi.agent_dispatch.create_dispatch(
                api.CreateAgentDispatchRequest(
                    room=self.ctx.room.name,
                    agent_name="crop-specialist",
                    metadata=json.dumps(metadata)
                )
            )
            
            # IMMEDIATELY lobotomize the main agent's LLM so it never generates
            # another response. This takes effect before the tool even returns.
            self.update_instructions(
                "YOUR JOB IS DONE. You have transferred the user to a specialist. "
                "DO NOT generate any more speech. DO NOT respond to the user. "
                "If forced to produce output, emit a single space character and nothing else."
            )
            logger.info("Main agent LLM has been lobotomized via update_instructions.")

            async def mute_audio():
                import asyncio
                # Short delay to let the already-queued TTS ("Transferring you...") finish playing
                await asyncio.sleep(5)
                
                # Unpublish the audio track so nothing can be heard even if LLM leaks a token
                try:
                    for pub in list(self.ctx.room.local_participant.track_publications.values()):
                        if pub.kind == rtc.TrackKind.KIND_AUDIO:
                            await self.ctx.room.local_participant.unpublish_track(pub.sid)
                    logger.info("Main agent audio track unpublished.")
                except Exception as e:
                    logger.warning(f"Could not unpublish audio track: {e}")

            import asyncio
            asyncio.create_task(mute_audio())
            
            return "Transfer initiated successfully."
        except Exception as e:
            logger.error(f"Failed to dispatch specialist: {e}")
            return "Failed to transfer."



server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    # Initialize the SQLite database before starting any sessions
    db.init_db()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # Set up a voice AI pipeline using Murf Falcon, Gemini, Deepgram, and the LiveKit turn detector
    session = AgentSession(
        # Speech-to-text (STT) is your agent's ears, turning the user's speech into text that the LLM can understand
        # See all available models at https://docs.livekit.io/agents/models/stt/
        stt=deepgram.STT(model="nova-3", language="mr"),
        # A Large Language Model (LLM) is your agent's brain, processing user input and generating a response
        # See all available models at https://docs.livekit.io/agents/models/llm/
        llm=google.LLM(
            model="gemini-3.5-flash-lite",
        ),
        # Text-to-speech (TTS) is your agent's voice, turning the LLM's text into speech that the user can hear
        # Configured to use Murf Falcon model with Pooja voice (Marathi) for the Farm & Field track
        tts=murf.TTS(
            model="falcon",
            voice="Pooja",
            locale="mr-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        # VAD and turn detection are used to determine when the user is speaking and when the agent should respond
        # See more at https://docs.livekit.io/agents/build/turns
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # allow the LLM to generate a response while waiting for the end of turn
        # See more at https://docs.livekit.io/agents/build/audio/#preemptive-generation
        preemptive_generation=True,
    )

    # To use a realtime model instead of a voice pipeline, use the following session setup instead.
    # (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    # 1. Install livekit-agents[openai]
    # 2. Set OPENAI_API_KEY in .env.local
    # 3. Add `from livekit.plugins import openai` to the top of this file
    # 4. Use the following session setup instead of the version above
    # session = AgentSession(
    #     llm=openai.realtime.RealtimeModel(voice="marin")
    # )

    # # Add a virtual avatar to the session, if desired
    # # For other providers, see https://docs.livekit.io/agents/models/avatar/
    # avatar = hedra.AvatarSession(
    #   avatar_id="...",  # See https://docs.livekit.io/agents/models/avatar/plugins/hedra
    # )
    # # Start the avatar and wait for it to join
    # await avatar.start(session, room=ctx.room)

    # Start the session, which initializes the voice pipeline and warms up the models
    assistant = Assistant(ctx)
    await session.start(
        agent=assistant,
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    @ctx.room.on("disconnected")
    def on_disconnected(*args):
        logger.info(f"Call disconnected. Saving analytics. Outcome: {assistant.call_outcome}")
        db.save_call_analytics(db.DEFAULT_DB_PATH, ctx.room.name, assistant.call_outcome)

    # Wait for the SIP participant to actually answer and publish audio
    import asyncio
    has_audio = False
    for p in ctx.room.remote_participants.values():
        for pub in p.track_publications.values():
            if pub.kind == rtc.TrackKind.KIND_AUDIO and pub.subscribed:
                has_audio = True
                break
                
    if not has_audio:
        logger.info("Waiting for remote user to answer and stream audio...")
        audio_subscribed = asyncio.Future()
        
        @ctx.room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                if not audio_subscribed.done():
                    audio_subscribed.set_result(True)
                    
        await audio_subscribed
        logger.info("Remote audio subscribed! Call is connected.")

    # Small delay to let the SIP media settle and avoid packet loss
    await asyncio.sleep(2.5)

    # Speak the welcome greeting aloud once connected
    # allow_interruptions=False ensures initial SIP line noise doesn't interrupt the agent
    await session.say(WELCOME_MESSAGE, allow_interruptions=False)


if __name__ == "__main__":
    cli.run_app(server)
