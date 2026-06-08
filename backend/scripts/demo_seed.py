"""
demo_seed.py — AI Sales Agent SaaS Enterprise V1 Demo Seed Script

Generates realistic demo data:
  - 100 clients (customers/leads)
  - 20 products with variants
  - 50 pipeline deals
  - 100 orders with items
  - 200 conversations with messages
  - 50 automation tasks
  - Inventory items for all products

Usage:
    python scripts/demo_seed.py [--empresa-slug SLUG] [--tenants TENANT_UUID]

Requires:
    - Running FastAPI backend with DB access
    - Or: DATABASE_URL environment variable for direct connection

Compatible with: PostgreSQL 15+, asyncpg, SQLAlchemy 2.0
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("demo_seed")

FIRST_NAMES = [
    "Sofia", "Mateo", "Valentina", "Santiago", "Isabella",
    "Sebastian", "Camila", "Benjamin", "Luciana", "Gabriel",
    "Maria", "Diego", "Ana", "Carlos", "Laura",
    "Andres", "Fernanda", "Jorge", "Patricia", "Ricardo",
    "Monica", "Alberto", "Daniela", "Fernando", "Veronica",
    "Rosa", "Jose", "Elena", "Manuel", "Silvia",
    "Carmen", "Luis", "Adriana", "Miguel", "Claudia",
    "Teresa", "Antonio", "Gloria", "Francisco", "Diana",
    "Julia", "Rafael", "Liliana", "Enrique", "Pilar",
    "Susana", "Juan", "Alejandra", "Pablo", "Natalia",
    "Cristina", "Hector", "Alicia", "Raul", "Fabiola",
    "Rocio", "Ignacio", "Viviana", "Wanda", "Ximena",
]

LAST_NAMES = [
    "Garcia", "Rodriguez", "Martinez", "Lopez", "Hernandez",
    "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres",
    "Flores", "Rivera", "Gomez", "Diaz", "Moreno",
    "Morales", "Vazquez", "Romero", "Reyes", "Castillo",
    "Alvarez", "Silva", "Mendoza", "Cruz", "Ramos",
    "Ortiz", "Vargas", "Gutierrez", "Molina", "Castro",
    "Delgado", "Guerrero", "Medina", "Aguilar", "Pena",
    "Rios", "Salazar", "Cortes", "Chavez", "Nunez",
    "Miranda", "Velasco", "Marquez", "Luna", "Cardenas",
    "Campos", "Ferrer", "Santos", "Vera", "Paredes",
]

COMPANY_NAMES = [
    "Distribuidora del Sur", "Importadora Norte", "Tienda Online Plus",
    "Boutique Fashion", "Calzados Elite", "ElectroHogar",
    "Deportes Total", "Juguetes & Mas", "Libros y Papel",
    "Belleza Natural", "Muebles Decor", "TecnoMundo",
    "Super Ahorro", "Ropa Casual", "Accesorios Lux",
    "Hogar Inteligente", "Ferreteria Express", "Farmacia Salud",
    "Optica Vision", "Perfumeria Diana",
]

PRODUCTS = [
    ("Camiseta basica", "Ropa", 29.99, "camiseta-basica", ["XS", "S", "M", "L", "XL"], ["Blanco", "Negro", "Gris", "Azul marino"]),
    ("Vestido floral", "Ropa", 89.99, "vestido-floral", ["S", "M", "L"], ["Rojo", "Azul", "Verde"]),
    ("Chaqueta de cuero", "Ropa", 199.99, "chaqueta-cuero", ["S", "M", "L", "XL"], ["Negro", "Marron"]),
    ("Pantalon vaquero", "Ropa", 59.99, "pantalon-vaquero", ["28", "30", "32", "34", "36"], ["Azul", "Negro", "Gris"]),
    ("Zapatillas deportivas", "Calzado", 129.99, "zapatillas-deportivas", ["38", "39", "40", "41", "42", "43", "44"], ["Blanco", "Negro", "Azul", "Rojo"]),
    ("Bolso de mano", "Accesorios", 49.99, "bolso-mano", ["Unico"], ["Negro", "Marron", "Beige"]),
    ("Reloj clasico", "Accesorios", 159.99, "reloj-clasico", ["Unico"], ["Dorado", "Plateado", "Negro"]),
    ("Gafas de sol", "Accesorios", 79.99, "gafas-sol", ["Unico"], ["Negro", "Marron", "Dorado"]),
    ("Cartera de cuero", "Accesorios", 39.99, "cartera-cuero", ["Unico"], ["Negro", "Marron"]),
    ("Bufanda de lana", "Ropa", 34.99, "bufanda-lana", ["Unico"], ["Gris", "Rojo", "Azul", "Verde"]),
    ("Camisa formal", "Ropa", 69.99, "camisa-formal", ["S", "M", "L", "XL"], ["Blanco", "Azul", "Rosa claro"]),
    ("Falda plisada", "Ropa", 54.99, "falda-plisada", ["S", "M", "L"], ["Negro", "Azul marino", "Gris"]),
    ("Chamarra impermeable", "Ropa", 89.99, "chamarra-impermeable", ["S", "M", "L", "XL"], ["Verde", "Azul", "Rojo", "Negro"]),
    ("Mochila urbana", "Accesorios", 69.99, "mochila-urbana", ["Unico"], ["Negro", "Gris", "Azul"]),
    ("Cinturon elegante", "Accesorios", 44.99, "cinturon-elegante", ["80", "85", "90", "95", "100"], ["Negro", "Marron"]),
    ("Pulsera de plata", "Accesorios", 89.99, "pulsera-plata", ["Unico"], ["Plateado"]),
    ("Sombrero playero", "Ropa", 29.99, "sombrero-playero", ["Unico"], ["Beige", "Blanco", "Negro"]),
    ("Chaleco termico", "Ropa", 74.99, "chaleco-termico", ["S", "M", "L", "XL"], ["Negro", "Gris", "Azul"]),
    ("Pijama seda", "Ropa", 64.99, "pijama-seda", ["S", "M", "L"], ["Rosa", "Azul", "Lavanda"]),
    ("Zapatos formales", "Calzado", 149.99, "zapatos-formales", ["39", "40", "41", "42", "43", "44"], ["Negro", "Marron"]),
]

PIPELINE_STAGES = ["new_lead", "contacted", "qualified", "proposal", "negotiation", "won", "lost"]
PIPELINE_ESTIMATED_VALUES = [Decimal(str(v)) for v in [500, 1000, 2000, 3500, 5000, 7500, 10000, 15000, 25000]]

LEAD_SOURCES = ["whatsapp", "instagram", "facebook", "web_form", "referral", "manual", "store"]

CONVERSATION_TOPICS = [
    "Consulta sobre producto", "Seguimiento de pedido", "Devolucion",
    "Informacion de tallas", "Disponibilidad de stock", "Precios y promociones",
    "Personalizacion de productos", "Envio y entregas", "Facturacion",
    "Reclamo por calidad", "Cambio de producto", "Recomendacion de producto",
]

ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
DELIVERY_TYPES = ["pickup", "delivery", "express"]

TASK_TYPES = ["follow_up", "call", "proposal", "meeting", "recovery", "alert"]
TASK_STATUSES = ["pending", "in_progress", "completed", "cancelled"]
TASK_PRIORITIES = ["low", "medium", "high", "critical"]

AUTOMATION_RULES = [
    {
        "rule_key": "follow_up_idle",
        "name": "Seguimiento cliente inactivo",
        "description": "Cliente sin interaccion en 7 dias",
        "trigger_type": "customer_idle",
        "config": {"idle_days": 7},
    },
    {
        "rule_key": "pipeline_stale",
        "name": "Negocio estancado",
        "description": "Negocio sin actividad en 5 dias",
        "trigger_type": "pipeline_stage",
        "config": {"max_idle_days": 5, "stages": ["contacted", "qualified", "proposal", "negotiation"]},
    },
    {
        "rule_key": "new_deal_created",
        "name": "Nuevo negocio creado",
        "description": "Tarea de seguimiento al crear negocio",
        "trigger_type": "pipeline_new",
        "config": {"delay_hours": 24},
    },
    {
        "rule_key": "deal_won",
        "name": "Negocio ganado",
        "description": "Felicitacion y preparacion de envio",
        "trigger_type": "pipeline_won",
        "config": {},
    },
    {
        "rule_key": "deal_lost",
        "name": "Negocio perdido",
        "description": "Registrar razon y recuperacion",
        "trigger_type": "pipeline_lost",
        "config": {"recovery_days": 30},
    },
]


def random_person():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def random_email(name):
    domains = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com.mx", "correo.com"]
    return f"{name.lower().replace(' ', '.')}@{random.choice(domains)}"


def random_phone():
    prefixes = ["55", "56", "81", "33", "44", "66", "77", "99"]
    return f"+52{random.choice(prefixes)}{random.randint(10000000, 99999999)}"


def random_date(days_ago=180):
    return datetime.now(timezone.utc) - timedelta(days=random.randint(0, days_ago))


def random_past_date(days_ago=180, min_days=0):
    return datetime.now(timezone.utc) - timedelta(days=random.randint(min_days, days_ago))


async def get_empresas(session: AsyncSession):
    result = await session.execute(text("SELECT id, slug, nombre FROM empresas ORDER BY created_at"))
    return result.fetchall()


async def get_admin_users(session: AsyncSession):
    result = await session.execute(text("SELECT id, email FROM admin_users ORDER BY created_at"))
    return result.fetchall()


async def get_usuarios(session: AsyncSession):
    result = await session.execute(text("SELECT id FROM usuarios ORDER BY created_at"))
    return result.fetchall()


async def seed_clients(session: AsyncSession, empresa_id: uuid.UUID, count: int = 100):
    logger.info("Seeding %d clients for empresa %s...", count, empresa_id)

    for i in range(count):
        name = random_person()
        email = random_email(name)
        phone = random_phone()
        lead_status = random.choice(["new", "interested", "negotiating", "won", "lost", "new", "new", "interested"])
        source = random.choice(LEAD_SOURCES)
        tags_list = random.sample(["VIP", "recurrente", "nuevo", "alto valor", "pago pendiente", "whatsapp", "instagram"], k=random.randint(0, 3))
        created = random_date(180)

        cliente_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO clientes (id, empresa_id, full_name, email, phone, whatsapp, tags, notes,
                    lead_status, source, lead_score, priority, conversation_count, created_at, updated_at)
                VALUES (:id, :empresa_id, :name, :email, :phone, :whatsapp, :tags, :notes,
                    :status, :source, :score, :priority, :conv_count, :created, :updated)
            """),
            {
                "id": cliente_id,
                "empresa_id": empresa_id,
                "name": name,
                "email": email,
                "phone": phone,
                "whatsapp": phone if random.random() < 0.7 else None,
                "tags": tags_list,
                "notes": f"Cliente {'potencial' if lead_status in ('new','interested') else 'activo'} - fuente: {source}" if random.random() < 0.3 else None,
                "status": lead_status,
                "source": source,
                "score": random.randint(0, 100),
                "priority": random.choice(["cold", "warm", "hot"]),
                "conv_count": random.randint(0, 15),
                "created": created,
                "updated": created + timedelta(hours=random.randint(1, 720)),
            },
        )

    await session.commit()
    logger.info("  -> %d clients created", count)
    return count


