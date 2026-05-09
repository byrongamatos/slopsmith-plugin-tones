# Clarifications — Tone Player

## Q1 — Why ship the extractor instead of bundling the assets?
**Resolved.** The gear images are property of Ubisoft. Bundling would be a
copyright violation. Each user runs `extract_assets.py` against their own
installation. README's "Setup" section is the canonical procedure.
Constitution §I.

## Q2 — Why two asset directories (user-supplied vs bundled)?
**Resolved.** `slopsmith-desktop` users may want to keep extracted assets
outside the plugin source tree. `SLOPSMITH_PLUGINS_DIR/tones/assets` is
checked first; the plugin's own `assets/` is the fallback. Constitution
§II.

## Q3 — Why does `_extract_model_from_knobs` exist alongside `gear.Type`?
**Resolved.** The CDLC `Type` is sometimes generic (e.g. `Pedal_Distortion`)
while the knob names embed the actual model (e.g. `Pedal_DS1_Gain`). The
plugin walks knob prefixes against `gear_map` to find the truest model
key, falling back to the raw `Type` when nothing matches.

## Q4 — Why dedupe tones by `Key`?
**Resolved.** Some CDLC reuse the same tone across multiple section
references. Without dedup the chain would render N times.

## Q5 — Why skip Vocals / ShowLights / JVocals?
**Resolved.** These arrangements have no playable signal chain. Leaving
them in produces empty cards that confuse users.

## Q6 — Why is the JSON parser regex-fallback?
**Resolved.** Rocksmith's manifests have known issues — trailing commas
inside `Tones` arrays in particular. `json.loads` is strict; the
regex-stripped retry tolerates the most common shape issue without a full
JSON5 dependency.

## Q7 — Why are slot counts capped at 4?
**Resolved.** Mirrors Rocksmith 2014's UI. CDLC built outside the official
toolchain might exceed this; today they would silently drop. Open in
spec.

## Q8 — Open: cache headers on the gear-image endpoint?
**Open.** Today every navigation re-fetches the same PNGs (browsers may
cache anyway via 304). Adding `Cache-Control: public, max-age=…` would
improve repeat loads.

## Q9 — What about user-installed gear or custom amp models?
**Resolved.** Out of scope; the plugin only knows what `gear_map.json`
declares. Custom gear would need a contribution to `extract_assets.py`.
