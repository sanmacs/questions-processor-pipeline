from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, TypeVar, Type, Dict, Any
from openai import OpenAI
import json


class Role(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message:
    def __init__(self,
                 role: Role,
                 content: str, 
                 image: str = None):
        self.role = role
        self.content = content
        self.image = image

    def format_message(self):
        if self.image is None:
            return {"role": self.role.value, "content": self.content}
        elif self.image is not None:
            return {"role": self.role.value, 
                "content": [
                    {"type": "text", "text": self.content},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{self.image}"}}
                ]}

class LLM:
    def __init__(self, api_key, model_name="gpt-4o-2024-08-06"):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

        self.input_tokens = 0
        self.output_tokens = 0

    def update_token_usage(self, response):
        self.input_tokens += response.usage.prompt_tokens
        self.output_tokens += response.usage.completion_tokens

    def generate_response(self,
                          system_prompt: str,
                          messages: List[Message],
                          response_format = None):
        messages = [message.format_message() for message in messages]
        messages = [{"role": Role.SYSTEM.value, "content": system_prompt}] + messages
        if response_format:
            response = self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=messages,
                response_format=response_format
            )

            self.update_token_usage(response)
            return response.choices[0].message.parsed
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )

            self.update_token_usage(response)
            return response.choices[0].message.content
