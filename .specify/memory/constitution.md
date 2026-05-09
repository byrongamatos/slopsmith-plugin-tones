# Tone Player — Constitution

## Inheritance

Slopsmith's core plugin contract governs everything in this repo (manifest,
plugin context: `get_dlc_dir`, `meta_db`, navigation, asset serving). This
constitution lists Tone Player's own non-negotiables.

## Core Principles

### I. Assets are user-supplied, never bundled
Gear images (amps, cabinets, pedals, racks) are property of Ubisoft. They
are extracted from the user's own legally-purchased Rocksmith 2014 install
via `extract_assets.py`. The repository MUST NOT commit DDS / PNG gear
assets. The `assets/` directory is gitignored.

### II. Asset directory resolution: user dir first, bundled second
`_get_assets_dir()` checks `SLOPSMITH_PLUGINS_DIR/tones/assets` first
(populated by `slopsmith-desktop` users) and falls back to the plugin's
`assets/` directory inside the repo. This order MUST be preserved so a
user-extracted asset set always wins.

### III. PSARC-only tone source; sloppaks have no tones
Sloppaks (`*.sloppak`) are stripped to stems + arrangement JSON and carry
no tone manifest. The endpoint MUST return `{arrangements: []}` rather
than feeding the file into `read_psarc_entries` (which 500s on the magic-
byte check). PSARC files are the sole tone source.

### IV. Tone parsing is shape-tolerant
Rocksmith JSON manifests are inconsistent (trailing commas, mixed
encodings). The parser falls back from `json.loads` to a regex-stripped
retry. New robustness rules belong in `_parse_tone` / `_parse_gear`, not
in the endpoint.

### V. Gear name → image is heuristic
`_find_gear_image` tries: exact key → suffixed channel variants
(`_0..._3`) → progressively shorter prefixes derived from knob-name
parts. Adding a new heuristic MUST stay in this function and MUST NOT
introduce per-tone special cases.

### VI. Read-only and stateless
The plugin reads CDLC metadata and gear assets; it writes nothing to the
filesystem or DB. Removing the plugin removes the feature with no
residual state.

## Governance

Asset extraction (`extract_assets.py`) is a developer / power-user tool.
Users MUST run it once before the plugin is functional. The README's
"Setup" section is the canonical install procedure. Changes to gear name
parsing MUST be tested against representative tone manifests.

**Version**: 1.0.0 | **Ratified**: 2026-05-09 | **Last Amended**: 2026-05-09
