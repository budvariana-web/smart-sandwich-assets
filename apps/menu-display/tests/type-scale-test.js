const assert = require('assert');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'Index.html'), 'utf8');

function fontSize(selector) {
  const pattern = new RegExp(`${selector.replace('.', '\\.')}\\s*\\{[^}]*?font-size:\\s*(\\d+)px`, 's');
  const match = html.match(pattern);
  assert.ok(match, `Missing font-size for ${selector}`);
  return Number(match[1]);
}

assert.ok(fontSize('.card-category') >= 12, 'TV category text must be at least 12px');
assert.ok(fontSize('.card-name') >= 18, 'TV product title must be at least 18px');
assert.ok(fontSize('.card-desc') >= 13, 'TV product description must be at least 13px');
assert.ok(fontSize('.card-price') >= 30, 'TV price must be at least 30px');
assert.ok(fontSize('.announcement') >= 22, 'TV announcement text must be at least 22px');
console.log('TV type scale: OK');
