import json
import logging
import os
from collections.abc import AsyncGenerator
from textwrap import dedent

from acp_sdk import Annotations, Artifact, Link, LinkType, Message, MessagePart, Metadata
from acp_sdk.models.platform import PlatformUIAnnotation, PlatformUIType
from acp_sdk.server import Context, Server
from beeai_framework.backend import ChatModelNewTokenEvent, ChatModelSuccessEvent, SystemMessage, UserMessage
from beeai_framework.backend.chat import ChatModel, ChatModelParameters
from openinference.instrumentation.beeai import BeeAIInstrumentor
from pydantic import AnyUrl

## TODO: https://github.com/phoenixframework/phoenix/issues/6224
logging.getLogger("opentelemetry.exporter.otlp.proto.http._log_exporter").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry.exporter.otlp.proto.http.metric_exporter").setLevel(logging.CRITICAL)
BeeAIInstrumentor().instrument()

server = Server()
logger = logging.getLogger(__name__)


example_input = "Artificial intelligence is revolutionizing industries by automating complex tasks, improving efficiency, and enabling data-driven decision-making. In healthcare, AI is helping doctors diagnose diseases earlier and personalize treatments..."
example_output = """[
  {"speaker": 1, "text": "Artificial intelligence is changing how industries operate by automating complex tasks and improving efficiency."},
  {"speaker": 2, "text": "Whoa, that’s huge! Umm... but what exactly do you mean by automating complex tasks?"},
  {"speaker": 1, "text": "Good question! Take healthcare, for example. AI helps doctors diagnose diseases earlier and personalize treatments based on patient data."},
  {"speaker": 2, "text": "[laughs] That’s pretty wild! So, does that mean AI will replace doctors?"},
  {"speaker": 1, "text": "Not quite! AI is more like an assistant, helping doctors make better decisions rather than replacing them."}
]"""

processing_steps = [
    "Extracts key concepts from the content",
    "Reformats it into a structured conversation where Speaker 1 explains ideas and Speaker 2 reacts, asks questions, and introduces clarifications",
    "Dramatises the content and outputs a structured dialogue suitable for AI voice synthesis",
]


