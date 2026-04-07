#!/usr/bin/env python3
"""
Extract gear images from Rocksmith 2014's gears.psarc.

This script reads the tone designer assets from your Rocksmith installation
and converts them to PNG images for use with the Slopsmith Tone Player plugin.

Usage:
    python extract_assets.py [/path/to/Rocksmith2014]

If no path is given, common Steam install locations are checked automatically.
"""

import json
import os
import struct
import sys
import zlib
from pathlib import Path

# ── Minimal PSARC reader (no external dependencies) ─────────────────────

ARC_KEY = bytes.fromhex("C53DB23870A1A2F71CAE64061FDD0E1157309DC85204D4C5BFDF25090DF2572C")
ARC_IV = bytes.fromhex("E915AA018FEF71FC508132E4BB4CEB42")


def _decrypt_toc(data):
    try:
        from Crypto.Cipher import AES
    except ImportError:
        try:
            from Cryptodome.Cipher import AES
        except ImportError:
            print("Error: pycryptodome is required. Install it with:")
            print("  pip install pycryptodome")
            sys.exit(1)
    aes = AES.new(ARC_KEY, AES.MODE_CFB, iv=ARC_IV, segment_size=128)
    return aes.decrypt(data)


def read_psarc(filepath, patterns=None):
    """Read specific files from a PSARC. Returns {path: bytes}."""
    import fnmatch
    result = {}
    with open(filepath, "rb") as f:
        magic = f.read(4)
        if magic != b"PSAR":
            raise ValueError("Not a PSARC file")

        _ver = struct.unpack(">I", f.read(4))[0]
        _comp = f.read(4)
        toc_length = struct.unpack(">I", f.read(4))[0]
        toc_entry_size = struct.unpack(">I", f.read(4))[0]
        toc_entries = struct.unpack(">I", f.read(4))[0]
        block_size = struct.unpack(">I", f.read(4))[0]
        archive_flags = struct.unpack(">I", f.read(4))[0]

        toc_region = f.read(toc_length - 32)
        if archive_flags == 4:
            toc_region = _decrypt_toc(toc_region)

        toc_data = toc_region[:toc_entry_size * toc_entries]
        bt_data = toc_region[toc_entry_size * toc_entries:]

        entries = []
        for i in range(toc_entries):
            off = i * toc_entry_size
            ed = toc_data[off:off + toc_entry_size]
            z_index = struct.unpack(">I", ed[16:20])[0]
            length = int.from_bytes(ed[20:25], "big")
            offset = int.from_bytes(ed[25:30], "big")
            entries.append({"z_index": z_index, "length": length, "offset": offset})

        block_sizes = []
        for i in range(len(bt_data) // 2):
            block_sizes.append(int.from_bytes(bt_data[i * 2:i * 2 + 2], "big"))

        # Read file listing
        fl_entry = entries[0]
        f.seek(fl_entry["offset"])
        fl_data = b""
        num_blocks = (fl_entry["length"] + block_size - 1) // block_size
        for i in range(num_blocks):
            bi = fl_entry["z_index"] + i
            cs = block_sizes[bi] if bi < len(block_sizes) else 0
            if cs == 0:
                remaining = fl_entry["length"] - len(fl_data)
                fl_data += f.read(min(block_size, remaining))
            else:
                bd = f.read(cs)
                try:
                    fl_data += zlib.decompress(bd)
                except zlib.error:
                    fl_data += bd
        fl_data = fl_data[:fl_entry["length"]]
        filenames = fl_data.decode("utf-8", errors="ignore").replace("\r\n", "\n").strip().split("\n")

        for entry, filename in zip(entries[1:], filenames):
            filename = filename.strip()
            if not filename:
                continue
            if patterns:
                if not any(fnmatch.fnmatch(filename.lower(), p.lower()) for p in patterns):
                    continue
            f.seek(entry["offset"])
            data = b""
            num_blocks = (entry["length"] + block_size - 1) // block_size
            for i in range(num_blocks):
                bi = entry["z_index"] + i
                cs = block_sizes[bi] if bi < len(block_sizes) else 0
                if cs == 0:
                    remaining = entry["length"] - len(data)
                    data += f.read(min(block_size, remaining))
                else:
                    bd = f.read(cs)
                    try:
                        data += zlib.decompress(bd)
                    except zlib.error:
                        data += bd
            result[filename] = data[:entry["length"]]

    return result


# ── DDS to PNG conversion (minimal, no Pillow required for basic DDS) ────

def dds_to_png_pillow(dds_data):
    """Convert DDS bytes to PNG bytes using Pillow."""
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(dds_data)).convert("RGBA")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


# ── Main ─────────────────────────────────────────────────────────────────

STEAM_PATHS = [
    Path.home() / ".local/share/Steam/steamapps/common/Rocksmith2014",
    Path.home() / ".steam/steam/steamapps/common/Rocksmith2014",
    Path("C:/Program Files (x86)/Steam/steamapps/common/Rocksmith2014"),
    Path("C:/Program Files/Steam/steamapps/common/Rocksmith2014"),
    Path.home() / "Library/Application Support/Steam/steamapps/common/Rocksmith2014",
]


