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
assert.match(html, /\.card-img\s*\{[^}]*?flex:\s*0 0 auto;[^}]*?aspect-ratio:\s*1\s*\/\s*1;/s, 'Every dish card must reserve a square full-width image zone');
assert.match(html, /\.card-no-img\s*\{[^}]*?flex:\s*0 0 auto;[^}]*?aspect-ratio:\s*1\s*\/\s*1;/s, 'The no-image placeholder must keep the same card geometry');
assert.match(html, /\.card-name\s*\{[\s\S]*?-webkit-line-clamp:\s*1;/, 'Names must use one compact line per language block');
assert.match(html, /\.card-desc\s*\{[\s\S]*?-webkit-line-clamp:\s*1;/, 'Descriptions must use one compact line per language block');
console.log('TV type scale: OK');
