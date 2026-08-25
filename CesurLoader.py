import pymem
import pymem.process
import win32gui
import win32con
import win32api
import time
import os
import pygame
import requests
import math
import tkinter as tk
from tkinter import ttk, colorchooser
import threading
import keyboard
import ctypes
import ctypes.wintypes
import json
import sys
from collections import deque
import random
import hashlib
import uuid

# ══════════════════════════════════════════════════════════
# CESUR LICENSE API
# ══════════════════════════════════════════════════════════
CESUR_API_URL  = "https://cesur-api.onrender.com"
CESUR_LICENSE_KEY = "CESUR-YOUR-KEY-HERE"

def _cesur_hwid():
    try:
        import wmi as _wmi
        c = _wmi.WMI()
        cpu = c.Win32_Processor()[0].ProcessorId.strip()
        mb = c.Win32_BaseBoard()[0].SerialNumber.strip()
        disk = c.Win32_DiskDrive()[0].SerialNumber.strip()
        return hashlib.sha256(f"{cpu}-{mb}-{disk}".encode()).hexdigest()[:32].upper()
    except Exception:
        return hashlib.sha256(uuid.getnode().to_bytes(6,'big')).hexdigest()[:32].upper()

def _cesur_validate():
    print("=" * 50)
    print("  Cesur - Lisans Dogrulama")
    print("=" * 50)
    print()
    print("  Lisans dogrulanıyor...")
    print()
    hwid = _cesur_hwid()
    for attempt in range(3):
        try:
            r = requests.post(CESUR_API_URL.rstrip("/") + "/api/validate",
                              json={"key": CESUR_LICENSE_KEY, "hwid": hwid}, timeout=10)
            d = r.json()
            if d.get("valid"):
                msg = d.get("message", "")
                days = d.get("remaining_days", "?")
                info = f"Lisans gecerli (kalan: {days} gun)"
                if msg: info += f"\n\n{msg}"
                print(f"  ✓ {info}")
                print()
                time.sleep(1)
                return True
            else:
                print(f"  ✗ {d.get('reason', 'Lisans gecersiz.')}")
                print()
                print("  Hile kapatiliyor.")
                print("=" * 50)
                time.sleep(3)
                sys.exit(1)
        except requests.exceptions.ConnectionError:
            if attempt < 2:
                print("  Sunucuya baglanamiyor, tekrar deneniyor...")
                time.sleep(2)
                continue
            print("  Sunucuya baglanamiyor. Internet baglantinizi kontrol edin.")
            time.sleep(3)
            sys.exit(1)
        except Exception as e:
            print(f"  Dogrulama hatasi: {e}")
            time.sleep(3)
            sys.exit(1)
    sys.exit(1)

# ★ Streamproof API
_user32_dll = ctypes.WinDLL('user32', use_last_error=True)
_SetWindowDisplayAffinity = _user32_dll.SetWindowDisplayAffinity
_SetWindowDisplayAffinity.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.DWORD]
_SetWindowDisplayAffinity.restype  = ctypes.wintypes.BOOL
WDA_NONE             = 0x00000000
WDA_EXCLUDEFROMCAPTURE = 0x00000011

def apply_streamproof(hwnd, enable):
    try:
        _SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE if enable else WDA_NONE)
    except Exception: pass

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

WINDOW_WIDTH  = 1920
WINDOW_HEIGHT = 1080

_surf_lightning   = None
_surf_particles   = None
_surf_arrows      = None
_surf_trajectory  = None  # ★ FIX: Separate surface for grenade trajectory
_surf_snow        = None
_surf_fov         = None
_surf_spec_bg     = None
_surf_weapon_icon = None

_font_esp       = None
_font_dist      = None
_font_weapon    = None
_font_grenade   = None
_font_spec_hdr  = None
_font_spec_name = None
_font_spec_wep  = None
_font_c4_big    = None
_font_c4_small  = None

CONFIG_FOLDER = "configs"
if not os.path.exists(CONFIG_FOLDER):
    os.makedirs(CONFIG_FOLDER)

# ══════════════════════════════════════════════════════════
# TOGGLES & SETTINGS
# ══════════════════════════════════════════════════════════
esp_skeleton      = False
esp_box           = False
esp_healthbar     = False
esp_chams         = False
esp_teammates     = False
esp_names         = False
esp_head          = False
bombtimer_enabled = False
fov_changer_enabled = False
fov_changer_value   = 90
triggerbot_enabled  = False
aimbot_enabled      = False
aimbot_hold_mode    = True
aimbot_auto_shoot   = True
aimbot_fov          = 90.0
aimbot_smooth       = 3.5
aimbot_max_angle    = 90.0
aimbot_bone         = 6
aimbot_priority     = "crosshair"
aimbot_only_visible = True
aimbot_wallbang     = False
triggerbot_thread_delay     = 0.001
triggerbot_click_delay      = 0.0005
triggerbot_continuous       = True
triggerbot_wallbang         = False
triggerbot_pre_delay        = 0.0
triggerbot_post_delay       = 0.0
triggerbot_hold_mode        = False
triggerbot_hold_key         = ""
triggerbot_shoot_teammates  = False
glow_enabled      = False
glow_show_enemies = True
glow_show_team    = False
glow_color_enemy  = (0.0, 1.0, 0.0, 1.0)
glow_color_team   = (0.0, 0.0, 1.0, 1.0)
bhop_enabled      = False
skeleton_color    = (255, 255, 255)
visible_color     = (0, 255, 0)
hidden_color      = (255, 0, 0)
chams_head_color  = (200, 150, 100)
chams_head_hidden = (80, 60, 40)
chams_body_color  = (100, 100, 150)
chams_body_hidden = (50, 50, 75)
chams_arms_color  = (150, 120, 100)
chams_arms_hidden = (60, 48, 40)
chams_legs_color  = (80, 60, 40)
chams_legs_hidden = (40, 30, 20)
chams_gloves_color  = (120, 100, 90)
chams_gloves_hidden = (60, 50, 40)
chams_helmet_color  = (140, 140, 140)
chams_helmet_hidden = (80, 80, 80)
chams_armor_color   = (180, 100, 80)
chams_armor_hidden  = (90, 50, 40)
chams_shoes_color   = (60, 50, 40)
chams_shoes_hidden  = (30, 25, 20)
player_trails_enabled = False
trail_color            = (180, 0, 255)
player_trail_history   = deque(maxlen=60)
chams_visible_alpha   = 140
chams_invisible_alpha = 90

lightning_effect_enabled = True
lightning_color          = (255, 255, 255)
lightning_glow_color     = (200, 170, 255)
lightning_duration       = 2.0
lightning_fall_speed     = 1.0
lightning_thickness      = 1.0
lightning_core_thickness = 2
lightning_glow_thickness = 14
lightning_segments       = 20
lightning_offset         = 22
lightning_spark_count    = 22
lightning_top_extend     = 2.5
lightning_deaths = {}
_entity_hp_prev  = {}
_entity_last_known_pos = {}  # ★ FIX: Cache last known bone positions for death effects

death_particles_enabled = True
death_particle_color    = (255, 80, 0)
death_particle_speed    = 1.0
death_particle_lifetime = 1.0
_death_particle_systems = []

noflash_enabled = False
nosmoke_enabled = False

smoke_color_enabled = False
smoke_color_r = 255
smoke_color_g = 255
smoke_color_b = 255

enemy_arrows_enabled = False
enemy_arrow_color    = (255, 50, 50)
enemy_arrow_radius   = 90

humanize_enabled     = False
humanize_base_smooth = 3.5
humanize_base_fov    = 90.0
_hum_smooth_cur      = 3.5
_hum_max_angle_cur   = 90.0
_hum_fov_cur         = 90.0
_hum_last_tick       = 0.0
_hum_direction       = 1   # +1 up, -1 down (linked)

spectator_list_enabled = True
spectator_show_weapon  = True

hitsound_enabled     = True
_hitsound_obj        = None
_hitsound_last       = 0.0
_local_shots_prev    = 0
_local_last_shot_time = 0.0
_SHOT_WINDOW         = 0.05   # ★ FIX: 0.45 → 0.05s — sadece çok yakın zamanda atılan atışlar için
_shot_consumed       = False   # ★ FIX: Her atış için 1 hitsound — tekrar çalmaz

grenade_trajectory_enabled       = True
grenade_trajectory_color         = (255, 200, 0)
grenade_trajectory_color_bounce  = (255, 100, 0)

aimbot_fov_circle_enabled = False
aimbot_fov_circle_color   = (255, 255, 255)

skeleton_thickness = 2
box_esp_color      = (255, 255, 0)
box_esp_scale      = 1.0   # ★ Box boyut çarpanı (0.5 = küçük, 1.0 = normal, 1.5 = büyük)

aimbot_hitbox_head = True
aimbot_hitbox_body = False
aimbot_hitbox_legs = False

triggerbot_hitbox_head = True
triggerbot_hitbox_body = True
triggerbot_hitbox_legs = False

# ★ STREAMPROOF
streamproof_enabled = False

# ★ SILENT AIM
silent_aim_enabled  = False
silent_aim_fov      = 8.0   # derece — bu FOV içindeki düşmana silent aim

# ★ BULLET TRACER
bullet_tracer_enabled = False
bullet_tracer_color   = (255, 80, 0)
bullet_tracer_duration = 0.4
_bullet_tracers = []   # [{'start':(x,y), 'end':(x,y), 'born':t}]

# ★ AIR STRAFE / JUMP SHOT
air_strafe_enabled  = False   # havadayken de vurma
jump_shot_enabled   = False   # zıplarken vurma (bhop ile uyumlu)

# ★ SNIPER CROSSHAIR
sniper_crosshair_enabled = False
sniper_crosshair_size    = 20
sniper_crosshair_thick   = 2
sniper_crosshair_color   = (0, 255, 0)
sniper_crosshair_dot     = True

# ★ WATERMARK
watermark_enabled = True
watermark_text    = "powered by Cesur"

_drag_c4_pos   = None
_drag_spec_pos = None
_gui_is_open   = False
_drag_active   = None
_drag_offset   = (0, 0)

snow_mode_enabled = False
snow_color        = (255, 255, 255)
sky_color_enabled = False
sky_color_r = 100
sky_color_g = 149
sky_color_b = 237
snow_density    = 200
_snow_particles = []

# Bone offsets
m_fFlags             = 0x3C8   # m_fFlags (also used by bhop)
m_vecAbsVelocity_off = 0x3C4   # only used for bhop reference; unused now

keybinds = {
    'skeleton':  'F1',
    'box':       'F2',
    'healthbar': 'F3',
    'chams':     'F4',
    'teammates': 'F5',
    'triggerbot':'F6',
    'aimbot':    'left shift',
    'bhop':      'F8',
    'gui':       'insert'
}
VK_XBUTTON1 = 0x05
VK_XBUTTON2 = 0x06

print("=" * 70)
print(" BY CESUR ")
print("=" * 70)
print("\nOffsetler indiriliyor...")

# Çoklu kaynak — sırayla dener, ilk çalışanı kullanır
_OFFSET_SOURCES = [
    (
        'https://raw.githubusercontent.com/sezzyaep/CS2-OFFSETS/main/offsets.json',
        'https://raw.githubusercontent.com/sezzyaep/CS2-OFFSETS/main/client_dll.json',
        'sezzyaep'
    ),
    (
        'https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json',
        'https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json',
        'a2x'
    ),
    (
        'https://raw.githubusercontent.com/ro0ti/CS2-Offsets/main/offsets.json',
        'https://raw.githubusercontent.com/ro0ti/CS2-Offsets/main/client_dll.json',
        'ro0ti'
    ),
]

offsets    = None
client_dll = None

for _off_url, _cli_url, _src_name in _OFFSET_SOURCES:
    try:
        print(f"  → {_src_name} deneniyor...")
        _off = requests.get(_off_url, timeout=8).json()
        _cli = requests.get(_cli_url, timeout=8).json()
        # Temel key kontrolü
        if 'client.dll' not in _off or 'dwEntityList' not in _off['client.dll']:
            print(f"  ✗ {_src_name}: eksik key, atlanıyor")
            continue
        offsets    = _off
        client_dll = _cli
        print(f"✅ Offsetler indirildi! Kaynak: {_src_name}")
        break
    except Exception as _e:
        print(f"  ✗ {_src_name}: {_e}")

if offsets is None:
    print("❌ Hiçbir offset kaynağına ulaşılamadı!")
    exit(1)

dwEntityList          = offsets['client.dll']['dwEntityList']
dwLocalPlayerPawn     = offsets['client.dll']['dwLocalPlayerPawn']
dwViewMatrix          = offsets['client.dll']['dwViewMatrix']
m_pGameSceneNode      = 0x330
m_modelState          = 0x140
m_hPlayerPawn         = 0x914
m_iHealth             = 0x34c
m_iTeamNum            = 0x3e7
m_lifeState           = 0x354
m_vecOrigin           = 0x80
m_iIDEntIndex         = 0x1528

# ★ DOĞRU YOL (a2x issue#362 + TKazer teyitli):
# pawn → m_pClippingWeapon (0x1620) → weapon entity (direkt ptr, handle değil!)
# weapon → m_AttributeManager (0x1148) → m_Item (0x50) → m_iItemDefinitionIndex (0x1BA)
try:
    m_pClippingWeapon = client_dll['client.dll']['classes'].get('C_CSPlayerPawnBase',{}).get('fields',{}).get('m_pClippingWeapon', 0)
except:
    m_pClippingWeapon = 0

# WeaponServices path (artık kullanılmıyor ama compat için sakla)
try:
    _wepsvc = client_dll['client.dll']['classes']['C_CSPlayerPawnBase']['fields']
    m_pWeaponServices = _wepsvc.get('m_pWeaponServices', 0x1208)
except:
    m_pWeaponServices = 0x1208

try:
    _wepsvc2 = client_dll['client.dll']['classes']['CPlayer_WeaponServices']['fields']
    m_hActiveWeapon = _wepsvc2.get('m_hActiveWeapon', 0x60)
except:
    m_hActiveWeapon = 0x60

# m_vecVelocity for players (for trajectory prediction)
try:
    m_vecVelocity = client_dll['client.dll']['classes']['C_BaseEntity']['fields'].get('m_vecVelocity', 0x430)
except:
    m_vecVelocity = 0x430

try:
    m_iShotsFired = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_iShotsFired']
except:
    m_iShotsFired = 0x1c8c

try:
    m_bIsScoped = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_bIsScoped']
except:
    m_bIsScoped = 0x1c78

try:
    m_entitySpottedState = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields']['m_entitySpottedState']
    m_bSpottedByMask     = m_entitySpottedState + 0xC
except:
    m_bSpottedByMask = 0x1c6c

dwPlantedC4           = offsets['client.dll'].get('dwPlantedC4', 0)
dwGlobalVars          = offsets['client.dll'].get('dwGlobalVars', 0)
dwLocalPlayerController = offsets['client.dll'].get('dwLocalPlayerController', 0)
dwViewAngles          = offsets['client.dll'].get('dwViewAngles', 0)
dwCSGOInput           = offsets['client.dll'].get('dwCSGOInput', 0)

try:
    _csgoinput_cls        = client_dll['client.dll']['classes']['CCSGOInput']['fields']
    m_bIsThirdPersonCamera = _csgoinput_cls.get('m_bIsThirdPersonCamera', 0x40)
except Exception:
    m_bIsThirdPersonCamera = 0x40

dwGameEntitySystem                    = offsets['client.dll'].get('dwGameEntitySystem', 0)
dwGameEntitySystem_highestEntityIndex = offsets['client.dll'].get('dwGameEntitySystem_highestEntityIndex', 0x2090)

try:
    m_pObserverServices_off = client_dll['client.dll']['classes']['C_CSPlayerPawn']['fields'].get('m_pObserverServices', 0x1220)
except Exception:
    m_pObserverServices_off = 0x1220

try:
    _obs_cls = client_dll['client.dll']['classes'].get('CPlayer_ObserverServices', {}).get('fields', {})
    m_hObserverTarget_off = _obs_cls.get('m_hObserverTarget', 0x44)
except Exception:
    m_hObserverTarget_off = 0x44

try:
    m_angEyeAngles = client_dll['client.dll']['classes']['C_CSPlayerPawnBase']['fields']['m_angEyeAngles']
except:
    m_angEyeAngles = 0x1510

try:
    m_flFlashMaxAlpha = client_dll['client.dll']['classes']['C_CSPlayerPawnBase']['fields']['m_flFlashMaxAlpha']
except:
    m_flFlashMaxAlpha = 0x1450

try:
    _smoke_cls = client_dll['client.dll']['classes']['C_SmokeGrenadeProjectile']['fields']
    m_bSmokeEffectSpawned   = _smoke_cls.get('m_bSmokeEffectSpawned',   0x22C8)
    m_nSmokeEffectTickBegin = _smoke_cls.get('m_nSmokeEffectTickBegin', 0x22BC)
    # ★ FIX 2026: m_vSmokeColor — çoklu isim denemesi, bulunamazsa 0x22D0
    _scolor_keys = ['m_vSmokeColor', 'm_vecSmokeColor', 'm_SmokeColor',
                    'm_clrRender', 'm_vColor', 'm_vecColor']
    m_vSmokeColor = 0
    for _k in _scolor_keys:
        if _k in _smoke_cls:
            m_vSmokeColor = _smoke_cls[_k]
            print(f"✅ Smoke renk offset bulundu: {_k} = {hex(m_vSmokeColor)}")
            break
    if not m_vSmokeColor:
        m_vSmokeColor = 0x22D0
        print(f"⚠️ Smoke renk offset bulunamadı, default: {hex(m_vSmokeColor)}")
except:
    m_bSmokeEffectSpawned   = 0x22C8
    m_nSmokeEffectTickBegin = 0x22BC
    m_vSmokeColor           = 0x22D0

dwSmokeGrenadeProjectile = offsets['client.dll'].get('dwSmokeGrenadeProjectile', 0)

try:
    _base_grenade = client_dll['client.dll']['classes'].get('C_BaseCSGrenadeProjectile', {}).get('fields', {})
    m_vecVelocity_grenade = _base_grenade.get('m_vecVelocity', 0x118)
except Exception:
    m_vecVelocity_grenade = 0x118

# ★ FIX 2026: m_AttributeManager — community teyitli değerler çoklu fallback ile
# a2x issue#362: 0x1148 | dump 2026: 0x1378 | eski: 0xDD8
try:
    m_AttributeManager = client_dll['client.dll']['classes']['C_EconEntity']['fields'].get('m_AttributeManager', 0x11a8)
except:
    m_AttributeManager = 0x11a8

# ★ FIX: m_iItemDefinitionIndex — a2x issue#362: 0x1BA, eskisi 0x1B8
try:
    m_iItemDefinitionIndex = client_dll['client.dll']['classes']['CEconItemView']['fields'].get('m_iItemDefinitionIndex', 0x1BA)
except:
    m_iItemDefinitionIndex = 0x1BA

# ★ FIX 2026: m_Item — a2x issue#362: 0x50 | sezzyaep: 0x60 | önceki: 0x68
# Her üçünü de deneyen robust fonksiyon var, fallback chain burada
m_Item_offsets = [0x50, 0x60, 0x68]  # öncelik sırası: community → dump → eski
m_Item = 0x50  # default, _get_weapon_def_index içinde chain denenir

GRENADE_DEF_INDICES = {
    43: 'flashbang',    # weapon_flashbang
    44: 'flashbang',
    45: 'smoke',        # weapon_smokegrenade  (NOT 47!)
    46: 'he_grenade',   # weapon_hegrenade
    47: 'smoke',
    48: 'molotov',      # weapon_molotov
    49: 'decoy',        # weapon_decoy
    55: 'decoy',
    56: 'incendiary',   # weapon_incgrenade
}

ITEM_DEF_NAMES = {
    1:'DEAGLE', 2:'ELITE', 3:'FIVESEVEN', 4:'GLOCK', 7:'AK47', 8:'AUG',
    9:'AWP', 10:'FAMAS', 11:'G3SG1', 13:'GALIL', 14:'M249', 16:'M4A4',
    17:'MAC10', 19:'P90', 23:'MP5SD', 24:'UMP45', 25:'XM1014', 26:'BIZON',
    27:'MAG7', 28:'NEGEV', 29:'SAWEDOFF', 30:'TEC9', 31:'ZEUS', 32:'P2000',
    33:'MP7', 34:'MP9', 35:'NOVA', 36:'P250', 38:'SCAR20', 39:'SG553',
    40:'SSG08', 41:'KNIFE(GG)', 42:'KNIFE', 43:'FLASHBANG', 44:'FLASHBANG',
    45:'SMOKE', 46:'HE', 47:'SMOKE', 48:'MOLOTOV', 49:'DECOY',
    50:'INC', 55:'DECOY', 56:'INC', 57:'M4A1S', 58:'USPS', 59:'CZ75',
    60:'R8', 61:'TASER', 63:'MP5',
    # Knife skins
    500:'BAYONET', 503:'CSS KNIFE', 505:'FLIP', 506:'GUT',
    507:'KARAMBIT', 508:'M9 BAYONET', 509:'HUNTSMAN', 512:'FALCHION',
    514:'BOWIE', 515:'BUTTERFLY', 516:'SHADOW DAGR', 519:'URSUS',
    520:'NAVAJA', 521:'STILETTO', 522:'TALON', 523:'SKELETON KNIFE',
    525:'PARACORD', 526:'SURVIVAL', 527:'NOMAD', 528:'CLASSIC KNIFE',
    529:'GHOST', 531:'KNIFE (T)',
    # Gloves
    5027:'GLOVE', 5030:'GLOVE', 5031:'GLOVE', 5032:'GLOVE',
    5033:'GLOVE', 5034:'GLOVE', 5035:'GLOVE', 5025:'GLOVE',
}

# Weapon classname → display name (for reliable knife/all-weapon reading)
CLASSNAME_TO_DISPLAY = {
    'knife':            'KNIFE',
    'knife_t':          'KNIFE (T)',
    'knife_bayonet':    'BAYONET',
    'knife_css':        'CSS KNIFE',
    'knife_flip':       'FLIP',
    'knife_gut':        'GUT',
    'knife_karambit':   'KARAMBIT',
    'knife_m9_bayonet': 'M9 BAYONET',
    'knife_tactical':   'HUNTSMAN',
    'knife_falchion':   'FALCHION',
    'knife_survival_bowie': 'BOWIE',
    'knife_butterfly':  'BUTTERFLY',
    'knife_push':       'SHADOW DAGR',
    'knife_ursus':      'URSUS',
    'knife_gypsy_jackknife': 'NAVAJA',
    'knife_stiletto':   'STILETTO',
    'knife_widowmaker': 'TALON',
    'knife_skeleton':   'SKELETON KNIFE',
    'knife_cord':       'PARACORD',
    'knife_canis':      'SURVIVAL',
    'knife_outdoor':    'NOMAD',
    'knife_ghost':      'GHOST',
    'knife_gg':         'KNIFE(GG)',
    'deagle':           'DEAGLE',
    'elite':            'ELITE',
    'fiveseven':        'FIVESEVEN',
    'glock':            'GLOCK',
    'ak47':             'AK47',
    'aug':              'AUG',
    'awp':              'AWP',
    'famas':            'FAMAS',
    'g3sg1':            'G3SG1',
    'galilar':          'GALIL',
    'm249':             'M249',
    'm4a1':             'M4A4',
    'm4a1_silencer':    'M4A1S',
    'mac10':            'MAC10',
    'p90':              'P90',
    'mp5sd':            'MP5SD',
    'ump45':            'UMP45',
    'xm1014':           'XM1014',
    'bizon':            'BIZON',
    'mag7':             'MAG7',
    'negev':            'NEGEV',
    'sawedoff':         'SAWEDOFF',
    'tec9':             'TEC9',
    'taser':            'ZEUS',
    'hkp2000':          'P2000',
    'mp7':              'MP7',
    'mp9':              'MP9',
    'nova':             'NOVA',
    'p250':             'P250',
    'scar20':           'SCAR20',
    'sg556':            'SG553',
    'ssg08':            'SSG08',
    'usp_silencer':     'USPS',
    'cz75a':            'CZ75',
    'revolver':         'R8',
    'flashbang':        'FLASH',
    'smokegrenade':     'SMOKE',
    'molotov':          'MOLOTOV',
    'incgrenade':       'INC',
    'decoy':            'DECOY',
    'hegrenade':        'HE',
}

m_vecViewOffset  = 0xe78
m_sCustomName    = 0x310
esp_weapon_name  = False

try:
    planted_c4_fields = client_dll['client.dll']['classes']['C_PlantedC4']['fields']
    m_flC4Blow       = planted_c4_fields['m_flC4Blow']
    m_flTimerLength  = planted_c4_fields['m_flTimerLength']
    m_nBombSite      = planted_c4_fields['m_nBombSite']
    m_bBombTicking   = planted_c4_fields.get('m_bBombTicking', 4464)
except:
    m_flC4Blow, m_flTimerLength, m_nBombSite, m_bBombTicking = 4512, 4520, 4468, 4464

m_iDesiredFOV  = 1932
CURTIME_OFFSET = 0x2C

