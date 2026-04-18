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
    cards.push({ wrap: wrapper, clip: g, border: border });
  });

  // Card 0 is authored as the "selected" variant (dark border, filled checkbox
  // with white checkmark). Every other card has an empty checkbox (a translucent
  // circle + a stroked inner ring). The animation transfers the selected state
  // to the center card (index 2).

  // Find the checkbox bits inside each card. The selected card has:
  //   rect[fill="#172031"] (filled dark circle) + a <path fill="white"> checkmark
  // Unselected cards have:
  //   rect[fill="#172031"][fill-opacity="0.1"] + rect[stroke="#172031"] ring
  function getCheckbox(card) {
    var children = Array.prototype.slice.call(card.clip.children);
    var filled = null, checkmark = null, faded = null, ring = null;
    children.forEach(function(el) {
      if (el.tagName.toLowerCase() === 'rect' && el.getAttribute('rx') === '12') {
        if (el.getAttribute('fill-opacity') === '0.1') faded = el;
        else if (el.getAttribute('fill') === '#172031' && !el.hasAttribute('fill-opacity')) filled = el;
      } else if (el.tagName.toLowerCase() === 'rect' && el.getAttribute('rx') === '11') {
        ring = el;
      } else if (el.tagName.toLowerCase() === 'path' && el.getAttribute('fill') === 'white'
                 && el.getAttribute('d') && el.getAttribute('d').indexOf('M27.683') === 0) {
        checkmark = el;
      } else if (el.tagName.toLowerCase() === 'path' && el.getAttribute('fill') === 'white'
                 && el.getAttribute('d') && /^M\d+\.\d+ \d+\.\d+L\d+\.\d+ \d+\.\d+C/.test(el.getAttribute('d'))) {
        // heuristic: short-ish white path near top (checkmark). Skip.
      }
    });
    return { filled: filled, checkmark: checkmark, faded: faded, ring: ring };
  }

  var checkboxes = cards.map(getCheckbox);

  // Build a synthetic "unselected" look for card 0: hide the filled dark circle
  // and checkmark, inject a translucent circle + ring matching the other cards.
  var card0 = cards[0];
  var cb0 = checkboxes[0];
  var card0Faded = null, card0Ring = null;
  if (cb0.filled) {
    card0Faded = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    card0Faded.setAttribute('x', '19');
    card0Faded.setAttribute('y', '19');
    card0Faded.setAttribute('width', '24');
    card0Faded.setAttribute('height', '24');
    card0Faded.setAttribute('rx', '12');
    card0Faded.setAttribute('fill', '#172031');
    card0Faded.setAttribute('fill-opacity', '0.1');
    cb0.filled.parentNode.insertBefore(card0Faded, cb0.filled);

    card0Ring = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    card0Ring.setAttribute('x', '20');
    card0Ring.setAttribute('y', '20');
    card0Ring.setAttribute('width', '22');
    card0Ring.setAttribute('height', '22');
    card0Ring.setAttribute('rx', '11');
    card0Ring.setAttribute('stroke', '#172031');
    card0Ring.setAttribute('stroke-opacity', '0.4');
    card0Ring.setAttribute('stroke-width', '2');
    card0Ring.setAttribute('fill', 'none');
    cb0.filled.parentNode.insertBefore(card0Ring, cb0.filled);
  }

  // Same for card 2 (center): inject a filled dark circle + white checkmark that
  // we can fade in during the "select" phase.
  var cb2 = checkboxes[2];
  var card2Filled = null, card2Checkmark = null;
  if (cb2.faded) {
    card2Filled = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    card2Filled.setAttribute('x', '19');
    card2Filled.setAttribute('y', '391');
    card2Filled.setAttribute('width', '24');
    card2Filled.setAttribute('height', '24');
    card2Filled.setAttribute('rx', '12');
    card2Filled.setAttribute('fill', '#172031');
    cb2.faded.parentNode.appendChild(card2Filled);

    card2Checkmark = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    // Checkmark glyph offset for y=391 checkbox (card1 checkbox is at y=19, this
    // one at y=391, so shift path by 372 downward). Source d starts at M27.683 35.014.
    card2Checkmark.setAttribute('d', 'M27.683 407.014L24.3013 403.6323C23.9245 403.2555 23.3254 403.2555 22.9486 403.6323C22.5718 404.0091 22.5718 404.6082 22.9486 404.985L26.997 409.0334C27.3738 409.4102 27.9825 409.4102 28.3594 409.0334L38.6011 398.8013C38.9779 398.4245 38.9779 397.8254 38.6011 397.4486C38.2243 397.0718 37.6253 397.0718 37.2484 397.4486L27.683 407.014Z');
    card2Checkmark.setAttribute('fill', 'white');
    cb2.faded.parentNode.appendChild(card2Checkmark);
  }

  // Card 0's border rect is the only one with stroke #172031 + stroke-width 3.
  // Card 2's border is light (#EDEDED, stroke-width 2). We'll fade the dark
  // border out of card 0 and morph card 2's border to dark.
  var card0Border = card0.border;
  var card2Border = cards[2].border;

  // Initial state: hide dark styling on card 0, show unselected; card 2 neutral.
  gsap.set(card0Faded, { opacity: 0 });
  gsap.set(card0Ring, { opacity: 0 });
  gsap.set(cb0.filled, { opacity: 1 });
  gsap.set(cb0.checkmark, { opacity: 1 });
  gsap.set(card0Border, { opacity: 1 });

  gsap.set(card2Filled, { opacity: 0 });
  gsap.set(card2Checkmark, { opacity: 0 });

  // Entrance: all cards slide up from below with a stagger, center card
  // scales in slightly larger.
  cards.forEach(function(c, i) {
    gsap.set(c.wrap, { y: 80, opacity: 0, transformOrigin: '194px ' + (93 + i * 186) + 'px' });
  });

  function build() {
    var tl = gsap.timeline({ repeat: -1, repeatDelay: 0.4 });

    // Reset (also runs at start of each loop iteration after the first)
    tl.set(cards.map(function(c) { return c.wrap; }), { y: 80, opacity: 0, scale: 1 });
    tl.set(card0Faded, { opacity: 0 });
    tl.set(card0Ring, { opacity: 0 });
    tl.set(cb0.filled, { opacity: 1 });
    tl.set(cb0.checkmark, { opacity: 1 });
    tl.set(card0Border, { opacity: 1 });
    tl.set(card2Filled, { opacity: 0 });
    tl.set(card2Checkmark, { opacity: 0 });
    tl.set(cards[2].wrap, { scale: 1 });

    // 1. Slide cards up with stagger
    tl.to(cards.map(function(c) { return c.wrap; }), {
      y: 0,
      opacity: 1,
      duration: 0.7,
      stagger: 0.08,
      ease: 'power3.out'
    });

    // 2. Pause briefly so viewer sees the initial list
    tl.to({}, { duration: 0.6 });

    // 3. Transfer selection to center card + scale it up
    tl.to(cb0.checkmark, { opacity: 0, duration: 0.25, ease: 'power2.in' }, '+=0');
    tl.to(cb0.filled, { opacity: 0, duration: 0.25, ease: 'power2.in' }, '<');
    tl.to([card0Faded, card0Ring], { opacity: 1, duration: 0.25, ease: 'power2.out' }, '>');
    tl.to(card0Border, { opacity: 0, duration: 0.3, ease: 'power2.inOut' }, '<');

    tl.to(cards[2].wrap, {
      scale: 1.04,
      duration: 0.5,
      ease: 'back.out(1.4)',
      transformOrigin: '194px 460px'
    }, '-=0.15');
    tl.to(card2Filled, { opacity: 1, duration: 0.25, ease: 'power2.out' }, '-=0.3');
    tl.to(card2Checkmark, { opacity: 1, duration: 0.2, ease: 'power2.out' }, '-=0.1');
    // Morph card 2's light border into the dark selected border look
    tl.to(card2Border, {
      attr: { stroke: '#172031', 'stroke-width': 3 },
      duration: 0.3,
      ease: 'power2.inOut'
    }, '-=0.4');

    // 4. Hold the selected state
    tl.to({}, { duration: 1.6 });

    // 5. Exit: slide all cards back down and reset
    tl.to(cards.map(function(c) { return c.wrap; }), {
      y: 40,
      opacity: 0,
      duration: 0.5,
      stagger: 0.05,
      ease: 'power2.in'
    });
    tl.to(card2Border, {
      attr: { stroke: '#EDEDED', 'stroke-width': 2 },
      duration: 0.01
    }, '>');

    return tl;
  }

  build();
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

for fname in ['index.html', 'index-dark.html']:
    with open(os.path.join(here, fname), 'w') as f:
        f.write(html)
    print(f"Built {fname}: {len(html)//1024} KB")
print("Done!")
