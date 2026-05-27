"""
Seed script: populates the database with realistic Peruvian/Latam fashion demo data.

Usage:
    python -m seed

Requires the database to exist and alembic migrations to be up-to-date.
"""

import asyncio
import logging
import sys
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select, text

from app.core.config import get_settings
from app.database.models import import_all_models
from app.database.session import AsyncSessionLocal, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("seed")

import_all_models()

from app.modules.auth.models import EmpresaUsuario, Usuario
from app.modules.companies.models import Empresa
from app.modules.conversations.models import Conversation, Message
from app.modules.customers.models import Cliente
from app.modules.products.models import ProductImage, ProductVariant, Producto

# ---------------------------------------------------------------------------
# Customers – 18 realistic Peruvian/Latam fashion buyers
# ---------------------------------------------------------------------------
CUSTOMERS = [
    # --- VIP customers ---
    {
        "full_name": "Carolina Fernández de la Vega",
        "email": "carolina.fernandez@moda.pe",
        "phone": "+51 999 888 001",
        "whatsapp": "+51 999 888 001",
        "instagram_username": "caro_fashion_vip",
        "tags": ["vip", "compra-recurrente", "coleccion-premium", "vestidos"],
        "notes": "Cliente premium. Compra colecciones completas cada temporada. Prefiere envío a domicilio en San Isidro. Factura corporativa.",
        "lead_status": "won",
        "source": "referido",
    },
    {
        "full_name": "Alejandro Martínez Rivas",
        "email": "alejandro.mr@outlook.pe",
        "phone": "+51 999 888 002",
        "whatsapp": "+51 999 888 002",
        "instagram_username": "ale_mr_lifestyle",
        "tags": ["vip", "casual-premium", "hombre", "pantalones"],
        "notes": "Ejecutivo de banca. Compra casual wear premium cada mes. Factura a su empresa. Envíos a Miraflores.",
        "lead_status": "won",
        "source": "instagram",
    },
    {
        "full_name": "Valentina Paz Castillo",
        "email": "valepaz@cantv.net",
        "phone": "+51 999 888 003",
        "whatsapp": "+51 999 888 003",
        "instagram_username": "vale_paz_style",
        "tags": ["vip", "influencer", "coleccion-verano", "accesorios"],
        "notes": "Influencer de moda con +50K seguidores. Solicita look completo para eventos y sesiones. Descuentos por colaboración.",
        "lead_status": "won",
        "source": "instagram",
    },
    # --- Negotiation leads ---
    {
        "full_name": "Diego Alejandro Torres Mori",
        "email": "diego.torres@modaempresarial.pe",
        "phone": "+51 999 888 004",
        "whatsapp": "+51 999 888 004",
        "instagram_username": None,
        "tags": ["negocio", "corporativo", "trajes", "volumen"],
        "notes": "Gerente de RH interesado en uniformes corporativos para 40 empleados. Negociando precio por volumen. Seguimiento prioritario.",
        "lead_status": "negotiating",
        "source": "whatsapp",
    },
    {
        "full_name": "María José Salazar Benavides",
        "email": "mj.salazar@shoponline.pe",
        "phone": "+51 999 888 005",
        "whatsapp": "+51 999 888 005",
        "instagram_username": "majo_sb_outfits",
        "tags": ["negocio", "boutique", "revendedora", "vestidos"],
        "notes": "Dueña de boutique en Barranco. Quiere comprar 15-20 vestidos por semana para su tienda. Negociando margen mayorista.",
        "lead_status": "negotiating",
        "source": "whatsapp",
    },
    # --- Abandoned cart customers ---
    {
        "full_name": "Franco Andre Seminario Paz",
        "email": "franco.seminario@gmail.com",
        "phone": "+51 999 888 006",
        "whatsapp": None,
        "instagram_username": "franco_sp",
        "tags": ["carrito-abandonado", "hombre", "hoodie", "descuento"],
        "notes": "Agregó Hoodie Essentials y Jean Cargo al carrito pero no completó compra. Enviar recordatorio con 10% off.",
        "lead_status": "interested",
        "source": "instagram",
    },
    {
        "full_name": "Andrea Milagros Córdova López",
        "email": "andreacordova@yahoo.pe",
        "phone": "+51 999 888 007",
        "whatsapp": None,
        "instagram_username": "andy_cordova",
        "tags": ["carrito-abandonado", "mujer", "blazer", "rebaja"],
        "notes": "Vio el Blazer Ivory Elite tres veces. Lo dejó en carrito por $189. Enviar cupón de $20 off.",
        "lead_status": "interested",
        "source": "instagram",
    },
    {
        "full_name": "Gabriela Sofía Huamán Quispe",
        "email": "gabriela.hq@hotmail.com",
        "phone": "+51 999 888 008",
        "whatsapp": None,
        "instagram_username": "gabb_hmn",
        "tags": ["carrito-abandonado", "vestido", "mujer", "evento"],
        "notes": "Dejó el Vestido Milano en carrito hace 3 días. Busca vestido para boda. Enviar fotos de combinaciones con accesorios.",
        "lead_status": "new",
        "source": "facebook",
    },
    # --- Returning customers ---
    {
        "full_name": "Renato Alonso Paredes Gálvez",
        "email": "renato.paredes@icloud.com",
        "phone": "+51 999 888 009",
        "whatsapp": "+51 999 888 009",
        "instagram_username": "renato_pg",
        "tags": ["recurrente", "hombre", "casaca", "jeans", "leal"],
        "notes": "Compra cada 45 días aprox. Prefiere Casacas Oversize y Jean Cargo. Tiene historial de 7 compras. Enviar preview de nueva colección.",
        "lead_status": "won",
        "source": "whatsapp",
    },
    {
        "full_name": "Ximena Lucía Ramírez Alvarado",
        "email": "ximena.ramirez@outlook.pe",
        "phone": "+51 999 888 010",
        "whatsapp": "+51 999 888 010",
        "instagram_username": "xime_ral",
        "tags": ["recurrente", "mujer", "accesorios", "bolsos"],
        "notes": "Clienta fiel desde el lanzamiento. Compra accesorios y bolsos cada mes. Excelente referente para nuevas clientas.",
        "lead_status": "won",
        "source": "whatsapp",
    },
    {
        "full_name": "Sergio Martín Cárdenas Tello",
        "email": "sergio.ct@modaurbana.pe",
        "phone": "+51 999 888 011",
        "whatsapp": None,
        "instagram_username": "sergio_ct_urban",
        "tags": ["recurrente", "hombre", "urbano", "jogger", "polos"],
        "notes": "Compra ropa urbana cada 3 semanas. Fan del Jogger Street Pro y los polos Premium. Enviar novedades de la línea urban.",
        "lead_status": "won",
        "source": "instagram",
    },
    {
        "full_name": "Paola Andrea Pizarro Neyra",
        "email": "paola.pizarro@gmail.com",
        "phone": "+51 999 888 012",
        "whatsapp": "+51 999 888 012",
        "instagram_username": "pao_pizarro",
        "tags": ["recurrente", "mujer", "vestidos", "elegante", "vip"],
        "notes": "Abogada en estudio corporativo. Compra vestidos elegantes y blazers para eventos y oficina. Envíos a San Borja.",
        "lead_status": "won",
        "source": "referido",
    },
    # --- Instagram leads ---
    {
        "full_name": "Luciana Fernanda Vega Ríos",
        "email": "luciana.vega@instagram.com",
        "phone": "+51 999 888 013",
        "whatsapp": "+51 999 888 013",
        "instagram_username": "lu_vega_fashion",
        "tags": ["instagram", "lead", "mujer", "verano"],
        "notes": "Llegó por anuncio de Instagram. Interesada en colección de verano. Preguntó por precios de tops y shorts.",
        "lead_status": "interested",
        "source": "instagram",
    },
    {
        "full_name": "Jorge Luis Bellido Pacheco",
        "email": "jorge.bellido@instagram.com",
        "phone": "+51 999 888 014",
        "whatsapp": None,
        "instagram_username": "jorgeluis_bp",
        "tags": ["instagram", "lead", "hombre", "polos"],
        "notes": "Dio like a historias de polos Premium Black. Consultó por tallas disponibles y precio.",
        "lead_status": "new",
        "source": "instagram",
    },
    {
        "full_name": "Camila Alessandra Torres Luna",
        "email": "camila.torres@instagram.com",
        "phone": "+51 999 888 015",
        "whatsapp": "+51 999 888 015",
        "instagram_username": "cami_torres_l",
        "tags": ["instagram", "lead", "mujer", "blazer", "office"],
        "notes": "Influencer micro (8K seguidores). Interesada en blazers y ropa de oficina. Propuesta de colaboración pendiente.",
        "lead_status": "interested",
        "source": "instagram",
    },
    # --- WhatsApp leads ---
    {
        "full_name": "Rodrigo Alonso Mendoza Salas",
        "email": "rodrigo.mendoza@whatsapp.com",
        "phone": "+51 999 888 016",
        "whatsapp": "+51 999 888 016",
        "instagram_username": None,
        "tags": ["whatsapp", "lead", "hombre", "casaca", "pantalon"],
        "notes": "Contactó por WhatsApp Business preguntando por casacas de invierno. Enviar catálogo de casacas Oversize.",
        "lead_status": "interested",
        "source": "whatsapp",
    },
    {
        "full_name": "María Fernanda Gutiérrez del Solar",
        "email": "mafe.gutierrez@whatsapp.com",
        "phone": "+51 999 888 017",
        "whatsapp": "+51 999 888 017",
        "instagram_username": "mafe_gs",
        "tags": ["whatsapp", "lead", "mujer", "accesorios", "bolsos"],
        "notes": "Preguntó por carteras y accesorios por WhatsApp. Le interesa la colección de bolsos de cuero.",
        "lead_status": "new",
        "source": "whatsapp",
    },
    {
        "full_name": "Patricia del Rosario Zavala Mejía",
        "email": "patricia.zavala@whatsapp.com",
        "phone": "+51 999 888 018",
        "whatsapp": "+51 999 888 018",
        "instagram_username": None,
        "tags": ["whatsapp", "lead", "mujer", "emprendedora", "uniformes"],
        "notes": "Emprendedora con equipo de 12 personas. Quiere comprar polos personalizados con logo. Solicita cotización por WhatsApp.",
        "lead_status": "negotiating",
        "source": "whatsapp",
    },
]