try:
    m_iszPlayerName = client_dll['client.dll']['classes']['CBasePlayerController']['fields']['m_iszPlayerName']
except:
    m_iszPlayerName = 0x6f4

print(f"📍 dwEntityList: {hex(dwEntityList)}")
print(f"📍 dwLocalPlayerPawn: {hex(dwLocalPlayerPawn)}")
print(f"📍 dwViewMatrix: {hex(dwViewMatrix)}")
print("\n🎮 CS2 bekleniyor...")
while True:
    time.sleep(1)
    try:
        pm     = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        print(f"✅ CS2 bulundu! client.dll base: {hex(client)}")
        break
    except:
        print("CS2 bulunamadı, bekleniyor...")
time.sleep(1)

BONE_CONNECTIONS = [
    (6,5),(5,4),(4,3),(3,2),(2,1),(1,0),
    (5,8),(8,9),(9,11),
    (5,13),(13,14),(14,16),
    (0,22),(22,23),(23,24),
    (0,25),(25,26),(26,27),
]

def init_persistent_surfaces():
    global _surf_lightning,_surf_particles,_surf_arrows,_surf_trajectory,_surf_snow
    global _surf_fov,_surf_spec_bg,_surf_weapon_icon
    global _font_esp,_font_dist,_font_weapon,_font_grenade
    global _font_spec_hdr,_font_spec_name,_font_spec_wep
    global _font_c4_big,_font_c4_small

    _surf_lightning   = pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT), pygame.SRCALPHA)
    _surf_particles   = pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT), pygame.SRCALPHA)
    _surf_arrows      = pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT), pygame.SRCALPHA)
    _surf_trajectory  = pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT), pygame.SRCALPHA)  # ★ FIX
    _surf_snow        = pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT), pygame.SRCALPHA)
    _surf_fov         = pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT), pygame.SRCALPHA)
    _surf_spec_bg     = pygame.Surface((260,300), pygame.SRCALPHA)
    _surf_weapon_icon = pygame.Surface((48,21), pygame.SRCALPHA)

    _font_esp       = pygame.font.SysFont('Arial', 11, bold=True)
    _font_dist      = pygame.font.SysFont('Arial', 10, bold=True)
    _font_weapon    = pygame.font.SysFont('Consolas', 10, bold=True)
    _font_grenade   = pygame.font.SysFont('Arial', 11, bold=True)
    _font_spec_hdr  = pygame.font.SysFont('Arial', 12, bold=True)
    _font_spec_name = pygame.font.SysFont('Arial', 11, bold=True)
    _font_spec_wep  = pygame.font.SysFont('Arial', 10)
    _font_c4_big    = pygame.font.SysFont('Arial', 48, bold=True)
    _font_c4_small  = pygame.font.SysFont('Arial', 24, bold=True)

def _clear_surf(s):
    s.fill((0,0,0,0))

def w2s(mtx, posx, posy, posz, width, height):
    try:
        screenW = mtx[12]*posx + mtx[13]*posy + mtx[14]*posz + mtx[15]
        if screenW < 0.01: return None
        screenX = mtx[0]*posx + mtx[1]*posy + mtx[2]*posz + mtx[3]
        screenY = mtx[4]*posx + mtx[5]*posy + mtx[6]*posz + mtx[7]
        camX = width/2; camY = height/2
        x = camX + (camX*screenX/screenW)
        y = camY - (camY*screenY/screenW)
        # ★ FIX: Increased tolerance so ESP doesn't vanish at high FOV values
        if x < -300 or x > width+300 or y < -300 or y > height+300: return None
        return [int(x), int(y)]
    except: return None

def _w2s_noclip(mtx, px, py, pz, W, H):
    try:
        sw = mtx[12]*px + mtx[13]*py + mtx[14]*pz + mtx[15]
        if sw < 0.01: return None
        sx = mtx[0]*px + mtx[1]*py + mtx[2]*pz + mtx[3]
        sy = mtx[4]*px + mtx[5]*py + mtx[6]*pz + mtx[7]
        return [W/2+(W/2*sx/sw), H/2-(H/2*sy/sw)]
    except: return None

def get_bone_position(bone_matrix, bone_index):
    try:
        x = pm.read_float(bone_matrix + bone_index*0x20)
        y = pm.read_float(bone_matrix + bone_index*0x20 + 0x4)
        z = pm.read_float(bone_matrix + bone_index*0x20 + 0x8)
        return (x, y, z)
    except: return None

def draw_skeleton(screen, bone_matrix, view_matrix, color, thickness=2, radius=3):
    bones_2d = {}
    for connection in BONE_CONNECTIONS:
        for bone_idx in connection:
            if bone_idx not in bones_2d:
                bone_pos = get_bone_position(bone_matrix, bone_idx)
                if bone_pos:
                    screen_pos = w2s(view_matrix, *bone_pos, WINDOW_WIDTH, WINDOW_HEIGHT)
                    if screen_pos: bones_2d[bone_idx] = screen_pos
    for bone1, bone2 in BONE_CONNECTIONS:
        if bone1 in bones_2d and bone2 in bones_2d:
            pos1 = bones_2d[bone1]; pos2 = bones_2d[bone2]
            pygame.draw.line(screen, color, pos1, pos2, thickness)
            pygame.draw.circle(screen, color, pos1, radius)
            pygame.draw.circle(screen, color, pos2, radius)
    return len(bones_2d) > 5, bones_2d

