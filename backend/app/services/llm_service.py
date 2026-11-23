"""Centralized LLM service using Groq API with fallback to mock mode."""
from groq import Groq
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from typing import Optional, Type, TypeVar, Any
import json, hashlib, time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ..config import get_settings
from ..utils.logger import get_logger

logger = get_logger(__name__)
T = TypeVar('T', bound=BaseModel)

class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self._client = None
        self._langchain_llm = None
    
    @property
    def is_demo_mode(self) -> bool:
        return not self.settings.groq_api_key or self.settings.groq_api_key == "your-groq-api-key-here"
    
    def get_langchain_llm(self) -> ChatGroq:
        if not self._langchain_llm and not self.is_demo_mode:
            self._langchain_llm = ChatGroq(
                api_key=self.settings.groq_api_key,
                model=self.settings.groq_model,
                temperature=self.settings.groq_temperature,
                max_tokens=self.settings.groq_max_tokens,
                timeout=60,
            )
        return self._langchain_llm
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def generate(self, system_prompt: str, user_prompt: str, response_model: Optional[Type[T]] = None) -> Any:
        if self.is_demo_mode:
            logger.warning("DEMO MODE: Returning mock LLM response")
            return self._get_demo_response(system_prompt, user_prompt, response_model)
        
        try:
            llm = self.get_langchain_llm()
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
            
            if response_model:
                # Use structured output
                structured_llm = llm.with_structured_output(response_model)
                result = structured_llm.invoke(messages)
                return result
            else:
                result = llm.invoke(messages)
                return result.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def _get_demo_response(self, system_prompt: str, user_prompt: str, response_model=None):
        """Return clearly labeled demo responses."""
        return {"demo": True, "message": "[DEMO MODE] Real LLM response requires GROQ_API_KEY configuration."}
    
    def get_status(self) -> dict:
        return {
            "provider": "groq",
            "model": self.settings.groq_model,
            "is_demo_mode": self.is_demo_mode,
            "configured": not self.is_demo_mode
        }

llm_service = LLMService()
