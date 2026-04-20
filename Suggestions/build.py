#!/usr/bin/env python3
"""Build self-contained Suggestions animation HTML.

Inlines the single SVG + GSAP + animation JS into index.html (also copies to
index-dark.html for a stable embed URL). Transparent background so the iframe
can be placed on any colored Frame in Framer.
"""
import os

here = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(here, 'Suggestion_cards.svg')) as f:
    svg = f.read()

# Clip the outer SVG to a shorter viewport so the iframe isn't abnormally tall
# (the authored SVG is 388×911). 560 fits three full cards top-to-bottom
# without cropping any of them mid-animation.
VIEW_H = 560
svg = svg.replace(
    '<svg width="388" height="911" viewBox="0 0 388 911"',
    f'<svg width="388" height="{VIEW_H}" viewBox="0 0 388 {VIEW_H}"',
)

with open(os.path.join(here, 'gsap.min.js')) as f:
    gsap = f.read()

animation_js = r'''
(function() {
  var svg = document.querySelector('#stage svg');
  if (!svg) return;

  // Group each card (the <g clip-path> + following border <rect>) into a wrapper <g>.
  var clipGroups = Array.prototype.slice.call(svg.querySelectorAll('g[clip-path]'));
  var cards = [];
  clipGroups.forEach(function(g, i) {
    var border = g.nextElementSibling;
    var wrapper = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    wrapper.setAttribute('class', 'card-wrap');
    wrapper.setAttribute('data-card', i);
    g.parentNode.insertBefore(wrapper, g);
    wrapper.appendChild(g);
    if (border && border.tagName.toLowerCase() === 'rect') wrapper.appendChild(border);
    cards.push(wrapper);
  });

  // Geometry
  var CARD_X = 194;
  var CARD_H = 173;
  var CARD_STRIDE = 186;
  var CARD_TOPS = [1.5, 187.5, 373.5, 559.5, 745.5];

  // Scale origins at each card's own center so the focal pulse feels local.
  cards.forEach(function(c, i) {
    gsap.set(c, { svgOrigin: CARD_X + ' ' + (CARD_TOPS[i] + CARD_H / 2) });
  });

  // Focal line sits at the vertical center of the visible window. Cards
  // passing through it get a subtle scale pulse — the motion lands where
  // the viewer is looking.
  var FOCAL_Y = 280;
  var DRIFT_END = -(5 * CARD_STRIDE);  // whole list past the top
  var DRIFT_DURATION = 5.6;

  var tl = gsap.timeline({ repeat: -1 });

  // Reset
  tl.set(cards, { y: 120, opacity: 0, scale: 1 });

  // 1. ENTRY — snappy expo.out, tight stagger. No rotation, no diagonal:
  //    keep it clean so the composition reads instantly.
  tl.to(cards, {
    y: 0,
    opacity: 1,
    duration: 0.9,
    stagger: 0.07,
    ease: 'expo.out',
  });

  // 2. SETTLE — short breath before the list starts moving.
  tl.to({}, { duration: 0.35 });

  // 3. DRIFT — whole list translates upward with a soft in/out ease
  //    (the drift itself is the main visible event inside the clipped frame).
  tl.to(cards, {
    y: '+=' + DRIFT_END,
    duration: DRIFT_DURATION,
    ease: 'power1.inOut',
  }, 'drift+=0');

  // 4. FOCAL PULSES — as each card crosses FOCAL_Y during the drift it gets a
  //    brief scale-up + settle. Pulses are scheduled at the exact moment the
  //    card's center reaches FOCAL_Y, so all the motion plays inside the clip.
  cards.forEach(function(c, i) {
    var startY = CARD_TOPS[i] + CARD_H / 2;       // where this card's center starts
    var targetDelta = startY - FOCAL_Y;            // how far upward until it reaches focal
    // Inverse of power1.inOut to find time: approximate with progress = delta / |DRIFT_END|
    var progress = Math.min(1, Math.max(0, targetDelta / Math.abs(DRIFT_END)));
    // power1.inOut approx inverse: t = 0.5 - 0.5*sqrt(1 - 2p) for p<=0.5, symmetrical above
    var t = progress <= 0.5
      ? 0.5 - 0.5 * Math.sqrt(Math.max(0, 1 - 2 * progress))
      : 0.5 + 0.5 * Math.sqrt(Math.max(0, 2 * progress - 1));
    var pulseAt = 'drift+=' + (t * DRIFT_DURATION);

    tl.to(c, { scale: 1.055, duration: 0.32, ease: 'power2.out' }, pulseAt)
      .to(c, { scale: 1, duration: 0.4, ease: 'power2.inOut' });
  });

  // 5. FADE / RESET — once the stack has cleared the visible area, gentle fade
  //    to zero and the timeline restarts.
  tl.to(cards, { opacity: 0, duration: 0.35, ease: 'power1.in' }, '>-0.1');
})();
'''

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Suggestions</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:100%;height:100%;overflow:hidden;background:transparent}}
body{{display:flex;justify-content:center;align-items:center}}
#stage{{position:relative;width:100%;height:100%;max-width:388px;max-height:{VIEW_H}px}}
#stage svg{{width:100%;height:100%;display:block}}
</style>
</head>
<body>
<div id="stage">
{svg}
</div>
<script>
{gsap}
</script>
<script>
{animation_js}
</script>
</body>
</html>'''

for fname in ['index.html', 'index-dark.html', 'cards.html']:
    with open(os.path.join(here, fname), 'w') as f:
        f.write(html)
    print(f"Built {fname}: {len(html)//1024} KB")
print("Done!")