async def seed_products(session: AsyncSession, empresa_id: uuid.UUID):
    logger.info("Seeding %d products for empresa %s...", len(PRODUCTS), empresa_id)

    product_ids = []
    for name, category, price, slug, sizes, colors in PRODUCTS:
        product_id = uuid.uuid4()
        created = random_date(180)
        status = "active"
        await session.execute(
            text("""
                INSERT INTO productos (id, empresa_id, name, slug, description, category, base_price, status, created_at, updated_at)
                VALUES (:id, :empresa_id, :name, :slug, :desc, :cat, :price, :status, :created, :updated)
            """),
            {
                "id": product_id,
                "empresa_id": empresa_id,
                "name": name,
                "slug": f"{slug}-{empresa_id.hex[:8]}",
                "desc": f"{name} de alta calidad para tu estilo de vida",
                "cat": category,
                "price": price,
                "status": status,
                "created": created,
                "updated": created + timedelta(hours=random.randint(1, 240)),
            },
        )

        for size in sizes:
            for color in colors:
                if random.random() < 0.6:
                    variant_id = uuid.uuid4()
                    sku = f"{slug[:4].upper()}-{size}-{color[:3].upper()}-{empresa_id.hex[:4]}"
                    stock = random.randint(5, 100)
                    await session.execute(
                        text("""
                            INSERT INTO product_variants (id, empresa_id, product_id, talla, color, sku, stock, reserved_stock, variant_price, created_at, updated_at)
                            VALUES (:id, :empresa_id, :product_id, :size, :color, :sku, :stock, :reserved, :price, :created, :updated)
                        """),
                        {
                            "id": variant_id,
                            "empresa_id": empresa_id,
                            "product_id": product_id,
                            "size": size,
                            "color": color,
                            "sku": sku,
                            "stock": stock,
                            "reserved": random.randint(0, min(10, stock)),
                            "price": price if random.random() < 0.8 else None,
                            "created": created,
                            "updated": created,
                        },
                    )

        product_ids.append(product_id)

    await session.commit()
    logger.info("  -> %d products with variants created", len(PRODUCTS))
    return product_ids


