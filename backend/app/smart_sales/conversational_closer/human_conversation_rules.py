CATALOG_REPETITIONS: list[str] = [
    "tenemos estas",
    "tenemos los siguientes",
    "mira estas opciones",
    "te interesa alguno",
    "te presento nuestras opciones",
    "contamos con",
    "disponemos de",
    "podemos ofrecerte",
    "nuestro catálogo incluye",
    "tenemos disponible",
]

TRANSITION_BLACKLIST: list[str] = [
    "¿Te interesa alguno?",
    "¿Te gusta alguno?",
]

REQUIRED_VARIETY: dict[str, int] = {
    "openings": 30,
    "closings": 30,
    "transitions": 20,
    "reassurance": 15,
}


class HumanConversationRules:
    def is_catalog_repetition(self, response: str) -> bool:
        resp_lower = response.lower().strip()
        score = 0
        for phrase in CATALOG_REPETITIONS:
            if phrase in resp_lower:
                score += 1
        return score >= 2

    def is_valid_transition(self, response: str, last_message: str) -> bool:
        if not last_message or not response:
            return True

        if last_message.lower().strip() == "gracias":
            if not any(kw in response.lower() for kw in ["combina", "queda", "estilo", "por cierto", "además"]):
                return False

        return True

    def should_vary_response(self, previous_responses: list[str], new_response: str) -> bool:
        if not previous_responses:
            return True

        for prev in previous_responses[-3:]:
            similarity = self._calc_similarity(prev, new_response)
            if similarity > 0.7:
                return False
        return True

    def _calc_similarity(self, a: str, b: str) -> float:
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())
        if not a_words or not b_words:
            return 0.0
        intersection = a_words & b_words
        return len(intersection) / max(len(a_words), len(b_words))
