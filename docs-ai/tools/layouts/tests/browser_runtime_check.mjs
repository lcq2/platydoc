// SPDX-License-Identifier: GPL-2.0-only
// Real Chromium check: fresh profile, file://, cache disabled, network offline.
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { resolve, dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { performance } from 'node:perf_hooks';
import { isDeepStrictEqual } from 'node:util';
import { createRequire } from 'node:module';
import { createHash } from 'node:crypto';

const args = process.argv.slice(2);
const harnessSmoke = args.includes('--smoke');
const forceFallback = args.includes('--fallback');
const positional = args.filter(value => !['--smoke', '--fallback'].includes(value));
const [pageArgument, reportArgument, nativeReportArgument, browser = 'chromium'] = positional;
if (!pageArgument || !reportArgument || !nativeReportArgument) throw new Error('Usage: browser_runtime_check.mjs page.html report.json native-comparison.json [chromium] [--smoke] [--fallback]');
const nativeReport = JSON.parse(await readFile(resolve(nativeReportArgument), 'utf8'));
if (nativeReport.wasm_parity !== 'passed' || !nativeReport.dependency_tracing) throw new Error('Passing traced native/Wasm evidence required');
const Contracts = createRequire(import.meta.url)('../browser/contracts.js');
const page = pathToFileURL(resolve(pageArgument)).href;
const reportPath = resolve(reportArgument);
const profile = await mkdtemp(join(dirname(reportPath), 'chromium-profile-'));
const child = spawn(browser, [
  '--headless=new', '--no-first-run', '--no-default-browser-check',
  '--disable-background-networking', '--disable-component-update',
  '--disable-sync', '--disable-default-apps', '--disable-extensions',
  '--disable-breakpad', '--metrics-recording-only', '--password-store=basic',
  '--host-resolver-rules=MAP * ~NOTFOUND', '--remote-debugging-pipe',
  `--user-data-dir=${profile}`, 'about:blank',
], { stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe'], detached: true });
let stderr = '', sequence = 0, wire = Buffer.alloc(0), ended = false;
const pending = new Map(), requests = [], exceptions = [];
const workerSetup = new Set();
const started = performance.now();
const report = {
  harness_sha256: createHash('sha256').update(await readFile(new URL(import.meta.url))).digest('hex'),
  package_manifest_sha256: createHash('sha256').update(await readFile(join(dirname(resolve(pageArgument)), 'manifest.json'))).digest('hex'),
  page, harness_smoke_only: harnessSmoke, fresh_profile: true, network_offline: true, cache_disabled: true,
  request_scope: 'Page and dedicated workers attached before worker execution; browser background targets excluded.',
  worker_targets: [], persistence_disabled: true, force_fallback: forceFallback,
  browser_version: null, requests, exceptions, peak_sampled_process_rss_bytes: 0,
  rss_note: 'Maximum sampled sum of browser-descendant RSS; shared pages may be counted multiple times. Not an exact instantaneous peak.',
};
function rejectPending(error) {
  for (const { reject, timer } of pending.values()) { clearTimeout(timer); reject(error); }
  pending.clear();
}
child.stderr.on('data', data => { stderr = (stderr + data).slice(-16000); });
child.on('error', error => { ended = true; rejectPending(error); });
child.on('exit', (code, signal) => {
  ended = true;
  rejectPending(new Error(`Browser exited (${code ?? signal}): ${stderr}`));
});
child.stdio[3].on('error', error => rejectPending(error));
child.stdio[4].on('data', chunk => {
  wire = Buffer.concat([wire, chunk]);
  let end;
  while ((end = wire.indexOf(0)) !== -1) {
    const text = wire.subarray(0, end).toString();
    wire = wire.subarray(end + 1);
    if (!text) continue;
    let message;
    try { message = JSON.parse(text); }
    catch (error) { rejectPending(error); continue; }
    if (message.id) {
      const waiter = pending.get(message.id);
      if (!waiter) continue;
      clearTimeout(waiter.timer); pending.delete(message.id);
      if (message.error) waiter.reject(new Error(JSON.stringify(message.error)));
      else waiter.resolve(message.result);
    } else if (message.method === 'Network.requestWillBeSent') {
      requests.push({ url: message.params.request.url, type: message.params.type, session: message.sessionId });
    } else if (message.method === 'Network.webSocketCreated') {
      requests.push({ url: message.params.url, type: 'WebSocket' });
    } else if (message.method === 'Network.webTransportCreated') {
      requests.push({ url: message.params.url, type: 'WebTransport' });
    } else if (message.method === 'Target.attachedToTarget') {
      const {sessionId: workerSession, targetInfo} = message.params;
      if (targetInfo.type !== 'worker') continue;
      report.worker_targets.push({id: targetInfo.targetId, url: targetInfo.url, session: workerSession});
      const setup = (async () => {
        await call('Runtime.enable', {}, workerSession);
        await call('Runtime.evaluate', {expression: `Object.defineProperty(globalThis,'indexedDB',{configurable:true,get(){throw new Error('Worker storage disabled by offline runtime test');}})`}, workerSession);
        await call('Network.enable', {}, workerSession);
        await call('Network.setCacheDisabled', {cacheDisabled: true}, workerSession);
        // Chromium workers expose request observation but do not implement
        // independent network emulation. The page is offline and browser-wide
        // host resolution is disabled; any observed remote attempt fails below.
        try {await call('Network.emulateNetworkConditions', {offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0}, workerSession);}
        catch (failure) {if (!failure.message.includes('Not supported')) throw failure; report.worker_network_emulation = 'unsupported; request observation and browser-wide host denial active';}
        await call('Runtime.runIfWaitingForDebugger', {}, workerSession);
      })().catch(error => exceptions.push({worker_setup: error.message}));
      workerSetup.add(setup); setup.finally(() => workerSetup.delete(setup));
    } else if (message.method === 'Runtime.exceptionThrown') {
      exceptions.push(message.params.exceptionDetails);
    }
  }
});
function call(method, params = {}, sessionId, timeoutMs = 20000) {
  if (ended) return Promise.reject(new Error(`Browser unavailable: ${stderr}`));
  const id = ++sequence;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pending.delete(id); reject(new Error(`CDP timeout: ${method}`));
    }, timeoutMs);
    pending.set(id, { resolve, reject, timer });
    child.stdio[3].write(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }) + '\0');
  });
}
async function sampleMemory() {
  try {
    const entries = (await readdir('/proc')).filter(name => /^\d+$/.test(name));
    const processes = await Promise.all(entries.map(async pid => {
      try {
        const status = await readFile(`/proc/${pid}/status`, 'utf8');
        return { pid: Number(pid), parent: Number(status.match(/^PPid:\s+(\d+)/m)?.[1]),
          rss: Number(status.match(/^VmRSS:\s+(\d+)/m)?.[1] || 0) * 1024 };
      } catch { return null; }
    }));
    const descendants = new Set([child.pid]);
    let changed;
    do {
      changed = false;
      for (const p of processes) if (p && descendants.has(p.parent) && !descendants.has(p.pid)) {
        descendants.add(p.pid); changed = true;
      }
    } while (changed);
    const total = processes.reduce((sum, p) => sum + (p && descendants.has(p.pid) ? p.rss : 0), 0);
    report.peak_sampled_process_rss_bytes = Math.max(report.peak_sampled_process_rss_bytes, total);
  } catch (error) { report.rss_unavailable = error.message; }
}
let sampling = false;
const sampler = setInterval(async () => {
  if (sampling) return;
  sampling = true;
  try { await sampleMemory(); } finally { sampling = false; }
}, 100);
try {
  report.browser_version = await call('Browser.getVersion');
  const {targetId} = await call('Target.createTarget', {url: 'about:blank'});
  const {sessionId} = await call('Target.attachToTarget', {targetId, flatten: true});
  for (const domain of ['Page', 'Runtime', 'Network']) await call(domain + '.enable', {}, sessionId);
  await call('Target.setAutoAttach', {autoAttach: true, waitForDebuggerOnStart: true, flatten: true}, sessionId);
  await call('Network.setCacheDisabled', {cacheDisabled: true}, sessionId);
  await call('Network.emulateNetworkConditions', {offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0}, sessionId);
  await call('Page.addScriptToEvaluateOnNewDocument', {source: `
    for (const name of ['localStorage', 'sessionStorage', 'indexedDB']) Object.defineProperty(window, name, {configurable: true, get() {throw new Error('Storage disabled by offline runtime test');}});
    ${forceFallback ? "Object.defineProperty(window, 'DecompressionStream', {value: undefined}); window.layoutRuntimeOptions={force_fallback:true};" : ''}
    window.runtimeHeartbeat={ticks:0,longest_ms:0}; let previous=performance.now();
    setInterval(()=>{const now=performance.now();window.runtimeHeartbeat.longest_ms=Math.max(window.runtimeHeartbeat.longest_ms,now-previous);previous=now;++window.runtimeHeartbeat.ticks;},20);
  `}, sessionId);
  const navigation = await call('Page.navigate', {url: page}, sessionId);
  if (navigation.errorText) throw new Error(navigation.errorText);
  const evaluate = async (expression, timeout = 60000) => {
    const response = await call('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true}, sessionId, timeout);
    if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
    return response.result.value;
  };
  const readyDeadline = performance.now() + 90000;
  while (performance.now() < readyDeadline) {
    const state = await evaluate(`({ready:!!window.layoutRuntimeCurrent, state:window.layoutRuntimeState, error:document.getElementById('layout-error')?.textContent})`);
    if (state.ready) break;
    if (state.error) throw new Error(state.error + ' ' + JSON.stringify(state.state));
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  const initial = await evaluate(`(async()=>{
    const current=window.layoutRuntimeCurrent;
    if (!current) throw new Error('Initial worker analysis did not complete');
    await LayoutContracts.validate(current.contract,{analysis:current.analysis});
    return {profile:current.profile,result_sha256:await LayoutContracts.sha256(LayoutContracts.canonical(current.result)),metrics:current.metrics,client_metrics:window.layoutRuntimeClient.metrics,heartbeat:window.runtimeHeartbeat,has_main_engine:typeof window.createLayoutEngine!=='undefined',dependency_registry:LayoutContracts.dependencyAnalysisCount?.()};
  })()`);
  const native = nativeReport.results[nativeReport.cases.indexOf(initial.profile)];
  const {dependency_trace, ...compact} = native;
  if (initial.result_sha256 !== await Contracts.sha256(Contracts.canonical(compact))) throw new Error('Initial worker result differs from complete native result (trace excluded from page transport)');
  if (initial.has_main_engine || !report.worker_targets.length) throw new Error('Compiler was not isolated in a worker');
  if (initial.heartbeat.ticks < 5) throw new Error('Page did not remain responsive during worker startup');
  const profileLoads = requests.filter(request => request.url.includes('/assets/profile-'));
  if (profileLoads.length !== 1 || !profileLoads[0].url.includes(initial.profile)) throw new Error('Startup loaded unselected profile bundles');
  report.initial = initial;
  report.checks = ['fresh offline file startup', 'storage disabled', 'only selected profile loaded', 'worker compiler isolation', 'complete native layout parity', 'page heartbeat during analysis'];
  if (!harnessSmoke) {
    const assertNative = async (value, name) => {
      const golden = nativeReport.results[nativeReport.cases.indexOf(name)];
      if (!golden) throw new Error('Missing native case: ' + name);
      const {dependency_trace, ...compact} = golden;
      if (value.sha !== await Contracts.sha256(Contracts.canonical(compact))) throw new Error('Native parity failed: ' + name);
    };
    const waitUI = async () => {
      const deadline = performance.now() + 60000;
      while (performance.now() < deadline) {
        const value = await evaluate(`(async()=>{const c=window.layoutRuntimeCurrent;return c?{profile:c.profile,sha:await LayoutContracts.sha256(LayoutContracts.canonical(c.result)),metrics:c.metrics}:null})()`);
        if (value) return value;
        const failure = await evaluate(`document.getElementById('layout-error').textContent`);
        if (failure) throw new Error(failure);
        await new Promise(resolve=>setTimeout(resolve,50));
      }
      throw new Error('UI analysis deadline');
    };
    report.profiles = [];
    for (const profile of ['development-t8103','development-vmapple','release-vmapple','release-t8103']) {
      const cleared = await evaluate(`(()=>{const p=document.getElementById('layout-profile');p.value=${JSON.stringify(profile)};p.dispatchEvent(new Event('change'));return !window.layoutRuntimeCurrent&&!document.getElementById('layout-tree').childElementCount;})()`);
      if (!cleared) throw new Error('Profile change retained stale offsets');
      const value = await waitUI(); await assertNative(value,profile); report.profiles.push(value);
    }
    await evaluate(`(()=>{const e=document.getElementById('layout-directives');e.value='#define CONFIG_PERVASIVE_CPI 0';e.dispatchEvent(new Event('input'));if(window.layoutRuntimeCurrent||document.getElementById('layout-tree').childElementCount)throw new Error('Edited directives retained stale layout');document.getElementById('layout-apply').click();})()`);
    report.manual = await waitUI(); await assertNative(report.manual,'probe-no-cpi');
    report.checks.push('four profiles match complete native layouts','profile and directive edits immediately clear stale offsets','manual directive matches native what-if');
    report.lifecycle = await evaluate(`(async()=>{
      const results=[]; const assert=(condition,message)=>{if(!condition)throw new Error(message);results.push(message);};
      const original=window.layoutRuntimeClient;original.dispose();
      let action=null; const states=[];
      const c=new LayoutRuntime.Client(window.layoutRuntimeManifest,{onstate:s=>{states.push(s.state);if(s.state==='compiling'&&action){const f=action;action=null;f();}}});
      action=()=>c.cancel();
      const cancelled=await c.analyze('release-t8103').then(()=>null,e=>e.code);
      assert(cancelled==='cancelled'&&c.worker===null,'cancel after real compile ACK terminates worker');
      let newer;
      action=()=>{newer=c.analyze('release-vmapple');};
      const replaced=await c.analyze('release-t8103').then(()=>null,e=>e.code);
      assert(replaced==='superseded','running compiler request settles as superseded');
      const replacement=await newer;
      assert(replacement.profile==='release-vmapple'&&replacement.result.status==='ok','replacement after running compile wins');
      const first=c.analyze('development-t8103').then(()=>null,e=>e.code);
      const last=c.analyze('release-t8103');
      assert(await first==='superseded','pending asset load settles as superseded');
      assert((await last).profile==='release-t8103','latest request wins during asset loading');
      const timed=await c.analyze('release-t8103',{timeout_ms:1}).then(()=>null,e=>e.code);
      assert(timed==='timeout'&&c.worker===null,'deadline terminates worker and settles');
      assert((await c.analyze('release-t8103')).result.status==='ok','valid request recovers after timeout');
      const asset=c.manifest.profiles.find(p=>p.id==='development-vmapple').asset, saved=asset.url;
      c.assetCache.clear();c.assetCacheBytes=0;asset.url='assets/intentionally-missing.js';
      const missing=await c.analyze('development-vmapple').then(()=>null,e=>e.code);asset.url=saved;
      assert(missing==='asset-error','missing local asset reports recoverable failure');
      assert((await c.analyze('development-vmapple')).result.status==='ok','valid request recovers after missing asset');
      assert(c.metrics.worker_starts===c.metrics.worker_terminations,'default memory retirement releases every real XNU worker');
      const metrics={...c.metrics};c.dispose();assert(c.assetCacheBytes===0&&!c.active&&!c.worker,'dispose releases worker, active job and decoded asset cache');
      return {checks:results,metrics,states};
    })()`,120000);
    report.cache = await evaluate(`(async()=>{
      const c=new LayoutRuntime.Client(window.layoutRuntimeManifest,{limits:{cache_entries:2,cache_bytes:64*1024*1024,max_linear_memory_bytes:1024*1024*1024}});
      const a=await c.analyze('release-t8103');const b=await c.analyze('release-t8103');
      if(!b.metrics.cache_hit||b.metrics.analyses!==a.metrics.analyses)throw new Error('Warm exact request did not reuse result');
      const custom=await c.analyze('release-t8103',{overrides:{CONFIG_PERVASIVE_CPI:'0'}});
      if(custom.metrics.cache_hit)throw new Error('Changed directives reused stale cache');
      const again=await c.analyze('release-t8103');
      if(again.metrics.cache_hit)throw new Error('Expected two-entry LRU eviction did not occur');
      for(const value of [a,b,custom,again])if(value.metrics.cache_entries>2||value.metrics.cache_serialized_bytes>64*1024*1024)throw new Error('Cache exceeded configured bounds');
      const repeated=[];
      for(let i=0;i<12;i++){
        const hit=await c.analyze('release-t8103');
        if(!hit.metrics.cache_hit||hit.metrics.analyses!==again.metrics.analyses||hit.metrics.linear_memory_bytes!==again.metrics.linear_memory_bytes||hit.metrics.cache_entries!==again.metrics.cache_entries||hit.metrics.cache_serialized_bytes!==again.metrics.cache_serialized_bytes)throw new Error('Repeated warm requests grew retained compiler/cache state');
        repeated.push(hit.metrics);
      }
      const result={checks:['warm exact-request cache hit','changed directives miss','two-entry LRU eviction','serialized-byte and entry bounds','12 repeated warm requests retain stable compiler capacity and cache size'],metrics:[a.metrics,b.metrics,custom.metrics,again.metrics],repeated,client:{...c.metrics}};c.dispose();return result;
    })()`,90000);
    report.checks.push(...report.lifecycle.checks,...report.cache.checks);
    // Restore a working proof for the final screenshot, including its UI handlers.
    await call('Page.reload', {ignoreCache:true},sessionId);
    await waitUI();
  }
  await sampleMemory();
  await call('Emulation.setDeviceMetricsOverride', {width:1280,height:1100,deviceScaleFactor:1,mobile:false}, sessionId);
  const screenshot = await call('Page.captureScreenshot', {format:'png',captureBeyondViewport:false}, sessionId);
  report.preview_screenshot = reportPath.replace(/\.json$/, '') + '-preview.png';
  await writeFile(report.preview_screenshot, Buffer.from(screenshot.data,'base64'));
  if (requests.some(request => /^https?:|^wss?:/i.test(request.url))) throw new Error('Runtime attempted a network request');
  await Promise.all([...workerSetup]);
  if (exceptions.length) throw new Error('Browser or worker exception: ' + JSON.stringify(exceptions));
  report.status='passed';
} catch (error) {
  report.status = 'failed'; report.error = error.stack || String(error);
  process.exitCode = 1;
} finally {
  clearInterval(sampler);
  report.elapsed_ms = performance.now() - started;
  report.browser_stderr = stderr;
  try { if (!ended) await call('Browser.close'); } catch { /* Pipe can close before acknowledgement. */ }
  try { process.kill(-child.pid, 'SIGTERM'); } catch { /* Already exited. */ }
  await new Promise(resolve => setTimeout(resolve, 300));
  try { process.kill(-child.pid, 'SIGKILL'); } catch { /* Already exited. */ }
  rejectPending(new Error('Browser check finished'));
  await writeFile(reportPath, JSON.stringify(report, null, 2) + '\n');
  await rm(profile, { recursive: true, force: true });
  console.log(JSON.stringify({ status: report.status, report: reportPath, metrics: report.metrics,
    peak_sampled_process_rss_bytes: report.peak_sampled_process_rss_bytes, error: report.error }, null, 2));
}
