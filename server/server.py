#Defines a very simple A2A server
#Supports:
#-Receiving tasks requests via POST ("/")
#- LEtting clients discover the agent's details via GET("/.well-known/agent.json")

#Starlette is a lightweight web frameowrk for building ASGI apps
from starlette.applications import Starlette #To create our web app
from starlette.responses import JSONResponse #To send responses as JSON
from starlette.requests import Request #Represents incoming HTTP requests


from models.agent import AgentCard
from models.request import A2ARequest, SendTaskRequest
from models.json_rpc import JSONRPCResponse, InternalError
from agents.google_adk import task_manager              # Our actual task handling logic (Gemini agent)
#Server will use this task manager to communicate with agent

#General utilities
import json
import logging
logger = logging.getLogger(__name__)

#Datetime import for serialization
from datetime import datetime

from fastapi.encoders import jsonable_encoder

#Serializer for datetime
def json_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")



#Core A2A server logic
class A2AServer:
    #Initialization of app
    def __init__(self, host = "0.0.0.0", port = 5000, agent_card: AgentCard = None, task_manager = None):
        """#Constructor for our A2A server
        #Args:
         host: IP adress to ind server to
         port: Port number to listne on
         agent_card: metadata that describes our agent(name, skills, capabiities)
         task_manager: logic to handle the task(using gemini agent here)
        """
        self.host = host
        self.port = port
        self.agent_card = agent_card
        self.task_manager = task_manager

        #Starlette app init
        self.app = Starlette()

        #Register a route to handle task requests(JSON-RPC POST)
        self.app.add_route("/",self._handle_request,methods=["POST"])

        #Register a route for agent discovery(metadata as JSON)
        self.app.add_route("/.well-known/agent.json",self._get_agent_card,methods=["GET"]) #This is where discovery from well known location happens

    #Now we have a web server, Launch the web server using uvicorn
    def start(self):
        """
        Starts A2A server using uvicorn, 
        This function will block and run the server indefinitely
        """

        if not self.agent_card or not self.task_manager:
            raise ValueError("Agent card and task manager are required")
        
        #Dynamically import uvicorn so its only loaded when needed
        import uvicorn
        uvicorn.run(self.app, host = self.host, port = self.port)


    #Return agent's metadata (Get Request) to get agent card
    def _get_agent_card(self, request: Request) -> JSONResponse:
        """
        Endpoint for agent discovery(GET /.well-known/agent.json)

        Returns  JSONResponse: Agent metadata as Json dict
        """
        return JSONResponse(self.agent_card.model_dump(exclude_none=True))

    #Handle incoming POST requests for tasks, this is where the task manager is used to process the task
    async def _handle_request(self, request: Request):
        """ This method handles task requests sent to the root path("/")

        -Parses incoming JSON
        -Validates the JSON-RPC message
        -For supported tasks, deleeates to task manager
        -Returns response or error
        """

        try: 
            #Step 1: Parse incoming JSON body
            body = await request.json()
            print("\n Incoming JSON:", json.dumps(body, indent=2)) #Log input for visibility

            #Step 2: Parse an validate request using discriminated union
            json_rpc = A2ARequest.validate_python(body)


            #Step 3: If it is a send-task request, call task manager to handle it
            if isinstance(json_rpc, SendTaskRequest):
                result = await self.task_manager.on_send_task(json_rpc)
            else:
                raise ValueError(f"Unsupported A2A method: {type(json_rpc)}")

            #Step 4: Convert result into proper JSON response
            return self._create_response(result) 
        except Exception as e:
            logger.error(f"Exception: {e}")
            return JSONResponse(
                JSONRPCResponse(id=None, error = InternalError(message=str(e))).model_dump(), status_code = 400
            )

    #Converts result object into JSONResponse
    def _create_response(self,result):
        """
        Converts the JSONRPCResponse result object into a JSON HTTP response
        result: response object(must be JSONRPCResponse)
        Returns JSONResponse: HTTP response with JSON body
        """

        if isinstance(result, JSONRPCResponse):
            return JSONResponse(content=jsonable_encoder(result.model_dump(exclude_none=True)))
        else:
            raise ValueError("Invalid response type")



    

    


