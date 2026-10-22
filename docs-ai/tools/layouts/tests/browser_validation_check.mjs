// SPDX-License-Identifier: GPL-2.0-only
// M8 validation: expanded live coverage and fault/recovery under file, ZIP and local HTTPS.
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
if (!bookArgument || !reportArgument || !nativeReportArgument) throw new Error('Usage: browser_validation_check.mjs book-root report.json native-comparison.json [chromium] [--extracted] [--fallback] [--https-project-path]');
const defaultProfile='release-t8103--kernel',manualCase=defaultProfile+'--no-cpi',unavailableCase=defaultProfile+'--private-undefined';
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
const surveyURL=new URL('../profiles/structure-catalog.json',import.meta.url);
const [harnessHash,manifestHash,layoutHash,evidenceHash,surveyHash,coverageHash,catalogHash]=await Promise.all([
  fileHash(new URL(import.meta.url)),
  fileHash(join(bookRoot,'build-manifest.json')),
  fileHash(join(bookRoot,'layouts/manifest.json')),
  fileHash(resolve(nativeReportArgument)),
  fileHash(surveyURL),
  fileHash(join(bookRoot,'layouts/coverage.json')),
  fileHash(join(bookRoot,'layouts/catalog.json')),
]);
const inputHashes={harness_sha256:harnessHash,build_manifest_sha256:manifestHash,layout_manifest_sha256:layoutHash,native_comparison_sha256:evidenceHash,survey_inventory_sha256:surveyHash,coverage_sha256:coverageHash,catalog_sha256:catalogHash};
const [sourceRecords,catalog,coverage]=await Promise.all(['source-records.json','layouts/catalog.json','layouts/coverage.json'].map(async name=>JSON.parse(await readFile(join(bookRoot,name),'utf8'))));
if(catalog.contract!=='platydoc.layout-catalog'||catalog.version!==1)throw Error('Expected integrated source-bound layout catalog');
const survey=JSON.parse(await readFile(surveyURL,'utf8'));
if(survey.contract!=='platydoc.structure-survey-inventory'||survey.version!==1||survey.platform!=='iPhoneOS'||new Set(survey.entries.map(entry=>entry.key)).size!==survey.entries.length||survey.source.revision!==catalog.source.revision)throw Error('Expected unique source-bound iOS survey inventory');
if(catalog.selections.length!==survey.entries.length||new Set(catalog.selections.map(entry=>entry.key)).size!==survey.entries.length||survey.entries.some(entry=>!catalog.selections.some(selection=>selection.key===entry.key)))throw Error('Catalog must retain every surveyed key, including unavailable entries');
if(coverage.contract!=='platydoc.layout-coverage'||coverage.version!==1||coverage.platform!=='iPhoneOS'||coverage.target!=='arm64e-apple-ios'||coverage.inventory_sha256!==surveyHash||coverage.source.revision!==survey.source.revision||coverage.base_profiles.length!==4||new Set(coverage.base_profiles).size!==4)throw Error('Invalid source-bound arm64e iOS coverage inventory');
const coverageRows=coverage.entries.flatMap(entry=>coverage.base_profiles.map(base=>({entry,base,cell:entry.profiles[base]})));
if(coverage.entries.length!==survey.entries.length||new Set(coverage.entries.map(entry=>entry.key)).size!==survey.entries.length||survey.entries.some(entry=>!coverage.entries.some(row=>row.key===entry.key))||coverageRows.some(row=>!row.cell||!['supported','unavailable','unsupported','compilation-error'].includes(row.cell.status)||!row.cell.reason&&row.cell.status!=='supported'))throw Error('Coverage must retain every finite survey root/base combination and failure reason');
for(const {entry,base,cell}of coverageRows){
  if(cell.full_input_equivalence!=='passed'||!Array.isArray(cell.diagnostics)||!['request_sha256','native_result_sha256'].every(key=>/^[a-f0-9]{64}$/.test(cell[key])))throw Error('Coverage lacks original equivalence/diagnostic/hash evidence: '+entry.key+'/'+base);
  if(cell.status==='supported'){
    if(cell.transport_status!=='ok')throw Error('Supported coverage cell has failed compiler transport');
    if(catalog.selections.find(selection=>selection.key===entry.key)?.declarations[cell.context_id]!==cell.declaration_id||!catalog.profiles.some(profile=>profile.id===cell.context_id)||!nativeReport.cases.includes(cell.context_id))throw Error('Supported coverage cell lacks its catalog/native binding: '+entry.key+'/'+base);
    const root=nativeReport.results[nativeReport.cases.indexOf(cell.context_id)].records.find(record=>record.id===cell.declaration_id);
    if(root?.name!==survey.entries.find(row=>row.key===entry.key)?.record)throw Error('Supported source identity maps a different native root: '+entry.key+'/'+base);
  }else{
    if(cell.declaration_id)throw Error('Unavailable coverage cell advertises geometry: '+entry.key+'/'+base);
    const result=nativeReport.results[nativeReport.cases.indexOf(base+'--unsupported--'+entry.key)];
    if(!result||result.status!==cell.transport_status||result.status!=='ok'&&result.records.length||Contracts.canonical(result.diagnostics)!==Contracts.canonical(cell.diagnostics))throw Error('Unavailable coverage cell differs from native admission evidence: '+entry.key+'/'+base);
    if(result.status==='ok'&&!result.diagnostics.length)throw Error('Successful excluded compiler result lacks its admission diagnostic: '+entry.key+'/'+base);
    if(catalog.selections.some(selection=>selection.key===entry.key&&selection.declarations[cell.context_id]))throw Error('Excluded admission cell leaked into runtime selections');
  }
}
for(const entry of catalog.profiles){const result=nativeReport.results[nativeReport.cases.indexOf(entry.id)];if(result?.status!=='ok'||result.target!=='arm64e-apple-ios'||result.effective_macros?.__arm64e__?.replacement!=='1'||result.effective_macros?.XNU_TARGET_OS_IOS?.replacement!=='1'||result.effective_macros?.XNU_TARGET_OS_OSX!==null||result.effective_macros?.__ptrauth?.function_like!==true||result.effective_macros.__ptrauth.replacement!=='')throw Error('Missing final arm64e iOS native evidence for context: '+entry.id);}
const manualProof=nativeReport.results[nativeReport.cases.indexOf(manualCase)],unavailableProof=nativeReport.results[nativeReport.cases.indexOf(unavailableCase)];
if(manualProof?.status!=='ok'||manualProof.target!=='arm64e-apple-ios'||manualProof.effective_macros?.CONFIG_PERVASIVE_CPI?.replacement!=='0'||!unavailableProof||unavailableProof.status==='ok'||unavailableProof.target!=='arm64e-apple-ios'||unavailableProof.records.length||!unavailableProof.diagnostics.length)throw Error('Final arm64e iOS native no-CPI and private-undefined probe evidence required');
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
const expectedFailureURLs=new Set();
const workerSetup = new Set();
const started = performance.now();
const report = {
  suite:'milestone8-integrated-validation',platform_scope:'arm64e-apple-ios with real upstream pointer-auth intrinsics/calls; explicit layout-only __ptrauth(...) macro erases qualifiers and the Apple-private feature macro remains unavailable. Source-context analysis, not an authenticated shipping-device ABI.',geometry_scope:'All advertised supported root/context combinations; representative native field, nonzero array, bitfield, union and anonymous-record paths, not every field.',
  ...inputHashes, native_comparison: resolve(nativeReportArgument),
  survey_roots:survey.entries.map(entry=>entry.key),coverage_summary:{base_profiles:coverage.base_profiles,combinations:coverageRows.length,status_counts:Object.fromEntries([...new Set(coverageRows.map(row=>row.cell.status))].map(status=>[status,coverageRows.filter(row=>row.cell.status===status).length]))},book_root:bookRoot,book_url:bookURL,extracted_zip:extracted,https_project_path:httpsProjectPath,https_certificate_spki_sha256_base64:certificateTrust,local_https_origin:httpsProjectPath?new URL(bookURL).origin:null,server_requests:serverRequests, fresh_profile: true, network_offline: !httpsProjectPath,page_external_requests_denied:true, cache_disabled: true,
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
  assert(result.target==='arm64e-apple-ios'&&snapshot.platform?.requestedTarget==='arm64e-apple-ios'&&snapshot.platform?.effectiveTarget==='arm64e-apple-ios','M8 requires the requested default arm64e-apple-ios target');
  assert(result.effective_macros?.__arm64e__?.replacement==='1'&&snapshot.platform.effective.__arm64e__?.replacement==='1','M8 requires the actual arm64e compiler builtin');
  assert(snapshot.platform.requestedPtrauth.intrinsics===true&&snapshot.platform.requestedPtrauth.calls===true&&result.options.includes('-fptrauth-intrinsics')&&result.options.includes('-fptrauth-calls'),'M8 requires explicit upstream pointer-auth intrinsics/calls switches passed to the frontend');
  for(const [macro,value]of Object.entries({PLATYDOC_PTRAUTH_INTRINSICS:'1',PLATYDOC_PTRAUTH_CALLS:'1',PLATYDOC_PTRAUTH_QUALIFIER:'0'}))assert(result.effective_macros?.[macro]?.replacement===value&&snapshot.platform.effective[macro]?.replacement===value,'Unexpected upstream pointer-auth feature result: '+macro);
  assert(result.effective_macros?.__PTRAUTH_INTRINSICS__===null&&snapshot.platform.effective.__PTRAUTH_INTRINSICS__?.state==='undefined','Apple-private pointer-auth macro must remain unavailable');
  assert(result.effective_macros?.__ptrauth?.function_like===true&&result.effective_macros.__ptrauth.replacement===''&&snapshot.platform.effective.__ptrauth?.state==='defined'&&snapshot.platform.effective.__ptrauth.function_like===true&&snapshot.platform.effective.__ptrauth.replacement===''&&snapshot.platform.appliedQualifierDirective&&snapshot.platform.visibleDirectiveText,'Layout-only qualifier erasure must be an explicit applied empty function-like __ptrauth macro');
  assert(result.effective_macros?.XNU_TARGET_OS_IOS?.replacement==='1'&&result.effective_macros?.XNU_TARGET_OS_OSX===null,'M8 native evidence is not explicit iOS with OSX undefined: '+name);
  assert(snapshot.platform?.requested?.XNU_TARGET_OS_IOS?.replacement==='1'&&snapshot.platform.requested.XNU_TARGET_OS_IOS.state==='defined'&&(!snapshot.platform.requested.XNU_TARGET_OS_OSX||snapshot.platform.requested.XNU_TARGET_OS_OSX.state==='undefined')&&snapshot.platform.effective.XNU_TARGET_OS_IOS?.replacement==='1'&&snapshot.platform.effective.XNU_TARGET_OS_OSX?.state==='undefined','Live result requested/effective platform is not iOS with OSX undefined');
}
function nativeField(name,path){
  const result=nativeReport.results[nativeReport.cases.indexOf(name)];assert(result,'Missing native case: '+name);
  const records=new Map(result.records.map(record=>[record.id,record]));
  const parts=path.split('.'),rootName=parts.shift();let record=result.records.find(record=>record.name===rootName),total=0,local=0,type,bitWidth=null;
  assert(record,'Missing native root: '+path);
  for(const part of parts){
    const match=/^(\w+)(?:\[(\d+)\])?$/.exec(part);assert(match,'Unsupported acceptance path: '+path);
    const field=record.fields.find(field=>field.name===match[1]);assert(field,'Missing native field: '+path);
    local=field.offset_bits;total+=local;type=field.type;bitWidth=field.bit_width;
    if(match[2]!==undefined){assert(type.kind==='array','Native field is not array: '+path);const index=Number(match[2]);assert(type.count===null||index<type.count,'Native array index outside bounds');local=index*type.element.size_bits;total+=local;type=type.element;bitWidth=null;}
    if(type.kind==='record')record=records.get(type.record_id);
  }
  return{root_bits:total,local_bits:local,size_bits:type.size_bits,bit_width:bitWidth};
}
function nativeProbes(result,root){
  const records=new Map(result.records.map(record=>[record.id,record])),samples=new Map();
  const add=(kind,path,total,local,field,type,arrays)=>{if(!samples.has(kind))samples.set(kind,{kind,path,root_bits:total,local_bits:local,bit_width:field?.bit_width??null,size_bits:type.size_bits,arrays});};
  function walk(record,path,total,seen,depth,arrays=[]){
    if(!record||depth>4||seen.has(record.id))return;seen=new Set([...seen,record.id]);
    for(const field of record.fields){
      const label=field.name||'<anonymous:'+field.id.slice(-8)+'>',fieldPath=path+'.'+label,at=total+field.offset_bits,type=field.type;
      add('field',fieldPath,at,field.offset_bits,field,type,arrays);
      if(field.bit_width!==null&&field.bit_width!==undefined)add('bitfield',fieldPath,at,field.offset_bits,field,type,arrays);
      if(record.kind==='union')add('union',fieldPath,at,field.offset_bits,field,type,arrays);
      if(!field.name||field.anonymous_record)add('anonymous',fieldPath,at,field.offset_bits,field,type,arrays);
      if(type.kind==='record')walk(records.get(type.record_id),fieldPath,at,seen,depth+1,arrays);
      if(type.kind==='array'&&type.count>0){const index=Math.min(1,type.count-1),indexed=fieldPath+'['+index+']',stride=index*type.element.size_bits,nextArrays=[...arrays,{path:fieldPath,index}];add('array',indexed,at+stride,stride,null,type.element,nextArrays);if(type.element.kind==='record')walk(records.get(type.element.record_id),indexed,at+stride,seen,depth+1,nextArrays);}
    }
  }
  walk(root,root.name,0,new Set(),0);return[...samples.values()];
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
  const waitUI=async (expectedRoot,expectedProfile=null)=>waitFor(`(async()=>{
    const c=window.layoutExplorerCurrent;if(!c||c.result?.status!=='ok'||window.layoutRuntimeClient?.active||(${JSON.stringify(expectedRoot)}!==null&&c.root_name!==${JSON.stringify(expectedRoot)})||(${JSON.stringify(expectedProfile)}!==null&&c.profile!==${JSON.stringify(expectedProfile)}))return null;
    await LayoutContracts.validate(c.contract,{analysis:c.analysis});const sha=await LayoutContracts.sha256(LayoutContracts.canonical(c.result));
    if(window.layoutExplorerCurrent!==c||window.layoutRuntimeClient.active)return null;
    return{profile:c.profile,root:c.root_name,root_id:c.root_id,sha,platform:{appliedQualifierDirective:c.request.files[c.request.main].startsWith('#define __ptrauth(...)\\n'),visibleDirectiveText:document.getElementById('directives').textContent.includes('#define __ptrauth(...)'),requestedPtrauth:{intrinsics:c.contract.configuration.requested?.ptrauth_intrinsics,calls:c.contract.configuration.requested?.ptrauth_calls},requestedTarget:c.contract.configuration.requested?.target,effectiveTarget:c.result.target,driverTarget:c.result.driver_target,requested:{XNU_TARGET_OS_IOS:c.contract.configuration.requested?.macros.XNU_TARGET_OS_IOS,XNU_TARGET_OS_OSX:c.contract.configuration.requested?.macros.XNU_TARGET_OS_OSX},effective:{__ptrauth:c.contract.configuration.effective.macros.__ptrauth,XNU_TARGET_OS_IOS:c.contract.configuration.effective.macros.XNU_TARGET_OS_IOS,XNU_TARGET_OS_OSX:c.contract.configuration.effective.macros.XNU_TARGET_OS_OSX,__arm64e__:c.contract.configuration.effective.macros.__arm64e__,__PTRAUTH_INTRINSICS__:c.contract.configuration.effective.macros.__PTRAUTH_INTRINSICS__,__ARM_FEATURE_PAUTH:c.contract.configuration.effective.macros.__ARM_FEATURE_PAUTH,__ARM_FEATURE_PAC_DEFAULT:c.contract.configuration.effective.macros.__ARM_FEATURE_PAC_DEFAULT,PLATYDOC_PTRAUTH_INTRINSICS:c.contract.configuration.effective.macros.PLATYDOC_PTRAUTH_INTRINSICS,PLATYDOC_PTRAUTH_CALLS:c.contract.configuration.effective.macros.PLATYDOC_PTRAUTH_CALLS,PLATYDOC_PTRAUTH_QUALIFIER:c.contract.configuration.effective.macros.PLATYDOC_PTRAUTH_QUALIFIER}},selected:c.selected?{path:c.selected.path,root_bits:c.selected.rootBits,local_bits:c.selected.localBits}:null,workers:{...window.layoutRuntimeClient.metrics},compiler_metrics:c.metrics,heartbeat:window.integrationHeartbeat,integrated:window.layoutExplorerConfig?.integrated,asset_root:window.layoutExplorerConfig?.assetRoot};
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
  report.task_link=await clickLink(`[...document.querySelectorAll('a[href]')].find(a=>new URL(a.href).pathname.endsWith('/structures/layout-browser.html')&&new URL(a.href).searchParams.get('declaration')==='task')`);
  report.task=await waitUI('task');assert(report.task.profile===defaultProfile,'Authored task link did not use default RELEASE T8103 arm64e iOS kernel context');await assertNative(report.task,report.task.profile);
  assert(report.task.integrated===true&&report.task.asset_root==='../layouts/','Explorer did not receive integrated asset configuration');
  report.applied_qualifier_directive=await evaluate(`(()=>{const details=document.getElementById('config-details'),summary=details.querySelector('summary');if(!details.open)summary.click();const pre=document.getElementById('directives'),text=pre.innerText,visible=details.open&&pre.getClientRects().length>0&&getComputedStyle(pre).visibility!=='hidden';const result={visible,applied:text.includes('#define __ptrauth(...)'),explanation:document.getElementById('config-limitation').innerText};summary.click();return result;})()`);
  assert(report.applied_qualifier_directive.visible&&report.applied_qualifier_directive.applied&&report.applied_qualifier_directive.explanation.includes('__ptrauth(...)'),'Directives UI does not visibly disclose applied layout-only qualifier erasure');
  report.checks.push('Directives UI visibly discloses applied empty __ptrauth(...) qualifier-erasure macro');

  assert(report.task.root_id===catalog.selections.find(s=>s.key==='task')?.declarations[report.task.profile],'Task link did not resolve pinned source declaration identity');
  assert(report.task.workers.worker_starts>0&&report.worker_targets.length>0,'Initial authoritative layout did not execute in a worker');
  assert(await evaluate(`typeof window.createLayoutEngine==='undefined'`),'Compiler was exposed on reader thread');
  report.task_shell=await readerReady();
  report.coverage_view=await evaluate(`({cells:[...document.querySelectorAll('#layout-coverage [data-coverage-root][data-base-profile]')].map(cell=>({root:cell.dataset.coverageRoot,base:cell.dataset.baseProfile,text:cell.textContent.trim()})),links:[...document.querySelectorAll('#layout-coverage tbody th a')].map(link=>({key:link.textContent,href:link.href}))})`);
  assert(report.coverage_view.cells.length===coverageRows.length&&new Set(report.coverage_view.cells.map(cell=>cell.base+'/'+cell.root)).size===coverageRows.length,'Readable finite coverage table omits or repeats survey cells');
  for(const {entry,base,cell}of coverageRows){const rendered=report.coverage_view.cells.find(row=>row.root===entry.key&&row.base===base);assert(rendered&&(cell.status==='supported'?rendered.text==='Available':rendered.text.includes(cell.status)&&rendered.text.includes(cell.reason)),'Coverage table lost original admission status/reason: '+entry.key+'/'+base);}
  assert(report.coverage_view.links.length===survey.entries.length,'Coverage table omitted authored declaration links');
  for(const link of report.coverage_view.links){localFile(link.href);assert(new URL(link.href).searchParams.get('declaration')===link.key&&survey.entries.some(entry=>entry.key===link.key),'Coverage link changed explicit survey key');}
  report.config_data=await evaluate(`(async()=>({coverage:await LayoutContracts.sha256(LayoutContracts.canonical(window.layoutExplorerConfig.coverage)),selections:await LayoutContracts.sha256(LayoutContracts.canonical(window.layoutExplorerConfig.selections))}))()`);
  assert(report.config_data.coverage===await Contracts.sha256(Contracts.canonical(coverage))&&report.config_data.selections===await Contracts.sha256(Contracts.canonical(catalog.selections)),'Page configuration differs from exact packaged coverage/selections');
  report.checks.push('readable coverage table retains every surveyed root/base status and reason','page configuration and all explicit coverage links bind exact packaged survey data');
  report.explorer_code_scope=await evaluate(`({copy:document.querySelectorAll('#structure-layout-explorer .copy-code').length,wrappers:document.querySelectorAll('#structure-layout-explorer .code-block').length})`);
  assert(report.explorer_code_scope.copy===0&&report.explorer_code_scope.wrappers===0,'Generic code enhancement wrapped live explorer controls');
  await evaluate(`window.layoutExplorer.selectField('task.ref_count')`);
  const taskGeometry=nativeField(report.task.profile,'task.ref_count');
  assert(await evaluate(`window.layoutExplorerCurrent.selected.rootBits===${taskGeometry.root_bits}&&window.layoutExplorerCurrent.selected.localBits===${taskGeometry.local_bits}`),'Task deep link did not select native task geometry');
  report.checks.push('source-page referring-chapter backlink returns to authored text','authored task inspect link resolves the explicit declaration','integrated task result matches complete native evidence','compiler remains isolated in dedicated worker','generic code copy enhancement leaves live explorer controls intact','default arm64e iOS context retains actual upstream PAC features and explicit qualifier limitation');

  // A complete but unmapped AST name must not become an authored entry point.
  const unmappedName=nativeReport.results[nativeReport.cases.indexOf(report.task.profile)].records.find(r=>r.name&&!catalog.selections.some(s=>s.key===r.name))?.name||'__not_an_authored_layout__';
  await navigate('structures/layout-browser.html?declaration='+encodeURIComponent(unmappedName));
  await waitFor(`!window.layoutExplorerCurrent&&!document.getElementById('explorer-error').hidden&&document.getElementById('explorer-error').textContent.trim()`,'Unknown authored declaration diagnostic');
  report.unknown_query=await evaluate(`({error:document.getElementById('explorer-error').textContent,offsets:document.querySelectorAll('#layout-tree [data-root-bits]').length,workers:window.layoutRuntimeClient.metrics.worker_starts})`);
  assert(report.unknown_query.offsets===0&&report.unknown_query.workers===0,'Unknown declaration query published geometry or started compiler');
  await click('reset-profile');report.query_recovery=await waitUI('recount_track');await assertNative(report.query_recovery,report.query_recovery.profile);
  const preferredFragment=await evaluate(`location.hash`);
  await navigate('structures/layout-browser.html?declaration=task'+preferredFragment);
  report.fragment_precedence=await waitUI('recount_track');await assertNative(report.fragment_precedence,report.fragment_precedence.profile);
  assert(report.fragment_precedence.root_id===catalog.selections.find(s=>s.key==='recount_track').declarations[report.fragment_precedence.profile],'Declaration query overrode exact bookmarked source identity');
  report.checks.push('unmapped declaration query reports diagnostic without offsets or compiler start','reset recovers from unknown authored declaration','exact layout fragment takes precedence over declaration query');

  const unavailable=coverageRows.find(row=>row.base==='release-t8103'&&row.cell.status!=='supported'&&!catalog.selections.some(entry=>entry.key===row.entry.key&&Object.keys(entry.declarations).length));
  assert(unavailable,'Finite survey lacks a retained unavailable declaration to exercise');
  await navigate('structures/layout-browser.html?declaration='+encodeURIComponent(unavailable.entry.key));
  await waitFor(`!window.layoutExplorerCurrent&&!document.getElementById('explorer-error').hidden&&document.getElementById('explorer-error').textContent.trim()`,'Unavailable authored declaration diagnostic');
  report.unavailable_query=await evaluate(`({error:document.getElementById('explorer-error').textContent,offsets:document.querySelectorAll('#layout-tree [data-root-bits]').length,workers:window.layoutRuntimeClient.metrics.worker_starts})`);
  report.unavailable_query.evidence={root:unavailable.entry.key,base:unavailable.base,status:unavailable.cell.status,reason:unavailable.cell.reason,diagnostics:unavailable.cell.diagnostics};
  assert(report.unavailable_query.offsets===0&&report.unavailable_query.workers===0,'Unavailable authored declaration published geometry or ran compiler');
  assert(report.unavailable_query.error.includes(unavailable.entry.key)&&(report.unavailable_query.error.includes(unavailable.cell.reason)||unavailable.cell.diagnostics.some(d=>report.unavailable_query.error.includes(d.message))),'Unavailable authored query lost its explicit root/source-backed reason');
  await click('reset-profile');report.unavailable_query_recovery=await waitUI('recount_track');await assertNative(report.unavailable_query_recovery,report.unavailable_query_recovery.profile);
  report.checks.push('known unavailable declaration reports retained source-backed reason with no geometry','reset recovers after unavailable authored declaration');

  const expandedEntry=catalog.selections.find(entry=>Object.keys(entry.declarations).length>0&&!['task','recount_track'].includes(entry.key)&&!Object.hasOwn(entry.declarations,defaultProfile)&&entry.chapters?.length);
  assert(expandedEntry,'Expanded catalog lacks a supported authored route outside the kernel closure');
  await navigate(expandedEntry.chapters[0].replace(/\.md(?=#|$)/,'.html'));await readerReady();
  report.expanded_link=await clickLink(`[...document.querySelectorAll('a[href]')].find(a=>new URL(a.href).pathname.endsWith('/structures/layout-browser.html')&&new URL(a.href).searchParams.get('declaration')===${JSON.stringify(expandedEntry.key)})`);
  report.expanded_route=await waitUI(null);await assertNative(report.expanded_route,report.expanded_route.profile);
  assert(report.expanded_route.root_id===expandedEntry.declarations[report.expanded_route.profile]&&report.expanded_route.profile!==defaultProfile,'Expanded authored route did not resolve its supported source context');
  report.checks.push('expanded authored link selects its explicit supported family context and native source identity');

  await navigate('subsystems/runtime/recount-and-resource-attribution.html');await readerReady();
  report.recount_link=await clickLink(`[...document.querySelectorAll('a[href]')].find(a=>new URL(a.href).pathname.endsWith('/structures/layout-browser.html')&&new URL(a.href).searchParams.get('declaration')==='recount_track')`);
  report.recount=await waitUI('recount_track');await assertNative(report.recount,report.recount.profile);
  assert(report.recount.root_id===catalog.selections.find(s=>s.key==='recount_track')?.declarations[report.recount.profile],'Recount link did not resolve pinned source declaration identity');
  await evaluate(`window.layoutExplorer.selectField('recount_track.rt_usage.ru_metrics[1].rm_cycles')`);
  const recountGeometry=nativeField(report.recount.profile,'recount_track.rt_usage.ru_metrics[1].rm_cycles');
  assert(await evaluate(`window.layoutExplorerCurrent.selected.rootBits===${recountGeometry.root_bits}&&window.layoutExplorerCurrent.selected.localBits===${recountGeometry.local_bits}`),'Recount deep link lost native embedded array offsets');
  const baselineStarts=await evaluate(`window.layoutRuntimeClient.metrics.worker_starts`);
  await click('reset-profile');report.baseline_reuse=await waitUI('recount_track');await assertNative(report.baseline_reuse,report.baseline_reuse.profile);
  assert(report.baseline_reuse.workers.worker_starts===baselineStarts,'Reset did not reuse the current verified baseline');
  report.baseline_reuse.kind='controller in-memory baseline reuse; generated common-profile artifacts do not bypass browser compilation';
  await evaluate(`(()=>{window.__integrationCompilePhases=[];const c=window.layoutRuntimeClient;window.__integrationOriginalState=c.options.onstate;c.options.onstate=s=>{window.__integrationOriginalState?.(s);window.__integrationCompilePhases.push(s.state);};const input=document.getElementById('raw-directives');input.value='#define CONFIG_PERVASIVE_CPI 0';input.dispatchEvent(new Event('input',{bubbles:true}));if(window.layoutExplorerCurrent||document.querySelectorAll('#layout-tree [data-root-bits]').length)throw Error('Manual edit retained stale offsets');document.getElementById('apply-directives').click();})()`);
  report.manual=await waitUI('recount_track');await assertNative(report.manual,manualCase);
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
  const manualGeometry=nativeField(manualCase,'recount_track.rt_usage.ru_metrics[1].rm_time_mach');
  assert(await evaluate(`window.layoutExplorerCurrent.selected.rootBits===${manualGeometry.root_bits}&&window.layoutExplorerCurrent.selected.localBits===${manualGeometry.local_bits}`),'Manual recount layout retained pre-override offsets');
  report.checks.push('authored recount inspect link resolves explicit declaration and native nested offsets','reset reuses the verified controller baseline without compiling','manual override starts a real compiler and matches native what-if','manual edit immediately clears prior geometry','handbook search and global shortcut remain functional inside explorer');

  console.log(JSON.stringify({phase:'reader-and-deep-links',status:'passed',checks:report.checks.length}));
  // Each advertised source root is checked against independently compiled native data.
  const baseProfile=report.task.profile,otherProfile=catalog.profiles.find(p=>p.id!==baseProfile&&p.id.endsWith('--kernel'))?.id;
  assert(otherProfile,'Failure/replacement checks require two real source profiles');
  const selectProfile=async id=>evaluate(`(()=>{const input=document.getElementById('profile-select');input.value=${JSON.stringify(id)};if(input.value!==${JSON.stringify(id)})throw Error('Profile unavailable');input.dispatchEvent(new Event('change',{bubbles:true}));if(window.layoutExplorerCurrent||document.querySelector('#layout-tree [data-root-bits]'))throw Error('Profile edit retained stale geometry');})()`);
  const noGeometry=async()=>evaluate(`!document.querySelector('#layout-tree [data-root-bits]')&&!window.layoutExplorerCurrent?.selected`);
  const failure=async label=>{
    await waitFor(`!window.layoutRuntimeClient.active&&!document.getElementById('explorer-error').hidden&&document.getElementById('explorer-error').textContent.trim()`,label);
    assert(await noGeometry(),label+' retained stale offsets');
    return evaluate(`({error:document.getElementById('explorer-error').textContent,status:document.getElementById('explorer-status').textContent,workers:{...window.layoutRuntimeClient.metrics},scripts:[...document.scripts].map(s=>s.src).filter(Boolean)})`);
  };
  report.coverage_matrix=[];report.coverage_contexts=[];report.geometry_kinds=[];
  for(const profileEntry of catalog.profiles){
    const contextStarted=performance.now();
    const first=catalog.selections.find(entry=>entry.declarations[profileEntry.id]);assert(first,'Runtime context lacks an advertised root: '+profileEntry.id);
    await selectProfile(profileEntry.id);
    await waitFor(`!window.layoutRuntimeClient.active&&!![...document.getElementById('root-select').options].find(option=>option.value===${JSON.stringify(first.declarations[profileEntry.id])})`,'Compiled family root selector');
    await evaluate(`(()=>{const input=document.getElementById('root-select');input.value=${JSON.stringify(first.declarations[profileEntry.id])};input.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    const snapshot=await waitUI(null,profileEntry.id);await assertNative(snapshot,profileEntry.id);
    report.coverage_contexts.push({...snapshot,elapsed_ms:performance.now()-contextStarted});
    const result=nativeReport.results[nativeReport.cases.indexOf(profileEntry.id)];
    for(const entry of catalog.selections){
      const id=entry.declarations[profileEntry.id];if(!id)continue;
      const root=result.records.find(r=>r.id===id);assert(root,'Advertised root missing native layout: '+entry.key+'/'+profileEntry.id);
      const displayed=await evaluate(`(()=>{const input=document.getElementById('root-select');input.value=${JSON.stringify(id)};if(input.value!==${JSON.stringify(id)})throw Error('Advertised root missing selector option');input.dispatchEvent(new Event('change',{bubbles:true}));return{root:window.layoutExplorerCurrent.root_id,size:document.getElementById('size-value').textContent,align:document.getElementById('align-value').textContent};})()`);
      assert(displayed.root===id,'Root selector chose a different source definition');
      const number=text=>Number(text.trim().split(/\s+/)[0]);
      assert(number(displayed.size)===root.size_bytes&&number(displayed.align)===root.alignment_bytes,'Advertised native structure dimensions differ: '+entry.key);
      const probes=nativeProbes(result,root),observed=[];
      for(const probe of probes){
        const actual=await evaluate(`(()=>{document.getElementById('expand-all').click();for(const bound of ${JSON.stringify(probe.arrays)}){const input=[...document.querySelectorAll('[data-array-path]')].find(i=>i.dataset.arrayPath===bound.path);if(!input)throw Error('Missing actual array index control');input.value=String(bound.index);input.dispatchEvent(new Event('change',{bubbles:true}));if(!input.validity.valid)throw Error('Native array index rejected');}window.layoutExplorer.selectField(${JSON.stringify(probe.path)});const row=[...document.querySelectorAll('.declaration-row[data-path]')].find(r=>r.dataset.path===${JSON.stringify(probe.path)});if(!row)throw Error('Native field absent from rendered rows');row.querySelector('.field-select').click();const d=window.layoutExplorerCurrent.selected;return{path:d.path,root_bits:d.rootBits,local_bits:d.localBits,bit_width:d.bitWidth,size_bits:d.type.size_bits,dom_root:Number(row.dataset.rootBits),dom_local:Number(row.dataset.localBits)};})()`);
        for(const key of ['path','root_bits','local_bits','bit_width','size_bits'])assert(actual[key]===probe[key],'Native '+probe.kind+' geometry differs: '+profileEntry.id+'/'+probe.path+'/'+key);
        assert(actual.dom_root===probe.root_bits&&actual.dom_local===probe.local_bits,'DOM offsets differ from native geometry');observed.push({expected:probe,actual});if(!report.geometry_kinds.includes(probe.kind))report.geometry_kinds.push(probe.kind);
      }
      report.coverage_matrix.push({profile:profileEntry.id,key:entry.key,id,size_bytes:root.size_bytes,alignment_bytes:root.alignment_bytes,probes:observed});
    }
    if(report.coverage_contexts.length%8===0||report.coverage_contexts.length===catalog.profiles.length)console.log(JSON.stringify({phase:'native-matrix',contexts:report.coverage_contexts.length,total:catalog.profiles.length,root_combinations:report.coverage_matrix.length,profile:profileEntry.id}));
  }
  const coveredBindings=coverageRows.filter(row=>row.cell.status==='supported').map(row=>row.cell.context_id+'/'+row.entry.key);
  const expectedCombinations=catalog.selections.flatMap(entry=>catalog.profiles.filter(profile=>Object.hasOwn(entry.declarations,profile.id)).map(profile=>profile.id+'/'+entry.key));
  assert(coveredBindings.length===expectedCombinations.length&&new Set(coveredBindings).size===coveredBindings.length&&coveredBindings.every(key=>expectedCombinations.includes(key)),'Supported catalog selections differ from complete finite survey availability');
  const actualCombinations=report.coverage_matrix.map(entry=>entry.profile+'/'+entry.key);
  assert(new Set(expectedCombinations).size===expectedCombinations.length&&new Set(actualCombinations).size===actualCombinations.length&&actualCombinations.length===expectedCombinations.length&&expectedCombinations.every(key=>actualCombinations.includes(key)),'Advertised root/profile matrix coverage differs from exact inventory');
  report.checks.push('every advertised supported root/profile renders native dimensions and representative field geometry','real source bitfields, unions, anonymous records and arrays sampled where present');

  console.log(JSON.stringify({phase:'fault-recovery',status:'started'}));
  // Faults alter this page's client only; packaged assets and manifests remain untouched.
  await selectProfile(baseProfile);
  await waitFor(`!window.layoutRuntimeClient.active&&!![...document.getElementById('root-select').options].find(option=>option.value===${JSON.stringify(catalog.selections.find(s=>s.key==='recount_track').declarations[baseProfile])})`,'Return to kernel context');
  await evaluate(`window.layoutExplorer.selectRoot('recount_track')`);await waitUI('recount_track',baseProfile);
  const missingAsset='assets/m8-intentionally-missing-profile.js';
  const missingURL=await evaluate(`(()=>{const c=window.layoutRuntimeClient,p=c.manifest.profiles.find(p=>p.id===${JSON.stringify(otherProfile)});window.__m8AssetURL=p.asset.url;p.asset.url=${JSON.stringify(missingAsset)};c.assetCache.clear();c.assetCacheBytes=0;c.metrics.asset_cache_bytes=0;return new URL(window.layoutExplorerConfig.assetRoot+p.asset.url,location.href).href;})()`);
  expectedFailureURLs.add(missingURL);const missingStart=requests.length,missingWorkers=await evaluate(`window.layoutRuntimeClient.metrics.worker_starts`);
  await selectProfile(otherProfile);report.missing_asset=await failure('Missing local asset diagnostic');
  assert(requests.slice(missingStart).some(r=>r.url===missingURL),'Missing-asset test did not issue actual local request');
  assert(httpsProjectPath?serverRequests.some(r=>r.url===new URL(missingURL).pathname&&r.status===404):loadingFailures.some(f=>f.url===missingURL),'Missing local request lacks observed failure evidence');
  report.missing_asset.intentional_url=missingURL;assert(report.missing_asset.workers.worker_starts===missingWorkers,'Missing profile asset incorrectly started compiler');
  assert(!report.missing_asset.scripts.includes(missingURL),'Failed asset script was not cleaned up');
  assert(/load|asset/i.test(report.missing_asset.error),'Missing local asset diagnostic lacks context');
  await evaluate(`(()=>{const p=window.layoutRuntimeClient.manifest.profiles.find(p=>p.id===${JSON.stringify(otherProfile)});p.asset.url=window.__m8AssetURL;delete window.__m8AssetURL;})()`);
  await click('reset-profile');report.missing_recovery=await waitUI('recount_track',otherProfile);await assertNative(report.missing_recovery,otherProfile);
  report.checks.push('actual missing local profile script clears geometry, reports error and cleans script','restored local asset recovers to complete native result');

  await evaluate(`(()=>{const c=window.layoutRuntimeClient;window.__m8OriginalLoad=c.options.loadEnvelope;window.__m8Corrupted=false;c.assetCache.clear();c.assetCacheBytes=0;c.metrics.asset_cache_bytes=0;const target=c.manifest.profiles.find(p=>p.id===${JSON.stringify(baseProfile)}).asset.id;c.options.loadEnvelope=async(asset,signal)=>{const envelope=await window.__m8OriginalLoad(asset,signal);if(asset.id!==target)return envelope;window.__m8Corrupted=true;const bytes=Uint8Array.from(atob(envelope.data),c=>c.charCodeAt(0));bytes[bytes.length-8]^=1;let data='';for(let at=0;at<bytes.length;at+=8192)data+=String.fromCharCode(...bytes.subarray(at,at+8192));return{...envelope,data:btoa(data)};};})()`);
  const corruptWorkers=await evaluate(`window.layoutRuntimeClient.metrics.worker_starts`);
  await selectProfile(baseProfile);report.corrupt_asset=await failure('Corrupt local payload diagnostic');
  assert(await evaluate(`window.__m8Corrupted`),'Corrupt-payload test failed to reach production decoder');
  report.corrupt_asset.injection={type:'gzip CRC trailer bit flip after real local asset delivery',decoder:forceFallback?'local fallback':'native DecompressionStream'};
  assert(report.corrupt_asset.workers.worker_starts===corruptWorkers,'Corrupt profile asset incorrectly started compiler');
  assert(/compress|data|damaged|CRC|checksum|gzip|integrity/i.test(report.corrupt_asset.error),'Corruption diagnostic lacks data context');
  await evaluate(`window.layoutRuntimeClient.options.loadEnvelope=window.__m8OriginalLoad;delete window.__m8OriginalLoad;delete window.__m8Corrupted`);
  await click('reset-profile');report.corrupt_recovery=await waitUI('recount_track',baseProfile);await assertNative(report.corrupt_recovery,baseProfile);
  report.checks.push('delivered local payload with corrupted gzip CRC is rejected by production decoder','valid payload recovers after corruption without package edits');

  // Cancel only after the real worker acknowledges synchronous compiler entry.
  await evaluate(`(()=>{const c=window.layoutRuntimeClient;window.__m8OriginalState=c.options.onstate;window.__m8Cancel=null;c.options.onstate=s=>{window.__m8OriginalState?.(s);if(s.state==='compiling'&&!window.__m8Cancel){window.__m8Cancel={state:s.state,id:s.id,generation:s.generation};document.getElementById('cancel-analysis').click();}};})()`);
  const cancelBefore=await evaluate(`({...window.layoutRuntimeClient.metrics})`);
  await selectProfile(otherProfile);
  await waitFor(`!!window.__m8Cancel&&!window.layoutRuntimeClient.active&&document.getElementById('explorer-status').textContent.includes('cancelled')`,'Actual compiler cancellation');
  report.cancel=await evaluate(`({ack:window.__m8Cancel,workers:{...window.layoutRuntimeClient.metrics},current:!!window.layoutExplorerCurrent,worker:!!window.layoutRuntimeClient.worker,active:!!window.layoutRuntimeClient.active})`);
  assert(report.cancel.workers.worker_starts>cancelBefore.worker_starts&&report.cancel.workers.worker_terminations>cancelBefore.worker_terminations&&!report.cancel.worker&&!report.cancel.active&&await noGeometry(),'Cancellation did not terminate an active compiler and clear geometry');
  await evaluate(`window.layoutRuntimeClient.options.onstate=window.__m8OriginalState;delete window.__m8OriginalState;delete window.__m8Cancel`);
  await click('reset-profile');report.cancel_recovery=await waitUI('recount_track',otherProfile);await assertNative(report.cancel_recovery,otherProfile);
  report.checks.push('cancel after real compiler ACK terminates worker and clears stale geometry','new analysis recovers after cancellation');

  // A second real UI profile edit supersedes a compile at its ACK boundary.
  await evaluate(`(()=>{const c=window.layoutRuntimeClient;window.__m8OriginalState=c.options.onstate;window.__m8Superseded=null;c.options.onstate=s=>{window.__m8OriginalState?.(s);if(s.state==='compiling'&&!window.__m8Superseded){window.__m8Superseded={id:s.id,generation:s.generation};const input=document.getElementById('profile-select');input.value=${JSON.stringify(otherProfile)};input.dispatchEvent(new Event('change',{bubbles:true}));}};})()`);
  await selectProfile(baseProfile);report.supersede=await waitUI('recount_track',otherProfile);await assertNative(report.supersede,otherProfile);
  report.supersede.ack=await evaluate(`window.__m8Superseded`);assert(report.supersede.ack,'Replacement test did not reach actual compiler ACK');
  await evaluate(`window.layoutRuntimeClient.options.onstate=window.__m8OriginalState;delete window.__m8OriginalState;delete window.__m8Superseded`);
  await new Promise(resolve=>setTimeout(resolve,300));
  assert(await evaluate(`window.layoutExplorerCurrent.profile===${JSON.stringify(otherProfile)}&&!window.layoutRuntimeClient.active`),'Cancelled old compile published over replacement');
  report.checks.push('new UI request supersedes an acknowledged real compile without stale publication');

  await selectProfile(baseProfile);report.final_baseline=await waitUI('recount_track',baseProfile);await assertNative(report.final_baseline,baseProfile);
  const unavailableNative=nativeReport.results[nativeReport.cases.indexOf(unavailableCase)];
  assert(unavailableNative&&unavailableNative.status!=='ok'&&unavailableNative.records.length===0&&unavailableNative.diagnostics.length>0&&unavailableNative.target==='arm64e-apple-ios','Final source-backed private-undefined native failure evidence required; interim ABI results are not accepted');
  await evaluate(`(()=>{const c=window.layoutRuntimeClient;window.__m8OriginalState=c.options.onstate;window.__m8FailurePhases=[];c.options.onstate=s=>{window.__m8OriginalState?.(s);window.__m8FailurePhases.push(s.state);};const input=document.getElementById('raw-directives');input.value='#undef MACH_KERNEL_PRIVATE';input.dispatchEvent(new Event('input',{bubbles:true}));if(window.layoutExplorerCurrent||document.querySelector('#layout-tree [data-root-bits]'))throw Error('Unavailable directive retained geometry');document.getElementById('apply-directives').click();})()`);
  report.unsupported_override=await failure('Source-backed unavailable configuration diagnostic');
  report.unsupported_override.result=await evaluate(`(async()=>{const c=window.layoutExplorerCurrent;await LayoutContracts.validate(c.contract,{analysis:c.analysis});return{status:c.result.status,records:c.result.records.length,sha:await LayoutContracts.sha256(LayoutContracts.canonical(c.result)),requested:c.contract.configuration.requested.macros.MACH_KERNEL_PRIVATE,phases:window.__m8FailurePhases};})()`);
  assert(report.unsupported_override.result.sha===await Contracts.sha256(Contracts.canonical(unavailableNative))&&report.unsupported_override.result.status===unavailableNative.status&&report.unsupported_override.result.records===0&&report.unsupported_override.result.requested?.state==='undefined'&&report.unsupported_override.result.phases.includes('compiling'),'Unavailable configuration differs from final native failure or did not run real compiler');
  await evaluate(`window.layoutRuntimeClient.options.onstate=window.__m8OriginalState;delete window.__m8OriginalState;delete window.__m8FailurePhases`);
  await click('reset-profile');report.unsupported_override_recovery=await waitUI('recount_track',baseProfile);await assertNative(report.unsupported_override_recovery,baseProfile);
  report.checks.push('source-backed unavailable macro configuration runs real compiler and matches final native failure','reset recovers native baseline after unavailable configuration');
  await evaluate(`(()=>{const c=window.layoutRuntimeClient;window.__m8OriginalState=c.options.onstate;window.__m8FailurePhases=[];c.options.onstate=s=>{window.__m8OriginalState?.(s);window.__m8FailurePhases.push(s.state);};})()`);
  await evaluate(`(()=>{const input=document.getElementById('raw-directives');input.value='#define CONFIG_PERVASIVE_CPI )';input.dispatchEvent(new Event('input',{bubbles:true}));if(window.layoutExplorerCurrent||document.querySelector('#layout-tree [data-root-bits]'))throw Error('Invalid edit retained geometry');document.getElementById('apply-directives').click();})()`);
  report.compiler_error=await failure('Actual compiler syntax diagnostic');
  report.compiler_error.result=await evaluate(`({status:window.layoutExplorerCurrent?.result.status,records:window.layoutExplorerCurrent?.result.records.length,diagnostics:window.layoutExplorerCurrent?.result.diagnostics,phases:window.__m8FailurePhases})`);
  assert(report.compiler_error.result.phases.includes('compiling')&&report.compiler_error.result.status==='error'&&report.compiler_error.result.records===0&&report.compiler_error.result.diagnostics.some(d=>d.severity==='error'),'Malformed expression did not run compiler and reject all geometry');
  await evaluate(`window.layoutRuntimeClient.options.onstate=window.__m8OriginalState;delete window.__m8OriginalState;delete window.__m8FailurePhases`);
  await click('reset-profile');report.compiler_error_recovery=await waitUI('recount_track',baseProfile);await assertNative(report.compiler_error_recovery,baseProfile);
  report.checks.push('real compiler syntax error clears prior geometry and preserves useful diagnostics','reset recovers native baseline after compiler failure');
  // The compiler accepts this macro edit; the runtime must reject its false PAC context.
  await evaluate(`(()=>{const c=window.layoutRuntimeClient;window.__m8OriginalState=c.options.onstate;window.__m8FailurePhases=[];c.options.onstate=s=>{window.__m8OriginalState?.(s);window.__m8FailurePhases.push(s.state);};const input=document.getElementById('raw-directives');input.value='#undef __arm64e__';input.dispatchEvent(new Event('input',{bubbles:true}));if(window.layoutExplorerCurrent||document.querySelector('#layout-tree [data-root-bits]'))throw Error('PAC edit retained stale geometry');document.getElementById('apply-directives').click();})()`);
  report.pac_guard=await failure('Runtime PAC context rejection');
  report.pac_guard.state=await evaluate(`({runtime:window.layoutRuntimeState,phases:window.__m8FailurePhases,publishedSuccess:window.layoutExplorerCurrent?.result.status==='ok'})`);
  assert(/PAC|arm64e|pointer.auth/i.test(report.pac_guard.error)&&!report.pac_guard.state.publishedSuccess,'Runtime accepted a false arm64e PAC context or omitted a clear PAC diagnostic');
  await evaluate(`window.layoutRuntimeClient.options.onstate=window.__m8OriginalState;delete window.__m8OriginalState;delete window.__m8FailurePhases`);
  await click('reset-profile');report.pac_guard_recovery=await waitUI('recount_track',baseProfile);await assertNative(report.pac_guard_recovery,baseProfile);
  report.checks.push('runtime rejects manual arm64e-macro erasure with a clear PAC error and no published geometry','reset restores the verified native PAC context after rejected arm64e override');

  await evaluate(`(()=>{const input=document.getElementById('raw-directives');input.value='#define CONFIG_PERVASIVE_CPI 0';input.dispatchEvent(new Event('input',{bubbles:true}));document.getElementById('apply-directives').click();})()`);
  report.final_manual=await waitUI('recount_track',baseProfile);await assertNative(report.final_manual,manualCase);
  await evaluate(`window.layoutExplorer.selectField('recount_track.rt_usage.ru_metrics[1].rm_time_mach')`);
  report.runtime_bounds=await evaluate(`({metrics:{...window.layoutRuntimeClient.metrics},cacheBudget:window.layoutRuntimeClient.assetBudget,worker:!!window.layoutRuntimeClient.worker,active:!!window.layoutRuntimeClient.active,storage:[...['localStorage','sessionStorage','indexedDB']].map(name=>{try{window[name];return{name,blocked:false};}catch{return{name,blocked:true};}})})`);
  assert(report.runtime_bounds.metrics.worker_starts===report.runtime_bounds.metrics.worker_terminations&&!report.runtime_bounds.worker&&!report.runtime_bounds.active,'Completed real XNU workers were not retired');
  assert(report.runtime_bounds.metrics.asset_cache_bytes<=report.runtime_bounds.cacheBudget&&report.runtime_bounds.storage.every(s=>s.blocked)&&report.runtime_bounds.metrics.persistence==='disabled','Runtime cache or storage bounds violated');
  report.checks.push('runtime completes without retained compiler workers and respects decoded cache budget','window storage remains disabled throughout recovery and profile matrix');
  report.post_recovery_search=await search('vm_map_entry');
  report.checks.push('handbook search remains usable after asset and compiler recovery');

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
  report.expected_local_loading_failures=loadingFailures.filter(f=>expectedFailureURLs.has(f.url));
  report.unexpected_loading_failures=loadingFailures.filter(f=>!expectedFailureURLs.has(f.url));
  assert(report.unexpected_loading_failures.length===0,'An unexpected reader/compiler asset failed: '+JSON.stringify(report.unexpected_loading_failures));
  assert(exceptions.length===0,'Browser or worker exception: '+JSON.stringify(exceptions));
  assert(await fileHash(new URL(import.meta.url))===harnessHash&&await fileHash(join(bookRoot,'build-manifest.json'))===manifestHash&&await fileHash(join(bookRoot,'layouts/manifest.json'))===layoutHash&&await fileHash(join(bookRoot,'layouts/coverage.json'))===coverageHash&&await fileHash(join(bookRoot,'layouts/catalog.json'))===catalogHash&&await fileHash(surveyURL)===surveyHash&&await fileHash(resolve(nativeReportArgument))===evidenceHash,'Book, layout, coverage, survey or native evidence changed during acceptance');
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
