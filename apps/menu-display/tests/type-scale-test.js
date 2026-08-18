const assert = require('assert');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'Index.html'), 'utf8');

function fontRule(selector) {
  const pattern = new RegExp(`${selector.replace('.', '\\.')}\\s*\\{[^}]*?font-size:\\s*([^;]+);`, 's');
  const match = html.match(pattern);
  assert.ok(match, `Missing font-size for ${selector}`);
  return match[1].trim();
}

function responsiveMin(selector, minimum) {
  const rule = fontRule(selector);
  assert.match(rule, new RegExp(`^clamp\\(${minimum}px,`), `${selector} must preserve a ${minimum}px 720p minimum and scale for 4K`);
}

responsiveMin('.card-category', 12);
responsiveMin('.card-name', 18);
responsiveMin('.card-desc', 13);
responsiveMin('.card-price', 30);
responsiveMin('.announcement', 22);

const imageRule = html.match(/\.card-img img\s*\{[^}]*?object-fit:\s*([^;]+);/s);
assert.ok(imageRule, 'Missing image presentation rule');
assert.strictEqual(imageRule[1].trim(), 'contain', 'Base layout must preserve the complete dish image');
assert.match(html, /@media \(min-width: 3000px\)[\s\S]*?\.card-img,\s*\.card-no-img\s*\{[\s\S]*?aspect-ratio:\s*1\s*\/\s*1;/, '4K layout must allocate a square full-width image zone');
console.log('TV type scale: OK');
