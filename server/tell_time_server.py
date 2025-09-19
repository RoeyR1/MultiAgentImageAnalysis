from flask import Flask, jsonify, request

from datetime import datetime

app = Flask(__name__)


#Define endpoint: Agent Card (Discovery phase)
@app.route('/.well-known/agent.json', methods=['GET']) #path required by protocol
def agent_card(): # get metadata about agnt in json format
    return jsonify({
        "name": "TellTimeAgent",
        "description": "Tells the current time when asked.",
        "url": "http://localhost:5000", #Where this agent is hosted
        "version": "1.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False
        }
    })


#Endpoint for Task Handling tasks/send
#Main endpoint that A2A clients use to send a task to the agent
@app.route('/tasks/send', methods=['POST'])
def handle_task():
    try:
        #prase incoming json payload into a python dict
        task = request.get_json()
        #Extract task ID from payload
        task_id = task.get("id")#Uniquely identfiies task in A2A protocol
        #extract user message text from first message part (Text part)
        #A2A represents messages as a list of parts, (Text part, file part, data part)
        user_message = task["message"]["parts"][0]["text"]
    #If request doesnt match expected structure, return error
    except (KeyError,IndexError,TypeError):
        return jsonify({"error": "Invalid task format"}), 400
    #Generate a response to the user's message
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #Build agents response message text
    reply_text = f"The current time is {current_time}"
    
    #Return properly formatted A2A task response(JSON)
    #This response includes orgiinal message and a new message from the agent
    return jsonify({
        "id": task_id, #Reuse the same task ID in response
        "status": {"state": "completed"}, #Mark task as completed
        "messages": [
            task["message"], #Include original message from user for context
            {
                "role": "agent", # Agent role b/c it is a message from the agent
                "parts": [{"text": reply_text}] #Reply contents in text format(Included in Text Part of message)
            }
        ]
    })
    

if __name__ == '__main__':
    app.run(port=5000)