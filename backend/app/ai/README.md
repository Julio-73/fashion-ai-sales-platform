# AI Conversational Engine - AI Sales Agent SaaS

## Architecture Overview

The AI Conversational Engine is the core intelligence layer of the platform. It processes incoming messages through a modular pipeline to produce structured, context-aware responses.

### Processing Pipeline

```
Mensaje cliente
       ↓
 IntentClassifierService    (keyword/scoring-based intent detection)
       ↓
 ConversationContextBuilder (customer profile, history, stage)
       ↓
 SalesConversationRulesEngine (business rules & sales actions)
       ↓
 AIResponseOrchestrator     (combines all → structured response)
       ↓
Respuesta estructurada
```

## Module Responsibilities

### `classifiers/` — IntentClassifierService
- Detects user intent using keyword matching and scoring
- Supports: pricing, purchase_intent, negotiation, delivery, greeting, support, return_request, product_question, sizing
- No ML dependency — rule-based for Phase 1, extensible to ML in future

### `context/` — ConversationContextBuilder
- Builds context from customer profile, lead score, tags, recent messages, conversation status, product interests
- Currently returns stub data; will be wired to real DB in next phase
- Multi-tenant aware (empresa_id isolation)

### `rules/` — SalesConversationRulesEngine
- Applies business rules to determine the appropriate sales action
- Actions: follow_up, escalate, suggest_discount, suggest_upsell, suggest_cross_sell, no_action
- Fully configurable and extensible

### `orchestrators/` — AIResponseOrchestrator
- Orchestrates the full pipeline: classifier → context → rules → response
- ResponseTemplateBuilder provides template-based responses (no GPT yet)
- Prepares structured OrchestratorResponse with all metadata

### `prompts/`
- Enterprise prompt templates ready for future OpenAI integration
- Files: sales_prompt.txt, support_prompt.txt, recovery_prompt.txt, upsell_prompt.txt

### `services/` — AIService
- Facade service that wires all components together
- Exposes three operations: classify, build_context, respond

### `schemas/`
- Pydantic models for all request/response types
- Enums for: IntentType, ConversationStage, SalesAction, ReplyType

## API Endpoints

All endpoints require JWT authentication and are protected by permission checks.

| Method | Path | Permission | Description |
|--------|------|-----------|-------------|
| POST | /api/v1/ai/classify | ai:classify | Classify a message intent |
| POST | /api/v1/ai/context | ai:context | Build conversation context |
| POST | /api/v1/ai/respond | ai:respond | Full orchestration pipeline |

## Multi-Tenant Isolation

- All endpoints extract `empresa_id` from the JWT token via `TenantContext`
- All services receive `empresa_id` and use it for data scoping
- Permissions are role-based (`owner`, `admin`, `sales_agent`)

## Extensibility

The architecture is designed to be extended in future phases:

1. **Real GPT integration** — Replace template builder with LLM calls
2. **WhatsApp/Instagram/Facebook** — Add channel adapters before the classifier
3. **Multiple AI agents** — Each agent type gets its own classifier/rules pipeline
4. **Vector DB / embeddings** — Enhance context builder with semantic search
5. **Workflow automation** — Add n8n or custom workflow engine after the orchestrator

## Development Status

- [x] Phase 1: Intent Classifier (rule-based)
- [x] Phase 2: Context Builder (stub data)
- [x] Phase 3: Sales Rules Engine
- [x] Phase 4: Response Orchestrator (templates)
- [x] Phase 5: Prompt System Foundation
- [x] Phase 6: API Endpoints
- [x] Phase 7: Tests
- [ ] Phase 8: Real DB integration for context
- [ ] Phase 9: OpenAI integration
- [ ] Phase 10: Channel adapters (WhatsApp, etc.)
