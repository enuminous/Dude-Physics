'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const api = require('./app.js');
const data = JSON.parse(fs.readFileSync(path.join(__dirname, 'inventory.json'), 'utf8'));
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('PASS: ' + name); }
test('blank query preserves all 72 entries and order', () => {
  assert.deepEqual(api.filterInventory(data, {query: '  '}).map(x => x.id), Array.from({length:72}, (_, i) => i + 1));
});
test('rug lookup is exact for this catalog', () => {
  assert.deepEqual(api.filterInventory(data, {query: ' RUG '}).map(x => x.id), [66]);
  assert.deepEqual(api.filterInventory(data, {query: '66'}).map(x => x.id), [66]);
});
test('search matches several terms across metadata', () => {
  const expected = data.filter(x => x.name.toLowerCase().includes('guitar'));
  assert.ok(expected.length >= 2);
  assert.deepEqual(api.filterInventory(data, {query:'music guitar'}), expected);
});
test('category and reading constraints intersect the query', () => {
  assert.equal(api.filterInventory(data, {query:'rug', category:'Music'}).length, 0);
  assert.deepEqual(api.filterInventory(data, {category:'Zoo', reading:'interpretive'}), data.filter(x => x.category === 'Zoo' && x.reading === 'interpretive'));
  assert.ok(api.filterInventory(data, {category:'Zoo', reading:'interpretive'}).length > 0);
});
test('unknown terms and category return no entries without mutating data', () => {
  const before = JSON.stringify(data);
  assert.equal(api.filterInventory(data, {query: 'a-uniquely-absent-object'}).length, 0);
  assert.equal(api.filterInventory(data, {category: 'not-a-collection'}).length, 0);
  assert.equal(JSON.stringify(data), before);
});
test('diacritics and case normalize; punctuation does not execute', () => {
  assert.equal(api.normalize(' MÖBIUS '), 'mobius');
  assert.equal(api.filterInventory(data, {query:'<script>alert(1)</script>'}).length, 0);
});
test('generated browser catalog equals canonical JSON', () => {
  const context = {};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, 'inventory.js'), 'utf8'), context);
  assert.equal(JSON.stringify(context.DUDE_INVENTORY), JSON.stringify(data));
});
test('physical claim remains unestablished; satire remains labeled', () => {
  assert.equal(api.evaluateClaim('physics').label, 'NOT ESTABLISHED');
  assert.equal(api.evaluateClaim('satire').label, 'SATIRE');
  assert.equal(api.evaluateClaim('composition').label, 'AESTHETIC INTERPRETATION');
  assert.match(api.evaluateClaim('physics').text, /empirical tests/);
});
test('unsupported claim keys fail instead of fabricating a verdict', () => {
  for (const key of ['unknown', '__proto__', 'constructor']) assert.throws(() => api.evaluateClaim(key), RangeError);
});
console.log(`PASS: ${passed} JavaScript checks`);
