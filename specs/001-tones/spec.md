# Spec — Tone Player (`tones`)

> Retrospective spec for shipped v1.0.0. Implementation in `routes.py` (264
> lines), `screen.js` (218), `screen.html` (21), and `extract_assets.py`
> (299) is the source of truth.

## Summary

A Slopsmith plugin that extracts and displays Rocksmith tone presets — the
amp / cabinet / pedal signal chain used in each song — with the actual
gear artwork from the game. Users run a one-time extraction script
against their own Rocksmith 2014 install to populate the plugin's
`assets/` directory.

## User stories

### US-1 — One-time asset extraction
- **Given** a fresh checkout of the plugin,
  **When** the user runs `python extract_assets.py /path/to/Rocksmith2014`,
  **Then** ~63 amps + ~58 cabs + ~83 pedals + ~17 racks (~221 256-px PNGs)
  plus a `gear_map.json` are written to `assets/`.
  Common Steam locations are auto-discovered if no path is supplied.

### US-2 — Asset readiness check
- **Given** the user opens the Tones screen,
  **When** the client calls `GET /api/plugins/tones/assets-status`,
  **Then** the response is `{ready: true, amps, pedals, cabs}` if assets
  are present, else `{ready: false, message: "Gear assets not extracted..."}`.

### US-3 — Browse / search songs
- **Given** the user types in the search box,
  **When** `GET /api/plugins/tones/search?q=...` runs,
  **Then** the server queries `meta_db.query_page(...)` and returns the
  top 10 by artist with `{filename, title, artist}`.

### US-4 — Inspect a song's tones
- **Given** the user picks a song,
  **When** `GET /api/plugins/tones/song/{filename}` runs,
  **Then** the response contains `arrangements[]`, each with
  `{name, tones[]}`. Each tone is parsed into `{name, key, chain[]}` where
  `chain` lists every gear in signal-chain order:
  `pre_pedal × ≤4 → amp → post_pedal × ≤4 → rack × ≤4 → cabinet`.

### US-5 — Display visual signal chain
- **Given** the response,
  **When** the UI renders,
  **Then** each gear card shows the gear image (via
  `GET /api/plugins/tones/gear-image/{type}`) and its knob values.
  Vocals / ShowLights / JVocals arrangements are skipped.

### US-6 — Sloppak handling
- **Given** the song is a `.sloppak`,
  **When** the song endpoint runs,
  **Then** it returns `{arrangements: []}` without attempting PSARC
  parsing. Trailing slashes are normalised so both `foo.sloppak` and
  `foo.sloppak/` are handled.

### US-7 — JSON robustness
- **Given** a Rocksmith JSON manifest with trailing commas,
  **When** the parser runs,
  **Then** `json.loads` is tried first; on failure, trailing commas are
  stripped via regex and `json.loads` is retried. Persistent failure
  skips the entry.

## Functional requirements

| ID    | Requirement                                                                                              | Source                |
|-------|----------------------------------------------------------------------------------------------------------|-----------------------|
| FR-1  | `GET /api/plugins/tones/assets-status` returns `{ready, amps?, pedals?, cabs?}` or `{ready: false, message}`. | `routes.py`           |
| FR-2  | `GET /api/plugins/tones/gear-image/{gear_type}` returns the PNG or 404.                                   | `routes.py`           |
| FR-3  | `GET /api/plugins/tones/song/{filename:path}` parses tones from PSARC; returns `{arrangements: []}` for sloppaks. | `routes.py`           |
| FR-4  | `GET /api/plugins/tones/search?q=...` returns up to 10 song summaries via `meta_db.query_page`.            | `routes.py`           |
| FR-5  | Asset directory resolution: `SLOPSMITH_PLUGINS_DIR/tones/assets` first, then `_plugin_dir/assets`.        | `routes.py`           |
| FR-6  | Skip `Vocals`, `ShowLights`, `JVocals` arrangements.                                                       | `routes.py`           |
| FR-7  | Deduplicate tones by `Key` per arrangement.                                                                | `routes.py`           |
| FR-8  | Knob name cleanup: split on `_`, take last part as label; round float values to 1 dp.                     | `routes.py` `_parse_gear` |
| FR-9  | Gear image lookup heuristic: exact → channel-suffixed → progressively shorter prefix.                      | `routes.py` `_find_gear_image` |
| FR-10 | Robust JSON parsing with regex-stripped retry on `JSONDecodeError`.                                        | `routes.py`           |
| FR-11 | Asset extractor (`extract_assets.py`) writes to `assets/{amps,cabs,pedals,racks}/` and `assets/gear_map.json`. | `extract_assets.py`   |
| FR-12 | Extractor auto-discovers common Steam Rocksmith install locations.                                         | `extract_assets.py`   |

## Non-functional

- **Latency**: tone fetch is dominated by PSARC unpack of JSON entries.
  Typically <500 ms.
- **Disk**: extracted assets are ~30 MB.
- **Compatibility**: relies on Slopsmith core's `read_psarc_entries`.

## Out of scope

- Editing tones / writing back to PSARC.
- Audio simulation of tones (that's the NAM-tone plugin's domain).
- Bundled assets (constitution §I).

## Open clarifications

- [NEEDS CLARIFICATION] What happens when the user has a non-standard
  Rocksmith 2014 install path that the auto-discovery misses? Today they
  pass the path manually; could the plugin offer an in-app prompt?
- [NEEDS CLARIFICATION] Should the gear-image endpoint set long-cache
  headers (the assets are immutable per install)?
- [NEEDS CLARIFICATION] How should the UI surface partial extractions
  (e.g. amps but no cabs) — fall back gracefully or hard-fail?
- [NEEDS CLARIFICATION] Are there CDLC tones with > 4 pre/post pedals or
  > 4 racks today? The slot count is an assumption inherited from the
  game's UI.
