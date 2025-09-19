#Client will dsicover tell time agent
#Import requests to send HTTP GET and POST requests
#Allows client to talk to server over Http
import requests

#Import uuid to generate unique task IDs
#Each A2A task needs a unique ID to track it
import uuid

#Step 1: Discover the agent
#Base URL where server agent is hosted (locally on port 5000 in this case)
base_url = "http://127.0.0.1:5000"
#Use GET request to fetch the agent's card from well known discovery endpoint.
res = requests.get(f"{base_url}/.well-known/agent.json")

#If the request fails, raise an error
if res.status_code != 200:
    raise Exception(f"Failed to discover agent: {res.status_code} {res.text}")

#Parse the response JSON into python dict to get agent info
agent_info = res.json()
print(f"Discovered agent: {agent_info['name']}")

#Display some basic info aboutthe ageent
print(f"Connected to: {agent_info['name']} - {agent_info['description']}")

#STEP 2: Prepare a task

#Generate unique ID for task using uuid
task_id = str(uuid.uuid4())

#Construct A2A task payload as Python dict
#According to A2a spec, we need to include:
#"id": Unique task ID
# "message": an object with "role" : "user" and list of "parts"
task_payload = {
    "id": task_id,
    "message": {
        "role": "user",
        "parts": [{"text": "What time is it?"}]
    }
}


#STEP 3: Send the task to the agent

#Send an HTTP POST request to tasks/send endpoint of agent
#Use json = so that requests serializes the dict into JSON
response = requests.post(f"{base_url}/tasks/send", json=task_payload)

#If server doesn't return 200 OK, raise error
if response.status_code != 200:
    raise Exception(f"Task failed: {response.text}")

#Parse agents response into python dict
response_data = response.json()

#STEP 4: Display the agents response

#Extract list of messages returned in the response
#Includes both the user's message and the agent's response
messages = response_data.get("messages", [])

#If there are messages, extract and print the agent's response (last message)
if messages:
    final_reply = messages[-1]["parts"][0]["text"] #Text part of agent's response
    print("Agent says:", final_reply)
else:
    #If no messages, notify user
    print("No response from agent")


