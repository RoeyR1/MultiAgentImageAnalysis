#This fole connects Gemini powered Agent to the task handling system
# Receives task, extracts the question("What time is it?"), asks the agent to respond, then saves and returns agent answer

import logging

from server.task_manager import InMemoryTaskManager
#import the actual agent we're using
from agents.google_adk.agent import TellTimeAgent


#Import data models used to structure nad return tasks
from models.request import SendTaskRequest, SendTaskResponse
from models.task import Message, Task, TextPart, TaskStatus, TaskState


#Logger setup
logger = logging.getLogger(__name__)


class AgentTaskManager(InMemoryTaskManager):
    #Connects gemini agent to task system
    # Uses the gemini agent to generate a response

    def __init__(self, agent: TellTimeAgent):
        super().__init__() #Calls parent class constructor
        self.agent = agent #Store gemini based agent as property

    #Extracts user query from incoming task
    def _get_user_query(self, request: SendTaskRequest) -> str:
        return request.params.message.parts[0].text
    
    #Main Logic to handle and complete a task
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        Does the following:
        1. Saves task into memory(or update it)
        2. Ask the gemini agent for a reply
        3. Format that reply as a message
        4. Save agent's reply into task history
        5. Return updated task to the caller
        """

        logger.info(f"Processing new task: {request.params.id}")

        #Step 1:  Save task using base class helper
        task = await self.upsert_task(request.params)

        #Step 2: Get what the user asked
        query = self._get_user_query(request)

        #Step 3: Ask gemini agent to respond(synchronous call)
        result_text = await self.agent.invoke(query, request.params.sessionId)

        #Step 4: Turn agents response into a message object

        agent_message = Message(
            role = "agent",
            parts = [TextPart(text = result_text)]
        )
        #Step 5: Update task state and add message to history

        async with self.lock:
            task.status = TaskStatus(state=TaskState.COMPLETED)
            task.history.append(agent_message)

        #Step 6: Return a structured response back to the A2A Client
        return SendTaskResponse(id = request.id, result = task)
       