// SPDX-License-Identifier: GPL-2.0-only
// Node is an additional parity check; it is not the file:// browser proof.
const fs = require('node:fs');
const {performance} = require('node:perf_hooks');

function analyze(engine, request) {
  const source = JSON.stringify(request);
  const ptr = engine._malloc(engine.lengthBytesUTF8(source) + 1);
  if (!ptr) throw new Error('input allocation failed');
  let result = 0;
  try {
    engine.stringToUTF8(source, ptr, engine.lengthBytesUTF8(source) + 1);
    result = engine._layout_analyze(ptr);
    if (!result) throw new Error('analysis allocation failed');
    return JSON.parse(engine.UTF8ToString(result));
  } finally {
    if (result) engine._layout_free(result);
    engine._free(ptr);
  }
}

(async () => {
  const start = performance.now();
  const factory = require(process.argv[2]);
  const wasmBinary = fs.readFileSync(process.argv[2].replace(/\.js$/, '.wasm'));
  const engine = await factory({wasmBinary, printErr: message => process.stderr.write(message + '\n')});
  const startupMs = performance.now() - start;
  const requests = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
  const times = [];
  const results = requests.map(request => {
    const before = performance.now();
    const result = analyze(engine, request);
    times.push(performance.now() - before);
    return result;
  });
  const bytesAfterCases = engine.HEAPU8.buffer.byteLength;
  for (let i = 0; i < 30; ++i) {
    const result = analyze(engine, requests[i % requests.length]);
    if (JSON.stringify(result) !== JSON.stringify(results[i % requests.length]))
      throw new Error('repeated request changed result');
  }
  process.stdout.write(JSON.stringify({results, metrics: {
    node: process.version, startup_ms: startupMs, parse_ms: times,
    linear_memory_after_cases_bytes: bytesAfterCases,
    linear_memory_after_repeats_bytes: engine.HEAPU8.buffer.byteLength,
    node_peak_rss_kib: process.resourceUsage().maxRSS,
  }}) + '\n');
})().catch(error => { process.stderr.write(error.stack + '\n'); process.exitCode = 1; });
