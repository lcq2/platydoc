// SPDX-License-Identifier: GPL-2.0-only
// Concatenated after the verified factory/contracts/dependency classic scripts.
(() => {
  'use strict';
  const C = self.LayoutContracts, D = self.LayoutDependencies;
  let engine = null, generation = null, identity = null, limits = null, busy = false, activeID = null;
  const cache = new Map(); let cacheBytes = 0;
  const metrics = {analyses: 0, cache_hits: 0, cache_entries: 0, cache_serialized_bytes: 0, peak_linear_memory_bytes: 0};
  const text = bytes => new TextDecoder('utf-8', {fatal: true}).decode(bytes);
  const serializeBytes = value => new TextEncoder().encode(C.canonical(value)).length;
  const copy = value => JSON.parse(C.canonical(value));
  function put(key, value) {
    const bytes = serializeBytes(value); if (bytes > limits.cache_bytes || !limits.cache_entries) return;
    if (cache.has(key)) {cacheBytes -= cache.get(key).bytes; cache.delete(key);}
    cache.set(key, {value, bytes}); cacheBytes += bytes;
    while (cache.size > limits.cache_entries || cacheBytes > limits.cache_bytes) {const oldest = cache.keys().next().value; cacheBytes -= cache.get(oldest).bytes; cache.delete(oldest);}
  }
  function get(key) {
    const entry = cache.get(key); if (!entry) return null;
    cache.delete(key); cache.set(key, entry); return entry.value;
  }
  function compile(request) {
    const json = JSON.stringify(request), length = engine.lengthBytesUTF8(json) + 1, pointer = engine._malloc(length);
    if (!pointer) throw new Error('Compiler input allocation failed');
    let response = 0;
    try {
      engine.stringToUTF8(json, pointer, length); self.postMessage({type: 'progress', phase: 'compiling', generation, id: activeID}); response = engine._layout_analyze(pointer);
      if (!response) throw new Error('Compiler response allocation failed');
      const result = JSON.parse(engine.UTF8ToString(response));
      if (result.compiler && (result.compiler.revision !== identity.compiler.revision || result.compiler.engine_sha256 !== identity.compiler.engine_sha256)) throw new Error('Compiler identity mismatch');
      ++metrics.analyses; return result;
    } finally {if (response) engine._layout_free(response); engine._free(pointer); metrics.peak_linear_memory_bytes = Math.max(metrics.peak_linear_memory_bytes, engine.HEAPU8.buffer.byteLength);}
  }
  async function baseline(profile, request, source) {
    const key = await C.sha256(C.canonical({kind: 'baseline', identity, profile, request, source}));
    let value = get(key);
    if (value) {await C.validate(value.document); return value;}
    const result = compile(request), policy = await C.createPolicy(request, result, {label: profile});
    const document = await C.create(request, result, {source, policy, profile});
    value = {request, result, document}; put(key, value); return value;
  }
  async function analyze(message) {
    const profileText = text(message.profile_bytes), profileSHA = await C.sha256(profileText);
    const computation = await C.sha256(C.canonical({identity, profile: message.profile, source: message.source, profile_sha256: profileSHA, overrides: message.overrides, dependencies: message.dependencies}));
    if (computation !== message.computation_sha256) throw new Error('Computation identity mismatch');
    const payload = JSON.parse(profileText);
    if (!payload || !payload.request || C.canonical(payload.source) !== C.canonical(message.source)) throw new Error('Invalid profile bundle');
    const baseRequest = {...payload.request, trace_dependencies: Boolean(message.dependencies), trace_files: true};
    if (!message.overrides || typeof message.overrides !== 'object' || Array.isArray(message.overrides)) throw new Error('Overrides must be an object');
    const key = await C.sha256(C.canonical({kind: 'result', identity, profile: message.profile, source: payload.source,
      baseline_request: baseRequest, overrides: message.overrides, dependencies: message.dependencies}));
    const hit = get(key);
    if (hit) {
      await C.validate(hit.contract, hit.analysis ? {analysis: hit.analysis} : {}); ++metrics.cache_hits;
      return {...hit, metrics: {...snapshot(), cache_hit: true}};
    }
    const base = await baseline(message.profile, baseRequest, payload.source);
    let request = baseRequest, result = base.result, document = base.document;
    const custom = Object.keys(message.overrides).length > 0;
    if (custom) {
      const resolved = C.resolveConfiguration(baseRequest, message.overrides, base.document.configuration.policy, {whatIf: true});
      if (resolved.resolution.status === 'invalid-configuration') throw new Error(resolved.resolution.issues.join('\n'));
      request = resolved.request; result = compile(request);
      document = await C.create(request, result, {source: payload.source, policy: base.document.configuration.policy, whatIf: true});
    }
    let analysis = null, contract = document;
    if (message.dependencies) {
      const entries = [{name: message.profile, request: baseRequest, result: base.result, document: base.document}];
      if (custom) entries.push({name: 'manual-what-if', request, result, document});
      analysis = await D.discover(entries, {space_id: message.profile + (custom ? '-baseline-and-manual-what-if' : '-runtime-baseline')});
      contract = await D.attach(document, analysis); await C.validate(contract, {analysis});
    }
    const {dependency_trace, ...compactResult} = result;
    const value = {profile: message.profile, request, result: compactResult, contract, analysis, computation_sha256: computation};
    put(key, value); return {...value, metrics: {...snapshot(), cache_hit: false}};
  }
  function snapshot() {
    const capacity = engine.HEAPU8.buffer.byteLength;
    return {...metrics, cache_entries: cache.size, cache_serialized_bytes: cacheBytes, linear_memory_bytes: capacity,
      retire_worker: capacity > limits.max_linear_memory_bytes, persistence: 'disabled'};
  }
  self.onmessage = async event => {
    const message = event.data;
    if (message?.type === 'init') {
      if (generation !== null) return;
      generation = message.generation; limits = message.limits; identity = {runtime_version: 1, compiler: message.compiler, assets: message.assets};
      try {
        engine = await createLayoutEngine({wasmBinary: new Uint8Array(message.wasm), printErr: () => {}, onAbort: message => {throw new Error(String(message));}});
        metrics.peak_linear_memory_bytes = engine.HEAPU8.buffer.byteLength;
        self.postMessage({type: 'ready', generation});
      } catch (failure) {self.postMessage({type: 'startup-error', generation, message: failure.message});}
      return;
    }
    if (!engine || message?.type !== 'analyze' || message.generation !== generation || busy) return;
    busy = true; activeID = message.id;
    try {
      const value = await analyze(message);
      self.postMessage({type: 'result', generation, id: message.id, value: {...value, id: message.id, generation}});
    } catch (failure) {self.postMessage({type: 'error', generation, id: message.id, message: failure.message});}
    finally {busy = false; activeID = null;}
  };
})();
