"""O serviço não sobe sem configuração nem sem banco (falha rápida no import)."""
import importlib
import sys
from unittest import mock

import psycopg2
import pytest


def importar_app():
    sys.modules.pop("app", None)
    return importlib.import_module("app")


@pytest.mark.parametrize("variavel", ["DATABASE_URL", "AUTH_SERVICE_URL"])
def test_sem_variavel_obrigatoria_encerra(monkeypatch, variavel):
    monkeypatch.delenv(variavel)
    with mock.patch("psycopg2.pool.SimpleConnectionPool"), pytest.raises(SystemExit) as saida:
        importar_app()
    assert saida.value.code == 1


def test_banco_inacessivel_encerra():
    with mock.patch(
        "psycopg2.pool.SimpleConnectionPool", side_effect=psycopg2.OperationalError("recusado")
    ), pytest.raises(SystemExit) as saida:
        importar_app()
    assert saida.value.code == 1
