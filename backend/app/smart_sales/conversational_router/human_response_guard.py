import re
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class RepetitionStats:
    catalog_repetition_score: float = 0.0
    structural_repetition_score: float = 0.0
    cta_repetition_score: float = 0.0
    is_blocked: bool = False
    block_reason: str = ""

    @property
    def total_score(self) -> float:
        return max(self.catalog_repetition_score, self.structural_repetition_score, self.cta_repetition_score)


_conversation_history: dict[str, list[str]] = defaultdict(list)
_conversation_catalog_count: dict[str, int] = defaultdict(int)
_conversation_structures: dict[str, list[str]] = defaultdict(list)
_conversation_cta_count: dict[str, int] = defaultdict(int)

CATALOG_PHRASES: list[str] = [
    "mira estas", "te recomiendo", "tenemos", "opciones",
    "modelos", "prendas", "te muestro", "disponibles",
    "catálogo", "colección", "productos",
]

CTA_PHRASES: list[str] = [
    "quieres ver más", "te interesa", "te gusta", "te parece",
    "qué opinas", "te llamó la atención", "te ayudo con",
]

STRUCTURE_PATTERNS: list[str] = [
    r"\b(?:mira|te recomiendo|tenemos)\s+(?:est[eaos]|estas)\s",
    r"\b(?:quieres|te gustaría)\s+(?:ver|conocer|saber)\s",
    r"\b(?:talla|color)\s*(?::|disponibles)",
]


class HumanResponseGuard:
    def record_response(self, conversation_id: str, response: str) -> None:
        _conversation_history[conversation_id].append(response)

        cat_count = sum(1 for p in CATALOG_PHRASES if p in response.lower())
        if cat_count >= 2:
            _conversation_catalog_count[conversation_id] += 1

        for sp in STRUCTURE_PATTERNS:
            if re.search(sp, response.lower()):
                _conversation_structures[conversation_id].append(sp)

        cta_count = sum(1 for c in CTA_PHRASES if c in response.lower())
        if cta_count >= 1:
            _conversation_cta_count[conversation_id] += 1

    def check_response(self, conversation_id: str, candidate: str, last_n: int = 3) -> RepetitionStats:
        stats = RepetitionStats()

        history = _conversation_history.get(conversation_id, [])
        recent = history[-last_n:] if history else []

        # structural repetition
        for sp in STRUCTURE_PATTERNS:
            if re.search(sp, candidate.lower()):
                existing = [r for r in recent if re.search(sp, r.lower())]
                if existing:
                    stats.structural_repetition_score = min(1.0, stats.structural_repetition_score + 0.4)
                    stats.block_reason = "Estructura repetitiva"

        # catalog overuse
        cat_count = _conversation_catalog_count.get(conversation_id, 0)
        if cat_count >= 2:
            cand_cat = sum(1 for p in CATALOG_PHRASES if p in candidate.lower())
            if cand_cat >= 1:
                stats.catalog_repetition_score = min(1.0, cat_count * 0.25)
                stats.block_reason = "Catálogo repetido"

        # CTA overuse
        cta_over = _conversation_cta_count.get(conversation_id, 0)
        if cta_over >= 2:
            cand_cta = sum(1 for c in CTA_PHRASES if c in candidate.lower())
            if cand_cta >= 1:
                stats.cta_repetition_score = min(1.0, cta_over * 0.3)
                if stats.block_reason:
                    stats.block_reason += " + CTA repetido"
                else:
                    stats.block_reason = "CTA repetido"

        # exact match blocking
        if recent and any(candidate.lower().strip() == r.lower().strip() for r in recent):
            stats.is_blocked = True
            stats.block_reason = "Respuesta idéntica reciente"

        if stats.total_score >= 0.7:
            stats.is_blocked = True

        return stats

    def get_catalog_count(self, conversation_id: str) -> int:
        return _conversation_catalog_count.get(conversation_id, 0)

    def reset(self, conversation_id: str) -> None:
        _conversation_history.pop(conversation_id, None)
        _conversation_catalog_count.pop(conversation_id, None)
        _conversation_structures.pop(conversation_id, None)
        _conversation_cta_count.pop(conversation_id, None)
