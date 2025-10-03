
# This file defines a reusable, asynchronous Python client for interacting
# with an Agent2Agent (A2A) server.
#
# It supports:
# - Sending tasks and receiving responses
# - Getting task status or history


import json #to encode/encode JSON data
from uuid import uuid4
import httpx
from httpx_sse import connect_sse
from typing import Any

#import supported requet types
from models.request import SendTaskRequest, GetTaskRequest #Removed canceltaskrequest

#Base request format for JSON-RPC 2.0
from models.json_rpc import JSONRPCRequest

#Models for task results and agent identity
from models.task import Task, TaskSendParams
from models.agent import AgentCard


#Custom Error Classes
class A2AClientHTTPError(Exception):
    pass

class A2AClientJSONError(Exception):
    """When response is not valid JSON"""
    pass


#A2AClient :Main interface for talking to an A2A Agent
class A2AClient:
    #Constructor
    def __init__(self, agent_card: AgentCard = None, url: str = None):
        """
        Initializes the client using either an agent card or a direct url
        One of the two must be provided
        """
        #Doing manual discovery here to discover the agent 
        #Client only needs to know URL in constructor
        if agent_card:
            self.url = agent_card.url
        elif url:
            self.url = url
        else:
            raise ValueError("Either agent_card or url must be provided")
    #Send a new task to the agent, this uses send_request fxn to send request to server
    async def send_task(self, payload: dict[str, Any]) -> Task:
        request = SendTaskRequest(
            id = uuid4().hex,
            params = TaskSendParams(**payload) #Proper model wrapping
            #TaskSendParams has an id, sessionid, message, historylength, metadata
            )

        print("\n Sending JSON-RPC request:")
        print(json.dumps(request.model_dump(), indent=2))

        response = await self._send_request(request) #Once request object is made, use send_request function to send request to agent,
        #We wait for response then return the task with the result from the response
        return Task(**response["result"]) #Extract just the "result" field 
    

    #Internal helper to send a JSON-RPC request to server
    async def _send_request(self, request: JSONRPCRequest) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                
                response = await client.post( #Send POST request to Agent's URL
                    self.url, #Send to agent's URL
                    json = request.model_dump(), #Convert request to JSON
                    timeout = 30
                    )
                response.raise_for_status() #Raise error if status is 4xx/5xx
                return response.json() #Return parsed response as a dict
                
            except httpx.HTTPStatusError as e:
                raise A2AClientHTTPError(e.response.status_code, str(e)) from e
            
            except json.JSONDecodeError as e:
                raise A2AClientJSONError(str(e)) from e