# ---------------------------------------------------------------------------
# Products – 24 realistic fashion products
# ---------------------------------------------------------------------------
PRODUCTS = [
    {
        "name": "Casaca Oversize Urban",
        "category": "Casacas",
        "base_price": "249.90",
        "description": "Casaca oversize con corte urbano y acabado premium. Confeccionada en algodón pesado con capucha ajustable y bolsillos amplios. Ideal para el clima de Lima y el estilo streetwear peruano.",
        "status": "active",
        "slug": "casaca-oversize-urban",
    },
    {
        "name": "Polo Premium Black",
        "category": "Polos",
        "base_price": "89.90",
        "description": "Polo de algodón pima peruano con acabado satinado. Cuello estructurado y botones de carey. Corte regular fit que se mantiene impecable lavada tras lavada.",
        "status": "active",
        "slug": "polo-premium-black",
    },
    {
        "name": "Jean Cargo Street",
        "category": "Pantalones",
        "base_price": "179.90",
        "description": "Jean cargo de corte recto con bolsillos laterales funcionales. Mezclilla elástica que se adapta al movimiento. Cierre de botón oculto y detalles en costura contrastante.",
        "status": "active",
        "slug": "jean-cargo-street",
    },
    {
        "name": "Hoodie Essentials",
        "category": "Hoodies",
        "base_price": "149.90",
        "description": "Hoodie de felpa francesa con bolsillo canguro y capucha forrada. Corte holgado con puños acanalados. La prenda básica de cualquier armario casual peruano.",
        "status": "active",
        "slug": "hoodie-essentials",
    },
    {
        "name": "Vestido Milano",
        "category": "Vestidos",
        "base_price": "259.90",
        "description": "Vestido midi con silueta envuelta y manga francesa. Estampado floral italiano sobre fondo negro. Tela viscolisa con caída elegante ideal para bodas y eventos de noche.",
        "status": "active",
        "slug": "vestido-milano",
    },
    {
        "name": "Blazer Ivory Elite",
        "category": "Blazers",
        "base_price": "389.90",
        "description": "Blazer sastre color marfil confeccionado en tejido de mezcla de lana. Forro interior de seda artificial, solapa con pico y dos botones frontales. Corte entallado premium.",
        "status": "active",
        "slug": "blazer-ivory-elite",
    },
    {
        "name": "Jogger Street Pro",
        "category": "Pantalones",
        "base_price": "129.90",
        "description": "Jogger de algodón con cintura elastizada y cordón ajustable. Bolsillos laterales profudos y puños tobilleros. Corte moderno para el día a día urbano.",
        "status": "active",
        "slug": "jogger-street-pro",
    },
    {
        "name": "Chompa Cardigan Luna",
        "category": "Chompas",
        "base_price": "199.90",
        "description": "Cardigan largo tejido en punto grueso con botones forrados. Bolsillos de parche y caída suave. Perfecto para las noches frescas de la costa peruana.",
        "status": "active",
        "slug": "chompa-cardigan-luna",
    },
    {
        "name": "Top Deportivo Fit",
        "category": "Tops",
        "base_price": "69.90",
        "description": "Top deportivo de secado rápido con soporte integrado. Espalda descubierta con tiras ajustables. Ideal para yoga, pilates y entrenamiento funcional.",
        "status": "active",
        "slug": "top-deportivo-fit",
    },
    {
        "name": "Camisa Oxford Azul",
        "category": "Camisas",
        "base_price": "119.90",
        "description": "Camisa Oxford en algodón 100% con tejido en espiga. Bolsillo frontal, cuello abotonable y puños ajustables. Clásico renovado para la oficina moderna.",
        "status": "active",
        "slug": "camisa-oxford-azul",
    },
    {
        "name": "Short Bermudas Cargo",
        "category": "Shorts",
        "base_price": "99.90",
        "description": "Bermuda cargo con cuatro bolsillos funcionales y cinturón ajustable. Tela gabardina resistente. El short ideal para el verano limeño.",
        "status": "active",
        "slug": "short-bermudas-cargo",
    },
    {
        "name": "Cartera Tote Milano",
        "category": "Accesorios",
        "base_price": "189.90",
        "description": "Tote bag de cuero sintético premium con acabado piel grabada. Compartimento principal con cierre y bolsillo interior para celular. Capacidad para laptop de 14 pulgadas.",
        "status": "active",
        "slug": "cartera-tote-milano",
    },
    {
        "name": "Mochila Urban Explorer",
        "category": "Accesorios",
        "base_price": "159.90",
        "description": "Mochila urbana con compartimento acolchado para laptop de 15 pulgadas. Bolsillo organizador frontal y laterales para botella. Cierre hermético anti-lluvia.",
        "status": "active",
        "slug": "mochila-urban-explorer",
    },
    {
        "name": "Cinturón Essential Cuero",
        "category": "Accesorios",
        "base_price": "79.90",
        "description": "Cinturón de cuero genuino con hebilla pulida cromada. Ancho de 3.5 cm, corte clásico que combina con todo. Hebilla intercambiable.",
        "status": "active",
        "slug": "cinturon-essential-cuero",
    },
    {
        "name": "Polo Algodón Pima",
        "category": "Polos",
        "base_price": "79.90",
        "description": "Polo clásico de algodón pima peruano. Corte regular fit, cuello redondo y mangas cortas. Suavidad incomparable que dura temporada tras temporada.",
        "status": "active",
        "slug": "polo-algodon-pima",
    },
    {
        "name": "Jean Slim Fit Azul",
        "category": "Pantalones",
        "base_price": "169.90",
        "description": "Jean slim fit en azul índigo profundo. Mezclilla con elasticidad para máxima comodidad. Cinco bolsillos clásicos y cierre de botón.",
        "status": "active",
        "slug": "jean-slim-fit-azul",
    },
    {
        "name": "Vestido Negra Noche",
        "category": "Vestidos",
        "base_price": "299.90",
        "description": "Vestido largo negro de gala con escote profundo y espalda descubierta. Cierre lateral invisible y apertura lateral en la pierna. Tela satinada con caída impecable.",
        "status": "active",
        "slug": "vestido-negra-noche",
    },
    {
        "name": "Blazer Negro Ejecutivo",
        "category": "Blazers",
        "base_price": "429.90",
        "description": "Blazer ejecutivo negro de construcción sartorial. Dos botones, solapa recta y bolsillos de ojal. Forro completo y entretela canadiense. Hecho para el profesional peruano.",
        "status": "active",
        "slug": "blazer-negro-ejecutivo",
    },
    {
        "name": "Casco Inverno Parka",
        "category": "Casacas",
        "base_price": "349.90",
        "description": "Parka invernal con relleno térmico y capucha desmontable forrada en piel sintética. Impermeable y cortaviento con costuras selladas. Para el frío extremo de la sierra peruana.",
        "status": "active",
        "slug": "casco-inverno-parka",
    },
    {
        "name": "Hoodie Premium Algodón",
        "category": "Hoodies",
        "base_price": "169.90",
        "description": "Hoodie premium de algodón orgánico con estampado minimalista. Bolsillo canguro con entrada para audífonos. Corte moderno y lavado stone.",
        "status": "active",
        "slug": "hoodie-premium-algodon",
    },
    {
        "name": "Chompa Cuello Tortuga",
        "category": "Chompas",
        "base_price": "139.90",
        "description": "Chompa de cuello tortuga en tejido de punto fino. Algodón mezcla con elastano para ajuste perfecto. Clásico atemporal para el armario de oficina.",
        "status": "active",
        "slug": "chompa-cuello-tortuga",
    },
    {
        "name": "Short Deportivo Run",
        "category": "Shorts",
        "base_price": "69.90",
        "description": "Short deportivo con interior de malla y cintura elastizada. Bolsillo con cierre para llaves y celular. Tejido de secado rápido y peso ligero.",
        "status": "active",
        "slug": "short-deportivo-run",
    },
    {
        "name": "Camisa Premium Lino",
        "category": "Camisas",
        "base_price": "149.90",
        "description": "Camisa de lino 100% en corte relajado. Ideal para el clima cálido peruano. Botones de concha natural y detalles en costura doble. Fresca y elegante.",
        "status": "active",
        "slug": "camisa-premium-lino",
    },
    {
        "name": "Top Jersey Algodón",
        "category": "Tops",
        "base_price": "59.90",
        "description": "Top jersey de algodón suave con cuello redondo y corte crop. Costura lateral invisible y dobladillo limpio. Básico esencial para capas y looks casuales.",
        "status": "active",
        "slug": "top-jersey-algodon",
    },
    {
        "name": "Zapatillas Urban Street",
        "category": "Zapatillas",
        "base_price": "289.90",
        "description": "Zapatillas urbanas con silueta contemporánea. Parte superior de gamuza y malla técnica, suela de caucho vulcanizado con amortiguación reactiva. Diseño low-top versátil para el día a día.",
        "status": "active",
        "slug": "zapatillas-urban-street",
    },
    {
        "name": "Casaca Denim Black",
        "category": "Casacas",
        "base_price": "219.90",
        "description": "Casaca de mezclilla negra con lavado stone envejecido. Cuello clásico con botones metálicos, bolsillos de parche y ajuste en la cintura con botones laterales.",
        "status": "active",
        "slug": "casaca-denim-black",
    },
    {
        "name": "Blusa Satin Luxe",
        "category": "Blusas",
        "base_price": "139.90",
        "description": "Blusa satinada con caída sedosa y cuello en pico profundo. Manga larga con puño abotonado y espalda con pinzas de entalle. Ideal para office wear nocturno.",
        "status": "active",
        "slug": "blusa-satin-luxe",
    },
    {
        "name": "Falda Minimal Beige",
        "category": "Faldas",
        "base_price": "149.90",
        "description": "Falda lápiz minimalista en color beige. Cierre oculto lateral, cintura ancha estructurada y abertura trasera para facilidad de movimiento. Tela de mezcla de viscosa con elastano.",
        "status": "active",
        "slug": "falda-minimal-beige",
    },
    {
        "name": "Polo Oversize Tokyo",
        "category": "Polos",
        "base_price": "99.90",
        "description": "Polo oversize con manga voluminosa y cuello caído. Bordado minimalista en el pecho. Corte relajado inspirado en la moda callejera japonesa. Algodón 100% peinado.",
        "status": "active",
        "slug": "polo-oversize-tokyo",
    },
    {
        "name": "Jogger Cargo Elite",
        "category": "Pantalones",
        "base_price": "159.90",
        "description": "Jogger cargo premium con bolsillos utilitarios laterales y traseros. Cintura elastizada con cordón de algodón grueso. Corte cónico con puños tobilleros. Tela ripstop resistente.",
        "status": "active",
        "slug": "jogger-cargo-elite",
    },
    {
        "name": "Camisa Linen Summer",
        "category": "Camisas",
        "base_price": "129.90",
        "description": "Camisa ligera de lino 100% con mezcla de viscosa, mangas cortas enrollables con presilla. Corte relajado con botones de concha natural. Frescura garantizada para el verano peruano.",
        "status": "active",
        "slug": "camisa-linen-summer",
    },
    {
        "name": "Vestido Sunset Rose",
        "category": "Vestidos",
        "base_price": "279.90",
        "description": "Vestido midi con estampado abstracto en tonos rosados y naranja. Corte en línea A con cintura imperio. Escote en V profundo y mangas globo. Tela viscosa satinada con forro interior.",
        "status": "active",
        "slug": "vestido-sunset-rose",
    },
    {
        "name": "Hoodie Techwear Pro",
        "category": "Hoodies",
        "base_price": "199.90",
        "description": "Hoodie techwear con bolsillo canguro modular y sistema de cierres ocultos. Capucha ajustable con visera rígida. Algodón técnico con tratamiento repelente al agua y costuras termoselladas.",
        "status": "active",
        "slug": "hoodie-techwear-pro",
    },
    {
        "name": "Blazer Executive Noir",
        "category": "Blazers",
        "base_price": "459.90",
        "description": "Blazer de alta dirección en negro profundo. Construcción semiestructurada con hombros naturales. Forro interior completo con bolsillo para reloj. Detalle de ojal en solapa hecho a mano.",
        "status": "active",
        "slug": "blazer-executive-noir",
    },
    {
        "name": "Chompa Alpaca Premium",
        "category": "Chompas",
        "base_price": "259.90",
        "description": "Chompa tejida en alpaca baby 100% peruana. Punto de espiga con acabado artesanal. Cuello redondo y mangas largas con puños acanalados. Suavidad y calidez incomparables.",
        "status": "active",
        "slug": "chompa-alpaca-premium",
    },
    {
        "name": "Jean Slim Fit Blue",
        "category": "Pantalones",
        "base_price": "189.90",
        "description": "Jean slim fit en azul medio con lavado stone clásico. Mezclilla con elastano para confort total. Cinco bolsillos con costura en contraste y cierre de botón metálico grabado.",
        "status": "active",
        "slug": "jean-slim-fit-blue",
    },
    {
        "name": "Top Active Motion",
        "category": "Tops",
        "base_price": "79.90",
        "description": "Top deportivo de alto rendimiento con compresión ligera. Tejido Dry-Fit con paneles de malla transpirable. Espalda cruzada con apertura y sujetador integrado de soporte medio.",
        "status": "active",
        "slug": "top-active-motion",
    },
    {
        "name": "Shorts Sport Flex",
        "category": "Shorts",
        "base_price": "89.90",
        "description": "Short deportivo con cintura elastizada y bolsillo lateral con cierre impermeable. Forro interior de compresión. Tejido de secado ultrarrápido con tratamiento antibacteriano.",
        "status": "active",
        "slug": "shorts-sport-flex",
    },
    {
        "name": "Cartera Urban Chic",
        "category": "Carteras",
        "base_price": "249.90",
        "description": "Cartera bandolera de cuero genuino con costura artesanal. Compartimento principal con organización interior, bolsillo acolchado para tablet y correa ajustable de hombro. Hebilla dorada pulida.",
        "status": "active",
        "slug": "cartera-urban-chic",
    },
    {
        "name": "Mochila Tech Minimal",
        "category": "Mochilas",
        "base_price": "199.90",
        "description": "Mochila minimalista con compartimento acolchado para laptop de 16 pulgadas. Cierre bidireccional enrollable impermeable. Bolsillo oculto antirrobo en la espalda y puerto USB externo.",
        "status": "active",
        "slug": "mochila-tech-minimal",
    },
    {
        "name": "Gorro Street Classic",
        "category": "Gorros",
        "base_price": "49.90",
        "description": "Gorro streetwear de punto grueso con dobladillo doble y logo bordado. Algodón acrílico suave. Diseño clásico cuffed que se adapta a cualquier estilo urbano.",
        "status": "active",
        "slug": "gorro-street-classic",
    },
    {
        "name": "Polo Basic White",
        "category": "Polos",
        "base_price": "69.90",
        "description": "Polo básico blanco de algodón pima peruano. Corte regular fit, cuello redondo reforzado que no pierde forma. El esencial de todo armario. Pack disponible de 3 unidades.",
        "status": "active",
        "slug": "polo-basic-white",
    },
    {
        "name": "Casaca Leather Rider",
        "category": "Casacas",
        "base_price": "499.90",
        "description": "Casaca de cuero genuino estilo rider con cierre asimétrico. Forro interior de poliéster con mezcla de algodón. Cremalleras metálicas, cuello con botón de presión y hombreras sutiles.",
        "status": "active",
        "slug": "casaca-leather-rider",
    },
    {
        "name": "Vestido Elegant Night",
        "category": "Vestidos",
        "base_price": "349.90",
        "description": "Vestido largo de gala en azul medianoche con pedrería sutil en el escote. Silueta sirena con falda drapeada y cola ligera. Cierre lateral invisible y espalda con abertura en V profunda.",
        "status": "active",
        "slug": "vestido-elegant-night",
    },
    {
        "name": "Camisa Oversize Korean",
        "category": "Camisas",
        "base_price": "119.90",
        "description": "Camisa oversize de influencia coreana con cuello mao y mangas amplias. Bolsillo frontal único y botones de contraste. Corte cuadrado que cae suelto sobre la cadera.",
        "status": "active",
        "slug": "camisa-oversize-korean",
    },
    {
        "name": "Pantalón Formal Milano",
        "category": "Pantalones",
        "base_price": "199.90",
        "description": "Pantalón de vestir corte recto italiano. Tela de mezcla de lana peinada con elastano. Pinzas frontales, bolsillos con ribete y basta ajustable. Perfecto para el ejecutivo peruano.",
        "status": "active",
        "slug": "pantalon-formal-milano",
    },
    {
        "name": "Sweater Nordic Winter",
        "category": "Sweaters",
        "base_price": "229.90",
        "description": "Sweater navideño de punto grueso con patrón geométrico nórdico. Cuello redondo alto, manga larga y dobladillo con punto elástico. Lana merino mezcla con acrílico para calidez sin peso.",
        "status": "active",
        "slug": "sweater-nordic-winter",
    },
    {
        "name": "Chaleco Urban Layer",
        "category": "Chalecos",
        "base_price": "169.90",
        "description": "Chaleco acolchado ligero con cierre frontal y bolsillos con cremallera. Tejido exterior anti-viento con forro térmico. Capucha desmontable y dobladillo ajustable con cordón.",
        "status": "active",
        "slug": "chaleco-urban-layer",
    },
    {
        "name": "Polo Deportivo Runner",
        "category": "Polos",
        "base_price": "89.90",
        "description": "Polo deportivo de manga corta con tejido Dry-Fit y paneles laterales de malla. Cuello redondo con detalle reflectivo para seguridad nocturna. Corte atlético para máximo rendimiento.",
        "status": "active",
        "slug": "polo-deportivo-runner",
    },
]