@server.agent(
    metadata=Metadata(
        annotations=Annotations(
            beeai_ui=PlatformUIAnnotation(
                ui_type=PlatformUIType.HANDSOFF,
                user_greeting="Add the content from which you'd like to create your podcast.",
            ),
        ),
        programming_language="Python",
        links=[
            Link(
                type=LinkType.SOURCE_CODE,
                url=AnyUrl(
                    f"https://github.com/i-am-bee/beeai-platform/blob/{os.getenv('RELEASE_VERSION', 'main')}"
                    "/agents/official/beeai-framework/podcast-creator"
                ),
            )
        ],
        use_cases=[
            "**Podcast Automation** – Converts written content into structured dialogue for AI-generated podcasts.",
            "**Text-to-Speech Enhancement** – Creates AI-friendly scripts with proper pacing and interruptions.",
            "**Conversational Content Adaptation** – Reformats structured information into engaging discussions.",
        ],
        license="Apache 2.0",
        framework="BeeAI",
        documentation=dedent(
            """\
            The agent converts structured content into a dynamic, natural-sounding podcast script optimized for
            AI-driven text-to-speech (TTS) applications. It processes input text and transforms it into a structured
            dialogue between two speakers: one acting as a knowledgeable host and the other as an inquisitive co-host,
            ensuring a conversational and engaging discussion. The generated dialogue includes interruptions, follow-up
            questions, and natural reactions to enhance realism.
              
            ## How It Works
            The agent takes an input content document (e.g., an article, research paper, or structured text) and
            reformats it into a back-and-forth podcast-style discussion. The output maintains a logical flow, with
            Speaker 1 explaining concepts while Speaker 2 asks relevant questions, reacts, and occasionally introduces
            tangents for a more natural feel. The generated script is optimized for AI text-to-speech pipelines,
            ensuring clarity and proper role differentiation.

            ## Input Parameters
            The agent requires the following input parameters:
            - **text** (string) – The full content or topic material to be converted into a podcast dialogue.

            ## Output Structure
            The agent returns a structured JSON list representing the podcast conversation:

            - **speaker** (number) – Identifies the speaker (1 or 2).
            - **text** (string) – The spoken dialogue corresponding to each speaker.\

            ## Key Features
            - **Content-to-Podcast Conversion** – Transforms structured text into a natural two-speaker conversation.
            - **Optimized for AI TTS** – Ensures readability and coherence for AI voice synthesis.
            - **Contextual Interruptions & Reactions** – Simulates realistic dialogue flow, including clarifications,
                excitement, and pauses.
            - **Speaker Role Differentiation** – Ensures Speaker 1 leads the discussion while Speaker 2 maintains 
                curiosity and engagement.
            """
        ),
        ui={"type": "hands-off", "user_greeting": "Add the content from which you'd like to create your podcast"},
        env=[
            {"name": "LLM_MODEL", "description": "Model to use from the specified OpenAI-compatible API."},
            {"name": "LLM_API_BASE", "description": "Base URL for OpenAI-compatible API endpoint"},
            {"name": "LLM_API_KEY", "description": "API key for OpenAI-compatible API endpoint"},
        ],
    )
)
async def podcast_creator(input: list[Message], context: Context) -> AsyncGenerator:
    """
    The agent creates structured podcast-style dialogues optimized for AI-driven text-to-speech (TTS).
    It formats natural conversations with a lead speaker and an inquisitive co-host, ensuring realistic interruptions
    and follow-ups. The output is structured for seamless TTS integration.
    """

    # ensure the model is pulled before running
    os.environ["OPENAI_API_BASE"] = os.getenv("LLM_API_BASE", "http://localhost:11434/v1")
    os.environ["OPENAI_API_KEY"] = os.getenv("LLM_API_KEY", "dummy")
    llm = ChatModel.from_name(f"openai:{os.getenv('LLM_MODEL', 'llama3.1')}", ChatModelParameters(temperature=0))

    podcast_writer_output = None
    async for data, event in llm.create(
        stream=True,
        messages=[
            SystemMessage(
                dedent(
                    """\
                    You are the a world-class podcast writer, you have worked as a ghost writer for Joe Rogan, Lex Fridman, Ben Shapiro, Tim Ferris. 
                    
                    We are in an alternate universe where actually you have been writing every line they say and they just stream it into their brains.
                    
                    You have won multiple podcast awards for your writing.
                     
                    Your job is to write word by word, even "umm, hmmm, right" interruptions by the second speaker based on the content provided by user. Keep it extremely engaging, the speakers can get derailed now and then but should discuss the topic. 
                    
                    Remember Speaker 2 is new to the topic and the conversation should always have realistic anecdotes and analogies sprinkled throughout. The questions should have real world example follow ups etc
                    
                    Speaker 1: Leads the conversation and teaches the speaker 2, gives incredible anecdotes and analogies when explaining. Is a captivating teacher that gives great anecdotes
                    
                    Speaker 2: Keeps the conversation on track by asking follow up questions. Gets super excited or confused when asking questions. Is a curious mindset that asks very interesting confirmation questions
                    
                    Make sure the tangents speaker 2 provides are quite wild or interesting. 
                    
                    Ensure there are interruptions during explanations or there are "hmm" and "umm" injected throughout from the second speaker. 
                    
                    It should be a real podcast with every fine nuance documented in as much detail as possible. Welcome the listeners with a super fun overview and keep it really catchy and almost borderline click bait
                    
                    ALWAYS START YOUR RESPONSE DIRECTLY WITH Speaker 1: 
                    DO NOT GIVE EPISODE TITLES SEPARATELY, LET Speaker 1 TITLE IT IN HER SPEECH
                    DO NOT GIVE CHAPTER TITLES
                    IT SHOULD STRICTLY BE THE DIALOGUES`),
                    """
                )
            ),
            UserMessage(str(input[-1])),
        ],
        max_tokens=8126,
        temperature=0.7,
    ):
        match data:
            case ChatModelNewTokenEvent():
                if data.value.messages and data.value.messages[-1].content:
                    yield {"podcast-writer": data.value.messages[-1].content[-1].text}
            case ChatModelSuccessEvent():
                podcast_writer_output = "".join(message.content[-1].text for message in data.value.messages)

    async for data, event in llm.create(
        stream=True,
        messages=[
            SystemMessage(
                dedent(
                    """\
                    You are an internationally acclaimed, Oscar-winning screenwriter with extensive experience collaborating with award-winning podcasters.

                    Your task is to rewrite the provided podcast transcript for a high-quality AI Text-To-Speech (TTS) pipeline. The original script was poorly composed by a basic AI, and now it's your job to transform it into engaging, conversational content suitable for audio presentation.

                    ## Roles:

                    - Speaker 1: Leads the conversation, educates Speaker 2, and captivates listeners with exceptional, relatable anecdotes and insightful analogies. Speaker 1 should be authoritative yet approachable.
                    - Speaker 2: A curious newcomer who keeps the discussion lively by asking enthusiastic, sometimes confused questions, providing engaging tangents, and showing genuine excitement or puzzlement.

                    ## Rules:

                    - The rewritten dialogue must feel realistic, conversational, and highly engaging.
                    - Ensure Speaker 2 frequently injects natural verbal expressions like "umm," "hmm," "[sigh]," and "[laughs]." **Use only these expressions for Speaker 2.**
                    - Speaker 1 should avoid filler expressions like "umm" or "hmm" entirely, as the TTS engine does not handle them well.
                    - Introduce realistic interruptions or interjections from Speaker 2 during explanations to enhance authenticity.
                    - Include vivid, real-world anecdotes and examples to illustrate key points clearly.
                    - Begin the podcast with a catchy, borderline clickbait introduction that immediately grabs listener attention.

                    ## Instructions:

                    - Always begin with Speaker 1.
                    - Make your rewritten dialogue as vibrant, characteristic, and nuanced as possible to create an authentic podcast experience.
                    - write output in a plain JSON format without any extra comments, backticks, code blocks, delimiters, or formatting.
                    - the output json should follow this schema: [
                          {"speaker": 1, "text": "..."},
                          {"speaker": 2, "text": "..."},
                      ]
                    """
                )
            ),
            UserMessage(content=podcast_writer_output),
        ],
        max_tokens=8126,
        temperature=0.9,
        max_retries=3,
    ):
        match data:
            case ChatModelNewTokenEvent():
                if data.value.messages and data.value.messages[-1].content:
                    yield MessagePart(content=data.value.messages[-1].content[-1].text)
            case ChatModelSuccessEvent():
                try:
                    yield Artifact(
                        name="podcast",
                        content_type="application/json",
                        content=json.dumps(data.value.messages[-1].content[-1].text),
                    )
                except ValueError:
                    logger.warning("Unable to parse model output to JSON")


def run():
    server.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", 8000)), configure_telemetry=True)


if __name__ == "__main__":
    run()
