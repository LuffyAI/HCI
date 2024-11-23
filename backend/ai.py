"""Current file being used
Prompts need further optimization!
Multiple CHoice and True False questions are working fine.
Fill in the blank and short answer questions are not working as expected.
Image questions are not fully implemented, but the structure is there.
"""

from dotenv import load_dotenv
import os
import json
from openai import OpenAI
import time
import atexit
import base64
from pydantic import BaseModel


class Suggestion(BaseModel):
    suggestion:str

class Suggestions(BaseModel):
    Response: list[Suggestion]


response_format={
           'type': 'json_schema',
           'json_schema': 
              {
                "name":"whocares", 
                "schema": Suggestions.model_json_schema()
              }
         } 


system_prompt= """

### OBJECTIVE
You are an advanced, contextually aware predictive text suggestion system from the future. 
Your role is to provide only suggestions in the specified json format, adapting to various user contexts and modes with precision. 
After the next message, you’ll respond only with context-specific suggestions."

### CONTEXT DEFINITION
{
  "previous_context": "{Provide any previous conversation or text context here}",
  "user_current_input": "{The user's current incomplete or draft input}",
  "context_mode": "{Professional, Friend, or Family}",
  "button_press": "{Yellow or Blue}"
  "suggestions": "{Provide the suggestions based on the context and button press}"
}
### CONTEXT MODES
Professional: Remain extremely formal, respectful, and avoid sounding overly casual.
Friend: Be friendly, informal, and expressive with emojis; use abbreviations when appropriate.
Family: Address family members by their roles, blending a mix of casual and respectful tone.

### BUTTON MODES
YELLOW: Proofread the USER CURRENT INPUT, offering any grammatical corrections or style improvements.
BLUE: Provide four predictive text suggestions for what might come next, based on the PREVIOUS CONTEXT and USER CURRENT INPUT.

### Who do you respond to?
You are helping the person called 'USER' and responding to 'OTHER USER'

=============================================
Example 1: Professional Mode + Yellow Button Press
{
  "previous_context": "Please confirm your availability for the meeting on Friday.",
  "user_current_input": "I am happy to",
  "context_mode": "Professional",
  "button_press": "Yellow",
  "suggestions": ["I am happy to confirm my availability for the meeting on Friday."]
}
=============================================
Example 2: Friend Mode + Blue Button Press
{
  "previous_context": "Hey! Do you want to meet up for coffee later?",
  "user_current_input": "Sure, let’s",
  "context_mode": "Friend",
  "button_press": "Blue",
  "suggestions": [
    "Sure, let’s meet around noon! 😊",
    "Sure, let’s plan for 2 PM?",
    "Sure, let’s grab a table at our usual spot!",
    "Sure, let’s make it a coffee and chat date!"
  ]
}
============================================
Example 3: Family Mode + Yellow Button Press
{
  "previous_context": "Are you joining us for dinner tonight?",
  "user_current_input": "Yes, I’ll be there around 7",
  "context_mode": "Family",
  "button_press": "Yellow",
  "suggestions": ["Yes, I’ll be there around 7 p.m."]
}
=============================================
Example 4: Professional Mode + Blue Button Press
{
  "previous_context": "Following up on our last email, we need to finalize the project details.",
  "user_current_input": "Regarding the project,",
  "context_mode": "Professional",
  "button_press": "Blue",
  "suggestions": [
    "Regarding the project, I’ll have the report ready by Friday.",
    "Regarding the project, could we schedule a meeting?",
    "Regarding the project, here are some points I’d like to address.",
    "Regarding the project, I’d appreciate your feedback on my proposal."
  ]
}
"""

structured_output = { "suggestions:" "[]"}



