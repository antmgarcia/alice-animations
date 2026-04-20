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
# (the authored SVG is 388×911). Cards still animate through the window.
VIEW_H = 420
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

  // Group each card (the <g clip-path> + following border <rect>) into a wrapper <g>
  // so both move together under GSAP transforms.
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

  // Geometry: cards authored at y = 1.5 + i * 186, each 173 tall.
  var CARD_X = 194;           // 388 / 2
  var CARD_H = 173;
  var CARD_TOPS = [1.5, 187.5, 373.5, 559.5, 745.5];
  var CARD_CENTERS = CARD_TOPS.map(function(t) { return t + CARD_H / 2; });

  // Pin rotation/scale origins to each card's own center so transforms feel local.
  cards.forEach(function(c, i) {
    gsap.set(c, { svgOrigin: CARD_X + ' ' + CARD_CENTERS[i] });
  });

  var tl = gsap.timeline({ repeat: -1, repeatDelay: 0.2, defaults: { ease: 'power3.out' } });

  // Reset each loop
  tl.set(cards, { y: 220, x: -14, opacity: 0, scale: 0.86, rotation: function(i) { return i % 2 ? 2.5 : -2.5; } });

  // 1. DEAL-IN — cards spring up from below with a diagonal sway that corrects
  //    to level. back.out overshoot gives the stack real weight.
  tl.to(cards, {
    y: 0, x: 0, opacity: 1, scale: 1, rotation: 0,
    duration: 1.05,
    stagger: { each: 0.085, from: 'start' },
    ease: 'back.out(1.7)',
  }, 0.05);

  // 2. FOCAL SWEEP — a soft scale pulse travels top→bottom like a highlight
  //    passing down the stack. Much livelier than a static hold.
  tl.to(cards, {
    scale: 1.045,
    duration: 0.32,
    stagger: { each: 0.11, from: 'start' },
    ease: 'power2.out',
    yoyo: true,
    repeat: 1,
  }, '+=0.35');

  // 3. PARALLAX LIFT-OFF — stack drifts up and dissolves with wave-like stagger
  //    and a faint rotation so motion feels loose rather than rigid.
  tl.to(cards, {
    y: function(i) { return -(CARD_TOPS[i] + CARD_H + 80); },
    opacity: 0,
    scale: 0.93,
    rotation: function(i) { return i % 2 ? -1.8 : 1.8; },
    duration: 1.25,
    stagger: { each: 0.06, from: 'start' },
    ease: 'power3.in',
  }, '+=0.45');
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
