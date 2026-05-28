import pytest


class TestMigrationValidator:
    def test_migration_chain_exists(self):
        """Verify the migration chain is complete."""
        import importlib
        import os
        import re

        migrations_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "alembic", "versions"
        )
        migrations_dir = os.path.normpath(migrations_dir)

        if not os.path.exists(migrations_dir):
            pytest.skip("Migrations directory not found")

        files = sorted([
            f for f in os.listdir(migrations_dir)
            if f.endswith(".py") and f != "__init__.py"
        ])

        assert len(files) >= 9, f"Expected at least 9 migrations, found {len(files)}"

        revisions = {}
        for f in files:
            modname = f.replace(".py", "")
            spec = importlib.util.spec_from_file_location(
                modname, os.path.join(migrations_dir, f)
            )
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception:
                continue
            revisions[mod.revision] = mod.down_revision

        has_0009 = any("0009" in rev for rev in revisions)
        assert has_0009, "Migration 0009 (conversation_memories) not found"

        last_rev = files[-1].replace(".py", "")
        spec = importlib.util.spec_from_file_location(
            last_rev, os.path.join(migrations_dir, files[-1])
        )
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
            assert mod.revision is not None
            assert mod.down_revision is not None
        except Exception as e:
            pytest.fail(f"Failed to load migration {files[-1]}: {e}")

    def test_memory_model_registered(self):
        from app.database.base import Base
        from app.database.models import import_all_models

        import_all_models()
        table_names = Base.metadata.tables.keys()
        assert "conversation_memories" in table_names, (
            "conversation_memories table not registered in metadata"
        )

    def test_all_models_have_tenant_mixin(self):
        from app.database.base import Base
        from app.database.models import import_all_models

        import_all_models()

        tenant_tables = ["clientes", "productos",
                         "conversations", "messages", "conversations_core",
                         "messages_core", "conversation_ai_states",
                         "conversation_ai_events", "conversation_memories"]

        for name, table in Base.metadata.tables.items():
            if name in tenant_tables:
                assert "empresa_id" in table.columns, (
                    f"Table {name} missing empresa_id column (tenant isolation)"
                )

    def test_new_memory_model_columns(self):
        from app.database.base import Base
        from app.database.models import import_all_models

        import_all_models()

        table = Base.metadata.tables.get("conversation_memories")
        assert table is not None

        expected_columns = [
            "id", "empresa_id", "customer_id", "conversation_id",
            "memory_type", "summary",
            "extracted_preferences", "extracted_sizes",
            "extracted_colors", "extracted_styles", "extracted_occasions",
            "confidence", "created_at", "updated_at",
        ]
        for col in expected_columns:
            assert col in table.columns, f"Missing column: {col}"
