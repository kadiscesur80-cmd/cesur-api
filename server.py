"""
Cesur License API - FastAPI sunucusu
Render.com ucretsiz planinda calisir.
"""
import os, json, time, hashlib, hmac, secrets
from datetime import datetime, timedelta
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Cesur License API")

ADMIN_TOKEN = os.environ.get("CESUR_ADMIN_TOKEN", "cesur-admin-secret-2026")
DB_FILE = Path(__file__).parent / "database.json"

# ─── Database ──────────────────────────────────────────────
def load_db():
    if DB_FILE.exists():
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    return {"keys": {}, "messages": [], "revoked": [], "banned_hwids": []}

def save_db(db):
    DB_FILE.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")

# ─── Key helpers ───────────────────────────────────────────
def generate_key(days: int) -> str:
    """Ornek: CESUR-A1B2-C3D4-7"""
    seg = lambda: secrets.token_hex(2).upper()
    exp_part = secrets.token_hex(1).upper()
    raw = f"{seg()}-{seg()}-{seg()}-{exp_part}"
    return f"CESUR-{raw}"

def verify_admin(token: str):
    if not hmac.compare_digest(token, ADMIN_TOKEN):
        raise HTTPException(status_code=401, detail="Yonetici yetkisi gerekli")

# ─── Models ────────────────────────────────────────────────
class KeyCreate(BaseModel):
    key: Optional[str] = None
    days: int = 7
    hwid_locked: bool = True

class LicenseCheck(BaseModel):
    key: str
    hwid: str

class MessageSet(BaseModel):
    text: str

class KeyAction(BaseModel):
    key: str

# ─── PUBLIC: License dogrulama ────────────────────────────
@app.post("/api/validate")
def validate_license(data: LicenseCheck):
    db = load_db()
    key = data.key.upper().strip()

    # Ban kontrolu
    if data.hwid in db.get("banned_hwids", []):
        return {"valid": False, "reason": "Bu makine engellenmis."}

    # Key var mi?
    if key not in db["keys"]:
        return {"valid": False, "reason": "Gecersiz lisans key."}

    k = db["keys"][key]

    # Iptal edilmis mi?
    if key in db.get("revoked", []):
        return {"valid": False, "reason": "Lisans iptal edilmis."}

    # Suresi dolmus mu?
    exp = datetime.fromisoformat(k["expires"])
    if datetime.now() > exp:
        return {"valid": False, "reason": f"Lisans suresi dolmus ({exp.strftime('%d.%m.%Y')})."}

    # HWID kontrolu
    if k.get("hwid_locked", True):
        if k.get("hwid") and k["hwid"] != data.hwid:
            return {"valid": False, "reason": "Bu lisans baska bir makineye kilitli."}
        if not k.get("hwid"):
            k["hwid"] = data.hwid
            save_db(db)

    # Kalan sure
    remaining = (exp - datetime.now()).total_seconds()
    remaining_days = int(remaining / 86400)

    # Mesaj var mi?
    msg = ""
    if db.get("messages"):
        msg = db["messages"][-1]["text"]

    return {
        "valid": True,
        "expires": exp.isoformat(),
        "remaining_days": remaining_days,
        "message": msg,
    }

# ─── ADMIN: Key yonetimi ──────────────────────────────────
@app.post("/api/admin/create_key")
def admin_create_key(data: KeyCreate, x_admin_token: str = Header(...)):
    verify_admin(x_admin_token)
    db = load_db()

    key = data.key.upper().strip() if data.key else generate_key(data.days)
    expires = (datetime.now() + timedelta(days=data.days)).isoformat()

    db["keys"][key] = {
        "created": datetime.now().isoformat(),
        "expires": expires,
        "hwid_locked": data.hwid_locked,
        "hwid": None,
    }
    save_db(db)
    return {"key": key, "expires": expires, "days": data.days}

@app.post("/api/admin/revoke")
def admin_revoke_key(data: KeyAction, x_admin_token: str = Header(...)):
    verify_admin(x_admin_token)
    db = load_db()
    key = data.key.upper().strip()
    if key not in db["keys"]:
        raise HTTPException(404, "Key bulunamadi.")
    if key not in db.get("revoked", []):
        db.setdefault("revoked", []).append(key)
    save_db(db)
    return {"ok": True, "key": key, "status": "iptal"}

@app.post("/api/admin/unrevoke")
def admin_unrevoke_key(data: KeyAction, x_admin_token: str = Header(...)):
    verify_admin(x_admin_token)
    db = load_db()
    key = data.key.upper().strip()
    db["revoked"] = [k for k in db.get("revoked", []) if k != key]
    save_db(db)
    return {"ok": True, "key": key, "status": "aktif"}

@app.get("/api/admin/list_keys")
def admin_list_keys(x_admin_token: str = Header(...)):
    verify_admin(x_admin_token)
    db = load_db()
    result = []
    for key, info in db["keys"].items():
        exp = datetime.fromisoformat(info["expires"])
        result.append({
            "key": key,
            "expires": exp.strftime("%d.%m.%Y %H:%M"),
            "hwid": info.get("hwid", "Yok"),
            "hwid_locked": info.get("hwid_locked", True),
            "revoked": key in db.get("revoked", []),
            "expired": datetime.now() > exp,
        })
    return {"keys": result, "total": len(result)}

@app.post("/api/admin/message")
def admin_set_message(data: MessageSet, x_admin_token: str = Header(...)):
    verify_admin(x_admin_token)
    db = load_db()
    db.setdefault("messages", []).append({
        "text": data.text,
        "time": datetime.now().isoformat(),
    })
    save_db(db)
    return {"ok": True, "message": data.text}

@app.post("/api/admin/ban_hwid")
def admin_ban_hwid(data: KeyAction, x_admin_token: str = Header(...)):
    verify_admin(x_admin_token)
    db = load_db()
    if data.key not in db.get("banned_hwids", []):
        db.setdefault("banned_hwids", []).append(data.key)
    save_db(db)
    return {"ok": True, "banned": data.key}

@app.post("/api/admin/delete_key")
def admin_delete_key(data: KeyAction, x_admin_token: str = Header(...)):
    verify_admin(x_admin_token)
    db = load_db()
    key = data.key.upper().strip()
    if key in db["keys"]:
        del db["keys"][key]
    db["revoked"] = [k for k in db.get("revoked", []) if k != key]
    save_db(db)
    return {"ok": True}

@app.get("/api/admin/messages")
def admin_list_messages(x_admin_token: str = Header(...)):
    verify_admin(x_admin_token)
    db = load_db()
    return {"messages": db.get("messages", [])[-20:]}

@app.post("/api/admin/clear_messages")
def admin_clear_messages(x_admin_token: str = Header(...)):
    verify_admin(x_admin_token)
    db = load_db()
    db["messages"] = []
    save_db(db)
    return {"ok": True}

@app.get("/")
def root():
    return {"status": "ok", "api": "Cesur License API", "version": "1.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