def draw_box(screen, head_pos, feet_pos, distance, color, thickness=2, bones_2d=None):
    """Vücuda göre gerçek bounding box — kemik pozisyonlarından hesaplanır."""
    try:
        draw_col = box_esp_color

        if bones_2d and len(bones_2d) >= 4:
            # Tüm kemik 2D pozisyonlarından min/max al
            xs = [p[0] for p in bones_2d.values()]
            ys = [p[1] for p in bones_2d.values()]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            # Biraz padding ekle
            pad_x = max(4, (max_x - min_x) * 0.12)
            pad_y = max(4, (max_y - min_y) * 0.05)
            x = int(min_x - pad_x)
            y = int(min_y - pad_y)
            w = int(max_x - min_x + pad_x * 2)
            h = int(max_y - min_y + pad_y * 2)
        else:
            # Fallback: head/feet'ten hesapla
            height = abs(head_pos[1] - feet_pos[1])
            if height < 5: return
            height = int(height * box_esp_scale)
            w = int(height * 0.42)
            center_x = (head_pos[0] + feet_pos[0]) // 2
            x = center_x - w // 2
            y = int(min(head_pos[1], feet_pos[1]))
            h = height

        if w < 5 or h < 5: return

        # Köşe çizgisi (corner box)
        clen = max(6, min(20, w // 4))
        pygame.draw.line(screen, draw_col, (x, y),       (x+clen, y),       thickness)
        pygame.draw.line(screen, draw_col, (x, y),       (x, y+clen),       thickness)
        pygame.draw.line(screen, draw_col, (x+w, y),     (x+w-clen, y),     thickness)
        pygame.draw.line(screen, draw_col, (x+w, y),     (x+w, y+clen),     thickness)
        pygame.draw.line(screen, draw_col, (x, y+h),     (x+clen, y+h),     thickness)
        pygame.draw.line(screen, draw_col, (x, y+h),     (x, y+h-clen),     thickness)
        pygame.draw.line(screen, draw_col, (x+w, y+h),   (x+w-clen, y+h),   thickness)
        pygame.draw.line(screen, draw_col, (x+w, y+h),   (x+w, y+h-clen),   thickness)

        _f   = _font_dist if _font_dist is not None else pygame.font.SysFont('Arial', 10, bold=True)
        text = _f.render(f"{distance * 0.0254:.0f}m", True, draw_col)
        screen.blit(text, (x+w+4, y))
    except: pass

def draw_full_body_chams(screen, bone_matrix, view_matrix, is_visible):
    try:
        if not bone_matrix: return
        bones_2d = {}
        for bone_idx in range(28):
            try:
                bp = get_bone_position(bone_matrix, bone_idx)
                if bp:
                    b2 = w2s(view_matrix, bp[0], bp[1], bp[2], WINDOW_WIDTH, WINDOW_HEIGHT)
                    if b2: bones_2d[bone_idx] = b2
            except: pass
        if len(bones_2d) < 15: return
        if is_visible:
            head_col=(255,255,0); body_col=(0,255,255); arm_col=(255,0,0); leg_col=(0,255,0); thickness=5
        else:
            head_col=(50,50,0);  body_col=(0,50,50);   arm_col=(50,0,0);   leg_col=(0,50,0); thickness=4
        def draw_chain(chain, col, thick):
            for i in range(len(chain)-1):
                b1, b2 = chain[i], chain[i+1]
                if b1 in bones_2d and b2 in bones_2d:
                    pygame.draw.line(screen, col, bones_2d[b1], bones_2d[b2], thick)
                    pygame.draw.circle(screen, col, bones_2d[b1], 2)
        if 6 in bones_2d and 5 in bones_2d: draw_chain([6,5], head_col, thickness)
        spine = [b for b in [5,4,3,2,0] if b in bones_2d]
        if len(spine) >= 2: draw_chain(spine, body_col, thickness)
        for arm in [[5,8,9,11],[5,13,14,16]]:
            la = [b for b in arm if b in bones_2d]
            if len(la) >= 2: draw_chain(la, arm_col, thickness-1)
        for leg in [[0,22,23,24],[0,25,26,27]]:
            ll = [b for b in leg if b in bones_2d]
            if len(ll) >= 2: draw_chain(ll, leg_col, thickness)
    except Exception: pass

def _handle_to_entity(handle: int, entity_list: int) -> int:
    """
    Skinchanger GetEntityByHandle() mantığı — stride 0x70 (teyitli).
    """
    SAFE_MIN = 0x10000; SAFE_MAX = 0x7FFFFFFFFFFF
    if not handle or handle == 0xFFFFFFFF or handle == 0xFFFF: return 0
    if not entity_list or not (SAFE_MIN < entity_list < SAFE_MAX): return 0
    try:
        idx = handle & 0x7FFF
        le  = pm.read_longlong(entity_list + 0x8 * (idx >> 9) + 0x10)
        if not le or not (SAFE_MIN < le < SAFE_MAX): return 0
        ent = pm.read_longlong(le + 0x70 * (idx & 0x1FF))
        if ent and (SAFE_MIN < ent < SAFE_MAX): return ent
    except: pass
    return 0


def _get_weapon_entity(pawn):
    """
    Aktif silah entity pointer'ı al.
    Skinchanger mantığı: m_hActiveWeapon handle → GetEntityByHandle
    m_pWeaponServices offset: a2x dump'tan güncellenir, fallback 0xA28 (skinchanger default)
    m_hActiveWeapon offset: a2x dump'tan güncellenir, fallback 0x50 (skinchanger default)
    """
    SAFE_MIN = 0x10000; SAFE_MAX = 0x7FFFFFFFFFFF
    if not pawn or not (SAFE_MIN < pawn < SAFE_MAX): return 0
    try:
        entity_list = pm.read_longlong(client + dwEntityList)
        if not entity_list: return 0

        # Skinchanger offset sırası: dump değeri önce, sonra bilinen çalışanlar
        # m_pWeaponServices: skinchanger=0xA28, debug teyit=0x1098
        WS_OFFS  = [m_pWeaponServices, 0xA28, 0x1098, 0x11C8]
        # m_hActiveWeapon: skinchanger=0x50, debug teyit=0x44
        HAW_OFFS = [m_hActiveWeapon, 0x50, 0x44, 0x60]

        for ws_off in WS_OFFS:
            try:
                svc = pm.read_longlong(pawn + ws_off)
                if not svc or not (SAFE_MIN < svc < SAFE_MAX): continue
                for haw_off in HAW_OFFS:
                    try:
                        h = pm.read_uint(svc + haw_off)
                        if not h or h == 0xFFFFFFFF: continue
                        if not (1 <= (h & 0x7FFF) < 0x7FFF): continue
                        wep = _handle_to_entity(h, entity_list)
                        if wep:
                            return wep
                    except: continue
            except: continue
    except: pass
    return 0


def _get_weapon_def_index(pawn):
    """
    ItemDefinitionIndex oku — CS2 2026 güncel, 3 farklı yol.
    YOL 1: m_pClippingWeapon → m_AttributeManager + m_Item + m_iItemDefinitionIndex (direkt inline)
    YOL 2: m_pWeaponServices → m_hActiveWeapon handle → GetEntityByHandle → aynı chain
    YOL 3: m_pClippingWeapon üzerinden bilinen sabit offset kombinasyonları
    """
    SAFE_MIN = 0x10000; SAFE_MAX = 0x7FFFFFFFFFFF
    if not pawn or not (SAFE_MIN < pawn < SAFE_MAX): return 0

    # ★ YOL 1: m_pClippingWeapon (en güncel CS2 yolu — direkt pointer, handle değil)
    try:
        wep = pm.read_longlong(pawn + m_pClippingWeapon)
        if wep and (SAFE_MIN < wep < SAFE_MAX):
            # CS2 2026: m_AttributeManager + m_Item inline struct + m_iItemDefinitionIndex
            # Bilinen çalışan kombinasyonlar (community + a2x dump):
            # 0xDF8+0x60+0x24 = 0xE7C  (skinchanger/neptune)
            # 0x1148+0x50+0x1BA = 0x134C (a2x dump eski)
            # 0x1378+0x50+0x1BA = 0x157C (a2x dump yeni)
            # 0x11a8 = m_AttributeManager (C_EconEntity, 14177)
            COMBOS = [
                (0x11a8, 0x50, 0x1BA),
                (0x11a8, 0x60, 0x1BA),
                (0x1148, 0x50, 0x1BA),
                (0x1378, 0x50, 0x1BA),
                (0xDD8,  0x50, 0x1BA),
            ]
            for am, it, iid in COMBOS:
                try:
                    addr = wep + am + it + iid
                    if not (SAFE_MIN < addr < SAFE_MAX): continue
                    di = pm.read_ushort(addr)
                    if 1 <= di <= 9999:
                        return di
                except: continue
    except: pass

    # ★ YOL 2: m_pWeaponServices → m_hActiveWeapon handle yolu
    try:
        wep = _get_weapon_entity(pawn)
        if wep and (SAFE_MIN < wep < SAFE_MAX):
            COMBOS = [
                (0x11a8, 0x50, 0x1BA),
                (0x11a8, 0x60, 0x1BA),
                (0x1148, 0x50, 0x1BA),
                (0x1378, 0x50, 0x1BA),
            ]
            for am, it, iid in COMBOS:
                try:
                    addr = wep + am + it + iid
                    if not (SAFE_MIN < addr < SAFE_MAX): continue
                    di = pm.read_ushort(addr)
                    if 1 <= di <= 9999:
                        return di
                except: continue
    except: pass

    return 0

def _read_weapon_name_for_pawn(pawn):
    """
    Oyuncunun elindeki silahın adını döndür.
    ★ FIX 2026: DefIndex + raw memory scan in weapon entity (bıçaklar dahil)
    """
    SAFE_MIN = 0x10000; SAFE_MAX = 0x7FFFFFFFFFFF

    # ★ YOL 1: DefIndex → ITEM_DEF_NAMES
    di = _get_weapon_def_index(pawn)
    if di and di in ITEM_DEF_NAMES:
        return ITEM_DEF_NAMES[di]

    # ★ YOL 2: m_pClippingWeapon → weapon entity belleğinde "weapon_" raw scan
    # CS2'de weapon entity başından 0x800 byte taranır, "weapon_" prefix'li string bulunur
    try:
        wep = pm.read_longlong(pawn + m_pClippingWeapon)
        if wep and (SAFE_MIN < wep < SAFE_MAX):
            # Önce pointer chain dene (vtable, classname)
            for str_off in [0x10, 0x18, 0x20, 0x28, 0x30, 0x38, 0x40, 0x48, 0x50, 0x58]:
                try:
                    ptr = pm.read_longlong(wep + str_off)
                    if not ptr or not (SAFE_MIN < ptr < SAFE_MAX): continue
                    for depth in range(3):
                        try:
                            if depth > 0:
                                ptr2 = pm.read_longlong(ptr)
                                if not ptr2 or not (SAFE_MIN < ptr2 < SAFE_MAX): break
                                ptr = ptr2
                            raw = pm.read_string(ptr, 64)
                            if not raw: continue
                            raw_lower = raw.lower().strip('\x00 \t')
                            if raw_lower.startswith('weapon_') or 'weapon_' in raw_lower:
                                cls = raw_lower.split('weapon_')[-1].strip('\x00 ')
                                cls = cls.split('\x00')[0].strip()
                                if cls in CLASSNAME_TO_DISPLAY:
                                    return CLASSNAME_TO_DISPLAY[cls]
                        except: continue
                except: continue

            # ★ YOL 3: weapon entity + 0x300-0x400 arası string scan (CS2 m_sCustomName bölgesi)
            for scan_off in range(0x2E0, 0x420, 8):
                try:
                    ptr = pm.read_longlong(wep + scan_off)
                    if not ptr or not (SAFE_MIN < ptr < SAFE_MAX): continue
                    raw = pm.read_string(ptr, 64)
                    if not raw: continue
                    raw_lower = raw.lower().strip('\x00 ')
                    if 'weapon_' in raw_lower:
                        cls = raw_lower.split('weapon_')[-1].strip('\x00 ')
                        cls = cls.split('\x00')[0].strip()
                        if cls in CLASSNAME_TO_DISPLAY:
                            return CLASSNAME_TO_DISPLAY[cls]
                except: continue

            # ★ YOL 4: Raw byte scan — weapon entity bellekte "weapon_" ASCII string ara
            try:
                # 0x0 - 0x800 arası oku, "weapon_" prefix bul
                raw_bytes = pm.read_bytes(wep, 0x500)
                if raw_bytes:
                    needle = b'weapon_'
                    pos = 0
                    while True:
                        idx = raw_bytes.find(needle, pos)
                        if idx == -1: break
                        end = raw_bytes.find(b'\x00', idx)
                        if end == -1: end = idx + 40
                        candidate = raw_bytes[idx:min(end, idx+40)].decode('ascii', errors='ignore').lower()
                        cls = candidate.replace('weapon_', '', 1).strip('\x00 ')
                        if cls and cls in CLASSNAME_TO_DISPLAY:
                            return CLASSNAME_TO_DISPLAY[cls]
                        pos = idx + 1
            except: pass
    except: pass

    if di and di not in ITEM_DEF_NAMES:
        return f"[{di}]"
    return ""

def draw_weapon_esp_below_player(screen, feet_pos, weapon_name, font):
    """Oyuncunun altına silah adını ve renkli kategori göstergesini çiz."""
    if not weapon_name or not feet_pos: return
    try:
        fx = int(feet_pos[0]); fy = int(feet_pos[1]) + 4
        wf = _font_weapon if _font_weapon is not None else pygame.font.SysFont('Consolas', 10, bold=True)
        wn = weapon_name.upper()

        # Renk kategorileri
        if any(k in wn for k in ['KNIFE','BAYONET','KARAMBIT','FLIP','GUT','BUTTERFLY','SHADOW',
                                   'URSUS','NAVAJA','STILETTO','TALON','PARACORD','SURVIVAL',
                                   'NOMAD','CLASSIC','GHOST','SKELETON','FALCHION','BOWIE',
                                   'HUNTSMAN','M9','CSS','DAGR']):
            col = (255, 180,  50)   # Altın — bıçak
            prefix = "🔪 "
        elif any(k in wn for k in ['AWP','SSG','G3SG','SCAR']):
            col = (100, 220, 255)   # Cyan — keskin nişancı
            prefix = "🎯 "
        elif any(k in wn for k in ['FLASH','SMOKE','MOLOTOV','INC','DECOY','HE']):
            col = (255, 140,  60)   # Turuncu — el bombası
            prefix = "💣 "
        elif any(k in wn for k in ['DEAGLE','R8']):
            col = (255, 100, 100)   # Kırmızı — ağır tabanca
            prefix = ""
        elif any(k in wn for k in ['GLOCK','P250','USPS','P2000','CZ','TEC','ELITE','FIVE','USP']):
            col = (255, 230, 100)   # Sarı — tabanca
            prefix = ""
        elif any(k in wn for k in ['AK47','FAMAS','GALIL','M4A4','M4A1','AUG','SG553']):
            col = (180, 255, 120)   # Yeşil — saldırı tüfeği
            prefix = ""
        elif any(k in wn for k in ['NEGEV','M249']):
            col = (255,  80,  80)   # Kırmızı — LMG
            prefix = ""
        else:
            col = (210, 210, 210)   # Gri — diğer
            prefix = ""

        display = prefix + wn

        # Arka plan + metin
        txt_surf = wf.render(display, True, col)
        shd_surf = wf.render(display, True, (0, 0, 0))
        tw = txt_surf.get_width(); th = txt_surf.get_height()
        tx = fx - tw // 2

        # Hafif arka plan kutusu
        bg_surf = pygame.Surface((tw + 6, th + 4), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 110))
        screen.blit(bg_surf, (tx - 3, fy - 2))

        screen.blit(shd_surf, (tx + 1, fy + 1))
        screen.blit(txt_surf, (tx, fy))
    except Exception: pass

def draw_hp_bar(screen, x, y, width, height, hp_percent, color):
    try:
        pygame.draw.rect(screen, (50,50,50), (x,y,width,height))
        hp_h = int(height * hp_percent)
        pygame.draw.rect(screen, color, (x, y+height-hp_h, width, hp_h))
    except: pass

def distance_3d(x1,y1,z1,x2,y2,z2):
    return math.sqrt((x2-x1)**2+(y2-y1)**2+(z2-z1)**2)

# ══════════════════════════════════════════════════════════
# GRENADE TRAJECTORY
# ══════════════════════════════════════════════════════════

def _read_weapon_defindex_direct(pawn):
    """
    CS2 2026 — en güvenilir silah defindex okuma.
    m_pClippingWeapon → direkt pointer (handle değil) → offset chain.
    Ayrıca m_pWeaponServices → m_hActiveWeapon handle yolu da denenir.
    """
    SAFE = lambda a: isinstance(a,int) and 0x10000 < a < 0x7FFFFFFFFFFF
    if not SAFE(pawn): return 0
    try:
        el = pm.read_longlong(client + dwEntityList)
        if not SAFE(el): return 0
    except: return 0

    # ── YOL 1: m_pClippingWeapon (direkt ptr) ──────────────────────────
    # CS2 2026 güncel: pawn+0x1620 → weapon entity (pointer, handle değil)
    for clip_off in [m_pClippingWeapon, 0x1620, 0x1628, 0x1618]:
        try:
            wep = pm.read_longlong(pawn + clip_off)
            if not SAFE(wep): continue
            # m_iItemDefinitionIndex arama — CS2 2026 teyitli offsetler
            # weapon entity + 0xD68 civarında m_AttributeManager inline struct
            for total_off in [0xD68, 0xD70, 0xD78, 0xD80,
                               0xDF8, 0xE00, 0xE08,
                               0x1148, 0x1150,
                               0x1378, 0x1380]:
                try:
                    v = pm.read_ushort(wep + total_off)
                    if 1 <= v <= 9999: return v
                except: continue
        except: continue

    # ── YOL 2: m_pWeaponServices → m_hActiveWeapon handle ──────────────
    for ws_off in [m_pWeaponServices, 0xA28, 0x1098, 0x11C8, 0xA20, 0xA30]:
        try:
            svc = pm.read_longlong(pawn + ws_off)
            if not SAFE(svc): continue
            for haw_off in [m_hActiveWeapon, 0x50, 0x44, 0x60, 0x58]:
                try:
                    h = pm.read_uint(svc + haw_off)
                    if not h or h == 0xFFFFFFFF: continue
                    idx = h & 0x7FFF
                    if not (1 <= idx < 0x7FFF): continue
                    le  = pm.read_longlong(el + 0x8*(idx>>9) + 0x10)
                    if not SAFE(le): continue
                    wep = pm.read_longlong(le + 0x70*(idx & 0x1FF))
                    if not SAFE(wep): continue
                    for total_off in [0xD68, 0xD70, 0xD78, 0xDF8, 0xE00,
                                      0x1148, 0x1378]:
                        try:
                            v = pm.read_ushort(wep + total_off)
                            if 1 <= v <= 9999: return v
                        except: continue
                except: continue
        except: continue

    # ── YOL 3: Raw byte scan — weapon entity içinde defindex ara ────────
    for clip_off in [m_pClippingWeapon, 0x1620]:
        try:
            wep = pm.read_longlong(pawn + clip_off)
            if not SAFE(wep): continue
            raw = pm.read_bytes(wep, 0x1800)
            if not raw: continue
            # defindex genellikle 0x600-0x1800 arasında uint16 olarak bulunur
            for off in range(0x600, min(len(raw)-2, 0x1800), 2):
                v = int.from_bytes(raw[off:off+2], 'little')
                if v in ITEM_DEF_NAMES or v in GRENADE_DEF_INDICES:
                    return v
        except: continue

    return 0


def _get_active_grenade_type():
    """Local oyuncunun elindeki grenade türünü döndür. Grenade değilse None."""
    try:
        local_player = pm.read_longlong(client + dwLocalPlayerPawn)
        if not local_player: return None
        di = _read_weapon_defindex_direct(local_player)
        if di and di in GRENADE_DEF_INDICES:
            return GRENADE_DEF_INDICES[di]
        return None
    except: return None

def _simulate_grenade_trajectory(eye_pos, pitch_deg, yaw_deg, grenade_type='he_grenade', player_z=None):
    """
    CS2 grenade yörüngesi simülasyonu.
    CS2 fizik: gravity=800, dt=1/64, drag=0.99/frame, restitution grenade tipine göre değişir.
    """
    GRAVITY = 800.0
    DT      = 1.0 / 64.0
    MAX_STEPS = 1200

    # CS2'ye yakın parametreler (Source 2 fizik motoru)
    params = {
        'he_grenade':  {'spd': 750.0, 'rest': 0.45, 'fric': 0.80, 'max_b': 3, 'drag': 0.9900},
        'flashbang':   {'spd': 820.0, 'rest': 0.55, 'fric': 0.85, 'max_b': 4, 'drag': 0.9900},
        'smoke':       {'spd': 680.0, 'rest': 0.40, 'fric': 0.75, 'max_b': 2, 'drag': 0.9885},
        'molotov':     {'spd': 600.0, 'rest': 0.05, 'fric': 0.55, 'max_b': 1, 'drag': 0.9850},
        'incendiary':  {'spd': 600.0, 'rest': 0.05, 'fric': 0.55, 'max_b': 1, 'drag': 0.9850},
        'decoy':       {'spd': 750.0, 'rest': 0.45, 'fric': 0.80, 'max_b': 3, 'drag': 0.9900},
    }
    p = params.get(grenade_type, params['he_grenade'])

    pr = math.radians(pitch_deg)
    yr = math.radians(yaw_deg)
    cos_p = math.cos(pr); sin_p = math.sin(pr)
    dx = cos_p * math.cos(yr)
    dy = cos_p * math.sin(yr)
    dz = -sin_p

    SPD = p['spd']
    vx = dx * SPD; vy = dy * SPD; vz = dz * SPD

    # Grenade spawn'u oyuncunun gözünden biraz ileriden başlar
    spawn_fwd = 18.0
    x = eye_pos[0] + dx * spawn_fwd
    y = eye_pos[1] + dy * spawn_fwd
    z = eye_pos[2] + dz * spawn_fwd

    # Zemin tahmini: oyuncu z'si - biraz margin
    ground_z = (player_z - 1.0) if player_z is not None else (eye_pos[2] - 65.0)

    points = [(x, y, z)]
    bounce_points = []
    bounces = 0
    total_dist = 0.0

    for _ in range(MAX_STEPS):
        # Fizik adımı
        vz -= GRAVITY * DT
        vx *= p['drag']; vy *= p['drag']

        nx = x + vx * DT
        ny = y + vy * DT
        nz = z + vz * DT

        # Zemin çarpışması
        if nz <= ground_z:
            # Zemin çarpma noktasını interpolate et
            if vz * DT != 0:
                t_hit = max(0.0, min(1.0, (ground_z - z) / (vz * DT)))
            else:
                t_hit = 0.0
            nx = x + vx * DT * t_hit
            ny = y + vy * DT * t_hit
            nz = ground_z

            if bounces < p['max_b'] and abs(vz) > 20.0:
                # Sekme
                vz = -vz * p['rest']
                vx *= p['fric']
                vy *= p['fric']
                bounces += 1
                bounce_points.append((nx, ny, nz))
                x, y, z = nx, ny, nz
                points.append((x, y, z))
                if grenade_type in ('molotov', 'incendiary'):
                    break
                continue
            else:
                # Dur
                points.append((nx, ny, nz))
                break

        x, y, z = nx, ny, nz
        points.append((x, y, z))

        step_dist = math.hypot(vx * DT, vy * DT)
        total_dist += step_dist
        if total_dist > 6000.0: break
        # Yavaşladıysa dur
        if abs(vx) < 0.3 and abs(vy) < 0.3 and abs(vz) < 1.5 and z <= ground_z + 5:
            break

    return points, bounce_points

def draw_grenade_trajectory(screen, view_matrix):
    if not grenade_trajectory_enabled: return
    try:
        grenade_type = _get_active_grenade_type()
        if grenade_type is None: return
        local_player = pm.read_longlong(client + dwLocalPlayerPawn)
        if not local_player: return
        node = pm.read_longlong(local_player + m_pGameSceneNode)
        if not node: return
        ox = pm.read_float(node + m_vecOrigin)
        oy = pm.read_float(node + m_vecOrigin + 4)
        oz = pm.read_float(node + m_vecOrigin + 8)
        try:
            dz = pm.read_float(local_player + m_vecViewOffset + 8)
            if not (1.0 < abs(dz) < 120.0): dz = 64.0
        except Exception: dz = 64.0
        eye = (ox, oy, oz+dz)
        pitch, yaw = get_view_angles_reliable()
        if pitch is None: return
        pts_3d, bounce_3d = _simulate_grenade_trajectory(eye, pitch, yaw, grenade_type=grenade_type, player_z=oz)
        if len(pts_3d) < 2: return
        tr,tg,tb = grenade_trajectory_color
        br,bg_b,bb = grenade_trajectory_color_bounce
        surf = _surf_trajectory if _surf_trajectory is not None else pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT),pygame.SRCALPHA)
        _clear_surf(surf)
        MAX_PTS = 60; STEP = max(1, len(pts_3d)//MAX_PTS)
        sampled = pts_3d[::STEP]
        if sampled[-1] != pts_3d[-1]: sampled.append(pts_3d[-1])
        pts_2d = []
        for p in sampled:
            s = w2s(view_matrix,p[0],p[1],p[2],WINDOW_WIDTH,WINDOW_HEIGHT)
            if s is None: s = _w2s_noclip(view_matrix,p[0],p[1],p[2],WINDOW_WIDTH,WINDOW_HEIGHT)
            pts_2d.append(s)
        prev_pt = None
        for idx, pt in enumerate(pts_2d):
            if pt is None: prev_pt=None; continue
            ix,iy = int(pt[0]),int(pt[1])
            t = idx/max(len(pts_2d)-1,1)
            a_line = int(210*(0.5+0.5*(1.0-t*0.45)))
            if prev_pt is not None:
                pygame.draw.line(surf,(tr,tg,tb,a_line//3),prev_pt,(ix,iy),3)
                pygame.draw.line(surf,(tr,tg,tb,a_line),prev_pt,(ix,iy),1)
            if idx%5==0 and idx>0:
                pygame.draw.rect(surf,(tr,tg,tb,a_line),(ix-2,iy-2,4,4))
            prev_pt = (ix,iy)
        for bp in bounce_3d:
            sp = w2s(view_matrix,bp[0],bp[1],bp[2],WINDOW_WIDTH,WINDOW_HEIGHT)
            if sp is None: sp = _w2s_noclip(view_matrix,bp[0],bp[1],bp[2],WINDOW_WIDTH,WINDOW_HEIGHT)
            if sp:
                bx,by = int(sp[0]),int(sp[1])
                pygame.draw.line(surf,(br,bg_b,bb,230),(bx-8,by),(bx+8,by),2)
                pygame.draw.line(surf,(br,bg_b,bb,230),(bx,by-8),(bx,by+8),2)
                pygame.draw.circle(surf,(br,bg_b,bb,180),(bx,by),5,1)
        last_3d = pts_3d[-1]
        lp = w2s(view_matrix,last_3d[0],last_3d[1],last_3d[2],WINDOW_WIDTH,WINDOW_HEIGHT)
        if lp is None: lp = _w2s_noclip(view_matrix,last_3d[0],last_3d[1],last_3d[2],WINDOW_WIDTH,WINDOW_HEIGHT)
        if lp:
            lx,ly = int(lp[0]),int(lp[1])
            pygame.draw.circle(surf,(tr,tg,tb,160),(lx,ly),10,1)
            pygame.draw.circle(surf,(tr,tg,tb,220),(lx,ly),3)
            lbl_map = {'smoke':'SMOKE','flashbang':'FLASH','molotov':'MOLOTOV','incendiary':'INC','he_grenade':'HE','decoy':'DECOY'}
            lbl = lbl_map.get(grenade_type, grenade_type.upper())
            try:
                _lf  = _font_grenade if _font_grenade else pygame.font.SysFont('Arial',11,bold=True)
                sh   = _lf.render(lbl,True,(0,0,0)); txt = _lf.render(lbl,True,(tr,tg,tb))
                surf.blit(sh,(lx+15,ly-7)); surf.blit(txt,(lx+14,ly-8))
            except: pass
        screen.blit(surf,(0,0))
    except Exception: pass

def _init_snow_particles(count=None):
    global _snow_particles
    if count is None: count = snow_density
    _snow_particles = []
    sr,sg,sb = snow_color
    for _ in range(count):
        _snow_particles.append({
            'x':random.uniform(0,WINDOW_WIDTH),'y':random.uniform(0,WINDOW_HEIGHT),
            'vx':random.uniform(-0.5,0.5),'vy':random.uniform(0.3,1.2),
            'size':random.choice([1,1,2,2,3]),'alpha':random.randint(120,220),
            'wobble':random.uniform(0,math.pi*2),'r':sr,'g':sg,'b':sb,
        })

def draw_snow(screen):
    if not snow_mode_enabled: return
    if not _snow_particles: _init_snow_particles()
    snow_surf = _surf_snow if _surf_snow is not None else pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT),pygame.SRCALPHA)
    _clear_surf(snow_surf)
    for p in _snow_particles:
        p['wobble']+=0.02; p['x']+=p['vx']+math.sin(p['wobble'])*0.3; p['y']+=p['vy']
        if p['y']>WINDOW_HEIGHT+5: p['y']=-5; p['x']=random.uniform(0,WINDOW_WIDTH)
        if p['x']<-5: p['x']=WINDOW_WIDTH+5
        elif p['x']>WINDOW_WIDTH+5: p['x']=-5
        a=p['alpha']; s=p['size']; ix,iy=int(p['x']),int(p['y'])
        pr2,pg2,pb2=p.get('r',255),p.get('g',255),p.get('b',255)
        pygame.draw.circle(snow_surf,(pr2,pg2,pb2,a),(ix,iy),s)
        if s>=2: pygame.draw.circle(snow_surf,(min(255,pr2+20),min(255,pg2+40),min(255,pb2+55),min(255,a+30)),(ix,iy),max(1,s-1))
    screen.blit(snow_surf,(0,0))

# ══════════════════════════════════════════════════════════
# CONFIG SAVE / LOAD
# ══════════════════════════════════════════════════════════

def save_config(config_name):
    config = {
        "esp_skeleton":esp_skeleton,"esp_box":esp_box,"esp_healthbar":esp_healthbar,
        "esp_chams":esp_chams,"esp_teammates":esp_teammates,"esp_names":esp_names,
        "esp_head":esp_head,"esp_weapon_name":esp_weapon_name,
        "triggerbot_enabled":triggerbot_enabled,"triggerbot_continuous":triggerbot_continuous,
        "triggerbot_wallbang":triggerbot_wallbang,
        "triggerbot_pre_delay_ms":int(triggerbot_pre_delay*1000),
        "triggerbot_post_delay_ms":int(triggerbot_post_delay*1000),
        "triggerbot_click_delay_ms":int(triggerbot_click_delay*1000),
        "triggerbot_hold_key":triggerbot_hold_key,"triggerbot_hold_mode":triggerbot_hold_mode,
        "triggerbot_shoot_teammates":triggerbot_shoot_teammates,
        "aimbot_enabled":aimbot_enabled,"aimbot_hold_mode":aimbot_hold_mode,
        "aimbot_auto_shoot":aimbot_auto_shoot,"aimbot_only_visible":aimbot_only_visible,
        "aimbot_wallbang":aimbot_wallbang,"aimbot_fov":aimbot_fov,"aimbot_smooth":aimbot_smooth,
        "aimbot_max_angle":aimbot_max_angle,"aimbot_bone":aimbot_bone,
        "humanize_enabled":humanize_enabled,"humanize_base_smooth":humanize_base_smooth,
        "keybinds":keybinds,"bombtimer_enabled":bombtimer_enabled,
        "fov_changer_enabled":fov_changer_enabled,"fov_changer_value":fov_changer_value,
        "bhop_enabled":bhop_enabled,"noflash_enabled":noflash_enabled,
        "nosmoke_enabled":nosmoke_enabled,"hitsound_enabled":hitsound_enabled,
        "spectator_list_enabled":spectator_list_enabled,"spectator_show_weapon":spectator_show_weapon,
        "smoke_color_enabled":smoke_color_enabled,"smoke_color":[smoke_color_r,smoke_color_g,smoke_color_b],
        "skeleton_color":list(skeleton_color),"visible_color":list(visible_color),"hidden_color":list(hidden_color),
        "chams_head_color":list(chams_head_color),"chams_head_hidden":list(chams_head_hidden),
        "chams_body_color":list(chams_body_color),"chams_body_hidden":list(chams_body_hidden),
        "chams_arms_color":list(chams_arms_color),"chams_arms_hidden":list(chams_arms_hidden),
        "chams_legs_color":list(chams_legs_color),"chams_legs_hidden":list(chams_legs_hidden),
        "chams_gloves_color":list(chams_gloves_color),"chams_gloves_hidden":list(chams_gloves_hidden),
        "chams_helmet_color":list(chams_helmet_color),"chams_helmet_hidden":list(chams_helmet_hidden),
        "chams_armor_color":list(chams_armor_color),"chams_armor_hidden":list(chams_armor_hidden),
        "chams_shoes_color":list(chams_shoes_color),"chams_shoes_hidden":list(chams_shoes_hidden),
        "glow_enabled":glow_enabled,"glow_show_enemies":glow_show_enemies,"glow_show_team":glow_show_team,
        "player_trails_enabled":player_trails_enabled,"trail_color":list(trail_color),
        "lightning_effect_enabled":lightning_effect_enabled,"lightning_color":list(lightning_color),
        "lightning_duration":lightning_duration,"lightning_fall_speed":lightning_fall_speed,
        "lightning_thickness":lightning_thickness,
        "death_particles_enabled":death_particles_enabled,"death_particle_color":list(death_particle_color),
        "death_particle_speed":death_particle_speed,"death_particle_lifetime":death_particle_lifetime,
        "enemy_arrows_enabled":enemy_arrows_enabled,"enemy_arrow_color":list(enemy_arrow_color),
        "enemy_arrow_radius":enemy_arrow_radius,
        "grenade_trajectory_enabled":grenade_trajectory_enabled,
        "grenade_trajectory_color":list(grenade_trajectory_color),
        "grenade_trajectory_color_bounce":list(grenade_trajectory_color_bounce),
        "sky_color_enabled":sky_color_enabled,"sky_color":[sky_color_r,sky_color_g,sky_color_b],
        "snow_mode_enabled":snow_mode_enabled,"snow_color":list(snow_color),"snow_density":snow_density,
        "aimbot_fov_circle_enabled":aimbot_fov_circle_enabled,"aimbot_fov_circle_color":list(aimbot_fov_circle_color),
        "streamproof_enabled":streamproof_enabled,
        "sniper_crosshair_enabled":sniper_crosshair_enabled,"sniper_crosshair_size":sniper_crosshair_size,
        "sniper_crosshair_thick":sniper_crosshair_thick,"sniper_crosshair_color":list(sniper_crosshair_color),
        "sniper_crosshair_dot":sniper_crosshair_dot,"watermark_enabled":watermark_enabled,"watermark_text":watermark_text,
        "drag_c4_pos":list(_drag_c4_pos) if _drag_c4_pos else None,
        "drag_spec_pos":list(_drag_spec_pos) if _drag_spec_pos else None,
        "skeleton_thickness":skeleton_thickness,"box_esp_color":list(box_esp_color),"box_esp_scale":box_esp_scale,
        "aimbot_hitbox_head":aimbot_hitbox_head,"aimbot_hitbox_body":aimbot_hitbox_body,"aimbot_hitbox_legs":aimbot_hitbox_legs,
        "triggerbot_hitbox_head":triggerbot_hitbox_head,"triggerbot_hitbox_body":triggerbot_hitbox_body,"triggerbot_hitbox_legs":triggerbot_hitbox_legs,
    }
    filepath = os.path.join(CONFIG_FOLDER, f"{config_name}.json")
    try:
        with open(filepath,'w',encoding='utf-8') as f: json.dump(config,f,indent=4,ensure_ascii=False)
        print(f"✅ Config kaydedildi: {filepath}"); return True
    except Exception as e: print(f"❌ Config kaydetme hatası: {e}"); return False

def load_config(config_name):
    global esp_skeleton,esp_box,esp_healthbar,esp_chams,esp_teammates,esp_names,esp_head
    global bombtimer_enabled,fov_changer_enabled,fov_changer_value
    global triggerbot_enabled,triggerbot_continuous,triggerbot_wallbang
    global triggerbot_pre_delay,triggerbot_post_delay,triggerbot_click_delay
    global triggerbot_hold_key,triggerbot_hold_mode,triggerbot_shoot_teammates
    global aimbot_enabled,aimbot_hold_mode,aimbot_auto_shoot,aimbot_only_visible,aimbot_wallbang
    global aimbot_fov,aimbot_smooth,aimbot_max_angle,aimbot_bone
    global keybinds,skeleton_color,visible_color,hidden_color
    global chams_head_color,chams_head_hidden,chams_body_color,chams_body_hidden
    global chams_arms_color,chams_arms_hidden,chams_legs_color,chams_legs_hidden
    global chams_gloves_color,chams_gloves_hidden,chams_helmet_color,chams_helmet_hidden
    global chams_armor_color,chams_armor_hidden,chams_shoes_color,chams_shoes_hidden
    global glow_enabled,glow_show_enemies,glow_show_team,bhop_enabled
    global player_trails_enabled,trail_color
    global lightning_effect_enabled,lightning_color,lightning_duration,lightning_fall_speed,lightning_thickness
    global death_particles_enabled,death_particle_color,death_particle_speed,death_particle_lifetime
    global noflash_enabled,nosmoke_enabled,smoke_color_enabled,smoke_color_r,smoke_color_g,smoke_color_b
    global enemy_arrows_enabled,enemy_arrow_color,enemy_arrow_radius
    global hitsound_enabled,spectator_list_enabled,spectator_show_weapon
    global humanize_enabled,humanize_base_smooth,esp_weapon_name
    global grenade_trajectory_enabled,grenade_trajectory_color,grenade_trajectory_color_bounce
    global sky_color_enabled,sky_color_r,sky_color_g,sky_color_b,snow_mode_enabled,snow_color,snow_density
    global aimbot_fov_circle_enabled,aimbot_fov_circle_color,_drag_c4_pos,_drag_spec_pos
    global skeleton_thickness,box_esp_color,box_esp_scale
    global aimbot_hitbox_head,aimbot_hitbox_body,aimbot_hitbox_legs
    global triggerbot_hitbox_head,triggerbot_hitbox_body,triggerbot_hitbox_legs
    # ★ FIX: Missing globals that caused config load errors for non-Misc sections
    global streamproof_enabled
    global sniper_crosshair_enabled,sniper_crosshair_size,sniper_crosshair_thick
    global sniper_crosshair_color,sniper_crosshair_dot
    global watermark_enabled,watermark_text

    filepath = os.path.join(CONFIG_FOLDER, f"{config_name}.json")
    try:
        with open(filepath,'r',encoding='utf-8') as f: config = json.load(f)
        def _color(key, default):
            v = config.get(key, default); return tuple(v) if isinstance(v,(list,tuple)) else default
        esp_skeleton=config.get("esp_skeleton",esp_skeleton); esp_box=config.get("esp_box",esp_box)
        esp_healthbar=config.get("esp_healthbar",esp_healthbar); esp_chams=config.get("esp_chams",esp_chams)
        esp_teammates=config.get("esp_teammates",esp_teammates); esp_names=config.get("esp_names",esp_names)
        esp_head=config.get("esp_head",esp_head); esp_weapon_name=config.get("esp_weapon_name",esp_weapon_name)
        triggerbot_enabled=config.get("triggerbot_enabled",triggerbot_enabled)
        triggerbot_continuous=config.get("triggerbot_continuous",triggerbot_continuous)
        triggerbot_wallbang=config.get("triggerbot_wallbang",triggerbot_wallbang)
        triggerbot_pre_delay=config.get("triggerbot_pre_delay_ms",int(triggerbot_pre_delay*1000))/1000.0
        triggerbot_post_delay=config.get("triggerbot_post_delay_ms",int(triggerbot_post_delay*1000))/1000.0
        triggerbot_click_delay=config.get("triggerbot_click_delay_ms",int(triggerbot_click_delay*1000))/1000.0
        triggerbot_hold_key=config.get("triggerbot_hold_key",triggerbot_hold_key)
        triggerbot_hold_mode=config.get("triggerbot_hold_mode",triggerbot_hold_mode)
        triggerbot_shoot_teammates=config.get("triggerbot_shoot_teammates",triggerbot_shoot_teammates)
        aimbot_enabled=config.get("aimbot_enabled",aimbot_enabled)
        aimbot_hold_mode=config.get("aimbot_hold_mode",aimbot_hold_mode)
        aimbot_auto_shoot=config.get("aimbot_auto_shoot",aimbot_auto_shoot)
        aimbot_only_visible=config.get("aimbot_only_visible",aimbot_only_visible)
        aimbot_wallbang=config.get("aimbot_wallbang",aimbot_wallbang)
        aimbot_fov=config.get("aimbot_fov",aimbot_fov); aimbot_smooth=config.get("aimbot_smooth",aimbot_smooth)
        aimbot_max_angle=config.get("aimbot_max_angle",aimbot_max_angle); aimbot_bone=config.get("aimbot_bone",aimbot_bone)
        humanize_enabled=config.get("humanize_enabled",humanize_enabled)
        humanize_base_smooth=config.get("humanize_base_smooth",humanize_base_smooth)
        keybinds=config.get("keybinds",keybinds)
        bombtimer_enabled=config.get("bombtimer_enabled",bombtimer_enabled)
        fov_changer_enabled=config.get("fov_changer_enabled",fov_changer_enabled)
        fov_changer_value=config.get("fov_changer_value",fov_changer_value)
        bhop_enabled=config.get("bhop_enabled",bhop_enabled)
        noflash_enabled=config.get("noflash_enabled",noflash_enabled)
        nosmoke_enabled=config.get("nosmoke_enabled",nosmoke_enabled)
        hitsound_enabled=config.get("hitsound_enabled",hitsound_enabled)
        spectator_list_enabled=config.get("spectator_list_enabled",spectator_list_enabled)
        spectator_show_weapon=config.get("spectator_show_weapon",spectator_show_weapon)
        smoke_color_enabled=config.get("smoke_color_enabled",smoke_color_enabled)
        sc=config.get("smoke_color",[smoke_color_r,smoke_color_g,smoke_color_b])
        smoke_color_r,smoke_color_g,smoke_color_b=sc[0],sc[1],sc[2]
        skeleton_color=_color("skeleton_color",skeleton_color)
        visible_color=_color("visible_color",visible_color)
        hidden_color=_color("hidden_color",hidden_color)
        for k in ['head','body','arms','legs','gloves','helmet','armor','shoes']:
            globals()[f'chams_{k}_color']=_color(f'chams_{k}_color',globals()[f'chams_{k}_color'])
            globals()[f'chams_{k}_hidden']=_color(f'chams_{k}_hidden',globals()[f'chams_{k}_hidden'])
        glow_enabled=config.get("glow_enabled",glow_enabled)
        glow_show_enemies=config.get("glow_show_enemies",glow_show_enemies)
        glow_show_team=config.get("glow_show_team",glow_show_team)
        player_trails_enabled=config.get("player_trails_enabled",player_trails_enabled)
        trail_color=_color("trail_color",trail_color)
        lightning_effect_enabled=config.get("lightning_effect_enabled",lightning_effect_enabled)
        lightning_color=_color("lightning_color",lightning_color)
        lightning_duration=config.get("lightning_duration",lightning_duration)
        lightning_fall_speed=config.get("lightning_fall_speed",lightning_fall_speed)
        lightning_thickness=config.get("lightning_thickness",lightning_thickness)
        death_particles_enabled=config.get("death_particles_enabled",death_particles_enabled)
        death_particle_color=_color("death_particle_color",death_particle_color)
        death_particle_speed=config.get("death_particle_speed",death_particle_speed)
        death_particle_lifetime=config.get("death_particle_lifetime",death_particle_lifetime)
        enemy_arrows_enabled=config.get("enemy_arrows_enabled",enemy_arrows_enabled)
        enemy_arrow_color=_color("enemy_arrow_color",enemy_arrow_color)
        enemy_arrow_radius=config.get("enemy_arrow_radius",enemy_arrow_radius)
        grenade_trajectory_enabled=config.get("grenade_trajectory_enabled",grenade_trajectory_enabled)
        grenade_trajectory_color=_color("grenade_trajectory_color",grenade_trajectory_color)
        grenade_trajectory_color_bounce=_color("grenade_trajectory_color_bounce",grenade_trajectory_color_bounce)
        sky_color_enabled=config.get("sky_color_enabled",sky_color_enabled)
        skc=config.get("sky_color",[sky_color_r,sky_color_g,sky_color_b])
        sky_color_r,sky_color_g,sky_color_b=skc[0],skc[1],skc[2]
        snow_mode_enabled=config.get("snow_mode_enabled",snow_mode_enabled)
        snow_color=_color("snow_color",snow_color)
        snow_density=int(config.get("snow_density",snow_density))
        aimbot_fov_circle_enabled=config.get("aimbot_fov_circle_enabled",aimbot_fov_circle_enabled)
        aimbot_fov_circle_color=_color("aimbot_fov_circle_color",aimbot_fov_circle_color)
        streamproof_enabled=config.get("streamproof_enabled",streamproof_enabled)
        sniper_crosshair_enabled=config.get("sniper_crosshair_enabled",sniper_crosshair_enabled)
        sniper_crosshair_size=int(config.get("sniper_crosshair_size",sniper_crosshair_size))
        sniper_crosshair_thick=int(config.get("sniper_crosshair_thick",sniper_crosshair_thick))
        sniper_crosshair_color=_color("sniper_crosshair_color",sniper_crosshair_color)
        sniper_crosshair_dot=config.get("sniper_crosshair_dot",sniper_crosshair_dot)
        watermark_enabled=config.get("watermark_enabled",watermark_enabled)
        watermark_text=config.get("watermark_text",watermark_text)
        _dc4=config.get("drag_c4_pos",None)
        if _dc4 and len(_dc4)==2: _drag_c4_pos=tuple(_dc4)
        _dsp=config.get("drag_spec_pos",None)
        if _dsp and len(_dsp)==2: _drag_spec_pos=tuple(_dsp)
        skeleton_thickness=int(config.get("skeleton_thickness",skeleton_thickness))
        box_esp_color=_color("box_esp_color",box_esp_color)
        box_esp_scale=float(config.get("box_esp_scale",box_esp_scale))
        aimbot_hitbox_head=config.get("aimbot_hitbox_head",aimbot_hitbox_head)
        aimbot_hitbox_body=config.get("aimbot_hitbox_body",aimbot_hitbox_body)
        aimbot_hitbox_legs=config.get("aimbot_hitbox_legs",aimbot_hitbox_legs)
        triggerbot_hitbox_head=config.get("triggerbot_hitbox_head",triggerbot_hitbox_head)
        triggerbot_hitbox_body=config.get("triggerbot_hitbox_body",triggerbot_hitbox_body)
        triggerbot_hitbox_legs=config.get("triggerbot_hitbox_legs",triggerbot_hitbox_legs)
        print(f"✅ Config yüklendi: {filepath}"); return True
    except Exception as e: print(f"❌ Config yükleme hatası: {e}"); return False

def list_configs():
    try: return [f.replace('.json','') for f in os.listdir(CONFIG_FOLDER) if f.endswith('.json')]
    except: return []

# ══════════════════════════════════════════════════════════
# GLOW & BHOP
# ══════════════════════════════════════════════════════════

class CS2GlowManager:
    def __init__(self):
        self.m_Glow=0x28; self.m_glowColorOverride=0x30; self.m_bGlowing=0x244; self.m_iGlowType=0x248
    def _to_argb(self,r,g,b,a):
        clamp=lambda x: max(0,min(1,x)); r,g,b,a=[int(clamp(c)*255) for c in (r,g,b,a)]
        return (a<<24)|(b<<16)|(g<<8)|r
    def update_glow(self):
        if not glow_enabled: return
        try:
            local=pm.read_longlong(client+dwLocalPlayerPawn)
            entities=pm.read_longlong(client+dwEntityList)
            team=pm.read_int(local+m_iTeamNum) if local else None
            if not (local and entities and team is not None): return
            for i in range(1,65):
                try:
                    le=pm.read_longlong(entities+0x8*((i&0x7FFF)>>9)+0x10)
                    if not le: continue
                    ctrl=pm.read_longlong(le+0x70*(i&0x1FF))
                    if not ctrl: continue
                    ph=pm.read_uint(ctrl+m_hPlayerPawn)
                    if not ph or ph==0xFFFFFFFF: continue
                    e2=pm.read_longlong(entities+0x8*((ph&0x7FFF)>>9)+0x10)
                    if not e2: continue
                    pawn=pm.read_longlong(e2+0x70*(ph&0x1FF))
                    if not pawn or pawn==local: continue
                    if pm.read_int(pawn+m_lifeState)!=256: continue
                    is_team=pm.read_int(pawn+m_iTeamNum)==team
                    if is_team and not glow_show_team: continue
                    if not is_team and not glow_show_enemies: continue
                    color=glow_color_team if is_team else glow_color_enemy
                    argb_color=self._to_argb(*color)
                    pm.write_uint(pawn+self.m_glowColorOverride,argb_color)
                    pm.write_byte(pawn+self.m_bGlowing,1)
                    pm.write_uint(pawn+self.m_iGlowType,3)
                except: continue
        except: pass

class BHopManager:
    def __init__(self):
        self.last_jump=0; self.VK_SPACE=0x20
    def press_space_fast(self):
        try:
            ctypes.windll.user32.keybd_event(self.VK_SPACE,0,0,0)
            time.sleep(0.0005)
            ctypes.windll.user32.keybd_event(self.VK_SPACE,0,2,0)
        except: pass
    def update_bhop(self):
        if not bhop_enabled: return
        # ★ FIX: Use keyboard.is_pressed — more reliable than GetAsyncKeyState for bhop
        if not keyboard.is_pressed('space'): return
        try:
            local=pm.read_longlong(client+dwLocalPlayerPawn)
            if not local: return
            # ★ FIX: read_uint + correct m_fFlags offset (not m_lifeState+0x100)
            flags=pm.read_uint(local+m_fFlags)
            on_ground=bool(flags&(1<<0))
            if on_ground:
                now=time.time()
                # ★ FIX: 20ms cooldown matches CS2 server tick rate
                if now-self.last_jump>0.020:
                    self.press_space_fast()
                    self.last_jump=now
        except: pass

glow_manager=None; bhop_manager=None

def get_local_index():
    try:
        entity_list=pm.read_longlong(client+dwEntityList)
        local_player=pm.read_longlong(client+dwLocalPlayerPawn)
        for i in range(1,65):
            le=pm.read_longlong(entity_list+0x8*((i&0x7FFF)>>9)+0x10)
            if not le: continue
            ec=pm.read_longlong(le+0x70*(i&0x1FF))
            if not ec: continue
            ph=pm.read_uint(ec+m_hPlayerPawn)
            if ph==0xFFFFFFFF: continue
            le2=pm.read_longlong(entity_list+0x8*((ph&0x7FFF)>>9)+0x10)
            if not le2: continue
            ep=pm.read_longlong(le2+0x70*(ph&0x1FF))
            if ep==local_player: return i-1
        return 0
    except: return 0

def is_player_visible(local_player, entity_pawn, entity_pos):
    """
    Gerçekçi visibility check:
    1. m_bSpottedByMask — CS2'nin kendi raycast sonucu (en güvenilir)
    2. Fallback: m_entitySpottedState doğrudan
    """
    try:
        local_index = get_local_index()
        # m_bSpottedByMask: her bit bir oyuncunun görüp görmediğini temsil eder
        spotted_mask = pm.read_longlong(entity_pawn + m_bSpottedByMask)
        if (spotted_mask & (1 << local_index)) != 0:
            return True
        # Fallback: 32-bit mask
        spotted_mask32 = pm.read_uint(entity_pawn + m_bSpottedByMask)
        if (spotted_mask32 & (1 << (local_index % 32))) != 0:
            return True
        return False
    except: return False

# ══════════════════════════════════════════════════════════
# HITSOUND
# ══════════════════════════════════════════════════════════

def _build_hitsound():
    wav_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"hitsound_money_claim.wav")
    if not os.path.exists(wav_path):
        try:
            r=requests.get("https://github.com/Kittywy/Neverlose.cc-hitsounds/raw/main/wav/money%20claim.wav",timeout=5)
            if r.status_code==200:
                with open(wav_path,'wb') as f: f.write(r.content)
        except: pass
    if os.path.exists(wav_path):
        try:
            if not pygame.mixer.get_init(): pygame.mixer.init(frequency=44100,size=-16,channels=2,buffer=512)
            snd=pygame.mixer.Sound(wav_path); snd.set_volume(0.85); return snd
        except: pass
    # ★ FIX: Güvenilir fallback beep (numpy'sız)
    try:
        import numpy as np
        sr=44100; n=int(sr*0.06); t=np.linspace(0,0.06,n,endpoint=False)
        w=((np.sin(2*np.pi*1000*t)*0.45+np.sin(2*np.pi*1600*t)*0.25)*32767).astype(np.int16)
        fade=np.linspace(1.0,0.0,int(n*0.40)); w[-len(fade):]=(w[-len(fade):]*fade).astype(np.int16)
        stereo=np.column_stack([w,w]); return pygame.sndarray.make_sound(stereo)
    except: return None

