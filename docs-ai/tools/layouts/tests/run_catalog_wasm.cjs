// SPDX-License-Identifier: GPL-2.0-only
// One complete request per process bounds retained compiler/trace state.
const fs = require('node:fs');
const {performance} = require('node:perf_hooks');
(async () => {
  const [factoryPath, requestPath, resultPath, metricsPath] = process.argv.slice(2);
  const started = performance.now();
  const engine = await require(factoryPath)({wasmBinary: fs.readFileSync(factoryPath.replace(/\.js$/, '.wasm')), printErr: message => process.stderr.write(message + '\n')});
  const startup = performance.now() - started;
  const request = fs.readFileSync(requestPath, 'utf8'), pointer = engine._malloc(engine.lengthBytesUTF8(request) + 1);
  if (!pointer) throw Error('Compiler request allocation failed');
  let response = 0;
  try {
    engine.stringToUTF8(request, pointer, engine.lengthBytesUTF8(request) + 1);
    const before = performance.now();response = engine._layout_analyze(pointer);
    if (!response) throw Error('Compiler response allocation failed');
    fs.writeFileSync(resultPath, engine.UTF8ToString(response));
    fs.writeFileSync(metricsPath, JSON.stringify({startup_ms: startup, parse_ms: performance.now() - before, linear_memory_bytes: engine.HEAPU8.buffer.byteLength, node_peak_rss_kib: process.resourceUsage().maxRSS}));
  } finally {if (response) engine._layout_free(response);engine._free(pointer);}
})().catch(error => {process.stderr.write(error.stack + '\n');process.exitCode = 1;});
