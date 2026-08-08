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
# =============================================================================

import logging
import sys

# Fix Windows console unicode errors when printing Marathi text
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    tokenize,
    room_io,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

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
तिसरा नियम एस्केलेशनसाठी आहे. जर शेतकऱ्याने अशा गंभीर पीक रोगाबद्दल विचारले जो तू ओळखू शकत नाहीस किंवा खूप क्लिष्ट प्रश्न आला तर नम्रपणे सांग की तू हे निदान करू शकत नाहीस. त्यांना त्यांच्या जवळच्या कृषी विज्ञान केंद्र म्हणजे KVK किंवा कृषी तज्ञांशी संपर्क करण्याचा सल्ला दे.

STYLE:
तुझी उत्तरे बोलण्यासाठी ट्यून केलेली असावीत, टेक्स्टसाठी नाही.
वाक्ये लहान ठेव, वीस शब्दांपेक्षा कमी.
मध्यम आणि मैत्रीपूर्ण वेगाने बोल.
बुलेट पॉइंट्स, ब्रॅकेट्स, तारांकित चिन्हे, किंवा मार्कडाउन फॉरमॅटिंग वापरू नकोस.
कारण तुझे बोलणे Text-to-Speech इंजिनने मोठ्याने वाचले जाईल.
"""

# First-turn greeting spoken aloud when the agent connects to a session.
WELCOME_MESSAGE = (
    "नमस्कार! मी AgriAlert, तुमचा शेतीतला डिजिटल मित्र. "
    "आज शेतात काय मदत करू? "
    "पीक, हवामान, खत, कीटक, कशाबद्दलही विचारा."
)



class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


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
                text_pacing=True
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
    await session.start(
        agent=Assistant(),
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

    # Speak the welcome greeting aloud once connected
    await session.say(WELCOME_MESSAGE)


if __name__ == "__main__":
    cli.run_app(server)
