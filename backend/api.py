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

class SuggestionRequest(BaseModel):
    text: str

# Endpoint for suggesting the next word in context
@app.post("/suggest_next_word")
async def suggest_next_word(request: SuggestionRequest):
    print(request.text)
    print("Next word suggestion request:", request.text)
    # Use the entire input text to generate a suggestion for the next word
    results = generator(request.text, max_new_tokens=1, num_return_sequences=3)
    suggestions = [result['generated_text'][len(request.text):].strip().split()[0] for result in results]
    return {"suggestions": suggestions}

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

# In-memory storage for messages
# In-memory storage for messages
messages = []
subscribers = []  # List of active connections

# Models
class Message(BaseModel):
    sender: str  # "user" for current user, "other" for other person
    text: str

class ResponseMessage(BaseModel):
    sender: str
    text: str

@app.post("/send_message/")
def send_message(message: Message):
    """
    Adds a new message to the in-memory store.
    """
    if not message.text.strip():
        raise HTTPException(status_code=400, detail="Message text cannot be empty.")
    messages.append(message)
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
    For now, returns arbitrary data.
    """
    print("Received payload:", payload.dict())
    y = payload.dict()
    x = f"""
    {{
        "previous_context": "{y['previous_context']}",
        "user_current_input": "{y['user_current_input']}",
        "context_mode": "Family",
        "button_press": "Blue",
        "suggestions": []
    }}
    """    
    return {"suggestions": Agent.infer(x)}