// SPDX-License-Identifier: GPL-2.0-only
// Real Chromium check: fresh profile, file://, cache disabled, network offline.
import { spawn } from 'node:child_process';
import { createReadStream } from 'node:fs';
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
if (!pageArgument || !reportArgument || !nativeReportArgument) throw new Error('Usage: browser_explorer_check.mjs page.html report.json native-comparison.json [chromium] [--smoke] [--fallback]');
const nativeReport = JSON.parse(await readFile(resolve(nativeReportArgument), 'utf8'));
if (nativeReport.wasm_parity !== 'passed' || !nativeReport.dependency_tracing || !Array.isArray(nativeReport.results) || nativeReport.results.length!==nativeReport.cases?.length) throw new Error('Passing traced native/Wasm evidence required');
// Page transport deliberately excludes the enormous raw dependency traces.
// Keep native compiler layouts for full digest parity and independent arithmetic.
for(const result of nativeReport.results)delete result.dependency_trace;
const Contracts = createRequire(import.meta.url)('../browser/contracts.js');
const page = pathToFileURL(resolve(pageArgument)).href;
const reportPath = resolve(reportArgument);
// Validate proof inputs before creating a browser process or temporary profile.
async function fileHash(path){const hash=createHash('sha256');for await(const bytes of createReadStream(path))hash.update(bytes);return hash.digest('hex');}
const [harnessHash,manifestHash,evidenceHash]=await Promise.all([
  fileHash(new URL(import.meta.url)),
  fileHash(join(dirname(resolve(pageArgument)), 'manifest.json')),
  fileHash(resolve(nativeReportArgument)),
]);
const inputHashes={harness_sha256:harnessHash,package_manifest_sha256:manifestHash,native_comparison_sha256:evidenceHash};
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
  ...inputHashes, native_comparison: resolve(nativeReportArgument),
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
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const expectedHashes = new Map();
async function assertNative(value, name) {
  const index = nativeReport.cases.indexOf(name);
  assert(index >= 0, 'Missing native case: ' + name);
  if (!expectedHashes.has(name)) {
    const {dependency_trace, ...compact} = nativeReport.results[index];
    expectedHashes.set(name, await Contracts.sha256(Contracts.canonical(compact)));
  }
  assert(value.sha === expectedHashes.get(name), 'Complete native layout parity failed: ' + name);
}
function nativeField(name, path) {
  const result = nativeReport.results[nativeReport.cases.indexOf(name)];
  const records = new Map(result.records.map(record => [record.id, record]));
  const parts = path.split('.'),rootName=parts.shift();
  let record = result.records.find(record => record.name === rootName), total = 0, local = 0, type, bitWidth=null;
  assert(record, 'Missing native root: ' + path);
  for (const part of parts) {
    const match = /^(\w+)(?:\[(\d+)\])?$/.exec(part);
    assert(match, 'Unsupported acceptance path: ' + path);
    const field = record.fields.find(field => field.name === match[1]);
    assert(field, 'Missing native field: ' + path);
    local = field.offset_bits; total += local; type = field.type; bitWidth=field.bit_width;
    if (match[2] !== undefined) {
      assert(type.kind === 'array', 'Native field is not an array: ' + path);
      const index = Number(match[2]);
      assert(type.count === null || index < type.count, 'Native array index out of range');
      local = index * type.element.size_bits; total += local; type = type.element; bitWidth=null;
    }
    if (type.kind === 'record') record = records.get(type.record_id);
  }
  return {root_bits: total, local_bits: local, size_bits: type.size_bits,bit_width:bitWidth};
}
try {
  report.browser_version = await call('Browser.getVersion');
  await call('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:profile});
  report.downloads_confined_to_temporary_profile=true;
  const {targetId} = await call('Target.createTarget', {url: 'about:blank'});
  const {sessionId} = await call('Target.attachToTarget', {targetId, flatten: true});
  for (const domain of ['Page', 'Runtime', 'Network']) await call(domain + '.enable', {}, sessionId);
  await call('Target.setAutoAttach', {autoAttach: true, waitForDebuggerOnStart: true, flatten: true}, sessionId);
  await call('Network.setCacheDisabled', {cacheDisabled: true}, sessionId);
  await call('Network.emulateNetworkConditions', {offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0}, sessionId);
  await call('Page.addScriptToEvaluateOnNewDocument', {source: `
    for (const name of ['localStorage','sessionStorage','indexedDB']) Object.defineProperty(window,name,{configurable:true,get(){throw new Error('Storage disabled by offline explorer test');}});
    ${forceFallback ? "Object.defineProperty(window,'DecompressionStream',{value:undefined});window.layoutRuntimeOptions={force_fallback:true};" : ''}
    window.explorerHeartbeat={ticks:0,longest_ms:0};let previous=performance.now();
    setInterval(()=>{const now=performance.now();window.explorerHeartbeat.longest_ms=Math.max(window.explorerHeartbeat.longest_ms,now-previous);previous=now;++window.explorerHeartbeat.ticks;},20);
  `}, sessionId);
  const evaluate = async (expression, timeout = 60000) => {
    const response = await call('Runtime.evaluate', {expression, awaitPromise:true, returnByValue:true}, sessionId, timeout);
    if (response.exceptionDetails) throw new Error(JSON.stringify(response.exceptionDetails));
    return response.result.value;
  };
  const waitFor = async (expression, label, timeout = 90000) => {
    const deadline = performance.now() + timeout;
    while (performance.now() < deadline) {
      let value;
      try {value=await evaluate(expression);}
      catch(error){if(!/Execution context was destroyed|Cannot find context|Inspected target navigated/i.test(error.message))throw error;}
      if (value) return value;
      await new Promise(resolve => setTimeout(resolve, 80));
    }
    const state = await evaluate(`({state:window.layoutExplorerState,status:document.getElementById('explorer-status')?.textContent,error:document.getElementById('explorer-error')?.textContent})`);
    throw new Error(label + ' deadline: ' + JSON.stringify(state));
  };
  const waitUI = async (profileName) => waitFor(`(async()=>{
    const c=window.layoutExplorerCurrent;
    if(!c||${profileName ? `c.profile!==${JSON.stringify(profileName)}||` : ''}c.result?.status!=='ok'||window.layoutRuntimeClient?.active)return null;
    await LayoutContracts.validate(c.contract,{analysis:c.analysis});
    const sha=await LayoutContracts.sha256(LayoutContracts.canonical(c.result));
    // Navigation or a new request may invalidate the result during validation.
    // Retry only that transition; actual validation failures remain fatal.
    if(window.layoutExplorerCurrent!==c||window.layoutRuntimeClient?.active)return null;
    return {profile:c.profile,sha,root_name:c.root_name,root_id:c.root_id,selected:c.selected?{path:c.selected.path,root_bits:c.selected.rootBits??c.selected.root_offset_bits,local_bits:c.selected.localBits??c.selected.local_offset_bits,presence:c.selected.presence,field_id:c.selected.fieldId}:null,state:window.layoutExplorerState,metrics:c.metrics,heartbeat:window.explorerHeartbeat};
  })()`,'Explorer analysis');
  const event = async (id, value, type = 'change') => evaluate(`(()=>{const e=document.getElementById(${JSON.stringify(id)});if(!e)throw new Error('Missing UI control: '+${JSON.stringify(id)});${typeof value === 'boolean' ? `e.checked=${value}` : `e.value=${JSON.stringify(value)}`};e.dispatchEvent(new Event(${JSON.stringify(type)},{bubbles:true}));})()`);
  const click = async id => evaluate(`(()=>{const e=document.getElementById(${JSON.stringify(id)});if(!e)throw new Error('Missing UI button: '+${JSON.stringify(id)});e.click();})()`);
  const assertCleared = async label => {
    const stale = await evaluate(`({current:!!window.layoutExplorerCurrent,rows:document.querySelectorAll('#layout-tree [data-root-bits]').length,root:document.getElementById('selected-root')?.textContent,size:document.getElementById('size-value')?.textContent})`);
    assert(!stale.current && stale.rows === 0, label + ' retained stale offsets: ' + JSON.stringify(stale));
  };
  const field = async (path, nativeName = 'release-t8103') => {
    await evaluate(`window.layoutExplorer.selectField(${JSON.stringify(path)})`);
    const actual = await evaluate(`(()=>{const c=window.layoutExplorerCurrent,s=c.selected;const row=[...document.querySelectorAll('.declaration-row')].find(e=>e.dataset.path===${JSON.stringify(path)});return {path:s?.path,root_bits:s?.rootBits??s?.root_offset_bits,local_bits:s?.localBits??s?.local_offset_bits,presence:s?.presence,bit_width:s?.bitWidth,row_root:row?.dataset.rootBits,row_local:row?.dataset.localBits,inspector:document.getElementById('selected-path')?.textContent};})()`);
    const expected = nativeField(nativeName, path);
    assert(actual.path === path, 'Field selection failed: ' + path + ' ' + JSON.stringify(actual));
    assert(actual.root_bits === expected.root_bits && actual.local_bits === expected.local_bits,
      'Compiler offset arithmetic failed: ' + path + ' ' + JSON.stringify({actual,expected}));
    assert(Number(actual.row_root) === expected.root_bits && Number(actual.row_local) === expected.local_bits,
      'Rendered offsets differ from native evidence: ' + path);
    assert(actual.bit_width===expected.bit_width,'Rendered bitfield width differs from native evidence: '+path);
    assert(actual.inspector.includes(path), 'Selected field inspector did not follow selection');
    return {path, actual, expected};
  };
  const navigate = await call('Page.navigate', {url:page}, sessionId);
  if (navigate.errorText) throw new Error(navigate.errorText);
  report.initial = await waitUI();
  await assertNative(report.initial, report.initial.profile);
  assert(report.worker_targets.length > 0, 'Compiler did not start in a dedicated worker');
  assert(await evaluate(`typeof window.createLayoutEngine==='undefined'`), 'Compiler leaked into main page');
  assert(report.initial.heartbeat.ticks >= 5, 'Page heartbeat did not run during real compilation');
  const profileLoads = requests.filter(request => request.url.includes('/assets/profile-'));
  assert(profileLoads.length === 1 && profileLoads[0].url.includes(report.initial.profile), 'Startup loaded unselected profiles');
  report.checks = ['fresh offline file startup with persistent storage disabled','only selected profile loaded','dedicated worker compiler isolation','complete native result parity','page heartbeat during real analysis'];
  report.field_paths = [];
  if (!harnessSmoke) {
    report.profiles = [];
    for (const name of ['development-t8103','development-vmapple','release-vmapple','release-t8103']) {
      await event('profile-select',name); await assertCleared('Profile edit');
      const value=await waitUI(name);await assertNative(value,name);report.profiles.push(value);
    }
    report.checks.push('all four profile UI selections match complete native results','profile edits immediately clear stale results');
    report.field_paths.push(await field('recount_track.rt_usage.ru_metrics[1].rm_cycles'));
    await evaluate(`(()=>{const input=document.querySelector('[data-array-path="recount_track.rt_usage.ru_metrics"]');if(!input)throw new Error('Missing array index control');input.value='0';input.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    report.field_paths.push(await field('recount_track.rt_usage.ru_metrics[0].rm_cycles'));
    await evaluate(`(()=>{const input=document.querySelector('[data-array-path="recount_track.rt_usage.ru_metrics"]');input.value='1';input.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    report.field_paths.push(await field('recount_track.rt_usage.ru_metrics[1].rm_cycles'));
    const rootCount=await evaluate(`document.getElementById('root-select').options.length`);
    await event('structure-search','task','input');
    assert(await evaluate(`(()=>{const options=[...document.getElementById('root-select').options];return options.length>0&&options.some(o=>o.textContent.includes('task'))&&options.length<=${rootCount};})()`),'Structure search did not retain matching root');
    await event('structure-search','','input');
    await event('field-search','__no_matching_field__','input');
    assert(await evaluate(`[...document.querySelectorAll('#layout-tree .field-select')].every(e=>!e.getClientRects().length)`),'Field search retained nonmatching fields');
    await event('field-search','rm_cycles','input');
    assert(await evaluate(`[...document.querySelectorAll('#layout-tree .field-select')].some(e=>e.getClientRects().length&&e.textContent.includes('rm_cycles'))`),'Field search hid matching field');
    await event('field-search','','input');
    await click('decimal-button');
    assert(await evaluate(`document.getElementById('decimal-button').getAttribute('aria-pressed')==='true'`),'Decimal control not selected');
    assert(await evaluate(`!document.getElementById('selected-root').textContent.includes('0x')`),'Decimal selection retained hexadecimal inspector offset');
    await click('hex-button');
    assert(await evaluate(`document.getElementById('selected-root').textContent.includes('0x')`),'Hex selection did not update inspector offset');
    const firstPath=await evaluate(`(()=>{const e=document.querySelector('#layout-tree .field-select');e.focus();return e.closest('[data-path]').dataset.path;})()`);
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowDown',code:'ArrowDown',windowsVirtualKeyCode:40},sessionId);
    await call('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowDown',code:'ArrowDown',windowsVirtualKeyCode:40},sessionId);
    const keyboardPath=await evaluate(`document.activeElement?.closest('.declaration-row')?.dataset.path`);
    assert(keyboardPath&&keyboardPath!==firstPath,'ArrowDown did not move field focus');
    report.keyboard={first:firstPath,moved:keyboardPath,before:await evaluate(`({active:document.activeElement?.outerHTML,selected:window.layoutExplorerCurrent?.selected?.path})`)};
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'Enter',code:'Enter',windowsVirtualKeyCode:13,nativeVirtualKeyCode:13,text:'\r',unmodifiedText:'\r'},sessionId);
    await call('Input.dispatchKeyEvent',{type:'keyUp',key:'Enter',code:'Enter',windowsVirtualKeyCode:13},sessionId);
    report.keyboard.after=await evaluate(`({active:document.activeElement?.outerHTML,selected:window.layoutExplorerCurrent?.selected?.path})`);
    assert(report.keyboard.after.selected===keyboardPath,'Enter did not select focused field: '+JSON.stringify(report.keyboard));
    await call('Input.dispatchKeyEvent',{type:'keyDown',key:'/',code:'Slash',text:'/'},sessionId);
    await call('Input.dispatchKeyEvent',{type:'keyUp',key:'/',code:'Slash'},sessionId);
    assert(await evaluate(`document.activeElement?.id==='field-search'`),'Slash keyboard shortcut did not focus field search');
    report.checks.push('array index UI accumulates native element stride and parent offsets','structure and field search and numeric format controls','keyboard field movement, selection and search shortcut');

    await click('pin-comparison');
    await event('cpi-toggle',false);await assertCleared('CPI edit');
    report.cpi=await waitUI('release-t8103');await assertNative(report.cpi,'probe-no-cpi');
    await event('show-excluded',true);await click('expand-all');
    report.excluded=await evaluate(`(()=>{const rows=[...document.querySelectorAll('.excluded-field')];return {count:rows.length,cycles:rows.filter(e=>e.textContent.includes('rm_cycles')).map(e=>({text:e.textContent,root:e.getAttribute('data-root-bits'),local:e.getAttribute('data-local-bits')})),summary:document.getElementById('comparison-summary').textContent,shifted:document.querySelectorAll('[data-change~="shifted"]').length,removed:document.querySelectorAll('[data-change~="removed"]').length};})()`);
    assert(report.excluded.cycles.length>0,'Removed CPI field was not shown as excluded');
    assert(report.excluded.cycles.every(row=>row.root===null&&row.local===null),'Excluded fields retained stale numeric offsets');
    assert(report.excluded.summary.trim().length>0,'Comparison did not explain changed layout');
    assert(report.excluded.shifted>0&&report.excluded.removed>0,'Comparison did not highlight shifted and removed fields');
    await evaluate(`window.layoutExplorer.selectField('recount_track.rt_usage.ru_metrics[1].rm_cycles')`);
    report.excluded.inspector=await evaluate(`({presence:window.layoutExplorerCurrent.selected.presence,root:window.layoutExplorerCurrent.selected.rootBits,local:window.layoutExplorerCurrent.selected.localBits,label:document.getElementById('selected-root').textContent,evidence:document.getElementById('field-evidence').textContent})`);
    assert(report.excluded.inspector.presence==='absent'&&report.excluded.inspector.root===null&&report.excluded.inspector.local===null,'Excluded inspector retained old numeric offsets');
    assert(report.excluded.inspector.evidence.includes('CONFIG_PERVASIVE_CPI'),'Excluded field lacks source condition evidence');
    report.field_paths.push(await field('recount_track.rt_usage.ru_energy_nj','probe-no-cpi'));
    report.field_paths.push(await field('recount_track.rt_usage.ru_metrics[1].rm_time_mach','probe-no-cpi'));
    report.descendant_shift=await evaluate(`(()=>{const row=[...document.querySelectorAll('.declaration-row')].find(e=>e.dataset.path==='recount_track.rt_usage.ru_metrics[1].rm_time_mach');return {change:row?.dataset.change,root:row?.dataset.rootBits,local:row?.dataset.localBits,comparison:window.layoutExplorerCurrent.selected.comparison};})()`);
    assert(/shift/.test(report.descendant_shift.change||''),'Array-stride descendant root shift was not highlighted despite unchanged local offset');
    const beforeStride=nativeField('release-t8103','recount_track.rt_usage.ru_metrics[1].rm_time_mach'),afterStride=nativeField('probe-no-cpi','recount_track.rt_usage.ru_metrics[1].rm_time_mach');
    assert(isDeepStrictEqual(report.descendant_shift.comparison,{before_root_bits:beforeStride.root_bits,after_root_bits:afterStride.root_bits,before_local_bits:beforeStride.local_bits,after_local_bits:afterStride.local_bits}),'Descendant comparison before/after root and local offsets differ from native evidence');
    report.checks.push('comparison highlights descendant root shift caused by changed array stride');
    report.checks.push('live CPI flag matches native what-if','removed fields show exclusion evidence without offsets','pinned comparison survives configuration change');
    await click('pin-comparison');
    await event('energy-toggle',false);await assertCleared('Energy edit');
    report.neither=await waitUI('release-t8103');await assertNative(report.neither,'probe-neither-counter');
    await click('reset-profile');report.reset=await waitUI('release-t8103');await assertNative(report.reset,'release-t8103');
    await click('expand-all');
    report.added=await evaluate(`({count:document.querySelectorAll('[data-change~="added"]').length,summary:document.getElementById('comparison-summary').textContent})`);
    assert(report.added.count>0,'Comparison did not highlight fields added when CPI returned');
    report.checks.push('comparison highlights added, removed and shifted fields with size changes');
    await event('raw-directives','#define CONFIG_TASK_SUSPEND_STATS 0','input');
    await assertCleared('Manual directive edit');await click('apply-directives');
    report.manual=await waitUI('release-t8103');await assertNative(report.manual,'probe-defined-zero-task-suspend');
    report.checks.push('combined flags match independent native result','reset restores original profile','manual defined-zero directive matches native #ifdef behavior');

    // Reopen the full manually edited selection, including an array index.
    await field('recount_track.rt_usage.ru_metrics[1].rm_cycles','probe-defined-zero-task-suspend');
    const saved=await evaluate(`({hash:location.hash,state:JSON.parse(JSON.stringify(window.layoutExplorerState)),path:window.layoutExplorerCurrent.selected.path,root:window.layoutExplorerCurrent.root_name,profile:window.layoutExplorerCurrent.profile})`);
    await evaluate(`window.__explorerOldDocument=true`);
    await call('Page.reload',{ignoreCache:true},sessionId);
    await waitFor(`typeof window.__explorerOldDocument==='undefined'&&!!window.layoutExplorerCurrent`,'Reload commits new document');
    report.restored=await waitUI(saved.profile);await assertNative(report.restored,'probe-defined-zero-task-suspend');
    const reopened=await evaluate(`({hash:location.hash,state:JSON.parse(JSON.stringify(window.layoutExplorerState)),path:window.layoutExplorerCurrent.selected.path,root:window.layoutExplorerCurrent.root_name,profile:window.layoutExplorerCurrent.profile})`);
    assert(isDeepStrictEqual(reopened,saved),'Reload did not restore complete fragment selection: '+JSON.stringify({saved,reopened}));
    report.bookmark={saved,reopened};
    await evaluate(`location.hash='#layout=%'`);
    await waitFor(`!window.layoutExplorerCurrent&&!document.getElementById('explorer-error').hidden&&document.getElementById('explorer-error').textContent.trim()`,'Malformed bookmark diagnostics');
    await assertCleared('Malformed bookmark');
    report.malformed_bookmark=await evaluate(`document.getElementById('explorer-error').textContent`);
    await evaluate(`location.hash=${JSON.stringify(saved.hash)}`);
    const afterMalformed=await waitUI(saved.profile);await assertNative(afterMalformed,'probe-defined-zero-task-suspend');
    assert(await evaluate(`window.layoutExplorerCurrent.selected.path===${JSON.stringify(saved.path)}`),'Valid bookmark did not recover selected field');
    report.checks.push('malformed bookmark clears offsets and reports diagnostic','valid bookmark recovers after malformed fragment');
    await evaluate(`(()=>{const e=document.getElementById('root-select');const o=[...e.options].find(o=>o.textContent.trim()==='task');if(!o)throw new Error('Missing task root');e.value=o.value;e.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    await waitFor(`window.layoutExplorerCurrent?.root_name==='task'`,'Task root selection');
    const nextHash=await evaluate(`location.hash`);
    await evaluate(`history.back()`);
    await waitFor(`location.hash===${JSON.stringify(saved.hash)}&&window.layoutExplorerCurrent?.selected?.path===${JSON.stringify(saved.path)}`,'Back restores selected field and array');
    await waitUI(saved.profile);
    await evaluate(`history.forward()`);
    await waitFor(`location.hash===${JSON.stringify(nextHash)}&&window.layoutExplorerCurrent?.root_name==='task'`,'Forward restores root');
    await waitUI(saved.profile);
    report.checks.push('fragment reload restores profile, root, field, array and manual overrides','browser back and forward restore explorer state');

    await evaluate(`(()=>{const bad=JSON.parse(JSON.stringify(window.layoutExplorerState));bad.indices={garbage:1};location.hash=LayoutExplorerModel.encodeState(bad);})()`);
    await waitFor(`!window.layoutExplorerCurrent&&!window.layoutRuntimeClient.active&&!document.getElementById('explorer-error').hidden&&document.getElementById('explorer-error').textContent.trim()`,'Semantic bookmark diagnostics');
    await assertCleared('Semantically invalid bookmark');
    report.semantic_bookmark_error=await evaluate(`document.getElementById('explorer-error').textContent`);
    await click('reset-profile');const afterSemantic=await waitUI('release-t8103');await assertNative(afterSemantic,'release-t8103');
    assert(await evaluate(`!Object.hasOwn(window.layoutExplorerState.indices,'garbage')`),'Reset retained invalid bookmark array selector');
    report.checks.push('semantically invalid array bookmark clears offsets and reports diagnostic','profile reset removes invalid view keys and recovers');
    await event('raw-directives','#define CONFIG_PERVASIVE_CPI )','input');await assertCleared('Invalid compiler directive edit');
    await click('apply-directives');
    await waitFor(`!window.layoutRuntimeClient.active&&!document.getElementById('explorer-error').hidden&&document.getElementById('explorer-error').textContent.trim()`,'Real compiler diagnostic');
    report.compiler_error=await evaluate(`({diagnostic:document.getElementById('explorer-error').textContent,validCurrent:window.layoutExplorerCurrent?.result?.status==='ok',rows:document.querySelectorAll('#layout-tree [data-root-bits]').length,selected:document.getElementById('selected-root').textContent,size:document.getElementById('size-value').textContent})`);
    assert(!report.compiler_error.validCurrent&&report.compiler_error.rows===0,'Compiler error retained valid offsets');
    await click('reset-profile');const recoveredCompiler=await waitUI('release-t8103');await assertNative(recoveredCompiler,'release-t8103');
    report.checks.push('real compiler syntax failure shows diagnostics without stale offsets','profile reset recovers after compiler failure');
    await evaluate(`window.layoutExplorer.selectRoot('task')`);
    report.field_paths.push(await field('task.requested_policy.trp_ext_darwinbg'));
    assert(await evaluate(`document.getElementById('selected-root').textContent.includes('1b')&&/^1 bits?$/.test(document.getElementById('selected-size').textContent)`),'Real task bitfield lost its bit position or width');
    report.checks.push('real task bitfield retains bit remainder and native width');
    report.field_paths.push(await field('task.tasks.next'));
    await evaluate(`(()=>{const b=document.querySelector('[data-follow-pointer="task.tasks.next"]');if(!b)throw new Error('Supported pointer has no follow action');b.click();})()`);
    await waitFor(`window.layoutExplorerCurrent?.root_name==='queue_entry'`,'Pointer follows separate object root');
    report.field_paths.push(await field('queue_entry.prev'));
    await evaluate(`window.layoutExplorer.selectRoot('task')`);await event('show-padding',true);await click('expand-all');
    report.padding=await evaluate(`({count:document.querySelectorAll('.padding-row').length,text:[...document.querySelectorAll('.padding-row')].slice(0,4).map(e=>e.textContent)})`);
    assert(report.padding.count>0,'Real task padding was not visualized');
    report.checks.push('following pointer resets offsets to separate object root','real task padding is visible');
    await evaluate(`window.layoutExplorer.selectRoot('lck_mtx_state')`);
    report.field_paths.push(await field('lck_mtx_state.data'));
    report.field_paths.push(await field('lck_mtx_state.val'));
    assert(await evaluate(`/overlap/i.test(document.getElementById('layout-tree').textContent)`),'Union view did not explain overlapping storage');
    report.checks.push('real XNU union alternatives retain overlapping native offsets');

    // Use actual UI cancellation at the worker compile acknowledgement.
    await evaluate(`(()=>{window.__explorerCancelObserved=false;const c=window.layoutRuntimeClient,original=c.options.onstate;c.options.onstate=s=>{original?.(s);if(s.state==='compiling'&&!window.__explorerCancelObserved){window.__explorerCancelObserved=true;document.getElementById('cancel-analysis').click();c.options.onstate=original;}};const p=document.getElementById('profile-select');p.value='development-t8103';p.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    await waitFor(`window.__explorerCancelObserved&&!window.layoutRuntimeClient.active`,'UI cancellation after real compiler ACK');
    await assertCleared('Cancelled analysis');
    assert(await evaluate(`/cancel/i.test(document.getElementById('explorer-status').textContent+' '+document.getElementById('explorer-error').textContent)`),'Cancelled UI lacks useful state');
    await event('profile-select','release-t8103');report.after_cancel=await waitUI('release-t8103');await assertNative(report.after_cancel,'release-t8103');
    await evaluate(`(()=>{window.__explorerReplacementObserved=false;const c=window.layoutRuntimeClient,original=c.options.onstate;c.options.onstate=s=>{original?.(s);if(s.state==='compiling'&&!window.__explorerReplacementObserved){window.__explorerReplacementObserved=true;c.options.onstate=original;const p=document.getElementById('profile-select');p.value='release-vmapple';p.dispatchEvent(new Event('change',{bubbles:true}));}};const p=document.getElementById('profile-select');p.value='development-vmapple';p.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    await waitFor(`window.__explorerReplacementObserved`,'Running compiler replacement');
    report.supersession=await waitUI('release-vmapple');await assertNative(report.supersession,'release-vmapple');
    assert(await evaluate(`document.getElementById('profile-select').value===window.layoutExplorerCurrent.profile`),'Stale request overwrote selected profile');
    report.checks.push('real UI cancel terminates in-progress compiler and clears offsets','valid analysis recovers after cancellation','new profile supersedes in-progress compiler without stale publication');

    // Source action must work inside the standalone package without a handbook build.
    await evaluate(`window.layoutExplorer.selectRoot('recount_track')`);
    await field('recount_track.rt_usage.ru_metrics[1].rm_time_mach','release-vmapple');
    report.source=await evaluate(`(()=>{const a=document.getElementById('selected-source');return {url:a&&!a.hidden?a.href:null,location:document.getElementById('source-location')?.textContent};})()`);
    if(report.source.url){
      const url=new URL(report.source.url);assert(url.protocol==='file:','Source action is not local');
      await readFile(url);
    }
    report.source_download=await evaluate(`(async()=>{const config=window.layoutExplorerConfig,saved=config.sourceLinks;const create=URL.createObjectURL;let captured=null;try{config.sourceLinks={};window.layoutExplorer.selectField('recount_track.rt_usage.ru_metrics[1].rm_time_mach');const button=document.getElementById('download-source');if(!button||button.hidden)throw new Error('Standalone source download is unavailable');URL.createObjectURL=function(blob){captured=blob;return create.call(this,blob);};button.click();if(!captured)throw new Error('Source action did not create a Blob');const bytes=new Uint8Array(await captured.arrayBuffer());return {sha256:await LayoutCodec.sha256(bytes),bytes:bytes.length,mappedLinkHidden:document.getElementById('selected-source').hidden};}finally{URL.createObjectURL=create;config.sourceLinks=saved;window.layoutExplorer.selectField('recount_track.rt_usage.ru_metrics[1].rm_time_mach');}})()`);
    const sourceBytes=await readFile(resolve('xnu/osfmk/kern/recount.h'));
    assert(report.source_download.sha256===createHash('sha256').update(sourceBytes).digest('hex'),'Downloaded source Blob differs from original XNU header bytes');
    assert(report.source_download.mappedLinkHidden,'Unavailable handbook source link was not hidden');
    report.checks.push('selected source link or exact-byte Blob download works offline');
  }
  // Save three actual render states; keep the declaration pane scrollable on narrow screens.
  report.screenshots={};
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false},sessionId);
  for(const theme of ['light','dark']){
    await evaluate(`(()=>{if(document.documentElement.dataset.theme!==${JSON.stringify(theme)})document.getElementById('theme-toggle').click();if(document.documentElement.dataset.theme!==${JSON.stringify(theme)})throw new Error('Theme control failed');})()`);
    const image=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},sessionId);
    const path=reportPath.replace(/\.json$/,'')+'-'+theme+'.png';await writeFile(path,Buffer.from(image.data,'base64'));report.screenshots[theme]=path;
  }
  await call('Emulation.setDeviceMetricsOverride',{width:390,height:1000,deviceScaleFactor:1,mobile:false},sessionId);
  report.narrow=await evaluate(`({width:innerWidth,scroll:document.documentElement.scrollWidth,treeWidth:document.getElementById('layout-tree').clientWidth,treeScroll:document.getElementById('layout-tree').scrollWidth})`);
  assert(report.narrow.scroll<=report.narrow.width+1,'Narrow viewport has page-wide horizontal overflow: '+JSON.stringify(report.narrow));
  const narrow=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},sessionId);
  report.screenshots.narrow=reportPath.replace(/\.json$/,'')+'-narrow.png';await writeFile(report.screenshots.narrow,Buffer.from(narrow.data,'base64'));
  report.checks.push('light, dark and 390-pixel rendering captured','narrow page does not overflow horizontally');
  await sampleMemory();await Promise.all([...workerSetup]);
  report.remote_requests=requests.filter(request=>/^(?:https?|wss?|ftp):/i.test(request.url));
  assert(report.remote_requests.length===0,'Page or worker attempted remote requests');
  assert(exceptions.length===0,'Browser or worker exception: '+JSON.stringify(exceptions));
  report.status='passed';
}catch(error){
  report.status='failed';report.error=error.stack||String(error);process.exitCode=1;
}finally{
  clearInterval(sampler);report.elapsed_ms=performance.now()-started;report.browser_stderr=stderr;
  try{if(!ended)await call('Browser.close');}catch{/* Pipe can close before acknowledgement. */}
  try{process.kill(-child.pid,'SIGTERM');}catch{/* Already exited. */}
  await new Promise(resolve=>setTimeout(resolve,300));
  try{process.kill(-child.pid,'SIGKILL');}catch{/* Already exited. */}
  rejectPending(new Error('Browser explorer check finished'));
  await writeFile(reportPath,JSON.stringify(report,null,2)+'\n');await rm(profile,{recursive:true,force:true});
  console.log(JSON.stringify({status:report.status,report:reportPath,checks:report.checks?.length,peak_sampled_process_rss_bytes:report.peak_sampled_process_rss_bytes,error:report.error},null,2));
}
