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

  // Each card's natural top sits at y = 1.5 + i * 186. To clear the top edge of
  // the 911-unit viewBox, a card needs to travel upward by at least
  // (its top + its height) => cards[i] needs y: -(1.5 + i*186 + 173). We use a
  // single list-wide shift (-920) so all cards leave together.
  var EXIT_Y = -920;

  gsap.set(cards, { y: 80, opacity: 0 });

  var tl = gsap.timeline({ repeat: -1, repeatDelay: 0.2 });

  // Reset at the start of every loop
  tl.set(cards, { y: 80, opacity: 0 });

  // 1. Cards slide up into place with a stagger (entrance the user liked)
  tl.to(cards, {
    y: 0,
    opacity: 1,
    duration: 0.7,
    stagger: 0.08,
    ease: 'power3.out'
  });

  // 2. Brief hold so the list settles
  tl.to({}, { duration: 0.8 });

  // 3. Whole list drifts upward so each card passes through the framed view.
  //    Framer will clip the iframe to a viewport showing one "main" card —
  //    the steady upward motion cycles the selection through that window.
  tl.to(cards, {
    y: EXIT_Y,
    duration: 3.2,
    ease: 'none'
  });

  // 4. A beat of empty before the loop restarts
  tl.to({}, { duration: 0.3 });
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
#stage{{position:relative;width:100%;height:100%;max-width:388px;max-height:911px}}
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
