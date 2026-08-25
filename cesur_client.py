"""
Cesur License Client - Hileye entegre edilecek lisans dogrulama modulu.
Kullanim:
    from cesur_client import verify_license
    ok, msg = verify_license("CESUR-XXXX-XXXX-XXXX")
"""
import requests, hashlib, uuid, wmi, time, sys

API_URL = "https://cesur-api.onrender.com"

def get_hwid() -> str:
    """Makine kimligi (HWID) - WMI ile donanim bilgisinden uretilir."""
    try:
        c = wmi.WMI()
        cpu = c.Win32_Processor()[0].ProcessorId.strip()
        mb = c.Win32_BaseBoard()[0].SerialNumber.strip()
        disk = c.Win32_DiskDrive()[0].SerialNumber.strip()
        raw = f"{cpu}-{mb}-{disk}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32].upper()
    except Exception:
        return hashlib.sha256(uuid.getnode().to_bytes(6,'big')).hexdigest()[:32].upper()

def verify_license(key: str, api_url: str = None) -> tuple:
    """
    Lisans dogrulama.
    Returns: (True, mesaj) veya (False, hata_mesaji)
    """
    url = (api_url or API_URL).rstrip("/") + "/api/validate"
    hwid = get_hwid()

    for attempt in range(3):
        try:
            resp = requests.post(url, json={"key": key, "hwid": hwid}, timeout=10)
            data = resp.json()

            if data.get("valid"):
                msg = data.get("message", "")
                days = data.get("remaining_days", "?")
                info = f"Lisans gecerli (kalan: {days} gun)"
                if msg:
                    info += f"\n\n{msg}"
                return True, info
            else:
                return False, data.get("reason", "Lisans gecersiz.")
        except requests.exceptions.ConnectionError:
            if attempt < 2:
                time.sleep(2)
                continue
            return False, "Sunucuya baglanamiyor. Internet baglantinizi kontrol edin."
        except Exception as e:
            return False, f"Dogrulama hatasi: {e}"

    return False, "Sunucu yanit vermiyor. Tekrar deneyin."

def check_license_on_startup(key: str, api_url: str = None) -> bool:
    """
    Baslangic ekraninda lisans dogrulama.
    Gecerliyse True doner, gecersizse sys.exit() ile kapatir.
    """
    print("=" * 50)
    print("  Cesur - Lisans Dogrulama")
    print("=" * 50)
    print()
    print("  Lisans dogrulanıyor...")
    print()

    ok, msg = verify_license(key, api_url)

    if ok:
        print(f"  ✓ {msg}")
        print()
        time.sleep(1)
        return True
    else:
        print(f"  ✗ {msg}")
        print()
        print("  Hile kapatiliyor.")
        print("=" * 50)
        time.sleep(3)
        sys.exit(1)

if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else "CESUR-TEST-XXXX-XXXX"
    ok, msg = verify_license(key)
    print(f"Sonuc: {'GECERLI' if ok else 'GECERSIZ'}")
    print(f"Mesaj: {msg}")
