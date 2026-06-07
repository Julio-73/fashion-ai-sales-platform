"""Automation Engine Enterprise V1.

Additive module. Provides a rule engine that scans existing data
(customers, pipeline, conversations, orders, inventory, ai-live) and
emits two kinds of side-effects:

* ``automation_tasks``  — actionable items shown in /dashboard/tasks
* ``automation_events`` — immutable audit log for downstream BI

The module is self-contained:

* new tables:  ``automation_rules``, ``automation_tasks``,
  ``automation_events``
* new routes:  ``/automation/...`` (see ``router.py``)
* NO foreign-key writes are performed on any frozen module's tables.
  The engine only reads them.

Public re-exports kept small — callers should import from
``app.modules.automation`` rather than reaching into submodules.
"""
from __future__ import annotations

from app.modules.automation.models import (
    AutomationEvent,
    AutomationRule,
    AutomationTask,
    RULE_001,
    RULE_002,
    RULE_003,
    RULE_004,
    RULE_005,
    RULE_006,
    RULE_007,
    DEFAULT_RULES,
)
from app.modules.automation.schemas import (
    AutomationEventResponse,
    AutomationMetricsResponse,
    AutomationRuleCreate,
    AutomationRuleResponse,
    AutomationRuleUpdate,
    AutomationTaskCreate,
    AutomationTaskResponse,
    AutomationTaskUpdate,
    BoardColumn,
    CalendarEntry,
    CalendarView,
    TaskBoardResponse,
)
from app.modules.automation.service import AutomationService
from app.modules.automation.engine import AutomationRuleEngine
from app.modules.automation.ai import AutomationAIService

__all__ = [
    "AutomationEvent",
    "AutomationRule",
    "AutomationTask",
    "AutomationService",
    "AutomationRuleEngine",
    "AutomationAIService",
    "RULE_001",
    "RULE_002",
    "RULE_003",
    "RULE_004",
    "RULE_005",
    "RULE_006",
    "RULE_007",
    "DEFAULT_RULES",
    "AutomationEventResponse",
    "AutomationMetricsResponse",
    "AutomationRuleCreate",
    "AutomationRuleResponse",
    "AutomationRuleUpdate",
    "AutomationTaskCreate",
    "AutomationTaskResponse",
    "AutomationTaskUpdate",
    "BoardColumn",
    "CalendarEntry",
    "CalendarView",
    "TaskBoardResponse",
]
