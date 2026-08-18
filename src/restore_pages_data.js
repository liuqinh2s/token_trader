#!/usr/bin/env node
// Restore scanner state from the previous GitHub Pages deployment.
const fs = require('fs');
const path = require('path');

const input = process.argv[2];
const queueInput = process.argv[3];
const dataDir = path.join(__dirname, '..', 'data');
fs.mkdirSync(dataDir, { recursive: true });
const retentionCutoff = Date.now() - 48 * 60 * 60 * 1000;

let queueRestored = false;
if (queueInput && fs.existsSync(queueInput)) {
  try {
    const queue = JSON.parse(fs.readFileSync(queueInput, 'utf8'));
    if (queue && Array.isArray(queue.tokens) && Number.isFinite(Number(queue.lastBlock))) {
      fs.writeFileSync(path.join(dataDir, 'queue.json'), JSON.stringify(queue));
      queueRestored = true;
      console.log(`[RESTORE] Restored queue with ${queue.tokens.length} tokens from Pages.`);
    }
  } catch (err) {
    console.log(`[RESTORE] Queue state is unavailable: ${err.message}`);
  }
}

try {
  if (!input || !fs.existsSync(input)) throw new Error('history file is unavailable');
  const payload = JSON.parse(fs.readFileSync(input, 'utf8'));
  for (const item of Array.isArray(payload) ? payload : []) {
    if (!item || typeof item.file !== 'string' || !item.data) continue;
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.json$/.test(item.file)) continue;
    const parts = item.file.replace('.json', '').split('T');
    const timestamp = Date.parse(`${parts[0]}T${parts[1].replace(/-/g, ':')}Z`);
    if (!Number.isFinite(timestamp) || timestamp < retentionCutoff) continue;
    fs.writeFileSync(path.join(dataDir, item.file), JSON.stringify(item.data));
  }
  console.log(`[RESTORE] Restored ${Array.isArray(payload) ? payload.length : 0} scan files from Pages.`);
} catch (err) {
  console.log(`[RESTORE] No previous scan history restored: ${err.message}`);
}

if (!queueRestored) process.exitCode = 2;
