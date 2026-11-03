"""End-to-end API tests for QUANTUMSHIELD X. Every test uses real crypto
(liboqs + cryptography); no values are faked."""
import io

from conftest import auth


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_auth_success_and_failure(client, user_token):
    r = client.post("/api/auth/login", json={"username": "alice", "password": "testpass123"})
    assert r.status_code == 200 and r.json()["username"] == "alice"
    r = client.post("/api/auth/login", json={"username": "alice", "password": "wrongpass"})
    assert r.status_code == 401
    r = client.get("/api/auth/me", headers=auth(user_token))
    assert r.json()["username"] == "alice"


def test_unauthenticated_rejected(client):
    assert client.get("/api/dashboard").status_code == 401


def test_keygen_kem(client, user_token):
    r = client.post("/api/keys/generate", json={"algorithm": "ML-KEM-768"},
                    headers=auth(user_token))
    assert r.status_code == 200
    body = r.json()
    assert body["public_key_bytes"] == 1184  # FIPS 203 ML-KEM-768 pk size
    assert body["private_key_bytes"] == 2400  # FIPS 203 ML-KEM-768 sk size
    assert body["stored_server_side"] is False
    assert "warning" in body


def test_kem_roundtrip(client, user_token):
    keys = client.post("/api/keys/generate", json={"algorithm": "ML-KEM-768"},
                       headers=auth(user_token)).json()
    enc = client.post("/api/kem/encaps",
                      json={"algorithm": "ML-KEM-768", "public_key": keys["public_key"]},
                      headers=auth(user_token)).json()
    assert enc["ciphertext_bytes"] == 1088  # FIPS 203 ML-KEM-768 ct size
    assert "secret_sha256" in enc and "shared_secret" not in str(enc)
    ok = client.post("/api/kem/decaps-verify",
                     json={"algorithm": "ML-KEM-768", "private_key": keys["private_key"],
                           "ciphertext": enc["ciphertext"],
                           "expected_secret_sha256": enc["secret_sha256"]},
                     headers=auth(user_token)).json()
    assert ok["match"] is True
    bad = client.post("/api/kem/decaps-verify",
                      json={"algorithm": "ML-KEM-768", "private_key": keys["private_key"],
                            "ciphertext": enc["ciphertext"],
                            "expected_secret_sha256": "0" * 64},
                      headers=auth(user_token)).json()
    assert bad["match"] is False


def test_sign_verify_and_tamper(client, user_token):
    keys = client.post("/api/keys/generate", json={"algorithm": "ML-DSA-65"},
                       headers=auth(user_token)).json()
    sig = client.post("/api/sign",
                      json={"algorithm": "ML-DSA-65", "private_key": keys["private_key"],
                            "message": "hello quantum"},
                      headers=auth(user_token)).json()
    assert sig["signature_bytes"] == 3309  # FIPS 204 ML-DSA-65 signature size
    good = client.post("/api/verify",
                       json={"algorithm": "ML-DSA-65", "public_key": keys["public_key"],
                             "message": "hello quantum", "signature": sig["signature"]},
                       headers=auth(user_token)).json()
    assert good["valid"] is True
    tampered = client.post("/api/verify",
                           json={"algorithm": "ML-DSA-65", "public_key": keys["public_key"],
                                 "message": "hello quantun", "signature": sig["signature"]},
                           headers=auth(user_token)).json()
    assert tampered["valid"] is False


def test_slh_dsa_sign_verify(client, user_token):
    keys = client.post("/api/keys/generate", json={"algorithm": "SLH_DSA_PURE_SHA2_128S"},
                       headers=auth(user_token)).json()
    assert keys["public_key_bytes"] == 32
    assert keys["private_key_bytes"] == 64
    sig = client.post("/api/sign",
                      json={"algorithm": "SLH_DSA_PURE_SHA2_128S",
                            "private_key": keys["private_key"], "message": "slh test"},
                      headers=auth(user_token)).json()
    assert sig["signature_bytes"] == 7856
    good = client.post("/api/verify",
                       json={"algorithm": "SLH_DSA_PURE_SHA2_128S",
                             "public_key": keys["public_key"],
                             "message": "slh test", "signature": sig["signature"]},
                       headers=auth(user_token)).json()
    assert good["valid"] is True


def test_aes_roundtrip_and_tamper(client, user_token):
    enc = client.post("/api/symmetric/encrypt", json={"plaintext": "secret message"},
                      headers=auth(user_token)).json()
    dec = client.post("/api/symmetric/decrypt",
                      json={"key": enc["key"], "nonce": enc["nonce"],
                            "ciphertext": enc["ciphertext"]},
                      headers=auth(user_token)).json()
    assert dec["plaintext"] == "secret message"
    # Flip one byte of the ciphertext: GCM authentication must fail.
    import base64
    ct = bytearray(base64.b64decode(enc["ciphertext"]))
    ct[0] ^= 1
    r = client.post("/api/symmetric/decrypt",
                    json={"key": enc["key"], "nonce": enc["nonce"],
                          "ciphertext": base64.b64encode(bytes(ct)).decode()},
                    headers=auth(user_token))
    assert r.status_code == 400


