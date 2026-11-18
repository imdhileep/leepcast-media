#!/usr/bin/env python3
"""Konala Vadda? pronunciation layer: turns a Telugu gadget script line into the spelling Dhileep's
IndicF5 voice reads best, BEFORE it goes to his my-voice server (~/indic-tts/server.py).

- Gadget English words (brands, chips, display/camera terms, units) -> Telugu-script phonetics
  the way Telugu tech channels say them (Motorola -> మోటరోలా, Android -> ఆండ్రాయిడ్).
- Numbers that belong to English (model numbers, specs with units) are read in English:
  "Signature 27" -> సిగ్నేచర్ ట్వెంటీ సెవెన్, "12 GB" -> ట్వెల్వ్ జీబీ, "6.8 ఇంచుల" -> సిక్స్ పాయింట్ ఎయిట్ ఇంచుల.
  Other numbers (prices, counts) are left for the server, which reads them in Telugu.
- Unknown Latin words are reported, so new names can be added to TERMS (the server would guess them).

    python3 kv_pronounce.py "Motorola Signature 27 లో 12 GB RAM ఉంది"
    from kv_pronounce import pronounce; text, unknown = pronounce(line)
"""
import re
import sys

TERMS = {
    # brands / products
    "motorola": "మోటరోలా", "moto": "మోటో", "signature": "సిగ్నేచర్", "edge": "ఎడ్జ్", "razr": "రేజర్",
    "apple": "యాపిల్", "iphone": "ఐఫోన్", "ipad": "ఐప్యాడ్", "macbook": "మ్యాక్‌బుక్", "imac": "ఐమ్యాక్",
    "mac": "మ్యాక్", "airpods": "ఎయిర్‌పాడ్స్", "watch": "వాచ్", "duo": "డ్యూయో", "homepod": "హోమ్‌పాడ్",
    "samsung": "శామ్‌సంగ్", "galaxy": "గెలాక్సీ", "google": "గూగుల్", "pixel": "పిక్సెల్",
    "oneplus": "వన్‌ప్లస్", "nord": "నార్డ్", "vivo": "వివో", "iqoo": "ఐకూ", "xiaomi": "షావోమీ",
    "redmi": "రెడ్‌మీ", "poco": "పోకో", "oppo": "ఒప్పో", "find": "ఫైండ్", "realme": "రియల్‌మీ",
    "nothing": "నథింగ్", "asus": "ఏసుస్", "zenbook": "జెన్‌బుక్", "rog": "ఆర్ ఓ జీ", "lenovo": "లెనోవో",
    "dell": "డెల్", "hp": "హెచ్‌పీ", "sony": "సోనీ", "tecno": "టెక్నో", "spark": "స్పార్క్",
    "lava": "లావా", "karbonn": "కార్బన్", "rebel": "రెబెల్", "honor": "ఆనర్", "huawei": "హువావే",
    "microsoft": "మైక్రోసాఫ్ట్", "surface": "సర్ఫేస్", "amazon": "అమెజాన్", "flipkart": "ఫ్లిప్‌కార్ట్",
    "bang": "బ్యాంగ్", "olufsen": "ఒలుఫ్సెన్", "dolby": "డాల్బీ", "vision": "విజన్", "atmos": "అట్మాస్",
    # chips / software
    "snapdragon": "స్నాప్‌డ్రాగన్", "qualcomm": "క్వాల్‌కామ్", "mediatek": "మీడియాటెక్",
    "dimensity": "డైమెన్సిటీ", "exynos": "ఎక్సినోస్", "tensor": "టెన్సర్", "bionic": "బయోనిక్",
    "elite": "ఎలీట్", "extreme": "ఎక్స్‌ట్రీమ్", "gen": "జెన్", "chip": "చిప్", "chipset": "చిప్‌సెట్",
    "processor": "ప్రాసెసర్", "android": "ఆండ్రాయిడ్", "ios": "ఐ ఓ ఎస్", "ipados": "ఐప్యాడ్ ఓ ఎస్",
    "macos": "మ్యాక్ ఓ ఎస్", "windows": "విండోస్", "hyperos": "హైపర్ ఓ ఎస్", "oneui": "వన్ యూ ఐ",
    "ui": "యూ ఐ", "os": "ఓ ఎస్", "ai": "ఏ ఐ", "app": "యాప్", "apps": "యాప్స్", "update": "అప్‌డేట్",
    "beta": "బీటా", "feature": "ఫీచర్", "features": "ఫీచర్స్",
    "intel": "ఇంటెల్", "core": "కోర్", "cores": "కోర్స్", "thunderbolt": "థండర్‌బోల్ట్", "college": "కాలేజీ",
    "hour": "అవర్", "power": "పవర్", "touchscreen": "టచ్‌స్క్రీన్", "students": "స్టూడెంట్స్",
    "aina": "ఐనా", "bengaluru": "బెంగళూరు", "san": "శాన్", "francisco": "ఫ్రాన్సిస్కో", "uber": "ఊబర్",
    "call": "కాల్", "delivery": "డెలివరీ", "reviews": "రివ్యూస్", "agents": "ఏజెంట్స్", "approve": "అప్రూవ్",
    "company": "కంపెనీ", "flick": "ఫ్లిక్", "mic": "మైక్", "music": "మ్యూజిక్", "pre-order": "ప్రీ ఆర్డర్",
    "routine": "రొటీన్", "startup": "స్టార్టప్", "twenty": "ట్వెంటీ", "seven": "సెవెన్",
    # trackers / everyday words (2026-11-11 Pixel Tag)
    "tag": "ట్యాగ్", "tags": "ట్యాగ్స్", "tracker": "ట్రాకర్", "hub": "హబ్", "store": "స్టోర్", "keys": "కీస్", "bag": "బ్యాగ్",
    "arrow": "యారో", "button": "బటన్", "guide": "గైడ్", "map": "మ్యాప్", "network": "నెట్‌వర్క్",
    "twist": "ట్విస్ట్", "uwb": "యూ డబ్ల్యూ బీ",
    # variants
    "pro": "ప్రో", "max": "మ్యాక్స్", "ultra": "అల్ట్రా", "plus": "ప్లస్", "mini": "మినీ", "lite": "లైట్",
    "air": "ఎయిర్", "fold": "ఫోల్డ్", "flip": "ఫ్లిప్", "neo": "నియో", "turbo": "టర్బో", "touch": "టచ్",
    # display / camera / battery
    "display": "డిస్‌ప్లే", "screen": "స్క్రీన్", "amoled": "అమోలెడ్", "oled": "ఓలెడ్", "ltpo": "ఎల్ టీ పీ ఓ",
    "lcd": "ఎల్ సీ డీ", "ips": "ఐ పీ ఎస్", "refresh": "రిఫ్రెష్", "rate": "రేట్", "brightness": "బ్రైట్‌నెస్",
    "nits": "నిట్స్", "camera": "కెమెరా", "cameras": "కెమెరాలు", "sensor": "సెన్సార్", "zoom": "జూమ్",
    "telephoto": "టెలిఫోటో", "periscope": "పెరిస్కోప్", "ultrawide": "అల్ట్రావైడ్", "selfie": "సెల్ఫీ",
    "video": "వీడియో", "battery": "బ్యాటరీ", "charging": "ఛార్జింగ్", "charger": "ఛార్జర్",
    "wireless": "వైర్‌లెస్", "fast": "ఫాస్ట్", "storage": "స్టోరేజ్", "ram": "ర్యామ్", "memory": "మెమరీ",
    "design": "డిజైన్", "premium": "ప్రీమియం", "flagship": "ఫ్లాగ్‌షిప్", "budget": "బడ్జెట్",
    "gaming": "గేమింగ్", "performance": "పర్ఫార్మెన్స్", "laptop": "ల్యాప్‌టాప్", "tablet": "టాబ్లెట్",
    "phone": "ఫోన్", "smartphone": "స్మార్ట్‌ఫోన్", "earbuds": "ఇయర్‌బడ్స్", "smartwatch": "స్మార్ట్‌వాచ్",
    "wifi": "వైఫై", "bluetooth": "బ్లూటూత్", "usb": "యూ ఎస్ బీ", "type": "టైప్", "nfc": "ఎన్ ఎఫ్ సీ",
    "esim": "ఈ సిమ్", "ip67": "ఐ పీ సిక్స్టీ సెవెన్", "ip68": "ఐ పీ సిక్స్టీ ఎయిట్", "ip69": "ఐ పీ సిక్స్టీ నైన్",
    # news words
    "vs": "వర్సెస్", "launch": "లాంచ్", "launched": "లాంచ్ అయ్యింది", "price": "ప్రైస్", "sale": "సేల్", "offer": "ఆఫర్",
    "india": "ఇండియా", "global": "గ్లోబల్", "verdict": "వెర్డిక్ట్", "rumour": "రూమర్", "rumor": "రూమర్",
    "leak": "లీక్", "redmagic": "రెడ్‌మ్యాజిక్", "gamers": "గేమర్స్", "updates": "అప్‌డేట్స్",
    "wait": "వెయిట్", "winner": "విన్నర్", "confirmed": "కన్ఫర్మ్డ్", "official": "అఫీషియల్", "review": "రివ్యూ", "specs": "స్పెక్స్",
    # added 2026-11-09 (news: Xiaomi 18 Pro, OPPO Reno 17, Vivo X500, ColorOS 17, iQOO 15)
    "reno": "రెనో", "pad": "ప్యాడ్", "paris": "ప్యారిస్", "leica": "లైకా", "coloros": "కలర్ ఓ ఎస్",
    "originos": "ఆరిజిన్ ఓ ఎస్", "open": "ఓపెన్", "encounter": "ఎన్‌కౌంటర్", "cat": "క్యాట్",
    "extender": "ఎక్స్‌టెండర్", "zeiss": "జైస్", "gt": "జీ టీ", "ce": "సీ ఈ", "notebookcheck": "నోట్‌బుక్‌చెక్", "smartprix": "స్మార్ట్‌ప్రిక్స్",
    # added 2026-11-09 (launch: OPPO Pad Air6)
    "air5": "ఎయిర్ ఫైవ్", "air6": "ఎయిర్ సిక్స్", "china": "చైనా", "super": "సూపర్", "confirm": "కన్ఫర్మ్",
    "phones": "ఫోన్స్", "skip": "స్కిప్", "smooth": "స్మూత్", "upgrade": "అప్‌గ్రేడ్",
    # added 2026-11-10 (launch: Honor 700 series)
    "8s": "ఎయిట్ ఎస్", "certification": "సర్టిఫికేషన్", "normal": "నార్మల్", "rear": "రియర్", "sixteen": "సిక్స్‌టీన్",
    "accurate": "యాక్యురేట్", "announce": "అనౌన్స్", "back": "బ్యాక్", "blood": "బ్లడ్", "clock": "క్లాక్",
    "colours": "కలర్స్", "colors": "కలర్స్", "date": "డేట్", "flight": "ఫ్లైట్", "heart": "హార్ట్", "idea": "ఐడియా",
    "info": "ఇన్ఫో", "leaks": "లీక్స్", "main": "మెయిన్", "models": "మోడల్స్", "oxygen": "ఆక్సిజన్", "pet": "పెట్",
    "pre-orders": "ప్రీ ఆర్డర్స్", "readings": "రీడింగ్స్", "rumours": "రూమర్స్", "series": "సిరీస్",
    "teaser": "టీజర్", "tipsters": "టిప్‌స్టర్స్", "700s": "సెవెన్ హండ్రెడ్ ఎస్",
    "europe": "యూరప్", "model": "మోడల్", "top": "టాప్",
    # added 2026-11-11 (verdict: vivo X500 Pro Max)
    "x500": "ఎక్స్ ఫైవ్ హండ్రెడ్", "lofic": "లోఫిక్", "2nm": "టూ నానోమీటర్", "black": "బ్లాక్", "digital": "డిజిటల్",
    "full": "ఫుల్", "malaysia": "మలేషియా", "photo": "ఫోటో", "photos": "ఫోటోస్", "simple": "సింపుల్", "world": "వరల్డ్",
    "artificial": "ఆర్టిఫిషియల్", "bump": "బంప్", "channel": "ఛానల్", "clear": "క్లియర్", "coming": "కమింగ్",
    "soon": "సూన్", "concerts": "కాన్సర్ట్స్", "decide": "డిసైడ్", "editing": "ఎడిటింగ్", "extra": "ఎక్స్‌ట్రా",
    "gadget": "గ్యాడ్జెట్", "king": "కింగ్", "live": "లైవ్", "macro": "మ్యాక్రో", "minus": "మైనస్", "number": "నంబర్",
    "optical": "ఆప్టికల్", "outstanding": "ఔట్‌స్టాండింగ్", "peak": "పీక్", "point": "పాయింట్", "problem": "ప్రాబ్లమ్",
    "process": "ప్రాసెస్", "processing": "ప్రాసెసింగ్", "protection": "ప్రొటెక్షన్", "rating": "రేటింగ్",
    "reports": "రిపోర్ట్స్", "resolution": "రిజల్యూషన్", "rivals": "రైవల్స్", "sharp": "షార్ప్", "side": "సైడ్",
    "site": "సైట్", "speed": "స్పీడ్", "stars": "స్టార్స్", "starting": "స్టార్టింగ్", "status": "స్టేటస్",
    "strong": "స్ట్రాంగ్", "subscribe": "సబ్‌స్క్రైబ్", "tipster": "టిప్‌స్టర్", "twist": "ట్విస్ట్", "use": "యూజ్",
    "value": "వాల్యూ", "verdicts": "వెర్డిక్ట్స్", "website": "వెబ్‌సైట్", "wildlife": "వైల్డ్‌లైఫ్", "wired": "వైర్డ్",
    # 2026-11-11 Signature 27 vs S26 Ultra
    "s26": "ఎస్ ట్వెంటీ సిక్స్", "s27": "ఎస్ ట్వెంటీ సెవెన్", "qhd": "క్యూ హెచ్ డీ",
}
# units after a number (read the number in English, then the unit)
UNITS = {
    "gb": "జీ బీ", "tb": "టీ బీ", "mb": "ఎం బీ", "mah": "ఎం ఏ హెచ్", "w": "వాట్", "watt": "వాట్",
    "hz": "హెర్ట్జ్", "ghz": "గిగాహెర్ట్జ్", "mp": "ఎం పీ", "x": "ఎక్స్", "inch": "ఇంచ్", "inches": "ఇంచెస్",
    "nits": "నిట్స్", "g": "జీ", "k": "కే",
}
# a bare model number before these words is read in English ("18 Pro" -> ఎయిటీన్ ప్రో; added 2026-11-09)
MODEL_AFTER = {"pro", "max", "ultra", "plus", "mini", "lite", "fe", "neo", "air"}
TE_UNIT_AFTER = ("ఇంచుల", "ఇంచ్", "ఇంచెస్", "వాట్", "మెగాపిక్సెల్", "జీబీ", "ఎంఏహెచ్", "హెర్ట్జ్", "ఎక్స్")

