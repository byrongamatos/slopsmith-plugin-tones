# Slopsmith Plugin: Tone Player

A plugin for [Slopsmith](https://github.com/byrongamatos/slopsmith) that extracts and displays Rocksmith tone presets — the amp, cabinet, and pedal signal chain used in each song — with the actual gear images from the game.

## Features

- **Visual signal chain** — shows each pedal, amp, and cabinet with the game's own gear artwork
- **Knob values** — displays every knob setting for each piece of gear
- **Per-song tones** — view all tones used in a song's arrangement (clean, crunch, lead, etc.)
- **Tone browser** — browse all tones across your library

## Setup

This plugin requires images extracted from your own Rocksmith 2014 installation. The images are **not included** in this repository.

### Step 1: Clone the plugin

```bash
git clone https://github.com/byrongamatos/slopsmith-plugin-tones.git
cd slopsmith-plugin-tones
```

### Step 2: Install Python dependencies

```bash
pip install pycryptodome Pillow
```

### Step 3: Extract gear assets

Run the extraction script, pointing it to your Rocksmith installation:

```bash
python extract_assets.py /path/to/Rocksmith2014
```

Common locations:
- **Linux**: `~/.local/share/Steam/steamapps/common/Rocksmith2014`
- **Windows**: `C:\Program Files (x86)\Steam\steamapps\common\Rocksmith2014`
- **macOS**: `~/Library/Application Support/Steam/steamapps/common/Rocksmith2014`

If Rocksmith is in a standard Steam location, the script will find it automatically:

```bash
python extract_assets.py
```

The script extracts ~220 gear images (amps, cabinets, pedals, rack effects) and a gear mapping file into the `assets/` folder.

### Step 4: Install the plugin

Copy the entire folder (with extracted assets) to your Slopsmith plugins directory:

```bash
cp -r /path/to/slopsmith-plugin-tones /path/to/slopsmith/plugins/tones
docker compose restart
```

## What Gets Extracted

| Type   | Count | Description                          |
|--------|-------|--------------------------------------|
| Amps   | ~63   | Amp head images                      |
| Cabs   | ~58   | Speaker cabinet images               |
| Pedals | ~83   | Stompbox pedal images                |
| Racks  | ~17   | Rack effect unit images              |
| Map    | ~917  | Gear name to image/display name mapping |

All images are 256px PNGs converted from the game's DDS textures.

## License

MIT

Note: The extracted gear images are from Rocksmith 2014 and are property of Ubisoft. They are extracted from your own legally purchased copy of the game for personal use only. Do not redistribute the extracted assets.