def test_hybrid_roundtrip(client, user_token):
    keys = client.post("/api/hybrid/keygen", headers=auth(user_token)).json()
    enc = client.post("/api/hybrid/encrypt",
                      json={"x25519_public_key": keys["x25519_public_key"],
                            "kem_public_key": keys["kem_public_key"],
                            "plaintext": "hybrid secret"},
                      headers=auth(user_token)).json()
    dec = client.post("/api/hybrid/decrypt",
                      json={"x25519_private_key": keys["x25519_private_key"],
                            "kem_private_key": keys["kem_private_key"],
                            "x25519_public_key": enc["x25519_public_key"],
                            "kem_ciphertext": enc["kem_ciphertext"],
                            "nonce": enc["nonce"], "ciphertext": enc["ciphertext"]},
                      headers=auth(user_token)).json()
    assert dec["plaintext"] == "hybrid secret"


def test_file_upload_hash_decrypt(client, user_token):
    keys = client.post("/api/keys/generate", json={"algorithm": "ML-KEM-768"},
                       headers=auth(user_token)).json()
    import hashlib
    content = b"quantumshield file test"
    r = client.post("/api/files/upload",
                    files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
                    data={"kem_public_key": keys["public_key"]},
                    headers=auth(user_token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["sha256"] == hashlib.sha256(content).hexdigest()
    assert body["sha3_256"] == hashlib.sha3_256(content).hexdigest()
    ok = client.post(f"/api/files/{body['id']}/verify-integrity",
                     json={"kem_private_key": keys["private_key"]},
                     headers=auth(user_token)).json()
    assert ok["match"] is True


def test_messaging_flow(client, user_token, bob_token):
    # Bob publishes keys; alice sends; bob decrypts + verifies.
    bob_kem = client.post("/api/keys/generate", json={"algorithm": "ML-KEM-768"},
                          headers=auth(bob_token)).json()
    alice_dsa = client.post("/api/keys/generate", json={"algorithm": "ML-DSA-65"},
                            headers=auth(user_token)).json()
    client.post("/api/auth/publish-keys",
                json={"kem_public_key": bob_kem["public_key"]}, headers=auth(bob_token))
    client.post("/api/auth/publish-keys",
                json={"dsa_public_key": alice_dsa["public_key"]}, headers=auth(user_token))
    sent = client.post("/api/messages/send",
                       json={"recipient_username": "bob", "plaintext": "hi bob, quantum-safe",
                             "signing_private_key": alice_dsa["private_key"]},
                       headers=auth(user_token))
    assert sent.status_code == 200, sent.text
    mid = sent.json()["id"]
    inbox = client.get("/api/messages/inbox", headers=auth(bob_token)).json()
    assert any(m["id"] == mid for m in inbox)
    assert all("hi bob" not in str(m) for m in inbox)  # ciphertext only
    dec = client.post(f"/api/messages/{mid}/decrypt",
                      json={"kem_private_key": bob_kem["private_key"]},
                      headers=auth(bob_token)).json()
    assert dec["plaintext"] == "hi bob, quantum-safe"
    ver = client.post("/api/messages/verify-text",
                      json={"message_id": mid, "plaintext": "hi bob, quantum-safe"},
                      headers=auth(bob_token)).json()
    assert ver["valid"] is True
    ver_bad = client.post("/api/messages/verify-text",
                          json={"message_id": mid, "plaintext": "forged"},
                          headers=auth(bob_token)).json()
    assert ver_bad["valid"] is False


def test_dashboard_counts_change(client, user_token):
    before = client.get("/api/dashboard", headers=auth(user_token)).json()
    client.post("/api/keys/generate", json={"algorithm": "ML-KEM-512"},
                headers=auth(user_token))
    after = client.get("/api/dashboard", headers=auth(user_token)).json()
    assert after["total_operations"] == before["total_operations"] + 1
    assert any(u["algorithm"] == "ML-KEM-512" for u in after["algorithm_usage"])


def test_audit_chain_verifies(client, user_token):
    r = client.get("/api/audit/verify-chain", headers=auth(user_token)).json()
    assert r["valid"] is True and r["total"] >= 1


def test_admin_rbac(client, user_token, admin_token):
    assert client.get("/api/admin/users", headers=auth(user_token)).status_code == 403
    r = client.get("/api/admin/users", headers=auth(admin_token))
    assert r.status_code == 200
    assert any(u["username"] == "alice" for u in r.json())
    # Password hashes must never appear in admin responses.
    assert "password" not in r.text.lower()


def test_invalid_input(client, user_token):
    r = client.post("/api/keys/generate", json={"algorithm": "NOPE-123"},
                    headers=auth(user_token))
    assert r.status_code == 400
    r = client.post("/api/symmetric/encrypt", json={"plaintext": "x", "key": "!!!not-b64!!!"},
                    headers=auth(user_token))
    assert r.status_code == 400
    r = client.post("/api/kem/encaps",
                    json={"algorithm": "ML-KEM-768", "public_key": "!!!"},
                    headers=auth(user_token))
    assert r.status_code == 400


def test_simulator_labelled_educational(client, user_token):
    body = client.get("/api/simulator", headers=auth(user_token)).json()
    assert "Educational model" in body["label"]
    assert any(c["algorithm"] == "RSA-2048" for c in body["comparison"])


def test_migration_and_hndl(client, user_token):
    m = client.post("/api/migration",
                    json={"systems": [{"name": "core", "algorithm": "RSA-2048",
                                       "data_secrecy_years": 25}]},
                    headers=auth(user_token)).json()
    assert m["score"] < 100 and len(m["recommendations"]) >= 1
    h = client.post("/api/hndl",
                    json={"algorithm": "RSA-2048", "secrecy_years": 20,
                          "migration_years": 5, "threat_years_estimate": 10},
                    headers=auth(user_token)).json()
    assert h["at_risk"] is True and h["exposure_level"] == "high"
    assert "Educational model" in h["label"]
