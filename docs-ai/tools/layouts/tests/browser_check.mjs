// SPDX-License-Identifier: GPL-2.0-only
// Real Chromium check: fresh profile, file://, cache disabled, network offline.
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { resolve, dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { performance } from 'node:perf_hooks';
import { isDeepStrictEqual } from 'node:util';
import { createRequire } from 'node:module';

const argumentsList = process.argv.slice(2);
const smokeIndex = argumentsList.indexOf('--harness-smoke');
const harnessSmoke = smokeIndex !== -1;
if (harnessSmoke) argumentsList.splice(smokeIndex, 1);
const [pageArgument, reportArgument, nativeReportArgument, browser = 'chromium'] = argumentsList;
if (!pageArgument || !reportArgument) {
  console.error('Usage: node browser_check.mjs page.html report.json native-comparison.json [chromium]\nHarness fixture only: node browser_check.mjs page.html report.json --harness-smoke');
  process.exit(2);
}
let nativeReport;
if (!harnessSmoke) {
  if (!nativeReportArgument) throw new Error('A passing native/Wasm comparison report is required');
  nativeReport = JSON.parse(await readFile(resolve(nativeReportArgument), 'utf8'));
  if (nativeReport.wasm_parity !== 'passed' || !nativeReport.results?.length ||
      nativeReport.cases?.length !== nativeReport.results.length)
    throw new Error('Native/Wasm comparison report is incomplete or not passing');
}
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
const started = performance.now();
const report = {
  page, harness_smoke_only: harnessSmoke, fresh_profile: true, network_offline: true, cache_disabled: true,
  request_scope: 'Observed page target via CDP; not a whole-browser or child-worker traffic capture.',
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
      requests.push({ url: message.params.request.url, type: message.params.type });
    } else if (message.method === 'Network.webSocketCreated') {
      requests.push({ url: message.params.url, type: 'WebSocket' });
    } else if (message.method === 'Network.webTransportCreated') {
      requests.push({ url: message.params.url, type: 'WebTransport' });
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
  const { targetId } = await call('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await call('Target.attachToTarget', { targetId, flatten: true });
  await call('Page.enable', {}, sessionId);
  await call('Runtime.enable', {}, sessionId);
  await call('Network.enable', {}, sessionId);
  await call('Network.setCacheDisabled', { cacheDisabled: true }, sessionId);
  await call('Network.emulateNetworkConditions', {
    offline: true, latency: 0, downloadThroughput: 0, uploadThroughput: 0,
  }, sessionId);
  const navigation = await call('Page.navigate', { url: page }, sessionId);
  if (navigation.errorText) throw new Error(navigation.errorText);
  const deadline = performance.now() + 120000;
  while (performance.now() < deadline) {
    const { result, exceptionDetails } = await call('Runtime.evaluate', {
      expression: 'window.layoutProofMetrics || null', returnByValue: true,
    }, sessionId);
    if (exceptionDetails) throw new Error(JSON.stringify(exceptionDetails));
    if (result.value) { report.metrics = result.value; break; }
    await new Promise(resolve => setTimeout(resolve, 150));
  }
  await sampleMemory();
  if (!report.metrics) throw new Error('Browser proof did not complete within 120 seconds');
  if (report.metrics.parity !== 'passed') throw new Error(report.metrics.error || 'Browser parity failed');
  if (report.metrics.protocol !== 'file:') throw new Error('Proof was not opened through file://');
  if (!harnessSmoke) {
    if (report.metrics.fixture_only || report.metrics.cases !== nativeReport.results.length)
      throw new Error('Browser did not run the complete compiler fixture matrix');
    if (nativeReport.dependency_tracing) {
      // Compare all compiler evidence without copying hundreds of megabytes
      // through CDP. Each digest binds canonical bytes, not a selected summary.
      const fingerprints = await call('Runtime.evaluate', {
        expression: `(async () => { const hashes = []; for (const result of window.layoutProofResults)
          hashes.push(await LayoutContracts.sha256(LayoutContracts.canonical(result))); return hashes; })()`,
        awaitPromise: true, returnByValue: true,
      }, sessionId);
      if (fingerprints.exceptionDetails) throw new Error(JSON.stringify(fingerprints.exceptionDetails));
      const library = createRequire(import.meta.url)('../browser/contracts.js');
      const expected = [];
      for (const result of nativeReport.results) expected.push(await library.sha256(library.canonical(result)));
      if (!isDeepStrictEqual(fingerprints.result.value, expected))
        throw new Error('Browser compiler evidence differs from the independent native/Wasm report');
      report.compiler_result_sha256 = expected;
    } else {
      const { result } = await call('Runtime.evaluate', {
        expression: 'window.layoutProofResults', returnByValue: true,
      }, sessionId);
      if (!isDeepStrictEqual(result.value, nativeReport.results))
        throw new Error('Browser results differ from the independent native/Wasm comparison report');
    }
    report.native_comparison = resolve(nativeReportArgument);
    if (nativeReport.kind === 'xnu-contexts') {
      const contracts = await call('Runtime.evaluate', {
        awaitPromise: true, returnByValue: true,
        expression: `(async () => {
          if (!Array.isArray(window.layoutContractSets) || window.layoutContractSets.length !== window.layoutProofResults.length)
            throw new Error('Missing normalized browser contracts');
          const serialized = [];
          for (const document of window.layoutContractSets) {
            await LayoutContracts.validate(document);
            serialized.push(LayoutContracts.canonical(document));
          }
          const assert = (value, message) => { if (!value) throw new Error(message); };
          const documents = new Map(window.layoutCases.map((entry, i) => [entry.name, window.layoutContractSets[i]]));
          const release = documents.get('release-t8103'), development = documents.get('development-t8103');
          const declaration = (document, kind, name, owner) => document.declarations.entries.find(d =>
            d.kind === kind && d.name === name && (!owner || d.owner_id === owner));
          const recount = declaration(release, 'struct', 'recount_track').id;
          const task = declaration(release, 'struct', 'task').id;
          assert(declaration(development, 'struct', 'task').id === task, 'Task source identity changed with configuration');
          const cycles = LayoutContracts.resolvePath(release, recount, ['rt_usage', 'ru_metrics', {index: 1}, 'rm_cycles']);
          assert(cycles.root_offset_bits === 384 && cycles.local_offset_bits === 128, 'Contract recount offset differs from source expectation');
          const suspended = LayoutContracts.resolvePath(development, task, ['t_suspend_sources', {index: 3}, 'tss_procname']);
          assert(suspended.root_offset_bits === 3904 && suspended.local_offset_bits === 160, 'Contract task offset differs from source expectation');
          const stopped = declaration(release, 'field', 'user_stop_count', task).id;
          assert(declaration(development, 'field', 'user_stop_count', task).id === stopped, 'Conditional field insertion changed later field identity');
          const stats = declaration(development, 'field', 't_suspend_stats', task).id;
          const presence = LayoutContracts.mergePresence(window.layoutContractSets).find(f => f.declaration_id === stats).configurations;
          assert(presence[release.configuration.id] === 'absent' && presence[development.configuration.id] === 'present', 'Conditional field presence mismatch');
          assert(presence[documents.get('incomplete-task').configuration.id] === 'unknown', 'Incomplete analysis claimed field absence');
          const zero = documents.get('probe-defined-zero-task-suspend').configuration.requested.macros.CONFIG_TASK_SUSPEND_STATS;
          assert(zero.state === 'defined' && zero.replacement === '0', 'Defined-zero macro lost its value');
          const redefined = documents.get('probe-header-redefinition').configuration;
          assert(redefined.requested.macros.DEBUG.replacement === '1' && redefined.effective.macros.DEBUG.replacement === '0', 'Requested and effective directives collapsed');
          if (!window.layoutExpectedDependencyAnalysis) for (const document of window.layoutContractSets)
            assert(document.dependencies.status === 'not-computed' && document.dependencies.coverage === 'unknown', 'Dependency placeholder claims complete coverage');
          if (window.layoutExpectedDependencyAnalysis) {
            assert(window.layoutDependencyAnalysis, 'Missing actual dependency analysis');
            await LayoutDependencies.validate(window.layoutDependencyAnalysis, window.layoutContractSets);
            assert(LayoutContracts.canonical(window.layoutDependencyAnalysis) === LayoutContracts.canonical(window.layoutExpectedDependencyAnalysis), 'Browser/native dependency evidence mismatch');
            const recountControls = LayoutDependencies.controlsFor(window.layoutDependencyAnalysis, recount);
            const taskControls = LayoutDependencies.controlsFor(window.layoutDependencyAnalysis, task);
            for (const macro of ['CONFIG_PERVASIVE_CPI', 'CONFIG_PERVASIVE_ENERGY', 'CONFIG_SPTM']) {
              const control = recountControls.find(control => control.macro === macro);
              assert(control && control.paths.length, 'Missing recount dependency path: ' + macro);
              assert(control.classification === 'demonstrated' && control.observed_changes.length, 'Missing controlled recount change: ' + macro);
              assert(!taskControls.some(control => control.macro === macro), 'Pointee dependency leaked into task: ' + macro);
            }
            const suspendControl = taskControls.find(control => control.macro === 'CONFIG_TASK_SUSPEND_STATS');
            assert(suspendControl?.paths.length && suspendControl.classification === 'demonstrated', 'Missing demonstrated conditional task field control');
            const comparisonFor = (left, right) => window.layoutDependencyAnalysis.comparisons.find(comparison =>
              [comparison.from, comparison.to].includes(documents.get(left).configuration.id) &&
              [comparison.from, comparison.to].includes(documents.get(right).configuration.id));
            const definedValues = comparisonFor('probe-defined-zero-task-suspend', 'probe-defined-one-task-suspend');
            assert(definedValues?.attribution === 'single-macro-intervention' && suspendControl.observed_no_change.includes(definedValues.id), 'Defined-zero/one equivalence lost for ifdef field');
            const debug = taskControls.find(control => control.macro === 'DEBUG');
            const redefinition = comparisonFor('release-t8103', 'probe-header-redefinition');
            assert(debug?.observed_no_change.includes(redefinition?.id), 'Header-redefined DEBUG falsely claimed a layout change');
            const profiles = comparisonFor('release-t8103', 'development-t8103');
            assert(profiles?.attribution === 'joint-context-difference', 'Profile comparison attributed to one flag');
          }
          return {serialized, analysis: window.layoutDependencyAnalysis ? LayoutContracts.canonical(window.layoutDependencyAnalysis) : null,
            checks: ['configuration-independent declaration IDs', 'nested root/local offsets',
            'field IDs survive conditional insertion', 'present/absent/unknown coverage', 'defined-zero macros',
            'requested/effective macro distinction', ...(window.layoutDependencyAnalysis ?
              ['actual dependency evidence parity', 'source-backed demonstrated controls', 'pointer dependency boundaries',
               'defined-zero/one no-change evidence', 'header redefinition no-change evidence', 'confounded profile comparison'] : ['explicit uncomputed dependencies'])]};
        })()`
      }, sessionId);
      if (contracts.exceptionDetails) throw new Error(JSON.stringify(contracts.exceptionDetails));
      const contractLibrary = createRequire(import.meta.url)('../browser/contracts.js');
      const dependencyAnalysis = contracts.result.value.analysis ? JSON.parse(contracts.result.value.analysis) : null;
      if (dependencyAnalysis) {
        const dependencyLibrary = createRequire(import.meta.url)('../browser/dependencies.js');
        await contractLibrary.registerDependencyAnalysis(dependencyAnalysis);
        await dependencyLibrary.validate(dependencyAnalysis, contracts.result.value.serialized.map(value => JSON.parse(value)));
      }
      for (const serialized of contracts.result.value.serialized) {
        const document = JSON.parse(serialized);
        await contractLibrary.validate(document);
        if (contractLibrary.canonical(document) !== serialized)
          throw new Error('Browser/Node contract serialization mismatch');
      }
      report.contract_checks = { documents: contracts.result.value.serialized.length,
        browser_validation: 'passed', node_validation: 'passed', canonical_parity: 'passed',
        semantics: contracts.result.value.checks };
      const checked = await call('Runtime.evaluate', {
        awaitPromise: true, returnByValue: true,
        expression: `(async () => {
          const el = id => document.getElementById(id);
          const assert = (value, message) => { if (!value) throw new Error(message); };
          const change = (id, value) => { el(id).value = value; el(id).dispatchEvent(new Event('change')); };
          const field = path => [...el('layout-tree').querySelectorAll('.field-node')].find(n => n.dataset.fieldPath === path);
          const index = (path, value) => { const input = field(path).querySelector('input'); input.value = String(value); input.dispatchEvent(new Event('input')); };
          const offsets = (path, root, local) => {const n = field(path); assert(n && Number(n.dataset.rootBits) === root && Number(n.dataset.localBits) === local, 'Wrong offsets: ' + path); assert(n.querySelector('.field-offset')?.textContent === '(+0x' + (root / 8).toString(16) + ')', 'Wrong displayed hex offset: ' + path);};
          const apply = async text => {
            el('layout-directives').value = text; el('layout-directives').dispatchEvent(new Event('input'));
            assert(el('layout-tree').children.length === 0 && el('layout-meta').hidden, 'Editing retained a stale layout');
            el('layout-apply').click();
            const deadline = performance.now() + 15000;
            while (!window.layoutCustomResult && performance.now() < deadline) await new Promise(r => setTimeout(r, 20));
            assert(window.layoutCustomResult, 'Manual analysis timed out');
            return window.layoutCustomResult;
          };
          assert(el('layout-profile').options.length === 4 && !el('layout-apply').disabled, 'Explorer not ready');
          change('layout-profile', 'release-t8103'); change('layout-record', 'recount_track');
          index('recount_track.rt_usage.ru_metrics', 1);
          offsets('recount_track.rt_usage.ru_metrics[1].rm_cycles', 384, 128);
          change('layout-profile', 'release-vmapple');
          index('recount_track.rt_usage.ru_metrics', 1);
          offsets('recount_track.rt_usage.ru_metrics[1].rm_time_mach', 128, 0);
          change('layout-profile', 'development-t8103'); change('layout-record', 'task');
          index('task.t_suspend_sources', 3);
          offsets('task.t_suspend_sources[3].tss_procname', 3904, 160);
          el('layout-search').value = 'tss_procname'; el('layout-search').dispatchEvent(new Event('input'));
          assert(!field('task.t_suspend_sources[3].tss_procname').hidden && field('task.ref_count').hidden, 'Field search failed');
          index('task.t_suspend_sources', -1);
          assert(!field('task.t_suspend_sources[-1]'), 'Negative array index accepted');
          el('layout-search').value = ''; el('layout-search').dispatchEvent(new Event('input'));
          change('layout-profile', 'release-t8103');
          const definedZero = await apply('#define CONFIG_TASK_SUSPEND_STATS 0');
          assert(definedZero.result?.status === 'ok' && el('layout-meta').textContent.includes('0x7e0'), 'Defined-zero configuration failed');
          assert(definedZero.contract?.configuration.classification === 'what-if', 'Manual result is not labeled what-if');
          const redefined = await apply('#define DEBUG 1');
          assert(redefined.result?.effective_macros.DEBUG.replacement === '0', 'Header redefinition missing');
          assert(el('layout-config').textContent.includes('#define DEBUG 1') && el('layout-config').textContent.includes('/inputs/generated/debug.h'), 'Requested/effective provenance missing');
          const undefinedCpi = await apply('#undef CONFIG_PERVASIVE_CPI');
          assert(undefinedCpi.result?.effective_macros.CONFIG_PERVASIVE_CPI === null, 'Undef override failed');
          assert(undefinedCpi.result.records.find(r => r.name === 'recount_track').size_bytes === 32, 'Undef CPI size failed');
          const reserved = await apply('#define __ARM_FEATURE_CRC32 0');
          const baselineIndex = window.layoutCases.findIndex(entry => entry.name === 'release-t8103');
          assert(reserved.result?.status === 'ok' && reserved.result.effective_macros.__ARM_FEATURE_CRC32.replacement === '0', 'Explicit reserved-macro what-if failed');
          assert(reserved.contract?.configuration.classification === 'what-if' &&
            reserved.contract.configuration.policy.id === window.layoutContractSets[baselineIndex].configuration.policy.id,
            'What-if lost baseline policy or classification');
          assert(JSON.stringify(reserved.result.driver_target) === JSON.stringify(window.layoutProofResults[baselineIndex].driver_target), 'Macro override changed recorded compiler target features');
          const failed = await apply('#define uint64_t +');
          assert(failed.result?.status !== 'ok' && failed.result?.records.length === 0 && el('layout-tree').children.length === 0 && el('layout-meta').hidden, 'Compiler error retained layout');
          const invalid = await apply('#include <unsupported.h>');
          assert(invalid.error && el('layout-tree').children.length === 0, 'Unsupported editor directive accepted');
          el('layout-reset').click();
          assert(!el('layout-meta').hidden && el('layout-directives').value === '' && el('layout-meta').textContent.includes('0x660'), 'Reset failed');
          change('layout-record', 'recount_track'); index('recount_track.rt_usage.ru_metrics', 1);
          el('layout-search').value = 'rm_cycles'; el('layout-search').dispatchEvent(new Event('input'));
          el('layout-search').value = ''; el('layout-search').dispatchEvent(new Event('input'));
          for (const detail of el('layout-tree').querySelectorAll('details.field-node')) detail.open = true;
          if (window.layoutDependencyAnalysis) {
            const evidence = [...el('layout-tree').querySelectorAll('details')].find(detail => detail.firstElementChild?.textContent.startsWith('Configuration dependencies'));
            assert(evidence && evidence.textContent.includes('CONFIG_SPTM') && evidence.textContent.includes('demonstrated') && evidence.textContent.includes('unknown'), 'Dependency evidence not exposed in explorer');
          }
          const transfer = async result => window.layoutDependencyAnalysis ? await LayoutContracts.sha256(LayoutContracts.canonical(result)) : result;
          return {defined_zero: await transfer(definedZero.result), redefined: await transfer(redefined.result), checks: ['nested offsets', 'array stride', 'array bounds', 'field search', 'define zero', 'header redefinition', 'undef', 'explicit reserved-macro what-if preserves compiler features', 'compiler failure clears layout', 'invalid directive', 'reset', ...(window.layoutDependencyAnalysis ? ['dependency controls and coverage visible'] : [])]};
        })()`
      }, sessionId, 60000);
      if (checked.exceptionDetails) throw new Error(JSON.stringify(checked.exceptionDetails));
      for (const [key, name] of [['defined_zero', 'probe-defined-zero-task-suspend'], ['redefined', 'probe-header-redefinition']]) {
        const native = nativeReport.results[nativeReport.cases.indexOf(name)];
        const expected = nativeReport.dependency_tracing ? await contractLibrary.sha256(contractLibrary.canonical(native)) : native;
        if (!isDeepStrictEqual(checked.result.value[key], expected))
          throw new Error('Interactive configuration differs from native comparison: ' + name);
      }
      report.explorer_checks = checked.result.value.checks;
      await call('Emulation.setDeviceMetricsOverride', {width: 1280, height: 1100, deviceScaleFactor: 1, mobile: false}, sessionId);
      const screenshot = await call('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false}, sessionId);
      report.preview_screenshot = reportPath.replace(/\.json$/, '') + '-preview.png';
      await writeFile(report.preview_screenshot, Buffer.from(screenshot.data, 'base64'));
      if (nativeReport.dependency_tracing) {
        await call('Runtime.evaluate', {expression: `(() => {
          const detail = [...document.querySelectorAll('#layout-tree details')].find(detail => detail.firstElementChild?.textContent.startsWith('Configuration dependencies'));
          detail.open = true; detail.scrollIntoView({block: 'start'});
        })()`}, sessionId);
        const evidenceScreenshot = await call('Page.captureScreenshot', {format: 'png', captureBeyondViewport: false}, sessionId);
        report.dependency_screenshot = reportPath.replace(/\.json$/, '') + '-dependencies.png';
        await writeFile(report.dependency_screenshot, Buffer.from(evidenceScreenshot.data, 'base64'));
      }
    }
  }
  if (requests.some(request => /^https?:|^wss?:/i.test(request.url))) throw new Error('Proof attempted a network request');
  if (exceptions.length) throw new Error('Browser reported an uncaught exception');
  report.status = 'passed';
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