def play_hitsound():
    global _hitsound_obj, _hitsound_last
    if not hitsound_enabled: return
    try:
        now = time.time()
        if now - _hitsound_last < 0.08: return   # 80ms cooldown — spam yok
        _hitsound_last = now
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        if _hitsound_obj is None: _hitsound_obj = _build_hitsound()
        if _hitsound_obj: _hitsound_obj.stop(); _hitsound_obj.play()
    except: pass

def hitsound_init():
    global _hitsound_obj
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.pre_init(frequency=44100,size=-16,channels=2,buffer=512)
            pygame.mixer.init(frequency=44100,size=-16,channels=2,buffer=512)
        _hitsound_obj=_build_hitsound(); print("✅ Hitsound yuklendi!")
    except Exception as e: print(f"Hitsound init hatasi: {e}")

# ══════════════════════════════════════════════════════════
# LIGHTNING EFFECT
# ══════════════════════════════════════════════════════════

def _gen_zigzag_pts(sx,sy,ex,ey,segments,offset_str,rng):
    pts=[(sx,sy)]; drift=0.0
    for i in range(1,segments):
        t=i/segments; bx=sx+(ex-sx)*t; by=sy+(ey-sy)*t
        drift+=rng.uniform(-offset_str,offset_str); drift*=0.55
        pts.append((int(bx+drift),int(by)))
    pts.append((ex,ey)); return pts

