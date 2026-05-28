import random

_OPENINGS: list[str] = [
    "Te recomiendo",
    "Qué tal",
    "Mira esta opción",
    "Una excelente alternativa es",
    "Perfecto para lo que buscas",
    "Justo lo que necesitas",
    "Me encanta esta opción para ti",
    "Esta es ideal",
    "Te va a encantar",
    "Sin duda, esto es para ti",
    "Mira lo que tengo para ti",
    "Qué te parece",
    "Esto te va a quedar brutal",
    "Te presento",
    "Esta opción es perfecta",
    "Sin duda te recomiendo",
    "Mira esta joyita",
    "Para tu estilo, esto es",
    "Encontré esto que te va a fascinar",
    "Esto es justo lo tuyo",
    "Déjame mostrarte",
    "Te va a encantar esta opción",
    "Ideal para tu look",
    "Esta es la que buscas",
    "Sin duda, esta es",
    "Para ti tengo",
    "Entre las opciones, destaco",
    "Definitivamente te recomiendo",
    "Esta pieza es espectacular",
    "No puedo dejar de recomendarte",
]

_CLOSINGS: list[str] = [
    "¿Te interesa?",
    "¿Qué te parece?",
    "¿Te gusta?",
    "¿Te lo llevas?",
    "Dime y te ayudo con la talla",
    "¿Te parece bien?",
    "¿Alguna duda?",
    "¿Vamos con esa?",
    "¿Qué opinas?",
    "¿Te animas?",
    "Cuéntame qué te parece",
    "Estoy aquí para ayudarte",
    "¿Te sirve?",
    "¿Te ayudo con el pedido?",
    "Dime si te gusta",
    "¿La separamos?",
    "Queda a tu disposición",
    "¿Te parece buena opción?",
    "Háblame y te ayudo",
    "¿Te reservo una?",
    "Dime qué tal la ves",
    "¿Te convence?",
    "Estoy atento a tu respuesta",
    "¿La quieres probar?",
    "¿Te la aparto?",
    "Cuéntame si te gustó",
    "¿Seguimos viendo opciones?",
    "Dime si necesitas algo más",
    "¿Te parece?",
    "¿Listo para llevártela?",
]

_TRANSITIONS: list[str] = [
    "Por cierto,",
    "Además,",
    "También,",
    "Y hablando de outfits,",
    "A propósito,",
    "Si te gusta ese estilo,",
    "Otra cosa,",
    "Y ya que mencionas eso,",
    "Justamente,",
    "Siguiendo con el look,",
    "Para complementar,",
    "Y algo más,",
    "Como plus,",
    "Y si te interesa,",
    "Cambiando un poco el tema pero",
    "Ya que estamos en mode outfit,",
    "Y lo mejor,",
    "Lo bueno es que",
    "Adicionalmente,",
    "Por cierto, algo importante:",
]

_REASSURANCE: list[str] = [
    "Es una excelente elección.",
    "No te vas a arrepentir.",
    "Es calidad premium.",
    "Vas a notar la diferencia.",
    "Está súper bien valorado.",
    "Es de lo mejor que tenemos.",
    "La calidad se nota al instante.",
    "Te va a encantar, seguro.",
    "Es una inversión que vale la pena.",
    "Está hecho con materiales de primera.",
    "Tiene muy buenos comentarios.",
    "Es garantía de calidad.",
    "Vas a quedar encantado.",
    "Es un acierto total.",
    "Está diseñado para durar.",
]

_ENTHUSIASM: list[str] = [
    "🔥", "✨", "👌", "😊", "💪",
    "Está brutal 🔥",
    "Es espectacular ✨",
    "Te va a encantar 😊",
    "Está súper 🔥",
    "Es una maravilla ✨",
]


class NaturalLanguageVariator:
    _opening_idx: int = 0
    _closing_idx: int = 0
    _transition_idx: int = 0
    _reassurance_idx: int = 0

    def get_opening(self) -> str:
        idx = self._opening_idx
        self._opening_idx = (idx + 1) % len(_OPENINGS)
        return _OPENINGS[idx]

    def get_closing(self) -> str:
        idx = self._closing_idx
        self._closing_idx = (idx + 1) % len(_CLOSINGS)
        return _CLOSINGS[idx]

    def get_transition(self) -> str:
        idx = self._transition_idx
        self._transition_idx = (idx + 1) % len(_TRANSITIONS)
        return _TRANSITIONS[idx]

    def get_reassurance(self) -> str:
        idx = self._reassurance_idx
        self._reassurance_idx = (idx + 1) % len(_REASSURANCE)
        return _REASSURANCE[idx]

    def get_enthusiasm(self) -> str:
        return random.choice(_ENTHUSIASM)

    @property
    def openings_count(self) -> int:
        return len(_OPENINGS)

    @property
    def closings_count(self) -> int:
        return len(_CLOSINGS)

    @property
    def transitions_count(self) -> int:
        return len(_TRANSITIONS)

    @property
    def reassurance_count(self) -> int:
        return len(_REASSURANCE)
