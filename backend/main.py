from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request and response models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    new_message: str

class ChatResponse(BaseModel):
    message: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="API key not configured")

        # Configure Gemini API
        genai.configure(api_key=api_key)

        # Initialize the Gemini model
        model = genai.GenerativeModel("gemini-1.5-flash")  # Use 'gemini-1.5-flash' or latest available

        # Prepare messages as list of content parts
        conversation_history = []
        for msg in request.messages:
            conversation_history.append({"role": msg.role, "parts": [msg.content]})

        # Append the new message
        conversation_history.append({"role": "user", "parts": [request.new_message]})

        # Generate response
        response = model.generate_content(
            contents=conversation_history,
            generation_config=GenerationConfig(
                max_output_tokens=150
            )
        )

        # Extract response
        if not response or not response.text:
            raise HTTPException(status_code=500, detail="No response returned by Gemini API")

        return ChatResponse(message=response.text.strip())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Gemini API: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
