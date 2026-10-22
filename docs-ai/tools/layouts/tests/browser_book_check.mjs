// SPDX-License-Identifier: GPL-2.0-only
// Integrated book acceptance: fresh profile, offline file/ZIP or isolated local HTTPS.
import { spawn } from 'node:child_process';
import { createReadStream } from 'node:fs';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { resolve, dirname, join, relative, isAbsolute } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { createRequire } from 'node:module';
import { createHash, X509Certificate } from 'node:crypto';
import { createServer } from 'node:https';

const args = process.argv.slice(2);
const extracted = args.includes('--extracted');
const forceFallback = args.includes('--fallback');
const httpsProjectPath=args.includes('--https-project-path');
const positional = args.filter(value => !['--extracted', '--fallback','--https-project-path'].includes(value));
const [bookArgument, reportArgument, nativeReportArgument, browser = 'chromium'] = positional;
if (!bookArgument || !reportArgument || !nativeReportArgument) throw new Error('Usage: browser_book_check.mjs book-root report.json native-comparison.json [chromium] [--extracted] [--fallback] [--https-project-path]');
const nativeReport = JSON.parse(await readFile(resolve(nativeReportArgument), 'utf8'));
if (nativeReport.wasm_parity !== 'passed' || !nativeReport.dependency_tracing || !Array.isArray(nativeReport.results) || nativeReport.results.length!==nativeReport.cases?.length) throw new Error('Passing traced native/Wasm evidence required');
// Page transport deliberately excludes the enormous raw dependency traces.
// Keep native compiler layouts for full digest parity and independent arithmetic.
for(const result of nativeReport.results)delete result.dependency_trace;
const Contracts = createRequire(import.meta.url)('../browser/contracts.js');
const bookRoot=resolve(bookArgument);let bookURL=pathToFileURL(bookRoot+'/').href;
const reportPath = resolve(reportArgument);
// Validate proof inputs before creating a browser process or temporary profile.
async function fileHash(path){const hash=createHash('sha256');for await(const bytes of createReadStream(path))hash.update(bytes);return hash.digest('hex');}
const [harnessHash,manifestHash,layoutHash,evidenceHash]=await Promise.all([
  fileHash(new URL(import.meta.url)),
  fileHash(join(bookRoot,'build-manifest.json')),
  fileHash(join(bookRoot,'layouts/manifest.json')),
  fileHash(resolve(nativeReportArgument)),
]);
const inputHashes={harness_sha256:harnessHash,build_manifest_sha256:manifestHash,layout_manifest_sha256:layoutHash,native_comparison_sha256:evidenceHash};
const [sourceRecords,catalog]=await Promise.all(['source-records.json','layouts/catalog.json'].map(async name=>JSON.parse(await readFile(join(bookRoot,name),'utf8'))));
if(catalog.contract!=='platydoc.layout-catalog'||catalog.version!==1)throw Error('Expected integrated source-bound layout catalog');
const profile = await mkdtemp(join(dirname(reportPath), 'chromium-profile-'));
let server=null,certificateTrust=null;
const serverRequests=[];
try{if(httpsProjectPath){
  const keyPath=join(profile,'local-key.pem'),certPath=join(profile,'local-cert.pem');
  await new Promise((resolve,reject)=>{let error='',expired=false;const command=spawn('openssl',['req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=127.0.0.1','-addext','subjectAltName=IP:127.0.0.1','-keyout',keyPath,'-out',certPath],{stdio:['ignore','ignore','pipe']});const timer=setTimeout(()=>{expired=true;command.kill('SIGKILL');},15000);command.stderr.on('data',data=>{error=(error+data).slice(-4000);});command.on('error',failure=>{clearTimeout(timer);reject(failure);});command.on('exit',code=>{clearTimeout(timer);code===0?resolve():reject(Error(expired?'Local certificate generation exceeded 15 seconds':'Local certificate generation failed: '+error));});});
  const [key,cert]=await Promise.all([readFile(keyPath),readFile(certPath)]);
  certificateTrust=createHash('sha256').update(new X509Certificate(cert).publicKey.export({format:'der',type:'spki'})).digest('base64');
  const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.txt':'text/plain; charset=utf-8','.wasm':'application/wasm','.zip':'application/zip'};
  server=createServer({key,cert},async(request,response)=>{
    let path;
    try{
      const parsed=new URL(request.url,'https://127.0.0.1');
      if(!['GET','HEAD'].includes(request.method)||!parsed.pathname.startsWith('/xnu-handbook/'))throw Error('Outside local test prefix');
      const leaf=decodeURIComponent(parsed.pathname.slice('/xnu-handbook/'.length))||'index.html';path=resolve(bookRoot,leaf);
      const within=relative(bookRoot,path);if(isAbsolute(within)||within==='..'||within.startsWith('../'))throw Error('Outside test book');
      const bytes=await readFile(path),extension=path.slice(path.lastIndexOf('.'));
      response.writeHead(200,{'Content-Type':types[extension]||'application/octet-stream','Cache-Control':'no-store'});response.end(request.method==='HEAD'?undefined:bytes);serverRequests.push({url:request.url,status:200});
    }catch(error){response.writeHead(404,{'Content-Type':'text/plain'});response.end('Local test file unavailable');serverRequests.push({url:request.url,status:404,error:error.message});}
  });
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  bookURL='https://127.0.0.1:'+server.address().port+'/xnu-handbook/';
}}catch(error){if(server){server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}await rm(profile,{recursive:true,force:true});throw error;}
const allowedRequest=url=>{try{const parsed=new URL(url);if(['about:','blob:','data:'].includes(parsed.protocol))return true;const root=new URL(bookURL);return httpsProjectPath&&parsed.origin===root.origin&&parsed.pathname.startsWith(root.pathname);}catch{return false;}};
const child = spawn(browser, [
  '--headless=new', '--no-first-run', '--no-default-browser-check',
  '--disable-background-networking', '--disable-component-update',
  '--disable-sync', '--disable-default-apps', '--disable-extensions',
  '--disable-breakpad', '--metrics-recording-only', '--password-store=basic',
  httpsProjectPath?'--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1':'--host-resolver-rules=MAP * ~NOTFOUND', '--remote-debugging-pipe',
  ...(httpsProjectPath?['--no-proxy-server']:[]),
  ...(certificateTrust?['--ignore-certificate-errors-spki-list='+certificateTrust]:[]),
  `--user-data-dir=${profile}`, 'about:blank',
], { stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe'], detached: true });
let stderr = '', sequence = 0, wire = Buffer.alloc(0), ended = false;
const pending = new Map(), requests = [], exceptions = [],loadingFailures=[];
const workerSetup = new Set();
const started = performance.now();
const report = {
  ...inputHashes, native_comparison: resolve(nativeReportArgument),
  book_root:bookRoot,book_url:bookURL,extracted_zip:extracted,https_project_path:httpsProjectPath,https_certificate_spki_sha256_base64:certificateTrust,local_https_origin:httpsProjectPath?new URL(bookURL).origin:null,server_requests:serverRequests, fresh_profile: true, network_offline: !httpsProjectPath,page_external_requests_denied:true, cache_disabled: true,
  request_scope: 'Page and dedicated workers attached before worker execution; browser background targets excluded.',
  request_denial:httpsProjectPath?'Page Fetch permits only the exact local HTTPS origin/project prefix; browser DNS denied except 127.0.0.1, proxies disabled. Worker interception support is reported separately; worker requests remain observed.':'Page offline emulation and browser-wide DNS denial; worker requests observed.',
  worker_targets: [], persistence_disabled: true, force_fallback: forceFallback,
  browser_version: null, requests, exceptions,loading_failures:loadingFailures, peak_sampled_process_rss_bytes: 0,
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
      requests.push({ url: message.params.request.url, type: message.params.type, session: message.sessionId,request_id:message.params.requestId });
    } else if(message.method==='Fetch.requestPaused'){
      const allowed=allowedRequest(message.params.request.url);
      call(allowed?'Fetch.continueRequest':'Fetch.failRequest',{requestId:message.params.requestId,...(allowed?{}:{errorReason:'BlockedByClient'})},message.sessionId).catch(error=>exceptions.push({interception:error.message}));
    } else if(message.method==='Network.loadingFailed'){
      if(!message.params.canceled)loadingFailures.push({url:requests.findLast(r=>r.request_id===message.params.requestId&&r.session===message.sessionId)?.url,...message.params});
    } else if (message.method === 'Network.webSocketCreated') {
      requests.push({ url: message.params.url, type: 'WebSocket' });
    } else if (message.method === 'Network.webTransportCreated') {
      requests.push({ url: message.params.url, type: 'WebTransport' });
    } else if (message.method === 'Target.attachedToTarget') {
      const {sessionId: workerSession, targetInfo} = message.params;
      if (targetInfo.type !== 'worker') continue;
      report.worker_targets.push({id: targetInfo.targetId, url: targetInfo.url, session: workerSession});
      const setup = (async () => {
        try{
          await call('Runtime.enable', {}, workerSession);
          await call('Runtime.evaluate', {expression: `Object.defineProperty(globalThis,'indexedDB',{configurable:true,get(){throw new Error('Worker storage disabled by offline runtime test');}})`}, workerSession);
          await call('Network.enable', {}, workerSession);
          await call('Network.setCacheDisabled', {cacheDisabled: true}, workerSession);
          if(httpsProjectPath){
            try{await call('Fetch.enable',{patterns:[{urlPattern:'*'}]},workerSession);report.worker_fetch_interception='enabled';}
            catch(failure){if(!failure.message.includes('Fetch.enable')||!/-32601|not supported/i.test(failure.message))throw failure;report.worker_fetch_interception='unsupported by this Chromium worker; page Fetch, browser DNS denial and worker request observation remain active';}
          }
          // Workers expose request observation even where their emulation or
          // interception domains are unavailable. External attempts fail acceptance.
          try {await call('Network.emulateNetworkConditions', {offline: !httpsProjectPath, latency: 0, downloadThroughput: httpsProjectPath?-1:0, uploadThroughput: httpsProjectPath?-1:0}, workerSession);}
          catch (failure) {if (!failure.message.includes('Not supported')) throw failure; report.worker_network_emulation = 'unsupported; request observation, selected page conditions and browser-wide host denial active';}
        }finally{await call('Runtime.runIfWaitingForDebugger', {}, workerSession);}
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
const assert=(condition,message)=>{if(!condition)throw new Error(message);};
const expectedHashes=new Map();
async function assertNative(snapshot,name){
  const result=nativeReport.results[nativeReport.cases.indexOf(name)];assert(result,'Missing native case: '+name);
  if(!expectedHashes.has(name))expectedHashes.set(name,await Contracts.sha256(Contracts.canonical(result)));
  assert(snapshot.sha===expectedHashes.get(name),'Complete native compiler result differs: '+name);
}
function localFile(url){
  const parsed=new URL(url),root=new URL(bookURL);let path;
  if(httpsProjectPath){assert(parsed.origin===root.origin&&parsed.pathname.startsWith(root.pathname),'URL escapes local HTTPS project path: '+url);path=resolve(bookRoot,decodeURIComponent(parsed.pathname.slice(root.pathname.length)));}
  else{assert(parsed.protocol==='file:','Expected local file: '+url);path=fileURLToPath(parsed);}
  const within=relative(bookRoot,path);
  assert(!isAbsolute(within)&&within!=='..'&&!within.startsWith('../'),'File escapes this book: '+url);
  return path;
}
try{
  report.browser_version=await call('Browser.getVersion');
  await call('Browser.setDownloadBehavior',{behavior:'allow',downloadPath:profile});
  const {targetId}=await call('Target.createTarget',{url:'about:blank'});
  const {sessionId}=await call('Target.attachToTarget',{targetId,flatten:true});
  for(const domain of ['Page','Runtime','Network'])await call(domain+'.enable',{},sessionId);
  await call('Target.setAutoAttach',{autoAttach:true,waitForDebuggerOnStart:true,flatten:true},sessionId);
  await call('Network.setCacheDisabled',{cacheDisabled:true},sessionId);
  await call('Network.emulateNetworkConditions',{offline:!httpsProjectPath,latency:0,downloadThroughput:httpsProjectPath?-1:0,uploadThroughput:httpsProjectPath?-1:0},sessionId);
  if(httpsProjectPath)await call('Fetch.enable',{patterns:[{urlPattern:'*'}]},sessionId);
  await call('Page.addScriptToEvaluateOnNewDocument',{source:`
    for(const name of ['localStorage','sessionStorage','indexedDB'])Object.defineProperty(window,name,{configurable:true,get(){throw Error('Storage disabled by offline book integration test');}});
    ${forceFallback?"Object.defineProperty(window,'DecompressionStream',{value:undefined});window.layoutRuntimeOptions={force_fallback:true};":''}
    window.integrationHeartbeat={ticks:0,longest_ms:0};let previous=performance.now();
    setInterval(()=>{const now=performance.now();window.integrationHeartbeat.longest_ms=Math.max(window.integrationHeartbeat.longest_ms,now-previous);previous=now;++window.integrationHeartbeat.ticks;},20);
  `},sessionId);
  const evaluate=async(expression,timeout=60000)=>{
    const response=await call('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},sessionId,timeout);
    if(response.exceptionDetails)throw Error(JSON.stringify(response.exceptionDetails));return response.result.value;
  };
  const waitFor=async(expression,label,timeout=90000)=>{
    const deadline=performance.now()+timeout;
    while(performance.now()<deadline){
      if(exceptions.some(e=>e.worker_setup))throw Error(label+' worker setup failed: '+JSON.stringify(exceptions));
      let value;try{value=await evaluate(expression);}catch(error){if(!/Execution context was destroyed|Cannot find context|Inspected target navigated/i.test(error.message))throw error;}
      if(value)return value;await new Promise(resolve=>setTimeout(resolve,80));
    }
    throw Error(label+' deadline: '+JSON.stringify(await evaluate(`({url:location.href,status:document.getElementById('explorer-status')?.textContent,error:document.getElementById('explorer-error')?.textContent,source:document.getElementById('source-meta')?.textContent})`)));
  };
  const waitDocument=async(href,marker)=>waitFor(`${new URL(href).hash?'location.href':'location.href.split("#")[0]'}===${JSON.stringify(href)}&&window.__oldIntegrationDocument!==${JSON.stringify(marker)}&&document.readyState==='complete'`,'Local navigation');
  let navigationSequence=0;
  const navigate=async(relativePath)=>{
    const href=new URL(relativePath,bookURL).href,marker=++navigationSequence;
    await evaluate(`window.__oldIntegrationDocument=${marker}`);
    const result=await call('Page.navigate',{url:href},sessionId);if(result.errorText)throw Error(result.errorText);
    await waitDocument(href,marker);return href;
  };
  const clickLink=async(expression)=>{
    const marker=++navigationSequence;
    const href=await evaluate(`(()=>{const link=${expression};if(!link)throw Error('Missing reading link');window.__oldIntegrationDocument=${marker};const href=link.href;link.click();return href;})()`);
    localFile(href);await waitDocument(href,marker);return href;
  };
  const click=async id=>evaluate(`(()=>{const e=document.getElementById(${JSON.stringify(id)});if(!e)throw Error('Missing UI control '+${JSON.stringify(id)});e.click();})()`);
  const readerReady=async()=>{
    await waitFor(`document.querySelectorAll('#chapter-nav .nav-part a').length>20`,'Shared chapter navigation');
    const state=await evaluate(`({url:location.href,root:new URL(document.body.dataset.root,document.baseURI).href,navLinks:document.querySelectorAll('#chapter-nav .nav-part a').length,active:document.querySelector('#chapter-nav [aria-current="page"]')?.href,search:!!document.getElementById('search-dialog'),source:!!document.getElementById('source-dialog'),footer:document.querySelector('.book-footer')?.textContent,offline:{href:document.querySelector('.offline-download')?.href,download:document.querySelector('.offline-download')?.getAttribute('download')}})`);
    assert(state.root===bookURL,'Reader resolved the wrong book root: '+JSON.stringify(state));
    assert(state.search&&state.source&&state.footer.includes('CC BY 4.0'),'Reader shell lost dialogs or license footer');
    assert(state.offline.href===new URL(extracted?'download.html':'xnu-source-handbook.zip',bookURL).href,'Offline header destination incorrect');
    assert(extracted?!state.offline.download:state.offline.download==='xnu-source-handbook.zip','Offline header download state incorrect');
    return state;
  };
  const search=async query=>{
    await click('search-open');
    await evaluate(`(()=>{const input=document.getElementById('search-input');input.value=${JSON.stringify(query)};input.dispatchEvent(new Event('input',{bubbles:true}));})()`);
    await waitFor(`document.getElementById('search-dialog').open&&document.querySelectorAll('#search-results .search-result-link').length>0`,'Local handbook search');
    const result=await evaluate(`({status:document.getElementById('search-status').textContent,links:[...document.querySelectorAll('#search-results .search-result-link')].slice(0,5).map(a=>({href:a.href,text:a.textContent}))})`);
    for(const link of result.links)localFile(link.href);
    await evaluate(`document.querySelector('[data-close-search]').click()`);return result;
  };
  const waitUI=async expectedRoot=>waitFor(`(async()=>{
    const c=window.layoutExplorerCurrent;if(!c||c.result?.status!=='ok'||window.layoutRuntimeClient?.active||c.root_name!==${JSON.stringify(expectedRoot)})return null;
    await LayoutContracts.validate(c.contract,{analysis:c.analysis});const sha=await LayoutContracts.sha256(LayoutContracts.canonical(c.result));
    if(window.layoutExplorerCurrent!==c||window.layoutRuntimeClient.active)return null;
    return{profile:c.profile,root:c.root_name,root_id:c.root_id,sha,selected:c.selected?{path:c.selected.path,root_bits:c.selected.rootBits,local_bits:c.selected.localBits}:null,workers:{...window.layoutRuntimeClient.metrics},compiler_metrics:c.metrics,heartbeat:window.integrationHeartbeat,integrated:window.layoutExplorerConfig?.integrated,asset_root:window.layoutExplorerConfig?.assetRoot};
  })()`,'Integrated live explorer');
  const fullSource=async expectedURL=>{
    await waitFor(`document.querySelector('pre[data-source-full]')&&!document.querySelector('pre[data-source-full]').hasAttribute('aria-busy')&&document.querySelectorAll('pre[data-source-full] .source-line').length>0`,'Complete local source rendering');
    const recordURL=new URL(expectedURL).pathname.slice(new URL(bookURL).pathname.length);
    const record=sourceRecords[decodeURIComponent(recordURL)];assert(record,'Unknown source wrapper: '+recordURL);
    const result=await evaluate(`({url:location.href,path:document.body.dataset.sourcePath,count:document.querySelectorAll('pre[data-source-full] .source-line').length,last:document.querySelector('pre[data-source-full] .source-line:last-child')?.id,highlighted:document.querySelectorAll('pre[data-source-full] .source-line.is-highlighted').length,controls:[...document.querySelectorAll('.source-file-controls button')].map(b=>({label:b.textContent,disabled:b.disabled}))})`);
    assert(result.path===record.path&&result.count===record.line_count&&result.last==='L'+record.line_count,'Full file did not materialize every source line');
    assert(result.highlighted>0,'Full source lost the cited range');
    assert(result.controls.some(b=>b.label==='Copy full source'&&!b.disabled)&&result.controls.some(b=>b.label==='Print full source'&&!b.disabled),'Full source lost enabled copy/print controls');return{...result,expected_sha256:record.sha256};
  };
  report.checks=[];
  await navigate('structures/task-and-shared-ro.html');
  report.reader=await readerReady();
  assert(report.reader.active===new URL('structures/task-and-shared-ro.html',bookURL).href,'Nested chapter navigation lost its active entry');
  report.chapter_copy=await evaluate(`({buttons:document.querySelectorAll('#content .copy-code').length,associated:[...document.querySelectorAll('#content .copy-code')].some(button=>!!button.closest('.code-block')?.querySelector('pre code'))})`);
  assert(report.chapter_copy.buttons>0&&report.chapter_copy.associated,'Ordinary chapter code lost its copy controls');
  report.search=await search('recount_track');
  report.checks.push('nested authored chapter uses shared navigation, dialogs and license footer','local handbook search resolves nested results','ordinary chapter code retains associated copy controls','built or extracted offline header controls are correct');

  report.diagram=await evaluate(`(()=>{const a=document.querySelector('figure.diagram a.diagram-link');if(!a)throw Error('Task chapter lacks a diagram');const href=a.href;a.click();return{href};})()`);
  await waitFor(`document.getElementById('diagram-dialog').open&&document.getElementById('diagram-image').complete&&document.getElementById('diagram-image').naturalWidth>0`,'Local diagram enlargement');
  localFile(report.diagram.href);
  await click('diagram-image');
  assert(await evaluate(`document.getElementById('diagram-image').getAttribute('aria-pressed')==='true'`),'Diagram enlargement lost native-size zoom');
  await evaluate(`document.querySelector('[data-close-diagram]').click()`);
  await clickLink(`[...document.querySelectorAll('.header-links a')].find(a=>new URL(a.href).pathname.endsWith('/concept-index.html'))`);
  await readerReady();
  await waitFor(`document.getElementById('index-filter')?.dataset.ready&&document.querySelectorAll('.index-entry').length>0`,'Complete local concept index');
  report.index=await evaluate(`(()=>{const total=document.querySelectorAll('.index-entry').length,input=document.getElementById('index-filter');input.value='task';input.dispatchEvent(new Event('input',{bubbles:true}));return{total,visible:document.querySelectorAll('.index-entry:not([hidden])').length,links:[...document.querySelectorAll('.index-entry:not([hidden]) a')].slice(0,5).map(a=>a.href)};})()`);
  assert(report.index.visible>0&&report.index.visible<report.index.total,'Concept filter did not narrow the complete index');for(const href of report.index.links)localFile(href);
  await clickLink(`(()=>{const a=[...document.querySelectorAll('#chapter-nav a[href]')].find(a=>new URL(a.href).pathname===new URL('structures/task-and-shared-ro.html',${JSON.stringify(bookURL)}).pathname);if(a)for(let n=a.parentElement;n;n=n.parentElement)if(n.tagName==='DETAILS')n.open=true;return a;})()`);
  await readerReady();
  report.checks.push('local SVG enlargement and native-size zoom remain functional','complete local concept index loads and filters meaningful entries');

  // Exercise the existing reader before entering the explorer.
  report.citation=await evaluate(`(()=>{const link=[...document.querySelectorAll('a.source-link[data-source]')].find(a=>a.dataset.source==='xnu/osfmk/kern/task.h');if(!link)throw Error('Missing authored task source citation');const result={source:link.dataset.source,href:link.href,start:Number(link.dataset.start),end:Number(link.dataset.end),payload:link.dataset.sourcePayload};link.click();return result;})()`);
  await waitFor(`document.getElementById('source-dialog').open&&!document.getElementById('source-code').hasAttribute('aria-busy')&&document.querySelectorAll('#source-code .is-highlighted').length>0`,'Source citation popup');
  report.popup=await evaluate(`({title:document.getElementById('source-title').textContent,highlighted:document.querySelectorAll('#source-code .is-highlighted').length,full:document.getElementById('source-full-link').href,meta:document.getElementById('source-meta').textContent})`);
  assert(report.popup.title===report.citation.source,'Popup source identity differs from citation');
  const popupFirst=Math.max(1,report.citation.start-8),popupLast=Math.min(report.citation.end+8,popupFirst+99);
  assert(report.popup.highlighted===Math.max(0,Math.min(report.citation.end,popupLast)-report.citation.start+1),'Popup did not highlight cited lines');
  await clickLink(`document.getElementById('source-full-link')`);
  report.full_source=await fullSource(report.popup.full);
  await evaluate(`(()=>{window.__rawSourceBlob=null;window.__rawSourceCreate=URL.createObjectURL;URL.createObjectURL=function(blob){window.__rawSourceBlob=blob;return window.__rawSourceCreate.call(this,blob);};document.querySelector('.source-download').click();})()`);
  await waitFor(`!!window.__rawSourceBlob`,'Raw source Blob download');
  report.source_download=await evaluate(`(async()=>{try{const bytes=new Uint8Array(await window.__rawSourceBlob.arrayBuffer());const digest=new Uint8Array(await crypto.subtle.digest('SHA-256',bytes));return{bytes:bytes.length,sha256:[...digest].map(b=>b.toString(16).padStart(2,'0')).join('')};}finally{URL.createObjectURL=window.__rawSourceCreate;delete window.__rawSourceBlob;delete window.__rawSourceCreate;}})()`);
  assert(report.source_download.sha256===report.full_source.expected_sha256,'Reader raw source download changed bytes');
  report.checks.push('source citation popup preserves source identity and highlighted range','full-file reader materializes every line and preserves range','reader raw source download preserves exact bytes');

  await clickLink(`(()=>{const link=[...document.querySelectorAll('.source-backlinks a[href]')].find(a=>new URL(a.href).pathname===new URL('structures/task-and-shared-ro.html',${JSON.stringify(bookURL)}).pathname);if(link)for(let node=link.parentElement;node;node=node.parentElement)if(node.tagName==='DETAILS')node.open=true;return link;})()`);
  await readerReady();
  report.task_link=await clickLink(`document.querySelector('a[href*="layout-browser.html?declaration=task"]')`);
  report.task=await waitUI('task');await assertNative(report.task,'release-t8103');
  assert(report.task.integrated===true&&report.task.asset_root==='../layouts/','Explorer did not receive integrated asset configuration');
  assert(report.task.root_id===catalog.selections.find(s=>s.key==='task')?.declarations[report.task.profile],'Task link did not resolve pinned source declaration identity');
  assert(report.task.workers.worker_starts>0&&report.worker_targets.length>0,'Initial authoritative layout did not execute in a worker');
  assert(await evaluate(`typeof window.createLayoutEngine==='undefined'`),'Compiler was exposed on reader thread');
  report.task_shell=await readerReady();
  report.explorer_code_scope=await evaluate(`({copy:document.querySelectorAll('#structure-layout-explorer .copy-code').length,wrappers:document.querySelectorAll('#structure-layout-explorer .code-block').length})`);
  assert(report.explorer_code_scope.copy===0&&report.explorer_code_scope.wrappers===0,'Generic code enhancement wrapped live explorer controls');
  await evaluate(`window.layoutExplorer.selectField('task.ref_count')`);
  assert(await evaluate(`window.layoutExplorerCurrent.selected.rootBits===128&&window.layoutExplorerCurrent.selected.localBits===128`),'Task deep link did not select native task geometry');
  report.checks.push('source-page referring-chapter backlink returns to authored text','authored task inspect link resolves the explicit declaration','integrated task result matches complete native evidence','compiler remains isolated in dedicated worker','generic code copy enhancement leaves live explorer controls intact');

  // A complete but unmapped AST name must not become an authored entry point.
  assert(!catalog.selections.some(s=>s.key==='queue_entry'),'Unknown-query probe unexpectedly became an authored selection');
  await navigate('structures/layout-browser.html?declaration=queue_entry');
  await waitFor(`!window.layoutExplorerCurrent&&!document.getElementById('explorer-error').hidden&&document.getElementById('explorer-error').textContent.trim()`,'Unknown authored declaration diagnostic');
  report.unknown_query=await evaluate(`({error:document.getElementById('explorer-error').textContent,offsets:document.querySelectorAll('#layout-tree [data-root-bits]').length,workers:window.layoutRuntimeClient.metrics.worker_starts})`);
  assert(report.unknown_query.offsets===0&&report.unknown_query.workers===0,'Unknown declaration query published geometry or started compiler');
  await click('reset-profile');report.query_recovery=await waitUI('recount_track');await assertNative(report.query_recovery,'release-t8103');
  const preferredFragment=await evaluate(`location.hash`);
  await navigate('structures/layout-browser.html?declaration=task'+preferredFragment);
  report.fragment_precedence=await waitUI('recount_track');await assertNative(report.fragment_precedence,'release-t8103');
  assert(report.fragment_precedence.root_id===catalog.selections.find(s=>s.key==='recount_track').declarations[report.fragment_precedence.profile],'Declaration query overrode exact bookmarked source identity');
  report.checks.push('unmapped declaration query reports diagnostic without offsets or compiler start','reset recovers from unknown authored declaration','exact layout fragment takes precedence over declaration query');

  await navigate('subsystems/runtime/recount-and-resource-attribution.html');await readerReady();
  report.recount_link=await clickLink(`document.querySelector('a[href*="layout-browser.html?declaration=recount_track"]')`);
  report.recount=await waitUI('recount_track');await assertNative(report.recount,'release-t8103');
  assert(report.recount.root_id===catalog.selections.find(s=>s.key==='recount_track')?.declarations[report.recount.profile],'Recount link did not resolve pinned source declaration identity');
  await evaluate(`window.layoutExplorer.selectField('recount_track.rt_usage.ru_metrics[1].rm_cycles')`);
  assert(await evaluate(`window.layoutExplorerCurrent.selected.rootBits===384&&window.layoutExplorerCurrent.selected.localBits===128`),'Recount deep link lost embedded array offsets');
  const baselineStarts=await evaluate(`window.layoutRuntimeClient.metrics.worker_starts`);
  await click('reset-profile');report.baseline_reuse=await waitUI('recount_track');await assertNative(report.baseline_reuse,'release-t8103');
  assert(report.baseline_reuse.workers.worker_starts===baselineStarts,'Reset did not reuse the current verified baseline');
  report.baseline_reuse.kind='controller in-memory baseline reuse; generated common-profile artifacts do not bypass browser compilation';
  await evaluate(`(()=>{window.__integrationCompilePhases=[];const c=window.layoutRuntimeClient;window.__integrationOriginalState=c.options.onstate;c.options.onstate=s=>{window.__integrationOriginalState?.(s);window.__integrationCompilePhases.push(s.state);};const input=document.getElementById('raw-directives');input.value='#define CONFIG_PERVASIVE_CPI 0';input.dispatchEvent(new Event('input',{bubbles:true}));if(window.layoutExplorerCurrent||document.querySelectorAll('#layout-tree [data-root-bits]').length)throw Error('Manual edit retained stale offsets');document.getElementById('apply-directives').click();})()`);
  report.manual=await waitUI('recount_track');await assertNative(report.manual,'probe-no-cpi');
  report.manual.phases=await evaluate(`(()=>{const phases=window.__integrationCompilePhases;window.layoutRuntimeClient.options.onstate=window.__integrationOriginalState;delete window.__integrationCompilePhases;delete window.__integrationOriginalState;return phases;})()`);
  assert(report.manual.workers.worker_starts>baselineStarts&&report.manual.phases.includes('compiling'),'Manual override did not execute a real worker compile');
  await evaluate(`document.activeElement?.blur()`);
  await call('Input.dispatchKeyEvent',{type:'keyDown',key:'/',code:'Slash',text:'/'},sessionId);
  await call('Input.dispatchKeyEvent',{type:'keyUp',key:'/',code:'Slash'},sessionId);
  await waitFor(`document.getElementById('search-dialog').open&&document.activeElement?.id==='search-input'`,'Integrated handbook keyboard search',5000);
  report.shortcut=await evaluate(`({dialogs:document.querySelectorAll('dialog[open]').length,focus:document.activeElement?.id})`);
  assert(report.shortcut.dialogs===1,'Integrated shortcut opened conflicting dialogs');
  await evaluate(`document.querySelector('[data-close-search]').click()`);
  report.explorer_search=await search('task');
  await evaluate(`window.layoutExplorer.selectField('recount_track.rt_usage.ru_metrics[1].rm_time_mach')`);
  assert(await evaluate(`window.layoutExplorerCurrent.selected.rootBits===128&&window.layoutExplorerCurrent.selected.localBits===0`),'Manual recount layout retained pre-override offsets');
  report.checks.push('authored recount inspect link resolves explicit declaration and native nested offsets','reset reuses the verified controller baseline without compiling','manual override starts a real compiler and matches native what-if','manual edit immediately clears prior geometry','handbook search and global shortcut remain functional inside explorer');

  report.screenshots={};
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false},sessionId);
  for(const theme of ['light','dark']){
    await evaluate(`(()=>{if(document.documentElement.dataset.theme!==${JSON.stringify(theme)})document.getElementById('theme-toggle').click();if(document.documentElement.dataset.theme!==${JSON.stringify(theme)})throw Error('Integrated theme handlers conflict');})()`);
    const png=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},sessionId),path=reportPath.replace(/\.json$/,'')+'-'+theme+'.png';
    await writeFile(path,Buffer.from(png.data,'base64'));report.screenshots[theme]=path;
  }
  await call('Emulation.setDeviceMetricsOverride',{width:390,height:1000,deviceScaleFactor:1,mobile:false},sessionId);
  report.narrow=await evaluate(`({width:innerWidth,scroll:document.documentElement.scrollWidth})`);assert(report.narrow.scroll<=report.narrow.width+1,'Integrated narrow page overflows horizontally');
  const narrow=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},sessionId);report.screenshots.narrow=reportPath.replace(/\.json$/,'')+'-narrow.png';await writeFile(report.screenshots.narrow,Buffer.from(narrow.data,'base64'));
  report.checks.push('shared theme works once per click in integrated explorer','light, dark and narrow integrated layouts captured');

  // The explorer source action can either use the reader popup or open its full-file wrapper.
  const sourceMarker=++navigationSequence;
  report.explorer_source=await evaluate(`(()=>{const a=document.getElementById('selected-source');if(!a||a.hidden)throw Error('Integrated declaration lacks source mapping');window.__oldIntegrationDocument=${sourceMarker};const href=a.href;a.click();return href;})()`);
  localFile(report.explorer_source);
  await waitFor(`window.__oldIntegrationDocument!==${sourceMarker}||document.getElementById('source-dialog')?.open`,'Explorer source action');
  if(await evaluate(`!!document.getElementById('source-dialog')?.open`)){
    await waitFor(`!document.getElementById('source-code').hasAttribute('aria-busy')&&document.querySelectorAll('#source-code .source-line').length>0`,'Explorer source popup');
    await clickLink(`document.getElementById('source-full-link')`);
  }
  report.explorer_full_source=await fullSource(report.explorer_source);
  assert(report.explorer_full_source.path==='xnu/osfmk/kern/recount.h','Explorer source action opened wrong header');
  await navigate('download.html');await readerReady();
  if(extracted)assert(await evaluate(`document.getElementById('content').textContent.includes('This is the offline copy')`),'Extracted archive retained online download instructions');
  report.checks.push('explorer source mapping opens the exact local full-file header','offline reading instructions match built or extracted package');

  await sampleMemory();await Promise.all([...workerSetup]);
  report.remote_requests=requests.filter(r=>/^(?:https?|wss?|ftp):/i.test(r.url)&&!allowedRequest(r.url));
  assert(report.remote_requests.length===0,'Page or worker attempted remote traffic');
  for(const request of requests)if(/^(?:file|https?):/.test(request.url))localFile(request.url);
  assert(loadingFailures.length===0,'A local reader or compiler asset failed: '+JSON.stringify(loadingFailures));
  assert(exceptions.length===0,'Browser or worker exception: '+JSON.stringify(exceptions));
  assert(await fileHash(join(bookRoot,'build-manifest.json'))===manifestHash&&await fileHash(join(bookRoot,'layouts/manifest.json'))===layoutHash,'Book or layout package changed during acceptance');
  report.checks.push('every observed book request stays inside selected file folder or local HTTPS project path','zero observed page or worker remote requests or uncaught exceptions','book and layout manifests remain unchanged during checks');
  report.status='passed';
}catch(error){report.status='failed';report.error=error.stack||String(error);process.exitCode=1;}
finally{
  clearInterval(sampler);report.elapsed_ms=performance.now()-started;report.browser_stderr=stderr;
  try{if(!ended)await call('Browser.close');}catch{/* Browser may close the pipe first. */}
  try{process.kill(-child.pid,'SIGTERM');}catch{/* Already exited. */}
  await new Promise(resolve=>setTimeout(resolve,300));
  try{process.kill(-child.pid,'SIGKILL');}catch{/* Already exited. */}
  if(server){server.closeAllConnections();await new Promise(resolve=>server.close(resolve));}
  rejectPending(Error('Integrated book check finished'));await writeFile(reportPath,JSON.stringify(report,null,2)+'\n');await rm(profile,{recursive:true,force:true});
  console.log(JSON.stringify({status:report.status,report:reportPath,checks:report.checks?.length,peak_sampled_process_rss_bytes:report.peak_sampled_process_rss_bytes,error:report.error},null,2));
}
