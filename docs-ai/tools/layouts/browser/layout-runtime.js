// SPDX-License-Identifier: GPL-2.0-only
// One active request; terminating the worker also interrupts synchronous Wasm.
(function (root, factory) {
  const api = factory(root, typeof module === 'object' && module.exports ? require('./layout-codec.js') : root.LayoutCodec);
  if (typeof module === 'object' && module.exports) module.exports = api; else root.LayoutRuntime = api;
})(globalThis, function (root, Codec) {
  'use strict';
  const VERSION = 1, MiB = 1024 * 1024;
  const canonical = value => JSON.stringify(value && typeof value === 'object' ? Array.isArray(value) ? value.map(item => JSON.parse(canonical(item))) : Object.fromEntries(Object.keys(value).sort().map(key => [key, JSON.parse(canonical(value[key]))])) : value);
  const error = (code, message) => Object.assign(new Error(message), {code});
  const validAsset = asset => {
    if (!asset || typeof asset.id !== 'string' || !/^[A-Za-z0-9_.-]+$/.test(asset.id) || typeof asset.url !== 'string' ||
      !/^[A-Za-z0-9_./-]+\.js$/.test(asset.url) || asset.url.startsWith('/') || asset.url.split('/').some(part => ['..', '.'].includes(part)) ||
      !/^[a-f0-9]{64}$/.test(asset.sha256) || !Number.isSafeInteger(asset.bytes) || asset.bytes < 0 || asset.bytes > 64 * MiB) throw error('manifest-error', 'Invalid local asset');
    return asset;
  };
  function validateManifest(manifest) {
    if (!manifest || manifest.contract !== 'platydoc.layout-runtime-manifest' || manifest.version !== VERSION || !manifest.compiler || !manifest.assets || !Array.isArray(manifest.profiles) || !manifest.profiles.length) throw error('manifest-error', 'Unsupported runtime manifest');
    for (const key of ['revision', 'engine_sha256', 'wasm_sha256', 'factory_sha256']) if (!/^[a-f0-9]{40,64}$/.test(manifest.compiler[key])) throw error('manifest-error', 'Missing compiler identity');
    const ids = new Set();
    for (const asset of [...['factory', 'contracts', 'dependencies', 'worker', 'wasm'].map(name => manifest.assets[name]), ...manifest.profiles.map(profile => profile.asset)]) {
      validAsset(asset); if (ids.has(asset.id)) throw error('manifest-error', 'Duplicate asset ID'); ids.add(asset.id);
    }
    if (manifest.assets.wasm.sha256 !== manifest.compiler.wasm_sha256 || manifest.assets.factory.sha256 !== manifest.compiler.factory_sha256) throw error('manifest-error', 'Compiler artifact mismatch');
    const profiles = new Set();
    for (const profile of manifest.profiles) {if (typeof profile.id !== 'string' || profiles.has(profile.id) || !profile.source || typeof profile.source.release !== 'string' || typeof profile.source.revision !== 'string') throw error('manifest-error', 'Invalid profile'); profiles.add(profile.id);}
    return manifest;
  }
  const deliveries = new Map();
  root.LayoutRuntimeAssets = {deliver(id, envelope) {for (const receive of [...(deliveries.get(id) || [])]) receive(envelope);}};
  function localEnvelope(asset, signal) {
    return new Promise((resolve, reject) => {
      if (signal.aborted) {reject(error('cancelled', 'Asset loading cancelled')); return;}
      const script = document.createElement('script'); let delivered = false, envelope;
      const cleanup = () => {const subscribers = deliveries.get(asset.id); subscribers?.delete(receive); if (subscribers?.size === 0) deliveries.delete(asset.id); script.remove(); signal.removeEventListener('abort', abort); script.onload = script.onerror = null;};
      const abort = () => {cleanup(); reject(error('cancelled', 'Asset loading cancelled'));};
      const receive = value => {if (delivered) return; delivered = true; envelope = value;};
      if (!deliveries.has(asset.id)) deliveries.set(asset.id, new Set());
      deliveries.get(asset.id).add(receive);
      script.onload = () => {cleanup(); delivered ? resolve(envelope) : reject(error('asset-error', 'Asset did not register: ' + asset.id));};
      script.onerror = () => {cleanup(); reject(error('asset-error', 'Cannot load local asset: ' + asset.id));};
      signal.addEventListener('abort', abort, {once: true}); script.src = asset.url; document.head.append(script);
    });
  }
  class Client {
    constructor(manifest, options = {}) {
      this.manifest = validateManifest(JSON.parse(JSON.stringify(manifest))); this.options = {...options};
      this.sequence = 0; this.generation = 0; this.active = null; this.worker = null; this.disposed = false;
      this.assetBudget = options.asset_cache_bytes ?? 16 * MiB;
      if (!Number.isSafeInteger(this.assetBudget) || this.assetBudget < 0) throw error('options-error', 'Invalid asset cache budget');
      this.assetCache = new Map(); this.assetCacheBytes = 0;
      this.metrics = {worker_starts: 0, worker_terminations: 0, stale_messages: 0, cache_hits: 0, asset_cache_bytes: 0, persistence: 'disabled'};
      this.limits = {cache_entries: 3, cache_bytes: 64 * MiB, max_linear_memory_bytes: 256 * MiB, ...options.limits};
      for (const key of ['cache_entries', 'cache_bytes', 'max_linear_memory_bytes']) if (!Number.isSafeInteger(this.limits[key]) || this.limits[key] < 0) throw error('options-error', 'Invalid runtime limit');
    }
    state(state, job, message = '') {try {this.options.onstate?.({state, id: job?.id ?? null, generation: job?.generation ?? this.generation, message});} catch (_) {}}
    current(job) {return !this.disposed && this.active === job && !job.settled && job.generation === this.generation;}
    check(job) {if (!this.current(job)) throw error('superseded', 'Request is no longer current');}
    stopWorker() {
      if (this.workerURL) {URL.revokeObjectURL(this.workerURL); this.workerURL = null;}
      if (!this.worker) return;
      this.worker.onmessage = this.worker.onerror = this.worker.onmessageerror = null;
      this.worker.terminate(); this.worker = null; ++this.metrics.worker_terminations;
      const reject = this.readyReject; this.readyReject = null; this.readyResolve = null; if (reject) reject(error('cancelled', 'Worker terminated'));
    }
    settle(job, failure, value) {
      if (job.settled) return; job.settled = true; clearTimeout(job.timer); clearTimeout(job.startTimer); job.abort.abort();
      if (this.active === job) this.active = null;
      if (failure) {this.state(failure.code || 'error', job, failure.message); job.reject(failure);} else {this.state('complete', job); job.resolve(value);}
    }
    cancel(code = 'cancelled') {
      const job = this.active; ++this.generation; this.stopWorker();
      if (job) this.settle(job, error(code, code === 'superseded' ? 'Replaced by a newer request' : 'Analysis cancelled'));
    }
    dispose() {if (this.disposed) return; this.cancel('disposed'); this.disposed = true; this.assetCache.clear(); this.assetCacheBytes = 0; this.metrics.asset_cache_bytes = 0;}
    async asset(asset, job, keep = true) {
      this.check(job); const key = asset.sha256 + ':' + asset.bytes;
      if (keep && this.assetCache.has(key)) {const bytes = this.assetCache.get(key); this.assetCache.delete(key); this.assetCache.set(key, bytes); return bytes.slice();}
      const envelope = await (this.options.loadEnvelope || localEnvelope)(asset, job.abort.signal); this.check(job);
      const bytes = await Codec.decode(envelope, asset, {fallback: this.options.force_fallback, signal: job.abort.signal}); this.check(job);
      const budget = this.assetBudget;
      if (keep && bytes.length <= budget) {
        this.assetCache.set(key, bytes.slice()); this.assetCacheBytes += bytes.length;
        while (this.assetCacheBytes > budget) {const oldest = this.assetCache.keys().next().value; this.assetCacheBytes -= this.assetCache.get(oldest).length; this.assetCache.delete(oldest);}
        this.metrics.asset_cache_bytes = this.assetCacheBytes;
      }
      return bytes;
    }
    async start(job) {
      if (this.worker) return;
      this.state('loading-engine', job);
      const texts = [];
      for (const name of ['factory', 'contracts', 'dependencies', 'worker']) {const bytes = await this.asset(this.manifest.assets[name], job); this.check(job); texts.push(new TextDecoder('utf-8', {fatal: true}).decode(bytes));}
      const wasm = await this.asset(this.manifest.assets.wasm, job, false); this.check(job);
      const blob = new Blob(texts.map(text => text + '\n'), {type: 'text/javascript'});
      const url = URL.createObjectURL(blob);
      let worker;
      try {worker = (this.options.createWorker || (url => new Worker(url)))(url);} catch (failure) {URL.revokeObjectURL(url); throw failure;}
      this.workerURL = url;
      this.check(job); this.worker = worker; ++this.metrics.worker_starts;
      const ready = new Promise((resolve, reject) => {this.readyResolve = resolve; this.readyReject = reject;});
      ready.catch(() => {}); // postMessage may throw before the await is installed.
      worker.onmessage = event => {if (this.worker !== worker) {++this.metrics.stale_messages; return;} this.receive(event.data, job.generation);};
      worker.onerror = event => {if (this.worker !== worker) {++this.metrics.stale_messages; return;} event.preventDefault?.(); this.crash('worker-error', event.message || 'Worker execution failed', job.generation);};
      worker.onmessageerror = () => {if (this.worker !== worker) {++this.metrics.stale_messages; return;} this.crash('worker-message-error', 'Worker message could not be decoded', job.generation);};
      worker.postMessage({type: 'init', generation: job.generation, wasm: wasm.buffer, compiler: this.manifest.compiler,
        assets: Object.fromEntries(Object.entries(this.manifest.assets).map(([name, asset]) => [name, asset.sha256])), limits: this.limits}, [wasm.buffer]);
      this.state('starting-engine', job); await ready; this.check(job);
    }
    crash(code, message, generation) {
      if (generation !== this.generation) return;
      const failure = error(code, message), job = this.active, reject = this.readyReject;
      this.stopWorker(); if (reject) reject(failure); if (job) this.settle(job, failure);
    }
    async receive(message, generation) {
      const job = this.active;
      if (!job || generation !== this.generation || message?.generation !== generation || !this.current(job)) {++this.metrics.stale_messages; return;}
      if (message.type === 'ready') {if (this.workerURL) {URL.revokeObjectURL(this.workerURL); this.workerURL = null;} if (this.readyResolve) {const resolve = this.readyResolve; this.readyResolve = null; this.readyReject = null; resolve();} return;}
      if (message.type === 'startup-error') {this.crash('startup-error', String(message.message), generation); return;}
      if (message.id !== job.id) {++this.metrics.stale_messages; return;}
      if (message.type === 'progress') {if (message.phase !== 'compiling') {this.crash('worker-message-error', 'Unknown worker phase', generation); return;} this.state('compiling', job); return;}
      if (message.type === 'error') {this.crash('analysis-error', String(message.message), generation); return;}
      if (message.type !== 'result' || !message.value || message.value.id !== job.id || message.value.generation !== generation ||
          !message.value.result || !message.value.contract || !message.value.metrics || message.value.profile !== job.profile || message.value.computation_sha256 !== job.computation_sha256 ||
          !['ok', 'error', 'invalid-request', 'unsupported-layout', 'unavailable-type'].includes(message.value.result.status) ||
          !Array.isArray(message.value.result.records) || !Array.isArray(message.value.result.diagnostics) ||
          (message.value.result.status !== 'ok' && message.value.result.records.length)) {this.crash('worker-message-error', 'Malformed worker result', generation); return;}
      try {
        const value = message.value, measured = value.metrics;
        for (const name of ['analyses', 'cache_hits', 'cache_entries', 'cache_serialized_bytes', 'peak_linear_memory_bytes', 'linear_memory_bytes'])
          if (!Number.isSafeInteger(measured[name]) || measured[name] < 0) throw new Error('Invalid worker metric');
        if (measured.cache_entries > this.limits.cache_entries || measured.cache_serialized_bytes > this.limits.cache_bytes ||
            typeof measured.cache_hit !== 'boolean' || measured.persistence !== 'disabled' ||
            measured.retire_worker !== (measured.linear_memory_bytes > this.limits.max_linear_memory_bytes) ||
            measured.peak_linear_memory_bytes < measured.linear_memory_bytes) throw new Error('Worker cache/capacity metrics violate bounds');
        if (job.expectedRequest && (canonical(value.request) !== canonical(job.expectedRequest) || canonical(value.contract.source) !== canonical(job.source))) throw new Error('Reply belongs to a different request context');
        if (this.options.validateReply) await this.options.validateReply(value);
        else {
          const C = root.LayoutContracts, D = root.LayoutDependencies;
          if (!C || !D || !value.request) throw new Error('Missing result validator');
          if (value.result.compiler && (value.result.compiler.revision !== this.manifest.compiler.revision || value.result.compiler.engine_sha256 !== this.manifest.compiler.engine_sha256)) throw new Error('Compiler reply identity mismatch');
          await C.validate(value.contract, value.analysis ? {analysis: value.analysis} : {});
          const rebuilt = await C.create(value.request, value.result, {source: value.contract.source, policy: value.contract.configuration.policy, profile: value.contract.configuration.profile, whatIf: value.contract.configuration.classification === 'what-if'});
          if (C.canonical(rebuilt) !== C.canonical(D.baseDocument(value.contract))) throw new Error('Layout reply/contract mismatch');
        }
        if (!this.current(job)) {++this.metrics.stale_messages; return;}
      } catch (failure) {if (this.current(job)) this.crash('worker-message-error', failure.message, generation); return;}
      if (message.value.metrics.cache_hit) ++this.metrics.cache_hits;
      if (message.value.metrics.retire_worker) this.stopWorker();
      this.settle(job, null, message.value);
    }
    analyze(profile, options = {}) {
      if (this.disposed) return Promise.reject(error('disposed', 'Runtime has been disposed'));
      if (this.active) this.cancel('superseded');
      const id = ++this.sequence, generation = this.generation;
      let overrides;
      try {
        if (!options.overrides) overrides = {};
        else {
          if (typeof options.overrides !== 'object' || Array.isArray(options.overrides)) throw new Error('Overrides must be an object');
          overrides = Object.fromEntries(Object.entries(options.overrides).map(([name, value]) => {if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name) || value !== null && (typeof value !== 'string' || /[\0\r\n]/.test(value))) throw new Error('Invalid macro override'); return [name, value];}));
        }
      } catch (failure) {return Promise.reject(error('options-error', failure.message));}
      const dependencies = options.dependencies !== false;
      const selected = this.manifest.profiles.find(value => value.id === profile);
      return new Promise((resolve, reject) => {
        const job = {id, generation, profile, resolve, reject, settled: false, abort: new AbortController(), timer: null, startTimer: null};
        this.active = job;
        if (!selected) {this.settle(job, error('profile-error', 'Unknown profile')); return;}
        const timeout = options.timeout_ms ?? this.options.timeout_ms ?? 60000, startup = this.options.startup_timeout_ms ?? 30000;
        if (!Number.isSafeInteger(timeout) || timeout < 1 || !Number.isSafeInteger(startup) || startup < 1) {this.settle(job, error('options-error', 'Invalid timeout')); return;}
        job.timer = setTimeout(() => this.crash('timeout', 'Analysis exceeded its deadline', generation), timeout);
        job.startTimer = setTimeout(() => this.crash('startup-timeout', 'Engine startup exceeded its deadline', generation), startup);
        this.state('loading-profile', job);
        (async () => {
          try {
            const bytes = await this.asset(selected.asset, job); this.check(job);
            job.source = selected.source;
            if (!this.options.validateReply) {
              const payload = JSON.parse(new TextDecoder('utf-8', {fatal: true}).decode(bytes));
              if (canonical(payload.source) !== canonical(selected.source)) throw new Error('Profile source mismatch');
              job.expectedRequest = {...payload.request, trace_dependencies: dependencies, trace_files: true};
              job.expectedRequest.macros = {...(job.expectedRequest.macros || {}), ...overrides};
            }
            const identity = {runtime_version: 1, compiler: this.manifest.compiler, assets: Object.fromEntries(Object.entries(this.manifest.assets).map(([name, asset]) => [name, asset.sha256]))};
            job.computation_sha256 = await Codec.sha256(new TextEncoder().encode(canonical({identity, profile, source: selected.source, profile_sha256: selected.asset.sha256, overrides, dependencies}))); this.check(job);
            await this.start(job); this.check(job); clearTimeout(job.startTimer);
            this.state('analyzing', job);
            this.worker.postMessage({type: 'analyze', generation, id, profile, profile_bytes: bytes.buffer,
              source: selected.source, overrides, dependencies, computation_sha256: job.computation_sha256}, [bytes.buffer]);
          } catch (failure) {if (this.current(job)) {this.stopWorker(); this.settle(job, failure.code ? failure : error('asset-error', failure.message));}}
        })();
      });
    }
  }
  return {VERSION, Client, validateManifest};
});
