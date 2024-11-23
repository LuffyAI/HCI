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
from ai import ContextAgent
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()
Agent = ContextAgent()

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


class SuggestionRequest(BaseModel):
    text: str

# Model for updating the context mode
class ContextModeRequest(BaseModel):
    mode: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()


@app.websocket("/ws/suggest_next_word/")
async def websocket_suggest_next_word(websocket: WebSocket):
    """
    WebSocket endpoint for real-time 'suggest next word' feature.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for a message from the client
            data = await websocket.receive_json()
            text = data.get("text", "")

            if not text.strip():
                await websocket.send_json({"error": "Text cannot be empty."})
                continue

            print("Next word suggestion request:", text)

            # Generate suggestions
            results = generator(text, max_new_tokens=1, num_return_sequences=3)
            suggestions = [result['generated_text'][len(text):].strip().split()[0] for result in results]

            # Send suggestions back to the client
            await websocket.send_json({"suggestions": suggestions})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket disconnected: suggest_next_word")
    except Exception as e:
        print(f"Error in WebSocket (suggest_next_word): {e}")
        await websocket.close(code=1011)


@app.websocket("/ws/suggest_word_completion/")
async def websocket_suggest_word_completion(websocket: WebSocket):
    """
    WebSocket endpoint for real-time word completion suggestions.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for a message from the client
            data = await websocket.receive_json()
            text = data.get("text", "")

            if not text.strip():
                await websocket.send_json({"error": "Text cannot be empty."})
                continue

            print("Word completion request:", text)

            # Generate completions
            results = generator(text, max_new_tokens=3, num_return_sequences=3)
            suggestions = [result['generated_text'][len(text):].strip().split()[0] for result in results]

            # Send completions back to the client
            await websocket.send_json({"suggestions": suggestions})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket disconnected: suggest_word_completion")
    except Exception as e:
        print(f"Error in WebSocket (suggest_word_completion): {e}")
        await websocket.close(code=1011)


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
    read: bool = False

class ResponseMessage(BaseModel):
    sender: str
    text: str

@app.post("/send_message/")
def send_message(message: Message):
    """
    Adds a new message to the in-memory store.
    """
    print(message)
    if not message.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty.")
    messages.append(message)
    return {"status": "Message sent successfully!"}

@app.websocket("/ws/get_messages/")
async def websocket_get_messages(websocket: WebSocket):
    """
    WebSocket endpoint for real-time message updates.
    Sends only unread messages and marks them as read after sending.
    """

    print(messages)

    await manager.connect(websocket)
    try:
        while True:
            # Filter unread messages
            unread_messages = [message for message in messages if not message.read]

            if unread_messages:
                # Mark messages as read
                for message in unread_messages:
                    message.read = True

                # Send unread messages to the client
                await websocket.send_json([message.dict() for message in unread_messages])

            # Sleep or wait to simulate periodic updates
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("WebSocket disconnected")

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
    print("Received payload:", payload.dict())
    y = payload.dict()
    x = f"""
    {{
        "previous_context": "{y['previous_context']}",
        "user_current_input": "{y['user_current_input']}",
        "context_mode": "{context_mode}",
        "button_press": "Blue",
        "suggestions": []
    }}
    """    
    payload = {"suggestions": Agent.infer(x)}
    print("Payload:", payload)
    return payload 



@app.post("/checkmark_click/")
def handle_checkmark_click(payload: LightbulbPayload):
    """
    Handles the checkmark click and processes the payload.
    Calls OpenAI to simulate the contextually aware responses.
    """
    print("Received payload:", payload.dict())
    y = payload.dict()
    x = f"""
    {{
        "previous_context": "{y['previous_context']}",
        "user_current_input": "{y['user_current_input']}",
        "context_mode": "{context_mode}",
        "button_press": "Yellow",
        "suggestions": []
    }}
    """    
    payload = {"suggestions": Agent.infer(x)}
    print("Payload:", payload)
    return payload 