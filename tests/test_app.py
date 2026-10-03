"""Testes unitários do flag-service (sem banco e sem auth-service reais)."""
import requests

from conftest import AUTH


def test_health(svc):
    resp = svc.client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_sem_header_de_autorizacao_retorna_401(svc):
    resp = svc.client.get("/flags")
    assert resp.status_code == 401
    svc.auth_get.assert_not_called()


def test_chave_invalida_retorna_401(svc):
    svc.auth_get.return_value.status_code = 401
    resp = svc.client.get("/flags", headers=AUTH)
    assert resp.status_code == 401


def test_auth_service_fora_do_ar_retorna_504(svc):
    svc.auth_get.side_effect = requests.exceptions.Timeout()
    resp = svc.client.get("/flags", headers=AUTH)
    assert resp.status_code == 504


def test_criar_flag_exige_nome(svc):
    resp = svc.client.post("/flags", json={}, headers=AUTH)
    assert resp.status_code == 400


def test_criar_flag(svc):
    svc.cursor.fetchone.return_value = {"name": "novo-checkout", "is_enabled": True}
    resp = svc.client.post("/flags", json={"name": "novo-checkout", "is_enabled": True}, headers=AUTH)
    assert resp.status_code == 201
    assert resp.get_json()["name"] == "novo-checkout"
    svc.conn.commit.assert_called_once()
    svc.pool.putconn.assert_called_once_with(svc.conn)


def test_buscar_flag_inexistente_retorna_404(svc):
    svc.cursor.fetchone.return_value = None
    resp = svc.client.get("/flags/nao-existe", headers=AUTH)
    assert resp.status_code == 404


def test_atualizar_flag_sem_campos_retorna_400(svc):
    resp = svc.client.put("/flags/novo-checkout", json={"outro": 1}, headers=AUTH)
    assert resp.status_code == 400


def test_remover_flag_inexistente_retorna_404(svc):
    svc.cursor.rowcount = 0
    resp = svc.client.delete("/flags/nao-existe", headers=AUTH)
    assert resp.status_code == 404