def draw_lightning_bolt(screen, head_pos, feet_pos, alpha, age=0.0):
    if alpha <= 0: return
    try:
        cr, cg, cb = lightning_color; gr, gg, gb = lightning_glow_color
        # ★ FIX: inceltilebilir kalınlık — slider 0.1'e kadar iner
        thick_mul = max(0.1, lightning_thickness)
        glow_t  = max(1, int(lightning_glow_thickness * thick_mul))
        mid_t   = max(1, int((lightning_glow_thickness * 0.35) * thick_mul))
        core_t  = max(1, int(lightning_core_thickness * thick_mul))
        hx = int(head_pos[0]); hy = int(head_pos[1])
        fx = int(feet_pos[0]); fy = int(feet_pos[1])
        # ★ FIX: Yıldırım mapin EN ÜSTÜNDEN gelsin — top_y her zaman ekranın çok üstü
        top_y = -80   # Ekranın üstünden 80px yukarıdan başla (çok büyük görünür)
        # Yıldırım vuruş noktası = oyuncunun baş/orta noktası
        land_y = hy  # Kafaya iner
        land_x = hx + random.randint(-8, 8)
        span = abs(land_y - top_y)
        if span < 20: return
        vis = alpha ** 0.33
        seed = (hx * 53 + int(age * 90)) & 0xFFFF
        rng = random.Random(seed)
        # ★ FIX: Çizgi hep ekranın en üstünden (top_y=-80) oyuncuya (land_x, land_y) iner
        pts = _gen_zigzag_pts(hx, top_y, land_x, land_y, lightning_segments, lightning_offset, rng)
        step_y = (land_y - top_y) / max(lightning_segments, 1)
        surf = _surf_lightning if _surf_lightning is not None else pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        _clear_surf(surf)
        a1 = int(vis * 22)
        if a1 > 0:
            for i in range(len(pts)-1): pygame.draw.line(surf, (gr, gg, gb, a1), pts[i], pts[i+1], glow_t + 4)
        a2 = int(vis * 55)
        if a2 > 0:
            c2 = (min(255, gr+30), min(255, gg+30), min(255, gb+30), a2)
            for i in range(len(pts)-1): pygame.draw.line(surf, c2, pts[i], pts[i+1], mid_t)
        a3 = int(vis * 120)
        if a3 > 0:
            c3 = (min(255, cr//2+gr//2), min(255, cg//2+gg//2), min(255, cb//2+gb//2), a3)
            for i in range(len(pts)-1): pygame.draw.line(surf, c3, pts[i], pts[i+1], core_t + 1)
        a4 = int(vis * 220)
        if a4 > 0:
            c4 = (min(255, cr+40), min(255, cg+40), min(255, cb+40), a4)
            for i in range(len(pts)-1): pygame.draw.line(surf, c4, pts[i], pts[i+1], core_t)
        if alpha > 0.55:
            a5 = int((alpha - 0.55) / 0.45 * 255)
            for i in range(len(pts)-1): pygame.draw.line(surf, (255, 255, 255, a5), pts[i], pts[i+1], 1)
        # Dal yıldırımlar
        b_rng = random.Random(seed + 999)
        for b in range(3):
            b_idx = b_rng.randint(max(1, lightning_segments//5), max(2, lightning_segments*2//3))
            if b_idx >= len(pts): continue
            bstart = pts[b_idx]; bdir = b_rng.choice([-1, 1]); b_pts = [bstart]; b_off = 0.0
            for _ in range(b_rng.randint(4, 8)):
                b_off += b_rng.uniform(7, 18) * bdir; bdir *= b_rng.uniform(0.65, 1.05)
                b_pts.append((bstart[0] + int(b_off), int(b_pts[-1][1] + step_y * 0.80)))
            ab_g = int(vis*18); ab_m = int(vis*50); ab_c = int(vis*140)
            if ab_g > 0:
                for i in range(len(b_pts)-1): pygame.draw.line(surf, (gr, gg, gb, ab_g), b_pts[i], b_pts[i+1], max(1, mid_t-1))
            if ab_m > 0:
                for i in range(len(b_pts)-1): pygame.draw.line(surf, (min(255,gr+20), min(255,gg+20), min(255,gb+20), ab_m), b_pts[i], b_pts[i+1], 1)
            if ab_c > 0:
                for i in range(len(b_pts)-1): pygame.draw.line(surf, (255, 255, 255, ab_c), b_pts[i], b_pts[i+1], 1)
        # Kıvılcımlar — vuruş noktasından
        if alpha > 0.40:
            s_rng = random.Random(seed + 12345); s_alpha = int((alpha - 0.40) / 0.60 * 255)
            for _ in range(lightning_spark_count):
                sx_o = s_rng.randint(-22, 22); sy_o = s_rng.randint(-14, 6)
                sx2 = land_x + sx_o + s_rng.randint(-8, 8); sy2 = land_y + sy_o + s_rng.randint(-4, 12)
                sa = max(0, s_alpha - s_rng.randint(0, 80))
                pygame.draw.line(surf, (min(255,cr+80), min(255,cg+80), min(255,cb+80), sa), (land_x+sx_o//2, land_y+sy_o//2), (sx2, sy2), 1)
                if s_rng.random() < 0.4: pygame.draw.circle(surf, (255, 255, 255, max(0, s_alpha-60)), (sx2, sy2), 1)
        # Vuruş parlaması
        if alpha > 0.80:
            fl_a = int((alpha - 0.80) / 0.20 * 180); fl_r = int(18 * (alpha - 0.80) / 0.20)
            if fl_r > 0 and fl_a > 0: pygame.draw.circle(surf, (255, 255, 255, fl_a), (land_x, land_y), fl_r)
        screen.blit(surf, (0, 0))
    except Exception: pass

def draw_all_lightning(screen,view_matrix):
    if not lightning_effect_enabled: return
    global lightning_deaths
    now=time.time(); FLASH_DUR=max(0.15,min(3.0,lightning_duration*0.5))
    dead=[k for k,v in lightning_deaths.items() if now-v["time"]>FLASH_DUR]
    for k in dead: del lightning_deaths[k]
    for addr,data in list(lightning_deaths.items()):
        age=now-data["time"]
        if age>=FLASH_DUR: continue
        alpha=1.0-(age/FLASH_DUR)
        try:
            h3=data.get("head_3d"); f3=data.get("feet_3d")
            if h3 and f3:
                # ★ FIX: head_pos (kafanın ekran koordinatı) — yıldırım buraya iner
                hp=w2s(view_matrix,h3[0],h3[1],h3[2]+8,WINDOW_WIDTH,WINDOW_HEIGHT)
                # fp sadece fallback olarak kullanılır (artık top_y=-80 kullanıyoruz)
                fp=w2s(view_matrix,f3[0],f3[1],f3[2]-10,WINDOW_WIDTH,WINDOW_HEIGHT)
                if not hp:
                    # Ekran dışıysa bile kısmen görünür olsun
                    raw=_w2s_noclip(view_matrix,h3[0],h3[1],h3[2]+8,WINDOW_WIDTH,WINDOW_HEIGHT)
                    if raw: hp=[max(-200,min(WINDOW_WIDTH+200,int(raw[0]))),max(0,min(WINDOW_HEIGHT,int(raw[1])))]
                if hp:
                    if not fp: fp=[hp[0]+10, hp[1]+200]  # fallback feet pos
                    draw_lightning_bolt(screen,hp,fp,alpha,age)
        except: pass

def spawn_death_particles(origin_3d):
    if not death_particles_enabled: return
    ox,oy,oz=origin_3d; particles=[]; count=80
    spd=max(0.1,death_particle_speed); lt=max(0.1,death_particle_lifetime)
    for _ in range(count):
        yaw=random.uniform(0,math.pi*2); pitch=random.uniform(-math.pi*0.6,math.pi*0.5)
        speed=random.uniform(20,120)*spd
        vx=math.cos(pitch)*math.cos(yaw)*speed; vy=math.cos(pitch)*math.sin(yaw)*speed
        vz=abs(math.sin(pitch))*speed*random.uniform(0.5,2.0)
        life=random.uniform(0.3,0.9)*lt; size=random.choice([1,1,1,2])
        particles.append({'x':float(ox),'y':float(oy),'z':float(oz),'px':float(ox),'py':float(oy),'pz':float(oz),
                          'vx':vx,'vy':vy,'vz':vz,'life':life,'max_life':life,'size':size})
    _death_particle_systems.append({'particles':particles,'born':time.time()})

def draw_death_particles(screen,view_matrix):
    if not death_particles_enabled or not _death_particle_systems: return
    dt=1.0/120.0; r0,g0,b0=death_particle_color; to_remove=[]
    for sys_idx,sys in enumerate(_death_particle_systems):
        alive=[]
        for p in sys['particles']:
            p['px'],p['py'],p['pz']=p['x'],p['y'],p['z']; p['life']-=dt
            if p['life']<=0: continue
            p['x']+=p['vx']*dt; p['y']+=p['vy']*dt; p['z']+=p['vz']*dt
            p['vz']-=280*dt; p['vx']*=0.985; p['vy']*=0.985
            alpha=p['life']/p['max_life']
            cur=w2s(view_matrix,p['x'],p['y'],p['z'],WINDOW_WIDTH,WINDOW_HEIGHT)
            prev=w2s(view_matrix,p['px'],p['py'],p['pz'],WINDOW_WIDTH,WINDOW_HEIGHT)
            if cur and prev:
                cr=int(r0*alpha); cg=int(g0*alpha); cb=int(b0*alpha)
                pygame.draw.line(screen,(cr,cg,cb),(int(prev[0]),int(prev[1])),(int(cur[0]),int(cur[1])),1)
                if alpha>0.5: pygame.draw.circle(screen,(min(255,cr+120),min(255,cg+120),min(255,cb+160)),(int(cur[0]),int(cur[1])),1)
            elif cur:
                pygame.draw.circle(screen,(int(r0*alpha),int(g0*alpha),int(b0*alpha)),(int(cur[0]),int(cur[1])),1)
            alive.append(p)
        if not alive: to_remove.append(sys_idx)
        else: sys['particles']=alive
    for idx in reversed(to_remove): _death_particle_systems.pop(idx)

def draw_spectator_list(screen,font):
    if not spectator_list_enabled: return
    SAFE_MIN=0x10000; SAFE_MAX=0x7FFFFFFFFFFF

    # ★ GUI açıkken FAKE spectator listesi göster (drag için)
    if _gui_is_open:
        fake_spectators = [
            {'name': 'Spektatör1',  'weapon': 'AK47'},
            {'name': 'Spektatör2',  'weapon': 'AWP'},
            {'name': 'ghost_user',  'weapon': 'KNIFE'},
        ]
        _draw_spec_panel(screen, fake_spectators)
        return

    try:
        entity_list=pm.read_longlong(client+dwEntityList)
        local_player=pm.read_longlong(client+dwLocalPlayerPawn)
        local_ctrl=pm.read_longlong(client+dwLocalPlayerController) if dwLocalPlayerController else 0
        if not entity_list or not local_player: return
        if not (SAFE_MIN<entity_list<SAFE_MAX): return
        spectators=[]
        for idx in range(1,65):
            try:
                chunk=(idx&0x7FFF)>>9; slot=idx&0x1FF
                le=pm.read_longlong(entity_list+0x8*chunk+0x10)
                if not le or not (SAFE_MIN<le<SAFE_MAX): continue
                ctrl=pm.read_longlong(le+0x70*slot)
                if not ctrl or not (SAFE_MIN<ctrl<SAFE_MAX): continue
                if local_ctrl and ctrl==local_ctrl: continue
                # ★ FIX: Pawn handle üzerinden pawn'a git
                pawn_h=pm.read_uint(ctrl+m_hPlayerPawn)
                if not pawn_h or pawn_h==0xFFFFFFFF: continue
                le2=pm.read_longlong(entity_list+0x8*((pawn_h&0x7FFF)>>9)+0x10)
                if not le2 or not (SAFE_MIN<le2<SAFE_MAX): continue
                pawn_addr=pm.read_longlong(le2+0x70*(pawn_h&0x1FF))
                if not pawn_addr or not (SAFE_MIN<pawn_addr<SAFE_MAX): continue
                if pawn_addr==local_player: continue

                # ★ FIX: Güncel CS2 observer offsets — SadraKhorami yaklaşımı
                # m_pObserverServices → m_hObserverTarget → resolve handle
                is_watching_us = False
                for obs_off in [m_pObserverServices_off, 0x10C0, 0x10D8, 0x10B8, 0x10E0]:
                    try:
                        obs_svc=pm.read_longlong(pawn_addr+obs_off)
                        if not obs_svc or not (SAFE_MIN<obs_svc<SAFE_MAX): continue
                        # m_hObserverTarget — CS2 güncel offsetler
                        for hobs_off in [m_hObserverTarget_off, 0x10, 0x14, 0x18, 0x44, 0x48]:
                            try:
                                obs_h=pm.read_uint(obs_svc+hobs_off)
                                if not obs_h or obs_h==0xFFFFFFFF: continue
                                obs_idx = obs_h & 0x7FFF
                                if obs_idx < 1 or obs_idx > 2047: continue
                                t_le=pm.read_longlong(entity_list+0x8*(obs_idx>>9)+0x10)
                                if not t_le or not (SAFE_MIN<t_le<SAFE_MAX): continue
                                t_ent=pm.read_longlong(t_le+0x70*(obs_idx&0x1FF))
                                if not t_ent: continue
                                # Direkt pawn karşılaştır
                                if t_ent==local_player:
                                    is_watching_us=True; break
                                # Controller üzerinden pawn kontrolü
                                try:
                                    t_ph=pm.read_uint(t_ent+m_hPlayerPawn)
                                    if t_ph and t_ph!=0xFFFFFFFF:
                                        t_le2=pm.read_longlong(entity_list+0x8*((t_ph&0x7FFF)>>9)+0x10)
                                        if t_le2 and (SAFE_MIN<t_le2<SAFE_MAX):
                                            t_p2=pm.read_longlong(t_le2+0x70*(t_ph&0x1FF))
                                            if t_p2==local_player:
                                                is_watching_us=True; break
                                except: pass
                            except: continue
                        if is_watching_us: break
                    except: continue

                if not is_watching_us: continue
                try:
                    name=pm.read_string(ctrl+m_iszPlayerName,32)
                    name=name.strip() if name else f"Player{idx}"
                except: name=f"Player{idx}"
                wep_name=""
                if spectator_show_weapon:
                    try: wep_name=_read_weapon_name_for_pawn(pawn_addr)
                    except: pass
                spectators.append({'name':name,'weapon':wep_name})
            except: continue
        if spectators:
            _draw_spec_panel(screen, spectators)
    except: pass

def _draw_spec_panel(screen, spectators):
    """Spectator panelini çiz — hem fake hem gerçek verilerle kullanılır."""
    try:
        row_h=20; pad=8; bg_w=240
        bg_h=pad+22+len(spectators)*row_h+pad
        if _drag_spec_pos is None: bg_x=WINDOW_WIDTH-bg_w-12; bg_y=12
        else: bg_x,bg_y=_drag_spec_pos
        bg_s=pygame.Surface((bg_w,bg_h),pygame.SRCALPHA)
        pygame.draw.rect(bg_s,(10,8,28,200),(0,0,bg_w,bg_h),border_radius=4)
        screen.blit(bg_s,(bg_x,bg_y))
        border_col=(255,200,0) if _gui_is_open else (180,70,255)
        border_thick=2 if _gui_is_open else 1
        pygame.draw.rect(screen,border_col,(bg_x,bg_y,bg_w,bg_h),border_thick,border_radius=4)
        hf=_font_spec_hdr if _font_spec_hdr else pygame.font.SysFont("Arial",12,bold=True)
        hdr_txt=f"👁 SPECTATORS ({len(spectators)})"
        if _gui_is_open: hdr_txt += "  ✥ DRAG"
        hdr=hf.render(hdr_txt,True,(210,100,255) if not _gui_is_open else (255,200,0))
        screen.blit(hdr,(bg_x+pad,bg_y+pad))
        for n,sp in enumerate(spectators):
            row_y=bg_y+pad+22+n*row_h
            nf=_font_spec_name if _font_spec_name else pygame.font.SysFont("Arial",11,bold=True)
            ns=nf.render(sp['name'],True,(235,185,255))
            screen.blit(ns,(bg_x+pad+4,row_y))
            if spectator_show_weapon and sp.get('weapon'):
                wf=_font_spec_wep if _font_spec_wep else pygame.font.SysFont("Arial",10)
                ws=wf.render(f"[{sp['weapon']}]",True,(255,200,80))
                screen.blit(ws,(bg_x+pad+4+ns.get_width()+6,row_y+2))
    except: pass

# ══════════════════════════════════════════════════════════
# ★ HUMANIZE — smooth & max_angle birlikte, LINKED
# ══════════════════════════════════════════════════════════

def humanize_tick():
    """
    Smooth ve MaxAngle aynı yönde değişir (biri artıyorsa diğeri de artar).
    Her tick rastgele bir factor üretilir, her iki değer aynı factor ile çarpılır.
    """
    global _hum_smooth_cur, _hum_max_angle_cur, _hum_fov_cur, _hum_last_tick, _hum_direction
    if not humanize_enabled:
        _hum_smooth_cur    = aimbot_smooth
        _hum_max_angle_cur = aimbot_max_angle
        return
    now = time.time()
    if now - _hum_last_tick < random.uniform(0.25, 0.9): return
    _hum_last_tick = now

    # Linked factor: aynı yönde %85-115 arası
    factor = random.uniform(0.85, 1.15)
    _hum_smooth_cur    = round(max(1.0,  min(20.0,  aimbot_smooth    * factor)), 2)
    _hum_max_angle_cur = round(max(2.0,  min(180.0, aimbot_max_angle * factor)), 2)


# ══════════════════════════════════════════════════════════
# ESP MAIN LOOP
# ══════════════════════════════════════════════════════════

entities_found = 0; entities_drawn = 0; crosshair_entity = None
_hs_shots_prev = 0
# Hitsound için: {pawn_addr: hp} — sadece düşmanlar
_hs_enemy_hp   = {}

def esp(screen, font):
    global entities_found, entities_drawn, crosshair_entity
    global _hs_shots_prev, _local_last_shot_time, _shot_consumed, _hs_enemy_hp
    entities_found = 0; entities_drawn = 0; crosshair_entity = None
    try:
        view_matrix   = [pm.read_float(client+dwViewMatrix+i*4) for i in range(16)]
        local_player  = pm.read_longlong(client+dwLocalPlayerPawn)
        if not local_player: return
        local_team    = pm.read_int(local_player+m_iTeamNum)

        # ── ShotsFired takibi ──────────────────────────────────────────
        try:
            shots_cur = pm.read_int(local_player + m_iShotsFired)
            now_t = time.time()
            if shots_cur != _hs_shots_prev and shots_cur > 0:
                _local_last_shot_time = now_t
                _hs_shots_prev = shots_cur
                _shot_consumed = False
        except: pass
        try:
            crosshair_id = pm.read_int(local_player+m_iIDEntIndex)
            if crosshair_id > 0: crosshair_entity = crosshair_id
        except: pass
        try:
            local_x=pm.read_float(local_player+m_vecOrigin); local_y=pm.read_float(local_player+m_vecOrigin+4)
            local_z=pm.read_float(local_player+m_vecOrigin+8); local_pos=(local_x,local_y,local_z)
        except: local_pos=(0,0,0)
        entity_list = pm.read_longlong(client+dwEntityList)
        if not entity_list: return
        entity_data_list = []
        for i in range(1,65):
            try:
                le=pm.read_longlong(entity_list+0x8*((i&0x7FFF)>>9)+0x10)
                if not le: continue
                ec=pm.read_longlong(le+0x70*(i&0x1FF))
                if not ec: continue
                ph=pm.read_uint(ec+m_hPlayerPawn)
                if ph==0xFFFFFFFF or not ph: continue
                le2=pm.read_longlong(entity_list+0x8*((ph&0x7FFF)>>9)+0x10)
                if not le2: continue
                ep=pm.read_longlong(le2+0x70*(ph&0x1FF))
                if not ep or ep==local_player: continue
                entities_found += 1
                life_state = pm.read_int(ep+m_lifeState)
                if life_state != 256:
                    if ep in _entity_hp_prev and _entity_hp_prev[ep]>0:
                        entity_team2=pm.read_int(ep+m_iTeamNum)
                        if entity_team2!=local_team:
                            # ★ FIX: Kill hitsound — life_state dalı (ölüm anında yakalandı)
                            if (time.time()-_local_last_shot_time)<_SHOT_WINDOW:
                                _shot_consumed = False
                                play_hitsound()
                                _shot_consumed = True
                            cached_pos = _entity_last_known_pos.get(ep)
                            if cached_pos:
                                hb2, fb2 = cached_pos
                                lightning_deaths[ep]={'time':time.time(),'head_3d':hb2,'feet_3d':fb2,'head':(0,0),'feet':(0,0)}
                                spawn_death_particles((hb2[0],hb2[1],(hb2[2]+fb2[2])/2))
                            else:
                                try:
                                    gs2=pm.read_longlong(ep+m_pGameSceneNode)
                                    bm2=pm.read_longlong(gs2+m_modelState+0x80) if gs2 else None
                                    hb2=get_bone_position(bm2,6) if bm2 else None
                                    fb2=get_bone_position(bm2,0) if bm2 else None
                                    if hb2 and fb2:
                                        lightning_deaths[ep]={'time':time.time(),'head_3d':hb2,'feet_3d':fb2,'head':(0,0),'feet':(0,0)}
                                        spawn_death_particles((hb2[0],hb2[1],(hb2[2]+fb2[2])/2))
                                except: pass
                        _entity_hp_prev.pop(ep,None)
                        _entity_last_known_pos.pop(ep,None)
                    continue
                entity_hp = pm.read_int(ep+m_iHealth)
                if entity_hp <= 0: continue

                # ★ Weapon name — direkt pawn üzerinden oku (en güvenilir yol)
                weapon_name_str = ""
                if esp_weapon_name:
                    try:
                        weapon_name_str = _read_weapon_name_for_pawn(ep)
                    except: weapon_name_str = ""

                entity_team   = pm.read_int(ep+m_iTeamNum); is_teammate=(entity_team==local_team)
                if is_teammate and not esp_teammates: continue
                try:
                    ex=pm.read_float(ep+m_vecOrigin); ey=pm.read_float(ep+m_vecOrigin+4)
                    ez=pm.read_float(ep+m_vecOrigin+8); entity_pos=(ex,ey,ez)
                except: continue
                dist        = distance_3d(local_pos[0],local_pos[1],local_pos[2],entity_pos[0],entity_pos[1],entity_pos[2])
                is_visible  = is_player_visible(local_player,ep,entity_pos)
                gs          = pm.read_longlong(ep+m_pGameSceneNode)
                if not gs: continue
                bone_matrix = pm.read_longlong(gs+m_modelState+0x80)
                if not bone_matrix: continue
                head_bone   = get_bone_position(bone_matrix,6); feet_bone=get_bone_position(bone_matrix,0)
                if not head_bone or not feet_bone: continue
                head_pos    = w2s(view_matrix,head_bone[0],head_bone[1],head_bone[2]+8,WINDOW_WIDTH,WINDOW_HEIGHT)
                feet_pos    = w2s(view_matrix,feet_bone[0],feet_bone[1],feet_bone[2]-10,WINDOW_WIDTH,WINDOW_HEIGHT)
                # ★ FIX: noclip fallback for high FOV (clamp to screen edges)
                if not head_pos:
                    raw = _w2s_noclip(view_matrix,head_bone[0],head_bone[1],head_bone[2]+8,WINDOW_WIDTH,WINDOW_HEIGHT)
                    if raw: head_pos = [max(0,min(WINDOW_WIDTH,int(raw[0]))), max(0,min(WINDOW_HEIGHT,int(raw[1])))]
                if not feet_pos:
                    raw = _w2s_noclip(view_matrix,feet_bone[0],feet_bone[1],feet_bone[2]-10,WINDOW_WIDTH,WINDOW_HEIGHT)
                    if raw: feet_pos = [max(0,min(WINDOW_WIDTH,int(raw[0]))), max(0,min(WINDOW_HEIGHT,int(raw[1])))]
                if not head_pos or not feet_pos: continue
                height = abs(head_pos[1]-feet_pos[1])
                if height<10 or height>800: continue
                entity_data = {
                    'entity_controller':ec,'entity_pawn':ep,'entity_hp':entity_hp,
                    'is_visible':is_visible,'head_pos':head_pos,'feet_pos':feet_pos,
                    'dist':dist,'bone_matrix':bone_matrix,'is_teammate':is_teammate,
                    'weapon_name':weapon_name_str,'head_bone':head_bone,'feet_bone':feet_bone
                }
                entity_data_list.append(entity_data); entities_drawn += 1
                # ★ FIX: Cache last known bone positions for death effect fallback
                _entity_last_known_pos[ep] = (head_bone, feet_bone)
                try:
                    if ep not in _entity_hp_prev: _entity_hp_prev[ep]=entity_hp
                    else:
                        prev_hp=_entity_hp_prev[ep]
                        # ── Hitsound: SADECE düşman, SADECE local player attıysa ──
                        if not is_teammate:
                            now_hs = time.time()
                            shot_window = (now_hs - _local_last_shot_time) < 0.12
                            if entity_hp < prev_hp and shot_window and not _shot_consumed:
                                play_hitsound()
                                _shot_consumed = True
                            if prev_hp > 0 and entity_hp <= 0 and shot_window:
                                # Öldürme sesi — ayrı çal
                                _shot_consumed = False
                                play_hitsound()
                                _shot_consumed = True
                                lightning_deaths[ep]={'time':time.time(),'head_3d':head_bone,'feet_3d':feet_bone,'head':head_pos,'feet':feet_pos}
                                spawn_death_particles((head_bone[0],head_bone[1],(head_bone[2]+feet_bone[2])/2))
                        _entity_hp_prev[ep]=entity_hp
                except: pass
            except: continue

        if esp_chams:
            for data in entity_data_list: draw_full_body_chams(screen,data['bone_matrix'],view_matrix,data['is_visible'])
        for data in entity_data_list:
            draw_color = visible_color if data['is_visible'] else hidden_color if esp_chams else skeleton_color
            skeleton_drawn = True  # ★ FIX: skeleton kapalıysa diğer ESP'leri engelleme
            if esp_skeleton:
                thickness=skeleton_thickness if not esp_chams else max(skeleton_thickness,4)
                radius=max(2,skeleton_thickness)
                skeleton_drawn,bones_2d=draw_skeleton(screen,data['bone_matrix'],view_matrix,draw_color,thickness,radius)
                if not skeleton_drawn: continue
            else:
                bones_2d = {}
            if esp_head:
                head_r = max(3, min(15, int(abs(data['head_pos'][1]-data['feet_pos'][1])/8)))
                pygame.draw.circle(screen,draw_color,data['head_pos'],head_r,2)
            if esp_box: draw_box(screen,data['head_pos'],data['feet_pos'],data['dist'],draw_color,2,bones_2d if bones_2d else None)
            if esp_healthbar:
                hp_percent=min(data['entity_hp']/100.0,1.0)
                bar_x=data['head_pos'][0]-35; bar_width=5
                draw_hp_bar(screen,bar_x,data['head_pos'][1],bar_width,int(abs(data['head_pos'][1]-data['feet_pos'][1])),hp_percent,draw_color)
                hp_text=font.render(str(data['entity_hp']),True,(255,255,255))
                screen.blit(hp_text,(bar_x-25,data['head_pos'][1]-5))
            if esp_names:
                try:
                    player_name=pm.read_string(data['entity_controller']+m_iszPlayerName,32)
                    name_text=font.render(player_name,True,(255,255,0))
                    screen.blit(name_text,(data['head_pos'][0]-name_text.get_width()//2,data['head_pos'][1]-20))
                except: pass
            if esp_weapon_name and data.get('weapon_name'):
                draw_weapon_esp_below_player(screen,data['feet_pos'],data['weapon_name'],font)
    except: pass
    try:
        draw_all_lightning(screen,view_matrix)
        draw_death_particles(screen,view_matrix)
    except: pass
    draw_spectator_list(screen,font)


# ══════════════════════════════════════════════════════════
# TRIGGERBOT
# ══════════════════════════════════════════════════════════

def triggerbot_worker():
    print("🎯 Triggerbot başlatıldı!")
    user32=ctypes.windll.user32; last_shot_time=0.0; target_since=0.0; had_target_prev=False
    def _get_trigger_bones():
        bones=[]
        if triggerbot_hitbox_head: bones.extend([6])
        if triggerbot_hitbox_body: bones.extend([5,4,3,2,1,0,8,9,13,14])
        if triggerbot_hitbox_legs: bones.extend([22,23,25,26])
        return bones if bones else [6,5,4,3,2,1,0,8,9,13,14,22,23,25,26]
    def _key_held():
        key=triggerbot_hold_key if triggerbot_hold_key else keybinds.get('triggerbot','')
        if not key: return True
        try:
            if key=='xbutton1': return bool(user32.GetAsyncKeyState(0x05)&0x8000)
            elif key=='xbutton2': return bool(user32.GetAsyncKeyState(0x06)&0x8000)
            else: return bool(keyboard.is_pressed(key))
        except: return True
    while True:
        time.sleep(0.0005)
        if not triggerbot_enabled: last_shot_time=0.0; had_target_prev=False; continue
        if triggerbot_hold_mode:
            if not _key_held(): had_target_prev=False; continue
        try:
            view_matrix=[pm.read_float(client+dwViewMatrix+k*4) for k in range(16)]
            local_player=pm.read_longlong(client+dwLocalPlayerPawn)
            if not local_player: continue
            local_team=pm.read_int(local_player+m_iTeamNum)
            entity_list=pm.read_longlong(client+dwEntityList)
            if not entity_list: continue
            cx=WINDOW_WIDTH/2.0; cy=WINDOW_HEIGHT/2.0; trig_px=6.0
            best_dist=float('inf'); best_enemy=None
            for i in range(1,65):
                try:
                    le=pm.read_longlong(entity_list+0x8*((i&0x7FFF)>>9)+0x10)
                    if not le: continue
                    ec=pm.read_longlong(le+0x70*(i&0x1FF))
                    if not ec: continue
                    ph=pm.read_uint(ec+m_hPlayerPawn)
                    if ph==0xFFFFFFFF: continue
                    le2=pm.read_longlong(entity_list+0x8*((ph&0x7FFF)>>9)+0x10)
                    if not le2: continue
                    ep=pm.read_longlong(le2+0x70*(ph&0x1FF))
                    if not ep or ep==local_player: continue
                    ent_team=pm.read_int(ep+m_iTeamNum); is_teammate=(ent_team==local_team)
                    if is_teammate and not triggerbot_shoot_teammates: continue
                    if pm.read_int(ep+m_lifeState)!=256: continue
                    if pm.read_int(ep+m_iHealth)<=0: continue
                    gs=pm.read_longlong(ep+m_pGameSceneNode)
                    if not gs: continue
                    bm=pm.read_longlong(gs+m_modelState+0x80)
                    if not bm: continue
                    hit=False
                    for bone_idx in _get_trigger_bones():
                        tp=get_bone_position(bm,bone_idx)
                        if not tp: continue
                        sp=w2s(view_matrix,tp[0],tp[1],tp[2],WINDOW_WIDTH,WINDOW_HEIGHT)
                        if not sp: continue
                        dist=math.hypot(sp[0]-cx,sp[1]-cy)
                        if dist<trig_px:
                            if not triggerbot_wallbang and not is_teammate:
                                ex2=pm.read_float(ep+m_vecOrigin); ey2=pm.read_float(ep+m_vecOrigin+4)
                                ez2=pm.read_float(ep+m_vecOrigin+8)
                                if not is_player_visible(local_player,ep,(ex2,ey2,ez2)): continue
                            if dist<best_dist: best_dist=dist; best_enemy=ep
                            hit=True; break
                    if hit: continue
                except: continue
            now=time.time()
            if best_enemy is not None:
                if not had_target_prev: target_since=now; had_target_prev=True
                if (now-target_since)<triggerbot_pre_delay: continue
                cooldown=0.03 if triggerbot_continuous else 0.06
                if now-last_shot_time>cooldown:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
                    time.sleep(max(0.0001,triggerbot_click_delay))
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
                    last_shot_time=now
                    if triggerbot_post_delay>0: time.sleep(triggerbot_post_delay)
            else: had_target_prev=False
        except: continue

# ══════════════════════════════════════════════════════════
# AIMBOT
# ══════════════════════════════════════════════════════════

def aimbot_loop():
    print("🎯 Aimbot thread başladı!")
    last_shot_time=0
    while True:
        humanize_tick()
        if aimbot_hold_mode:
            key=keybinds['aimbot']; is_pressed=False
            if key=='xbutton1': is_pressed=ctypes.windll.user32.GetAsyncKeyState(VK_XBUTTON1)&0x8000
            elif key=='xbutton2': is_pressed=ctypes.windll.user32.GetAsyncKeyState(VK_XBUTTON2)&0x8000
            else: is_pressed=keyboard.is_pressed(key)
            if not is_pressed: time.sleep(0.01); continue
        else:
            if not aimbot_enabled: time.sleep(0.01); continue
        try:
            view_matrix=[pm.read_float(client+dwViewMatrix+i*4) for i in range(16)]
            local_player=pm.read_longlong(client+dwLocalPlayerPawn)
            if not local_player: time.sleep(0.001); continue
            local_team=pm.read_int(local_player+m_iTeamNum)
            entity_list=pm.read_longlong(client+dwEntityList)
            if not entity_list: continue
            best_score=float('inf'); best_target=None
            mouse_x,mouse_y=win32api.GetCursorPos()
            fov_rad_px=(WINDOW_HEIGHT/2.0)*math.tan(math.radians(aimbot_fov/2.0))
            for i in range(1,65):
                try:
                    le=pm.read_longlong(entity_list+0x8*((i&0x7FFF)>>9)+0x10)
                    if not le: continue
                    ec=pm.read_longlong(le+0x70*(i&0x1FF))
                    if not ec: continue
                    ph=pm.read_uint(ec+m_hPlayerPawn)
                    if ph==0xFFFFFFFF: continue
                    le2=pm.read_longlong(entity_list+0x8*((ph&0x7FFF)>>9)+0x10)
                    if not le2: continue
                    ep=pm.read_longlong(le2+0x70*(ph&0x1FF))
                    if not ep or ep==local_player: continue
                    if pm.read_int(ep+m_lifeState)!=256: continue
                    if pm.read_int(ep+m_iHealth)<=0: continue
                    entity_team=pm.read_int(ep+m_iTeamNum); is_teammate=(entity_team==local_team)
                    if not esp_teammates and is_teammate: continue
                    ex=pm.read_float(ep+m_vecOrigin); ey=pm.read_float(ep+m_vecOrigin+4)
                    ez=pm.read_float(ep+m_vecOrigin+8); entity_pos=(ex,ey,ez)
                    gs=pm.read_longlong(ep+m_pGameSceneNode)
                    if not gs: continue
                    bm=pm.read_longlong(gs+m_modelState+0x80)
                    if not bm: continue
                    hitbox_bones=[]
                    if aimbot_hitbox_head: hitbox_bones.append(6)
                    if aimbot_hitbox_body: hitbox_bones.extend([5,4,3])
                    if aimbot_hitbox_legs: hitbox_bones.extend([22,23,25,26])
                    if not hitbox_bones: hitbox_bones=[aimbot_bone]
                    best_bone_pos=None; best_bone_dist=float('inf')
                    for bone_idx in hitbox_bones:
                        bp=get_bone_position(bm,bone_idx)
                        if not bp: continue
                        sp2=w2s(view_matrix,*bp,WINDOW_WIDTH,WINDOW_HEIGHT)
                        if not sp2: continue
                        bd=math.hypot(sp2[0]-mouse_x,sp2[1]-mouse_y)
                        if bd<best_bone_dist: best_bone_dist=bd; best_bone_pos=sp2
                    if best_bone_pos:
                        screen_pos=best_bone_pos; screen_dist_to_center=best_bone_dist
                    else:
                        tp=get_bone_position(bm,aimbot_bone)
                        if not tp: continue
                        screen_pos=w2s(view_matrix,*tp,WINDOW_WIDTH,WINDOW_HEIGHT)
                        if not screen_pos: continue
                        screen_dist_to_center=math.hypot(screen_pos[0]-mouse_x,screen_pos[1]-mouse_y)
                    if screen_dist_to_center>fov_rad_px: continue
                    is_visible=is_player_visible(local_player,ep,entity_pos)
                    if aimbot_only_visible and not is_visible and not aimbot_wallbang: continue
                    if screen_dist_to_center<best_score: best_score=screen_dist_to_center; best_target=(screen_pos[0],screen_pos[1])
                except: continue
            if best_target:
                target_x,target_y=best_target; dx=target_x-mouse_x; dy=target_y-mouse_y
                dist_angle=math.hypot(dx,dy)
                if dist_angle==0: continue
                _eff_ma=_hum_max_angle_cur if humanize_enabled else aimbot_max_angle
                move_angle=min(dist_angle,_eff_ma)
                _eff_sm=_hum_smooth_cur if humanize_enabled else aimbot_smooth
                move_x=int(dx*(move_angle/dist_angle)/_eff_sm)
                move_y=int(dy*(move_angle/dist_angle)/_eff_sm)
                if abs(move_x)>0 or abs(move_y)>0: win32api.mouse_event(win32con.MOUSEEVENTF_MOVE,move_x,move_y,0,0)
                if aimbot_auto_shoot and dist_angle<5:
                    current_time=time.time()
                    if current_time-last_shot_time>0.1:
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0,0,0)
                        time.sleep(0.05)
                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0,0,0)
                        last_shot_time=current_time
        except: pass
        time.sleep(0.0005)

# ══════════════════════════════════════════════════════════
# GUI — LabHub tarzı modern tasarım
# ══════════════════════════════════════════════════════════

LH_BG        = "#0d0e1a"
LH_PANEL     = "#13152a"
LH_ACCENT    = "#5b5fc7"
LH_ACCENT2   = "#7c7ff5"
LH_TEXT      = "#c8cce8"
LH_TEXT_DIM  = "#6b6f9e"
LH_GREEN     = "#3bba8c"
LH_RED       = "#e05555"
LH_ORANGE    = "#e8963c"
LH_YELLOW    = "#d4b84a"
LH_BORDER    = "#2a2d4a"

class ESPGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cesur")
        self.root.geometry("600x680")
        self.root.configure(bg=LH_BG)
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.withdraw()
        self.waiting_for_key = None; self.mouse_listener_active = False

        self.skeleton_var = tk.BooleanVar(value=esp_skeleton)
        self.box_var = tk.BooleanVar(value=esp_box)
        self.healthbar_var = tk.BooleanVar(value=esp_healthbar)
        self.chams_var = tk.BooleanVar(value=esp_chams)
        self.teammates_var = tk.BooleanVar(value=esp_teammates)
        self.names_var = tk.BooleanVar(value=esp_names)
        self.head_var = tk.BooleanVar(value=esp_head)
        self.weapon_name_var = tk.BooleanVar(value=esp_weapon_name)
        self.triggerbot_var = tk.BooleanVar(value=triggerbot_enabled)
        self.continuous_var = tk.BooleanVar(value=triggerbot_continuous)
        self.trig_wallbang_var = tk.BooleanVar(value=triggerbot_wallbang)
        self.aimbot_var = tk.BooleanVar(value=aimbot_enabled)
        self.aimbot_mode_var = tk.StringVar(value="hold" if aimbot_hold_mode else "toggle")
        self.visible_only_var = tk.BooleanVar(value=aimbot_only_visible)
        self.aimbot_wallbang_var = tk.BooleanVar(value=aimbot_wallbang)
        self.auto_shoot_var = tk.BooleanVar(value=aimbot_auto_shoot)
        self.bombtimer_var = tk.BooleanVar(value=bombtimer_enabled)
        self.fov_changer_var = tk.BooleanVar(value=fov_changer_enabled)
        self.player_trails_var = tk.BooleanVar(value=player_trails_enabled)
        self.lightning_var = tk.BooleanVar(value=lightning_effect_enabled)
        self.hitsound_var = tk.BooleanVar(value=hitsound_enabled)
        self.spectator_var = tk.BooleanVar(value=spectator_list_enabled)
        self.spectator_show_weapon_var = tk.BooleanVar(value=spectator_show_weapon)
        self.humanize_var = tk.BooleanVar(value=humanize_enabled)
        self.death_particles_var = tk.BooleanVar(value=death_particles_enabled)
        self.noflash_var = tk.BooleanVar(value=noflash_enabled)
        self.nosmoke_var = tk.BooleanVar(value=nosmoke_enabled)
        self.enemy_arrows_var = tk.BooleanVar(value=enemy_arrows_enabled)
        self.grenade_traj_var = tk.BooleanVar(value=grenade_trajectory_enabled)
        self.smoke_color_var = tk.BooleanVar(value=smoke_color_enabled)
        self.sky_color_var = tk.BooleanVar(value=sky_color_enabled)
        self.snow_var = tk.BooleanVar(value=snow_mode_enabled)
        self.fov_circle_var = tk.BooleanVar(value=aimbot_fov_circle_enabled)
        self.bhop_var = tk.BooleanVar(value=bhop_enabled)
        self.aim_hb_head_var = tk.BooleanVar(value=aimbot_hitbox_head)
        self.aim_hb_body_var = tk.BooleanVar(value=aimbot_hitbox_body)
        self.aim_hb_legs_var = tk.BooleanVar(value=aimbot_hitbox_legs)
        self.trig_hb_head_var = tk.BooleanVar(value=triggerbot_hitbox_head)
        self.trig_hb_body_var = tk.BooleanVar(value=triggerbot_hitbox_body)
        self.trig_hb_legs_var = tk.BooleanVar(value=triggerbot_hitbox_legs)
        self.hold_key_enabled_var = tk.BooleanVar(value=triggerbot_hold_mode)

        header = tk.Frame(self.root, bg=LH_PANEL, height=48)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text="⬡  Cesur", font=("Segoe UI",15,"bold"), bg=LH_PANEL, fg=LH_ACCENT2).pack(side="left",padx=16,pady=10)
        tk.Label(header, text="CS2 External v3.1", font=("Segoe UI",9), bg=LH_PANEL, fg=LH_TEXT_DIM).pack(side="left",pady=14)
        self.status_label = tk.Label(header, text="● ACTIVE", font=("Segoe UI",9,"bold"), bg=LH_PANEL, fg=LH_GREEN)
        self.status_label.pack(side="right", padx=16)
        tk.Frame(self.root, bg=LH_BORDER, height=1).pack(fill="x")

        body = tk.Frame(self.root, bg=LH_BG); body.pack(fill="both", expand=True)
        self.nav_frame = tk.Frame(body, bg=LH_PANEL, width=150)
        self.nav_frame.pack(side="left", fill="y"); self.nav_frame.pack_propagate(False)
        tk.Frame(self.nav_frame, bg=LH_BORDER, height=1).pack(fill="x", pady=(8,0))

        categories = [("👁  ESP","Visuals"),("🎯  Aimbot","Aimbot"),("⚡  Triggerbot","Triggerbot"),
                      ("🔑  Keybinds","Keybinds"),("💾  Config","Config"),("⚙️  Misc","Misc")]
        self.nav_btns = {}; self.current_category = "Visuals"
        for label, key in categories:
            btn = tk.Button(self.nav_frame, text=label, font=("Segoe UI",10),
                            bg=LH_PANEL, fg=LH_TEXT_DIM, bd=0, pady=10, padx=8,
                            activebackground=LH_ACCENT, activeforeground="#ffffff",
                            anchor="w", width=18,
                            command=lambda k=key: self.switch_category(k))
            btn.pack(fill="x", padx=4, pady=2)
            self.nav_btns[key] = btn
        tk.Frame(self.nav_frame, bg=LH_BORDER, height=1).pack(fill="x", pady=4)
        tk.Label(self.nav_frame, text="INSERT = Toggle GUI", font=("Segoe UI",7), bg=LH_PANEL, fg=LH_TEXT_DIM).pack(pady=4)

        content_frame = tk.Frame(body, bg=LH_BG); content_frame.pack(side="left", fill="both", expand=True)
        tk.Frame(body, bg=LH_BORDER, width=1).pack(side="left", fill="y")
        self.right_canvas = tk.Canvas(content_frame, bg=LH_BG, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.right_canvas.yview)
        self.right_frame = tk.Frame(self.right_canvas, bg=LH_BG)
        self.right_frame.bind("<Configure>", lambda e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all")))
        self.right_canvas.create_window((0,0), window=self.right_frame, anchor="nw")
        self.right_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.right_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.right_canvas.bind_all("<MouseWheel>", lambda e: self.right_canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        tk.Frame(self.root, bg=LH_BORDER, height=1).pack(fill="x")
        footer = tk.Frame(self.root, bg=LH_PANEL, height=28); footer.pack(fill="x"); footer.pack_propagate(False)
        tk.Label(footer, text="© 2025 Atapiro  |  For educational purposes only", font=("Segoe UI",8), bg=LH_PANEL, fg=LH_TEXT_DIM).pack(side="left",padx=12,pady=6)

        self.root.bind('<Key>', self.on_key_press)
        self.root.bind('<Button>', self.on_mouse_click)
        self.register_hotkeys()
        self.root.after(100, self.update_from_hotkeys)
        self.root.after(200, self._humanize_gui_tick)  # ★ Humanize live display
        self.switch_category("Visuals")
        self._highlight_nav("Visuals")

    # ─── Humanize GUI live display ───────────────────────────
    def _humanize_gui_tick(self):
        """Her 300ms'de humanize değerlerini GUI slider'larına yansıt"""
        try:
            if humanize_enabled and self.current_category == "Aimbot":
                if hasattr(self, 'smooth_scale') and hasattr(self, 'smooth_label'):
                    self.smooth_scale.set(_hum_smooth_cur)
                    self.smooth_label.config(text=f"{_hum_smooth_cur:.1f}")
                if hasattr(self, 'max_angle_scale') and hasattr(self, 'max_angle_label'):
                    self.max_angle_scale.set(_hum_max_angle_cur)
                    self.max_angle_label.config(text=f"{_hum_max_angle_cur:.1f}°")
        except: pass
        self.root.after(300, self._humanize_gui_tick)

    def _highlight_nav(self, active):
        for key, btn in self.nav_btns.items():
            if key == active: btn.config(bg=LH_ACCENT, fg="#ffffff", font=("Segoe UI",10,"bold"))
            else: btn.config(bg=LH_PANEL, fg=LH_TEXT_DIM, font=("Segoe UI",10))

    def switch_category(self, category):
        self.current_category = category; self._highlight_nav(category)
        for w in self.right_frame.winfo_children(): w.destroy()
        # ★ FIX: Reset scroll position so content is always visible
        self.right_canvas.yview_moveto(0)
        if   category == "Visuals":    self.setup_esp_tab()
        elif category == "Aimbot":     self.setup_aimbot_tab()
        elif category == "Triggerbot": self.setup_triggerbot_tab()
        elif category == "Keybinds":   self.setup_keybinds_tab()
        elif category == "Config":     self.setup_config_tab()
        elif category == "Misc":       self.setup_misc_tab()
        # Force geometry update so scrollregion recalculates
        self.right_frame.update_idletasks()
        self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))

    def _section(self, parent, title, color=None):
        c = color or LH_ACCENT2
        f = tk.Frame(parent, bg=LH_BG); f.pack(fill="x", pady=(14,4), padx=12)
        tk.Frame(f, bg=c, width=3, height=20).pack(side="left")
        tk.Label(f, text=f"  {title}", font=("Segoe UI",11,"bold"), bg=LH_BG, fg=c).pack(side="left")
        tk.Frame(parent, bg=LH_BORDER, height=1).pack(fill="x", padx=12, pady=(0,6))
        return f

    def _lh_check(self, parent, text, var, cmd, color=None):
        c = color or LH_TEXT
        f = tk.Frame(parent, bg=LH_BG); f.pack(fill="x", padx=16, pady=2)
        tk.Checkbutton(f, text=text, variable=var, command=cmd,
                       bg=LH_BG, fg=c, selectcolor=LH_PANEL,
                       activebackground=LH_BG, activeforeground=LH_ACCENT2,
                       font=("Segoe UI",10), bd=0, highlightthickness=0).pack(side="left")
        return f

    def _lh_slider(self, parent, label, from_, to_, init, cmd, unit="", color=None):
        c = color or LH_TEXT_DIM
        f = tk.Frame(parent, bg=LH_BG); f.pack(fill="x", padx=16, pady=(4,2))
        tk.Label(f, text=label, font=("Segoe UI",9), bg=LH_BG, fg=c, width=18, anchor="w").pack(side="left")
        lbl = tk.Label(f, text=f"{init}{unit}", font=("Segoe UI",9,"bold"), bg=LH_BG, fg=LH_ACCENT2, width=7)
        lbl.pack(side="right")
        scale = ttk.Scale(f, from_=from_, to=to_, orient="horizontal", length=200,
                          command=lambda v, l=lbl, u=unit, fn=cmd: [fn(v), l.config(text=f"{float(v):.1f}{u}")])
        scale.set(init); scale.pack(side="left", padx=8)
        return scale, lbl

    def _lh_btn(self, parent, text, cmd, bg=None, fg=None, width=18):
        bg = bg or LH_ACCENT; fg = fg or "#ffffff"
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                      font=("Segoe UI",9,"bold"), bd=0, pady=5, padx=8,
                      activebackground=LH_ACCENT2, activeforeground="#ffffff", width=width)
        b.pack(padx=16, pady=3, anchor="w"); return b

    # ─── TABS ────────────────────────────────────────────────

    def setup_esp_tab(self):
        pad = tk.Frame(self.right_frame, bg=LH_BG); pad.pack(fill="both", expand=True, pady=8)
        self._section(pad, "ESP / Visuals", LH_ACCENT2)
        toggles = [
            ("Skeleton ESP",self.skeleton_var,self.toggle_skeleton,LH_TEXT),
            ("Box ESP",self.box_var,self.toggle_box,LH_TEXT),
            ("Health Bar",self.healthbar_var,self.toggle_healthbar,LH_GREEN),
            ("Chams (Duvar Arkası Renk)",self.chams_var,self.toggle_chams,LH_ORANGE),
            ("Takım Arkadaşları",self.teammates_var,self.toggle_teammates,LH_TEXT_DIM),
            ("İsim (Name ESP)",self.names_var,self.toggle_names,LH_TEXT),
            ("Kafa Çemberi (Head ESP)",self.head_var,self.toggle_head,LH_TEXT),
            ("Silah Adı (Weapon ESP — Bıçak dahil!)",self.weapon_name_var,self.toggle_weapon_name,LH_ORANGE),
        ]
        for t,v,c,col in toggles: self._lh_check(pad,t,v,c,col)
        self._section(pad,"Renkler",LH_YELLOW)
        for t,c in [("🎨 Skeleton Rengi",self.choose_skeleton_color),("🎨 Box ESP Rengi",self.choose_box_color),
                    ("🟢 Görünür (Chams)",self.choose_visible_color),("🔴 Duvar Arkası (Chams)",self.choose_hidden_color)]:
            self._lh_btn(pad,t,c,bg=LH_PANEL,fg=LH_TEXT)
        self._section(pad,"Skeleton Kalınlık",LH_TEXT_DIM)
        sk_row = tk.Frame(pad,bg=LH_BG); sk_row.pack(fill="x",padx=16,pady=2)
        self.skel_thick_lbl = tk.Label(sk_row,text=f"{skeleton_thickness}px",font=("Segoe UI",9,"bold"),bg=LH_BG,fg=LH_ACCENT2,width=5)
        self.skel_thick_lbl.pack(side="right")
        self.skel_thick_scale = ttk.Scale(sk_row,from_=1,to=6,orient="horizontal",length=220,command=self._update_skel_thickness)
        self.skel_thick_scale.set(skeleton_thickness); self.skel_thick_scale.pack(side="left",padx=4)
        # ★ Box ESP Boyut Slider
        self._section(pad,"📦 Box ESP Boyutu",LH_TEXT_DIM)
        bx_row = tk.Frame(pad,bg=LH_BG); bx_row.pack(fill="x",padx=16,pady=2)
        self.box_scale_lbl = tk.Label(bx_row,text=f"{box_esp_scale:.2f}x",font=("Segoe UI",9,"bold"),bg=LH_BG,fg=LH_ACCENT2,width=6)
        self.box_scale_lbl.pack(side="right")
        self.box_scale_scale = ttk.Scale(bx_row,from_=0.3,to=2.0,orient="horizontal",length=220,command=self._update_box_scale)
        self.box_scale_scale.set(box_esp_scale); self.box_scale_scale.pack(side="left",padx=4)
        self._section(pad,"💣 Grenade Trajectory",LH_YELLOW)
        self._lh_check(pad,"Trajectory Önizleme",self.grenade_traj_var,self.toggle_grenade_traj,LH_YELLOW)
        self._lh_btn(pad,"🎨 Trajectory Rengi",self.choose_traj_color,bg=LH_PANEL,fg=LH_TEXT)
        self._lh_btn(pad,"🎨 Sekme Noktası Rengi",self.choose_traj_bounce_color,bg=LH_PANEL,fg=LH_TEXT)
        self._section(pad,"⚡ Yıldırım Efekti",LH_YELLOW)
        self._lh_check(pad,"Yıldırım Efektini Aç",self.lightning_var,self.toggle_lightning,LH_YELLOW)
        self._lh_btn(pad,"🎨 Yıldırım Rengi",self.choose_lightning_color,bg=LH_PANEL,fg=LH_TEXT)
        self._lh_slider(pad,"Süre",0.5,6.0,lightning_duration,self.update_lightning_duration,"s")
        self._lh_slider(pad,"Kalınlık",0.1,4.0,lightning_thickness,self.update_lightning_thickness,"x")

    def setup_aimbot_tab(self):
        pad = tk.Frame(self.right_frame, bg=LH_BG); pad.pack(fill="both", expand=True, pady=8)
        self._section(pad,"Aimbot",LH_RED)
        self._lh_check(pad,"Aimbot Etkin",self.aimbot_var,self.toggle_aimbot,LH_RED)
        self._lh_check(pad,"Sadece Görünürlere",self.visible_only_var,self.toggle_visible_only)
        self._lh_check(pad,"Duvar Arkası (Wallbang)",self.aimbot_wallbang_var,self.toggle_aimbot_wallbang,LH_TEXT_DIM)
        self._lh_check(pad,"Otomatik Ateş",self.auto_shoot_var,self.toggle_auto_shoot,LH_ORANGE)
        self._lh_check(pad,"İnsancıllaştırma (Smooth+Angle Linked)",self.humanize_var,self.toggle_humanize,LH_GREEN)

        mf = tk.Frame(pad,bg=LH_BG); mf.pack(fill="x",padx=16,pady=4)
        tk.Label(mf,text="Mod:",font=("Segoe UI",9),bg=LH_BG,fg=LH_TEXT_DIM).pack(side="left")
        ttk.Radiobutton(mf,text="Basılı Tut",variable=self.aimbot_mode_var,value="hold",command=self.toggle_aimbot_mode).pack(side="left",padx=8)
        ttk.Radiobutton(mf,text="Aç/Kapat",variable=self.aimbot_mode_var,value="toggle",command=self.toggle_aimbot_mode).pack(side="left")

        self._section(pad,"Parametreler",LH_ACCENT2)

        # Humanize bilgi kutusu
        if humanize_enabled:
            info_f = tk.Frame(pad,bg=LH_PANEL,padx=8,pady=4); info_f.pack(fill="x",padx=12,pady=(0,6))
            tk.Label(info_f,text="⚡ Humanize Aktif — Değerler Otomatik Değişiyor",font=("Segoe UI",8,"bold"),bg=LH_PANEL,fg=LH_GREEN).pack(anchor="w")
            tk.Label(info_f,text="Smooth ve MaxAngle aynı yönde birlikte değişir.",font=("Segoe UI",7,"italic"),bg=LH_PANEL,fg=LH_TEXT_DIM).pack(anchor="w")

        self.fov_scale, self.fov_label     = self._lh_slider(pad,"FOV",5,180,aimbot_fov,self.update_fov,"°")
        self.smooth_scale, self.smooth_label       = self._lh_slider(pad,"Smooth",1,20,aimbot_smooth,self.update_smooth)
        self.max_angle_scale, self.max_angle_label = self._lh_slider(pad,"Max Angle",5,180,aimbot_max_angle,self.update_max_angle,"°")

        self._lh_btn(pad,"⚡ LEGIT Preset",self.set_legit_preset,bg="#1a3a1a",fg=LH_GREEN)
        self._lh_btn(pad,"💥 RAGE Preset",self.set_rage_preset,bg="#3a1a1a",fg=LH_RED)

        self._section(pad,"Hitbox Seçimi",LH_ORANGE)
        for t,v,c in [("Kafa (Head)",self.aim_hb_head_var,self._toggle_aim_hb_head),
                      ("Gövde (Body)",self.aim_hb_body_var,self._toggle_aim_hb_body),
                      ("Bacaklar (Legs)",self.aim_hb_legs_var,self._toggle_aim_hb_legs)]:
            self._lh_check(pad,t,v,c,LH_ORANGE)
        self._section(pad,"FOV Circle",LH_ACCENT2)
        self._lh_check(pad,"FOV Çemberi Göster",self.fov_circle_var,self.toggle_fov_circle,LH_ACCENT2)
        self._lh_btn(pad,"🎨 Renk",self.choose_fov_circle_color,bg=LH_PANEL,fg=LH_TEXT)

    def setup_triggerbot_tab(self):
        pad = tk.Frame(self.right_frame, bg=LH_BG); pad.pack(fill="both", expand=True, pady=8)
        self._section(pad,"Triggerbot",LH_ORANGE)
        self._lh_check(pad,"Triggerbot Etkin",self.triggerbot_var,self.toggle_triggerbot,LH_ORANGE)
        self._lh_check(pad,"Sürekli Ateş",self.continuous_var,self.toggle_continuous)
        self._lh_check(pad,"Duvar Arkası (Wallbang)",self.trig_wallbang_var,self.toggle_trig_wallbang,LH_TEXT_DIM)
        self._section(pad,"Delay Ayarları",LH_YELLOW)
        self._lh_slider(pad,"Pre-fire Delay",0,500,int(triggerbot_pre_delay*1000),self._update_pre_delay,"ms")
        self._lh_slider(pad,"Post-fire Delay",0,500,int(triggerbot_post_delay*1000),self._update_post_delay,"ms")
        self._lh_slider(pad,"Click Delay",0,500,int(triggerbot_click_delay*1000),self._update_click_delay,"ms")
        self._section(pad,"Hold Key",LH_ACCENT2)
        self._lh_check(pad,"Hold Key Modunu Aç",self.hold_key_enabled_var,self._toggle_hold_key_enabled,LH_ACCENT2)
        hkf = tk.Frame(pad,bg=LH_BG); hkf.pack(fill="x",padx=16,pady=4)
        tk.Label(hkf,text="Hold Key:",font=("Segoe UI",9),bg=LH_BG,fg=LH_TEXT_DIM,width=12,anchor="w").pack(side="left")
        _disp = triggerbot_hold_key.upper() if triggerbot_hold_key else "— YOK —"
        self.hold_key_btn = tk.Button(hkf,text=_disp,command=self._set_hold_key,bg=LH_PANEL,fg=LH_ACCENT2,font=("Segoe UI",9,"bold"),width=14,relief="flat",bd=1)
        self.hold_key_btn.pack(side="left",padx=6)
        tk.Button(hkf,text="✖",command=self._clear_hold_key,bg=LH_PANEL,fg=LH_RED,font=("Segoe UI",9),width=3,relief="flat").pack(side="left")
        self._section(pad,"Hitbox Seçimi",LH_ORANGE)
        for t,v,c in [("Kafa",self.trig_hb_head_var,self._toggle_trig_hb_head),
                      ("Gövde",self.trig_hb_body_var,self._toggle_trig_hb_body),
                      ("Bacaklar",self.trig_hb_legs_var,self._toggle_trig_hb_legs)]:
            self._lh_check(pad,t,v,c,LH_ORANGE)

    def setup_keybinds_tab(self):
        pad = tk.Frame(self.right_frame, bg=LH_BG); pad.pack(fill="both", expand=True, pady=8)
        self._section(pad,"Keybinds",LH_ACCENT2)
        tk.Label(pad,text="Butona tıkla → yeni tuşa bas (ESC = iptal)",font=("Segoe UI",9,"italic"),bg=LH_BG,fg=LH_TEXT_DIM).pack(padx=16,pady=4,anchor="w")
        keybind_data = [("👁 Skeleton","skeleton"),("📦 Box","box"),("❤ Health Bar","healthbar"),
                        ("🎨 Chams","chams"),("👥 Takım","teammates"),("⚡ Triggerbot","triggerbot"),
                        ("🎯 Aimbot","aimbot"),("🐰 BHop","bhop"),("📋 GUI Menü","gui")]
        for text, key in keybind_data:
            f = tk.Frame(pad,bg=LH_PANEL,padx=10,pady=6); f.pack(fill="x",padx=12,pady=2)
            tk.Label(f,text=text,font=("Segoe UI",10),bg=LH_PANEL,fg=LH_TEXT,width=22,anchor="w").pack(side="left")
            disp = self.format_keybind_display(keybinds.get(key,'?'))
            btn = tk.Button(f,text=disp,command=lambda k=key: self.set_keybind(k),bg=LH_ACCENT,fg="#fff",font=("Segoe UI",9,"bold"),width=10,bd=0,pady=2)
            btn.pack(side="right",padx=4)
            setattr(self,f"{key}_key_btn",btn)

    def setup_config_tab(self):
        pad = tk.Frame(self.right_frame, bg=LH_BG); pad.pack(fill="both", expand=True, pady=8)
        self._section(pad,"Config Yönetimi",LH_GREEN)
        tk.Label(pad,text="Ayar İsmi:",font=("Segoe UI",9),bg=LH_BG,fg=LH_TEXT_DIM).pack(padx=16,anchor="w")
        self.config_name_entry = tk.Entry(pad,font=("Segoe UI",11),bg=LH_PANEL,fg=LH_TEXT,insertbackground=LH_ACCENT2,relief="flat",bd=2)
        self.config_name_entry.pack(fill="x",padx=16,pady=4); self.config_name_entry.insert(0,"my_config")
        bf = tk.Frame(pad,bg=LH_BG); bf.pack(fill="x",padx=16,pady=6)
        tk.Button(bf,text="💾 KAYDET",command=self.save_config_gui,bg=LH_GREEN,fg="#000",font=("Segoe UI",10,"bold"),bd=0,pady=6,width=16).pack(side="left",padx=(0,8))
        tk.Button(bf,text="📂 YÜKLE",command=self.load_config_gui,bg=LH_ACCENT,fg="#fff",font=("Segoe UI",10,"bold"),bd=0,pady=6,width=16).pack(side="left",padx=(0,8))
        tk.Button(bf,text="🗑 SİL",command=self.delete_config_gui,bg=LH_RED,fg="#fff",font=("Segoe UI",10,"bold"),bd=0,pady=6,width=10).pack(side="left")
        self._section(pad,"Kayıtlı Configler",LH_ACCENT2)
        self.config_listbox = tk.Listbox(pad,font=("Segoe UI",10),height=8,bg=LH_PANEL,fg=LH_TEXT,selectbackground=LH_ACCENT,selectforeground="#fff",relief="flat",bd=0)
        self.config_listbox.pack(fill="both",expand=True,padx=12,pady=4)
        self.config_listbox.bind("<Double-Button-1>",lambda e: self.load_config_gui())
        self._lh_btn(pad,"🔄 Yenile",self.refresh_configs,bg=LH_PANEL,fg=LH_TEXT_DIM)
        self.refresh_configs()

    def setup_misc_tab(self):
        pad = tk.Frame(self.right_frame, bg=LH_BG); pad.pack(fill="both", expand=True, pady=8)

        self._section(pad,"🔭 FOV Changer",LH_ACCENT2)
        self._lh_check(pad,"FOV Changer Etkin",self.fov_changer_var,self.toggle_fov_changer,LH_ACCENT2)
        self._lh_slider(pad,"FOV Değeri",60,140,fov_changer_value,self.update_fov_changer)
        self._lh_btn(pad,"▶ Şimdi Uygula",self.apply_fov_now,bg=LH_ACCENT,fg="#fff")

        self._section(pad,"🐰 BHop",LH_GREEN)
        self._lh_check(pad,"BHop Etkin (Space tuşu)",self.bhop_var,self.toggle_bhop,LH_GREEN)

        self._section(pad,"🔊 Hitsound",LH_ACCENT2)
        self._lh_check(pad,"Hitsound (Sadece ben vurduğumda)",self.hitsound_var,self.toggle_hitsound,LH_ACCENT2)

        self._section(pad,"👁 Spectator List",LH_TEXT)
        self._lh_check(pad,"Spectator Listesi Göster",self.spectator_var,self.toggle_spectator_list)
        self._lh_check(pad,"Silah İsmi Göster (Spectator)",self.spectator_show_weapon_var,self.toggle_spectator_weapon,LH_TEXT_DIM)

        self._section(pad,"🚫 Anti Effects",LH_ORANGE)
        self._lh_check(pad,"NoFlash (Flash kör etmez)",self.noflash_var,self.toggle_noflash,LH_ORANGE)
        self._lh_check(pad,"NoSmoke (Duman kaldırılır)",self.nosmoke_var,self.toggle_nosmoke,LH_ORANGE)
        self._lh_check(pad,"Smoke Renk Değiştir",self.smoke_color_var,self.toggle_smoke_color,LH_TEXT)
        self._lh_btn(pad,"🎨 Smoke Rengi",self.choose_smoke_color,bg=LH_PANEL,fg=LH_TEXT)

        self._section(pad,"✨ Trails",LH_ACCENT)
        self._lh_check(pad,"Hareket İzi (Trail)",self.player_trails_var,self.toggle_player_trails,LH_ACCENT)
        self._lh_btn(pad,"🎨 Trail Rengi",self.choose_player_trail_color,bg=LH_PANEL,fg=LH_TEXT)

        self._section(pad,"💥 Ölüm Efekti",LH_RED)
        self._lh_check(pad,"Partikül Efekti",self.death_particles_var,self.toggle_death_particles,LH_RED)
        self._lh_btn(pad,"🎨 Partikül Rengi",self.choose_death_particle_color,bg=LH_PANEL,fg=LH_TEXT)
        self._lh_slider(pad,"Partikül Hızı",0.3,2.5,death_particle_speed,self.update_particle_speed,"x")
        self._lh_slider(pad,"Partikül Ömrü",0.5,2.5,death_particle_lifetime,self.update_particle_lifetime,"x")

        self._section(pad,"🎯 Düşman Okları",LH_RED)
        self._lh_check(pad,"Ekran Dışı Düşman Okları",self.enemy_arrows_var,self.toggle_enemy_arrows,LH_RED)
        self._lh_btn(pad,"🎨 Ok Rengi",self.choose_arrow_color,bg=LH_PANEL,fg=LH_TEXT)
        self._lh_slider(pad,"Ok Uzaklığı",30,300,enemy_arrow_radius,self.update_arrow_radius,"px")

        self._section(pad,"❄️ Snow Mode",LH_ACCENT2)
        self._lh_check(pad,"Snow Mode (Kar animasyonu)",self.snow_var,self.toggle_snow,LH_ACCENT2)
        self._lh_btn(pad,"🎨 Kar Rengi",self.choose_snow_color,bg=LH_PANEL,fg=LH_TEXT)
        self._lh_slider(pad,"Kar Sıklığı",50,600,snow_density,self._update_snow_density)

        self._section(pad,"🎯 Sniper Crosshair",LH_ACCENT)
        self.sniper_cross_var = tk.BooleanVar(value=sniper_crosshair_enabled)
        self._lh_check(pad,"Sniper Crosshair (Scope'da özel nişangah)",self.sniper_cross_var,self.toggle_sniper_cross,LH_ACCENT)
        self._lh_slider(pad,"Crosshair Boyutu",5,60,sniper_crosshair_size,self._update_sniper_size)
        self._lh_slider(pad,"Crosshair Kalınlığı",1,5,sniper_crosshair_thick,self._update_sniper_thick)
        self._lh_btn(pad,"🎨 Crosshair Rengi",self.choose_sniper_color,bg=LH_PANEL,fg=LH_TEXT)
        self.sniper_dot_var = tk.BooleanVar(value=sniper_crosshair_dot)
        self._lh_check(pad,"Merkez Nokta",self.sniper_dot_var,self.toggle_sniper_dot,LH_ACCENT2)

        self._section(pad,"💧 Watermark",LH_ACCENT2)
        self.watermark_var2 = tk.BooleanVar(value=watermark_enabled)
        self._lh_check(pad,"Watermark Göster",self.watermark_var2,self.toggle_watermark,LH_ACCENT2)

        self._section(pad,"🔒 Stream Proof",LH_RED)
        self.streamproof_var = tk.BooleanVar(value=streamproof_enabled)
        self._lh_check(pad,"Stream Proof (OBS/Discord'dan gizle — GUI dahil)",self.streamproof_var,self.toggle_streamproof,LH_RED)
        tk.Label(pad,text="  Overlay ve GUI penceresini ekran yakalamalarından gizler.",font=("Segoe UI",8,"italic"),bg=LH_BG,fg=LH_TEXT_DIM).pack(padx=16,anchor="w",pady=(0,4))

    # ─── Toggle handlers ─────────────────────────────────────

    def toggle_skeleton(self): global esp_skeleton; esp_skeleton=self.skeleton_var.get()
    def toggle_box(self): global esp_box; esp_box=self.box_var.get()
    def toggle_healthbar(self): global esp_healthbar; esp_healthbar=self.healthbar_var.get()
    def toggle_chams(self): global esp_chams; esp_chams=self.chams_var.get()
    def toggle_teammates(self):
        global esp_teammates,triggerbot_shoot_teammates
        esp_teammates=self.teammates_var.get(); triggerbot_shoot_teammates=esp_teammates
    def toggle_names(self): global esp_names; esp_names=self.names_var.get()
    def toggle_head(self): global esp_head; esp_head=self.head_var.get()
    def toggle_weapon_name(self): global esp_weapon_name; esp_weapon_name=self.weapon_name_var.get()
    def toggle_grenade_traj(self): global grenade_trajectory_enabled; grenade_trajectory_enabled=self.grenade_traj_var.get()
    def toggle_lightning(self): global lightning_effect_enabled; lightning_effect_enabled=self.lightning_var.get()
    def toggle_aimbot(self): global aimbot_enabled; aimbot_enabled=self.aimbot_var.get()
    def toggle_aimbot_mode(self):
        global aimbot_hold_mode,aimbot_enabled
        if self.aimbot_mode_var.get()=="hold": aimbot_hold_mode=True; aimbot_enabled=False
        else: aimbot_hold_mode=False
    def toggle_visible_only(self): global aimbot_only_visible; aimbot_only_visible=self.visible_only_var.get()
    def toggle_aimbot_wallbang(self): global aimbot_wallbang; aimbot_wallbang=self.aimbot_wallbang_var.get()
    def toggle_auto_shoot(self): global aimbot_auto_shoot; aimbot_auto_shoot=self.auto_shoot_var.get()
    def toggle_humanize(self):
        global humanize_enabled,humanize_base_smooth
        humanize_enabled=self.humanize_var.get()
        humanize_base_smooth=aimbot_smooth
        # Sekmeyi yenile ki info kutusu çıksın/gitsin
        self.switch_category("Aimbot")
    def toggle_triggerbot(self): global triggerbot_enabled; triggerbot_enabled=self.triggerbot_var.get()
    def toggle_continuous(self): global triggerbot_continuous; triggerbot_continuous=self.continuous_var.get()
    def toggle_trig_wallbang(self): global triggerbot_wallbang; triggerbot_wallbang=self.trig_wallbang_var.get()
    def toggle_bombtimer(self): global bombtimer_enabled; bombtimer_enabled=self.bombtimer_var.get()
    def toggle_fov_changer(self): global fov_changer_enabled; fov_changer_enabled=self.fov_changer_var.get()
    def toggle_bhop(self): global bhop_enabled; bhop_enabled=self.bhop_var.get()
    def toggle_hitsound(self): global hitsound_enabled; hitsound_enabled=self.hitsound_var.get()
    def toggle_spectator_list(self): global spectator_list_enabled; spectator_list_enabled=self.spectator_var.get()
    def toggle_spectator_weapon(self): global spectator_show_weapon; spectator_show_weapon=self.spectator_show_weapon_var.get()
    def toggle_noflash(self): global noflash_enabled; noflash_enabled=self.noflash_var.get()
    def toggle_nosmoke(self): global nosmoke_enabled; nosmoke_enabled=self.nosmoke_var.get()
    def toggle_smoke_color(self): global smoke_color_enabled; smoke_color_enabled=self.smoke_color_var.get()
    def toggle_snow(self):
        global snow_mode_enabled; snow_mode_enabled=self.snow_var.get()
        if snow_mode_enabled: _init_snow_particles(snow_density)
    def toggle_player_trails(self): global player_trails_enabled; player_trails_enabled=self.player_trails_var.get()
    def toggle_death_particles(self): global death_particles_enabled; death_particles_enabled=self.death_particles_var.get()
    def toggle_enemy_arrows(self): global enemy_arrows_enabled; enemy_arrows_enabled=self.enemy_arrows_var.get()
    def toggle_fov_circle(self): global aimbot_fov_circle_enabled; aimbot_fov_circle_enabled=self.fov_circle_var.get()
    def toggle_sniper_cross(self): global sniper_crosshair_enabled; sniper_crosshair_enabled=self.sniper_cross_var.get()
    def toggle_sniper_dot(self): global sniper_crosshair_dot; sniper_crosshair_dot=self.sniper_dot_var.get()
    def _update_sniper_size(self,val): global sniper_crosshair_size; sniper_crosshair_size=int(float(val))
    def _update_sniper_thick(self,val): global sniper_crosshair_thick; sniper_crosshair_thick=int(float(val))
    def choose_sniper_color(self): self._pick("Sniper Crosshair Rengi",lambda:sniper_crosshair_color,lambda c:globals().update(sniper_crosshair_color=c))
    def toggle_watermark(self): global watermark_enabled; watermark_enabled=self.watermark_var2.get()

    def toggle_streamproof(self):
        global streamproof_enabled; streamproof_enabled=self.streamproof_var.get()
        # ★ Apply to overlay window
        try:
            hwnd=win32gui.FindWindow(None,"Overlay")
            apply_streamproof(hwnd, streamproof_enabled)
        except: pass
        # ★ Apply to GUI (Tkinter) window — OBS da görmeyecek
        try:
            gui_hwnd=ctypes.windll.user32.GetAncestor(self.root.winfo_id(), 2)
            apply_streamproof(gui_hwnd, streamproof_enabled)
        except: pass
        print(f"🔒 Streamproof: {'ON (Overlay+GUI)' if streamproof_enabled else 'OFF'}")

    def _toggle_aim_hb_head(self): global aimbot_hitbox_head; aimbot_hitbox_head=self.aim_hb_head_var.get()
    def _toggle_aim_hb_body(self): global aimbot_hitbox_body; aimbot_hitbox_body=self.aim_hb_body_var.get()
    def _toggle_aim_hb_legs(self): global aimbot_hitbox_legs; aimbot_hitbox_legs=self.aim_hb_legs_var.get()
    def _toggle_trig_hb_head(self): global triggerbot_hitbox_head; triggerbot_hitbox_head=self.trig_hb_head_var.get()
    def _toggle_trig_hb_body(self): global triggerbot_hitbox_body; triggerbot_hitbox_body=self.trig_hb_body_var.get()
    def _toggle_trig_hb_legs(self): global triggerbot_hitbox_legs; triggerbot_hitbox_legs=self.trig_hb_legs_var.get()
    def _toggle_hold_key_enabled(self): global triggerbot_hold_mode; triggerbot_hold_mode=self.hold_key_enabled_var.get()

    # ─── Sliders ─────────────────────────────────────────────
    def update_fov(self,val): global aimbot_fov; aimbot_fov=float(val)
    def update_smooth(self,val): global aimbot_smooth; aimbot_smooth=float(val)
    def update_max_angle(self,val): global aimbot_max_angle; aimbot_max_angle=float(val)
    def update_fov_changer(self,val): global fov_changer_value; fov_changer_value=int(float(val))
    def update_lightning_duration(self,val): global lightning_duration; lightning_duration=round(float(val),1)
    def update_lightning_thickness(self,val): global lightning_thickness; lightning_thickness=round(float(val),1)
    def update_particle_speed(self,val): global death_particle_speed; death_particle_speed=float(val)
    def update_particle_lifetime(self,val): global death_particle_lifetime; death_particle_lifetime=float(val)
    def update_arrow_radius(self,val): global enemy_arrow_radius; enemy_arrow_radius=int(float(val))
    def _update_skel_thickness(self,val):
        global skeleton_thickness; skeleton_thickness=max(1,int(float(val)))
        if hasattr(self,'skel_thick_lbl'): self.skel_thick_lbl.config(text=f"{skeleton_thickness}px")
    def _update_box_scale(self,val):
        global box_esp_scale; box_esp_scale=round(max(0.3,min(2.0,float(val))),2)
        if hasattr(self,'box_scale_lbl'): self.box_scale_lbl.config(text=f"{box_esp_scale:.2f}x")
    def _update_snow_density(self,val):
        global snow_density; snow_density=int(float(val))
        if snow_mode_enabled: _init_snow_particles(snow_density)
    def _update_pre_delay(self,val): global triggerbot_pre_delay; triggerbot_pre_delay=float(val)/1000.0
    def _update_post_delay(self,val): global triggerbot_post_delay; triggerbot_post_delay=float(val)/1000.0
    def _update_click_delay(self,val): global triggerbot_click_delay; triggerbot_click_delay=float(val)/1000.0

    # ─── Presets ─────────────────────────────────────────────
    def set_legit_preset(self):
        global aimbot_fov,aimbot_smooth,aimbot_max_angle
        aimbot_fov=45.0; aimbot_smooth=12.0; aimbot_max_angle=15.0
        if hasattr(self,'fov_scale'): self.fov_scale.set(aimbot_fov)
        if hasattr(self,'smooth_scale'): self.smooth_scale.set(aimbot_smooth)
        if hasattr(self,'max_angle_scale'): self.max_angle_scale.set(aimbot_max_angle)
        self.status_label.config(text="LEGIT preset ✅",fg=LH_GREEN)
    def set_rage_preset(self):
        global aimbot_fov,aimbot_smooth,aimbot_max_angle
        aimbot_fov=120.0; aimbot_smooth=1.5; aimbot_max_angle=90.0
        if hasattr(self,'fov_scale'): self.fov_scale.set(aimbot_fov)
        if hasattr(self,'smooth_scale'): self.smooth_scale.set(aimbot_smooth)
        if hasattr(self,'max_angle_scale'): self.max_angle_scale.set(aimbot_max_angle)
        self.status_label.config(text="RAGE preset ⚡",fg=LH_RED)

    # ─── Color choosers ──────────────────────────────────────
    def _pick(self,title,getter,setter,btn_attr=None):
        color=colorchooser.askcolor(title=title,color="#{:02x}{:02x}{:02x}".format(*getter()))
        if color[0]:
            setter(tuple(int(c) for c in color[0]))
            if btn_attr and hasattr(self,btn_attr):
                getattr(self,btn_attr).config(bg="#{:02x}{:02x}{:02x}".format(*getter()))

    def choose_skeleton_color(self): self._pick("Skeleton Rengi",lambda:skeleton_color,lambda c:globals().update(skeleton_color=c))
    def choose_box_color(self): self._pick("Box Rengi",lambda:box_esp_color,lambda c:globals().update(box_esp_color=c))
    def choose_visible_color(self): self._pick("Görünür Renk",lambda:visible_color,lambda c:globals().update(visible_color=c))
    def choose_hidden_color(self): self._pick("Gizli Renk",lambda:hidden_color,lambda c:globals().update(hidden_color=c))
    def choose_traj_color(self): self._pick("Trajectory Rengi",lambda:grenade_trajectory_color,lambda c:globals().update(grenade_trajectory_color=c))
    def choose_traj_bounce_color(self): self._pick("Sekme Rengi",lambda:grenade_trajectory_color_bounce,lambda c:globals().update(grenade_trajectory_color_bounce=c))
    def choose_lightning_color(self): self._pick("Yıldırım Rengi",lambda:lightning_color,lambda c:globals().update(lightning_color=c))
    def choose_fov_circle_color(self): self._pick("FOV Circle Rengi",lambda:aimbot_fov_circle_color,lambda c:globals().update(aimbot_fov_circle_color=c))
    def choose_smoke_color(self):
        color=colorchooser.askcolor(title="Smoke Rengi")
        if color[0]:
            global smoke_color_r,smoke_color_g,smoke_color_b
            smoke_color_r,smoke_color_g,smoke_color_b=int(color[0][0]),int(color[0][1]),int(color[0][2])
    def choose_arrow_color(self): self._pick("Ok Rengi",lambda:enemy_arrow_color,lambda c:globals().update(enemy_arrow_color=c))
    def choose_snow_color(self):
        self._pick("Kar Rengi",lambda:snow_color,lambda c:globals().update(snow_color=c))
        _init_snow_particles(snow_density)
    def choose_player_trail_color(self):
        self._pick("Trail Rengi",lambda:trail_color,lambda c:globals().update(trail_color=c))
        player_trail_history.clear()
    def choose_death_particle_color(self): self._pick("Partikül Rengi",lambda:death_particle_color,lambda c:globals().update(death_particle_color=c))

    # ─── Config GUI ──────────────────────────────────────────
    def save_config_gui(self):
        name=self.config_name_entry.get().strip()
        if not name: self.status_label.config(text="İsim boş!",fg=LH_RED); return
        if save_config(name): self.status_label.config(text=f"'{name}' kaydedildi ✅",fg=LH_GREEN); self.refresh_configs()
        else: self.status_label.config(text="Hata!",fg=LH_RED)
    def load_config_gui(self):
        sel=self.config_listbox.curselection()
        if not sel: self.status_label.config(text="Config seç!",fg=LH_RED); return
        name=self.config_listbox.get(sel[0])
        if load_config(name): self.status_label.config(text=f"'{name}' yüklendi ✅",fg=LH_GREEN); self.update_gui_from_config(); self.register_hotkeys()
        else: self.status_label.config(text="Hata!",fg=LH_RED)
    def delete_config_gui(self):
        sel=self.config_listbox.curselection()
        if not sel: return
        name=self.config_listbox.get(sel[0])
        try: os.remove(os.path.join(CONFIG_FOLDER,f"{name}.json")); self.status_label.config(text=f"'{name}' silindi",fg=LH_ORANGE); self.refresh_configs()
        except: self.status_label.config(text="Silme hatası",fg=LH_RED)
    def refresh_configs(self):
        self.config_listbox.delete(0,tk.END)
        for c in list_configs(): self.config_listbox.insert(tk.END,c)
    def apply_fov_now(self):
        if not dwLocalPlayerController: self.status_label.config(text="Offset yok",fg=LH_RED); return
        try:
            ctrl=pm.read_longlong(client+dwLocalPlayerController)
            if ctrl and 60<=int(fov_changer_value)<=140:
                pm.write_uint(ctrl+m_iDesiredFOV,int(fov_changer_value))
                self.status_label.config(text=f"FOV={fov_changer_value} ✅",fg=LH_GREEN)
        except Exception as e: self.status_label.config(text=f"Hata: {e}",fg=LH_RED)
    def update_gui_from_config(self):
        self.skeleton_var.set(esp_skeleton); self.box_var.set(esp_box)
        self.healthbar_var.set(esp_healthbar); self.chams_var.set(esp_chams)
        self.teammates_var.set(esp_teammates); self.names_var.set(esp_names)
        self.head_var.set(esp_head); self.triggerbot_var.set(triggerbot_enabled)
        self.continuous_var.set(triggerbot_continuous); self.visible_only_var.set(aimbot_only_visible)
        self.aimbot_wallbang_var.set(aimbot_wallbang); self.auto_shoot_var.set(aimbot_auto_shoot)
        self.trig_wallbang_var.set(triggerbot_wallbang); self.bombtimer_var.set(bombtimer_enabled)
        self.fov_changer_var.set(fov_changer_enabled); self.aimbot_var.set(aimbot_enabled)
        self.aimbot_mode_var.set("hold" if aimbot_hold_mode else "toggle")
        self.noflash_var.set(noflash_enabled); self.nosmoke_var.set(nosmoke_enabled)
        self.hitsound_var.set(hitsound_enabled); self.spectator_var.set(spectator_list_enabled)
        self.humanize_var.set(humanize_enabled); self.weapon_name_var.set(esp_weapon_name)
        self.player_trails_var.set(player_trails_enabled); self.lightning_var.set(lightning_effect_enabled)
        self.death_particles_var.set(death_particles_enabled); self.enemy_arrows_var.set(enemy_arrows_enabled)
        self.grenade_traj_var.set(grenade_trajectory_enabled); self.smoke_color_var.set(smoke_color_enabled)
        self.snow_var.set(snow_mode_enabled); self.bhop_var.set(bhop_enabled)
        self.spectator_show_weapon_var.set(spectator_show_weapon)
        # ★ FIX: Sync Misc tab vars that were missing
        if hasattr(self,'streamproof_var'): self.streamproof_var.set(streamproof_enabled)
        if hasattr(self,'sniper_cross_var'): self.sniper_cross_var.set(sniper_crosshair_enabled)
        if hasattr(self,'sniper_dot_var'): self.sniper_dot_var.set(sniper_crosshair_dot)
        if hasattr(self,'watermark_var2'): self.watermark_var2.set(watermark_enabled)
        self.switch_category(self.current_category)

    # ─── Keybinds ────────────────────────────────────────────
    def format_keybind_display(self,key):
        if key=='xbutton1': return "XBUTTON1"
        elif key=='xbutton2': return "XBUTTON2"
        return key.upper() if key else "?"
    def set_keybind(self,feature):
        self.waiting_for_key=feature; self.mouse_listener_active=True
        btn=getattr(self,f"{feature}_key_btn",None)
        if btn: btn.config(text="...",bg=LH_ORANGE)
        self.status_label.config(text="Tuşa bas...",fg=LH_ORANGE)
    def on_key_press(self,event):
        if self.waiting_for_key is None: return
        btn=getattr(self,f"{self.waiting_for_key}_key_btn",None)
        if event.keysym=='Escape':
            if btn: btn.config(text=self.format_keybind_display(keybinds.get(self.waiting_for_key,'')),bg=LH_ACCENT)
            self.waiting_for_key=None; self.mouse_listener_active=False
            self.status_label.config(text="● ACTIVE",fg=LH_GREEN); return
        self.apply_keybind(event.keysym.lower())
    def on_mouse_click(self,event):
        if not self.mouse_listener_active or self.waiting_for_key is None: return
        if event.num==4: self.apply_keybind('xbutton1')
        elif event.num==5: self.apply_keybind('xbutton2')
    def apply_keybind(self,new_key):
        feature=self.waiting_for_key; btn=getattr(self,f"{feature}_key_btn",None)
        old_key=keybinds.get(feature,'')
        try:
            if old_key not in ['xbutton1','xbutton2']: keyboard.remove_hotkey(old_key)
        except: pass
        keybinds[feature]=new_key
        if btn: btn.config(text=self.format_keybind_display(new_key),bg=LH_ACCENT)
        self.register_hotkeys(); self.waiting_for_key=None; self.mouse_listener_active=False
        self.status_label.config(text=f"{feature.upper()} = {new_key.upper()} ✅",fg=LH_GREEN)
    def register_hotkeys(self):
        try: keyboard.unhook_all_hotkeys()
        except: pass
        def t_sk(): global esp_skeleton; esp_skeleton=not esp_skeleton; self.skeleton_var.set(esp_skeleton)
        def t_bx(): global esp_box; esp_box=not esp_box; self.box_var.set(esp_box)
        def t_hb(): global esp_healthbar; esp_healthbar=not esp_healthbar; self.healthbar_var.set(esp_healthbar)
        def t_ch(): global esp_chams; esp_chams=not esp_chams; self.chams_var.set(esp_chams)
        def t_tm():
            global esp_teammates,triggerbot_shoot_teammates
            esp_teammates=not esp_teammates; triggerbot_shoot_teammates=esp_teammates; self.teammates_var.set(esp_teammates)
        def t_tr(): global triggerbot_enabled; triggerbot_enabled=not triggerbot_enabled; self.triggerbot_var.set(triggerbot_enabled)
        def t_ai():
            global aimbot_enabled
            if not aimbot_hold_mode: aimbot_enabled=not aimbot_enabled; self.aimbot_var.set(aimbot_enabled)
        def t_bh(): global bhop_enabled; bhop_enabled=not bhop_enabled; self.bhop_var.set(bhop_enabled)
        def t_gui():
            global _gui_is_open
            if self.root.state()=='withdrawn':
                self.root.deiconify(); _gui_is_open=True
                # Re-apply streamproof to GUI when it opens
                if streamproof_enabled:
                    try:
                        gui_hwnd=ctypes.windll.user32.GetAncestor(self.root.winfo_id(), 2)
                        apply_streamproof(gui_hwnd, True)
                    except: pass
            else: self.root.withdraw(); _gui_is_open=False
        fns={'skeleton':t_sk,'box':t_bx,'healthbar':t_hb,'chams':t_ch,'teammates':t_tm,'triggerbot':t_tr,'aimbot':t_ai,'bhop':t_bh,'gui':t_gui}
        for feature,key in keybinds.items():
            if key in ['xbutton1','xbutton2']: continue
            fn=fns.get(feature)
            if fn:
                try: keyboard.add_hotkey(key,fn)
                except: pass
    def update_from_hotkeys(self):
        if self.root.state()!='withdrawn':
            self.skeleton_var.set(esp_skeleton); self.box_var.set(esp_box)
            self.healthbar_var.set(esp_healthbar); self.chams_var.set(esp_chams)
            self.teammates_var.set(esp_teammates); self.triggerbot_var.set(triggerbot_enabled)
            self.aimbot_var.set(aimbot_enabled); self.aimbot_mode_var.set("hold" if aimbot_hold_mode else "toggle")
        self.root.after(100,self.update_from_hotkeys)

    def _set_hold_key(self):
        global triggerbot_hold_key
        if hasattr(self,'hold_key_btn'): self.hold_key_btn.config(text="— Tuşa bas... —",fg=LH_ORANGE)
        self.root.update()
        def _wait():
            user32=ctypes.windll.user32; xmap={0x05:'xbutton1',0x06:'xbutton2'}; deadline=time.time()+8.0
            while time.time()<deadline:
                time.sleep(0.01)
                for vk,name in xmap.items():
                    if user32.GetAsyncKeyState(vk)&0x8000:
                        self.root.after(0,lambda n=name:self._apply_hold_key(n)); return
                for vk in range(0x08,0xFF):
                    if user32.GetAsyncKeyState(vk)&0x8001:
                        try:
                            buf=ctypes.create_unicode_buffer(64); scan=(ctypes.windll.user32.MapVirtualKeyW(vk,0)<<16)
                            ctypes.windll.user32.GetKeyNameTextW(scan,buf,64)
                            kname=buf.value.strip().lower() or f"vk{vk}"
                            self.root.after(0,lambda n=kname:self._apply_hold_key(n)); return
                        except: self.root.after(0,lambda v=vk:self._apply_hold_key(f"vk{v}")); return
            self.root.after(0,lambda:self.hold_key_btn.config(text=triggerbot_hold_key.upper() if triggerbot_hold_key else "— YOK —",fg=LH_ACCENT2))
        threading.Thread(target=_wait,daemon=True).start()
    def _apply_hold_key(self,key_name):
        global triggerbot_hold_key; triggerbot_hold_key=key_name
        if hasattr(self,'hold_key_btn'): self.hold_key_btn.config(text=key_name.upper() if key_name else "— YOK —",fg=LH_ACCENT2)
    def _clear_hold_key(self):
        global triggerbot_hold_key; triggerbot_hold_key=""
        if hasattr(self,'hold_key_btn'): self.hold_key_btn.config(text="— YOK —",fg=LH_ACCENT2)


# ══════════════════════════════════════════════════════════
# BOMB TIMER
# ══════════════════════════════════════════════════════════

c4_is_planted=False; c4_remaining=0.0; c4_plant_site="?"; c4_planted_by_t=False
_c4_plant_time_ms=0; _c4_was_planted=False

def check_and_update_c4():
    global c4_is_planted,c4_remaining,c4_plant_site,c4_planted_by_t
    global _c4_plant_time_ms,_c4_was_planted
    if not bombtimer_enabled or not dwPlantedC4: return
    try:
        planted_addr=client+dwPlantedC4-0x8
        try: is_bomb_planted=pm.read_bool(planted_addr)
        except:
            try: is_bomb_planted=pm.read_int(planted_addr)!=0
            except: is_bomb_planted=False
        now_ms=int(time.time()*1000)
        if is_bomb_planted and not _c4_was_planted:
            _c4_plant_time_ms=now_ms; _c4_was_planted=True; c4_planted_by_t=True
            print("💣 Bomba kuruldu! 40s geri sayım başladı.")
        if not is_bomb_planted and _c4_was_planted:
            _c4_was_planted=False; c4_is_planted=False; c4_remaining=0.0; return
        if not is_bomb_planted: c4_is_planted=False; return
        remaining_ms=40000-(now_ms-_c4_plant_time_ms)
        c4_remaining=max(0.0,remaining_ms/1000.0)
        c4_is_planted=True
        try:
            cPlantedC4=pm.read_longlong(client+dwPlantedC4)
            if cPlantedC4:
                try: cPlantedC4=pm.read_longlong(cPlantedC4)
                except: pass
                bomb_site=pm.read_int(cPlantedC4+m_nBombSite)
                c4_plant_site="A" if bomb_site==0 else "B" if bomb_site==1 else "?"
        except: pass
        if c4_remaining<=0: c4_is_planted=False; _c4_was_planted=False
    except: pass

def draw_c4_timer(screen,font):
    return

def bomb_timer_loop():
    while True:
        time.sleep(9999)


def check_mouse_buttons():
    user32=ctypes.windll.user32; xb1p=False; xb2p=False
    while True:
        time.sleep(0.01)
        if keybinds.get('triggerbot')=='xbutton1' or keybinds.get('aimbot')=='xbutton1':
            if user32.GetAsyncKeyState(VK_XBUTTON1)&0x8000:
                if not xb1p:
                    xb1p=True
                    if keybinds.get('triggerbot')=='xbutton1': globals()['triggerbot_enabled']=not triggerbot_enabled
                    if keybinds.get('aimbot')=='xbutton1' and not aimbot_hold_mode: globals()['aimbot_enabled']=not aimbot_enabled
            else: xb1p=False
        if keybinds.get('triggerbot')=='xbutton2' or keybinds.get('aimbot')=='xbutton2':
            if user32.GetAsyncKeyState(VK_XBUTTON2)&0x8000:
                if not xb2p:
                    xb2p=True
                    if keybinds.get('triggerbot')=='xbutton2': globals()['triggerbot_enabled']=not triggerbot_enabled
                    if keybinds.get('aimbot')=='xbutton2' and not aimbot_hold_mode: globals()['aimbot_enabled']=not aimbot_enabled
            else: xb2p=False

def fov_changer_loop():
    while True:
        if fov_changer_enabled and dwLocalPlayerController:
            try:
                ctrl=pm.read_longlong(client+dwLocalPlayerController)
                if ctrl and 60<=fov_changer_value<=140: pm.write_uint(ctrl+m_iDesiredFOV,int(fov_changer_value))
            except: pass
        time.sleep(0.1)

def draw_sniper_crosshair(screen):
    if not sniper_crosshair_enabled: return
    try:
        local_player=pm.read_longlong(client+dwLocalPlayerPawn)
        if not local_player: return
        try: is_scoped=pm.read_bool(local_player+m_bIsScoped)
        except: return
        if not is_scoped: return
        cx=WINDOW_WIDTH//2; cy=WINDOW_HEIGHT//2
        r,g,b=sniper_crosshair_color; sz=sniper_crosshair_size; th=max(1,sniper_crosshair_thick)
        surf=pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT),pygame.SRCALPHA)
        pygame.draw.line(surf,(r,g,b,230),(cx-sz,cy),(cx-4,cy),th)
        pygame.draw.line(surf,(r,g,b,230),(cx+4,cy),(cx+sz,cy),th)
        pygame.draw.line(surf,(r,g,b,230),(cx,cy-sz),(cx,cy-4),th)
        pygame.draw.line(surf,(r,g,b,230),(cx,cy+4),(cx,cy+sz),th)
        if sniper_crosshair_dot: pygame.draw.circle(surf,(r,g,b,255),(cx,cy),max(1,th))
        screen.blit(surf,(0,0))
    except: pass

def draw_watermark(screen, font):
    if not watermark_enabled: return
    try:
        _wf = pygame.font.SysFont('Arial', 14, bold=True)
        wm_line = "powered by Cesur"
        txt = _wf.render(f"⚡ {wm_line}", True, (110, 100, 220))
        sh  = _wf.render(f"⚡ {wm_line}", True, (0, 0, 0))
        screen.blit(sh,  (12, 12))
        screen.blit(txt, (11, 11))
    except: pass

def draw_fov_circle(screen):
    if not aimbot_fov_circle_enabled: return
    try:
        ref=WINDOW_HEIGHT/2.0; half_fov_rad=math.radians(aimbot_fov/2.0)
        radius=int(ref*math.tan(half_fov_rad)); radius=max(5,min(radius,WINDOW_WIDTH))
        cx,cy=WINDOW_WIDTH//2,WINDOW_HEIGHT//2; r,g,b=aimbot_fov_circle_color
        fov_surf=_surf_fov if _surf_fov else pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT),pygame.SRCALPHA)
        fov_surf.fill((0,0,0,0))
        pygame.draw.circle(fov_surf,(r,g,b,200),(cx,cy),radius,1)
        screen.blit(fov_surf,(0,0))
    except: pass

