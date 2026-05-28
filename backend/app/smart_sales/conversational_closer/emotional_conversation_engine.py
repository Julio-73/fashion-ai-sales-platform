import random

EMOTIONAL_TONES: dict[str, dict] = {
    "excitement": {
        "prefixes": ["🔥 ", "✨ ", "", ""],
        "suffixes": [" 🔥", " 😍", " 👌", ""],
        "adverbs": ["brutalmente ", "increíblemente ", "súper ", ""],
        "intensity": "high",
    },
    "warm": {
        "prefixes": ["😊 ", "", ""],
        "suffixes": [" 😊", " 👌", ""],
        "adverbs": ["", "muy ", "bastante "],
        "intensity": "medium",
    },
    "confident": {
        "prefixes": ["", "", "Sin duda "],
        "suffixes": [".", ".", " 👌"],
        "adverbs": ["", "totalmente ", "completamente "],
        "intensity": "high",
    },
    "empathetic": {
        "prefixes": ["Te entiendo ", "Claro ", "Tranqui 😊 "],
        "suffixes": [" 😊", "", ""],
        "adverbs": ["", "perfectamente "],
        "intensity": "medium",
    },
    "premium": {
        "prefixes": ["", "✨ ", ""],
        "suffixes": ["", " ✨", "."],
        "adverbs": ["excelentemente ", "elegantemente ", ""],
        "intensity": "medium",
    },
}


class EmotionalConversationEngine:
    def get_tone_for_emotion(self, emotion: str | None) -> str:
        if emotion in ("excitement", "high_intent"):
            return "excitement"
        if emotion == "greeting":
            return "warm"
        if emotion in ("hesitation", "indecision"):
            return "empathetic"
        if emotion == "frustration":
            return "empathetic"
        if emotion == "urgency":
            return "confident"
        return "warm"

    def apply_tone(self, text: str, tone: str) -> str:
        tone_config = EMOTIONAL_TONES.get(tone, EMOTIONAL_TONES["warm"])
        prefix = random.choice(tone_config["prefixes"])
        suffix = random.choice(tone_config["suffixes"])
        return f"{prefix}{text}{suffix}"

    def add_micro_emotion(self, text: str, emotion: str | None) -> str:
        micro_map = {
            "excitement": "🔥 ¡Qué emoción! ",
            "high_intent": "🔥 ¡Excelente! ",
            "greeting": "😊 ¡Qué gusto verte! ",
            "urgency": "⚡ ¡Dale rápido! ",
            "frustration": "😊 Entiendo, resolvamos esto. ",
        }
        prefix = micro_map.get(emotion, "")
        return f"{prefix}{text}" if prefix else text
