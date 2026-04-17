# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Overview

**Alice Animations** — a static site hosting two animated SVG sequences built with GSAP 3.12.7 and vanilla JS:

- **SmartCharging** — 5-scene loop for EV charging flows (`/SmartCharging/`)
- **SmartThermo** — 5-scene loop for thermostat controls, including an animated fox (`/SmartThermo/`)

Each sequence ships as self-contained HTML (SVGs + GSAP inlined, no external requests). Two variants per sequence: `index-dark.html` and `index-light.html`. A landing page at the repo root (`index.html`) embeds both as live iframe previews.

Primary use case: **iframe embedding in Framer**. `vercel.json` sets permissive `X-Frame-Options: ALLOWALL` + `frame-ancestors *` headers so embedders aren't blocked.

## Deployment

Deployed on Vercel as a single project at repo root (not per-subdir). Production URL:

```
https://alice-animations.vercel.app
```

- `/` → landing page with live previews
- `/SmartCharging/index-dark.html` → charging, dark
- `/SmartCharging/index-light.html` → charging, light
- `/SmartThermo/index-dark.html` → thermo, dark
- `/SmartThermo/index-light.html` → thermo, light

`index.html` and `index-dark.html` are identical files per sequence — the explicit `-dark` name exists so Framer (and other embedders) always have a stable named URL.

## How to View / Test

No dev server needed — all HTML is self-contained:

```bash
open index.html                              # landing page
open SmartCharging/index-dark.html
open SmartThermo/index-dark.html
```

## File Structure

```
/
├─ index.html                   ← landing page (dark palette, matches SVG bg #2E3749)
├─ vercel.json                  ← permissive iframe CSP headers
├─ SmartCharging/
│  ├─ SmartCharging - 0[1-5].svg   (698×627; scenes 01, 02 embed raster images)
│  ├─ gsap.min.js
│  ├─ index.html                   (dark; hand-edited)
│  ├─ index-dark.html              (identical copy of index.html for stable URL)
│  └─ index-light.html             (light variant)
└─ SmartThermo/
   ├─ Smart Thermo - 0[1-5].svg
   ├─ gsap.min.js
   ├─ build.py                     (generates all three HTML files)
   ├─ index.html / index-dark.html
   └─ index-light.html
```

## Build Process

**SmartThermo** has a Python build script (`SmartThermo/build.py`) that:
1. Reads all 5 SVGs + `gsap.min.js`
2. Inlines them into HTML with the animation JS
3. Writes `index.html`, `index-dark.html` (copy), and `index-light.html` (prepends `fixLightColors()` remapper)

Run: `cd SmartThermo && python3 build.py`

**SmartCharging** was hand-edited; no build script. If SVGs or animation JS change, edit the HTML files directly.

## Animation System (applies to both sequences)

Each scene is a function (`s1()` … `s5()`) returning a GSAP timeline. `buildMaster()` chains them with `repeat: -1`. Scene transitions: enter → hold → exit → next.

Element selection uses **index-based slicing** on `directChildren(sceneNum)` — direct children of each SVG excluding `<defs>`.

### SmartCharging element indices

| Scene | Notes |
|-------|-------|
| 1 | ch[5-12] lines, ch[1] title, ch[2-4] ellipses, ch[13] bolt, ch[14] image |
| 2 | ch[1-2] arcs, ch[3-5] toggle, ch[6-8] search, ch[9] image |
| 3 | ch[2-5] card1, ch[6-10] card2, ch[11-15] card3, ch[16-17] close |
| 4 | ch[8-14] rows, ch[2-4] left card, ch[5-7] right card, ch[15-18] badges |
| 5 | ch[2-28] bars, ch[29-30] main bubbles, ch[31-34] chat, ch[37-47] face, ch[48-55] labels |

### SmartThermo element indices (from `build.py`)

| Scene | Notes |
|-------|-------|
| 1 | ch[2-4] ellipses, ch[5-12] lines, ch[13] bolt, ch[14] image |
| 2 | ch[1-3] card1, ch[4-6] card2, ch[7-12] card3; animated green progress bar via pattern matrix |
| 3 | ch[2] slider bar, ch[30] indicator, ch[31-33] balloon/text/bigNum, ch[34-35] gray ticks |
| 4 | ch[2] toggleTrack, ch[3] leftCircle, ch[13] rightCircle, ch[14] sparkle, ch[15] dashedLine, ch[16-17] bubble |
| 5 | ch[2] bigHeart, ch[3-7,32-34] route lines/circles, ch[8] heartBg, ch[9-29] fox (animated as single unit) |

## Light Mode Strategy

Global safe remap handles backgrounds and grays. **Does not** globally remap `white` or `#F5F5F5` — they need per-scene context (`white` is the fox face in one scene, a bell icon in another).

SmartCharging per-scene fixes:
- Scene 3: bell icon `white` → `#334155`
- Scene 4: value text `#F5F5F5` → `#1E293B`
- Scene 5: fox face `white` stays white; "20" bubble → `#E8F0FE`; text `#364157` → `#475569`

SmartThermo `fixLightColors()` is in `build.py` — regenerates on each build.

## Key Constraints

- SVG elements with native `transform="rotate(...)"` (e.g., SmartCharging scene 3 card tilts): **do not animate `rotation`** with GSAP — it overrides the native transform. Use `x`/`y`/`opacity` only.
- SmartCharging scene 2 toggle: knob travels exactly 44px right; label fades out as knob slides over it.
- SmartCharging scene 1 ellipses: enter from bottom (`y: 80` → `y: 0`), not center scale.
- SmartThermo scene 2 progress bar: the green stripe is a pattern at `translateY(0.372) scaleY(0.0256)` of the rect — animations on "top of the bar" must compute `stripeTop = bbox.y + bbox.height * 0.372` and `stripeHeight = bbox.height * 0.256`.
- SmartThermo scene 3 slider: the slider **stays static**; only the blue circle indicator moves along it.
- SmartThermo scene 5 fox: animate as a single unit via `opacity` + `y` offset only — per-path `scale` distorts the fox because each path has its own local origin.
