import logging

from app.smart_sales.entity_extractor import EntityExtractor
from app.smart_sales.product_matcher import ProductMatcher

logger = logging.getLogger("ai_sales_agent.ai.memory.summarizer")


class MemorySummarizer:
    def __init__(self) -> None:
        self._entity_extractor = EntityExtractor()
        self._product_matcher = ProductMatcher()

    async def summarize_messages(
        self,
        messages: list[dict],
    ) -> dict:
        all_text = " ".join(m.get("content", "") for m in messages if m.get("content"))
        entities = self._entity_extractor.extract(all_text)

        styles = []
        if entities.style:
            styles.append(entities.style)
        occasions = []
        if entities.occasion:
            occasions.append(entities.occasion)
        colors = []
        if entities.color:
            colors.append(entities.color)
        sizes = []
        if entities.size:
            sizes.append(entities.size)

        preferences = []
        if entities.product_type:
            preferences.append(f"interesado en {entities.product_type}")
        if entities.gender:
            preferences.append(f"género: {entities.gender}")

        summary_parts = []
        if entities.product_type:
            summary_parts.append(f"Producto de interés: {entities.product_type}")
        if entities.style:
            summary_parts.append(f"Estilo preferido: {entities.style}")
        if entities.color:
            summary_parts.append(f"Color: {entities.color}")
        if entities.size:
            summary_parts.append(f"Talla: {entities.size}")
        if entities.occasion:
            summary_parts.append(f"Ocasión: {entities.occasion}")

        summary = " | ".join(summary_parts) if summary_parts else "Sin resumen disponible"

        return {
            "summary": summary,
            "preferences": preferences,
            "sizes": sizes,
            "colors": colors,
            "styles": styles,
            "occasions": occasions,
            "confidence": 0.7 if entities.has_any else 0.3,
        }

    def summarize_memory_context(
        self, preferences: list[str], colors: list[str], sizes: list[str], styles: list[str]
    ) -> str:
        parts = []
        if preferences:
            parts.append("Preferencias: " + ", ".join(preferences))
        if colors:
            parts.append("Colores: " + ", ".join(colors))
        if sizes:
            parts.append("Tallas: " + ", ".join(sizes))
        if styles:
            parts.append("Estilos: " + ", ".join(styles))
        return " | ".join(parts) if parts else "Sin preferencias registradas"