# ---------------------------------------------------------------------------
# Variant templates – sizes × colors with realistic SKU patterns
# ---------------------------------------------------------------------------
SIZES = ["S", "M", "L", "XL"]
COLORS = ["Negro", "Beige", "Azul", "Gris", "Blanco"]

# Which products get which size/color combos based on category
PRODUCT_VARIANT_PLANS = {
    "Casacas": {"sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Beige", "Gris", "Azul"]},
    "Polos": {"sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Blanco", "Azul", "Gris"]},
    "Pantalones": {"sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Azul", "Beige", "Gris"]},
    "Hoodies": {"sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Gris", "Beige", "Azul"]},
    "Vestidos": {"sizes": ["S", "M", "L"], "colors": ["Negro", "Azul", "Blanco", "Beige"]},
    "Blazers": {"sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Beige", "Azul", "Gris"]},
    "Chompas": {"sizes": ["S", "M", "L", "XL"], "colors": ["Beige", "Negro", "Gris", "Azul"]},
    "Tops": {"sizes": ["S", "M", "L"], "colors": ["Negro", "Blanco", "Beige", "Gris"]},
    "Camisas": {"sizes": ["S", "M", "L", "XL"], "colors": ["Blanco", "Azul", "Beige", "Negro"]},
    "Shorts": {"sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Beige", "Azul", "Gris"]},
    "Accesorios": None,  # no variants for accessories
    "Zapatillas": {"sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Blanco", "Azul", "Gris"]},
    "Blusas": {"sizes": ["S", "M", "L", "XL"], "colors": ["Blanco", "Negro", "Beige", "Azul"]},
    "Faldas": {"sizes": ["S", "M", "L"], "colors": ["Negro", "Beige", "Azul", "Gris"]},
    "Carteras": None,
    "Mochilas": None,
    "Gorros": {"sizes": ["S", "M", "L"], "colors": ["Negro", "Gris", "Beige", "Azul"]},
    "Sweaters": {"sizes": ["S", "M", "L", "XL"], "colors": ["Gris", "Beige", "Negro", "Azul"]},
    "Chalecos": {"sizes": ["S", "M", "L", "XL"], "colors": ["Negro", "Gris", "Azul", "Beige"]},
}

