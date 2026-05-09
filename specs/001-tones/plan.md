# Plan — Tone Player (as built)

## File map

| File                  | Lines | Purpose                                                                  |
|-----------------------|-------|--------------------------------------------------------------------------|
| `plugin.json`         | 11    | Manifest. `id: tones`, version `1.0.0`, nav `Tones`, declares `screen.html`/`screen.js`/`routes.py`. |
| `routes.py`           | 264   | Asset directory resolution, gear-image lookup, tone parsing, search, four endpoints. |
| `screen.html`         | 21    | Status banner, search box, tone display container.                        |
| `screen.js`           | 218   | Search, song fetch, tone rendering with images and knob values.           |
| `extract_assets.py`   | 299   | One-time DDS → PNG extraction from a Rocksmith 2014 install.              |
| `assets/`             | (gitignored) | Output of the extractor: `amps/`, `cabs/`, `pedals/`, `racks/`, `gear_map.json`. |

## Endpoints

| Verb | Path                                       | Purpose                                              |
|------|--------------------------------------------|------------------------------------------------------|
| GET  | `/api/plugins/tones/assets-status`         | Asset readiness probe                                 |
| GET  | `/api/plugins/tones/gear-image/{type}`     | Serve a PNG for a gear type (heuristic resolution)    |
| GET  | `/api/plugins/tones/song/{filename:path}`  | Parse tones from PSARC; `[]` for sloppaks             |
| GET  | `/api/plugins/tones/search?q=...`          | Top 10 song summaries via `meta_db.query_page`        |

## Asset directory resolution

```python
def _get_assets_dir():
    user_plugins_dir = os.environ.get("SLOPSMITH_PLUGINS_DIR")
    if user_plugins_dir:
        user_assets = Path(user_plugins_dir) / "tones" / "assets"
        if user_assets.exists():
            return user_assets
    return _plugin_dir / "assets"
```

## Tone parsing flow

```
PSARC                     read_psarc_entries(*.json)
  │                           │
  ▼                           ▼
parse JSON (json.loads)  →  on JSONDecodeError, regex-strip trailing commas + retry
  │
  ▼
for each Entries[*].Attributes:
   if ArrangementName in {Vocals, ShowLights, JVocals}: skip
   for each Tones[]:
      dedupe by Key
      _parse_tone(t):
         chain = []
         for slot in PrePedal1..4: _parse_gear(...)
         for slot Amp:             _parse_gear(...)
         for slot in PostPedal1..4: _parse_gear(...)
         for slot in Rack1..4:      _parse_gear(...)
         for slot Cabinet:          _parse_gear(...)
   accumulate {name, tones[]}
```

`_parse_gear(gear, slot_type)`:
- `_extract_model_from_knobs(knobs)` finds the truest model key.
- `_find_gear_image(model_key)` resolves the image path.
- Knob names cleaned: split on `_`, last segment is the label; floats
  rounded to 1 dp.

`_find_gear_image(effect_type)`:
1. exact key in `gear_map`
2. `effect_type_0..._3` (channel variants)
3. progressively shorter prefixes derived from `effect_type.split("_")`

## Frontend flow

```
on screen mount:
  GET /assets-status
    └─► if not ready: show banner with extraction instructions

search box ─► onEnter ─► GET /search?q=
                          └─► render result list

click result ─► GET /song/{filename}
                  └─► render arrangements:
                         per tone: signal chain row of gear cards
                         per gear card: <img src="/gear-image/{type}">  + knob values
```

## Extractor (`extract_assets.py`)

- Scans Rocksmith install for relevant `.psarc` containers.
- Decrypts JSON manifests (uses `pycryptodome`).
- Decodes DDS textures (uses `Pillow`).
- Writes 256-px PNGs into `amps/`, `cabs/`, `pedals/`, `racks/`.
- Builds `gear_map.json` mapping gear keys → image filenames + display
  names.

## Risks / drift watchpoints

- **`gear_map` shape**: `_find_gear_image` and `_extract_model_from_knobs`
  both walk the gear map; renames in `extract_assets.py` propagate.
- **`read_psarc_entries` import**: relies on the core's PSARC helper. A
  rename or signature change breaks the song endpoint.
- **JSON encoding**: some manifests use UTF-16 / Latin-1; the regex retry
  uses `errors="ignore"` decode which can hide broader issues.
- **Slot count cap of 4** (Q7): unofficial CDLC may exceed this.
- **No cache headers** on gear images (Q8).