def draw_enemy_arrows(screen,view_matrix,font):
    if not enemy_arrows_enabled: return
    try:
        local_player=pm.read_longlong(client+dwLocalPlayerPawn)
        if not local_player: return
        local_team=pm.read_int(local_player+m_iTeamNum)
        entity_list=pm.read_longlong(client+dwEntityList)
        if not entity_list: return
        cx=WINDOW_WIDTH//2; cy=WINDOW_HEIGHT//2; r0,g0,b0=enemy_arrow_color
        for i in range(1,65):
            try:
                le=pm.read_longlong(entity_list+0x8*((i&0x7FFF)>>9)+0x10)
                if not le: continue
                ctrl=pm.read_longlong(le+0x70*(i&0x1FF))
                if not ctrl: continue
                ph=pm.read_uint(ctrl+m_hPlayerPawn)
                if not ph or ph==0xFFFFFFFF: continue
                le2=pm.read_longlong(entity_list+0x8*((ph&0x7FFF)>>9)+0x10)
                if not le2: continue
                pawn=pm.read_longlong(le2+0x70*(ph&0x1FF))
                if not pawn or pawn==local_player: continue
                if pm.read_int(pawn+m_iTeamNum)==local_team: continue
                if pm.read_int(pawn+m_lifeState)!=256: continue
                if pm.read_int(pawn+m_iHealth)<=0: continue
                gs=pm.read_longlong(pawn+m_pGameSceneNode)
                if not gs: continue
                bm=pm.read_longlong(gs+m_modelState+0x80)
                if not bm: continue
                hb=get_bone_position(bm,6)
                if not hb: continue
                sp=w2s(view_matrix,hb[0],hb[1],hb[2],WINDOW_WIDTH,WINDOW_HEIGHT)
                # ★ FIX: Show arrow if enemy is off-screen (sp is None)
                # Also show if on-screen but near edge (within 80px of border)
                on_screen = sp is not None
                near_edge = on_screen and (sp[0]<80 or sp[0]>WINDOW_WIDTH-80 or sp[1]<80 or sp[1]>WINDOW_HEIGHT-80)
                if on_screen and not near_edge: continue  # fully visible center — no arrow needed
                # ★ FIX: Use _w2s_noclip which works even when behind camera (screenW<0)
                raw=_w2s_noclip(view_matrix,hb[0],hb[1],hb[2],WINDOW_WIDTH,WINDOW_HEIGHT)
                if raw:
                    dx=raw[0]-cx; dy=raw[1]-cy
                else:
                    # ★ FIX: Directly behind — use view matrix forward vector to get direction
                    # Compute world-space direction from local player to enemy
                    try:
                        lx=pm.read_float(local_player+m_vecOrigin); ly=pm.read_float(local_player+m_vecOrigin+4)
                        edx=hb[0]-lx; edy=hb[1]-ly
                        # Project to screen using view matrix rows 0,4 only (left/up components)
                        sx=view_matrix[0]*edx+view_matrix[1]*edy
                        sy=view_matrix[4]*edx+view_matrix[5]*edy
                        dx=sx if abs(sx)>0.001 else 0.001; dy=-sy
                    except: continue
                dist_2d=math.hypot(dx,dy)
                if dist_2d<0.001: continue
                nx=dx/dist_2d; ny=dy/dist_2d
                ax=int(cx+nx*enemy_arrow_radius); ay=int(cy+ny*enemy_arrow_radius)
                angle=math.atan2(ny,nx); arrow_r=12
                tip_x=ax+math.cos(angle)*arrow_r; tip_y=ay+math.sin(angle)*arrow_r
                left_x=ax+math.cos(angle+2.5)*(arrow_r*0.55); left_y=ay+math.sin(angle+2.5)*(arrow_r*0.55)
                righ_x=ax+math.cos(angle-2.5)*(arrow_r*0.55); righ_y=ay+math.sin(angle-2.5)*(arrow_r*0.55)
                pts=[(int(tip_x),int(tip_y)),(int(left_x),int(left_y)),(int(righ_x),int(righ_y))]
                pygame.draw.polygon(screen,(r0,g0,b0),pts,0)
                pygame.draw.polygon(screen,(255,255,255),pts,1)
            except: continue
    except: pass

