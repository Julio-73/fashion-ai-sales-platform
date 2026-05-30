"""
Sales Conversation Scenarios — QA Testing Suite

Validates that the AI sales agent behaves like a real human premium sales advisor.

Categories:
  - Greetings (01-10)
  - Gratitude (11-20)
  - Farewell / Closing (21-30)
  - Casual chat / Status questions (31-40)
  - Product interest (41-50)
  - Sizing queries (51-60)
  - Color queries (61-65)
  - Commitment / Ready to buy (66-75)
  - Objections (76-85)
  - Non-existent products (86-95)
  - Category changes (96-100)
  - Hesitation (101-105)
  - Comparisons (106-110)

Each scenario specifies:
  - messages: list of conversation turns
  - expected_behavior: what the AI MUST NOT do (red flags)
  - expected_patterns: what the AI response SHOULD contain
"""

from dataclasses import dataclass, field


@dataclass
class ConversationScenario:
    id: str
    name: str
    category: str
    messages: list[str]
    forbidden_patterns: list[str] = field(default_factory=list)
    expected_patterns: list[str] = field(default_factory=list)
    description: str = ""


SCENARIOS: list[ConversationScenario] = [
    # =========================================================================
    # GREETINGS (01-10)
    # =========================================================================
    ConversationScenario(
        id="S001", category="greeting", name="Saludo simple",
        messages=["Hola"],
        forbidden_patterns=["tenemos estas opciones", "te muestro", "catálogo", "te recomiendo estas"],
        expected_patterns=["estilo", "ropa", "busca", "outfit", "tipo", "hombre", "mujer", "sneaker", "elegante", "casual", "accesorio"],
        description="Al saludar, NO debe listar catálogo. Debe responder como humano.",
    ),
    ConversationScenario(
        id="S002", category="greeting", name="Saludo con 'buenas'",
        messages=["Buenas"],
        forbidden_patterns=["tenemos estas", "disponibles", "catálogo"],
        expected_patterns=["estilo", "ropa", "busca", "outfit", "tipo", "hombre", "mujer", "sneaker", "elegante", "casual"],
        description="Saludo genérico debe recibir respuesta humana.",
    ),
    ConversationScenario(
        id="S003", category="greeting", name="Saludo 'qué tal'",
        messages=["Qué tal"],
        forbidden_patterns=["tenemos estas opciones", "lista de productos"],
        expected_patterns=["estilo", "ropa", "busca", "outfit", "tipo", "hombre", "mujer", "sneaker", "elegante", "casual"],
        description="'Qué tal' debe responder como humano.",
    ),
    ConversationScenario(
        id="S004", category="greeting", name="Saludo 'hey'",
        messages=["Hey"],
        forbidden_patterns=["tenemos estas", "disponibles"],
        expected_patterns=["estilo", "ropa", "busca", "outfit", "tipo", "hombre", "mujer", "sneaker", "elegante", "casual", "accesorio", "ofrece"],
        description="Saludo informal debe ser respondido informalmente.",
    ),
    ConversationScenario(
        id="S005", category="greeting", name="Saludo con nombre",
        messages=["Hola, buenas tardes"],
        forbidden_patterns=["tenemos estas opciones"],
        expected_patterns=["estilo", "ropa", "busca", "outfit", "tipo", "hombre", "mujer", "sneaker", "elegante", "casual", "accesorio"],
        description="Saludo con cortesía debe ser respondido con cortesía.",
    ),
    ConversationScenario(
        id="S006", category="greeting", name="Bienvenida",
        messages=["Bienvenido"],
        forbidden_patterns=["te muestro", "catálogo", "tenemos"],
        expected_patterns=["estilo", "ropa", "busca", "outfit", "tipo", "hombre", "mujer", "sneaker", "elegante", "casual", "accesorio", "gracias"],
        description="'Bienvenido' debe recibir respuesta de agradecimiento.",
    ),
    ConversationScenario(
        id="S007", category="greeting", name="Saludo 'holi'",
        messages=["Holi"],
        forbidden_patterns=["tenemos estas", "disponibles"],
        expected_patterns=["estilo", "ropa", "busca", "outfit", "tipo", "hombre", "mujer", "sneaker", "elegante", "casual", "accesorio"],
        description="Saludo informal debe ser respondido sin catálogo.",
    ),
    ConversationScenario(
        id="S008", category="greeting", name="Saludo 'hello'",
        messages=["Hello"],
        forbidden_patterns=["tenemos estas opciones"],
        expected_patterns=["estilo", "ropa", "busca", "outfit", "tipo", "hombre", "mujer", "sneaker", "elegante", "casual", "accesorio"],
        description="Saludo en inglés debe ser respondido en español.",
    ),
    ConversationScenario(
        id="S009", category="greeting", name="Saludo 'buenos días'",
        messages=["Buenos días"],
        forbidden_patterns=["tenemos estas", "te recomiendo"],
        expected_patterns=["estilo", "ropa", "busca", "outfit", "tipo", "hombre", "mujer", "sneaker", "elegante", "casual"],
        description="Saludo formal matutino.",
    ),
    ConversationScenario(
        id="S010", category="greeting", name="Saludo con producto inmediato",
        messages=["Hola, busco un polo negro"],
        forbidden_patterns=["cómo estás", "qué tal"],
        expected_patterns=["polo", "negro", "tienes", "disponible", "talla", "color",
                           "estilo", "ropa", "busca", "outfit", "hombre", "mujer"],
        description="Si saludo + producto, debe responder sobre el producto.",
    ),

    # =========================================================================
    # GRATITUDE (11-20)
    # =========================================================================
    ConversationScenario(
        id="S011", category="gratitude", name="Agradecimiento simple",
        messages=["Gracias"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "mira estas",
                            "disponibles", "quieres que te ayude con el pedido",
                            "te paso más info", "catálogo", "modelos"],
        expected_patterns=["con gusto", "un placer", "de nada", "confianza",
                           "encantado", "gracias a ti", "contento", "listo",
                           "cuando", "aquí", "estoy", "estaré", "día", "ayudar",
                           "gusto", "asistirte", "tienes", "cuidate", "verte", "vuelta",
                           "luego", "surge", "escribirme", "ayuda", "adelante",
                           "quieras", "necesites", "puedo"],
        description="Al agradecer, NO debe seguir vendiendo ni mostrar catálogo.",
    ),
    ConversationScenario(
        id="S012", category="gratitude", name="Muchas gracias",
        messages=["Muchas gracias"],
        forbidden_patterns=["tenemos estas", "disponibles", "quieres que te"],
        expected_patterns=["con gusto", "un placer", "de nada", "confianza",
                           "encantado", "gracias a ti", "contento", "listo",
                           "cuando", "aquí", "estoy", "estaré", "día"],
        description="Agradecimiento efusivo debe cerrar elegantemente.",
    ),
    ConversationScenario(
        id="S013", category="gratitude", name="Gracias con despedida",
        messages=["Gracias, eso sería todo"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "quieres"],
        expected_patterns=["con gusto", "un placer", "de nada", "confianza",
                           "encantado", "gracias", "listo", "cuando", "aquí",
                           "estoy", "día", "excelente"],
        description="Gracias + despedida debe cerrar conversación.",
    ),
    ConversationScenario(
        id="S014", category="gratitude", name="Mil gracias",
        messages=["Mil gracias"],
        forbidden_patterns=["tenemos estas", "disponibles", "quieres que"],
        expected_patterns=["con gusto", "un placer", "de nada", "confianza",
                           "encantado", "gracias a ti", "contento", "listo",
                           "cuando", "aquí", "estoy", "estaré"],
        description="'Mil gracias' debe cerrar sin vender más.",
    ),
    ConversationScenario(
        id="S015", category="gratitude", name="Gracias post-compra",
        messages=["Gracias por tu ayuda"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "mira estas"],
        expected_patterns=["con gusto", "un placer", "de nada", "confianza",
                           "encantado", "gracias a ti", "contento", "listo",
                           "cuando", "aquí", "estoy", "estaré", "día", "ayuda",
                           "ayudar", "luego"],
        description="Agradecimiento post-atención debe cerrar elegantemente.",
    ),
    ConversationScenario(
        id="S016", category="gratitude", name="Gracias a ti",
        messages=["Gracias a ti"],
        forbidden_patterns=["tenemos estas", "disponibles", "te muestro"],
        expected_patterns=["gracias", "a ti", "con gusto", "un placer", "de nada",
                           "confianza", "encantado", "contento", "listo", "cuando",
                           "aquí", "estoy", "estaré"],
        description="'Gracias a ti' debe responder con reciprocidad.",
    ),
    ConversationScenario(
        id="S017", category="gratitude", name="Te agradezco",
        messages=["Te agradezco mucho"],
        forbidden_patterns=["tenemos estas opciones"],
        expected_patterns=["con gusto", "un placer", "de nada", "confianza",
                           "encantado", "gracias a ti", "contento", "listo",
                           "cuando", "aquí", "estoy", "estaré"],
        description="Agradecimiento formal debe cerrar sin seguir vendiendo.",
    ),
    ConversationScenario(
        id="S018", category="gratitude", name="Gracias + consulta",
        messages=["Gracias. ¿Y ese modelo en rojo lo tienen?"],
        forbidden_patterns=[],
        expected_patterns=["rojo", "disponible", "talla", "modelo",
                           "con gusto", "un placer", "de nada", "cuando",
                           "aquí", "estoy", "estaré"],
        description="Si agradece pero sigue preguntando, debe responder la consulta.",
    ),
    ConversationScenario(
        id="S019", category="gratitude", name="Gracias luego de elegir",
        messages=["Me llevo el polo negro, gracias"],
        forbidden_patterns=["tenemos estas opciones", "mira estas", "te recomiendo estas"],
        expected_patterns=["polo", "negro", "talla", "excelente", "elección",
                           "con gusto", "placer", "gracias"],
        description="Gracias + compra debe entrar en modo cierre, no mostrar catálogo.",
    ),
    ConversationScenario(
        id="S020", category="gratitude", name="Gracias por la info",
        messages=["Gracias por la información"],
        forbidden_patterns=["tenemos estas opciones", "quieres que te"],
        expected_patterns=["con gusto", "un placer", "de nada", "confianza",
                           "encantado", "gracias a ti", "contento", "listo",
                           "cuando", "aquí", "estoy", "estaré"],
        description="Agradecimiento informativo debe cerrar sin vender.",
    ),

    # =========================================================================
    # FAREWELL / CLOSING (21-30)
    # =========================================================================
    ConversationScenario(
        id="S021", category="farewell", name="Eso es todo",
        messages=["Eso es todo"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "mira estas",
                            "disponibles", "quieres que te muestre", "catálogo",
                            "te gustaría ver"],
        expected_patterns=["perfecto", "gracias", "excelente", "día", "luego",
                           "cuidate", "hasta", "listo", "gusto", "bien",
                           "encantado", "ayudarte", "placer", "asistirte",
                           "estoy", "confiar", "pronto", "resuelto", "tiempo",
                           "alegra", "lindo"],
        description="'Eso es todo' debe cerrar, NO seguir vendiendo.",
    ),
    ConversationScenario(
        id="S022", category="farewell", name="Nada más",
        messages=["Nada más, gracias"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "mira estas"],
        expected_patterns=["perfecto", "gracias", "excelente", "listo", "gusto",
                           "bien", "encantado", "ayudarte", "día"],
        description="'Nada más' debe cerrar conversación.",
    ),
    ConversationScenario(
        id="S023", category="farewell", name="Chao",
        messages=["Chao"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "disponibles"],
        expected_patterns=["chao", "adiós", "hasta", "luego", "cuidate", "día",
                           "perfecto", "gracias", "listo", "pronto"],
        description="Despedida simple debe responder con despedida.",
    ),
    ConversationScenario(
        id="S024", category="farewell", name="Adiós",
        messages=["Adiós"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo"],
        expected_patterns=["adiós", "chao", "hasta", "luego", "cuidate", "día",
                           "perfecto", "gracias", "listo", "pronto"],
        description="'Adiós' debe cerrar la conversación.",
    ),
    ConversationScenario(
        id="S025", category="farewell", name="Bye",
        messages=["Bye"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo"],
        expected_patterns=["bye", "adiós", "chao", "hasta", "luego", "cuidate",
                           "perfecto", "gracias", "listo", "pronto", "día"],
        description="'Bye' debe responder con despedida.",
    ),
    ConversationScenario(
        id="S026", category="farewell", name="Nos vemos",
        messages=["Nos vemos"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo"],
        expected_patterns=["nos vemos", "hasta", "luego", "cuidate", "chao",
                           "adiós", "perfecto", "gracias", "listo", "día", "pronto"],
        description="'Nos vemos' debe cerrar naturalmente.",
    ),
    ConversationScenario(
        id="S027", category="farewell", name="Gracias por todo + cierre",
        messages=["Gracias por todo, hasta luego"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "disponibles"],
        expected_patterns=["gracias", "hasta luego", "con gusto", "placer",
                           "perfecto", "encantado", "listo", "cuidate", "día"],
        description="Despedida agradecida debe cerrar elegantemente.",
    ),
    ConversationScenario(
        id="S028", category="farewell", name="Ya me voy",
        messages=["Ya me voy, gracias"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "mira estas"],
        expected_patterns=["gracias", "cuidate", "hasta", "luego", "día",
                           "perfecto", "listo", "pronto", "con gusto", "un placer",
                           "de nada", "confianza", "encantado", "contento",
                           "cuando", "aquí", "estoy", "estaré"],
        description="'Ya me voy' debe cerrar la conversación.",
    ),
    ConversationScenario(
        id="S029", category="farewell", name="Eso sería todo",
        messages=["Eso sería todo, gracias"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "disponibles"],
        expected_patterns=["perfecto", "gracias", "excelente", "día", "listo",
                           "gusto", "bien", "encantado", "con gusto", "un placer",
                           "de nada", "confianza", "contento", "cuando",
                           "aquí", "estoy", "estaré"],
        description="'Eso sería todo' debe cerrar la conversación.",
    ),
    ConversationScenario(
        id="S030", category="farewell", name="Hasta luego",
        messages=["Hasta luego"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo"],
        expected_patterns=["hasta luego", "cuidate", "adiós", "chao",
                           "perfecto", "gracias", "listo", "día", "pronto"],
        description="'Hasta luego' debe responder con despedida.",
    ),

    # =========================================================================
    # CASUAL CHAT / STATUS (31-40)
    # =========================================================================
    ConversationScenario(
        id="S031", category="casual", name="Cómo estás",
        messages=["Cómo estás"],
        forbidden_patterns=["tenemos estas opciones", "mira estas", "te recomiendo",
                            "disponibles", "catálogo", "productos"],
        expected_patterns=["bien", "gracias", "preguntar", "ayudar", "qué tal",
                           "gracias por preguntar", "estoy", "aquí", "encontrar",
                           "busca", "especial", "gusto"],
        description="'Cómo estás' debe responder como humano, NO mostrar productos.",
    ),
    ConversationScenario(
        id="S032", category="casual", name="Cómo te va",
        messages=["Cómo te va"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo", "catálogo"],
        expected_patterns=["bien", "gracias", "qué tal", "ayudar", "preguntar",
                           "gracias por preguntar", "estoy", "aquí"],
        description="'Cómo te va' debe responder humanamente.",
    ),
    ConversationScenario(
        id="S033", category="casual", name="Todo bien",
        messages=["Todo bien"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo"],
        expected_patterns=["bien", "genial", "qué bien", "ayudar", "dale",
                           "perfecto", "excelente", "gusta", "algo más",
                           "necesitas", "estoy", "alegra", "cool", "listo",
                           "novedades", "bacán", "estilos", "gusto", "conversar",
                           "contento", "especial", "puedo"],
        description="'Todo bien' debe continuar conversación natural.",
    ),
    ConversationScenario(
        id="S034", category="casual", name="Qué tal tu día",
        messages=["Qué tal tu día"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo"],
        expected_patterns=["bien", "gracias", "preguntar", "ayudar", "qué tal",
                           "gracias por preguntar", "estoy", "aquí"],
        description="Pregunta personal debe recibir respuesta personal.",
    ),
    ConversationScenario(
        id="S035", category="casual", name="Ok simple",
        messages=["Ok"],
        forbidden_patterns=["tenemos estas opciones", "catálogo"],
        expected_patterns=["bien", "genial", "perfecto", "dale", "ok", "qué tal",
                           "ayudar", "gusta", "estamos", "alegra", "excelente",
                           "algo más", "necesitas", "ayuda", "cool", "listo",
                           "novedades", "bacán", "estilos", "variar", "gusto",
                           "conversar", "contento", "especial", "muestro",
                           "completo", "puedo"],
        description="'Ok' debe ser respuesta corta, no catálogo.",
    ),
    ConversationScenario(
        id="S036", category="casual", name="Perfecto",
        messages=["Perfecto"],
        forbidden_patterns=["tenemos estas opciones", "catálogo", "te recomiendo"],
        expected_patterns=["bien", "genial", "perfecto", "dale", "qué tal",
                           "ayudar", "gusta", "estamos", "alegra", "excelente",
                           "algo más", "necesitas", "ayuda", "cool", "listo",
                           "novedades", "bacán", "estilos", "variar", "gusto",
                           "conversar", "contento", "especial", "muestro",
                           "completo", "puedo"],
        description="'Perfecto' debe ser acknowledgment, no catálogo.",
    ),
    ConversationScenario(
        id="S037", category="casual", name="Dale",
        messages=["Dale"],
        forbidden_patterns=["tenemos estas opciones", "catálogo"],
        expected_patterns=["bien", "genial", "perfecto", "dale", "qué tal",
                           "ayudar", "gusta", "estamos", "alegra", "excelente",
                           "algo más", "necesitas", "ayuda", "cool", "listo",
                           "novedades", "bacán", "estilos", "variar", "gusto",
                           "conversar", "contento", "especial", "muestro",
                           "completo", "puedo"],
        description="'Dale' debe ser acknowledgment.",
    ),
    ConversationScenario(
        id="S038", category="casual", name="Genial",
        messages=["Genial"],
        forbidden_patterns=["tenemos estas opciones", "catálogo"],
        expected_patterns=["bien", "genial", "perfecto", "dale", "qué tal",
                           "ayudar", "gusta", "estamos", "alegra", "excelente",
                           "algo más", "necesitas", "ayuda", "cool", "listo",
                           "novedades", "bacán", "estilos", "variar", "gusto",
                           "conversar", "contento", "especial", "muestro",
                           "completo", "puedo"],
        description="'Genial' debe ser acknowledgment.",
    ),
    ConversationScenario(
        id="S039", category="casual", name="Claro",
        messages=["Claro"],
        forbidden_patterns=["tenemos estas opciones", "catálogo"],
        expected_patterns=["bien", "genial", "perfecto", "dale", "qué tal",
                           "ayudar", "gusta", "estamos", "alegra", "excelente",
                           "algo más", "necesitas", "ayuda", "cool", "listo",
                           "novedades", "bacán", "estilos", "variar", "gusto",
                           "conversar", "contento", "especial", "muestro",
                           "completo", "puedo"],
        description="'Claro' debe ser acknowledgment.",
    ),
    ConversationScenario(
        id="S040", category="casual", name="Entiendo",
        messages=["Entiendo"],
        forbidden_patterns=["tenemos estas opciones", "catálogo"],
        expected_patterns=["bien", "genial", "perfecto", "dale", "qué tal",
                           "ayudar", "gusta", "estamos", "alegra", "excelente",
                           "algo más", "necesitas", "ayuda", "cool", "listo",
                           "novedades", "bacán", "estilos", "variar", "gusto",
                           "conversar", "contento", "especial", "muestro",
                           "completo", "puedo"],
        description="'Entiendo' acknowledgment sin catálogo.",
    ),

    # =========================================================================
    # PRODUCT INTEREST (41-50)
    # =========================================================================
    ConversationScenario(
        id="S041", category="interest", name="Me gusta un producto",
        messages=["Me gusta el polo premium black"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas", "tenemos estas"],
        expected_patterns=["polo premium black", "talla", "color", "excelente", "elección"],
        description="Al expresar gusto por un producto específico, debe enfocarse en ese producto.",
    ),
    ConversationScenario(
        id="S042", category="interest", name="Quiero ese",
        messages=["Quiero ese"],
        forbidden_patterns=["tenemos estas opciones", "mira estas", "catálogo"],
        expected_patterns=["excelente", "elección", "talla", "color", "producto"],
        description="'Quiero ese' debe activar modo cierre.",
    ),
    ConversationScenario(
        id="S043", category="interest", name="Me quedo con ese",
        messages=["Me quedo con ese"],
        forbidden_patterns=["tenemos estas opciones", "mira estas", "catálogo"],
        expected_patterns=["excelente", "elección", "talla", "color",
                           "chompa", "polo", "casaca", "jean", "cuéntame",
                           "buscas", "ideal", "ayudar", "producto", "modelo"],
        description="'Me quedo con ese' debe confirmar producto y preguntar talla/color.",
    ),
    ConversationScenario(
        id="S044", category="interest", name="Se ve bien",
        messages=["Se ve bien ese modelo"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["excelente", "elección", "gusta", "talla", "color",
                           "chompa", "polo", "casaca", "jean", "cuéntame",
                           "buscas", "ideal", "modelo", "producto"],
        description="Interés en modelo debe llevar a detalles del producto.",
    ),
    ConversationScenario(
        id="S045", category="interest", name="Me interesa",
        messages=["Me interesa la casaca oversize"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["casaca oversize", "talla", "color", "disponible"],
        description="Interés específico debe centrarse en ese producto.",
    ),
    ConversationScenario(
        id="S046", category="interest", name="Cuéntame más",
        messages=["Cuéntame más de ese modelo"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["modelo", "disponible", "talla", "color", "precio"],
        description="'Cuéntame más' debe dar detalles, no listar otros.",
    ),
    ConversationScenario(
        id="S047", category="interest", name="Lo quiero",
        messages=["Lo quiero"],
        forbidden_patterns=["tenemos estas opciones", "mira estas", "te recomiendo"],
        expected_patterns=["excelente", "talla", "color", "reservar", "comprar"],
        description="'Lo quiero' debe iniciar cierre de venta.",
    ),
    ConversationScenario(
        id="S048", category="interest", name="Me encanta",
        messages=["Me encanta ese diseño"],
        forbidden_patterns=["tenemos estas opciones"],
        expected_patterns=["encanta", "excelente", "talla", "color"],
        description="Entusiasmo por diseño debe reforzar la elección.",
    ),
    ConversationScenario(
        id="S049", category="interest", name="Buena opción",
        messages=["Buena opción, me gusta"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["excelente", "elección", "talla", "color"],
        description="Aprobación debe llevar a cierre natural.",
    ),
    ConversationScenario(
        id="S050", category="interest", name="Ese me gusta",
        messages=["Ese me gusta"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["excelente", "elección", "talla", "color", "gusta"],
        description="'Ese me gusta' debe cerrar en el producto.",
    ),

    # =========================================================================
    # SIZING QUERIES (51-60)
    # =========================================================================
    ConversationScenario(
        id="S051", category="sizing", name="Talla M hay",
        messages=["Talla M hay?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas", "te recomiendo",
                            "catálogo", "lista de productos"],
        expected_patterns=["talla M", "disponible", "reserve", "stock",
                           "separo", "enviamos", "casa", "recoger", "listo",
                           "buenísima", "decisión", "talla"],
        description="Pregunta de talla debe responder directamente, no listar catálogo.",
    ),
    ConversationScenario(
        id="S052", category="sizing", name="Tienes talla L",
        messages=["Tienes talla L?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["talla L", "disponible", "reserve"],
        description="Pregunta directa de talla debe responder disponibilidad.",
    ),
    ConversationScenario(
        id="S053", category="sizing", name="En qué tallas lo tienes",
        messages=["En qué tallas lo tienes?"],
        forbidden_patterns=["te recomiendo estas opciones"],
        expected_patterns=["talla", "disponible"],
        description="Pregunta de tallas disponibles debe listar tallas, no catálogo.",
    ),
    ConversationScenario(
        id="S054", category="sizing", name="Talla S disponible",
        messages=["La talla S está disponible?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["talla S", "disponible", "sí"],
        description="Consulta de talla específica debe responder directamente.",
    ),
    ConversationScenario(
        id="S055", category="sizing", name="Talla XL",
        messages=["Talla XL?"],
        forbidden_patterns=["tenemos estas opciones", "catálogo"],
        expected_patterns=["talla XL", "disponible"],
        description="Talla específica debe tener respuesta directa.",
    ),
    ConversationScenario(
        id="S056", category="sizing", name="Hay en talla grande",
        messages=["Hay en talla grande?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["talla", "grande", "disponible", "L", "XL"],
        description="Talla grande debe responder sobre disponibilidad L/XL.",
    ),
    ConversationScenario(
        id="S057", category="sizing", name="Me queda la M",
        messages=["Me quedará la M?"],
        forbidden_patterns=["tenemos estas opciones"],
        expected_patterns=["talla M", "medidas", "guía", "disponible"],
        description="Consulta de ajuste debe responder sobre talla M.",
    ),
    ConversationScenario(
        id="S058", category="sizing", name="Talla + color",
        messages=["Talla M en negro?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["talla M", "negro", "disponible"],
        description="Talla + color debe responder combinación específica.",
    ),
    ConversationScenario(
        id="S059", category="sizing", name="Manejan talla XS",
        messages=["Manejan talla XS?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["talla XS", "disponible", "XS"],
        description="Talla pequeña debe tener respuesta directa.",
    ),
    ConversationScenario(
        id="S060", category="sizing", name="Talla después de elegir",
        messages=["Me gusta la casaca. Talla M hay?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas", "te recomiendo estas"],
        expected_patterns=["casaca", "talla M", "disponible", "reserve"],
        description="Talla después de elegir producto debe responder específicamente.",
    ),

    # =========================================================================
    # COLOR QUERIES (61-65)
    # =========================================================================
    ConversationScenario(
        id="S061", category="color", name="En negro hay",
        messages=["En negro lo tienen?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["negro", "disponible", "color"],
        description="Consulta de color debe responder directamente.",
    ),
    ConversationScenario(
        id="S062", category="color", name="Colores disponibles",
        messages=["Qué colores tienen?"],
        forbidden_patterns=["te recomiendo estas opciones"],
        expected_patterns=["color", "disponible", "tenemos"],
        description="Pregunta de colores debe listar colores.",
    ),
    ConversationScenario(
        id="S063", category="color", name="En blanco",
        messages=["Lo quiero en blanco"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["blanco", "disponible", "talla"],
        description="'Lo quiero en blanco' debe confirmar color y seguir a talla.",
    ),
    ConversationScenario(
        id="S064", category="color", name="Prefiero azul",
        messages=["Prefiero el azul"],
        forbidden_patterns=["tenemos estas opciones"],
        expected_patterns=["azul", "disponible", "talla"],
        description="Preferencia de color debe confirmar disponibilidad.",
    ),
    ConversationScenario(
        id="S065", category="color", name="Tiene en rojo",
        messages=["Tiene en rojo?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["rojo", "disponible", "color"],
        description="Color específico debe responder directamente.",
    ),

    # =========================================================================
    # COMMITMENT / READY TO BUY (66-75)
    # =========================================================================
    ConversationScenario(
        id="S066", category="commitment", name="Lo compro",
        messages=["Me gusta el jean cargo. Lo compro."],
        forbidden_patterns=["tenemos estas opciones", "mira estas", "te recomiendo estas"],
        expected_patterns=["jean", "cargo", "talla", "color", "comprar", "reservar"],
        description="Decisión de compra debe iniciar proceso de cierre.",
    ),
    ConversationScenario(
        id="S067", category="commitment", name="Reservar",
        messages=["Quiero reservar el polo premium"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["reservar", "polo", "talla", "color"],
        description="Intención de reserva debe iniciar cierre.",
    ),
    ConversationScenario(
        id="S068", category="commitment", name="Cómo lo pido",
        messages=["Cómo lo pido?"],
        forbidden_patterns=["tenemos estas opciones", "te recomiendo estas"],
        expected_patterns=["pedido", "comprar", "delivery", "proceso", "pago"],
        description="'Cómo lo pido' debe explicar proceso de compra.",
    ),
    ConversationScenario(
        id="S069", category="commitment", name="Separar producto",
        messages=["Quiero separar la casaca oversize"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["separar", "casaca", "oversize", "talla", "color"],
        description="'Separar' debe accionar proceso de reserva.",
    ),
    ConversationScenario(
        id="S070", category="commitment", name="Delivery",
        messages=["Hacen delivery?"],
        forbidden_patterns=["tenemos estas opciones"],
        expected_patterns=["delivery", "envío", "domicilio", "sí"],
        description="Pregunta de delivery debe responder directamente.",
    ),
    ConversationScenario(
        id="S071", category="commitment", name="Cuánto cuesta",
        messages=["Cuánto cuesta?"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["precio", "cuesta", "soles", "USD"],
        description="Pregunta de precio debe responder con precio.",
    ),
    ConversationScenario(
        id="S072", category="commitment", name="Medios de pago",
        messages=["Qué medios de pago aceptan?"],
        forbidden_patterns=["te recomiendo estas", "mira estas opciones"],
        expected_patterns=["pago", "tarjeta", "transferencia", "yape", "plin"],
        description="Medios de pago debe informar, no vender más.",
    ),
    ConversationScenario(
        id="S073", category="commitment", name="Confirmar compra",
        messages=["Dale, confírmame el pedido"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["confirmar", "pedido", "talla", "color", "dirección"],
        description="Confirmación de compra debe proceder con datos de envío.",
    ),
    ConversationScenario(
        id="S074", category="commitment", name="Ya lo quiero",
        messages=["Ya lo quiero, cómo hago?"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["comprar", "pedido", "proceso", "talla", "color"],
        description="'Ya lo quiero' debe guiar al usuario al proceso de compra.",
    ),
    ConversationScenario(
        id="S075", category="commitment", name="Apartar modelo",
        messages=["Quiero apartar ese modelo"],
        forbidden_patterns=["tenemos estas opciones", "mira estas"],
        expected_patterns=["apartar", "modelo", "talla", "color", "reserva"],
        description="'Apartar' debe iniciar proceso de reserva.",
    ),

    # =========================================================================
    # OBJECTIONS (76-85)
    # =========================================================================
    ConversationScenario(
        id="S076", category="objection", name="No me convenció",
        messages=["No me convenció"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas", "tenemos estas"],
        expected_patterns=["entiendo", "qué fue", "no te convenció", "estilo", "color",
                           "precio", "tipo de prenda"],
        description="'No me convenció' debe explorar la objeción, NO listar más productos.",
    ),
    ConversationScenario(
        id="S077", category="objection", name="Muy caro",
        messages=["Está muy caro"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["precio", "caro", "opciones", "alternativa", "económico"],
        description="Objeción de precio debe manejar la objeción, no forzar venta.",
    ),
    ConversationScenario(
        id="S078", category="objection", name="No me gusta",
        messages=["No me gusta ese modelo"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["entiendo", "gustaría", "alternativa", "qué buscas"],
        description="No gustar un modelo debe explorar preferencias.",
    ),
    ConversationScenario(
        id="S079", category="objection", name="Quiero ver más opciones",
        messages=["Quiero ver más opciones"],
        forbidden_patterns=[],
        expected_patterns=["opciones", "alternativas", "claro", "muestro"],
        description="Pedir más opciones SÍ debe mostrar alternativas.",
    ),
    ConversationScenario(
        id="S080", category="objection", name="No me alcanza",
        messages=["No me alcanza el presupuesto"],
        forbidden_patterns=["te recomiendo estas opciones"],
        expected_patterns=["presupuesto", "opciones", "económico", "alternativa"],
        description="Problema de presupuesto debe ofrecer alternativas económicas.",
    ),
    ConversationScenario(
        id="S081", category="objection", name="Lo voy a pensar",
        messages=["Lo voy a pensar"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["tiempo", "pienses", "disponible", "cuando quieras"],
        description="'Lo voy a pensar' debe dar espacio, no presionar.",
    ),
    ConversationScenario(
        id="S082", category="objection", name="No estoy seguro",
        messages=["No estoy seguro"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["seguro", "tiempo", "ayudar", "dudas"],
        description="Inseguridad debe ser apoyada, no forzada.",
    ),
    ConversationScenario(
        id="S083", category="objection", name="Prefiero ver en tienda",
        messages=["Prefiero verlo en tienda primero"],
        forbidden_patterns=["te recomiendo estas opciones"],
        expected_patterns=["tienda", "ver", "dirección", "claro", "por supuesto"],
        description="Preferencia de tienda física debe ser respetada.",
    ),
    ConversationScenario(
        id="S084", category="objection", name="No me convence el color",
        messages=["No me convence el color"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["color", "gustaría", "alternativa", "disponible"],
        description="Objeción de color debe ofrecer alternativas de color.",
    ),
    ConversationScenario(
        id="S085", category="objection", name="Muy grande/muy pequeño",
        messages=["Me queda muy grande"],
        forbidden_patterns=["te recomiendo estas opciones"],
        expected_patterns=["talla", "cambiar", "menor", "disponible", "medidas"],
        description="Problema de talla debe ofrecer cambio de talla.",
    ),

    # =========================================================================
    # NON-EXISTENT PRODUCTS (86-95)
    # =========================================================================
    ConversationScenario(
        id="S086", category="nonexistent", name="Producto que no existe",
        messages=["Tienen medias negras?"],
        forbidden_patterns=["inventar", "crear", "media", "calcetín", "no contamos"],
        expected_patterns=["no tengo", "disponible", "contamos con", "polos", "casacas",
                           "jeans", "zapatillas"],
        description="Producto inexistente: NO inventar, ofrecer categorías reales.",
    ),
    ConversationScenario(
        id="S087", category="nonexistent", name="Corbata",
        messages=["Busco una corbata roja"],
        forbidden_patterns=["inventar", "corbata"],
        expected_patterns=["no tengo", "disponible", "contamos con"],
        description="Corbata no existe en catálogo. No inventar.",
    ),
    ConversationScenario(
        id="S088", category="nonexistent", name="Traje de baño",
        messages=["Tienen trajes de baño?"],
        forbidden_patterns=["inventar"],
        expected_patterns=["no tengo", "disponible"],
        description="Traje de baño no existe. Informar sin inventar.",
    ),
    ConversationScenario(
        id="S089", category="nonexistent", name="Pijama",
        messages=["Venden pijamas?"],
        forbidden_patterns=["inventar", "pijama"],
        expected_patterns=["no tengo", "disponible"],
        description="Pijama no existe. Informar sin inventar.",
    ),
    ConversationScenario(
        id="S090", category="nonexistent", name="Ropa de bebé",
        messages=["Tienen ropa de bebé?"],
        forbidden_patterns=["inventar"],
        expected_patterns=["no tengo", "bebé", "disponible"],
        description="Ropa de bebé no existe. Informar sin inventar.",
    ),
    ConversationScenario(
        id="S091", category="nonexistent", name="Abrigo de invierno",
        messages=["Busco un abrigo de invierno"],
        forbidden_patterns=["inventar", "abrigo"],
        expected_patterns=["no tengo", "disponible", "casaca", "chompa", "parka"],
        description="Abrigo no existe como categoría, sugerir casacas/chompas.",
    ),
    ConversationScenario(
        id="S092", category="nonexistent", name="Ropa deportiva específica",
        messages=["Tienen leggins?"],
        forbidden_patterns=["inventar", "leggins"],
        expected_patterns=["no tengo", "disponible", "deportivo", "short", "top"],
        description="Leggins no existen. Informar y sugerir alternativas reales.",
    ),
    ConversationScenario(
        id="S093", category="nonexistent", name="Accesorio inexistente",
        messages=["Tienen aretes?"],
        forbidden_patterns=["inventar"],
        expected_patterns=["no tengo", "disponible", "accesorios"],
        description="Aretes no existen. Informar sin inventar.",
    ),
    ConversationScenario(
        id="S094", category="nonexistent", name="Producto mal escrito",
        messages=["Tienen poler?"],
        forbidden_patterns=["inventar"],
        expected_patterns=["polos", "chompas", "hoodies"],
        description="Producto mal escrito debe interpretar y responder con alternativas reales.",
    ),
    ConversationScenario(
        id="S095", category="nonexistent", name="Marca específica",
        messages=["Tienen Nike?"],
        forbidden_patterns=["inventar", "Nike no"],
        expected_patterns=["no tenemos", "marca", "propia", "modelos"],
        description="Marca específica no disponible. Informar sin inventar.",
    ),

    # =========================================================================
    # CATEGORY CHANGES (96-100)
    # =========================================================================
    ConversationScenario(
        id="S096", category="category_change", name="Cambio de categoría",
        messages=[
            "Me gusta la casaca oversize",
            "En realidad, mejor muéstrame polos",
        ],
        forbidden_patterns=[],
        expected_patterns=["polo", "claro", "cambio", "polos"],
        description="Cambio de categoría debe ser soportado naturalmente.",
    ),
    ConversationScenario(
        id="S097", category="category_change", name="Primero ver luego decidir",
        messages=[
            "Qué casacas tienen?",
            "Y también jeans?",
            "Prefiero los jeans",
        ],
        forbidden_patterns=[],
        expected_patterns=["jean", "claro", "prefieres"],
        description="Navegar entre categorías debe ser fluido.",
    ),
    ConversationScenario(
        id="S098", category="category_change", name="De hombre a mujer",
        messages=[
            "Ropa de hombre",
            "Y para mujer qué tienen?",
        ],
        forbidden_patterns=[],
        expected_patterns=["mujer", "claro", "tenemos"],
        description="Cambio de género debe ser soportado.",
    ),
    ConversationScenario(
        id="S099", category="category_change", name="Multi-categoría",
        messages=["Tienen polos y jeans?"],
        forbidden_patterns=[],
        expected_patterns=["polo", "jean", "polos", "jeans"],
        description="Preguntar por múltiples categorías debe responder ambas.",
    ),
    ConversationScenario(
        id="S100", category="category_change", name="Exploración general",
        messages=["Qué tienen de ropa?"],
        forbidden_patterns=["no tengo", "no disponible"],
        expected_patterns=["tenemos", "categorías", "polos", "casacas", "jeans", "zapatillas"],
        description="Pregunta general debe listar categorías disponibles.",
    ),

    # =========================================================================
    # HESITATION (101-105)
    # =========================================================================
    ConversationScenario(
        id="S101", category="hesitation", name="No sé",
        messages=["No sé"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["tiempo", "ayudar", "buscas", "preferencias"],
        description="'No sé' debe ser apoyado sin presión.",
    ),
    ConversationScenario(
        id="S102", category="hesitation", name="Tal vez",
        messages=["Tal vez después"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["tiempo", "cuando quieras", "disponible"],
        description="'Tal vez' debe dar espacio.",
    ),
    ConversationScenario(
        id="S103", category="hesitation", name="Lo consulto",
        messages=["Lo consulto y te escribo"],
        forbidden_patterns=["te recomiendo estas opciones"],
        expected_patterns=["claro", "consultes", "cuando quieras"],
        description="'Lo consulto' debe ser respetado.",
    ),
    ConversationScenario(
        id="S104", category="hesitation", name="Déjame pensar",
        messages=["Déjame pensar"],
        forbidden_patterns=["te recomiendo estas opciones"],
        expected_patterns=["tiempo", "pienses", "cuando quieras"],
        description="'Déjame pensar' debe dar espacio.",
    ),
    ConversationScenario(
        id="S105", category="hesitation", name="Mmm no sé",
        messages=["Mmm no sé"],
        forbidden_patterns=["te recomiendo estas opciones", "mira estas"],
        expected_patterns=["tiempo", "ayudar", "buscas", "preferencias"],
        description="Hesitación debe ser apoyada.",
    ),

    # =========================================================================
    # COMPARISONS (106-110)
    # =========================================================================
    ConversationScenario(
        id="S106", category="comparison", name="Comparar dos modelos",
        messages=["Cuál es mejor, el polo premium o el polo básico?"],
        forbidden_patterns=["te recomiendo estas opciones"],
        expected_patterns=["polo", "premium", "básico", "diferencia", "comparar"],
        description="Comparación debe explicar diferencias.",
    ),
    ConversationScenario(
        id="S107", category="comparison", name="Cuál recomiendas",
        messages=["Cuál me recomiendas?"],
        forbidden_patterns=[],
        expected_patterns=["recomiendo", "opción", "gusta", "estilo"],
        description="Recomendación debe basarse en preferencias.",
    ),
    ConversationScenario(
        id="S108", category="comparison", name="Diferencia de precios",
        messages=["Cuál es la diferencia de precio entre estos dos?"],
        forbidden_patterns=[],
        expected_patterns=["precio", "diferencia", "valor"],
        description="Diferencia de precio debe ser explicada.",
    ),
    ConversationScenario(
        id="S109", category="comparison", name="Calidad vs precio",
        messages=["Vale la pena el más caro?"],
        forbidden_patterns=[],
        expected_patterns=["calidad", "precio", "material", "vale la pena", "duradero"],
        description="'Vale la pena' debe argumentar calidad/precio.",
    ),
    ConversationScenario(
        id="S110", category="comparison", name="Versus",
        messages=["Casaca vs chompa, qué me recomiendas para el frío?"],
        forbidden_patterns=[],
        expected_patterns=["casaca", "chompa", "frío", "recomiendo", "abrigo"],
        description="Comparación para clima debe recomendar según necesidad.",
    ),
]


def get_scenarios_by_category(category: str) -> list[ConversationScenario]:
    return [s for s in SCENARIOS if s.category == category]


def get_all_scenarios() -> list[ConversationScenario]:
    return SCENARIOS


CATEGORIES: dict[str, str] = {
    "greeting": "Greetings — 10 scenarios",
    "gratitude": "Gratitude — 10 scenarios",
    "farewell": "Farewell / Closing — 10 scenarios",
    "casual": "Casual chat / Status — 10 scenarios",
    "interest": "Product interest — 10 scenarios",
    "sizing": "Sizing queries — 10 scenarios",
    "color": "Color queries — 5 scenarios",
    "commitment": "Commitment / Ready to buy — 10 scenarios",
    "objection": "Objections — 10 scenarios",
    "nonexistent": "Non-existent products — 10 scenarios",
    "category_change": "Category changes — 5 scenarios",
    "hesitation": "Hesitation — 5 scenarios",
    "comparison": "Comparisons — 5 scenarios",
}


def print_summary() -> None:
    print(f"\n{'='*60}")
    print(f"  SALES CONVERSATION SCENARIOS — QA SUITE")
    print(f"{'='*60}")
    print(f"\nTotal scenarios: {len(SCENARIOS)}")
    print(f"\nCategories:")
    for cat, desc in CATEGORIES.items():
        count = len(get_scenarios_by_category(cat))
        print(f"  • {desc} ({count})")
    print(f"\n{'='*60}")
