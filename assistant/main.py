import asyncio
import json
import argparse
import os
from typing import Optional

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai, silero, elevenlabs
from livekit.plugins.elevenlabs import Voice, VoiceSettings
from livekit import rtc
from dotenv import load_dotenv
from livekit import api

from assistant.base_prompts import base_prompts

load_dotenv("../.env")

AGENT_TYPE = os.environ.get('AGENT_TYPE') # SELF_AGENT, THERAPIST, BEST_FRIEND

# This function is the entrypoint for the agent.
async def entrypoint(ctx: JobContext):
    base_prompt = f"""
        base_prompts[AGENT_TYPE]
        Chat history
        <chat history here>
    """
    global chat_history
    chat_history = []
    # Create an initial chat context with a system prompt
    token = GetToken("asj-room")
    print("PlayGround Token:", token)
    initial_ctx = llm.ChatContext().append(role="system", text=base_prompt)

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

    # ZasyRy4wU4dDh3cG8ju4
    HARI_VOICE = Voice(
        id="ZJpPHx76HGgYYHKJJD0d",
        name="Hari",
        category="premade",
        settings=VoiceSettings(
            stability=0.10,
            similarity_boost=0.65,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    def before_lmm_cb(assistant, chat_ctx):
        global chat_history
        chat_history = [message for message in chat_ctx.messages]
        return assistant.llm.chat(
            chat_ctx=chat_ctx,
            fnc_ctx=assistant.fnc_ctx,
        )

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=openai.LLM(),
        # tts=openai.TTS(),
        tts=elevenlabs.TTS(voice=HARI_VOICE),
        chat_ctx=initial_ctx,
        before_llm_cb=before_lmm_cb,
        min_endpointing_delay=3,
    )

    def user_started_speaking_callback(answer_message):
        global chat_history
        chat_history.append(answer_message)
        # Save here - Bobby

    assistant.on("agent_speech_committed", user_started_speaking_callback)
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
    await assistant.say("Hey, whats up?", allow_interruptions=True)


def GetToken(roomName: str):
    apiKey = os.environ.get("LIVEKIT_API_KEY")
    apiSecrete = os.environ.get("LIVEKIT_API_SECRET")
    token = (
        api.AccessToken(apiKey, apiSecrete)
        .with_identity("identity")
        .with_name("my name")
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=roomName,
            )
        )
    )
    return token.to_jwt()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
