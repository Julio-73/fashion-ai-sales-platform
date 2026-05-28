OBJECTION_RESPONSES: dict[str, list[str]] = {
    "caro": [
        "Te entiendo 😊 Ese modelo es premium por el tipo de acabado y la calidad del material. Pero también tengo opciones similares un poco más accesibles si quieres comparar 👌",
        "Entiendo tu punto. La calidad de este modelo justifica el precio por sus materiales y terminación. ¿Quieres que te muestre alternativas en otro rango?",
        "Sí, es una inversión, pero la durabilidad y el diseño lo valen. Si prefieres, puedo mostrarte opciones más económicas pero con estilo similar.",
    ],
    "pensar": [
    "Tranqui 😊 Tómate tu tiempo. Si quieres, puedo dejarte la información y me avisas cuando decidas 👌",
    "Por supuesto, sin presión. Cuando quieras seguir viendo opciones, aquí estoy 🔥",
    "Claro, es una decisión importante. Si en algún momento tienes dudas o quieres ver más opciones, me dices 😊",
    ],
    "no_se": [
        "Tranqui 😊 Si quieres puedo mostrarte opciones similares para que compares estilos, precios y fits antes de decidir 👌",
        "Sin problema. Cuéntame más qué estás buscando y te ayudo a encontrar justo lo que necesitas 🔥",
        "Déjame hacerte unas preguntas rápidas para recomendarte algo perfecto para ti 😊",
    ],
    "ver_mas": [
        "Claro, tengo más opciones. ¿Te interesa ver algo similar o prefieres explorar otra categoría?",
        "Por supuesto. ¿Buscas algo en particular o prefieres que te muestre lo más destacado?",
        "Dime qué estilo te llama más y te enseño lo que tenemos 🔥",
    ],
    "barato": [
        "Claro, tengo opciones con excelente relación calidad-precio. Déjame mostrarte algunas alternativas 👌",
        "Por supuesto. Tenemos modelos más accesibles que también están muy bonitos. ¿Te interesa verlos?",
        "Sí, tenemos opciones para todos los presupuestos. ¿Qué rango de precio tienes en mente?",
    ],
    "otra_opcion": [
        "Claro, déjame mostrarte otras alternativas que también son muy populares 👌",
        "Por supuesto, tengo varias opciones que te pueden gustar. ¿Prefieres algo del mismo estilo o diferente?",
        "Claro, tenemos más variedad. Cuéntame qué buscas exactamente y te enseño lo ideal 🔥",
    ],
    "no_seguro": [
        "Tranqui, es normal tener dudas. Cuéntame qué te genera más preguntas y te ayudo a decidir 😊",
        "Sin problema. Si quieres te doy más detalles del producto para que puedas decidir con calma 👌",
    ],
}


class ObjectionHandler:
    def detect_objection(self, message: str) -> str | None:
        msg_lower = message.lower().strip()

        patterns = [
            ("caro", ["caro", "cara", "precio", "costoso", "elevado", "carísimo"]),
            ("pensar", ["pensaré", "pensarlo", "lo pensaré", "lo voy a pensar", "consulto"]),
            ("no_se", ["no sé", "nose", "no estoy seguro", "no estoy segura", "mmm", "hmm"]),
            ("ver_mas", ["ver más", "quiero ver más", "muestra más", "otras opciones", "más opciones"]),
            ("barato", ["barato", "económico", "accesible", "menos precio", "más barato"]),
            ("otra_opcion", ["otra opción", "alternativa", "algo más", "otro modelo", "otra cosa"]),
            ("no_seguro", ["no seguro", "no convencido", "dudas", "indeciso"]),
        ]

        for key, keywords in patterns:
            if any(kw in msg_lower for kw in keywords):
                return key

        return None

    def get_response(self, objection_key: str) -> str:
        responses = OBJECTION_RESPONSES.get(objection_key)
        if not responses:
            return "Te entiendo. ¿Qué te parece si busco algo que se ajuste mejor a lo que necesitas? 😊"
        import random
        return random.choice(responses)

    def handle_objection(self, message: str) -> tuple[bool, str]:
        key = self.detect_objection(message)
        if key:
            return True, self.get_response(key)
        return False, ""
