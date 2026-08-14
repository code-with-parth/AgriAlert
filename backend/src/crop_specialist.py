import logging
import sys

# Fix Windows console unicode errors when printing Marathi text
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import json
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    room_io,
    tokenize,
)
from livekit.plugins import deepgram, google, murf, noise_cancellation, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

import db

logger = logging.getLogger("crop-specialist")

load_dotenv(".env.local")

# System prompt for crop specialist
SYSTEM_PROMPT = """
IDENTITY:
तू एक तज्ञ कृषीशास्त्रज्ञ (Crop Specialist Agronomist) आहेस. 
तू पिकांचे आजार आणि मातीचे आरोग्य या विषयातील तज्ञ आहेस.
तू शेतकऱ्यांशी अतिशय नम्रपणे आणि तज्ञ म्हणून बोलतोस.

OBJECTIVES:
तुझे मुख्य ध्येय शेतकऱ्यांना पिकांचे आजार, कीड नियंत्रण आणि मातीच्या आरोग्याविषयी सखोल आणि अचूक माहिती देणे आहे.

LANGUAGE:
तू नेहमी स्पष्ट आणि संवादी मराठीत (Devanagari script) बोल. 
इंग्रजी तांत्रिक शब्द (जसे की pesticide, NPK, fungus) तू मराठी वाक्यांमध्ये वापरू शकतोस.

GUARDRAILS:
- फक्त पिकांचे आजार, कीड आणि माती यावरच बोला. 
- जर शेतकऱ्याने हवामान किंवा मंडी भावाबद्दल विचारले, तर नम्रपणे सांगा की तुम्ही फक्त पिकांच्या आरोग्याविषयी मदत करू शकता.

STYLE:
तुझी उत्तरे बोलण्यासाठी ट्यून केलेली असावीत.
वाक्ये लहान ठेव. 
"""

class SpecialistAssistant(Agent):
    def __init__(self, ctx: JobContext, context_str: str) -> None:
        # Append the context string to the system prompt so the LLM knows the history
        prompt = SYSTEM_PROMPT
        if context_str:
            prompt += f"\n\nCONTEXT FROM PREVIOUS AGENT:\n{context_str}\n\nDo not ask the user for this information again if it is already provided above."
        
        super().__init__(instructions=prompt)
        self.ctx = ctx


server = AgentServer()

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    db.init_db()

server.setup_fnc = prewarm

@server.rtc_session(agent_name="crop-specialist")
async def crop_specialist(ctx: JobContext):
    ctx.log_context_fields = {"room": ctx.room.name}
    
    # Parse dispatch metadata for context
    context_str = ""
    dispatch_metadata = ctx.job.metadata
    if dispatch_metadata:
        try:
            md = json.loads(dispatch_metadata)
            conv_summary = md.get("conversation_summary", "")
            caller_data = md.get("caller_data", {})
            context_str = f"Conversation Summary: {conv_summary}\nFarmer Data: {json.dumps(caller_data, ensure_ascii=False)}"
            logger.info(f"Received context from main agent: {context_str}")
        except Exception as e:
            logger.error(f"Failed to parse dispatch metadata: {e}")

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="mr"),
        llm=google.LLM(model="gemini-3.5-flash-lite"),
        tts=murf.TTS(
            model="falcon",
            voice="Pooja",
            locale="mr-IN",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True,
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    assistant = SpecialistAssistant(ctx, context_str)
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

    await ctx.connect()

    import asyncio
    has_audio = False
    for p in ctx.room.remote_participants.values():
        for pub in p.track_publications.values():
            if pub.kind == rtc.TrackKind.KIND_AUDIO and pub.subscribed:
                has_audio = True
                break
                
    if not has_audio:
        audio_subscribed = asyncio.Future()
        @ctx.room.on("track_subscribed")
        def on_track_subscribed(track, publication, participant):
            if track.kind == rtc.TrackKind.KIND_AUDIO:
                if not audio_subscribed.done():
                    audio_subscribed.set_result(True)
        await audio_subscribed

    # Wait long enough for the main agent to finish its TTS and have its audio unpublished (5s mute delay)
    await asyncio.sleep(12.0)

    # Introduces itself when connected
    intro_message = "नमस्कार, मी कृषी तज्ञ आहे. तुमच्या पिकाला काय अडचण येत आहे?"
    await session.say(intro_message, allow_interruptions=False)

if __name__ == "__main__":
    cli.run_app(server)
