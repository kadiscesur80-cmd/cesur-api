"""
Cesur Admin Paneli - Key yonetimi, mesaj gonderme, ban.
Kullanim:
    python admin.py create 7          -> 7 gunluk key olustur
    python admin.py list              -> tum keyleri listele
    python admin.py revoke CESUR-XXX  -> keyi iptal et
    python admin.py unrevoke CESUR-XXX -> keyi geri ac
    python admin.py msg "mesaj"       -> acilista mesaj goster
    python admin.py ban HWID          -> makineyi engelle
    python admin.py delete CESUR-XXX  -> keyi sil
"""
import requests, sys, json

API_URL = "https://cesur-api.onrender.com"
ADMIN_TOKEN = "cesur-admin-secret-2026"

def headers():
    return {"x-admin-token": ADMIN_TOKEN}

def cmd_create(days=7):
    r = requests.post(f"{API_URL}/api/admin/create_key",
                       json={"days": days}, headers=headers(), timeout=10)
    d = r.json()
    print(f"\n  Key olusturuldu:")
    print(f"  Key     : {d['key']}")
    print(f"  Suresi  : {d['days']} gun")
    print(f"  Bitis   : {d['expires']}\n")

def cmd_list():
    r = requests.get(f"{API_URL}/api/admin/list_keys", headers=headers(), timeout=10)
    d = r.json()
    print(f"\n  Toplam {d['total']} key:\n")
    for k in d["keys"]:
        durum = ""
        if k["revoked"]: durum = " [IPTAL]"
        elif k["expired"]: durum = " [SURE DOLMUS]"
        hwid_short = k["hwid"][:12] + "..." if k["hwid"] and k["hwid"] != "Yok" else "Yok"
        print(f"  {k['key']}  |  {k['expires']}  |  HWID: {hwid_short}{durum}")
    print()

def cmd_revoke(key):
    r = requests.post(f"{API_URL}/api/admin/revoke",
                       json={"key": key}, headers=headers(), timeout=10)
    print(f"\n  {r.json()}\n")

def cmd_unrevoke(key):
    r = requests.post(f"{API_URL}/api/admin/unrevoke",
                       json={"key": key}, headers=headers(), timeout=10)
    print(f"\n  {r.json()}\n")

def cmd_delete(key):
    r = requests.post(f"{API_URL}/api/admin/delete_key",
                       json={"key": key}, headers=headers(), timeout=10)
    print(f"\n  {r.json()}\n")

def cmd_msg(text):
    r = requests.post(f"{API_URL}/api/admin/message",
                       json={"text": text}, headers=headers(), timeout=10)
    print(f"\n  Mesaj gonderildi: {r.json()['message']}\n")

def cmd_ban(hwid):
    r = requests.post(f"{API_URL}/api/admin/ban_hwid",
                       json={"key": hwid}, headers=headers(), timeout=10)
    print(f"\n  {r.json()}\n")

def cmd_help():
    print("""
  Cesur Admin Paneli
  ─────────────────────────────
  python admin.py create [gun]              -> Key olustur
  python admin.py list                      -> Keyleri listele
  python admin.py revoke <KEY>              -> Keyi iptal et
  python admin.py unrevoke <KEY>            -> Keyi geri ac
  python admin.py delete <KEY>              -> Keyi sil
  python admin.py msg "<mesaj>"             -> Acilista mesaj goster
  python admin.py ban <HWID>                -> Makineyi engelle
  python admin.py set_token <token>         -> Admin token degistir
    """)

def cmd_set_token(token):
    global ADMIN_TOKEN
    ADMIN_TOKEN = token
    print(f"\n  Token guncellendi: {token}\n")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args: cmd_help(); sys.exit(0)

    cmd = args[0].lower()
    if cmd == "create":    cmd_create(int(args[1]) if len(args) > 1 else 7)
    elif cmd == "list":    cmd_list()
    elif cmd == "revoke":  cmd_revoke(args[1])
    elif cmd == "unrevoke": cmd_unrevoke(args[1])
    elif cmd == "delete":  cmd_delete(args[1])
    elif cmd == "msg":     cmd_msg(" ".join(args[1:]))
    elif cmd == "ban":     cmd_ban(args[1])
    elif cmd == "set_token": cmd_set_token(args[1])
    else: cmd_help()
