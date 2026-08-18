const fs = require('fs');
const vm = require('vm');
const assert = require('assert');

const html = fs.readFileSync(require('path').join(__dirname, '..', 'Index.html'), 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
const script = scripts.at(-1)[1];
const elements = Object.fromEntries([
  'ann-bottom', 'ann-bottom-badge', 'ann-bottom-text', 'ann-top', 'ann-top-badge', 'ann-top-text',
  'brand-name', 'fullscreen-video', 'fullscreen-video-el', 'header-clock', 'menu', 'offline',
  'page-count', 'page-countdown', 'subtitle', 'updated', 'video-counter', 'video-label',
  'video-placeholder', 'video-slot', 'video-zone'
].map(id => [id, {
  textContent: '', innerHTML: '', style: {},
  classList: { add() {}, remove() {}, toggle() {} },
  addEventListener() {}, pause() {}, play() { return Promise.resolve(); },
  removeAttribute() {}, load() {}
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
const fetch = (url) => {
  const payload = String(url).includes('open-meteo')
    ? { current: { temperature_2m: 24, apparent_temperature: 25, precipitation: 0, weather_code: 0, wind_speed_10m: 5 }, daily: { temperature_2m_min: [18], temperature_2m_max: [27] } }
    : menu;
  return {
    then(first) {
      const value = first({ ok: true, status: 200, json() { return payload; } });
      return { then(second) { second(value); return { catch() {} }; } };
    }
  };
};
const context = {
  document: { getElementById: id => elements[id] },
  window: { google, setTimeout() {}, MENU_LANG: 'ru' }, google, fetch,
  localStorage: { setItem() {}, getItem() { return null; } },
  URL, Date, Intl, console, setTimeout() { return 1; }, clearTimeout() {},
  setInterval() { return 1; }, clearInterval() {}
};
vm.createContext(context);
vm.runInContext(script, context);
assert.strictEqual(elements['brand-name'].textContent, 'SMART <BAR>');
assert.match(elements['page-count'].textContent, /^1 \/ [2-9]\d*$/, 'First page and a multi-page cycle must be shown');
assert.ok(elements.menu.innerHTML.includes('&lt;img src=x onerror=alert(1)&gt;'), 'Menu values must be HTML-escaped');
assert.ok(!elements.menu.innerHTML.includes('<img src=x onerror=alert(1)>'), 'Raw injected HTML must not be rendered');
console.log('Render test: OK — pagination and escaped Sheet content verified');
