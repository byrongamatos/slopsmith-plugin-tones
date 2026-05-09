# Tasks — Tone Player

Status legend: `DONE` (shipped in v1.0.0), `OPEN` (not yet implemented), `[P]` (parallelisable).

## US-1 — Asset extraction
- [DONE] `extract_assets.py` decodes DDS → 256-px PNG.
- [DONE] Common Steam path auto-discovery.
- [DONE] Outputs amps / cabs / pedals / racks + gear_map.json.

## US-2 — Asset readiness probe
- [DONE] `/assets-status` returns counts when ready, message otherwise.

## US-3 — Search
- [DONE] `/search?q=` calls `meta_db.query_page`, returns top 10.
- [DONE] Frontend search box wires Enter key.

## US-4 — Inspect tones
- [DONE] `/song/{filename}` walks Entries / Attributes / Tones.
- [DONE] Skip vocals / showlights / JVocals.
- [DONE] Dedupe by tone Key.

## US-5 — Display signal chain
- [DONE] Frontend renders gear cards with image + knobs.
- [DONE] Gear images served by `/gear-image/{type}`.

## US-6 — Sloppak handling
- [DONE] Return `{arrangements: []}` for sloppaks.
- [DONE] Trailing-slash normalisation.

## US-7 — JSON robustness
- [DONE] regex-strip trailing commas + retry on `JSONDecodeError`.

## Cross-cutting
- [DONE] `_get_assets_dir` resolution order.
- [DONE] `_extract_model_from_knobs` heuristic.
- [DONE] `_find_gear_image` with channel variants and prefix walk.
- [OPEN] [P] Cache-Control headers on gear images (Q8).
- [OPEN] [P] In-app prompt for non-standard Rocksmith install paths.
- [OPEN] [P] Surface partial-extraction state (e.g. amps but no pedals).
- [OPEN] Investigate slot counts > 4 in third-party CDLC (Q7).
- [OPEN] Tests: unit-test `_find_gear_image` and `_parse_tone` against
  fixture manifests.
