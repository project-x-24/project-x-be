import asyncio
import json
import os
import re

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant, AssistantTranscriptionOptions
from livekit.plugins import deepgram, openai, silero, elevenlabs
from livekit.plugins.elevenlabs import Voice, VoiceSettings
from livekit import rtc
from dotenv import load_dotenv
from livekit import api
import requests

from assistant.base_prompts import base_prompts

load_dotenv("../.env")


class Agent():
    # This function is the entrypoint for the agent.
    agentType = ''
    lastQuestion = ''
    def __init__(self, agentType: str):
        self.agentType = agentType
    
    async def entrypoint(self, ctx: JobContext):
        chat_history = ''
        try:
            chat_history = requests.get(f"http://0.0.0.0:3000/api/context?agent={self.agentType}", headers={"Content-Type": "application/json"})
        except Exception as error:
            print("Couldn't get chat history", error)
        base_prompt = f"""
            {base_prompts[self.agentType]}
            Chat history
            {chat_history}
        """
        # Create an initial chat context with a system prompt
        token = GetToken("my-room")
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

        KURIAN_VOICE = Voice(
            id="aWHwsR3lAJpw5qdEam15",
            name="Kurian",
            category="premade",
        )

        def before_lmm_cb(assistant, chat_ctx):
            return assistant.llm.chat(
                chat_ctx=chat_ctx,
                fnc_ctx=assistant.fnc_ctx,
            )

        transcriptionOptions = AssistantTranscriptionOptions(
            user_transcription=True,
            agent_transcription=True,
        )

        assistant = VoiceAssistant(
            vad=silero.VAD.load(),
            stt=deepgram.STT(),
            llm=openai.LLM(),
            # tts=openai.TTS(),
            tts=elevenlabs.TTS(voice=KURIAN_VOICE),
            chat_ctx=initial_ctx,
            before_llm_cb=before_lmm_cb,
            min_endpointing_delay=3,
            transcription=transcriptionOptions,
        )

        def user_started_speaking_callback( answer_message):
            self.lastQuestion = answer_message.content
            try:
                # Regular expression pattern to capture Event Name and Date
                pattern = r"\[(.+?)\|(.+?)\]"

                # Using re.search to find matches
                match = re.search(pattern, answer_message.content)

                if match:
                    event_name = match.group(1)  # First captured group is the event name
                    date = match.group(2)  # Second captured group is the date
                    print(f"Event Name: {event_name}")
                    print(f"Date: {date}")

                    try:
                        data = { "event": event_name, "date": date }
                        response = requests.post("http://0.0.0.0:3000/api/todo", data=json.dumps(data), headers={"Content-Type": "application/json"})
                        if response.status_code == 200:
                            print("ToDo successfully sent to the API.")
                        else:
                            print(f"Failed to add To Do. Status code: {response.status_code}")
                    except Exception as error:
                        print("An exception occurred", error)
                else:
                    print("No match found.")
            except Exception as e:
                print("Error in extracting Event Name and Date")
                pass
            print("User started speaking")

            # Save here - Bobby

        assistant.on("agent_speech_committed", user_started_speaking_callback)
        # Start the voice assistant with the LiveKit room
        assistant.start(ctx.room)

        # listen to incoming chat messages, only required if you'd like the agent to
        # answer incoming messages from Chat
        chat = rtc.ChatManager(ctx.room)

        async def answer_from_text(self, txt: str):
            api_url = "http://0.0.0.0:3000/api/context"
            headers = {'Content-Type': 'application/json'}
            data = {     
                "agent":self.agentType,
                "question":self.lastQuestion,
                "answer":txt,}
            try:
                response = requests.post(api_url, data=json.dumps(data), headers=headers)
                if response.status_code == 200:
                    print("Chat history successfully sent to the API.")
                else:
                    print(f"Failed to send chat history. Status code: {response.status_code}")
            except Exception as error:
                print("An exception occurred", error)    
            chat_ctx = assistant.chat_ctx.copy()
            chat_ctx.append(role="user", text=txt)
            stream = llm_plugin.chat(chat_ctx=chat_ctx)
            await assistant.say(stream)

        @chat.on("message_received")
        def on_chat_received(msg: rtc.ChatMessage):
            if msg.message:
                asyncio.create_task(answer_from_text(self, msg.message))

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
    AGENT_TYPE = os.environ.get("AGENT_TYPE") # SELF_AGENT, THERAPIST, BEST_FRIEND, GAME_AGENT
    agent = Agent(AGENT_TYPE)
    print("Agent Type", AGENT_TYPE)
    cli.run_app(WorkerOptions(entrypoint_fnc=agent.entrypoint))
