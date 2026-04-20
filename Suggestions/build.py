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

# Authored SVG is 388×911 (all 5 cards). Add top padding above the first card
# so the card is vertically centered when embedded in the target iframe.
TOP_PAD = 90
VIEW_H = 911 + TOP_PAD
svg = svg.replace(
    '<svg width="388" height="911" viewBox="0 0 388 911"',
    f'<svg width="388" height="{VIEW_H}" viewBox="0 -{TOP_PAD} 388 {VIEW_H}"',
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

  var tl = gsap.timeline({ repeat: -1, repeatDelay: 0.4 });

  // Reset — cards start below and slightly askew for a hand-placed feel.
  tl.set(cards, {
    y: 220,
    x: -14,
    opacity: 0,
    scale: 0.86,
    rotation: function(i) { return i % 2 ? 2.5 : -2.5; },
  });

  // 1. DEAL-IN — cards spring up from below with a diagonal sway that
  //    corrects to level. back.out overshoot gives the stack real weight.
  tl.to(cards, {
    y: 0, x: 0, opacity: 1, scale: 1, rotation: 0,
    duration: 1.05,
    stagger: { each: 0.085, from: 'start' },
    ease: 'back.out(1.7)',
  }, 0.05);

  // 2. FOCAL SWEEP — a subtle scale wave passes through the stack while the
  //    cards are still fixed. Pulse stays at 1.025 so no edges extend past
  //    the card's natural bounds.
  tl.to(cards, {
    scale: 1.025,
    duration: 0.35,
    stagger: { each: 0.12, from: 'start' },
    ease: 'power2.out',
    yoyo: true,
    repeat: 1,
  }, '+=0.35');

  // 3. SETTLE — short beat before the scroll starts.
  tl.to({}, { duration: 0.45 });

  // 4. SCROLL — with cards fixed at their natural positions, the whole stack
  //    now scrolls upward off the viewport. This is the only translate phase,
  //    so there's no zoom happening at the same time.
  tl.to(cards, {
    y: -(5 * CARD_STRIDE),
    duration: 1.6,
    ease: 'power2.in',
  });
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
