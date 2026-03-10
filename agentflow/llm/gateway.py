# agentflow/llm/gateway.py
"""Unified LLM gateway using LiteLLM - defaults to Groq (Grok/Llama3) with DB memory."""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import litellm
from litellm import acompletion, completion

from agentflow.core.config import get_settings

import structlog

logger = structlog.get_logger(__name__)
litellm.drop_params = True

settings = get_settings()

# Set Groq API key for LiteLLM
if settings.groq_api_key:
    os.environ["GROQ_API_KEY"] = settings.groq_api_key
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.anthropic_api_key:
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key


class DBMemoryManager:
    """Manages conversation history stored in the database for LLM context."""

    def __init__(self, session_id: str, window_size: int = 20):
        self.session_id = session_id
        self.window_size = window_size
        self._conversation_id: Optional[str] = None

    def _get_db(self):
        from agentflow.core.database import SessionLocal
        return SessionLocal()

    def get_or_create_conversation(self) -> str:
        """Get existing conversation or create a new one."""
        if self._conversation_id:
            return self._conversation_id
        from agentflow.core.database import ConversationModel
        db = self._get_db()
        try:
            conv = db.query(ConversationModel).filter(
                ConversationModel.session_id == self.session_id
            ).order_by(ConversationModel.created_at.desc()).first()
            if not conv:
                conv = ConversationModel(
                    id=str(uuid.uuid4()),
                    session_id=self.session_id,
                    created_at=datetime.utcnow()
                )
                db.add(conv)
                db.commit()
                db.refresh(conv)
            self._conversation_id = conv.id
            return conv.id
        finally:
            db.close()

    def load_messages(self) -> List[Dict]:
        """Load recent messages from DB for context window."""
        from agentflow.core.database import MessageModel, ConversationModel
        conv_id = self.get_or_create_conversation()
        db = self._get_db()
        try:
            msgs = db.query(MessageModel).filter(
                MessageModel.conversation_id == conv_id
            ).order_by(MessageModel.created_at.desc()).limit(self.window_size).all()
            msgs.reverse()
            return [{"role": m.role, "content": m.content} for m in msgs]
        finally:
            db.close()

    def save_message(self, role: str, content: str) -> None:
        """Persist a message to the DB."""
        from agentflow.core.database import MessageModel
        conv_id = self.get_or_create_conversation()
        db = self._get_db()
        try:
            msg = MessageModel(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role=role,
                content=content,
                created_at=datetime.utcnow()
            )
            db.add(msg)
            db.commit()
        finally:
            db.close()

    def clear(self) -> None:
        """Clear all messages for this session."""
        from agentflow.core.database import MessageModel, ConversationModel
        conv_id = self.get_or_create_conversation()
        db = self._get_db()
        try:
            db.query(MessageModel).filter(
                MessageModel.conversation_id == conv_id
            ).delete()
            db.commit()
        finally:
            db.close()


class ModelGateway:
    """Routes LLM calls through LiteLLM. Default model is Groq Llama3."""

    def __init__(self, model: Optional[str] = None, session_id: Optional[str] = None):
        self._settings = get_settings()
        self._primary_model = model or self._settings.active_llm_model
        self._fallback_chain = self._build_fallback_chain()
        self.memory: Optional[DBMemoryManager] = None
        if session_id and self._settings.enable_memory:
            self.memory = DBMemoryManager(
                session_id=session_id,
                window_size=self._settings.memory_window_size
            )

    def _build_fallback_chain(self) -> list[str]:
        chain = [self._primary_model]
        # Add fallbacks if primary fails
        fallbacks = [
            "groq/llama3-8b-8192",
            "groq/mixtral-8x7b-32768",
            "groq/gemma2-9b-it",
        ]
        for m in fallbacks:
            if m != self._primary_model:
                chain.append(m)
        return chain

    async def achat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        target = model or self._primary_model
        attempt_chain = [target] + [m for m in self._fallback_chain if m != target]

        # Build full message list with memory
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        if self.memory:
            full_messages.extend(self.memory.load_messages())
        full_messages.extend(messages)

        # Save user messages to memory
        if self.memory:
            for msg in messages:
                if msg["role"] == "user":
                    self.memory.save_message(msg["role"], msg["content"])

        last_error = None
        for m in attempt_chain:
            try:
                response = await acompletion(
                    model=m,
                    messages=full_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                result = response.choices[0].message.content
                # Save assistant reply to memory
                if self.memory:
                    self.memory.save_message("assistant", result)
                logger.info("llm_response", model=m, tokens=response.usage.total_tokens if response.usage else None)
                return result
            except Exception as e:
                last_error = e
                logger.warning("llm_fallback", model=m, error=str(e))
        raise RuntimeError(f"All LLM models failed. Last error: {last_error}")

    def chat(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Synchronous chat."""
        target = model or self._primary_model
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        if self.memory:
            full_messages.extend(self.memory.load_messages())
        full_messages.extend(messages)

        if self.memory:
            for msg in messages:
                if msg["role"] == "user":
                    self.memory.save_message(msg["role"], msg["content"])

        response = completion(
            model=target,
            messages=full_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        result = response.choices[0].message.content
        if self.memory:
            self.memory.save_message("assistant", result)
        return result


def get_gateway(model: Optional[str] = None, session_id: Optional[str] = None) -> ModelGateway:
    """Factory function to get a ModelGateway instance."""
    return ModelGateway(model=model, session_id=session_id)
