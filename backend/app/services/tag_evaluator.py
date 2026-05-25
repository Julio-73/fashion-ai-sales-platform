"""Extensible tag evaluation framework for automatic customer tagging.

This module defines the interface for tag evaluators. Concrete evaluators
can be plugged in later (including AI-powered ones) without modifying
the core bridge logic.

Currently ships with a NoOpTagEvaluator that performs no classification.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TagEvaluationContext:
    empresa_id: UUID
    customer_id: UUID
    conversation_id: UUID
    message_content: str
    message_sender: str
    conversation_status: str
    lead_status: str
    existing_tags: tuple[str, ...]


class TagEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, context: TagEvaluationContext) -> list[str]:
        ...


class NoOpTagEvaluator(TagEvaluator):
    async def evaluate(self, context: TagEvaluationContext) -> list[str]:
        return []


DEFAULT_EVALUATOR: TagEvaluator = NoOpTagEvaluator()
