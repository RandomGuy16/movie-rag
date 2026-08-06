from typing import Optional, List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., description="The main text prompt for the model.")
    model: Optional[str] = Field("gemini-3.5-flash", description="Target GenAI model identifier to use.")
    system: Optional[str] = Field(None, description="System message to define the model's behavior/role.")
    temperature: Optional[float] = Field(None, description="Controls response creativity. Higher means more random.")
    top_p: Optional[float] = Field(None, description="Nucleus sampling limit. 1.0 means consider all tokens.")
    top_k: Optional[int] = Field(None, description="Top-k sampling. Limits choices to top K tokens.")
    num_predict: Optional[int] = Field(None, description="Max tokens to generate in the response.")
    repeat_penalty: Optional[float] = Field(None, description="Applies penalty to repeated tokens.")
    stream: bool = Field(False, description="Whether to stream response tokens back dynamically.")
    context: Optional[List[int]] = Field(None, description="Conversation context tokens from previous turns for memory.")
    previous_interaction_id: Optional[str] = Field(None, description="Interaction context ID from previous turns")
