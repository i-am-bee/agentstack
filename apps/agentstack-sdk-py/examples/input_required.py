from typing import AsyncGenerator
from a2a.types import Message, TaskStatus
from agentstack_sdk.a2a.types import InputRequired
from agentstack_sdk.server import Server

server = Server()

@server.agent()
async def input_required(
    message: Message
) -> AsyncGenerator[TaskStatus | str, Message]:
    """Agent that asks for user input during execution"""
    
    yield "I'm processing your request...\n"
    
    response = yield InputRequired(text="What email address should I use?")
    email = response.parts[0].root.text
    yield f"Great! I'll use {email}\n"
    
    response = yield InputRequired(text="What subject line do you want?")
    subject = response.parts[0].root.text
    
    yield f"Perfect! Sending email to {email} with subject: {subject}"

if __name__ == "__main__":
    server.run()
