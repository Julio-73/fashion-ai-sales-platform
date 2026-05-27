"""End-to-end test for AI Live endpoints."""
import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.modules.auth.models import EmpresaUsuario, Usuario
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.companies.models import Empresa
from app.modules.conversations.models import Conversation
from app.modules.customers.models import Cliente
from app.ai_live.repository import ConversationAIRepository


async def setup():
    async with AsyncSessionLocal() as session:
        repo = AuthRepository(session)
        svc = AuthService(repo)

        user = await repo.get_user_by_email(email="live-test@example.com")
        if user:
            print(f"User exists: id={user.id} empresa={user.empresa_id}")
            result = await session.execute(
                select(Conversation).where(
                    Conversation.empresa_id == user.empresa_id
                ).limit(1)
            )
            conv = result.scalar_one_or_none()
            conv_id = conv.id if conv else None
            token = await svc.create_token_pair(
                user.id, user.empresa_id, ["owner"]
            )
            return token.access_token, user.empresa_id, conv_id

        eid = uuid4()
        session.add(Empresa(id=eid, nombre="Live Test", slug="live-test"))

        uid = uuid4()
        pw_hash = svc._hash_password("Test123456!")
        now = datetime.now(timezone.utc)
        session.add(
            Usuario(
                id=uid,
                empresa_id=eid,
                email="live-test@example.com",
                nombre="Live",
                password_hash=pw_hash,
                rol="owner",
                created_at=now,
                updated_at=now,
            )
        )
        session.add(EmpresaUsuario(empresa_id=eid, usuario_id=uid, rol="owner"))

        cid = uuid4()
        session.add(
            Cliente(
                id=cid,
                empresa_id=eid,
                full_name="Test Client",
                email="client@test.com",
                phone="+51999000001",
                lead_status="new",
                source="web",
                created_at=now,
                updated_at=now,
            )
        )

        conv_id = uuid4()
        session.add(
            Conversation(
                id=conv_id,
                empresa_id=eid,
                cliente_id=cid,
                asunto="Test Conversation",
                canal="manual",
                estado="open",
                created_at=now,
                updated_at=now,
            )
        )

        await session.commit()

        token = await svc.create_token_pair(uid, eid, ["owner"])
        print(f"Created: token={token.access_token[:20]}... empresa={eid} conv={conv_id}")
        return token.access_token, eid, conv_id


async def test_endpoint(token, empresa_id, conv_id):
    import httpx

    base = "http://localhost:8000/api/v1"
    headers = {"Authorization": f"Bearer {token}"}

    # Test GET state
    print("\n=== GET state ===")
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{base}/ai-live/conversations/{conv_id}/state", headers=headers)
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:300]}")
        if r.status_code != 200:
            print("FAILED!")

    # Test POST suggest-reply
    print("\n=== POST suggest-reply ===")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{base}/ai-live/conversations/{conv_id}/suggest-reply",
            headers=headers,
            json={},
        )
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:300]}")
        if r.status_code != 200:
            print("FAILED!")

    # Test GET insights
    print("\n=== GET insights ===")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{base}/ai-live/conversations/{conv_id}/insights", headers=headers
        )
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:300]}")
        if r.status_code != 200:
            print("FAILED!")

    # Test PATCH toggle-ai
    print("\n=== PATCH toggle-ai ===")
    async with httpx.AsyncClient() as client:
        r = await client.patch(
            f"{base}/ai-live/conversations/{conv_id}/toggle-ai",
            headers=headers,
            json={"ai_enabled": False},
        )
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:300]}")
        if r.status_code != 200:
            print("FAILED!")

    # Test PATCH toggle-auto-reply
    print("\n=== PATCH toggle-auto-reply ===")
    async with httpx.AsyncClient() as client:
        r = await client.patch(
            f"{base}/ai-live/conversations/{conv_id}/toggle-auto-reply",
            headers=headers,
            json={"auto_reply_enabled": True},
        )
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:300]}")
        if r.status_code != 200:
            print("FAILED!")

    # Test POST handoff
    print("\n=== POST handoff ===")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{base}/ai-live/conversations/{conv_id}/handoff",
            headers=headers,
            json={"reason": "Test handoff"},
        )
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:300]}")
        if r.status_code != 200:
            print("FAILED!")

    # Test POST analyze-intent
    print("\n=== POST analyze-intent ===")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{base}/ai-live/conversations/{conv_id}/analyze-intent",
            headers=headers,
            json={"message": "Hola, quiero comprar un producto"},
        )
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:300]}")
        if r.status_code != 200:
            print("FAILED!")

    # Test GET events
    print("\n=== GET events ===")
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{base}/ai-live/conversations/{conv_id}/events", headers=headers
        )
        print(f"Status: {r.status_code}")
        print(f"Body: {r.text[:300]}")
        if r.status_code != 200:
            print("FAILED!")

    print("\n=== ALL TESTS COMPLETE ===")


if __name__ == "__main__":
    token, empresa_id, conv_id = asyncio.run(setup())
    asyncio.run(test_endpoint(token, empresa_id, conv_id))
