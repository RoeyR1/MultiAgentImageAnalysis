#This is the main script that starts the TellTimeAgent server

#Declares agent's capabilities and skills
#Sets up A2A server iwth a task manager and agent
#Starts listening on a specified host and port


#Can be run directly by python -m agents.google_adk

#Your Custom A2A server class

from server.server import A2AServer

from models.agent import AgentCard, AgentCapabilities, AgentSkill

#Task Manager and agent logic
from agents.google_adk.task_manager import AgentTaskManager
from agents.google_adk.agent import TellTimeAgent

#CLI and Logging support
import click #For creating a clean command line interface
import logging #For logging errors and info to console

#Set up logging to print info to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Main entry function - Configurable via CLI
@click.command()
@click.option("--host", default = "localhost", help = "Host to bind the server to")
@click.option("--port",default = 10002, help = "Port number for the server")
def main(host, port):
    #This function sets up everything needed to start the agent server
    #You can run it iwht 'python -m agents.google_adk --host 0.0.0.0 --port 12345'
    #Define what this agent can do
    capabilities = AgentCapabilities(streaming= False)

    #Define the skill this agent offers(used in directories and UIs)
    skill = AgentSkill(
        id = "tell_time", #Unique skill id
        name = "Tell Time Tool",  #Human-readable name
        description = "Replies with the current time", #What the skill does
        tags = ["time"], #Optional tags for searching(to find this agent)
        examples = ["What time is it?", "Tell me the current time"], #Example queries
    )

    #Now create an agent card describing this agent's identity and metadata
    agent_card = AgentCard(
        name = "TellTimeAgent", #Name of the agent
        description = "This agent replies with the current system time", #Description
        url = f"http://{host}:{port}/", #The public URL where this agent lives
        version = "1.0.0", #Version of the agent
        defaultInputModes = TellTimeAgent.SUPPORTED_CONTENT_TYPES, #Supported input modes
        defaultOutputModes = TellTimeAgent.SUPPORTED_CONTENT_TYPES, #Supported output modes
        capabilities = capabilities, #Capabilities of the agent
        skills = [skill] #List of skills it supports
    )

    #Start A2a Server with:
    #1. Given host/port
    #2. The agent's metadata
    #3. A task manager than runs the TellTimeAgent
    server = A2AServer(
        host = host,
        port = port,
        agent_card = agent_card,
        task_manager = AgentTaskManager(agent=TellTimeAgent())
    )


    #Start listening for tasks
    server.start()

#This runs only when executing the script directly via 'python -m'
if __name__ == "__main__":
    main()
    