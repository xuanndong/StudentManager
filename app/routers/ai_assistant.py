from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from google import genai
import os
from dotenv import load_dotenv

from app.dependencies import get_current_user

load_dotenv()

router = APIRouter(prefix=os.getenv("API_V1_STR", "/api/v1") + "/ai", tags=['AI Assistant'])


class ChatRequest(BaseModel):
    message: str
    context: str | None = None


class ChatResponse(BaseModel):
    response: str
    error: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_request: ChatRequest,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    AI Assistant for students, teachers, and advisors
    Helps with academic questions, course information, and general guidance
    """
    try:
        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI service not configured"
            )
        
        client = genai.Client(api_key=api_key)
        
        # Build context-aware prompt
        user_role = current_user.get("role", "STUDENT")
        user_name = current_user.get("full_name", "User")
        
        system_prompt = f"""You are an AI assistant for a Student Management System.
You are helping {user_name}, who is a {user_role}.

Your role:
- For STUDENTS: Help with academic questions, course information, study tips, grade understanding
- For TEACHERS: Assist with course management, grading guidelines, student engagement tips
- For CVHT (Academic Advisors): Help with student monitoring, academic planning, intervention strategies
- For ADMIN: Provide system management guidance

Guidelines:
- Be helpful, friendly, and professional
- Keep responses concise and actionable
- If you don't know something specific about the system, be honest
- Encourage users to contact administrators for system-specific issues
- Use Vietnamese when appropriate, but can respond in English

User's question: {chat_request.message}
"""
        
        if chat_request.context:
            system_prompt += f"\n\nAdditional context: {chat_request.context}"
        
        # Generate response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt
        )
        
        return ChatResponse(response=response.text, error=None)
        
    except Exception as e:
        return ChatResponse(
            response="Xin lỗi, tôi đang gặp sự cố kỹ thuật. Vui lòng thử lại sau.",
            error=str(e)
        )


@router.get("/health")
async def check_ai_health(current_user: dict = Depends(get_current_user)):
    """Check if AI service is available"""
    api_key = os.getenv("GEMINI_API_KEY")
    return {
        "available": bool(api_key),
        "model": "gemini-2.5-flash"
    }
