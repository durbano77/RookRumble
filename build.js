// Copies web assets into www/ for Capacitor to bundle into the Android APK.
// The Python server files (server.py, requirements.txt) are intentionally
// excluded — they're only needed for the hosted web version on Render.
import { cpSync, mkdirSync, rmSync, existsSync } from 'fs';
import { resolve } from 'path';

const ROOT = resolve('.');
const OUT  = resolve('www');

const copy = (from, to = from) => {
  const src = resolve(ROOT, from);
  if (!existsSync(src)) { console.warn(`  skip  ${from} (not found)`); return; }
  cpSync(src, resolve(OUT, to), { recursive: true });
  console.log(`  copy  ${from}`);
};

console.log('Building www/...');
rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT);

copy('index.html');
copy('privacy.html');
copy('manifest.json');
copy('sw.js');
copy('favicon.ico');
copy('apple-touch-icon.png');
copy('css');
copy('js');
copy('icons');
copy('static');   // Pyodide + Stockfish — bundled locally in the APK
copy('game');     // Python source files loaded by Pyodide at runtime
copy('.well-known');

console.log(`\nDone — www/ is ready for Capacitor.`);
