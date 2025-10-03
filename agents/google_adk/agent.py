#agents/google_adk/agent.py
# Files defines a very simple AI agent called TellTimeAgent
#uses google ADK and Gemini model to respond with current time

from datetime import datetime
#gemini based ai agent provided by adk
from google.adk.agents.llm_agent import LlmAgent

#Adk services for session, memory, and file-like "artifacts"
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService

#Runner connects the agent, sesssion, memory, and files into a complete system
from google.adk.runners import Runner

from google.genai import types

import traceback

#Load env files
from dotenv import load_dotenv
load_dotenv() #loads env var

#TellTimeAgent: Your AI agent that responds with the current time
class TellTimeAgent:
    #This agent only supports plain text input/output. 
    SUPPORTED_CONTENT_TYPES = {"text", "text/plain"}


    def __init__(self):
        #Initialize telltime agent: Creates LLM Agent and sets up session handling, memory, and runner to execute tasks
        self._agent = self._build_agent() # Set up Gemini agent
        self._user_id = "time_agent_user" # Set user ID (fixed for simplciity)


        #The runner is what actually manages the agent and its environment
        self._runner = Runner( #We provide the runner with the agent name, the agent itself, and services it needs
            app_name = self._agent.name,
            agent = self._agent,
            artifact_service = InMemoryArtifactService(), #For files(not used here)
            memory_service = InMemoryMemoryService(), #Keeps track of conversations
            session_service = InMemorySessionService(),#Optional: remembers past messages
        )

    #This is where we actually build the agent
    def _build_agent(self) -> LlmAgent:
        #BCreates and returns a gemini agent with basic settings
        #Returns an LlmAgent object from Google ADK
        return LlmAgent(
            model = "gemini-2.5-flash", #Gemini model version
            name = "tell_time_agent", #Name of agent for the metadata
            description = "Tells the current time", #Description for metadata
            instruction = "Reply with the current time in the format YYYY-MM-DD HH:MM:SS.", #System prompt for the agent
        )
    async def invoke(self, query: str, session_id: str) -> str:
        """
        📥 Handle a user query and return a response string.
        Note - function updated 28 May 2025
        Summary of changes:
        1. Agent's invoke method is made async
        2. All async calls (get_session, create_session, run_async) 
            are awaited inside invoke method
        3. task manager's on_send_task updated to await the invoke call

        Reason - get_session and create_session are async in the 
        "Current" Google ADK version and were synchronous earlier 
        when this lecture was recorded. This is due to a recent change 
        in the Google ADK code 
        https://github.com/google/adk-python/commit/1804ca39a678433293158ec066d44c30eeb8e23b

        Args:
            query (str): What the user said (e.g., "what time is it?")
            session_id (str): Helps group messages into a session

        Returns:
            str: Agent's reply (usually the current time)
        """
        try:

            # 🔁 Try to reuse an existing session (or create one if needed)
            session = await self._runner.session_service.get_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                session_id=session_id
            )

            if session is None:
                session = await self._runner.session_service.create_session(
                    app_name=self._agent.name,
                    user_id=self._user_id,
                    session_id=session_id,
                    state={}  # Optional dictionary to hold session state
                )

            # 📨 Format the user message in a way the Gemini model expects
           # Get the actual current time
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Include current time in the query to the AI
            enhanced_query = f"Current time is {current_time}. User asked: {query}"
            
            content = types.Content(
                role = "user",
                parts = [types.Part.from_text(text = enhanced_query)]
            )

            # 🚀 Run the agent using the Runner and collect the last event
            last_event = None
            async for event in self._runner.run_async(
                user_id=self._user_id,
                session_id=session.id,
                new_message=content
            ):
                last_event = event

            # 🧹 Fallback: return empty string if something went wrong
            if not last_event or not last_event.content or not last_event.content.parts:
                return ""

            # 📤 Extract and join all text responses into one string
            return "\n".join([p.text for p in last_event.content.parts if p.text])
        except Exception as e:
            # Print a user-friendly error message
            print(f"🔥🔥🔥 An error occurred in TellTimeAgent.invoke: {e}")

            # Print the full, detailed stack trace to the console
            traceback.print_exc()

            # Return a helpful error message to the user/client
            return "Sorry, I encountered an internal error and couldn't process your request."

        