class ContextAgent:
    def __init__(self) -> None:
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.initialize_assistant
        self.start_context_thread("Remember to always send responses in JSON")

        # Register the cleanup function to be called on exit
        atexit.register(self.cleanup)

    def start_context_thread(self, query):
        """Associates each question with a thread"""
        messages = [
            {
                "role": "user",
                "content": f"""
                {query}
                """
            }
        ]
        thread = self.client.beta.threads.create(messages=messages)
        self.thread = thread
        print(f"Created the thread':",thread.id)


    def infer(self, student_message):
       
        print(student_message)

        try:
            message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=student_message)
        
            run = self.client.beta.threads.runs.create_and_poll(thread_id=self.thread.id, assistant_id=self.assistant.id, temperature=0)
            run_status = self.client.beta.threads.runs.retrieve(thread_id=self.thread.id,run_id=run.id)

            while run_status.status != 'completed':
                print("Job Status :", run_status.status)
                print("Waiting a few seconds to retieve ",self.thread.id,"...")
                time.sleep(2)
            print("Done waiting!")
            # This retrieves the list of messages generated within the thread. The latest response is index[0] of messages
            messages = list(self.client.beta.threads.messages.list(thread_id=self.thread.id, run_id=run.id))
            message_content = messages[0].content[0].text
            print(student_message)
            print("\n")
            print("AI REPLY:", message_content.value)
            print("\n")
            data = json.loads(message_content.value)
            suggestions = [item['suggestion'] for item in data.get('Response', [])]
            return suggestions
        except Exception as e:
            print("Error in infer:", e) 
    
             
    @property
    def initialize_assistant(self):
        """Initializes the AI Assistant"""
        self.assistant = self.client.beta.assistants.create(
            name="OverClock AI Assistant - A Tutor for Building Computers",
            instructions=system_prompt,
            model="gpt-4o-2024-08-06",
            temperature=0.4,
            response_format=response_format,
        )
        print("Created the Assistant:", self.assistant.id)

    @property
    def delete_assistant_and_thread(self):
        """Deletes the AI Assistant"""
        self.client.beta.assistants.delete(self.assistant.id)
        print("Deleted the Assistant:", self.assistant.id)

    def cleanup(self):
        """Cleanup function to delete the assistant on exit"""
        for x in range(0,3):
          try:
            time.sleep(5)
            if hasattr(self, 'assistant') and self.assistant:
                self.delete_assistant_and_thread
            break
          except Exception as e:
                print("Error in cleanup:", e)

x = """
  {
  "previous_context": "Hello dear, how's it going! Could you pick up the eggs?",
  "user_current_input": "",
  "context_mode": "Family",
  "button_press": "Blue",
  "suggestions": [],
}
"""






"""
## Call the Computer Vision API to handle image questions
## Store this information student_progress under previous tries
progress = print(tutor.call_computerVision("label.png"))
"""


"""
question_data = {
                    "activity": "Troubleshooting",
                    "type": "fillInBlank",
                    "question": "Your PC does not power on. The first component you should check is the ___ supply.",
                    "hint": "This component provides power to the entire system.",
                    "answer": "power"
     }
    
student_progress = {
        "answer_status": "Unanswered",
        "Attempts": 2,
        "Previous Tries": {"Power Supply": "Incorrect", "PSU": "Incorrect"},
}
query = "Why is this wrong?"
"""

"""
question_data = {
                    "activity": "Functionality",
                    "type": "multipleChoice",
                    "question": "Which component acts as the brain of the computer, processing all the instructions?",
                    "options": ["CPU", "GPU", "RAM", "SSD"],
                    "hint": "Think of the part responsible for carrying out commands and calculations.",
                    "answer": "CPU"
    }


query = "Why is this right?"

student_progress = {
        "answer_status": "Answered",
        "Attempts": 1,
        "Previous Tries": {"CPU":"Correct"},
    }
"""

"""
question_data = {
                    "activity": "Functionality",
                    "type": "multipleChoice",
                    "question": "Which component acts as the brain of the computer, processing all the instructions?",
                    "options": ["CPU", "GPU", "RAM", "SSD"],
                    "hint": "Think of the part responsible for carrying out commands and calculations.",
                    "answer": "CPU"
    }


query = "I don't understand this!"

student_progress = {
        "answer_status": "Unanswered",
        "Attempts": 1,
        "Previous Tries": {"GPU": "Incorrect"},
    }

tutor.start_question_thread(query=query, question=question_data['question'])
tutor.infer(question_data, query, student_progress)
"""



