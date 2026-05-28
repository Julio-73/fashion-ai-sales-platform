
GRATITUDE_PATTERNS: list[str] = [
    "gracias", "thank", "thanks", "graciass", "mil gracias",
    "muchas gracias", "te agradezco", "se agradece",
]

ACKNOWLEDGMENT_RESPONSES: list[str] = [
    "Con gusto 😊",
    "Para eso estoy 🔥",
    "Un placer ayudarte 👌",
    "A la orden 😊",
    "Cuando quieras 🔥",
    "Con todo gusto 😊",
]

OK_PATTERNS: list[str] = [
    "ok", "okay", "okei", "dale", "listo", "perfecto",
    "genial", "excelente", "de acuerdo", "sale",
]

INTEREST_PATTERNS: list[str] = [
    "me gusta", "interesante", "wow", "me encanta",
    "se ve bien", "se ve bueno", "me convence",
]

HESITATION_PATTERNS: list[str] = [
    "mm no sé", "mmm no sé", "no sé", "no estoy seguro",
    "tal vez", "quizá", "lo pensaré",
]


class AcknowledgmentEngine:
    def is_gratitude(self, message: str) -> bool:
        msg = message.lower().strip()
        return any(p in msg for p in GRATITUDE_PATTERNS)

    def is_ok_acknowledgment(self, message: str) -> bool:
        msg = message.lower().strip()
        return any(p in msg for p in OK_PATTERNS)

    def is_interest(self, message: str) -> bool:
        msg = message.lower().strip()
        return any(p in msg for p in INTEREST_PATTERNS)

    def is_hesitation(self, message: str) -> bool:
        msg = message.lower().strip()
        return any(p in msg for p in HESITATION_PATTERNS)

    def get_gratitude_response(self) -> str:
        import random
        return random.choice(ACKNOWLEDGMENT_RESPONSES)

    def get_ok_response(self) -> str:
        import random
        items = [
            "Perfecto 🔥",
            "Dale, quedamos atentos 👌",
            "Listo, cualquier cosa me avisas 😊",
            "Genial, estamos aquí para lo que necesites 🔥",
        ]
        return random.choice(items)

    def get_interest_response(self) -> str:
        import random
        items = [
            "Me alegra que te guste 🔥",
            "Buena elección 👌",
            "Súper, es de los más pedidos 😊",
        ]
        return random.choice(items)

    def should_skip_catalog(self, message: str) -> bool:
        return any([
            self.is_gratitude(message),
            self.is_ok_acknowledgment(message),
            self.is_hesitation(message),
        ])
