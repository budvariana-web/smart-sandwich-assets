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

responsiveMin('.card-category', 16);
responsiveMin('.card-name', 24);
responsiveMin('.card-desc', 16);
responsiveMin('.card-price', 30);
responsiveMin('.announcement', 22);

const imageRule = html.match(/\.card-img img\s*\{[^}]*?object-fit:\s*([^;]+);/s);
assert.ok(imageRule, 'Missing image presentation rule');
assert.strictEqual(imageRule[1].trim(), 'contain', 'Base layout must preserve the complete dish image');
assert.match(html, /\.card-img\s*\{[^}]*?flex:\s*0 0 auto;[^}]*?aspect-ratio:\s*1\s*\/\s*1;/s, 'Every dish card must reserve a square full-width image zone');
assert.match(html, /@media \(max-width: 1500px\)[\s\S]*?\.card-img,\s*\.card-no-img\s*\{[\s\S]*?aspect-ratio:\s*4\s*\/\s*3;/, 'Compact TV mode must preserve price room with a full 4:3 image field');
assert.match(html, /@media \(max-width: 1500px\)[\s\S]*?\.card-desc\s*\{[\s\S]*?-webkit-line-clamp:\s*4;/, 'Compact TV mode must allow four description lines per language');
assert.match(html, /\.layout\s*\{[\s\S]*?height:\s*calc\(100vh\s*-\s*51px\);[\s\S]*?margin:\s*35px 30px 16px;/, 'Cards must reclaim unused lower layout space while keeping a footer safe-gap');
assert.match(html, /\.card-name\s*\{[\s\S]*?-webkit-line-clamp:\s*2;/, 'Names must have room for two readable lines per language block');
assert.match(html, /\.card-desc\s*\{[\s\S]*?-webkit-line-clamp:\s*4;/, 'Descriptions must wrap across four readable lines per language block');
assert.match(html, /\.card-language-block \+ \.card-language-block \.card-name\s*\{[\s\S]*?display:\s*none;/, 'A duplicate second-language title must not consume description space');
assert.match(html, /\.card-desc\s*\{[\s\S]*?overflow-wrap:\s*break-word;/, 'Descriptions must wrap long words safely');
console.log('TV type scale: OK');
