"""Tone Player plugin — extract and display tone presets from CDLC."""

import json
import os
from pathlib import Path

from fastapi.responses import FileResponse, JSONResponse

_get_dlc_dir = None
_plugin_dir = Path(__file__).parent
_gear_map = None


def _get_assets_dir():
    """Get the assets directory, checking user plugins dir first, then bundled."""
    # Check user plugins directory first (for slopsmith-desktop)
    user_plugins_dir = os.environ.get("SLOPSMITH_PLUGINS_DIR")
    if user_plugins_dir:
        user_assets = Path(user_plugins_dir) / "tones" / "assets"
        if user_assets.exists():
            return user_assets
    
    # Fall back to bundled assets
    return _plugin_dir / "assets"


def _load_gear_map():
    global _gear_map
    if _gear_map is None:
        assets_dir = _get_assets_dir()
        map_file = assets_dir / "gear_map.json"
        if map_file.exists():
            _gear_map = json.loads(map_file.read_text())
        else:
            _gear_map = {}
    return _gear_map


def _find_gear_image(effect_type):
    """Find the image file for a gear effect type like 'Amp_EN50' or 'Pedal_Distortion'."""
    gear_map = _load_gear_map()
    assets_dir = _get_assets_dir()

    # Try: exact key, then with _0/_1/_2/_3 suffix (channel variants)
    candidates = [effect_type] + [f"{effect_type}_{i}" for i in range(4)]

    for key in candidates:
        info = gear_map.get(key)
        if info and info.get("image"):
            image_key = info["image"]
            for subdir in ["amps", "cabs", "pedals", "racks"]:
                img = assets_dir / subdir / f"{image_key}.png"
                if img.exists():
                    return str(img), info.get("name", effect_type)

    # Try matching by prefix (e.g. "Amp_EN50_Gain" -> "Amp_EN50")
    parts = effect_type.split("_")
    for i in range(len(parts), 0, -1):
        prefix = "_".join(parts[:i])
        for suffix in ["", "_0", "_1", "_2"]:
            info = gear_map.get(prefix + suffix)
            if info and info.get("image"):
                image_key = info["image"]
                for subdir in ["amps", "cabs", "pedals", "racks"]:
                    img = assets_dir / subdir / f"{image_key}.png"
                    if img.exists():
                        return str(img), info.get("name", effect_type)

    return None, effect_type


def _parse_tone(tone_data):
    """Parse a tone into a structured signal chain."""
    name = tone_data.get("Name", "Unknown")
    key = tone_data.get("Key", "")
    gear_list = tone_data.get("GearList", {})

    # Signal chain order: PrePedals -> Amp -> PostPedals -> Racks -> Cabinet
    chain = []

    # Pre pedals (up to 4)
    for slot in ["PrePedal1", "PrePedal2", "PrePedal3", "PrePedal4"]:
        gear = gear_list.get(slot)
        if gear and gear.get("Type"):
            chain.append(_parse_gear(gear, "pre_pedal"))

    # Amp
    gear = gear_list.get("Amp")
    if gear and gear.get("Type"):
        chain.append(_parse_gear(gear, "amp"))

    # Post pedals (up to 4)
    for slot in ["PostPedal1", "PostPedal2", "PostPedal3", "PostPedal4"]:
        gear = gear_list.get(slot)
        if gear and gear.get("Type"):
            chain.append(_parse_gear(gear, "post_pedal"))

    # Rack effects (up to 4)
    for slot in ["Rack1", "Rack2", "Rack3", "Rack4"]:
        gear = gear_list.get(slot)
        if gear and gear.get("Type"):
            chain.append(_parse_gear(gear, "rack"))

    # Cabinet
    gear = gear_list.get("Cabinet")
    if gear and gear.get("Type"):
        chain.append(_parse_gear(gear, "cabinet"))

    return {"name": name, "key": key, "chain": chain}


def _extract_model_from_knobs(knobs, slot_type):
    """Extract the gear model key from knob names.
    E.g. 'Amp_HG500_Gain' -> 'Amp_HG500', 'Pedal_Distortion_Gain' -> 'Pedal_Distortion'."""
    if not knobs:
        return None
    first_knob = next(iter(knobs))
    parts = first_knob.split("_")
    # Knob names: Category_Model_KnobName (e.g. Amp_EN50_Gain, Pedal_Distortion_Tone)
    # Some have more parts: Rack_StudioEQ_Bass, Bass_Pedal_BassEQ8_30
    # We want everything except the last part (the knob name)
    if len(parts) >= 3:
        # Try progressively shorter prefixes to find a gear map match
        gear_map = _load_gear_map()
        for i in range(len(parts) - 1, 0, -1):
            candidate = "_".join(parts[:i])
            if candidate in gear_map:
                return candidate
        # No match — return all but last part
        return "_".join(parts[:-1])
    elif len(parts) == 2:
        return parts[0]
    return None


