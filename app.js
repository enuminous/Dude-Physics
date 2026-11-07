/* No network calls. Editorial labels are fixed explanations, not scientific outputs. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else { root.DudePhysics = api; api.mount(root.document, root.DUDE_INVENTORY || []); }
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function normalize(value) {
    return String(value == null ? '' : value).normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  }
  function filterInventory(items, options = {}) {
    const terms = normalize(options.query).split(/\s+/).filter(Boolean);
    return items.filter(item => {
      if (options.category && options.category !== 'all' && item.category !== options.category) return false;
      if (options.reading && options.reading !== 'all' && item.reading !== options.reading) return false;
      const haystack = normalize([item.id, item.name, item.category, item.connection, item.reading].join(' '));
      return terms.every(term => haystack.includes(term));
    });
  }
  const claims = Object.freeze({
    composition: Object.freeze({ label: 'AESTHETIC INTERPRETATION', text: 'A reasonable visual reading. Another viewer can disagree; no coherence score was measured.' }),
    physics: Object.freeze({ label: 'NOT ESTABLISHED', text: 'A generated picture supplies no measurement of a universal field. A physical claim needs defined observables, predictions and empirical tests.' }),
    satire: Object.freeze({ label: 'SATIRE', text: 'Spontaneous symmetry lounging is a joke coined in the exchange. The mock laws of Rug Theory are fictional.' })
  });
  function evaluateClaim(key) {
    if (!Object.prototype.hasOwnProperty.call(claims, key)) throw new RangeError('Unknown claim');
    return claims[key];
  }
  function mount(doc, items) {
    if (!doc || !doc.getElementById('catalog')) return;
    const search = doc.getElementById('search');
    const category = doc.getElementById('category');
    const reading = doc.getElementById('reading');
    const nodes = Array.from(doc.querySelectorAll('.artifact'));
    function render() {
      const matches = filterInventory(items, {query: search.value, category: category.value, reading: reading.value});
      const ids = new Set(matches.map(x => x.id));
      nodes.forEach(node => { node.hidden = !ids.has(Number(node.dataset.id)); });
      doc.getElementById('result-count').textContent = `${matches.length} of ${items.length} entries`;
      doc.getElementById('empty-state').hidden = matches.length !== 0;
    }
    search.addEventListener('input', render);
    category.addEventListener('change', render);
    reading.addEventListener('change', render);
    doc.getElementById('filters').addEventListener('submit', event => event.preventDefault());
    doc.getElementById('filters').addEventListener('reset', () => { setTimeout(render, 0); });
    doc.getElementById('find-rug').addEventListener('click', () => {
      search.value = '66'; category.value = 'all'; reading.value = 'all'; render();
      doc.getElementById('artifact-66').scrollIntoView({block: 'center'});
      search.focus({preventScroll: true});
    });
    doc.querySelectorAll('[data-room]').forEach(button => button.addEventListener('click', () => {
      const original = button.dataset.room === 'original';
      const img = doc.getElementById('room-image');
      img.src = original ? 'room-original.jpeg' : 'room.png';
      img.alt = original ? 'The original empty room: pale walls, gray floor, low ceiling and a rear partition with a passage to its left.' : 'An imagined warm research and music studio, with books and a writing desk to the left, scientific computing at the back, music equipment to the right and a patterned rug in the center.';
      doc.getElementById('image-link').href = original ? 'room-original.jpeg' : 'room.png';
      doc.getElementById('image-caption').textContent = original ? 'The supplied starting image. Many features changed in the edit; this is not a controlled rug-only comparison.' : 'Generated portrait of a creative life. The objects are imagined; the interests are personal.';
      doc.querySelectorAll('[data-room]').forEach(other => other.setAttribute('aria-pressed', String(other === button)));
    }));
    doc.querySelectorAll('[data-claim]').forEach(button => button.addEventListener('click', () => {
      const verdict = evaluateClaim(button.dataset.claim);
      const target = doc.getElementById('claim-result');
      target.querySelector('strong').textContent = verdict.label;
      target.querySelector('p').textContent = verdict.text;
      doc.querySelectorAll('[data-claim]').forEach(other => other.setAttribute('aria-pressed', String(other === button)));
    }));
    render();
  }
  return Object.freeze({ normalize, filterInventory, evaluateClaim, mount });
});
