// SPDX-License-Identifier: GPL-2.0-only
// Standalone milestone-one smoke page, deliberately separate from the book.
(async () => {
  const status = document.getElementById('status');
  const output = document.getElementById('results');
  const metricsNode = document.getElementById('metrics');
  const metrics = {
    user_agent: navigator.userAgent,
    protocol: location.protocol,
    startup_ms: null,
    parse_ms: [],
    peak_linear_memory_bytes: 0,
    parity: 'running',
  };
  function analyze(engine, request) {
    const source = JSON.stringify(request);
    const bytes = engine.lengthBytesUTF8(source) + 1;
    const ptr = engine._malloc(bytes);
    if (!ptr) throw new Error('input allocation failed');
    let response = 0;
    try {
      engine.stringToUTF8(source, ptr, bytes);
      response = engine._layout_analyze(ptr);
      if (!response) throw new Error('analysis allocation failed');
      return JSON.parse(engine.UTF8ToString(response));
    } finally {
      if (response) engine._layout_free(response);
      engine._free(ptr);
      metrics.peak_linear_memory_bytes = Math.max(
        metrics.peak_linear_memory_bytes, engine.HEAPU8.buffer.byteLength);
    }
  }
  // Object order is not significant in the protocol. Arrays remain ordered.
  function canonical(value) {
    if (Array.isArray(value)) return value.map(canonical);
    if (value !== null && typeof value === 'object')
      return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
    return value;
  }
  try {
    const binary = decodeLayoutWasm();
    const engine = await createLayoutEngine({
      wasmBinary: binary,
      printErr: text => { document.getElementById('stderr').textContent += text + '\n'; },
      onAbort: message => { throw new Error(String(message)); },
    });
    metrics.startup_ms = performance.now() - window.layoutProofStart;
    const results = [];
    for (let i = 0; i < window.layoutCases.length; ++i) {
      const before = performance.now();
      const result = analyze(engine, window.layoutCases[i].request);
      metrics.parse_ms.push(performance.now() - before);
      const match = JSON.stringify(canonical(result)) === JSON.stringify(canonical(window.layoutExpected[i]));
      if (!match) throw new Error('native/browser mismatch: ' + window.layoutCases[i].name);
      results.push(result);
      const line = document.createElement('li');
      line.textContent = window.layoutCases[i].name + ': matched native (' + result.status + ')';
      output.append(line);
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    const memoryBeforeRepeats = engine.HEAPU8.buffer.byteLength;
    for (let i = 0; i < 30; ++i) {
      const index = i % window.layoutCases.length;
      const result = analyze(engine, window.layoutCases[index].request);
      if (JSON.stringify(canonical(result)) !== JSON.stringify(canonical(results[index])))
        throw new Error('repeat analysis changed result');
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    metrics.linear_memory_before_repeats_bytes = memoryBeforeRepeats;
    metrics.linear_memory_after_repeats_bytes = engine.HEAPU8.buffer.byteLength;
    metrics.parity = 'passed';
    metrics.cases = results.length;
    metrics.repeated_requests = 30;
    window.layoutProofResults = results;
    status.textContent = 'All ' + results.length + ' native/browser comparisons passed.';
    document.documentElement.dataset.result = 'passed';
  } catch (error) {
    metrics.parity = 'failed';
    metrics.error = error.stack || String(error);
    status.textContent = 'Failed: ' + error.message;
    document.documentElement.dataset.result = 'failed';
  }
  metrics.total_ms = performance.now() - window.layoutProofStart;
  metricsNode.textContent = JSON.stringify(metrics, null, 2);
  window.layoutProofMetrics = metrics;
})();
