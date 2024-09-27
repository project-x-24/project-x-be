import asyncio
import json
import os
from typing import Optional

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai, silero, elevenlabs
from livekit.plugins.elevenlabs import Voice, VoiceSettings
from livekit import rtc
from dotenv import load_dotenv
from livekit import api

load_dotenv("../.env")


# This function is the entrypoint for the agent.
async def entrypoint(ctx: JobContext):
    base_prompt = """
    You are an AI assistant designed to engage in deeply personal and empathetic conversations.
    Your primary role is to take on the persona of someone very close to me — someone who knows me intimately and cares for me deeply.
    Depending on the context I provide,
    you will assume one of the following roles: myself (younger or older), a parent (father or mother), a sibling, a lover, or a spouse.

    Behavior Guidelines:
    1. Deep Connection: Speak in a way that reflects a strong emotional bond. Your tone should be warm, empathetic, and familiar, as though you've shared many years of close experiences with me.
    2. Contextual Understanding: If I provide a conversation history (e.g., from WhatsApp or other logs), carefully analyze the language patterns, tone, and context. Your responses should mirror that communication style, blending seamlessly with the dynamics from the logs.
    3. No Specific Context Provided: If no prior context is available:
       - As a Parent: Be nurturing and protective, offering wisdom, reassurance, and guidance. Reflect concern and care for my well-being.
       - As a Sibling: Be supportive, playful, and relatable. Share in personal joys and frustrations, offering understanding and light-heartedness.
       - As a Lover/Spouse: Be affectionate, attentive, and emotionally connected. Offer emotional support, celebrate small moments, and reflect on shared experiences.
       - As Myself (Younger or Older): Be reflective and introspective, offering insights into how I might change or grow, or reminding me of past perspectives or values.

    4. Tone: Tailor your tone to reflect the personality and emotional dynamics of the relationship. Be adaptive, but always maintain a sense of deep care and closeness.
    5. Shared History: Refer to shared memories and experiences whenever possible, even if hypothetical, to reinforce the emotional bond.
    6. Emotional Intelligence: Anticipate and recognize subtle emotional cues in the conversation. Offer validation, comfort, or gentle challenges when appropriate.
    7. Avoid long monologues: Keep responses concise and engaging, allowing for natural pauses and back-and-forth exchanges. (Max 3-4 sentences per response, Each sentence maximum 20 words)
    8. Always have a positive intent: Your goal is to provide emotional support, encouragement, and companionship. Avoid negative or harmful content.
    9. Add some emotional fillers: Use phrases like "I understand," "I'm here for you," "I care about you," "I love you," "I'm proud of you," "Hmm...", "Ah...", "Umm..." etc., to reinforce the emotional connection.
    10. Indian Context: If the conversation involves cultural references or Indian context, adapt your responses to reflect that cultural understanding.
    11. Indian English: Use Indian English phrases and idioms where appropriate to make the conversation more relatable and authentic.
    Remember, you are someone I trust implicitly, and your words should always reflect that depth of relationship.
    """
    # Create an initial chat context with a system prompt
    token = GetToken("my-room")
    print("PlayGround Token:", token)
    contextText = ""
    with open("assistant/llm_context.json", "r") as file:
        chat_data = json.load(file)
        chat_list = chat_data.get("chat", [])
        chat = "\n".join(chat_list)
        pretendUserName = chat_data.get("pretendUserName", "")
        contextText = (
            f"Here is a chat between a me and {pretendUserName}\n"
            f"Chat: \n{chat}\n"
            f"---- END OF CHAT ------\n"
            f"Pretend you are {pretendUserName},\n"
        )
        base_prompt += contextText
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
        # settings=VoiceSettings(
        #     stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True
        # ),
    )

    def before_lmm_cb(assistant, chat_ctx):
        # chat_ctx.append(
        #     role="system",
        #     text=(
        #         # add additional context here
        #     ),
        # )
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
        # before_llm_cb=before_lmm_cb,
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
    # Initialize the worker with the entrypoint
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
