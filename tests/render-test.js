const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const html = fs.readFileSync(require('path').join(__dirname, '..', 'Index.html'), 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1];
const elements = Object.fromEntries(['brand', 'menu', 'page-count', 'updated', 'offline'].map(id => [id, {
  textContent: '', innerHTML: '',
  classList: { toggle() {} }
}]));
const menu = {
  brand: 'SMART <BAR>', refreshSeconds: 60, pageSeconds: 15,
  items: Array.from({ length: 13 }, (_, i) => ({
    category: i < 7 ? 'Бургеры' : 'Сэндвичи',
    name: i === 0 ? '<img src=x onerror=alert(1)>' : `Позиция ${i + 1}`,
    description: 'Тестовое описание', price: `${300 + i * 10} ₽`, oldPrice: '', badge: '', imageUrl: ''
  }))
};
const google = { script: { run: { withSuccessHandler(ok) { return { withFailureHandler() { return { getMenu() { ok(menu); } }; } }; } } } };
const context = {
  document: { getElementById: id => elements[id] },
  window: { google, setTimeout() {} }, google,
  localStorage: { setItem() {}, getItem() { return null; } },
  URL, Date, console, setInterval() { return 1; }, clearInterval() {}
};
vm.createContext(context);
vm.runInContext(script, context);
assert.strictEqual(elements.brand.textContent, 'SMART <BAR>');
assert.strictEqual(elements['page-count'].textContent, '1 / 2');
assert.ok(elements.menu.innerHTML.includes('&lt;img src=x onerror=alert(1)&gt;'), 'Menu values must be HTML-escaped');
assert.ok(!elements.menu.innerHTML.includes('<img src=x onerror=alert(1)>'), 'Raw injected HTML must not be rendered');
console.log('Render test: OK — pagination and escaped Sheet content verified');