_ONES = ["జీరో", "వన్", "టూ", "త్రీ", "ఫోర్", "ఫైవ్", "సిక్స్", "సెవెన్", "ఎయిట్", "నైన్", "టెన్",
         "ఎలెవెన్", "ట్వెల్వ్", "థర్టీన్", "ఫోర్టీన్", "ఫిఫ్టీన్", "సిక్స్‌టీన్", "సెవెంటీన్", "ఎయిటీన్", "నైన్‌టీన్"]
_TENS = ["", "", "ట్వెంటీ", "థర్టీ", "ఫార్టీ", "ఫిఫ్టీ", "సిక్స్టీ", "సెవెంటీ", "ఎయిటీ", "నైంటీ"]


def en_int(n):
    """Integer (0..999,999) in English words, written in Telugu script."""
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        return _ONES[n // 100] + " హండ్రెడ్" + ("" if n % 100 == 0 else " " + en_int(n % 100))
    if n < 1_000_000:
        return en_int(n // 1000) + " థౌజండ్" + ("" if n % 1000 == 0 else " " + en_int(n % 1000))
    return " ".join(_ONES[int(d)] for d in str(n))


def en_num(s):
    s = s.replace(",", "")
    if "." in s:
        a, b = s.split(".", 1)
        return en_int(int(a or 0)) + " పాయింట్ " + " ".join(_ONES[int(d)] for d in b)
    return en_int(int(s))


_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9+\-']*|\d[\d,]*(?:\.\d+)?|\S")
_LATIN = re.compile(r"[A-Za-z]")


def pronounce(text):
    """Returns (spoken text for the voice server, sorted list of Latin words not in TERMS)."""
    text = text.replace("\"", " ఇంచ్ ").replace("”", " ఇంచ్ ")
    parts = re.split(r"(\s+)", text)
    out, unknown = [], set()
    words = [p for p in parts]
    prev_latin = False
    for i, w in enumerate(words):
        if not w or w.isspace():
            out.append(w)
            continue
        m = re.match(r"^([^\w₹]*)(.*?)([^\w]*)$", w, re.UNICODE)
        lead, core, trail = m.groups() if m else ("", w, "")
        nxt = next((x for x in words[i + 1:] if x and not x.isspace()), "")
        nxt_core = re.sub(r"[^\w]", "", nxt).lower()
        low = core.lower()
        if re.fullmatch(r"\d[\d,]*(?:\.\d+)?", core):
            english = prev_latin or nxt_core in UNITS or nxt_core in MODEL_AFTER or nxt.startswith(TE_UNIT_AFTER) or "." in core
            out.append(lead + (en_num(core) if english else core) + trail)
            prev_latin = False
            continue
        num_unit = re.fullmatch(r"(\d[\d,]*(?:\.\d+)?)([A-Za-z]+)", core)
        if num_unit and num_unit.group(2).lower() in UNITS:  # 100W, 5G, 200MP
            out.append(lead + en_num(num_unit.group(1)) + " " + UNITS[num_unit.group(2).lower()] + trail)
            prev_latin = False
            continue
        if _LATIN.search(core):
            if low in TERMS:
                out.append(lead + TERMS[low] + trail)
            elif low in UNITS:
                out.append(lead + UNITS[low] + trail)
            elif re.fullmatch(r"[A-Z0-9]{2,6}", core):  # acronym: let the server spell it letter by letter
                out.append(w)
            else:
                unknown.add(core)
                out.append(w)
            prev_latin = True
            continue
        out.append(w)
        prev_latin = False
    spoken = re.sub(r"\s{2,}", " ", "".join(out)).strip()
    return spoken, sorted(unknown)


if __name__ == "__main__":
    for line in (sys.argv[1:] or [l.rstrip("\n") for l in sys.stdin if l.strip()]):
        s, unk = pronounce(line)
        print(s + (f"   [unknown: {', '.join(unk)}]" if unk else ""))


# 2026-11-12 (C3 iPad mini)
TERMS.update({"liquid": "లిక్విడ్", "retina": "రెటీనా", "water": "వాటర్", "resistance": "రెసిస్టెన్స్",
              "a17": "ఏ సెవెంటీన్", "a20": "ఏ ట్వెంటీ"})

# 2026-11-12 (long news: HomeView, Apple TV, OSTA, Xiaomi/Vivo watches)
TERMS.update({"a18": "ఏ ఎయిటీన్", "a19": "ఏ నైన్‌టీన్", "k100": "కే హండ్రెడ్", "o1": "ఓ వన్", "osta": "ఓస్టా",
              "s5": "ఎస్ ఫైవ్", "41mm": "ఫార్టీ వన్ ఎం ఎం", "5atm": "ఫైవ్ ఏ టీ ఎం", "tv": "టీవీ",
              "homeview": "హోమ్‌వ్యూ", "home": "హోమ్", "siri": "సిరి", "remote": "రిమోట్", "sofa": "సోఫా",
              "buy": "బై", "chat": "చాట్", "station": "స్టేషన్", "english": "ఇంగ్లీష్", "my": "మై",
              "news": "న్యూస్", "november": "నవంబర్", "off": "ఆఫ్", "white": "వైట్", "pay": "పే",
              "richard": "రిచర్డ్", "yu": "యూ", "xingmang": "షింగ్‌మాంగ్", "telugu": "తెలుగు",
              "konala": "కొనాలా", "vadda": "వద్దా", "available": "అవైలబుల్", "base": "బేస్", "box": "బాక్స్",
              "brand": "బ్రాండ్", "business": "బిజినెస్", "chairman": "ఛైర్మన్", "chance": "ఛాన్స్",
              "charge": "ఛార్జ్", "consumer": "కన్స్యూమర్", "event": "ఈవెంట్", "far-field": "ఫార్ ఫీల్డ్",
              "feeds": "ఫీడ్స్", "flat": "ఫ్లాట్", "gadgets": "గ్యాడ్జెట్స్", "just": "జస్ట్",
              "lovers": "లవర్స్", "maps": "మ్యాప్స్", "microphones": "మైక్రోఫోన్స్", "modes": "మోడ్స్",
              "offline": "ఆఫ్‌లైన్", "speaker": "స్పీకర్", "sports": "స్పోర్ట్స్", "surprise": "సర్‌ప్రైజ్",
              "trend": "ట్రెండ్", "user": "యూజర్", "watches": "వాచెస్"})
TERMS.update({"carl": "కార్ల్", "pei": "పెయ్", "december": "డిసెంబర్", "recorder": "రికార్డర్", "bonus": "బోనస్",
              "circle": "సర్కిల్", "device": "డివైస్", "gray": "గ్రే", "lights": "లైట్స్", "pink": "పింక్",
              "rose": "రోజ్", "ship": "షిప్", "silver": "సిల్వర్", "space": "స్పేస్", "starlight": "స్టార్‌లైట్",
              "voice": "వాయిస్", "ceo": "సీ ఈ ఓ"})
TERMS.update({"telangana": "తెలంగాణ", "loss": "లాస్", "unit": "యూనిట్", "watt-hours": "వాట్ అవర్స్",
              "zero": "జీరో"})

# 2026-11-12 (T4 best 5G phones under 15,000)
TERMS.update({"bold": "బోల్డ్", "ads": "యాడ్స్", "clean": "క్లీన్", "description": "డిస్క్రిప్షన్",
              "order": "ఆర్డర్", "links": "లింక్స్", "n2": "ఎన్ టూ", "n4": "ఎన్ ఫోర్", "a7": "ఏ సెవెన్",
              "ip64": "ఐ పీ సిక్స్టీ ఫోర్", "hertz": "హెర్ట్జ్", "pick": "పిక్"})

# 2026-11-12 (C4 AirPods 5 vs AirPods Pro 3)
TERMS.update({"hearing": "హియరింగ్", "noise": "నాయిస్", "test": "టెస్ట్", "calls": "కాల్స్",
              "cancellation": "క్యాన్సిలేషన్", "ear": "ఇయర్", "fit": "ఫిట్", "gym": "జిమ్",
              "in-ear": "ఇన్ ఇయర్", "open-ear": "ఓపెన్ ఇయర్", "sensing": "సెన్సింగ్", "tips": "టిప్స్",
              "workouts": "వర్కౌట్స్"})

# 2026-11-12 (C5 Samsung + Google Intelligent Eyewear)
TERMS.update({"gemini": "జెమినై", "gentle": "జెంటిల్", "monster": "మాన్‌స్టర్", "korea": "కొరియా",
              "meta": "మెటా", "ray-ban": "రే బాన్", "directions": "డైరెక్షన్స్", "frames": "ఫ్రేమ్స్",
              "glasses": "గ్లాసెస్", "import": "ఇంపోర్ట్", "menu": "మెనూ", "translate": "ట్రాన్స్‌లేట్"})

# 2026-11-13 (T3 iPhone cost per day)
TERMS.update({"17e": "సెవెంటీన్ ఈ", "divide": "డివైడ్", "foldable": "ఫోల్డబుల్", "worth": "వర్త్",
              "years": "ఇయర్స్", "duo": "డ్యూయో"})

# 2026-11-13 (T5 Apple HomeView)
TERMS.update({"calendar": "క్యాలెండర్", "control": "కంట్రోల్", "door": "డోర్", "face": "ఫేస్", "faces": "ఫేసెస్",
              "locks": "లాక్స్", "messages": "మెసేజెస్", "reminders": "రిమైండర్స్", "smart": "స్మార్ట్",
              "wall": "వాల్", "wow": "వావ్", "homeview": "హోమ్ వ్యూ"})

# 2026-11-13 (long: November Pixel Drop update explainer)
TERMS.update({"background": "బ్యాక్‌గ్రౌండ్", "calculator": "కాల్క్యులేటర్", "carrier": "క్యారియర్",
              "coach": "కోచ్", "drop": "డ్రాప్", "family": "ఫ్యామిలీ", "health": "హెల్త్", "hilight": "హైలైట్",
              "hindi": "హిందీ", "intelligence": "ఇంటెలిజెన్స్", "mode": "మోడ్", "notification": "నోటిఫికేషన్",
              "pixels": "పిక్సెల్స్", "rambler": "రాంబ్లర్", "real": "రియల్", "reps": "రెప్స్",
              "settings": "సెట్టింగ్స్", "software": "సాఫ్ట్‌వేర్", "system": "సిస్టమ్", "takeout": "టేక్‌అవుట్",
              "thursday": "థర్స్‌డే", "transit": "ట్రాన్సిట్", "unknown": "అన్‌నోన్", "wednesday": "వెడ్నెస్‌డే",
              "wi-fi": "వై ఫై", "active": "యాక్టివ్", "blog": "బ్లాగ్", "book": "బుక్", "by": "బై",
              "calendars": "క్యాలెండర్స్", "catch": "క్యాచ్", "chats": "చాట్స్", "connect": "కనెక్ట్",
              "contacts": "కాంటాక్ట్స్", "conversion": "కన్వర్షన్", "countdown": "కౌంట్‌డౌన్",
              "currency": "కరెన్సీ", "default": "డీఫాల్ట్", "details": "డీటెయిల్స్", "emails": "ఈమెయిల్స్",
              "favourite": "ఫేవరెట్", "focus": "ఫోకస్", "follow": "ఫాలో", "free": "ఫ్రీ", "glow": "గ్లో",
              "good": "గుడ్", "groceries": "గ్రోసరీస్", "icon": "ఐకాన్", "icons": "ఐకాన్స్",
              "install": "ఇన్‌స్టాల్", "language": "లాంగ్వేజ్", "languages": "లాంగ్వేజెస్", "location": "లొకేషన్",
              "log": "లాగ్", "look": "లుక్", "manage": "మేనేజ్", "markets": "మార్కెట్స్", "on": "ఆన్",
              "passwords": "పాస్‌వర్డ్స్", "phases": "ఫేజెస్", "proactive": "ప్రోయాక్టివ్", "regions": "రీజియన్స్",
              "reservation": "రిజర్వేషన్", "restart": "రీస్టార్ట్", "restaurant": "రెస్టారెంట్", "ride": "రైడ్",
              "routines": "రొటీన్స్", "search": "సెర్చ్", "select": "సెలెక్ట్", "share": "షేర్",
              "sharing": "షేరింగ్", "step": "స్టెప్", "styles": "స్టైల్స్", "subscription": "సబ్‌స్క్రిప్షన్",
              "suggestions": "సజెషన్స్", "summaries": "సమ్మరీస్", "summary": "సమ్మరీ", "tap": "ట్యాప్",
              "text": "టెక్స్ట్", "time": "టైమ్", "train": "ట్రైన్", "trip": "ట్రిప్", "typing": "టైపింగ్",
              "unlock": "అన్‌లాక్", "users": "యూజర్స్", "vacation": "వెకేషన్", "weight": "వెయిట్",
              "widget": "విడ్జెట్", "eta": "ఈ టీ ఏ", "uwb": "యూ డబ్ల్యూ బీ", "premium": "ప్రీమియం"})
# 2026-11-12 T1 (iPhone Name Recognition)
TERMS.update({"accessibility": "యాక్సెసిబిలిటీ", "name": "నేమ్", "office": "ఆఫీస్", "recognition": "రికగ్నిషన్",
              "set": "సెట్", "sound": "సౌండ్", "up": "అప్", "and": "అండ్", "bus": "బస్", "earphones": "ఇయర్‌ఫోన్స్",
              "list": "లిస్ట్", "miss": "మిస్", "music": "మ్యూజిక్", "record": "రికార్డ్", "setting": "సెట్టింగ్"})
# 2026-11-12 C1 (HyperOS 4)
TERMS.update({"about": "అబౌట్", "check": "చెక్", "f": "ఎఫ్", "lock": "లాక్", "note": "నోట్", "notes": "నోట్స్",
              "region": "రీజియన్", "backup": "బ్యాకప్", "dates": "డేట్స్", "eight": "ఎయిట్", "fifteen": "ఫిఫ్టీన్",
              "for": "ఫర్", "fourteen": "ఫోర్టీన్", "glass": "గ్లాస్", "lab": "ల్యాబ్", "light": "లైట్", "list": "లిస్ట్",
              "memo": "మెమో", "notifications": "నోటిఫికేషన్స్", "seventeen": "సెవెంటీన్", "soft": "సాఫ్ట్",
              "to-do": "టు డూ", "widgets": "విడ్జెట్స్", "stack": "స్టాక్"})
# 2026-11-12 T2 (Apple Support Community closing)
TERMS.update({"community": "కమ్యూనిటీ", "support": "సపోర్ట్", "com": "కామ్", "dot": "డాట్", "fix": "ఫిక్స్",
              "fixes": "ఫిక్సెస్", "forum": "ఫోరమ్", "help": "హెల్ప్", "posts": "పోస్ట్స్", "problems": "ప్రాబ్లమ్స్",
              "questions": "క్వశ్చన్స్", "repair": "రిపేర్", "save": "సేవ్", "start": "స్టార్ట్"})
# 2026-11-13 C2 (Apple Watch battle)
TERMS.update({"fitness": "ఫిట్‌నెస్", "score": "స్కోర్", "sleep": "స్లీప్", "steps": "స్టెప్స్", "tracking": "ట్రాకింగ్"})
# 2026-11-13 T4 (best soundbars under ₹15,000)
TERMS.update({"aavante": "ఆవాంటే", "cinema": "సినిమా", "ht-s20r": "హెచ్ టీ ఎస్ ట్వెంటీ ఆర్", "m.r.p": "ఎం ఆర్ పీ",
              "prime": "ప్రైమ్", "bar": "బార్", "boat": "బోట్", "center": "సెంటర్", "dialogues": "డైలాగ్స్",
              "room": "రూమ్", "separate": "సెపరేట్", "soundbars": "సౌండ్‌బార్స్", "soundbar": "సౌండ్‌బార్",
              "speakers": "స్పీకర్స్", "subwoofer": "సబ్‌వూఫర్", "sb510": "ఎస్ బీ ఫైవ్ టెన్",
              "5000da": "ఫైవ్ థౌజండ్ డీ ఏ"})
# 2026-11-13 C4 (Galaxy Buds4 Pro vs Buds4)
TERMS.update({"amazon.in": "అమెజాన్ డాట్ ఇన్", "buds4": "బడ్స్ ఫోర్", "better": "బెటర్", "metro": "మెట్రో",
              "seal": "సీల్", "tweeter": "ట్వీటర్", "woofer": "వూఫర్", "ip57": "ఐ పీ ఫిఫ్టీ సెవెన్",
              "ip54": "ఐ పీ ఫిఫ్టీ ఫోర్"})
# 2026-11-13 C5 (Ray-Ban Meta Gen 3 vs Gen 2)
TERMS.update({"action": "యాక్షన్", "press": "ప్రెస్", "style": "స్టైల్"})
# 2026-11-13 T1 (Google TV app phone remote)
TERMS.update({"pair": "పెయిర్", "quick": "క్విక్", "tvs": "టీవీస్", "add": "యాడ్", "code": "కోడ్",
              "cushions": "కుషన్స్", "keyboard": "కీబోర్డ్", "movie": "మూవీ", "nearby": "నియర్‌బై",
              "tension": "టెన్షన్", "volume": "వాల్యూమ్"})
# 2026-11-13 T2 (Amazon Alexa for Shopping)
TERMS.update({"alexa": "అలెక్సా", "history": "హిస్టరీ", "shopping": "షాపింగ్", "alert": "అలర్ట్",
              "compare": "కంపేర్", "confusion": "కన్‌ఫ్యూజన్", "discount": "డిస్కౌంట్"})
# 2026-11-13 C1 (OnePlus ColorOS 17)
TERMS.update({"guard": "గార్డ్", "oxygenos": "ఆక్సిజన్ ఓ ఎస్", "fake": "ఫేక్", "six": "సిక్స్", "smoothness": "స్మూత్‌నెస్",
              "swap": "స్వాప్", "three": "త్రీ", "twelve": "ట్వెల్వ్", "warning": "వార్నింగ్"})
# 2026-11-14 long (Gadget News: Google Wallet home key, realme service, QPR3, Redmi Note 18, Nothing)
TERMS.update({"4a": "ఫోర్ ఏ", "4b": "ఫోర్ బీ", "6a": "సిక్స్ ఏ", "absolute": "ఆబ్సల్యూట్", "akis": "ఆకిస్",
              "aliro": "అలీరో", "approach": "అప్రోచ్", "aqara": "అకారా", "august": "ఆగస్ట్", "centres": "సెంటర్స్",
              "centre": "సెంటర్", "day": "డే", "developer": "డెవలపర్", "disable": "డిసేబుల్", "evangelidis": "ఎవాంజెలిడిస్",
              "interiors": "ఇంటీరియర్స్", "keypad": "కీప్యాడ్", "labour": "లేబర్", "launcher": "లాంచర్", "nuki": "నూకీ",
              "preview": "ప్రివ్యూ", "public": "పబ్లిక్", "random": "రాండమ్", "schlage": "ష్లాగ్", "sense": "సెన్స్",
              "service": "సర్వీస్", "wallet": "వాలెట్", "branding": "బ్రాండింగ్", "bug": "బగ్", "certified": "సర్టిఫైడ్",
              "charges": "ఛార్జెస్", "cities": "సిటీస్", "cleaning": "క్లీనింగ్", "co-founder": "కో ఫౌండర్",
              "crashes": "క్రాషెస్", "database": "డేటాబేస్", "double": "డబుల్", "drain": "డ్రెయిన్", "engineers": "ఇంజనీర్స్",
              "genuine": "జెన్యూన్", "key": "కీ", "lineup": "లైనప్", "options": "ఆప్షన్స్", "panel": "ప్యానెల్",
              "parts": "పార్ట్స్", "plan": "ప్లాన్", "protector": "ప్రొటెక్టర్", "reboots": "రీబూట్స్", "repairs": "రిపేర్స్",
              "report": "రిపోర్ట్", "section": "సెక్షన్", "spare": "స్పేర్", "stable": "స్టేబుల్", "to": "టు",
              "toggle": "టాగుల్", "towns": "టౌన్స్", "useful": "యూస్‌ఫుల్", "version": "వెర్షన్", "watts": "వాట్స్",
              "way": "వే", "wear": "వేర్"})
# 2026-11-15 long (Weekly Roundup: HomeView, Apple TV 4K, Pixel Tag, Samsung eyewear, Pixel Drop, Alexa, vivo X500)
TERMS.update({"a": "ఏ", "airtag": "ఎయిర్‌ట్యాగ్", "airtel": "ఎయిర్‌టెల్", "basic": "బేసిక్", "echo": "ఎకో",
              "eyewear": "ఐవేర్", "facetime": "ఫేస్‌టైమ్", "fog": "ఫాగ్", "homepods": "హోమ్‌పాడ్స్",
              "intelligent": "ఇంటెలిజెంట్", "jio": "జియో", "kit": "కిట్", "kitchen": "కిచెన్", "movies": "మూవీస్",
              "multi": "మల్టీ", "parker": "పార్కర్", "photographer": "ఫోటోగ్రాఫర్", "privacy": "ప్రైవసీ",
              "s": "ఎస్", "safety": "సేఫ్టీ", "schneider": "ష్నైడర్", "south": "సౌత్", "stage": "స్టేజ్",
              "table": "టేబుల్", "warby": "వార్బీ", "wideband": "వైడ్‌బ్యాండ్", "assistant": "అసిస్టెంట్",
              "bedroom": "బెడ్‌రూమ్", "blur": "బ్లర్", "brands": "బ్రాండ్స్", "built": "బిల్ట్", "capture": "క్యాప్చర్",
              "car": "కార్", "case": "కేస్", "cell": "సెల్", "coin": "కాయిన్", "colour": "కలర్",
              "connections": "కనెక్షన్స్", "content": "కంటెంట్", "data": "డేటా", "decoder": "డీకోడర్", "deep": "డీప్",
              "degree": "డిగ్రీ", "designs": "డిజైన్స్", "devices": "డివైసెస్", "direction": "డైరెక్షన్",
              "dollars": "డాలర్స్", "doubt": "డౌట్", "ecosystem": "ఎకోసిస్టమ్", "eighteen": "ఎయిటీన్",
              "experience": "ఎక్స్‌పీరియన్స్", "finding": "ఫైండింగ్", "five": "ఫైవ్", "format": "ఫార్మాట్",
              "future": "ఫ్యూచర్", "grams": "గ్రామ్స్", "graphics": "గ్రాఫిక్స్", "group": "గ్రూప్", "guess": "గెస్",
              "hundred": "హండ్రెడ్", "iphones": "ఐఫోన్స్", "in": "ఇన్", "internet": "ఇంటర్నెట్", "item": "ఐటమ్",
              "items": "ఐటమ్స్", "lighting": "లైటింగ్", "moment": "మొమెంట్", "money": "మనీ", "mount": "మౌంట్",
              "nineteen": "నైన్‌టీన్", "pack": "ప్యాక్", "perfect": "పర్ఫెక్ట్", "personal": "పర్సనల్",
              "precision": "ప్రెసిషన్", "prices": "ప్రైసెస్", "product": "ప్రోడక్ట్", "quality": "క్వాలిటీ",
              "release": "రిలీజ్", "return": "రిటర్న్", "rollout": "రోల్‌అవుట్", "rule": "రూల్", "shop": "షాప్",
              "sign": "సైన్", "silent": "సైలెంట్", "stainless": "స్టెయిన్‌లెస్", "steel": "స్టీల్",
              "storefronts": "స్టోర్‌ఫ్రంట్స్", "streaming": "స్ట్రీమింగ్", "suggest": "సజెస్ట్", "surround": "సరౌండ్",
              "tasks": "టాస్క్స్", "ten": "టెన్", "thirteen": "థర్టీన్", "thirty": "థర్టీ", "trick": "ట్రిక్",
              "try": "ట్రై", "tuning": "ట్యూనింగ్", "turn": "టర్న్", "two": "టూ", "view": "వ్యూ",
              "warranty": "వారంటీ", "week": "వీక్", "s10": "ఎస్ టెన్", "cr2032": "సీ ఆర్ ట్వెంటీ థర్టీ టూ",
              "x500": "ఎక్స్ ఫైవ్ హండ్రెడ్"})

# 2026-11-16 (long news: Reno 17, Xiaomi 18 Pro global, Edge 70 Neo, Lava Probuds, Apple glasses)
TERMS.update({"7s": "సెవెన్ ఎస్", "13mm": "థర్టీన్ ఎం ఎం", "bloomberg": "బ్లూమ్‌బర్గ్", "blue": "బ్లూ",
              "cosmic": "కాస్మిక్", "velvet": "వెల్వెట్", "red": "రెడ్", "gurman": "గర్మన్", "mark": "మార్క్",
              "italy": "ఇటలీ", "june": "జూన్", "nov": "నవంబర్", "probuds": "ప్రోబడ్స్", "xplore": "ఎక్స్‌ప్లోర్",
              "recent": "రీసెంట్", "consider": "కన్సిడర్", "dark": "డార్క్", "green": "గ్రీన్",
              "drivers": "డ్రైవర్స్", "edit": "ఎడిట్", "link": "లింక్", "listing": "లిస్టింగ్", "page": "పేజ్",
              "retail": "రీటైల్", "welcome": "వెల్కమ్", "ip69k": "ఐ పీ సిక్స్టీ నైన్ కే", "wwdc": "డబ్ల్యూ డబ్ల్యూ డీ సీ",
              "ifa": "ఐ ఎఫ్ ఏ", "anc": "ఏ ఎన్ సీ", "ois": "ఓ ఐ ఎస్", "hint": "హింట్"})

# 2026-11-18 (long verdict: Xiaomi 18 Pro series global)
TERMS.update({"75mm": "సెవెంటీ ఫైవ్ ఎం ఎం", "asia": "ఏషియా", "bright": "బ్రైట్", "cable": "కేబుల్", "compact": "కాంపాక్ట్",
              "creators": "క్రియేటర్స్", "france": "ఫ్రాన్స్", "french": "ఫ్రెంచ్", "front": "ఫ్రంట్", "gimmick": "గిమ్మిక్",
              "gorilla": "గొరిల్లా", "philippines": "ఫిలిప్పీన్స్", "presse-citron": "ప్రెస్ సిట్రాన్", "september": "సెప్టెంబర్",
              "today": "టుడే", "ultra-wide": "అల్ట్రా వైడ్", "victus": "విక్టస్", "videos": "వీడియోస్", "angles": "యాంగిల్స్",
              "auto": "ఆటో", "best": "బెస్ట్", "buyer": "బయ్యర్", "cards": "కార్డ్స్", "chips": "చిప్స్", "degrees": "డిగ్రీస్",
              "direct": "డైరెక్ట్", "early": "ఎర్లీ", "euro": "యూరో", "exciting": "ఎక్సైటింగ్", "final": "ఫైనల్", "fps": "ఎఫ్ పీ ఎస్",
              "games": "గేమ్స్", "heavy": "హెవీ", "lens": "లెన్స్", "night": "నైట్", "numbers": "నంబర్స్", "offers": "ఆఫర్స్",
              "option": "ఆప్షన్", "part": "పార్ట్", "ranking": "ర్యాంకింగ్", "ready": "రెడీ", "rival": "రైవల్", "rupees": "రూపీస్",
              "samples": "శాంపిల్స్", "shadows": "షాడోస్", "size": "సైజ్", "sky": "స్కై", "taxes": "టాక్సెస్",
              "technology": "టెక్నాలజీ", "tests": "టెస్ట్స్", "very": "వెరీ", "vlogs": "వ్లాగ్స్", "wallpapers": "వాల్‌పేపర్స్"})
TERMS.update({"x10": "ఎక్స్ టెన్", "xl": "ఎక్స్ ఎల్"})
