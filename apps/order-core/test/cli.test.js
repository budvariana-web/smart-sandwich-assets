import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const appDir = resolve(here, '..');

test('CLI server entrypoint listens when launched with a Windows-compatible path', async (t) => {
  const port = 3911;
  const child = spawn(process.execPath, ['src/server.js'], {
    cwd: appDir, env: { ...process.env, PORT: String(port) }, stdio: ['ignore', 'pipe', 'pipe'],
  });
  let output = '';
  child.stdout.on('data', (chunk) => { output += chunk; });
  child.stderr.on('data', (chunk) => { output += chunk; });
  t.after(() => { if (!child.killed) child.kill(); });

  await new Promise((resolve, reject) => {
    let interval;
    const timeout = setTimeout(() => { clearInterval(interval); reject(new Error(`server did not start: ${output}`)); }, 1500);
    child.on('exit', (code) => { clearInterval(interval); clearTimeout(timeout); reject(new Error(`server exited ${code}: ${output}`)); });
    interval = setInterval(async () => {
      try {
        const response = await fetch(`http://127.0.0.1:${port}/health`);
        clearInterval(interval); clearTimeout(timeout);
        assert.deepEqual(await response.json(), { ok: true, orderCount: 0 });
        resolve();
      } catch { /* wait until listening */ }
    }, 30);
  });
});
