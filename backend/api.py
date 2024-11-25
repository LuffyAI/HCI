# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import pipeline
import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import asyncio
from datetime import datetime
from ai import ContextAgent

app = FastAPI()
Agent = ContextAgent()

all_suggestions = 0

recent_smart_suggestions = {}

# Allow CORS for all origins (adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend URL here for production
    allow_credentials=True,
    allow_methods=["*"],  # Or ["POST"]
    allow_headers=["*"],
)

generator = pipeline("text-generation", model="gpt2-medium")

# In-memory storage for messages
messages = []
subscribers = []  # List of active connections
context_mode = "Family"  # Default context mode
suggestion_history = []




class SuggestionRequest(BaseModel):
    text: str

class SuggestionStat(BaseModel):
    suggestion: str
    used: bool  # Whether the suggestion was used in the message


# Model for updating the context mode
class ContextModeRequest(BaseModel):
    mode: str


@app.post("/track_suggestion/")
def track_suggestion(stat: SuggestionStat):
    """
    Tracks whether a suggestion was used in the user's message.
    """
    global suggestion_history
    suggestion_history.append(stat.dict())
    return {"status": "Suggestion tracked successfully!"}

@app.get("/get_suggestion_stats/")
def get_suggestion_stats():
    """
    Returns statistics on suggestion usage.
    """
    global suggestion_history
    global all_suggestions
    total_suggestions = len(suggestion_history)
    used_suggestions = sum(1 for stat in suggestion_history if stat["used"])
    unused_suggestions = total_suggestions - used_suggestions

    return {
        "total_suggestions": total_suggestions,
        "total_number_of_suggestions": all_suggestions, 
        "history": suggestion_history,
    }

@app.get("/get_context_mode/")
def get_context_mode():
    """
    Returns the current context mode as the first element in the list of contexts.
    """
    all_contexts = ["Family", "Professional", "Friends"]

    # Ensure the current context mode is the first element
    contexts = [context_mode] + [ctx for ctx in all_contexts if ctx != context_mode]

    return {"contexts": contexts}


@app.post("/set_context_mode/")
def set_context_mode(request: ContextModeRequest):
    """
    Sets a new context mode.
    """
    global context_mode
    if not request.mode.strip():
        raise HTTPException(status_code=400, detail="Context mode cannot be empty.")
    context_mode = request.mode
    return {"status": "Context mode updated successfully!", "new_context_mode": context_mode}

# Endpoint for suggesting the next word in context
@app.post("/suggest_next_word")
async def suggest_next_word(request: SuggestionRequest):
    print(request.text)
    print("Next word suggestion request:", request.text)
    # Use the entire input text to generate a suggestion for the next word
    results = generator(request.text, max_new_tokens=1, num_return_sequences=3)
    suggestions = [result['generated_text'][len(request.text):].strip().split()[0] for result in results]
    return {"suggestions": suggestions}

@app.delete("/delete_messages/")
def delete_messages():
    """
    Deletes all messages from the in-memory store.
    """
    global messages
    messages.clear()
    return {"status": "All messages have been deleted successfully!"}

# Endpoint for suggesting word completions
@app.post("/suggest_word_completion")
async def suggest_word_completion(request: SuggestionRequest):
    print(request.text)
    print("Word completion request:", request.text)
    # Use the partial word to generate possible completions
    results = generator(request.text, max_new_tokens=3, num_return_sequences=3)
    suggestions = [result['generated_text'][len(request.text):].strip().split()[0] for result in results]
    return {"suggestions": suggestions}

# New endpoint for OpenAI API
@app.post("/generate_suggestion")
async def generate_suggestion(request: SuggestionRequest):
    try:
        print(request.text)
        response = openai.Completion.create(
            engine="text-davinci-003",  # Adjust engine as needed
            prompt=request.text,
            max_tokens=10,  # Adjust based on the desired suggestion length
            n=1,
            stop=None,
            temperature=0.7,
        )
        suggestion = response.choices[0].text.strip()
        print(suggestion)
        return {"suggestion": suggestion}
    except Exception as e:
        return {"error": str(e)}


# Models
class Message(BaseModel):
    sender: str  # "user" for current user, "other" for other person
    text: str

class ResponseMessage(BaseModel):
    sender: str
    text: str
    timestamp: str

@app.post("/send_message/")
def send_message(message: Message):
    """
    Adds a new message to the in-memory store.
    """
    global suggestion_history
    global recent_smart_suggestions

    if not message.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty.")
    
    message_with_timestamp = {
        "sender": message.sender,
        "text": message.text,
        "timestamp": datetime.utcnow().isoformat()  # Generate current UTC time in ISO format
    }
    messages.append(message_with_timestamp)

    # Check if the message text contains any suggestions

    print("Recent Smart Suggestions:", recent_smart_suggestions)

    if recent_smart_suggestions:
        print("Recent Smart Suggestions:", recent_smart_suggestions)
        for suggestion, used in recent_smart_suggestions.items():
            if suggestion in message.text:
                track_suggestion(SuggestionStat(suggestion=suggestion, used=True))
                

    return {"status": "Message sent successfully!"}

@app.get("/get_messages/")
def get_messages(start_index: int = 0):
    """
    Returns all messages starting from a specific index.
    """
    return messages[start_index:]


# Models
class LightbulbPayload(BaseModel):
    previous_context: str
    user_current_input: str
    context_mode: str
    button_press: str
    suggestions: list

@app.post("/lightbulb_click/")
def handle_lightbulb_click(payload: LightbulbPayload):
    """
    Handles the lightbulb click and processes the payload.
    Calls OpenAI to simulate the contextually aware responses.
    """
    global recent_smart_suggestions
    global all_suggestions
    print("Received payload:", payload.dict())
    y = payload.dict()
    x = f"""
    You are responding to the 'Other User'. You are the 'USER'.
    {{
        "previous_context": "{y['previous_context']}",
        "user_current_input": "{y['user_current_input']}",
        "context_mode": "{context_mode}",
        "button_press": "Blue",
        "suggestions": []
    }}
    """    
    options = Agent.infer(x) 
    all_suggestions += len(options)


    for x in options:
        recent_smart_suggestions[x]= False
    print("Recent Smart Suggestions:", recent_smart_suggestions)


    payload = {"suggestions": options}


    return payload 



@app.post("/checkmark_click/")
def handle_checkmark_click(payload: LightbulbPayload):
    """
    Handles the checkmark click and processes the payload.
    Calls OpenAI to simulate the contextually aware responses.
    """
    global recent_smart_suggestions
    global suggestion_history
    global all_suggestions
    print("Received payload:", payload.dict())
    y = payload.dict()
    x = f"""
    You are responding to the 'Other User'. You are the 'USER'.
    {{
        "previous_context": "{y['previous_context']}",
        "user_current_input": "{y['user_current_input']}",
        "context_mode": "{context_mode}",
        "button_press": "Yellow",
        "suggestions": []
    }}
    """ 
    options = Agent.infer(x) 
    all_suggestions += len(options)



    for x in options:
        recent_smart_suggestions[x]= False
    print("Recent Smart Suggestions:", recent_smart_suggestions)


    payload = {"suggestions": options}




    print("Payload:", payload)
    return payload 