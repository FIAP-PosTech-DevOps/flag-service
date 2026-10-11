"""Caminhos de sucesso e de erro das rotas de flags (com o banco simulado)."""
import psycopg2
import requests

from conftest import AUTH

FLAG = {"name": "novo-checkout", "description": "checkout novo", "is_enabled": True}


def test_auth_service_com_erro_de_conexao_retorna_503(svc):
    svc.auth_get.side_effect = requests.exceptions.ConnectionError()
    resp = svc.client.get("/flags", headers=AUTH)
    assert resp.status_code == 503


def test_criar_flag_duplicada_retorna_409(svc):
    svc.cursor.execute.side_effect = psycopg2.IntegrityError()
    resp = svc.client.post("/flags", json=FLAG, headers=AUTH)
    assert resp.status_code == 409
    svc.conn.rollback.assert_called_once()
    svc.pool.putconn.assert_called_once_with(svc.conn)


def test_criar_flag_com_erro_no_banco_retorna_500(svc):
    svc.cursor.execute.side_effect = RuntimeError("banco fora")
    resp = svc.client.post("/flags", json=FLAG, headers=AUTH)
    assert resp.status_code == 500
    svc.conn.rollback.assert_called_once()


def test_erro_ao_pegar_conexao_do_pool_retorna_500(svc):
    # Sem conexão nem cursor: o finally não tenta fechar nem devolver nada.
    svc.pool.getconn.side_effect = RuntimeError("pool esgotado")
    resp = svc.client.post("/flags", json=FLAG, headers=AUTH)
    assert resp.status_code == 500
    svc.pool.putconn.assert_not_called()


def test_listar_flags(svc):
    svc.cursor.fetchall.return_value = [FLAG]
    resp = svc.client.get("/flags", headers=AUTH)
    assert resp.status_code == 200
    assert resp.get_json() == [FLAG]
    svc.cursor.close.assert_called_once()


def test_listar_flags_com_erro_no_banco_retorna_500(svc):
    svc.cursor.execute.side_effect = RuntimeError("banco fora")
    resp = svc.client.get("/flags", headers=AUTH)
    assert resp.status_code == 500


def test_listar_flags_sem_conexao_retorna_500(svc):
    svc.pool.getconn.side_effect = RuntimeError("pool esgotado")
    resp = svc.client.get("/flags", headers=AUTH)
    assert resp.status_code == 500


def test_buscar_flag(svc):
    svc.cursor.fetchone.return_value = FLAG
    resp = svc.client.get("/flags/novo-checkout", headers=AUTH)
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "novo-checkout"


def test_buscar_flag_com_erro_no_banco_retorna_500(svc):
    svc.cursor.execute.side_effect = RuntimeError("banco fora")
    resp = svc.client.get("/flags/novo-checkout", headers=AUTH)
    assert resp.status_code == 500


def test_buscar_flag_sem_conexao_retorna_500(svc):
    svc.pool.getconn.side_effect = RuntimeError("pool esgotado")
    resp = svc.client.get("/flags/novo-checkout", headers=AUTH)
    assert resp.status_code == 500


def test_atualizar_flag_sem_corpo_retorna_400(svc):
    resp = svc.client.put("/flags/novo-checkout", json={}, headers=AUTH)
    assert resp.status_code == 400


def test_atualizar_flag(svc):
    svc.cursor.rowcount = 1
    svc.cursor.fetchone.return_value = {**FLAG, "is_enabled": False}
    resp = svc.client.put(
        "/flags/novo-checkout", json={"description": "nova", "is_enabled": False}, headers=AUTH
    )
    assert resp.status_code == 200
    query, values = svc.cursor.execute.call_args.args
    assert "description = %s" in query
    assert "is_enabled = %s" in query
    assert values == ("nova", False, "novo-checkout")
    svc.conn.commit.assert_called_once()


def test_atualizar_flag_inexistente_retorna_404(svc):
    svc.cursor.rowcount = 0
    resp = svc.client.put("/flags/nao-existe", json={"is_enabled": True}, headers=AUTH)
    assert resp.status_code == 404


def test_atualizar_flag_com_erro_no_banco_retorna_500(svc):
    svc.cursor.execute.side_effect = RuntimeError("banco fora")
    resp = svc.client.put("/flags/novo-checkout", json={"is_enabled": True}, headers=AUTH)
    assert resp.status_code == 500
    svc.conn.rollback.assert_called_once()


def test_atualizar_flag_sem_conexao_retorna_500(svc):
    svc.pool.getconn.side_effect = RuntimeError("pool esgotado")
    resp = svc.client.put("/flags/novo-checkout", json={"is_enabled": True}, headers=AUTH)
    assert resp.status_code == 500


def test_remover_flag(svc):
    svc.cursor.rowcount = 1
    resp = svc.client.delete("/flags/novo-checkout", headers=AUTH)
    assert resp.status_code == 204
    svc.conn.commit.assert_called_once()


def test_remover_flag_com_erro_no_banco_retorna_500(svc):
    svc.cursor.execute.side_effect = RuntimeError("banco fora")
    resp = svc.client.delete("/flags/novo-checkout", headers=AUTH)
    assert resp.status_code == 500
    svc.conn.rollback.assert_called_once()


def test_remover_flag_sem_conexao_retorna_500(svc):
    svc.pool.getconn.side_effect = RuntimeError("pool esgotado")
    resp = svc.client.delete("/flags/novo-checkout", headers=AUTH)
    assert resp.status_code == 500