# ---------------------------------------------------------------------------
# Image URLs – Unsplash fashion images (direct source URLs)
# ---------------------------------------------------------------------------
# Using Unsplash with specific fashion-related search params for reliable images
IMAGE_URLS = {
    "Casaca Oversize Urban": [
        "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=600&h=800&fit=crop",
    ],
    "Polo Premium Black": [
        "https://images.unsplash.com/photo-1586363104862-3a5e2ab60d99?w=600&h=800&fit=crop",
    ],
    "Jean Cargo Street": [
        "https://images.unsplash.com/photo-1542272454315-4c01d7abdf4a?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1604176354204-9268737828e4?w=600&h=800&fit=crop",
    ],
    "Hoodie Essentials": [
        "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=600&h=800&fit=crop",
    ],
    "Vestido Milano": [
        "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=600&h=800&fit=crop",
    ],
    "Blazer Ivory Elite": [
        "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1591369822096-5e2a31f31806?w=600&h=800&fit=crop",
    ],
    "Jogger Street Pro": [
        "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1552902865-b72c031ac5ea?w=600&h=800&fit=crop",
    ],
    "Chompa Cardigan Luna": [
        "https://images.unsplash.com/photo-1434389677669-e08b4cda3a0b?w=600&h=800&fit=crop",
    ],
    "Top Deportivo Fit": [
        "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&h=800&fit=crop",
    ],
    "Camisa Oxford Azul": [
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600&h=800&fit=crop",
    ],
    "Short Bermudas Cargo": [
        "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600&h=800&fit=crop",
    ],
    "Cartera Tote Milano": [
        "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?w=600&h=800&fit=crop",
    ],
    "Mochila Urban Explorer": [
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&h=800&fit=crop",
    ],
    "Cinturón Essential Cuero": [
        "https://images.unsplash.com/photo-1624222247344-550fb60583dc?w=600&h=800&fit=crop",
    ],
    "Polo Algodón Pima": [
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=600&h=800&fit=crop",
    ],
    "Jean Slim Fit Azul": [
        "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600&h=800&fit=crop",
    ],
    "Vestido Negra Noche": [
        "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&h=800&fit=crop",
    ],
    "Blazer Negro Ejecutivo": [
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=800&fit=crop",
    ],
    "Casco Inverno Parka": [
        "https://images.unsplash.com/photo-1544022613-e87ca75a784a?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1539533113208-f6df8cc8b543?w=600&h=800&fit=crop",
    ],
    "Hoodie Premium Algodón": [
        "https://images.unsplash.com/photo-1578768079052-aa76e52ff62e?w=600&h=800&fit=crop",
    ],
    "Chompa Cuello Tortuga": [
        "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&h=800&fit=crop",
    ],
    "Short Deportivo Run": [
        "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=600&h=800&fit=crop",
    ],
    "Camisa Premium Lino": [
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600&h=800&fit=crop",
    ],
    "Top Jersey Algodón": [
        "https://images.unsplash.com/photo-1564257631407-4deb1f99d992?w=600&h=800&fit=crop",
    ],
    "Zapatillas Urban Street": [
        "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=600&h=800&fit=crop",
    ],
    "Casaca Denim Black": [
        "https://images.unsplash.com/photo-1601333144130-8cbb312386b6?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600&h=800&fit=crop",
    ],
    "Blusa Satin Luxe": [
        "https://images.unsplash.com/photo-1608236415051-8c1d4f0b3ae7?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1624206112918-f40f1fe4a7c9?w=600&h=800&fit=crop",
    ],
    "Falda Minimal Beige": [
        "https://images.unsplash.com/photo-1583496661160-fb5886a0aaaa?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=600&h=800&fit=crop",
    ],
    "Polo Oversize Tokyo": [
        "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&h=800&fit=crop",
    ],
    "Jogger Cargo Elite": [
        "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1552902865-b72c031ac5ea?w=600&h=800&fit=crop",
    ],
    "Camisa Linen Summer": [
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600&h=800&fit=crop",
    ],
    "Vestido Sunset Rose": [
        "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=600&h=800&fit=crop",
    ],
    "Hoodie Techwear Pro": [
        "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1578768079052-aa76e52ff62e?w=600&h=800&fit=crop",
    ],
    "Blazer Executive Noir": [
        "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&h=800&fit=crop",
    ],
    "Chompa Alpaca Premium": [
        "https://images.unsplash.com/photo-1434389677669-e08b4cda3a0b?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600&h=800&fit=crop",
    ],
    "Jean Slim Fit Blue": [
        "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600&h=800&fit=crop",
    ],
    "Top Active Motion": [
        "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&h=800&fit=crop",
    ],
    "Shorts Sport Flex": [
        "https://images.unsplash.com/photo-1517457373958-b7bdd4587205?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?w=600&h=800&fit=crop",
    ],
    "Cartera Urban Chic": [
        "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?w=600&h=800&fit=crop",
    ],
    "Mochila Tech Minimal": [
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1622560480605-d83c853bc5c3?w=600&h=800&fit=crop",
    ],
    "Gorro Street Classic": [
        "https://images.unsplash.com/photo-1576871337632-b9aef4c17ab9?w=600&h=800&fit=crop",
    ],
    "Polo Basic White": [
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=600&h=800&fit=crop",
    ],
    "Casaca Leather Rider": [
        "https://images.unsplash.com/photo-1520975954732-35dd22299614?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=600&h=800&fit=crop",
    ],
    "Vestido Elegant Night": [
        "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&h=800&fit=crop",
    ],
    "Camisa Oversize Korean": [
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600&h=800&fit=crop",
    ],
    "Pantalón Formal Milano": [
        "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600&h=800&fit=crop",
    ],
    "Sweater Nordic Winter": [
        "https://images.unsplash.com/photo-1434389677669-e08b4cda3a0b?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600&h=800&fit=crop",
    ],
    "Chaleco Urban Layer": [
        "https://images.unsplash.com/photo-1544022613-e87ca75a784a?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?w=600&h=800&fit=crop",
    ],
    "Polo Deportivo Runner": [
        "https://images.unsplash.com/photo-1586363104862-3a5e2ab60d99?w=600&h=800&fit=crop",
        "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&h=800&fit=crop",
    ],
}


