# Analyze — Tone Player

## Coverage

| Area              | Spec | Plan | Code               | Notes                                  |
|-------------------|------|------|--------------------|----------------------------------------|
| Asset extractor   | ✅   | ✅   | `extract_assets.py`| One-time DDS → PNG                     |
| Status probe      | ✅   | ✅   | `routes.py`        | counts + readiness                     |
| Tone parsing      | ✅   | ✅   | `routes.py`        | PSARC walk, dedupe, robust JSON        |
| Image serving     | ✅   | ✅   | `routes.py`        | heuristic resolution                   |
| Search            | ✅   | ✅   | `routes.py`        | top 10 via `meta_db`                   |
| Frontend display  | ✅   | ✅   | `screen.html` + JS | search → results → chain               |
| Sloppak handling  | ✅   | ✅   | `routes.py`        | `[]` short-circuit                     |
| Tests             | ❌   | ❌   | —                  | None automated                         |

## Drift

- README's "What gets extracted" table matches `extract_assets.py` output.
- README's "Step 3" instruction matches `_get_assets_dir` precedence.
- README warns the assets are property of Ubisoft; constitution §I aligns.

## Gaps

1. **No cache headers** on gear images (Q8). Repeat fetches re-roundtrip.
2. **Hard-cap 4 slots** for pedals / racks (Q7). Third-party CDLC may
   silently drop gear.
3. **JSON regex fallback** is fragile; non-trailing-comma issues fail.
4. **No tests** for `_find_gear_image` or `_parse_tone`.
5. **No surfacing of partial extractions** (e.g. amps directory empty
   but pedals populated). Today the user sees broken images.
6. **No fuzzy gear-name search** in the UI — just artist/title song
   search.

## Recommendations

- **Add `Cache-Control: public, max-age=31536000, immutable`** on the
  gear-image responses. The PNGs never change for a given install.
- **Lift the slot cap behind a sentinel** — iterate on slot keys present
  rather than `1..4`. If `gear_list` ever has `Pedal5`, surface it.
- **Replace regex JSON repair** with a JSON5 / json-tricks dependency
  (or inline a tiny tolerant parser) — covers more shape errors.
- **Unit-test `_find_gear_image`** with a fixture `gear_map.json` and
  expected lookups for the heuristic chain.
- **UX for partial extractions**: status probe could break out per
  category counts and the UI could warn when one is empty.
- **Gear-name search**: add a `?gear=DS1` query that returns songs whose
  tones include that gear — useful for "who uses a Marshall JCM 800?".
