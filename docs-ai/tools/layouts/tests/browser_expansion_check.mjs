// SPDX-License-Identifier: GPL-2.0-only
// Focused thread/IPv6 expansion acceptance; reviewed M8 harness and evidence remain unchanged.
import { spawn } from 'node:child_process';
import { createReadStream } from 'node:fs';
import { mkdtemp, readFile, readdir, rm, writeFile } from 'node:fs/promises';
import { resolve, dirname, join, relative, isAbsolute } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { createRequire } from 'node:module';
import { createHash, X509Certificate } from 'node:crypto';
import { createServer } from 'node:https';

const args=process.argv.slice(2), options={}, positional=[];
for(let at=0;at<args.length;at++){
  const arg=args[at];
  if(arg==='--https-project-path')options.https=true;
  else if(['--baseline-book','--baseline-native','--baseline-browser'].includes(arg)){if(!args[at+1]||args[at+1].startsWith('--')||options[arg])throw Error('Missing/duplicate '+arg);options[arg]=args[++at];}
  else if(arg.startsWith('--'))throw Error('Unknown option: '+arg);else positional.push(arg);
}
const [bookArgument,reportArgument,nativeReportArgument,browser='chromium']=positional;
const baselineOptions=['--baseline-book','--baseline-native','--baseline-browser'];
if(positional.length<3||positional.length>4||baselineOptions.some(key=>options[key])&&!baselineOptions.every(key=>options[key]))throw Error('Usage: browser_expansion_check.mjs BOOK REPORT COMPARISON [CHROMIUM] [--baseline-book M8_BOOK --baseline-native M8_COMPARISON --baseline-browser M8_BROWSER_REPORT] [--https-project-path]');
const baselineAudit=baselineOptions.every(key=>options[key]);
const httpsProjectPath=Boolean(options.https),extracted=false,forceFallback=false;
const baselineBook=baselineAudit?resolve(options['--baseline-book']):null,baselineNativePath=baselineAudit?resolve(options['--baseline-native']):null,baselineBrowserPath=baselineAudit?resolve(options['--baseline-browser']):null;
const REVIEWED_BASELINE_BROWSER='951945d0e169132c5c78afd7d1dfa8692a195ff93ddc60789938b83bdd56e622';
const APPROVED_NEW_ROOTS=['machine_thread','arm_saved_state64','thread_group','in6_addr','sockaddr_in6','ip6_hdr','ip6_hbh','ip6_dest','ip6_rthdr','ip6_frag','ip6_pktopts','ip6_exthdrs','ip6_out_args','ip6q','ip6_moptions','route_in6','in6_ifaddr','in6_multi','in6_mfilter','nd_ifinfo','nd_defrouter','nd_prefix','llinfo_nd6','mld_ifinfo'];
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