def draw_player_trails(screen,view_matrix):
    global player_trail_history
    if not player_trails_enabled or len(player_trail_history)<2: return
    try:
        pts=list(player_trail_history)
        pts2d=[w2s(view_matrix,px,py,pz,WINDOW_WIDTH,WINDOW_HEIGHT) for (px,py,pz) in pts]
        total=len(pts2d); r,g,b=trail_color
        for i in range(total-1):
            p1,p2=pts2d[i],pts2d[i+1]
            if p1 is None or p2 is None: continue
            t=i/max(total-1,1)
            cr=max(0,min(255,int(r*(0.10+0.90*t)))); cg=max(0,min(255,int(g*(0.10+0.90*t)))); cb=max(0,min(255,int(b*(0.15+0.85*t))))
            pygame.draw.line(screen,(cr,cg,cb),p1,p2,max(1,int(1+5*t)))
    except: pass

def player_trail_loop():
    print("👣 Player Trail thread başladı!")
    while True:
        if player_trails_enabled:
            try:
                lp=pm.read_longlong(client+dwLocalPlayerPawn)
                if lp:
                    gs=pm.read_longlong(lp+m_pGameSceneNode)
                    if gs:
                        bm=pm.read_longlong(gs+m_modelState+0x80)
                        if bm:
                            lf=get_bone_position(bm,24); rf=get_bone_position(bm,27)
                            if lf and rf: player_trail_history.append(((lf[0]+rf[0])/2,(lf[1]+rf[1])/2,(lf[2]+rf[2])/2))
                            elif lf: player_trail_history.append(lf)
                            elif rf: player_trail_history.append(rf)
            except: pass
        else: player_trail_history.clear()
        time.sleep(0.016)