# ---------------------------------------------------------------------------
# Seed logic
# ---------------------------------------------------------------------------
async def seed() -> None:
    logger.info("=" * 60)
    logger.info("  SEED: AI Sales Agent SaaS — Demo Data Generator")
    logger.info("=" * 60)

    settings = get_settings()
    logger.info("Database: %s", settings.database_url.replace("://", "://***:***@"))

    async with AsyncSessionLocal() as session:
        # ---- 1. Ensure empresa exists ---------------------------------------
        result = await session.execute(select(Empresa).limit(1))
        empresa = result.scalar_one_or_none()

        if empresa is None:
            logger.info("No empresa found. Creating demo company...")
            empresa = Empresa(
                nombre="Fashion Sales AI — Demo",
                slug="fashion-sales-ai-demo",
                estado="active",
            )
            session.add(empresa)
            await session.flush()

            demo_user = Usuario(
                email="demo@fashionsales.ai",
                password_hash="$2b$12$pUqeFLpZGsg8BQN.rPXNCeYat192.JqvQuOxnlks3Dy4HWM2l6uPK",
                estado="active",
            )
            session.add(demo_user)
            await session.flush()

            membership = EmpresaUsuario(
                empresa_id=empresa.id,
                usuario_id=demo_user.id,
                rol="admin",
                estado="active",
            )
            session.add(membership)
            await session.flush()
            await session.commit()
            logger.info("  ✓ Empresa created: %s (%s)", empresa.nombre, empresa.id)
            logger.info("  ✓ User created: demo@fashionsales.ai / password: Demo@2024!")
        else:
            logger.info("  ✓ Empresa found: %s (%s)", empresa.nombre, empresa.id)
            # Check if demo user exists for this empresa
            demo_user = (
                await session.execute(
                    select(Usuario).where(Usuario.email == "demo@fashionsales.ai")
                )
            ).scalar_one_or_none()
            if demo_user is None:
                import bcrypt
                password_hash = bcrypt.hashpw(
                    b"Demo@2024!", bcrypt.gensalt()
                ).decode("utf-8")
                demo_user = Usuario(
                    email="demo@fashionsales.ai",
                    password_hash=password_hash,
                    estado="active",
                )
                session.add(demo_user)
                await session.flush()

                membership = EmpresaUsuario(
                    empresa_id=empresa.id,
                    usuario_id=demo_user.id,
                    rol="admin",
                    estado="active",
                )
                session.add(membership)
                await session.flush()
                logger.info("  ✓ Demo user created for existing empresa")
            else:
                logger.info("  ✓ Demo user already exists")

        empresa_id = empresa.id

        # ---- 2. Clean existing seed data ------------------------------------
        logger.info("Cleaning existing data...")

        await session.execute(
            ProductImage.__table__.delete().where(
                ProductImage.empresa_id == empresa_id
            )
        )
        logger.info("  ✓ Product images cleaned")

        await session.execute(
            ProductVariant.__table__.delete().where(
                ProductVariant.empresa_id == empresa_id
            )
        )
        logger.info("  ✓ Product variants cleaned")

        await session.execute(
            Producto.__table__.delete().where(Producto.empresa_id == empresa_id)
        )
        logger.info("  ✓ Products cleaned")

        await session.execute(
            Message.__table__.delete().where(Message.empresa_id == empresa_id)
        )
        logger.info("  ✓ Messages cleaned")

        await session.execute(
            Conversation.__table__.delete().where(Conversation.empresa_id == empresa_id)
        )
        logger.info("  ✓ Conversations cleaned")

        await session.execute(
            Cliente.__table__.delete().where(Cliente.empresa_id == empresa_id)
        )
        logger.info("  ✓ Customers cleaned")

        await session.commit()
        logger.info("  ✓ All seed data removed")

        # ---- 3. Seed customers ----------------------------------------------
        logger.info("\nSeeding customers...")
        customer_count = 0
        for data in CUSTOMERS:
            customer = Cliente(
                empresa_id=empresa_id,
                full_name=data["full_name"],
                email=data["email"],
                phone=data.get("phone"),
                whatsapp=data.get("whatsapp"),
                instagram_username=data.get("instagram_username"),
                tags=data["tags"],
                notes=data["notes"],
                lead_status=data["lead_status"],
                source=data["source"],
            )
            session.add(customer)
            customer_count += 1

        await session.flush()
        logger.info("  ✓ %d customers created", customer_count)

        # ---- 4. Seed products -----------------------------------------------
        logger.info("\nSeeding products...")
        product_count = 0
        variant_count = 0
        image_count = 0

        for prod_data in PRODUCTS:
            product = Producto(
                empresa_id=empresa_id,
                name=prod_data["name"],
                slug=prod_data["slug"],
                category=prod_data["category"],
                base_price=Decimal(prod_data["base_price"]),
                description=prod_data["description"],
                status=prod_data["status"],
            )
            session.add(product)
            await session.flush()
            product_count += 1

            # ---- 4a. Seed variants ------------------------------------------
            plan = PRODUCT_VARIANT_PLANS.get(prod_data["category"])
            if plan:
                for size in plan["sizes"]:
                    for color in plan["colors"]:
                        sku_base = prod_data["slug"].upper().replace("-", "")
                        sku = f"{sku_base}-{size}-{color[:3].upper()}"

                        # Realistic stock levels
                        import random
                        total_stock = random.randint(12, 80)
                        reserved = random.randint(0, min(5, total_stock // 4))

                        # Some variants get a price surcharge
                        price_surcharge = None
                        if size == "XL" and random.random() < 0.3:
                            price_surcharge = str(
                                Decimal(prod_data["base_price"]) + Decimal("20.00")
                            )

                        variant = ProductVariant(
                            empresa_id=empresa_id,
                            product_id=product.id,
                            talla=size,
                            color=color,
                            sku=sku,
                            stock=total_stock,
                            reserved_stock=reserved,
                            variant_price=price_surcharge,
                        )
                        session.add(variant)
                        variant_count += 1

            # ---- 4b. Seed images --------------------------------------------
            urls = IMAGE_URLS.get(prod_data["name"], [])
            for idx, url in enumerate(urls):
                image = ProductImage(
                    empresa_id=empresa_id,
                    product_id=product.id,
                    image_url=url,
                    order_index=idx,
                )
                session.add(image)
                image_count += 1

        await session.commit()
        logger.info("  ✓ %d products created", product_count)
        logger.info("  ✓ %d variants created", variant_count)
        logger.info("  ✓ %d images attached", image_count)

        # ---- 5. Seed conversations -------------------------------------------
        logger.info("\nSeeding conversations & messages...")

        # get all created customers for this empresa
        result = await session.execute(
            select(Cliente).where(Cliente.empresa_id == empresa_id)
        )
        all_customers = {c.full_name: c for c in result.scalars().all()}

        def _customer(name: str) -> Cliente:
            return all_customers[name]

        from datetime import timedelta

        conversation_count = 0
        message_count = 0

        # --- Conversation 1: VIP negotiation ---
        conv1 = Conversation(
            empresa_id=empresa_id,
            cliente_id=_customer("Diego Alejandro Torres Mori").id,
            asunto="Cotización uniformes corporativos — 40 empleados",
            canal="whatsapp",
            estado="open",
            created_at=datetime.now(UTC) - timedelta(days=5),
            updated_at=datetime.now(UTC) - timedelta(hours=2),
        )
        session.add(conv1)
        await session.flush()
        conversation_count += 1

        conv1_msgs = [
            ("client", "Hola, soy Diego Torres, gerente de RH de CorpModa Perú. ¿Me pueden dar una cotización para uniformes corporativos? Somos 40 personas.", "Diego Torres", conv1.created_at),
            ("agent", "¡Hola Diego! Claro que sí. Con gusto te cotizamos uniformes para tu equipo. ¿Qué tipo de prendas necesitas y en qué plazo?", "María (Ventas)", conv1.created_at + timedelta(minutes=15)),
            ("client", "Necesito polos con logo bordado, pantalones de vestir y casacas ligeras. Para empezar, 40 de cada uno. El logo te lo envío por separado.", "Diego Torres", conv1.created_at + timedelta(hours=1)),
            ("agent", "Perfecto. Te preparo una cotización detallada. Los polos Premium Black bordados van a S/ 109.90 c/u, los pantalones formal Milano a S/ 199.90 y las casacas ligeras alrededor de S/ 249.90. ¿Te parece si te envío la propuesta completa mañana?", "María (Ventas)", conv1.created_at + timedelta(hours=2)),
            ("client", "Sí, por favor. El precio me parece razonable para la calidad que veo en su catálogo. ¿Hay descuento por volumen?", "Diego Torres", conv1.created_at + timedelta(hours=3)),
            ("agent", "¡Claro! Para pedidos corporativos de 40+ unidades te damos 12% de descuento en la orden total. Te envío la cotización formal mañana antes del mediodía.", "María (Ventas)", conv1.created_at + timedelta(hours=3, minutes=30)),
            ("client", "Excelente, quedo atento. Gracias.", "Diego Torres", conv1.created_at + timedelta(days=1)),
            ("agent", "¡Buenos días Diego! Aquí te va la cotización completa con descuento corporativo incluido. Quedamos atentos a tu respuesta.", "María (Ventas)", datetime.now(UTC) - timedelta(hours=2)),
        ]
        for role, content, sender, ts in conv1_msgs:
            m = Message(empresa_id=empresa_id, conversation_id=conv1.id, role=role, content=content, sender_name=sender, created_at=ts, updated_at=ts)
            session.add(m)
            message_count += 1

        # --- Conversation 2: Instagram lead ---
        conv2 = Conversation(
            empresa_id=empresa_id,
            cliente_id=_customer("Luciana Fernanda Vega Ríos").id,
            asunto="Consulta colección verano — Instagram",
            canal="instagram",
            estado="open",
            created_at=datetime.now(UTC) - timedelta(days=2),
            updated_at=datetime.now(UTC) - timedelta(hours=6),
        )
        session.add(conv2)
        await session.flush()
        conversation_count += 1

        conv2_msgs = [
            ("client", "Hola! Vi su colección de verano en Instagram y me encantó. ¿Me pueden decir precios de los tops y shorts que aparecen en el reel?", "Luciana Vega", conv2.created_at),
            ("agent", "¡Hola Luciana! Qué alegría que te guste nuestra colección. Los tops deportivos están desde S/ 69.90 y los shorts desde S/ 89.90. ¿Te interesa alguna combinación en especial?", "Carlos (Social)", conv2.created_at + timedelta(minutes=10)),
            ("client", "Sí, el Top Deportivo Fit en negro y el Short Sport Flex en beige. ¿Tienen disponibles en talla M?", "Luciana Vega", conv2.created_at + timedelta(hours=1)),
            ("agent", "Ambos los tenemos en talla M 🙌 El Top Deportivo Fit en negro y el Short Sport Flex en beige están en stock. ¿Te los enviamos a domicilio? Tenemos delivery en Lima metropolitana.", "Carlos (Social)", conv2.created_at + timedelta(hours=1, minutes=20)),
            ("client", "Genial! Sí, vivo en Miraflores. ¿Cuánto es el delivery y en cuánto tiempo llega?", "Luciana Vega", conv2.created_at + timedelta(hours=2)),
            ("agent", "El delivery a Miraflores es S/ 12 y llega en 24-48 horas hábiles. En compras mayores a S/ 200 el envío es gratis 😊", "Carlos (Social)", datetime.now(UTC) - timedelta(hours=6)),
        ]
        for role, content, sender, ts in conv2_msgs:
            m = Message(empresa_id=empresa_id, conversation_id=conv2.id, role=role, content=content, sender_name=sender, created_at=ts, updated_at=ts)
            session.add(m)
            message_count += 1

        # --- Conversation 3: WhatsApp lead - accessories ---
        conv3 = Conversation(
            empresa_id=empresa_id,
            cliente_id=_customer("María Fernanda Gutiérrez del Solar").id,
            asunto="Consulta bolsos de cuero — WhatsApp",
            canal="whatsapp",
            estado="pending",
            created_at=datetime.now(UTC) - timedelta(days=1),
            updated_at=datetime.now(UTC) - timedelta(hours=10),
        )
        session.add(conv3)
        await session.flush()
        conversation_count += 1

        conv3_msgs = [
            ("client", "Hola, les escribo por WhatsApp porque vi que tienen bolsos de cuero. ¿Me pueden mostrar la colección completa?", "María Fernanda Gutiérrez", conv3.created_at),
            ("agent", "¡Hola María Fernanda! Claro, con gusto. Tenemos dos modelos principales: la Cartera Tote Milano en S/ 189.90 y la Cartera Urban Chic en S/ 249.90. La Urban Chic es de cuero genuino. ¿Te interesa alguna en particular?", "Lucía (Ventas)", conv3.created_at + timedelta(minutes=8)),
            ("client", "La Urban Chic me llama la atención. ¿De qué colores está disponible y tiene correa larga?", "María Fernanda Gutiérrez", conv3.created_at + timedelta(hours=1)),
            ("agent", "Sí, viene con correa ajustable para usarla como bandolera. Está disponible en negro, beige y marrón. El interior tiene compartimento para tablet. Es súper práctica 😊", "Lucía (Ventas)", conv3.created_at + timedelta(hours=1, minutes=15)),
            ("client", "El beige me encanta. ¿Puedo pasar a verla a su tienda?", "María Fernanda Gutiérrez", datetime.now(UTC) - timedelta(hours=10)),
        ]
        for role, content, sender, ts in conv3_msgs:
            m = Message(empresa_id=empresa_id, conversation_id=conv3.id, role=role, content=content, sender_name=sender, created_at=ts, updated_at=ts)
            session.add(m)
            message_count += 1

        # --- Conversation 4: VIP returning customer ---
        conv4 = Conversation(
            empresa_id=empresa_id,
            cliente_id=_customer("Renato Alonso Paredes Gálvez").id,
            asunto="Consulta nueva colección hombre",
            canal="manual",
            estado="closed",
            created_at=datetime.now(UTC) - timedelta(days=10),
            updated_at=datetime.now(UTC) - timedelta(days=8),
        )
        session.add(conv4)
        await session.flush()
        conversation_count += 1

        conv4_msgs = [
            ("client", "¡Buenas! Soy Renato, cliente frecuente. Quería saber si ya llegó la nueva colección de casacas oversize.", "Renato Paredes", conv4.created_at),
            ("agent", "¡Renato! Claro que sí, acaba de llegar. Tenemos la Casaca Denim Black (S/ 219.90) y la Casaca Leather Rider (S/ 499.90). ¿Te gustaría ver fotos?", "María (Ventas)", conv4.created_at + timedelta(minutes=5)),
            ("client", "Sí, mándame fotos de la Denim Black. ¿En talla L la tienen?", "Renato Paredes", conv4.created_at + timedelta(hours=2)),
            ("agent", "Te envío fotos por aquí. En talla L la tenemos en negro y azul. ¿Te parece si te la reservo?", "María (Ventas)", conv4.created_at + timedelta(hours=2, minutes=10)),
            ("client", "Dale, la quiero en negro talla L. ¿Me la puedes dejar separada? Paso a recoger mañana.", "Renato Paredes", conv4.created_at + timedelta(hours=3)),
            ("agent", "Reservada ✅ Te esperamos mañana. Cualquier cosa me avisas.", "María (Ventas)", conv4.created_at + timedelta(hours=3, minutes=15)),
            ("client", "Ya pasé a recoger la casaca, todo bien. ¡Gracias!", "Renato Paredes", conv4.created_at + timedelta(days=1)),
            ("agent", "¡Qué bien! Que la disfrutes, Renato. Cualquier cosa aquí estamos.", "María (Ventas)", conv4.created_at + timedelta(days=1, hours=1)),
        ]
        for role, content, sender, ts in conv4_msgs:
            m = Message(empresa_id=empresa_id, conversation_id=conv4.id, role=role, content=content, sender_name=sender, created_at=ts, updated_at=ts)
            session.add(m)
            message_count += 1

        # --- Conversation 5: Abandoned cart recovery ---
        conv5 = Conversation(
            empresa_id=empresa_id,
            cliente_id=_customer("Franco Andre Seminario Paz").id,
            asunto="Recordatorio carrito — Hoodie + Jean",
            canal="instagram",
            estado="open",
            created_at=datetime.now(UTC) - timedelta(days=3),
            updated_at=datetime.now(UTC) - timedelta(hours=12),
        )
        session.add(conv5)
        await session.flush()
        conversation_count += 1

        conv5_msgs = [
            ("agent", "¡Hola Franco! 🖐️ Vimos que dejaste la Hoodie Essentials y el Jean Cargo Street en tu carrito. ¿Te gustaría completar tu compra? Te podemos dar un 10% de descuento en tu primera orden.", "Sistema", conv5.created_at),
            ("client", "Oh sí, estaba viendo eso. La hoodie me interesa pero no estoy seguro de la talla. ¿Cómo es el fit?", "Franco Seminario", conv5.created_at + timedelta(hours=2)),
            ("agent", "La Hoodie Essentials es corte holgado (oversize). Si usas M regular, la hoodie en M te quedará suelta pero cómoda. Para un fit más ajustado te recomiendo S. ¿Qué talla usas normalmente?", "Sistema", conv5.created_at + timedelta(hours=2, minutes=5)),
            ("client", "Uso M normalmente. Creo que la M estaría bien entonces. ¿El descuento still aplica?", "Franco Seminario", conv5.created_at + timedelta(days=1)),
            ("agent", "¡Sí! El 10% de descuento sigue disponible. Solo tienes que completar la compra 😊", "Sistema", datetime.now(UTC) - timedelta(hours=12)),
        ]
        for role, content, sender, ts in conv5_msgs:
            m = Message(empresa_id=empresa_id, conversation_id=conv5.id, role=role, content=content, sender_name=sender, created_at=ts, updated_at=ts)
            session.add(m)
            message_count += 1

        await session.commit()
        logger.info("  ✓ %d conversations created", conversation_count)
        logger.info("  ✓ %d messages created", message_count)

        # ---- 6. Summary -----------------------------------------------------
        logger.info("\n" + "=" * 60)
        logger.info("  SEED COMPLETE")
        logger.info("=" * 60)
        logger.info("  Customers:      %d", customer_count)
        logger.info("  Products:       %d", product_count)
        logger.info("  Variants:       %d", variant_count)
        logger.info("  Images:         %d", image_count)
        logger.info("  Conversations:  %d", conversation_count)
        logger.info("  Messages:       %d", message_count)
        logger.info("")
        logger.info("  Login: demo@fashionsales.ai")
        logger.info("  Pass:  Demo@2024!")
        logger.info("=" * 60)


async def main() -> None:
    try:
        # Verify database connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection OK")

        await seed()
    except Exception as exc:
        logger.error("Seed failed: %s", exc)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