def find_rocksmith():
    for p in STEAM_PATHS:
        if (p / "gears.psarc").exists():
            return p
    return None


def main():
    # Find Rocksmith install
    if len(sys.argv) > 1:
        rs_path = Path(sys.argv[1])
    else:
        rs_path = find_rocksmith()

    if not rs_path or not (rs_path / "gears.psarc").exists():
        print("Could not find Rocksmith 2014 installation.")
        print()
        print("Usage: python extract_assets.py /path/to/Rocksmith2014")
        print()
        print("Common locations:")
        for p in STEAM_PATHS:
            print(f"  {p}")
        sys.exit(1)

    gears_path = rs_path / "gears.psarc"
    print(f"Found Rocksmith at: {rs_path}")
    print(f"Reading gears.psarc...")

    # Check Pillow
    try:
        from PIL import Image
    except ImportError:
        print("Error: Pillow is required for image conversion. Install it with:")
        print("  pip install Pillow")
        sys.exit(1)

    # Output directory
    plugin_dir = Path(__file__).parent
    assets_dir = plugin_dir / "assets"
    assets_dir.mkdir(exist_ok=True)
    (assets_dir / "amps").mkdir(exist_ok=True)
    (assets_dir / "cabs").mkdir(exist_ok=True)
    (assets_dir / "pedals").mkdir(exist_ok=True)
    (assets_dir / "racks").mkdir(exist_ok=True)

    # Step 1: Extract gear images (256px, angle 0)
    print("Extracting gear images...")
    images = read_psarc(str(gears_path), ["gfxassets/tone_designer/*_0_256.dds"])
    print(f"  Found {len(images)} images")

    converted = 0
    for path, dds_data in sorted(images.items()):
        # Determine category and output name
        basename = path.split("/")[-1]  # gear_amp_en50_0_256.dds
        name = basename.replace("_0_256.dds", "")  # gear_amp_en50

        if "/amp/" in path:
            out_dir = assets_dir / "amps"
        elif "/cab/" in path:
            out_dir = assets_dir / "cabs"
        elif "/effect/" in path:
            if "rack" in name.lower():
                out_dir = assets_dir / "racks"
            else:
                out_dir = assets_dir / "pedals"
        else:
            continue

        out_file = out_dir / f"{name}.png"
        try:
            png_data = dds_to_png_pillow(dds_data)
            out_file.write_bytes(png_data)
            converted += 1
        except Exception as e:
            print(f"  Warning: Failed to convert {basename}: {e}")

    print(f"  Converted {converted} images to PNG")

    # Step 2: Extract gear manifests for name mapping
    print("Extracting gear metadata...")
    manifests = read_psarc(str(gears_path), ["manifests/gears/*.json"])

    gear_map = {}  # effect_key -> {name, category, image}
    for path, data in sorted(manifests.items()):
        try:
            j = json.loads(data)
        except json.JSONDecodeError:
            # Some manifests have trailing commas — fix and retry
            text = data.decode("utf-8", errors="ignore")
            import re
            text = re.sub(r",\s*([}\]])", r"\1", text)
            try:
                j = json.loads(text)
            except Exception:
                continue

        for k, v in j.get("Entries", {}).items():
            attrs = v.get("Attributes", {})
            name = attrs.get("Name", "")
            category = attrs.get("Category", "")
            skin = attrs.get("DefaultSkin", "")
            effects = attrs.get("Effects", [])

            if not name or not effects:
                continue

            # skin = "urn:image:dds:gear_amp_en50_0" -> image key = "gear_amp_en50"
            image_key = skin.replace("urn:image:dds:", "")
            # Remove trailing _0 (the angle/variant suffix) but not part of the name
            if image_key.endswith("_0"):
                image_key = image_key[:-2]

            for effect in effects:
                effect_name = effect.get("Name", "")
                if effect_name:
                    gear_map[effect_name] = {
                        "name": name,
                        "category": category,
                        "image": image_key,
                    }

    # Save gear mapping
    map_file = assets_dir / "gear_map.json"
    map_file.write_text(json.dumps(gear_map, indent=2))
    print(f"  Saved {len(gear_map)} gear entries to gear_map.json")

    # Summary
    amp_count = len(list((assets_dir / "amps").glob("*.png")))
    cab_count = len(list((assets_dir / "cabs").glob("*.png")))
    pedal_count = len(list((assets_dir / "pedals").glob("*.png")))
    rack_count = len(list((assets_dir / "racks").glob("*.png")))
    print()
    print(f"Extraction complete!")
    print(f"  Amps:    {amp_count}")
    print(f"  Cabs:    {cab_count}")
    print(f"  Pedals:  {pedal_count}")
    print(f"  Racks:   {rack_count}")
    print(f"  Mapping: {len(gear_map)} entries")
    print()
    print(f"Assets saved to: {assets_dir}")
    print()
    print("To install the plugin, copy this entire folder to your Slopsmith plugins directory:")
    print()
    print(f"  cp -r {plugin_dir} /path/to/slopsmith/plugins/tones")
    print()
    print("Then restart Slopsmith:")
    print()
    print("  docker compose restart")


if __name__ == "__main__":
    main()
