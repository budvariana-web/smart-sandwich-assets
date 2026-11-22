export function normalizeUrls(values) {
  const seen = new Set();
  return (values || []).map(value => String(value || '').trim()).filter(value => {
    if (!/^https:\/\/.+\.mp4(?:[?#].*)?$/i.test(value) || seen.has(value)) return false;
    seen.add(value);
    return true;
  });
}

export class ShuffledQueue {
  constructor(urls = [], random = Math.random) {
    this.random = random;
    this.urls = normalizeUrls(urls);
    this.queue = [];
    this.current = '';
  }

  replace(urls) {
    const next = normalizeUrls(urls);
    if (next.join('\n') === this.urls.join('\n')) return false;
    this.urls = next;
    this.queue = this.queue.filter(url => next.includes(url));
    if (this.current && !next.includes(this.current)) this.current = '';
    return true;
  }

  shuffle() {
    const values = this.urls.slice();
    for (let i = values.length - 1; i > 0; i -= 1) {
      const j = Math.floor(this.random() * (i + 1));
      [values[i], values[j]] = [values[j], values[i]];
    }
    if (values.length > 1 && values[0] === this.current) {
      const j = 1 + Math.floor(this.random() * (values.length - 1));
      [values[0], values[j]] = [values[j], values[0]];
    }
    this.queue = values;
  }

  next() {
    if (!this.urls.length) return '';
    if (!this.queue.length) this.shuffle();
    this.current = this.queue.shift() || '';
    return this.current;
  }
}