async def seed_inventory(session: AsyncSession, empresa_id: uuid.UUID, product_ids: list):
    logger.info("Seeding inventory for %d products...", len(product_ids))

    for product_id in product_ids:
        stock = random.randint(20, 500)
        min_stock = random.choice([5, 10, 15, 20])
        reserved = random.randint(0, min(30, stock // 3))
        await session.execute(
            text("""
                INSERT INTO inventory_items (id, empresa_id, product_id, stock_actual, stock_minimo, stock_reservado, created_at, updated_at)
                VALUES (:id, :empresa_id, :product_id, :stock, :min_stock, :reserved, :created, :updated)
            """),
            {
                "id": uuid.uuid4(),
                "empresa_id": empresa_id,
                "product_id": product_id,
                "stock": stock,
                "min_stock": min_stock,
                "reserved": reserved,
                "created": random_date(90),
                "updated": random_date(7),
            },
        )

    await session.commit()
    logger.info("  -> %d inventory items created", len(product_ids))


async def seed_pipeline_deals(session: AsyncSession, empresa_id: uuid.UUID, client_ids: list[dict], count: int = 50):
    logger.info("Seeding %d pipeline deals...", count)

    current_time = datetime.now(timezone.utc)

    for i in range(count):
        client = random.choice(client_ids)
        stage = random.choices(
            PIPELINE_STAGES,
            weights=[15, 20, 20, 18, 12, 10, 5],
            k=1,
        )[0]
        estimated_value = random.choice(PIPELINE_ESTIMATED_VALUES)
        probability = {"new_lead": 10, "contacted": 20, "qualified": 40, "proposal": 60, "negotiation": 75, "won": 100, "lost": 0}[stage]
        created = random_date(120)
        stage_entered = created + timedelta(hours=random.randint(1, 720))

        await session.execute(
            text("""
                INSERT INTO sales_pipeline_items (id, empresa_id, customer_id, title, estimated_value, probability,
                    stage, stage_entered_at, last_activity_at, notes, channel, position, is_vip, created_at, updated_at)
                VALUES (:id, :empresa_id, :customer_id, :title, :value, :prob,
                    :stage, :stage_entered, :last_active, :notes, :channel, :pos, :vip, :created, :updated)
            """),
            {
                "id": uuid.uuid4(),
                "empresa_id": empresa_id,
                "customer_id": client["id"],
                "title": f"Venta a {client['name']} - {random.choice(COMPANY_NAMES)}",
                "value": estimated_value,
                "prob": probability,
                "stage": stage,
                "stage_entered": stage_entered,
                "last_active": min(stage_entered + timedelta(hours=random.randint(1, 168)), current_time),
                "notes": random.choice([None, "Cliente interesado en catalogo completo", "Solicito cotizacion", "Negociando condiciones", None, None]),
                "channel": random.choice(["whatsapp", "instagram", "store", "web"]),
                "pos": i % 20,
                "vip": random.random() < 0.1,
                "created": created,
                "updated": created + timedelta(hours=random.randint(1, 720)),
            },
        )

    await session.commit()
    logger.info("  -> %d pipeline deals created", count)


async def seed_conversations_and_messages(session: AsyncSession, empresa_id: uuid.UUID, client_ids: list[dict], count: int = 200):
    logger.info("Seeding %d conversations with messages...", count)

    current_time = datetime.now(timezone.utc)

    for i in range(count):
        client = random.choice(client_ids)
        created = random_date(150)
        estado = random.choice(["open", "closed", "open", "open"])
        conv_id = uuid.uuid4()

        await session.execute(
            text("""
                INSERT INTO conversations (id, empresa_id, cliente_id, asunto, canal, estado, created_at, updated_at)
                VALUES (:id, :empresa_id, :cliente_id, :asunto, :canal, :estado, :created, :updated)
            """),
            {
                "id": conv_id,
                "empresa_id": empresa_id,
                "cliente_id": client["id"],
                "asunto": random.choice(CONVERSATION_TOPICS),
                "canal": random.choice(["whatsapp", "instagram", "web", "manual"]),
                "estado": estado,
                "created": created,
                "updated": created + timedelta(hours=random.randint(1, 96)),
            },
        )

        # Also seed conversation_core
        core_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO conversations_core (id, empresa_id, customer_id, status, last_message, created_at, updated_at)
                VALUES (:id, :empresa_id, :customer_id, :status, :last_msg, :created, :updated)
            """),
            {
                "id": core_id,
                "empresa_id": empresa_id,
                "customer_id": client["id"],
                "status": "active" if estado == "open" else "closed",
                "last_msg": None,
                "created": created,
                "updated": created,
            },
        )

        msg_count = random.randint(2, 12)
        for j in range(msg_count):
            role = "user" if j % 2 == 0 else "assistant"
            sender = client["name"] if role == "user" else "Vendedor IA"
            msg_created = created + timedelta(minutes=j * random.randint(2, 60))

            await session.execute(
                text("""
                    INSERT INTO messages (id, empresa_id, conversation_id, role, content, sender_name, created_at, updated_at)
                    VALUES (:id, :empresa_id, :conv_id, :role, :content, :sender, :created, :updated)
                """),
                {
                    "id": uuid.uuid4(),
                    "empresa_id": empresa_id,
                    "conv_id": conv_id,
                    "role": role,
                    "content": random.choice([
                        "Hola, me gustaria saber mas sobre este producto",
                        "¿Tienen disponible en color rojo?",
                        "Me interesa la talla M, ¿cuanto cuesta?",
                        "¿Hacen envios a toda la Republica?",
                        "¿Cual es el tiempo de entrega?",
                        "Ya recibi mi pedido, ¡muchas gracias!",
                        "¿Puedo hacer un cambio de talla?",
                        "Quisiera cancelar mi pedido",
                        "¿Tienen promociones vigentes?",
                        "Me encanta la calidad del producto, gracias",
                        "¿Aceptan tarjeta de credito?",
                        "¿El producto viene con garantia?",
                    ]),
                    "sender": sender,
                    "created": msg_created,
                    "updated": msg_created,
                },
            )

            # Message core
            await session.execute(
                text("""
                    INSERT INTO messages_core (id, empresa_id, conversation_id, sender, content, created_at, updated_at)
                    VALUES (:id, :empresa_id, :conv_id, :sender, :content, :created, :updated)
                """),
                {
                    "id": uuid.uuid4(),
                    "empresa_id": empresa_id,
                    "conv_id": core_id,
                    "sender": role,
                    "content": random.choice([
                        "Hola, buenos dias! Me interesa un producto",
                        "Si, tenemos disponible en varios colores",
                        "El precio es de $999 MX",
                        "Claro, hacemos envios a todo Mexico",
                        "El tiempo de entrega es de 3-5 dias habiles",
                        "Gracias por tu compra!",
                        "Claro, puedes solicitar el cambio desde tu cuenta",
                        "Procedemos con la cancelacion",
                        "Tenemos 20% de descuento en esta semana",
                        "Gracias por tu preferencia!",
                    ]),
                    "created": msg_created,
                    "updated": msg_created,
                },
            )

        # Update last_message on the core conversation
        await session.execute(
            text("UPDATE conversations_core SET last_message = (SELECT content FROM messages_core WHERE conversation_id = :cid ORDER BY created_at DESC LIMIT 1), updated_at = :now WHERE id = :cid"),
            {"cid": core_id, "now": current_time},
        )
        await session.execute(
            text("UPDATE conversations SET updated_at = :now WHERE id = :cid"),
            {"cid": conv_id, "now": current_time},
        )

        if (i + 1) % 50 == 0:
            await session.commit()
            logger.info("  -> %d conversations committed", i + 1)

    await session.commit()
    logger.info("  -> %d conversations with messages created", count)


async def seed_orders(session: AsyncSession, empresa_id: uuid.UUID, product_ids: list, client_ids: list[dict], count: int = 100):
    logger.info("Seeding %d orders with items...", count)

    for i in range(count):
        client = random.choice(client_ids)
        created = random_date(120)
        status = random.choices(ORDER_STATUSES, weights=[5, 15, 20, 50, 10], k=1)[0]
        delivered = created + timedelta(days=random.randint(1, 7)) if status == "delivered" else None
        order_num = f"ORD-{empresa_id.hex[:4].upper()}-{1000 + i}"

        order_id = uuid.uuid4()
        num_items = random.randint(1, 5)
        total = Decimal("0")

        # Insert order
        await session.execute(
            text("""
                INSERT INTO orders (id, empresa_id, order_number, customer_name, customer_phone,
                    delivery_type, delivery_address, status, total, created_at, updated_at)
                VALUES (:id, :empresa_id, :order_num, :customer, :phone,
                    :delivery, :address, :status, :total, :created, :updated)
            """),
            {
                "id": order_id,
                "empresa_id": empresa_id,
                "order_num": order_num,
                "customer": client["name"],
                "phone": client.get("phone"),
                "delivery": random.choice(DELIVERY_TYPES),
                "address": f"Calle {random.choice(['Principal', 'Juarez', 'Hidalgo', 'Morelos', 'Zaragoza'])} #{random.randint(100, 999)}, Col. Centro, CP {random.randint(10000, 99999)}" if random.random() < 0.7 else None,
                "status": status,
                "total": 0,
                "created": created,
                "updated": delivered or created + timedelta(hours=random.randint(1, 168)),
            },
        )

        for _ in range(num_items):
            product_id = random.choice(product_ids)
            sizes = ["S", "M", "L", "XL"]
            colors = ["Negro", "Blanco", "Rojo", "Azul"]
            quantity = random.randint(1, 3)
            price = Decimal(str(random.choice([29.99, 49.99, 79.99, 99.99, 129.99, 149.99])))
            line_total = price * quantity
            total += line_total

            await session.execute(
                text("""
                    INSERT INTO order_items (id, empresa_id, order_id, product_id, product_name,
                        size, color, quantity, price, created_at, updated_at)
                    VALUES (:id, :empresa_id, :order_id, :product_id, :product_name,
                        :size, :color, :qty, :price, :created, :updated)
                """),
                {
                    "id": uuid.uuid4(),
                    "empresa_id": empresa_id,
                    "order_id": order_id,
                    "product_id": product_id,
                    "product_name": random.choice(PRODUCTS)[0],
                    "size": random.choice(sizes),
                    "color": random.choice(colors),
                    "qty": quantity,
                    "price": price,
                    "created": created,
                    "updated": created,
                },
            )

        # Update total
        await session.execute(
            text("UPDATE orders SET total = :total WHERE id = :id"),
            {"total": total, "id": order_id},
        )

        if (i + 1) % 50 == 0:
            await session.commit()
            logger.info("  -> %d orders committed", i + 1)

    await session.commit()
    logger.info("  -> %d orders created", count)


async def seed_automation(session: AsyncSession, empresa_id: uuid.UUID, client_ids: list[dict]):
    logger.info("Seeding automation rules and tasks...")

    rule_ids = []
    for rule in AUTOMATION_RULES:
        rule_id = uuid.uuid4()
        rule_ids.append(rule_id)
        await session.execute(
            text("""
                INSERT INTO automation_rules (id, empresa_id, rule_key, name, description, trigger_type, enabled, config, created_at, updated_at)
                VALUES (:id, :empresa_id, :key, :name, :desc, :trigger, :enabled, :config, :created, :updated)
            """),
            {
                "id": rule_id,
                "empresa_id": empresa_id,
                "key": rule["rule_key"],
                "name": rule["name"],
                "desc": rule["description"],
                "trigger": rule["trigger_type"],
                "enabled": True,
                "config": rule["config"],
                "created": random_date(60),
                "updated": random_date(7),
            },
        )

    for i in range(50):
        client = random.choice(client_ids)
        task_type = random.choice(TASK_TYPES)
        priority = random.choice(TASK_PRIORITIES)
        status = random.choice(TASK_STATUSES)
        due = random_past_date(30, min_days=1) if status in ("pending", "in_progress") else random_past_date(60)

        await session.execute(
            text("""
                INSERT INTO automation_tasks (id, empresa_id, rule_id, customer_id, title, task_type, priority,
                    status, ai_reason, ai_score, due_date, created_at, updated_at)
                VALUES (:id, :empresa_id, :rule_id, :customer_id, :title, :task_type, :priority,
                    :status, :reason, :score, :due, :created, :updated)
            """),
            {
                "id": uuid.uuid4(),
                "empresa_id": empresa_id,
                "rule_id": random.choice(rule_ids) if random.random() < 0.7 else None,
                "customer_id": client["id"],
                "title": random.choice([
                    f"Seguimiento con {client['name']}",
                    f"Llamar a {client['name']}",
                    f"Enviar propuesta a {client['name']}",
                    f"Reunion con {client['name']}",
                    f"Revision de pedido - {client['name']}",
                    f"Alerta: cliente inactivo - {client['name']}",
                ]),
                "task_type": task_type,
                "priority": priority,
                "status": status,
                "reason": random.choice([None, "Cliente no ha respondido en 7 dias", "Negocio estancado en negociacion", "Alta probabilidad de cierre"]),
                "score": random.randint(30, 99),
                "due": due,
                "created": due - timedelta(days=random.randint(1, 14)),
                "updated": due,
            },
        )

    await session.commit()
    logger.info("  -> automation rules (%d) and tasks (%d) created", len(AUTOMATION_RULES), 50)


async def seed_whatsapp(session: AsyncSession, empresa_id: uuid.UUID):
    wa_id = uuid.uuid4()
    await session.execute(
        text("""
            INSERT INTO whatsapp_accounts (id, empresa_id, phone_number_id, business_account_id,
                display_phone_number, verified_name, access_token, webhook_verify_token, is_active, created_at, updated_at)
            VALUES (:id, :empresa_id, :phone_id, :bus_id, :display, :verified, :token, :webhook, :active, :created, :updated)
        """),
        {
            "id": wa_id,
            "empresa_id": empresa_id,
            "phone_id": f"test-phone-{empresa_id.hex[:8]}",
            "bus_id": f"test-bus-{empresa_id.hex[:8]}",
            "display": "+521234567890",
            "verified": "Demo SaaS",
            "token": "test-access-token-placeholder",
            "webhook": "demo-vtoken-abc123",
            "active": True,
            "created": random_date(60),
            "updated": random_date(7),
        },
    )
    await session.commit()
    logger.info("  -> demo whatsapp account created")


async def get_existing_clients(session: AsyncSession, empresa_id: uuid.UUID):
    result = await session.execute(
        text("SELECT id, full_name as name, phone FROM clientes WHERE empresa_id = :eid ORDER BY created_at"),
        {"eid": empresa_id},
    )
    return [{"id": row[0], "name": row[1], "phone": row[2]} for row in result.fetchall()]


async def seed_empresa(session: AsyncSession, empresa_id: uuid.UUID, slug: str, name: str):
    existing = await session.execute(
        text("SELECT id FROM empresas WHERE id = :eid"),
        {"eid": empresa_id},
    )
    if existing.fetchone():
        return

    await session.execute(
        text("""
            INSERT INTO empresas (id, nombre, slug, estado, plan, created_at, updated_at)
            VALUES (:id, :name, :slug, :estado, :plan, :created, :updated)
        """),
        {
            "id": empresa_id,
            "name": name,
            "slug": slug,
            "estado": "active",
            "plan": "enterprise",
            "created": datetime.now(timezone.utc) - timedelta(days=120),
            "updated": datetime.now(timezone.utc),
        },
    )
    await session.commit()
    logger.info("Created empresa: %s (%s)", name, slug)


async def main():
    parser = argparse.ArgumentParser(description="Seed demo data for AI Sales Agent SaaS")
    parser.add_argument("--empresa-slug", default="empresa-demo", help="Empresa slug to seed")
    parser.add_argument("--empresa-name", default="Empresa Demo", help="Empresa name to seed")
    parser.add_argument("--empresa-id", help="Existing empresa UUID")

    args = parser.parse_args()

    settings_module = __import__("app.core.config", fromlist=["get_settings"])
    settings = settings_module.get_settings()

    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        empresas = await get_empresas(session)
        logger.info("Found %d existing empresas", len(empresas))

        if args.empresa_id:
            empresa_ids = [uuid.UUID(args.empresa_id)]
        elif empresas:
            empresa_ids = [row[0] for row in empresas]
            logger.info("Using existing empresas: %s", [str(e) for e in empresa_ids])
        else:
            target_id = uuid.uuid4()
            await seed_empresa(session, target_id, args.empresa_slug, args.empresa_name)
            empresa_ids = [target_id]

        for eid in empresa_ids:
            logger.info("\n=== Seeding empresa: %s ===", eid)

            clients = await get_existing_clients(session, eid)
            if clients:
                logger.info("  Clients already exist (%d found), skipping seed", len(clients))
            else:
                await seed_clients(session, eid, 100)
                clients = await get_existing_clients(session, eid)

            existing_products = await session.execute(
                text("SELECT id FROM productos WHERE empresa_id = :eid LIMIT 1"),
                {"eid": eid},
            )
            if existing_products.fetchone():
                logger.info("  Products already exist, skipping")
                await session.execute(text("SELECT id FROM productos WHERE empresa_id = :e1"), {"e1": eid})
                product_ids = [row[0] for row in await session.execute(
                    text("SELECT id FROM productos WHERE empresa_id = :e2"),
                    {"e2": eid},
                )]
                product_ids = product_ids.fetchall()
            else:
                product_ids = await seed_products(session, eid)

            # Get product IDs as list
            result = await session.execute(
                text("SELECT id FROM productos WHERE empresa_id = :eid"),
                {"eid": eid},
            )
            product_ids = [row[0] for row in result.fetchall()]

            existing_inv = await session.execute(
                text("SELECT id FROM inventory_items WHERE empresa_id = :eid LIMIT 1"),
                {"eid": eid},
            )
            if not existing_inv.fetchone():
                await seed_inventory(session, eid, product_ids)

            existing_deals = await session.execute(
                text("SELECT id FROM sales_pipeline_items WHERE empresa_id = :eid LIMIT 1"),
                {"eid": eid},
            )
            if not existing_deals.fetchone():
                await seed_pipeline_deals(session, eid, clients, 50)

            existing_convs = await session.execute(
                text("SELECT id FROM conversations WHERE empresa_id = :eid LIMIT 1"),
                {"eid": eid},
            )
            if not existing_convs.fetchone():
                await seed_conversations_and_messages(session, eid, clients, 200)

            existing_orders = await session.execute(
                text("SELECT id FROM orders WHERE empresa_id = :eid LIMIT 1"),
                {"eid": eid},
            )
            if not existing_orders.fetchone():
                await seed_orders(session, eid, product_ids, clients, 100)

            existing_auto = await session.execute(
                text("SELECT id FROM automation_rules WHERE empresa_id = :eid LIMIT 1"),
                {"eid": eid},
            )
            if not existing_auto.fetchone():
                await seed_automation(session, eid, clients)

            existing_wa = await session.execute(
                text("SELECT id FROM whatsapp_accounts WHERE empresa_id = :eid LIMIT 1"),
                {"eid": eid},
            )
            if not existing_wa.fetchone():
                await seed_whatsapp(session, eid)

            logger.info("=== Seeding complete for empresa: %s ===\n", eid)

        # Count summary
        for eid in empresa_ids:
            counts = await session.execute(
                text("""
                    SELECT
                        (SELECT COUNT(*) FROM clientes WHERE empresa_id = :e1) as clients,
                        (SELECT COUNT(*) FROM productos WHERE empresa_id = :e2) as products,
                        (SELECT COUNT(*) FROM sales_pipeline_items WHERE empresa_id = :e3) as deals,
                        (SELECT COUNT(*) FROM conversations WHERE empresa_id = :e4) as conversations,
                        (SELECT COUNT(*) FROM messages WHERE empresa_id = :e5) as messages,
                        (SELECT COUNT(*) FROM orders WHERE empresa_id = :e6) as orders,
                        (SELECT COUNT(*) FROM order_items WHERE empresa_id = :e7) as order_items,
                        (SELECT COUNT(*) FROM automation_rules WHERE empresa_id = :e8) as rules,
                        (SELECT COUNT(*) FROM automation_tasks WHERE empresa_id = :e9) as tasks,
                        (SELECT COUNT(*) FROM inventory_items WHERE empresa_id = :e10) as inventory_items
                """),
                {"e1": eid, "e2": eid, "e3": eid, "e4": eid, "e5": eid, "e6": eid, "e7": eid, "e8": eid, "e9": eid, "e10": eid},
            )
            row = counts.fetchone()
            if row:
                logger.info("""
                ╔══════════════════════════════════════╗
                ║     DEMO DATA SEED SUMMARY           ║
                ╠══════════════════════════════════════╣
                ║  Clients:       %-4d                 ║
                ║  Products:      %-4d                 ║
                ║  Pipeline Deals:%-4d                 ║
                ║  Conversations: %-4d                 ║
                ║  Messages:      %-4d                 ║
                ║  Orders:        %-4d                 ║
                ║  Order Items:   %-4d                 ║
                ║  Auto Rules:    %-4d                 ║
                ║  Auto Tasks:    %-4d                 ║
                ║  Inventory:     %-4d                 ║
                ╚══════════════════════════════════════╝
                """ , row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])

    await engine.dispose()
    logger.info("Demo seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
