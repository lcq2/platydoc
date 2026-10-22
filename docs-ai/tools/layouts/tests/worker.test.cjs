// SPDX-License-Identifier: GPL-2.0-only
// Real contract/dependency code with a deterministic native-evidence compiler adapter.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const C = require('../browser/contracts.js');
const D = require('../browser/dependencies.js');
(async () => {
  const input=JSON.parse(fs.readFileSync(0,'utf8')), base=input.entries.find(entry=>entry.name==='dep-base'), leaf=input.entries.find(entry=>entry.name==='dep-leaf');
  let allocations=0, calls=0, source='', response='';
  const engine={HEAPU8:new Uint8Array(1024),_malloc:()=>{++allocations;return 1;},_free:()=>{--allocations;},lengthBytesUTF8:text=>Buffer.byteLength(text),
    stringToUTF8:text=>{source=text;},_layout_analyze:()=>{++calls;++allocations;const request=JSON.parse(source);response=JSON.stringify(request.macros.LEAF_EXTRA==='1'?leaf.result:base.result);return 2;},UTF8ToString:()=>response,_layout_free:()=>{--allocations;}};
  const messages=[],self={LayoutContracts:C,LayoutDependencies:D,postMessage:message=>messages.push(message)};
  const context=vm.createContext({self,TextDecoder,TextEncoder,Uint8Array,crypto:require('node:crypto').webcrypto,createLayoutEngine:async()=>engine});
  const realm=value=>vm.runInContext('JSON.parse('+JSON.stringify(JSON.stringify(value))+')',context);
  for(const name of ['contracts','dependencies'])vm.runInContext(fs.readFileSync(require.resolve('../browser/'+name+'.js'),'utf8'),context);
  self.LayoutContracts=context.LayoutContracts;self.LayoutDependencies=context.LayoutDependencies;
  vm.runInContext(fs.readFileSync(require.resolve('../browser/layout-worker.js'),'utf8'),context);
  const compiler=base.result.compiler;
  await self.onmessage({data:{type:'init',generation:7,wasm:new ArrayBuffer(1),compiler:realm(compiler),assets:realm({wasm:'test'}),limits:realm({cache_entries:3,cache_bytes:8*1024*1024,max_linear_memory_bytes:2048})}});
  assert.equal(messages.pop().type,'ready');
  let sequence=0;
  const run=async(profile,overrides={},request=base.request,source={release:'test',revision:'a'.repeat(40)})=>{
    const payload=new TextEncoder().encode(JSON.stringify({request,source}));
    const identity={runtime_version:1,compiler,assets:{wasm:'test'}};
    const computation_sha256=await C.sha256(C.canonical({identity,profile,source,profile_sha256:await C.sha256(new TextDecoder().decode(payload)),overrides,dependencies:true}));
    await self.onmessage({data:{type:'analyze',generation:7,id:++sequence,profile,profile_bytes:payload.buffer,source:realm(source),overrides:realm(overrides),dependencies:true,computation_sha256}});
    const message=messages.pop();if(message.type==='error')throw Error(message.message);await C.validate(JSON.parse(JSON.stringify(message.value.contract)),{analysis:JSON.parse(JSON.stringify(message.value.analysis))});return message.value;
  };
  let assertions=1;
  const first=await run('profile-a');assert.equal(calls,1);++assertions;
  assert.equal(allocations,0);++assertions;
  const second=await run('profile-a');assert.equal(calls,1);assert.equal(second.metrics.cache_hit,true);assertions+=2;
  const manual=await run('profile-a',{LEAF_EXTRA:'1'});assert.equal(calls,2);++assertions;
  assert.equal(manual.contract.configuration.classification,'what-if');++assertions;
  assert.ok(!Object.hasOwn(manual.result,'dependency_trace'));++assertions;
  const baseline={...base.request,macros:{...base.request.macros,NOOP:'1'}};
  const other=await run('profile-b',{LEAF_EXTRA:'1'},baseline);
  assert.ok(calls>=4);++assertions;
  assert.notEqual(other.analysis.id,manual.analysis.id);++assertions;
  assert.notEqual(other.contract.configuration.policy.id,manual.contract.configuration.policy.id);++assertions;
  assert.ok(other.metrics.cache_entries<=3);++assertions;
  assert.ok(other.metrics.cache_serialized_bytes<=8*1024*1024);++assertions;
  assert.equal(allocations,0);++assertions;
  process.stdout.write(JSON.stringify({status:'passed',assertions,compiler_calls:calls})+'\n');
})().catch(error=>{process.stderr.write(error.stack+'\n');process.exitCode=1;});
