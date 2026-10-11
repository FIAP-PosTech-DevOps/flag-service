"""Fixtures dos testes unitários.

O app.py conecta no PostgreSQL e lê variáveis de ambiente no momento do
import. Aqui as variáveis recebem valores de teste e o pool de conexões é
trocado por um mock ANTES do import, então os testes rodam sem banco e sem
o auth-service.
"""
import importlib
import os
import sys
from unittest import mock

import pytest

os.environ.setdefault("DATABASE_URL", "postgres://test:test@localhost:5432/test")
os.environ.setdefault("AUTH_SERVICE_URL", "http://auth-service.test")


@pytest.fixture
def svc():
    """Importa o app com o pool de conexões e o auth-service simulados."""
    with mock.patch("psycopg2.pool.SimpleConnectionPool") as pool_cls:
        sys.modules.pop("app", None)
        module = importlib.import_module("app")

        pool = pool_cls.return_value
        conn = pool.getconn.return_value
        cursor = conn.cursor.return_value

        with mock.patch.object(module.requests, "get") as auth_get:
            auth_get.return_value.status_code = 200
            module.app.config["TESTING"] = True
            yield mock.Mock(
                module=module,
                client=module.app.test_client(),
                pool=pool,
                conn=conn,
                cursor=cursor,
                auth_get=auth_get,
            )


AUTH = {"Authorization": "Bearer tm_key_teste"}
