# This file is a command-line interface (CLI) that lets users interact with
# the TellTimeAgent running on an A2A server.
#
# You can send text messages (like "What time is it?") to the agent,
# waits for a response, and displays it in the terminal.
#
# This version supports:
# - basic task sending via A2AClient
# - session reuse
# - optional task history printing


import asyncclick as click #async version of click, allows for async functions
import asyncio #Python module to run async event loops
from uuid import uuid4 #Used to generate unique task and session IDs

#Import A2a client from client module(this handles request/response logic)
from client.client import A2AClient

#Import Task model for response type
from models.task import Task




#Click command turns fxn below into command-line command
@click.command()
#Provide the Command line app with the agent that the client needs to connect to
@click.option("--agent", default="http://localhost:10002", help="Base URL of the A2A agent server")
# ^ This defines the --agent option. It's a string with a default of localhost:10002
# ^ Used to point to the running agent server (adjust if server runs elsewhere)

@click.option("--session", default=0, help="Session ID (use 0 to generate a new one)")
# ^ This defines the --session option. A session groups multiple tasks together.
# ^ If user passes 0, we generate a random session ID using uuid4.

@click.option("--history", is_flag=True, help="Print full task history after receiving a response")
async def cli(agent: str, session: str, history: bool):
    """
    Command Line interface to send user messages to an A2A Agent and display the response

    Args:
    agent: Base url of the A2A Agent server( e.g. http://localhost:10002)
    session: Either s tring session id or 0 to generate a new one
    history: If true, prints the full task history
    """

    #Initialize A2AClient by providing it with full POST endpoint(URL) for sending tasks
    print(f"Connecting to agent at: {agent}")
    client = A2AClient(url=f"{agent}") #Now knows what agent it needs to connect to

    #generate new session id if not provided (user passed 0)
    session_id = uuid4().hex if str(session) == "0" else str(session)
    print(f"Using session ID: {session_id}")

    # Start main input loop
    print("Starting CLI...")
    while True:
        #Prompt the user for input
        prompt = click.prompt("\n What do you want to send to the agent? (type ':q' or 'quit' to exit)")

        #Exit loop if user types ':q' or 'quit'
        if prompt.strip().lower() in [":q", "quit"]:
            break


        #Construct the payload using expected JSON-RPC task format
        payload = {
            "id": uuid4().hex,  # Generate a new unique task ID for this message
            "sessionId": session_id,  # Reuse or create session ID
            "message": {
                "role": "user",  # The message is from the user
                "parts": [{"type": "text", "text": prompt}]  # Wrap user input in a text part
            }
        }

        #Use the client to send the task to the agent
        try:
            #Send the task to the agent and get a Task response
            task: Task = await client.send_task(payload)

            #Check if agent responded(expecting at least 2 messages: user + agent)
            if task.history and len(task.history) > 1:
                reply = task.history[-1] #Last message is usually from the agent
                print("\n Agent says:", reply.parts[0].text)
            else:
                print("\n No response received.")

            #If history flag was set, show entire conversation history
            if history:
                print("\n Task History:")
                for msg in task.history:
                    print(f"[{msg.role}] {msg.parts[0].text}") #Show each message in sequence

        except Exception as e:
            print(f"\n Error while sending task: {e}")


# -----------------------------------------------------------------------------
# Entrypoint: This ensures the CLI only runs when executing `python cmd.py`
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Run the async `cli()` function inside the event loop
    asyncio.run(cli())