def get_view_angles_reliable():
    try:
        local_player=pm.read_longlong(client+dwLocalPlayerPawn)
        if not local_player: return None,None
        pitch=None; yaw=None
        if dwViewAngles:
            try:
                p=pm.read_float(client+dwViewAngles); y=pm.read_float(client+dwViewAngles+0x4)
                # ★ FIX: yaw aralığı ±360'a genişlet (CS2 normalize etmeden önce büyük değer verebilir)
                if abs(p)<=90.0 and abs(y)<=360.0: pitch=p; yaw=y
            except: pass
        if pitch is None:
            try:
                p=pm.read_float(local_player+m_angEyeAngles); y=pm.read_float(local_player+m_angEyeAngles+0x4)
                if abs(p)<=90.0 and abs(y)<=360.0: pitch=p; yaw=y
            except: pass
        if pitch is not None and yaw is not None:
            while yaw>180: yaw-=360
            while yaw<-180: yaw+=360
            return pitch,yaw
        return None,None
    except: return None,None

def glow_loop():
    global glow_manager; glow_manager=CS2GlowManager(); print("✨ Glow thread başladı!")
    while True:
        if glow_manager: glow_manager.update_glow()
        time.sleep(1.0/240.0)

def bhop_loop():
    global bhop_manager; bhop_manager=BHopManager(); print("🎯 BHop thread başladı!")
    while True:
        if bhop_manager: bhop_manager.update_bhop()
        # ★ FIX: 5ms — fast enough for bhop without wasting CPU
        time.sleep(0.005)

def noflash_loop():
    print("🔦 NoFlash thread başladı!"); was_enabled=False
    while True:
        try:
            lp=pm.read_longlong(client+dwLocalPlayerPawn)
            if lp:
                if noflash_enabled: pm.write_float(lp+m_flFlashMaxAlpha,0.0); was_enabled=True
                elif was_enabled: pm.write_float(lp+m_flFlashMaxAlpha,255.0); was_enabled=False
        except: pass
        time.sleep(0.008)

# ══════════════════════════════════════════════════════════
# ★ NOSMOKE + SMOKE RENK — Düzeltilmiş v3 (Çökme yok, güvenli okuma)
# ══════════════════════════════════════════════════════════

def nosmoke_loop():
    """
    NoSmoke v5 — crash yok, güvenli pointer kontrolü.
    Sadece geçerli smoke entity'lerine yazar, hiçbir zaman çökmez.
    """
    print("💨 NoSmoke/SmokeColor thread başladı!")
    SAFE = lambda a: isinstance(a, int) and 0x10000 < a < 0x7FFFFFFFFFFF

    def _apply(ent):
        if not SAFE(ent): return
        # spawn flag sıfırla
        try: pm.write_byte(ent + m_bSmokeEffectSpawned, 0)
        except: pass
        # tick = gelecek → hiç başlamaz
        try: pm.write_int(ent + m_nSmokeEffectTickBegin, 0x7FFFFFFF)
        except: pass

    def _color(ent):
        if not SAFE(ent): return
        rf = max(0.001, min(1.0, smoke_color_r / 255.0))
        gf = max(0.001, min(1.0, smoke_color_g / 255.0))
        bf = max(0.001, min(1.0, smoke_color_b / 255.0))
        for off in [m_vSmokeColor, 0x22D0, 0x22C8, 0x2300]:
            try:
                if SAFE(ent + off):
                    pm.write_float(ent + off,     rf)
                    pm.write_float(ent + off + 4, gf)
                    pm.write_float(ent + off + 8, bf)
            except: continue

    def _is_smoke(ent):
        if not SAFE(ent): return False
        try:
            if pm.read_byte(ent + m_bSmokeEffectSpawned) == 1: return True
        except: pass
        try:
            t = pm.read_int(ent + m_nSmokeEffectTickBegin)
            if 1 < t < 0x70000000: return True
        except: pass
        return False

    def _find_smokes():
        found = []; seen = set()
        # Yol 1: entity list 1-256
        try:
            el = pm.read_longlong(client + dwEntityList)
            if SAFE(el):
                for i in range(1, 257):
                    try:
                        le = pm.read_longlong(el + 0x8 * ((i & 0x7FFF) >> 9) + 0x10)
                        if not SAFE(le): continue
                        ent = pm.read_longlong(le + 0x70 * (i & 0x1FF))
                        if not SAFE(ent) or ent in seen: continue
                        if _is_smoke(ent):
                            found.append(ent); seen.add(ent)
                    except: continue
        except: pass
        # Yol 2: dwSmokeGrenadeProjectile
        if dwSmokeGrenadeProjectile:
            try:
                ptr = pm.read_longlong(client + dwSmokeGrenadeProjectile)
                if SAFE(ptr) and ptr not in seen:
                    found.append(ptr); seen.add(ptr)
            except: pass
        return found

    while True:
        try:
            if nosmoke_enabled or smoke_color_enabled:
                for ent in _find_smokes():
                    if nosmoke_enabled:   _apply(ent)
                    if smoke_color_enabled: _color(ent)
        except: pass
        time.sleep(0.05)


def third_person_loop():
    print("👁 Third Person thread başladı!")
    while True:
        try:
            if dwCSGOInput:
                cs_input = pm.read_longlong(client + dwCSGOInput)
                if cs_input and 0x10000 < cs_input < 0x7FFFFFFFFFFF:
                    pm.write_bool(cs_input + m_bIsThirdPersonCamera, False)
        except: pass
        time.sleep(0.05)


# ══════════════════════════════════════════════════════════
# ★ OVERLAY LOOP — Optimize edilmiş (60 FPS)
# ══════════════════════════════════════════════════════════

def pygame_overlay_loop():
    global _gui_is_open,_drag_active,_drag_offset,_drag_c4_pos,_drag_spec_pos
    os.environ['SDL_VIDEO_WINDOW_POS']='0,0'
    pygame.mixer.pre_init(frequency=44100,size=-16,channels=2,buffer=512)
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("Overlay")
    hwnd = pygame.display.get_wm_info()['window']
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOPMOST
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0,0,0), 0, win32con.LWA_COLORKEY)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0,0,0,0, win32con.SWP_NOMOVE|win32con.SWP_NOSIZE|win32con.SWP_NOACTIVATE)
    if streamproof_enabled: apply_streamproof(hwnd, True)
    init_persistent_surfaces()
    font     = _font_esp if _font_esp else pygame.font.SysFont('Arial',11,bold=True)
    big_font = _font_c4_big if _font_c4_big else pygame.font.SysFont('Arial',48,bold=True)
    clock    = pygame.time.Clock()
    running  = True

    def _c4_rect():
        if _drag_c4_pos is None: x=WINDOW_WIDTH//2-150; y=56
        else: x,y=_drag_c4_pos
        return pygame.Rect(x-4,y-4,320,100)
    def _spec_rect():
        if _drag_spec_pos is None: x=WINDOW_WIDTH-252; y=8
        else: x,y=_drag_spec_pos
        # Fake 3 spectator boyutuna göre: pad+22+3*20+pad = 8+22+60+8 = 98px yükseklik
        return pygame.Rect(x,y,244,110)

    # ★ Cached view matrix — sadece aktif framede yenile
    _vm_cache = [0.0]*16
    _vm_last  = 0.0

    while running:
        mx,my = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running=False
            if _gui_is_open:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                    # ★ FIX: Bomba timer her zaman drag edilebilir (bomba patlanmamış olsa bile fake görünür)
                    if bombtimer_enabled and _c4_rect().collidepoint(mx,my):
                        _drag_active='c4'; base=_drag_c4_pos if _drag_c4_pos else (WINDOW_WIDTH//2-150,60)
                        _drag_offset=(mx-base[0],my-base[1])
                    # ★ FIX: Spectator panel her zaman drag edilebilir (boş bile olsa fake gösterir)
                    elif spectator_list_enabled and _spec_rect().collidepoint(mx,my):
                        _drag_active='spec'; base=_drag_spec_pos if _drag_spec_pos else (WINDOW_WIDTH-252,12)
                        _drag_offset=(mx-base[0],my-base[1])
                    else: _drag_active=None
                elif event.type==pygame.MOUSEBUTTONUP and event.button==1: _drag_active=None
                elif event.type==pygame.MOUSEMOTION and _drag_active:
                    nx=max(0,min(mx-_drag_offset[0],WINDOW_WIDTH-50))
                    ny=max(0,min(my-_drag_offset[1],WINDOW_HEIGHT-30))
                    if _drag_active=='c4': _drag_c4_pos=(nx,ny)
                    elif _drag_active=='spec': _drag_spec_pos=(nx,ny)

        screen.fill((0,0,0))

        # View matrix: cache ile güncelle
        now_t = time.time()
        try:
            _vm_cache = [pm.read_float(client+dwViewMatrix+i*4) for i in range(16)]
            _vm_last  = now_t
        except: pass
        _vm_main = _vm_cache

        esp(screen, font)
        try:
            if _vm_main:
                draw_player_trails(screen, _vm_main)
                draw_grenade_trajectory(screen, _vm_main)
        except: pass
        try:
            if _vm_main and enemy_arrows_enabled: draw_enemy_arrows(screen, _vm_main, font)
        except: pass
        draw_fov_circle(screen)
        draw_sniper_crosshair(screen)
        draw_watermark(screen, font)
        draw_c4_timer(screen, big_font)
        draw_snow(screen)
        pygame.display.flip()
        clock.tick(60)   # ★ 60 FPS — daha az CPU kullanımı

    keyboard.unhook_all()
    pygame.quit()


_gui_instance = None
def run_gui():
    global _gui_instance
    try:
        gui = ESPGUI(); _gui_instance=gui; gui.root.mainloop()
    except Exception as e: print(f"[GUI] Hata: {e}")


def main():
    _cesur_validate()
    threading.Thread(target=triggerbot_worker, daemon=True).start()
    hitsound_init()
    threading.Thread(target=aimbot_loop,         daemon=True).start()
    threading.Thread(target=check_mouse_buttons, daemon=True).start()
    threading.Thread(target=fov_changer_loop,    daemon=True).start()
    threading.Thread(target=player_trail_loop,   daemon=True).start()
    threading.Thread(target=glow_loop,           daemon=True).start()
    threading.Thread(target=bhop_loop,           daemon=True).start()
    threading.Thread(target=bomb_timer_loop,     daemon=True).start()
    threading.Thread(target=noflash_loop,        daemon=True).start()
    threading.Thread(target=nosmoke_loop,        daemon=True).start()
    threading.Thread(target=third_person_loop,   daemon=True).start()
    time.sleep(0.5)
    threading.Thread(target=pygame_overlay_loop, daemon=True).start()
    os.system("cls")
    print("="*70)
    print(" Cesur.")
    print("="*70)
    print(f"\n{keybinds['gui'].upper()} = GUI Menüsünü Aç/Kapa")
    print("="*70)
    run_gui()


if __name__ == '__main__':
    main()