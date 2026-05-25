import sys
fpath = r"C:\Users\User\Documents\ai-sales-agent-saas\backend\tests\unit\test_auth_service.py"
with open(fpath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the test method completely
old_method = '''
    async def test_valid_login_returns_session(self, auth_service, auth_repository):
        mock_user = MagicMock(spec=Usuario)
        mock_user.id = uuid4(); mock_user.email = "user@example.com"
        mock_user.password_hash = "somehash"; mock_user.estado = "active"
        mock_membership = MagicMock(spec=EmpresaUsuario)
        mock_membership.empresa_id = uuid4(); mock_membership.rol = "sales_agent"

        auth_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_repository.get_membership = AsyncMock(return_value=mock_membership)
        auth_repository.create_refresh_token = AsyncMock()
        auth_repository.commit = AsyncMock()

        import app.core.security.password as pwd_mod
        original = pwd_mod.verify_password
        pwd_mod.verify_password = lambda pw, h: True
        try:
            result = await auth_service.login(LoginRequest(email="user@example.com", password="AnyPass123!", empresa_id=uuid4()))
            assert result.access_token is not None
        finally:
            pwd_mod.verify_password = original
'''

new_method = '''
    async def test_valid_login_returns_session(self, auth_service, auth_repository):
        from unittest.mock import patch
        mock_user = MagicMock(spec=Usuario)
        mock_user.id = uuid4(); mock_user.email = "user@example.com"
        mock_user.password_hash = ""
        mock_user.estado = "active"
        mock_membership = MagicMock(spec=EmpresaUsuario)
        mock_membership.empresa_id = uuid4(); mock_membership.rol = "sales_agent"

        auth_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_repository.get_membership = AsyncMock(return_value=mock_membership)
        auth_repository.create_refresh_token = AsyncMock()
        auth_repository.commit = AsyncMock()

        with patch("app.core.security.password.verify_password", return_value=True):
            result = await auth_service.login(LoginRequest(email="user@example.com", password="AnyPass123!", empresa_id=uuid4()))
            assert result.access_token is not None
'''

content = content.replace(old_method, new_method)

with open(fpath, "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed successfully")
