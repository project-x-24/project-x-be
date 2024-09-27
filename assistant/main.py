import asyncio

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai, silero, elevenlabs
from livekit.plugins.elevenlabs import Voice, VoiceSettings
from livekit import rtc
from dotenv import load_dotenv

load_dotenv("../.env")


# This function is the entrypoint for the agent.
async def entrypoint(ctx: JobContext):
    # Create an initial chat context with a system prompt
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are a voice assistant created by LiveKit. Your interface with users will be voice. "
            "You should use short and concise responses, and avoiding usage of unpronouncable punctuation."
        ),
    )

    # Connect to the LiveKit room
    # indicating that the agent will only subscribe to audio tracks
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    llm_plugin = openai.LLM()

    # VoiceAssistant is a class that creates a full conversational AI agent.
    # See https://github.com/livekit/agents/tree/main/livekit-agents/livekit/agents/voice_assistant
    # for details on how it works.

    AJAI_VOICE = Voice(
        id="hM5T22C2VeL3rbIKUecn",
        name="Ajai",
        category="premade",
        # settings=VoiceSettings(
        #     stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True
        # ),
    )

    HARI_VOICE = Voice(
        id="ZasyRy4wU4dDh3cG8ju4",
        name="Hari",
        category="premade",
        # settings=VoiceSettings(
        #     stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True
        # ),
    )

    def before_lmm_cb(assistant, chat_ctx):
        chat_ctx.append(
            role="system",
            text=(
                "Pretend you are alex, alex a good minecraft player"
            ),
        )
        return assistant.llm.chat(
            chat_ctx=chat_ctx,
            fnc_ctx=assistant.fnc_ctx,
        )

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        # tts=elevenlabs.TTS(voice=HARI_VOICE),
        chat_ctx=initial_ctx,
        before_llm_cb=before_lmm_cb
    )

    # Start the voice assistant with the LiveKit room
    assistant.start(ctx.room)

    # listen to incoming chat messages, only required if you'd like the agent to
    # answer incoming messages from Chat
    chat = rtc.ChatManager(ctx.room)

    async def answer_from_text(txt: str):
        chat_ctx = assistant.chat_ctx.copy()
        chat_ctx.append(role="user", text=txt)
        stream = llm_plugin.chat(chat_ctx=chat_ctx)
        await assistant.say(stream)

    @chat.on("message_received")
    def on_chat_received(msg: rtc.ChatMessage):
        if msg.message:
            asyncio.create_task(answer_from_text(msg.message))

    await asyncio.sleep(1)

    # Greets the user with an initial message
    await assistant.say("Hey, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    # Initialize the worker with the entrypoint
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
