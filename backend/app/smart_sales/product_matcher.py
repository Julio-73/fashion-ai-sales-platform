import logging
import re
from dataclasses import dataclass

from app.smart_sales.entity_extractor import ExtractedEntities, PRODUCT_ALIASES, COLOR_ALIASES

logger = logging.getLogger("ai_sales_agent.smart_sales.product_matcher")


@dataclass
class MatchedProduct:
    product_id: str
    name: str
    category: str | None
    base_price: float | None
    available_variants: list["MatchedVariant"]
    score: float
    match_reason: str

    @property
    def has_stock(self) -> bool:
        return any(v.available_stock > 0 for v in self.available_variants)

    @property
    def price_range(self) -> str:
        prices = [v.price for v in self.available_variants if v.available_stock > 0 and v.price]
        if not prices:
            return ""
        min_p = min(prices)
        max_p = max(prices)
        if min_p == max_p:
            return f"S/{min_p:.0f}"
        return f"desde S/{min_p:.0f}"

    @property
    def available_colors(self) -> list[str]:
        return sorted(set(v.color for v in self.available_variants if v.available_stock > 0 and v.color))

    @property
    def available_sizes(self) -> list[str]:
        return sorted(set(v.talla for v in self.available_variants if v.available_stock > 0 and v.talla))
    
    @property
    def total_available_stock(self) -> int:
        return sum(v.available_stock for v in self.available_variants)


@dataclass
class MatchedVariant:
    variant_id: str
    talla: str | None
    color: str | None
    price: float | None
    stock: int
    reserved_stock: int
    sku: str

    @property
    def available_stock(self) -> int:
        return self.stock - self.reserved_stock


class ProductMatcher:
    def match_product_types(self, raw_query: str) -> list[str]:
        if not raw_query:
            return []
        normalized = raw_query.lower().strip()
        matches = set()
        for canonical, aliases in PRODUCT_ALIASES.items():
            for alias in aliases:
                pattern = r'\b' + re.escape(alias) + r's?\b'
                if re.search(pattern, normalized):
                    matches.add(canonical)
                    break
        return list(matches)

    def normalize_text(self, text: str) -> str:
        normalized = text.lower().strip()
        normalized = re.sub(r'\bun[oa]s?\b', '', normalized)
        normalized = re.sub(r'\bl[oa]s?\b', '', normalized)
        normalized = re.sub(r'\b(quiero|necesito|busco|hay|tienen|dame|me)\b', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def compute_similarity(self, query_words: list[str], product_name: str) -> float:
        name_words = product_name.lower().split()
        if not query_words or not name_words:
            return 0.0
        matches = sum(1 for qw in query_words for nw in name_words
                      if qw == nw or nw.startswith(qw) or qw.startswith(nw))
        if not matches:
            for qw in query_words:
                for nw in name_words:
                    if len(qw) > 3 and len(nw) > 3:
                        if self._fuzzy_match(qw, nw, threshold=0.7):
                            matches += 0.5
                            break
        max_len = max(len(query_words), len(name_words))
        return matches / max_len if max_len > 0 else 0.0

    def _fuzzy_match(self, a: str, b: str, threshold: float = 0.7) -> bool:
        if a == b:
            return True
        longer, shorter = (a, b) if len(a) >= len(b) else (b, a)
        if len(longer) == 0:
            return True
        edit_dist = self._levenshtein(longer, shorter)
        return 1.0 - (edit_dist / len(longer)) >= threshold

    def _levenshtein(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        if len(s2) == 0:
            return len(s1)
        prev = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr = [i + 1]
            for j, c2 in enumerate(s2):
                cost = 0 if c1 == c2 else 1
                curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
            prev = curr
        return prev[-1]

    def score_product(self, product_name: str, product_category: str | None,
                      entities: ExtractedEntities) -> float:
        score = 0.0
        reasons = []
        normalized = (product_name + " " + (product_category or "")).lower()

        if entities.product_type:
            aliases = PRODUCT_ALIASES.get(entities.product_type, [entities.product_type])
            if any(a in normalized for a in aliases):
                score += 30.0
                reasons.append("product_type")

        if entities.color:
            if entities.color.lower() in normalized:
                score += 20.0
                reasons.append("color")
            else:
                for alias, canonical in COLOR_ALIASES.items():
                    if canonical == entities.color and alias in normalized:
                        score += 30.0
                        reasons.append("color")
                        break

        if entities.gender:
            gender_terms = {
                "hombre": ["hombre", "men", "man", "masculino"],
                "mujer": ["mujer", "woman", "women", "femenino", "dama"],
                "unisex": ["unisex", "niño", "niña"],
            }
            terms = gender_terms.get(entities.gender, [])
            if any(t in normalized for t in terms):
                score += 15.0
                reasons.append("gender")

        if entities.style:
            from app.smart_sales.entity_extractor import STYLE_ALIASES
            style_words = STYLE_ALIASES.get(entities.style, [entities.style])
            if any(s in normalized for s in style_words):
                score += 10.0
                reasons.append("style")

        if entities.occasion:
            from app.smart_sales.entity_extractor import OCCASION_ALIASES
            occ_words = OCCASION_ALIASES.get(entities.occasion, [entities.occasion])
            if any(o in normalized for o in occ_words):
                score += 10.0
                reasons.append("occasion")

        logger.debug("Score for '%s': %.1f (reasons: %s)", product_name, score, reasons)
        return score
