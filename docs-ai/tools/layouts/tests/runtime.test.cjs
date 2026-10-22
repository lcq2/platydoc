// SPDX-License-Identifier: GPL-2.0-only
const assert = require('node:assert/strict');
const zlib = require('node:zlib');
const Codec = require('../browser/layout-codec.js');
const Runtime = require('../browser/layout-runtime.js');
const delay = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
(async () => {
  let assertions = 0;
  const raw = Buffer.from('π\r\n' + 'local offline data '.repeat(100));
  const envelope = bytes => ({schema:2, encoding:'gzip-base64', data:zlib.gzipSync(bytes).toString('base64')});
  const expected = {bytes:raw.length, sha256:await Codec.sha256(raw)};
  for (const fallback of [false, true]) {assert.deepEqual(Buffer.from(await Codec.decode(envelope(raw), expected, {fallback})), raw); ++assertions;}
  await assert.rejects(Codec.decode(envelope(raw), {...expected, sha256:'0'.repeat(64)})); ++assertions;
  await assert.rejects(Codec.decode(envelope(raw), {...expected, bytes:1}, {fallback:true})); ++assertions;
  const broken = zlib.gzipSync(raw); broken[broken.length-8] ^= 1;
  for (const fallback of [false,true]) {await assert.rejects(Codec.decode({schema:2,encoding:'gzip-base64',data:broken.toString('base64')}, expected, {fallback})); ++assertions;}
  const controller = new AbortController(); controller.abort();
  await assert.rejects(Codec.decode(envelope(raw), expected, {signal:controller.signal})); ++assertions;
  const assets = {}, payloads = new Map();
  for (const name of ['factory','contracts','dependencies','worker','wasm','profile-a','profile-b']) {
    const bytes = Buffer.from(name); assets[name] = {id:name,url:'assets/'+name+'.js',bytes:bytes.length,sha256:await Codec.sha256(bytes)}; payloads.set(name,envelope(bytes));
  }
  const manifest = {contract:'platydoc.layout-runtime-manifest',version:1,compiler:{revision:'a'.repeat(40),engine_sha256:'b'.repeat(64),wasm_sha256:assets.wasm.sha256,factory_sha256:assets.factory.sha256},
    assets:Object.fromEntries(['factory','contracts','dependencies','worker','wasm'].map(name=>[name,assets[name]])),
    profiles:['a','b'].map(id=>({id,source:{release:'test',revision:'c'.repeat(40)},asset:assets['profile-'+id]}))};
  const workers = [];
  class FakeWorker {
    constructor() {this.terminated=false;this.messages=[];workers.push(this);}
    postMessage(message) {this.messages.push(message); if(message.type==='init') setTimeout(()=>this.onmessage?.({data:{type:'ready',generation:message.generation}}),0);}
    terminate() {this.terminated=true;}
    emit(message) {this.onmessage?.({data:message});}
  }
  const options = {loadEnvelope:async asset=>payloads.get(asset.id),createWorker:()=>new FakeWorker(),validateReply:async value=>{if(value.bad)throw Error('bad contract');},timeout_ms:500,startup_timeout_ms:500};
  const client = new Runtime.Client(manifest, options);
  const waitJob = async (worker, id = client.sequence) => {for(let n=0;n<100;n++){const job=worker?.messages.findLast(message=>message.type==='analyze');if(job && job.id===id && !worker.terminated)return job;await delay(2);worker=workers.at(-1);}throw Error('No job');};
  const complete = (worker,job,extra={}) => worker.emit({type:'result',generation:job.generation,id:job.id,value:{id:job.id,generation:job.generation,profile:job.profile,computation_sha256:job.computation_sha256,result:{status:'ok',records:[],diagnostics:[]},contract:{},metrics:{analyses:1,cache_hits:0,cache_entries:0,cache_serialized_bytes:0,peak_linear_memory_bytes:1,linear_memory_bytes:1,cache_hit:false,retire_worker:false,persistence:'disabled',...extra.metrics},...Object.fromEntries(Object.entries(extra).filter(([key])=>key!=='metrics'))}});
  const first = client.analyze('a'); const firstJob = await waitJob(); const old = workers.at(-1), late = old.onmessage;
  const second = client.analyze('b'); await assert.rejects(first,{code:'superseded'}); ++assertions;
  const secondJob = await waitJob(); const current = workers.at(-1);
  assert.ok(old.terminated); ++assertions;
  late({data:{type:'result',generation:firstJob.generation,id:firstJob.id,value:{}}});
  complete(current,secondJob); const value = await second; assert.equal(value.profile,'b'); ++assertions;
  assert.ok(client.metrics.stale_messages); ++assertions;
  const third = client.analyze('b'); const thirdJob = await waitJob(current); complete(current,thirdJob,{metrics:{cache_hit:true,retire_worker:false}}); await third;
  assert.equal(workers.at(-1),current); ++assertions;
  assert.equal(client.metrics.cache_hits,1); ++assertions;
  const cancel = client.analyze('a'); await delay(1); client.cancel(); await assert.rejects(cancel,{code:'cancelled'}); ++assertions;
  const timeout = client.analyze('a',{timeout_ms:10}); await assert.rejects(timeout,{code:'timeout'}); ++assertions;
  const recovery = client.analyze('a'); const recoveryJob = await waitJob(); complete(workers.at(-1),recoveryJob,{metrics:{cache_hit:false,retire_worker:true,linear_memory_bytes:300*1024*1024,peak_linear_memory_bytes:300*1024*1024}}); await recovery;
  assert.equal(client.worker,null); ++assertions;
  const malformed = client.analyze('a'); const malformedJob = await waitJob(); complete(workers.at(-1),malformedJob,{bad:true}); await assert.rejects(malformed,{code:'worker-message-error'}); ++assertions;
  const snapshot={TEST:'1'}; const snap=client.analyze('a',{overrides:snapshot}); snapshot.TEST='0'; const snapJob=await waitJob();
  assert.equal(snapJob.overrides.TEST,'1'); ++assertions; complete(workers.at(-1),snapJob); await snap;
  const mismatch=client.analyze('a'); const mismatchJob=await waitJob(); complete(workers.at(-1),mismatchJob,{computation_sha256:'0'.repeat(64)});
  await assert.rejects(mismatch,{code:'worker-message-error'}); ++assertions;
  const valid=client.analyze('a');const validJob=await waitJob();const retiring=workers.at(-1),retiredCallback=retiring.onmessage;
  complete(retiring,validJob,{metrics:{cache_hit:false,retire_worker:true,linear_memory_bytes:300*1024*1024,peak_linear_memory_bytes:300*1024*1024}});await valid;
  const replacement=client.analyze('b');const replacementJob=await waitJob();retiredCallback({data:{type:'startup-error',generation:replacementJob.generation,message:'late'}});
  complete(workers.at(-1),replacementJob);await replacement;assert.ok(!workers.at(-1).terminated);++assertions;
  client.dispose(); await assert.rejects(client.analyze('a'),{code:'disposed'}); ++assertions;
  assert.equal(client.metrics.asset_cache_bytes,0); ++assertions;
  // Late async loader completion cannot create a worker or settle a newer request.
  let release;
  const delayed = new Runtime.Client(manifest,{...options,loadEnvelope:asset=>asset.id==='profile-a'?new Promise(resolve=>{release=()=>resolve(payloads.get(asset.id));}):Promise.resolve(payloads.get(asset.id))});
  const loading=delayed.analyze('a'); delayed.cancel(); await assert.rejects(loading,{code:'cancelled'}); ++assertions;
  const next=delayed.analyze('b'); const nextJob=await waitJob(undefined,delayed.sequence);complete(workers.at(-1),nextJob);await next;release();await delay(10);
  assert.equal(delayed.metrics.worker_starts,1); ++assertions; delayed.dispose();
  for (const budget of [Infinity,NaN,-1,1.5]) {assert.throws(()=>new Runtime.Client(manifest,{asset_cache_bytes:budget}),{code:'options-error'});++assertions;}
  const failure=new Runtime.Client(manifest,{...options,createWorker:()=>{const worker=new FakeWorker();worker.postMessage=()=>{throw Error('post failed');};return worker;}});
  await assert.rejects(failure.analyze('a'),{code:'asset-error'});++assertions;await delay(0);failure.dispose();
  const hung=new Runtime.Client(manifest,{...options,startup_timeout_ms:10,createWorker:()=>{const worker=new FakeWorker();worker.postMessage=()=>{};return worker;}});
  await assert.rejects(hung.analyze('a'),{code:'startup-timeout'});++assertions;hung.dispose();
  // Local classic-script registration supports overlapping clients and old cancellation cleanup.
  const scripts=[];global.document={createElement:()=>({remove(){this.removed=true;}}),head:{append(script){scripts.push(script);}}};
  const localOptions={...options,loadEnvelope:undefined};
  const localA=new Runtime.Client(manifest,localOptions),localB=new Runtime.Client(manifest,localOptions);
  const pendingA=localA.analyze('a'),pendingB=localB.analyze('a');localA.cancel();await assert.rejects(pendingA,{code:'cancelled'});++assertions;
  for(let turn=0;turn<100 && !workers.at(-1)?.messages.some(message=>message.type==='analyze' && message.computation_sha256===localB.active?.computation_sha256);turn++) {
    for(const script of scripts.filter(script=>!script.served)){script.served=true;const asset=Object.values(assets).find(asset=>asset.url===script.src);global.LayoutRuntimeAssets.deliver(asset.id,payloads.get(asset.id));script.onload?.();}
    await delay(2);
  }
  const localJob=await waitJob(undefined,localB.sequence);complete(workers.at(-1),localJob);await pendingB;
  assert.ok(scripts.every(script=>script.removed));++assertions;localA.dispose();localB.dispose();delete global.document;
  process.stdout.write(JSON.stringify({status:'passed',assertions})+'\n');
})().catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=1;});