let baselineHashes=null,baselineSummary={mode:'current-artifacts-only',prior_preservation:'not asserted'},baselinePreservation=[];
const newEntries=coverage.entries.filter(entry=>APPROVED_NEW_ROOTS.includes(entry.key)),newKeys=newEntries.map(entry=>entry.key);
if(newKeys.length!==APPROVED_NEW_ROOTS.length||new Set(newKeys).size!==APPROVED_NEW_ROOTS.length)throw Error('Missing or duplicate approved expansion root');
if(baselineAudit){
baselineHashes={browser:await fileHash(baselineBrowserPath),native:await fileHash(baselineNativePath),build:await fileHash(join(baselineBook,'build-manifest.json')),catalog:await fileHash(join(baselineBook,'layouts/catalog.json')),coverage:await fileHash(join(baselineBook,'layouts/coverage.json')),layout:await fileHash(join(baselineBook,'layouts/manifest.json'))};
if(baselineHashes.browser!==REVIEWED_BASELINE_BROWSER)throw Error('Baseline browser proof is not the reviewed M8 file acceptance');
const [baselineProof,baselineNative,baselineCatalog,baselineCoverage,baselineManifest,baselineBuild,runtimeManifest,baselineRuntime]=await Promise.all([
  baselineBrowserPath,baselineNativePath,join(baselineBook,'layouts/catalog.json'),join(baselineBook,'layouts/coverage.json'),join(baselineBook,'layouts/manifest.json'),join(baselineBook,'build-manifest.json'),join(bookRoot,'layouts/runtime-manifest.json'),join(baselineBook,'layouts/runtime-manifest.json')
].map(async path=>JSON.parse(await readFile(path,'utf8'))));
if(baselineProof.status!=='passed'||baselineProof.native_comparison_sha256!==baselineHashes.native||baselineProof.build_manifest_sha256!==baselineHashes.build||baselineProof.catalog_sha256!==baselineHashes.catalog||baselineProof.coverage_sha256!==baselineHashes.coverage||baselineProof.layout_manifest_sha256!==baselineHashes.layout)throw Error('Reviewed baseline book/native artifacts no longer match accepted proof');
if(Contracts.canonical(coverage.base_profiles)!==Contracts.canonical(baselineCoverage.base_profiles)||Contracts.canonical(coverage.source)!==Contracts.canonical(baselineCoverage.source))throw Error('Expansion changes the reviewed base/source scope');
const baselineKeys=new Set(baselineCoverage.entries.map(entry=>entry.key)),actualNewKeys=coverage.entries.filter(entry=>!baselineKeys.has(entry.key)).map(entry=>entry.key);
if(actualNewKeys.length!==APPROVED_NEW_ROOTS.length||actualNewKeys.some(key=>!APPROVED_NEW_ROOTS.includes(key)))throw Error('Expanded inventory differs from the approved thread/IPv6 root set');
function rootMeaning(record){return{id:record.id,name:record.name,kind:record.kind,size_bytes:record.size_bytes,alignment_bytes:record.alignment_bytes,fields:record.fields.map(({location,...field})=>field)};}
for(const entry of baselineCoverage.entries)for(const base of baselineCoverage.base_profiles){
  const old=entry.profiles[base],next=coverage.entries.find(row=>row.key===entry.key)?.profiles[base];
  if(!next||old.status!==next.status)throw Error('Prior admission changed: '+base+'/'+entry.key);
  if(old.status==='supported'){
    const oldResult=baselineNative.results[baselineNative.cases.indexOf(old.context_id)],nextResult=nativeReport.results[nativeReport.cases.indexOf(next.context_id)];
    const before=oldResult.records.find(record=>record.id===old.declaration_id),after=nextResult.records.find(record=>record.id===next.declaration_id);
    if(!before||!after||before.id!==after.id||Contracts.canonical(rootMeaning(before))!==Contracts.canonical(rootMeaning(after)))throw Error('Prior root source ID/geometry/type changed: '+base+'/'+entry.key);
    baselinePreservation.push({root:entry.key,base,prior_context:old.context_id,current_context:next.context_id,id:after.id,geometry_sha256:await Contracts.sha256(Contracts.canonical(rootMeaning(after)))});
  }else if(old.reason!==next.reason||old.transport_status!==next.transport_status||Contracts.canonical(old.diagnostics)!==Contracts.canonical(next.diagnostics))throw Error('Prior boundary evidence changed: '+base+'/'+entry.key);
}
// This focused suite relies on unchanged reviewed renderer/worker code, not repeated reader tests.
const sharedCode=['book-layouts.js','contracts.js','dependencies.js','explorer-model.js','layout-codec.js','layout-runtime.js','layouts.js','layouts.css'];
const unchangedCode=[];
for(const name of sharedCode){const before=await fileHash(join(baselineBook,'layouts',name)),after=await fileHash(join(bookRoot,'layouts',name));if(before!==baselineManifest.files[name]?.sha256||before!==after)throw Error('Runtime code changed; focused data-expansion acceptance is insufficient: '+name);unchangedCode.push({path:'layouts/'+name,sha256:after});}
for(const name of ['book.js','book.css']){const before=await fileHash(join(baselineBook,'assets',name)),after=await fileHash(join(bookRoot,'assets',name));if(before!==baselineBuild.book_tool_hashes['docs-ai/tools/book/assets/'+name]||before!==after)throw Error('Reader code changed; focused data-expansion acceptance is insufficient: '+name);unchangedCode.push({path:'assets/'+name,sha256:after});}
if(Contracts.canonical(runtimeManifest.compiler)!==Contracts.canonical(baselineRuntime.compiler))throw Error('Compiler identity changed outside expansion scope');
for(const name of Object.keys(baselineRuntime.assets)){if(runtimeManifest.assets[name]?.sha256!==baselineRuntime.assets[name].sha256||runtimeManifest.assets[name].bytes!==baselineRuntime.assets[name].bytes)throw Error('Worker/compiler asset changed outside expansion scope: '+name);}
baselineSummary={mode:'reviewed-m8-preservation',book:baselineBook,native:baselineNativePath,browser:baselineBrowserPath,...baselineHashes,prior_supported_bindings:baselinePreservation.length,old_root_geometry_and_source_ids:'preserved',unchanged_code:unchangedCode};
}
const declaredBindings=catalog.selections.flatMap(entry=>Object.keys(entry.declarations).map(context=>context+'/'+entry.key)),supportedBindings=coverageRows.filter(row=>row.cell.status==='supported').map(row=>row.cell.context_id+'/'+row.entry.key);
if(new Set(declaredBindings).size!==declaredBindings.length||new Set(supportedBindings).size!==supportedBindings.length||declaredBindings.length!==supportedBindings.length||supportedBindings.some(binding=>!declaredBindings.includes(binding)))throw Error('Catalog declarations differ from exact supported survey bindings');
const supportedContexts=[...new Set(coverageRows.filter(row=>row.cell.status==='supported').map(row=>row.cell.context_id))],advertisedContexts=catalog.profiles.map(profile=>profile.id);
if(new Set(advertisedContexts).size!==advertisedContexts.length||advertisedContexts.length!==supportedContexts.length||supportedContexts.some(context=>!advertisedContexts.includes(context)))throw Error('Advertised runtime contexts differ from supported survey contexts');
for(const entry of newEntries)for(const base of coverage.base_profiles){const expected=['thread_group','in6_ifaddr'].includes(entry.key)?'boundary':'supported';if((entry.profiles[base].status==='supported')!==(expected==='supported'))throw Error('Approved expansion admission changed: '+entry.key+'/'+base);}
const newSupportedRows=coverageRows.filter(row=>newKeys.includes(row.entry.key)&&row.cell.status==='supported');
const targetContexts=baselineAudit?[...new Set(newSupportedRows.map(row=>row.cell.context_id))].sort():catalog.profiles.map(profile=>profile.id).sort();
const targetRows=coverageRows.filter(row=>row.cell.status==='supported'&&targetContexts.includes(row.cell.context_id));
const newBoundaries=coverageRows.filter(row=>newKeys.includes(row.entry.key)&&row.cell.status!=='supported');
if(!targetContexts.length||!newSupportedRows.length||!newBoundaries.length)throw Error('Expansion lacks supported and explicit boundary coverage');
for(const key of ['thread_group','in6_ifaddr'])if(!newEntries.find(entry=>entry.key===key)||coverageRows.some(row=>row.entry.key===key&&row.cell.status==='supported'))throw Error('Declared expansion boundary unexpectedly became selectable: '+key);
const deltaSummary={new_roots:newKeys,target_contexts:targetContexts,new_supported_bindings:newSupportedRows.length,new_boundary_cells:newBoundaries.length,live_root_combinations:targetRows.length,prior_geometry:baselinePreservation};

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
  suite:'thread-ipv6-expansion',platform_scope:'arm64e-apple-ios with real upstream pointer-auth intrinsics/calls; explicit layout-only __ptrauth(...) macro erases qualifiers and the Apple-private feature macro remains unavailable. Source-context analysis, not an authenticated shipping-device ABI.',geometry_scope:baselineAudit?'New curated roots and existing roots sharing changed contexts; representative native geometry plus explicit thread registers, packed IPv6 address tails, route nesting and bitfields. Prior M8 reader/fault acceptance is hash-bound and unchanged executable assets are verified.':'All current curated runtime contexts; representative native geometry plus explicit expansion probes. Historical preservation and the full reader/fault suites are outside this standalone run.',
  ...inputHashes,baseline:baselineSummary,delta:deltaSummary,native_comparison: resolve(nativeReportArgument),
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
// Source-derived paths exercise last array elements and nested, packed wire records.
const EXPLICIT_FIELDS={
  machine_thread:['upcb','uNeon','kstackptr','rop_pid','jop_pid'],
  arm_saved_state64:['x[28]'],
  in6_addr:['__u6_addr.__u6_addr8[15]','__u6_addr.__u6_addr32[3]'],
  sockaddr_in6:['sin6_addr.__u6_addr.__u6_addr8[15]'],
  ip6_hdr:['ip6_ctlun.ip6_un1.ip6_un1_plen','ip6_src.__u6_addr.__u6_addr32[3]','ip6_dst.__u6_addr.__u6_addr8[15]'],
  ip6_frag:['ip6f_ident'],
  ip6_pktopts:['ip6po_minmtu','ip6po_prefer_tempaddr','ip6po_flags','ip6po_nhinfo.ip6po_nhi_route.ro_dst.sin6_addr.__u6_addr.__u6_addr8[15]'],
  route_in6:['ro_dst.sin6_addr.__u6_addr.__u6_addr8[15]'],
};
// Independently checked from source and external Clang record-layout dumps; offsets are bits.
const INDEPENDENT_WIRE={in6_addr:{size:16,align:4},sockaddr_in6:{size:28,align:4},ip6_hdr:{size:40,align:1},ip6_frag:{size:8,align:1},ip6_pktopts:{size:152,align:8}};
const INDEPENDENT_FIELDS={
  'ip6_hdr.ip6_dst.__u6_addr.__u6_addr8[15]':{bits:39*8},
  'sockaddr_in6.sin6_addr.__u6_addr.__u6_addr8[15]':{bits:23*8},
  'ip6_frag.ip6f_ident':{bits:4*8},
  'ip6_pktopts.ip6po_minmtu':{bits:32,width:3},
  'ip6_pktopts.ip6po_prefer_tempaddr':{bits:35,width:3},
  'ip6_pktopts.ip6po_flags':{bits:38,width:2},
};
function explicitProbe(context,path){
  const result=nativeReport.results[nativeReport.cases.indexOf(context)],records=new Map(result.records.map(record=>[record.id,record])),parts=path.split('.'),rootName=parts.shift();
  let record=result.records.find(record=>record.name===rootName),total=0,local=0,type,bitWidth=null,prefix=rootName;const arrays=[];
  assert(record,'Missing explicit native root: '+context+'/'+path);
  for(const part of parts){
    const match=/^(\w+)(?:\[(\d+)\])?$/.exec(part);assert(match,'Unsupported explicit path: '+path);
    const field=record?.fields.find(field=>field.name===match[1]);assert(field,'Missing explicit native field: '+context+'/'+path);
    local=field.offset_bits;total+=local;type=field.type;bitWidth=field.bit_width??null;prefix+='.'+match[1];
    if(match[2]!==undefined){
      assert(type.kind==='array','Explicit native field is not array: '+path);const index=Number(match[2]);assert(Number.isSafeInteger(type.count)&&index>=0&&index<type.count,'Explicit native array index outside bounds');
      arrays.push({path:prefix,index});local=index*type.element.size_bits;total+=local;type=type.element;bitWidth=null;prefix+='['+index+']';
    }
    if(type.kind==='record')record=records.get(type.record_id);
  }
  return{kind:'explicit',path,root_bits:total,local_bits:local,size_bits:type.size_bits,bit_width:bitWidth,arrays};
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
    // CDP omits loaderId for a same-document anchor transition; that document stays alive.
    if(result.loaderId)await waitDocument(href,marker);
    else await waitFor(`location.href===${JSON.stringify(href)}&&document.readyState==='complete'`,'Same-document chapter navigation');
    return href;
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
  await navigate('structures/layout-browser.html?declaration=machine_thread');
  report.initial=await waitUI('machine_thread');await assertNative(report.initial,report.initial.profile);
  report.reader=await readerReady();
  assert(report.initial.root_id===catalog.selections.find(entry=>entry.key==='machine_thread').declarations[report.initial.profile],'Thread query lost explicit native source identity');
  assert(report.initial.workers.worker_starts>0&&report.worker_targets.length>0&&await evaluate(`typeof window.createLayoutEngine==='undefined'`),'Authoritative compiler must execute in a dedicated worker');
  report.coverage_view=await evaluate(`({cells:[...document.querySelectorAll('#layout-coverage [data-coverage-root][data-base-profile]')].map(cell=>({root:cell.dataset.coverageRoot,base:cell.dataset.baseProfile,text:cell.textContent.trim()})),links:[...document.querySelectorAll('#layout-coverage tbody th a')].map(link=>({key:link.textContent,href:link.href}))})`);
  assert(report.coverage_view.cells.length===coverageRows.length&&new Set(report.coverage_view.cells.map(cell=>cell.base+'/'+cell.root)).size===coverageRows.length,'Coverage table omits or repeats finite survey cells');
  for(const {entry,base,cell}of coverageRows){const rendered=report.coverage_view.cells.find(row=>row.root===entry.key&&row.base===base);assert(rendered&&(cell.status==='supported'?rendered.text==='Available':rendered.text.includes(cell.status)&&rendered.text.includes(cell.reason)),'Coverage table changed admission evidence: '+entry.key+'/'+base);}
  assert(report.coverage_view.links.length===survey.entries.length,'Coverage table omitted authored declaration links');
  for(const link of report.coverage_view.links){localFile(link.href);assert(new URL(link.href).searchParams.get('declaration')===link.key&&survey.entries.some(entry=>entry.key===link.key),'Coverage link changed explicit survey key');}
  report.config_data=await evaluate(`(async()=>({coverage:await LayoutContracts.sha256(LayoutContracts.canonical(window.layoutExplorerConfig.coverage)),selections:await LayoutContracts.sha256(LayoutContracts.canonical(window.layoutExplorerConfig.selections))}))()`);
  assert(report.config_data.coverage===await Contracts.sha256(Contracts.canonical(coverage))&&report.config_data.selections===await Contracts.sha256(Contracts.canonical(catalog.selections)),'Page configuration differs from packaged coverage/selections');
  assert(await evaluate(`!document.querySelector('#structure-layout-explorer .copy-code,#structure-layout-explorer .code-block')`),'Generic reader code enhancement wrapped explorer');
  report.checks.push('expanded coverage table and query bind every exact source-backed survey status','integrated shell and worker remain functional with disabled persistence');

  const selectProfile=async id=>evaluate(`(()=>{const input=document.getElementById('profile-select');if(input.value===${JSON.stringify(id)})return;input.value=${JSON.stringify(id)};if(input.value!==${JSON.stringify(id)})throw Error('Profile unavailable');input.dispatchEvent(new Event('change',{bubbles:true}));if(window.layoutExplorerCurrent||document.querySelector('#layout-tree [data-root-bits]'))throw Error('Profile edit retained stale geometry');})()`);
  const observeProbe=async probe=>{
    const actual=await evaluate(`(()=>{document.getElementById('expand-all').click();for(const bound of ${JSON.stringify(probe.arrays)}){const input=[...document.querySelectorAll('[data-array-path]')].find(i=>i.dataset.arrayPath===bound.path);if(!input)throw Error('Missing actual array index control: '+bound.path);input.value=String(bound.index);input.dispatchEvent(new Event('change',{bubbles:true}));if(!input.validity.valid)throw Error('Native array index rejected');}window.layoutExplorer.selectField(${JSON.stringify(probe.path)});const row=[...document.querySelectorAll('.declaration-row[data-path]')].find(r=>r.dataset.path===${JSON.stringify(probe.path)});if(!row)throw Error('Native field absent from rendered rows');row.querySelector('.field-select').click();const d=window.layoutExplorerCurrent.selected;return{path:d.path,root_bits:d.rootBits,local_bits:d.localBits,bit_width:d.bitWidth,size_bits:d.type.size_bits,dom_root:Number(row.dataset.rootBits),dom_local:Number(row.dataset.localBits)};})()`);
    for(const key of ['path','root_bits','local_bits','bit_width','size_bits'])assert(actual[key]===probe[key],'Native '+probe.kind+' geometry differs: '+probe.path+'/'+key);
    assert(actual.dom_root===probe.root_bits&&actual.dom_local===probe.local_bits,'DOM offsets differ from native geometry');return{expected:probe,actual};
  };
  report.coverage_matrix=[];report.coverage_contexts=[];report.geometry_kinds=[];
  for(const context of targetContexts){
    const contextStarted=performance.now(),rows=targetRows.filter(row=>row.cell.context_id===context),first=rows[0];assert(first,'Target context has no source-bound selections');
    await selectProfile(context);
    await waitFor(`!window.layoutRuntimeClient.active&&!![...document.getElementById('root-select').options].find(option=>option.value===${JSON.stringify(first.cell.declaration_id)})`,'Compiled family root selector');
    await evaluate(`(()=>{const input=document.getElementById('root-select');input.value=${JSON.stringify(first.cell.declaration_id)};input.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    const snapshot=await waitUI(first.entry.record,context);await assertNative(snapshot,context);
    report.coverage_contexts.push({...snapshot,elapsed_ms:performance.now()-contextStarted});
    const result=nativeReport.results[nativeReport.cases.indexOf(context)];
    for(const {entry,cell}of rows){
      const root=result.records.find(record=>record.id===cell.declaration_id);assert(root,'Advertised root missing native layout: '+entry.key+'/'+context);
      const displayed=await evaluate(`(()=>{const input=document.getElementById('root-select');input.value=${JSON.stringify(cell.declaration_id)};if(input.value!==${JSON.stringify(cell.declaration_id)})throw Error('Advertised root missing selector option');input.dispatchEvent(new Event('change',{bubbles:true}));return{root:window.layoutExplorerCurrent.root_id,size:document.getElementById('size-value').textContent,align:document.getElementById('align-value').textContent};})()`);
      assert(displayed.root===root.id,'Root selector chose a different source definition');
      const number=text=>Number(text.trim().split(/\s+/)[0]);
      assert(number(displayed.size)===root.size_bytes&&number(displayed.align)===root.alignment_bytes,'Native root dimensions differ: '+entry.key+'/'+context);
      const probes=nativeProbes(result,root),observed=[];
      for(const suffix of EXPLICIT_FIELDS[entry.key]||[])probes.push(explicitProbe(context,entry.record+'.'+suffix));
      for(const probe of probes){observed.push(await observeProbe(probe));if(!report.geometry_kinds.includes(probe.kind))report.geometry_kinds.push(probe.kind);}
      if(entry.key==='machine_thread')assert(['upcb','uNeon','kstackptr','rop_pid','jop_pid'].every(name=>root.fields.some(field=>field.name===name)),'Thread PAC-dependent fields disappeared');
      const independent=INDEPENDENT_WIRE[entry.key];
      if(independent)assert(root.size_bytes===independent.size&&root.alignment_bytes===independent.align,'Source/external-Clang wire dimensions differ: '+entry.key);
      for(const probe of probes){const verified=INDEPENDENT_FIELDS[probe.path];if(verified)assert(probe.root_bits===verified.bits&&(verified.width===undefined||probe.bit_width===verified.width),'External-Clang/source arithmetic differs: '+probe.path);}
      report.coverage_matrix.push({profile:context,key:entry.key,id:root.id,size_bytes:root.size_bytes,alignment_bytes:root.alignment_bytes,probes:observed});
    }
    if(report.coverage_contexts.length%4===0||report.coverage_contexts.length===targetContexts.length)console.log(JSON.stringify({phase:'expansion-native-matrix',contexts:report.coverage_contexts.length,total:targetContexts.length,root_combinations:report.coverage_matrix.length,profile:context}));
  }
  const exactSet=(expected,actual)=>new Set(expected).size===expected.length&&new Set(actual).size===actual.length&&actual.length===expected.length&&expected.every(key=>actual.includes(key));
  const expectedCombinations=targetRows.map(row=>row.cell.context_id+'/'+row.entry.key),actualCombinations=report.coverage_matrix.map(row=>row.profile+'/'+row.key);
  assert(exactSet(expectedCombinations,actualCombinations)&&exactSet(targetContexts,report.coverage_contexts.map(row=>row.profile)),'Live matrix does not match exact expected context/root sets');
  assert(newSupportedRows.every(row=>actualCombinations.includes(row.cell.context_id+'/'+row.entry.key)),'A supported expansion binding was not exercised');
  for(const row of report.coverage_matrix){const explicit=EXPLICIT_FIELDS[row.key]||[];assert(explicit.every(suffix=>row.probes.some(probe=>probe.expected.path===row.key+'.'+suffix&&probe.expected.kind==='explicit')),'Explicit expansion geometry probe omitted: '+row.profile+'/'+row.key);}
  report.checks.push('exact target context and curated root sets render native sizes, alignment and source IDs','representative bitfields, unions, anonymous records and nonzero arrays match complete native results','explicit thread PAC fields, last saved register, packed IPv6 address tails and nested routes match native arithmetic');

  // Every new supported authored mapping is inspected; a real chapter link is followed per changed family.
  const supportedKeys=[...new Set(newSupportedRows.map(row=>row.entry.key))],chapterMappings=new Map();
  for(const key of supportedKeys)for(const chapter of catalog.selections.find(entry=>entry.key===key).chapters){
    const path=chapter.replace(/\.md(?=#|$)/,'.html');if(!chapterMappings.has(path))chapterMappings.set(path,[]);chapterMappings.get(path).push(key);
  }
  report.authored_mappings=[];report.authored_routes=[];const routedFamilies=new Set();
  for(const [chapter,keys]of chapterMappings){
    await navigate(chapter);await readerReady();
    for(const key of keys){
      const href=await evaluate(`(()=>{const a=[...document.querySelectorAll('a[href]')].find(a=>new URL(a.href).pathname.endsWith('/structures/layout-browser.html')&&new URL(a.href).searchParams.get('declaration')===${JSON.stringify(key)});return a?.href;})()`);
      assert(href,'Missing authored inspect link: '+chapter+'/'+key);localFile(href);report.authored_mappings.push({chapter,key,href});
    }
    const representative=keys.find(key=>!routedFamilies.has(survey.entries.find(entry=>entry.key===key).group));
    if(representative){
      await clickLink(`[...document.querySelectorAll('a[href]')].find(a=>new URL(a.href).pathname.endsWith('/structures/layout-browser.html')&&new URL(a.href).searchParams.get('declaration')===${JSON.stringify(representative)})`);
      const live=await waitUI(survey.entries.find(entry=>entry.key===representative).record);await assertNative(live,live.profile);
      assert(live.root_id===catalog.selections.find(entry=>entry.key===representative).declarations[live.profile],'Authored route resolved wrong source ID');
      routedFamilies.add(survey.entries.find(entry=>entry.key===representative).group);report.authored_routes.push({chapter,key:representative,...live});
    }
  }
  const expectedMappings=supportedKeys.flatMap(key=>catalog.selections.find(entry=>entry.key===key).chapters.map(chapter=>chapter.replace(/\.md(?=#|$)/,'.html')+'/'+key));
  assert(exactSet(expectedMappings,report.authored_mappings.map(row=>row.chapter+'/'+row.key)),'Authored mapping coverage incomplete');
  const expectedFamilies=[...new Set(newSupportedRows.map(row=>row.entry.group))];
  assert(exactSet(expectedFamilies,[...routedFamilies]),'A changed/new authored family was not actually followed');
  report.checks.push('all new supported authored chapter mappings point to exact declaration queries','actual chapter links resolve live source identities in every changed/new family');

  report.unavailable_queries=[];
  for(const key of ['thread_group','in6_ifaddr']){
    await navigate('structures/layout-browser.html?declaration='+encodeURIComponent(key));
    await waitFor(`!window.layoutExplorerCurrent&&!document.getElementById('explorer-error').hidden&&document.getElementById('explorer-error').textContent.trim()`,'Unavailable expansion query');
    const actual=await evaluate(`({error:document.getElementById('explorer-error').textContent,profile:document.getElementById('profile-select').value,offsets:document.querySelectorAll('#layout-tree [data-root-bits]').length,workers:window.layoutRuntimeClient.metrics.worker_starts})`);
    const cell=coverage.entries.find(entry=>entry.key===key).profiles[coverage.base_profiles.find(base=>actual.profile.startsWith(base+'--'))];
    assert(cell&&cell.status!=='supported'&&actual.offsets===0&&actual.workers===0&&actual.error.includes(key)&&(actual.error.includes(cell.reason)||cell.diagnostics.some(d=>actual.error.includes(d.message))),'Unavailable expansion root lost source diagnostics or published geometry');report.unavailable_queries.push({key,...actual});
  }
  report.checks.push('thread_group and in6_ifaddr queries report source-backed boundaries without compiler execution or editable geometry');

  await navigate('structures/layout-browser.html?declaration=ip6_hdr');
  const wire=await waitUI('ip6_hdr');await assertNative(wire,wire.profile);
  const tail=explicitProbe(wire.profile,'ip6_hdr.ip6_dst.__u6_addr.__u6_addr8[15]');
  report.bookmark_before=await observeProbe(tail);const savedHash=await evaluate('location.hash');assert(savedHash.startsWith('#layout='),'Nested IPv6 selection did not serialize');
  const reloadMarker=++navigationSequence;await evaluate(`window.__oldIntegrationDocument=${reloadMarker}`);await call('Page.reload',{ignoreCache:true},sessionId);
  await waitFor(`window.__oldIntegrationDocument!==${reloadMarker}&&document.readyState==='complete'`,'Fresh bookmark document');
  report.bookmark_restored=await waitUI('ip6_hdr',wire.profile);await assertNative(report.bookmark_restored,wire.profile);
  assert(report.bookmark_restored.selected?.path===tail.path&&report.bookmark_restored.selected.root_bits===tail.root_bits&&report.bookmark_restored.selected.local_bits===tail.local_bits&&await evaluate('location.hash')===savedHash,'Nested IPv6 bookmark lost path, array index, source context or offsets');
  report.bookmark_hash=savedHash;
  report.checks.push('nested union IPv6 byte index and exact source context survive document reload');
  await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1100,deviceScaleFactor:1,mobile:false},sessionId);
  report.screenshots={};
  for(const theme of ['light','dark']){
    await evaluate(`(()=>{if(document.documentElement.dataset.theme!==${JSON.stringify(theme)})document.getElementById('theme-toggle').click();if(document.documentElement.dataset.theme!==${JSON.stringify(theme)})throw Error('Integrated theme handlers conflict');})()`);
    const png=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},sessionId),path=reportPath.replace(/\.json$/,'')+'-ipv6-'+theme+'.png';await writeFile(path,Buffer.from(png.data,'base64'));report.screenshots[theme]=path;
  }
  await call('Emulation.setDeviceMetricsOverride',{width:390,height:1000,deviceScaleFactor:1,mobile:false},sessionId);
  report.narrow=await evaluate(`({width:innerWidth,scroll:document.documentElement.scrollWidth})`);assert(report.narrow.scroll<=report.narrow.width+1,'Expanded narrow page overflows horizontally');
  const narrow=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},sessionId);report.screenshots.narrow=reportPath.replace(/\.json$/,'')+'-ipv6-narrow.png';await writeFile(report.screenshots.narrow,Buffer.from(narrow.data,'base64'));
  report.checks.push('packed IPv6 nested selection captured in light, dark and narrow layouts');
  report.runtime_bounds=await evaluate(`({metrics:{...window.layoutRuntimeClient.metrics},cacheBudget:window.layoutRuntimeClient.assetBudget,worker:!!window.layoutRuntimeClient.worker,active:!!window.layoutRuntimeClient.active,compiler:window.layoutExplorerCurrent.metrics,limits:window.layoutRuntimeClient.limits,storage:['localStorage','sessionStorage','indexedDB'].map(name=>{try{window[name];return{name,blocked:false};}catch{return{name,blocked:true};}})})`);
  assert(!report.runtime_bounds.active&&report.runtime_bounds.metrics.asset_cache_bytes<=report.runtime_bounds.cacheBudget&&report.runtime_bounds.storage.every(s=>s.blocked)&&report.runtime_bounds.metrics.persistence==='disabled','Runtime cache/storage bounds violated');
  assert(!report.runtime_bounds.worker||report.runtime_bounds.compiler.linear_memory_bytes<=report.runtime_bounds.limits.max_linear_memory_bytes,'Worker retained beyond linear-memory bound');
  report.runtime_disposed=await evaluate(`(()=>{const c=window.layoutRuntimeClient;c.dispose();return{active:!!c.active,worker:!!c.worker,metrics:{...c.metrics}};})()`);
  assert(!report.runtime_disposed.active&&!report.runtime_disposed.worker&&report.runtime_disposed.metrics.worker_starts===report.runtime_disposed.metrics.worker_terminations,'Explicit test teardown retained compiler worker');
  report.checks.push('new contexts respect cache, worker memory and disabled storage bounds; explicit teardown terminates remaining worker');

  const sourceMarker=++navigationSequence;
  report.explorer_source=await evaluate(`(()=>{const a=document.getElementById('selected-source');if(!a||a.hidden)throw Error('IPv6 field lacks source mapping');window.__oldIntegrationDocument=${sourceMarker};const href=a.href;a.click();return href;})()`);localFile(report.explorer_source);
  await waitFor(`window.__oldIntegrationDocument!==${sourceMarker}||document.getElementById('source-dialog')?.open`,'IPv6 explorer source action');
  if(await evaluate(`!!document.getElementById('source-dialog')?.open`)){
    await waitFor(`!document.getElementById('source-code').hasAttribute('aria-busy')&&document.querySelectorAll('#source-code .source-line').length>0`,'IPv6 source popup');
    await clickLink(`document.getElementById('source-full-link')`);
  }
  report.explorer_full_source=await fullSource(report.explorer_source);
  assert(report.explorer_full_source.path==='xnu/bsd/netinet6/in6.h','IPv6 byte source action opened the wrong header');
  report.checks.push('new nested IPv6 field opens exact local full-file source with every line materialized');
  await sampleMemory();await Promise.all([...workerSetup]);
  report.remote_requests=requests.filter(r=>/^(?:https?|wss?|ftp):/i.test(r.url)&&!allowedRequest(r.url));
  assert(report.remote_requests.length===0,'Page or worker attempted remote traffic');
  for(const request of requests)if(/^(?:file|https?):/.test(request.url))localFile(request.url);
  report.expected_local_loading_failures=loadingFailures.filter(f=>expectedFailureURLs.has(f.url));
  report.unexpected_loading_failures=loadingFailures.filter(f=>!expectedFailureURLs.has(f.url));
  assert(report.unexpected_loading_failures.length===0,'An unexpected reader/compiler asset failed: '+JSON.stringify(report.unexpected_loading_failures));
  assert(exceptions.length===0,'Browser or worker exception: '+JSON.stringify(exceptions));
  assert((!baselineAudit||await fileHash(baselineBrowserPath)===baselineHashes.browser&&await fileHash(baselineNativePath)===baselineHashes.native&&await fileHash(join(baselineBook,'build-manifest.json'))===baselineHashes.build)&&await fileHash(new URL(import.meta.url))===harnessHash&&await fileHash(join(bookRoot,'build-manifest.json'))===manifestHash&&await fileHash(join(bookRoot,'layouts/manifest.json'))===layoutHash&&await fileHash(join(bookRoot,'layouts/coverage.json'))===coverageHash&&await fileHash(join(bookRoot,'layouts/catalog.json'))===catalogHash&&await fileHash(surveyURL)===surveyHash&&await fileHash(resolve(nativeReportArgument))===evidenceHash,'Book, layout, coverage, survey or native evidence changed during acceptance');
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