def _parse_gear(gear, slot_type):
    """Parse a single gear piece."""
    gear_type = gear.get("Type", "")
    knobs = gear.get("KnobValues", {})
    category = gear.get("Category", "")

    # Extract actual model from knob names
    model_key = _extract_model_from_knobs(knobs, slot_type) or gear_type

    # Clean up knob names
    clean_knobs = {}
    for k, v in knobs.items():
        parts = k.split("_")
        clean_name = parts[-1] if len(parts) > 1 else k
        clean_knobs[clean_name] = round(v, 1) if isinstance(v, float) else v

    _, display_name = _find_gear_image(model_key)

    return {
        "type": model_key,
        "name": display_name,
        "slot": slot_type,
        "category": category,
        "knobs": clean_knobs,
    }


def setup(app, context):
    global _get_dlc_dir
    _get_dlc_dir = context["get_dlc_dir"]

    @app.get("/api/plugins/tones/assets-status")
    def assets_status():
        """Check if gear assets have been extracted."""
        assets_dir = _get_assets_dir()
        if not assets_dir.exists() or not (assets_dir / "gear_map.json").exists():
            return {"ready": False, "message": "Gear assets not extracted. Run extract_assets.py first."}
        amp_count = len(list((assets_dir / "amps").glob("*.png")))
        pedal_count = len(list((assets_dir / "pedals").glob("*.png")))
        cab_count = len(list((assets_dir / "cabs").glob("*.png")))
        return {"ready": True, "amps": amp_count, "pedals": pedal_count, "cabs": cab_count}

    @app.get("/api/plugins/tones/gear-image/{gear_type}")
    def get_gear_image(gear_type: str):
        """Serve a gear image by effect type name."""
        img_path, _ = _find_gear_image(gear_type)
        if img_path and Path(img_path).exists():
            return FileResponse(img_path, media_type="image/png")
        return JSONResponse({"error": "not found"}, 404)

    @app.get("/api/plugins/tones/song/{filename:path}")
    def get_song_tones(filename: str):
        """Extract tones from a CDLC file."""
        from psarc import read_psarc_entries

        dlc = _get_dlc_dir()
        if not dlc:
            return {"error": "DLC folder not configured"}

        psarc_path = dlc / filename
        if not psarc_path.exists():
            return {"error": "File not found"}

        # Sloppaks don't carry RS-format tone manifests — they're a
        # stripped-down format with stems + arrangement JSON only. Return
        # an empty arrangements list rather than feeding a non-PSARC into
        # the PSARC parser (which 500s on the magic-byte check).
        # Normalize away any trailing path separators so both "foo.sloppak"
        # and "foo.sloppak/" are detected, while arbitrary non-sloppak
        # directories are not silently swallowed.
        if filename.rstrip("/\\").lower().endswith(".sloppak"):
            return {"arrangements": []}

        if psarc_path.is_dir():
            return {"error": "Path is a directory, not a file"}

        if not psarc_path.suffix.lower() == ".psarc":
            return {"error": "Invalid file type: expected .psarc file"}

        files = read_psarc_entries(str(psarc_path), ["*.json"])
        arrangements = []

        for path, data in sorted(files.items()):
            if not path.endswith(".json"):
                continue
            try:
                j = json.loads(data)
            except json.JSONDecodeError:
                import re
                text = data.decode("utf-8", errors="ignore")
                text = re.sub(r",\s*([}\]])", r"\1", text)
                try:
                    j = json.loads(text)
                except Exception:
                    continue

            entries = j.get("Entries", {})
            for k, v in entries.items():
                attrs = v.get("Attributes", {})
                arr_name = attrs.get("ArrangementName", "")
                if arr_name in ("Vocals", "ShowLights", "JVocals"):
                    continue
                tones = attrs.get("Tones", [])
                if not tones:
                    continue

                parsed_tones = []
                seen_keys = set()
                for t in tones:
                    key = t.get("Key", "")
                    if key in seen_keys:
                        continue
                    seen_keys.add(key)
                    parsed_tones.append(_parse_tone(t))

                if parsed_tones:
                    arrangements.append({
                        "name": arr_name,
                        "tones": parsed_tones,
                    })

        return {"arrangements": arrangements}

    @app.get("/api/plugins/tones/search")
    def search_tones(q: str = ""):
        """Search songs and return their tones."""
        meta_db = context["meta_db"]
        songs, _ = meta_db.query_page(q=q, page=0, size=10, sort="artist")
        return {"songs": [{"filename": s["filename"], "title": s["title"], "artist": s["artist"]} for s in songs]}
