// Pyodide worker — runs the Python game/ package in-browser for offline bot play
importScripts('/static/pyodide/pyodide.js');

let pyodide = null;
let session = null;

const GAME_FILES = [
  '__init__.py', 'base.py', 'constants.py', 'lobby.py', 'offline.py',
  'registry.py', 'room.py',
];
const VARIANT_FILES = [
  '__init__.py', 'atomic.py', 'classic.py', 'dice.py', 'fog.py',
  'king_hill.py', 'three_check.py', 'thress.py',
];

async function init() {
  try {
    pyodide = await loadPyodide({ indexURL: '/static/pyodide/' });
    await pyodide.loadPackage('micropip');
    const micropip = pyodide.pyimport('micropip');
    await micropip.install('/static/chess.whl');

    // Write game/ package files into Pyodide's virtual filesystem
    pyodide.FS.mkdir('/app');
    pyodide.FS.mkdir('/app/game');
    pyodide.FS.mkdir('/app/game/variants');

    for (const f of GAME_FILES) {
      const text = await fetch(`/game/${f}`).then(r => r.text());
      pyodide.FS.writeFile(`/app/game/${f}`, text);
    }
    for (const f of VARIANT_FILES) {
      const text = await fetch(`/game/variants/${f}`).then(r => r.text());
      pyodide.FS.writeFile(`/app/game/variants/${f}`, text);
    }

    // Add /app to sys.path and import the offline session
    await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, '/app')
from game.offline import OfflineSession
_session = OfflineSession()
`);
    session = true;
    self.postMessage({ type: 'ready' });
  } catch (err) {
    self.postMessage({ type: 'error', message: String(err) });
  }
}

self.onmessage = async (e) => {
  const msg = e.data;
  if (msg.type === 'init') {
    await init();
    return;
  }

  if (!session) {
    self.postMessage({ type: 'error', message: 'Pyodide not ready.' });
    return;
  }

  try {
    const msgType = msg.type;
    const payloadJson = JSON.stringify(msg);
    const resultJson = await pyodide.runPythonAsync(`
import json as _json
_result = _session.handle(${JSON.stringify(msgType)}, _json.loads(${JSON.stringify(payloadJson)}))
_json.dumps(_result)
`);
    self.postMessage(JSON.parse(resultJson));
  } catch (err) {
    self.postMessage({ type: 'error', message: String(err) });
  }
};
