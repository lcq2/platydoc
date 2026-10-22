// SPDX-License-Identifier: GPL-2.0-only
const fs = require('node:fs');
const assert = require('node:assert/strict');
const C = require('../browser/contracts.js');
(async () => {
  const evidence = JSON.parse(fs.readFileSync(0, 'utf8')), documents = [], byName = new Map();
  const source = {release: 'xnu-12377.121.6', revision: 'ac9718fb1af618d5ce8678d0dc6e8a58f252216f'};
  let checks = 0;
  async function reject(action, text) {await assert.rejects(action, text); ++checks;}
  const clone = value => JSON.parse(JSON.stringify(value));
  const field = (d, name) => d.declarations.entries.find(x => x.kind === 'field' && x.name === name);
  const record = (d, name) => d.declarations.entries.find(x => x.kind === 'struct' && x.name === name);
  const stamp = async (object, prefix) => {const {id, ...material} = object; object.id = prefix + ':' + await C.sha256(C.canonical(material));};
  for (const entry of evidence) {
    const supported = /^(release|development)-/.test(entry.name);
    const metadata = supported ? {source, profile: entry.name, policy: await C.createPolicy(entry.request, entry.result, {label: entry.name})} : {};
    const document = await C.create(entry.request, entry.result, metadata);
    assert.equal(C.canonical(document), C.canonical(await C.validate(clone(document))));
    documents.push(document); byName.set(entry.name, document); ++checks;
  }
  const narrow = byName.get('narrow-undefined'), zero = byName.get('narrow-zero'), wide = byName.get('wide-one');
  assert.equal(record(narrow, 'Node').id, record(wide, 'Node').id);
  for (const name of ['fixed', 'stable', 'next']) assert.equal(field(narrow, name).id, field(wide, name).id);
  for (const name of ['Value', 'Alias', 'NodeRef']) {
    const alias = d => d.declarations.entries.find(x => x.kind === 'alias' && x.name === name);
    assert.equal(alias(narrow).id, alias(wide).id);
    assert.notEqual(narrow.declarations.variants.find(v => v.declaration_id === alias(narrow).id).id,
      wide.declarations.variants.find(v => v.declaration_id === alias(wide).id).id);
  }
  assert.deepEqual(narrow.configuration.requested.macros.FLAG, {state: 'undefined'});
  assert.deepEqual(zero.configuration.requested.macros.FLAG, {state: 'defined', replacement: '0'});
  assert.notEqual(narrow.configuration.id, zero.configuration.id); checks += 8;
  const presence = C.mergePresence([narrow, zero, wide, byName.get('syntax-error')]);
  const conditional = presence.find(x => x.declaration_id === field(wide, 'conditional').id);
  assert.equal(conditional.configurations[narrow.configuration.id], 'absent');
  assert.equal(conditional.configurations[wide.configuration.id], 'present');
  assert.equal(conditional.configurations[byName.get('syntax-error').configuration.id], 'unknown');
  const conflict = clone(wide); field(conflict, 'stable').name = 'forged';
  assert.throws(() => C.mergePresence([narrow, conflict]), /conflicting/); checks += 4;
  const d = byName.get('undefined'), root = record(d, 'Outer');
  assert.equal(C.resolvePath(d, root.id, ['rows', {index: 1}, {index: 2}, 'value']).root_offset_bits, 176);
  assert.equal(C.resolvePath(d, root.id, ['payload', 'wide']).root_offset_bits, 256);
  assert.equal(C.resolvePath(d, root.id, ['opaque']).pointer_boundary, true);
  assert.throws(() => C.resolvePath(d, root.id, ['opaque', 'value']), /pointer boundary/);
  assert.throws(() => C.resolvePath(d, root.id, ['rows', {index: 2}]), /out of bounds/);
  const flexible = record(d, 'Flexible');
  assert.throws(() => C.resolvePath(d, flexible.id, ['bytes', {index: 3}]), /runtime length/);
  assert.equal(C.resolvePath(d, flexible.id, ['bytes', {index: 3}], {runtimeLengths: {[d.declarations.entries.find(x => x.kind === 'field' && x.owner_id === flexible.id && x.name === 'bytes').id]: 4}}).root_offset_bits, 56);
  assert.equal(C.resolvePath(d, flexible.id, ['bytes', {index: 100}], {allowFlexiblePreview: true}).bounds, 'runtime-unchecked-preview');
  assert.equal(C.resolvePath(d, record(d, 'Bits').id, ['high']).root_offset_bits, 5); checks += 9;
  for (const name of ['token-paste', 'command-line-origin', 'implicit-alias', 'ambiguous-selection']) {
    assert.equal(byName.get(name).layouts.status, 'unsupported'); assert.equal(byName.get(name).declarations.entries.length, 0); ++checks;
  }
  assert.equal(byName.get('scoped-records').layouts.entries.length, 2);
  const included0 = byName.get('macro-include-0'), included1 = byName.get('macro-include-1');
  assert.equal(record(included0, 'Root').id, record(included1, 'Root').id);
  const anonymous = doc => doc.declarations.entries.find(x => x.kind === 'struct' && x.name === '');
  assert.notEqual(anonymous(included0).id, anonymous(included1).id);
  assert.notEqual(field(included0, 'x').id, field(included1, 'x').id); checks += 3;
  assert.equal(new Set(byName.get('repeated-include').layouts.entries.map(x => x.declaration_id)).size, 3); checks += 2;
  const entry = evidence.find(x => x.name === 'narrow-undefined');
  const policy = await C.createPolicy(entry.request, entry.result, {label: 'baseline', editable: ['FLAG'], constraints: [{name: 'FLAG', values: [{state: 'undefined'}, {state: 'defined', replacement: '0'}]}]});
  assert.equal(C.resolveConfiguration(entry.request, {FLAG: '1'}, policy).resolution.status, 'invalid-configuration');
  assert.equal(C.resolveConfiguration(entry.request, {TYPE_VALUE: '1LL'}, policy).resolution.status, 'invalid-configuration');
  assert.equal(C.resolveConfiguration(entry.request, {TYPE_VALUE: '1LL'}, policy, {whatIf: true}).resolution.status, 'what-if');
  assert.equal(C.resolveConfiguration(entry.request, {__ARM_FEATURE_AES: '1'}, policy).resolution.status, 'invalid-configuration');
  assert.equal(C.resolveConfiguration(entry.request, {__ARM_FEATURE_AES: '1'}, policy, {whatIf: true}).resolution.status, 'what-if'); checks += 5;
  await reject(() => C.create(entry.request, entry.result, {profile: 'untrusted-label'}), /explicit baseline policy/);
  const invalidPolicy = await C.createPolicy(entry.request, entry.result, {label: 'bad', editable: ['FLAG'], constraints: [{name: 'FLAG', values: [{state: 'defined', replacement: '0'}]}]});
  await reject(() => C.create(entry.request, entry.result, {profile: 'bad', policy: invalidPolicy}), /baseline violates constraint/);
  const badShape = clone(policy); badShape.baseline.requested = false; await stamp(badShape, 'policy-v1');
  await reject(() => C.create(entry.request, entry.result, {policy: badShape}), /object|context|request/);
  for (const key of ['ptrauth_intrinsics', 'ptrauth_calls']) {
    const malformedPolicy = clone(policy); malformedPolicy.baseline.requested[key] = '1'; await stamp(malformedPolicy, 'policy-v1');
    await reject(() => C.create(entry.request, entry.result, {policy: malformedPolicy}), /boolean/);
  }
  for (const mutate of [
    x => {x.extra = 1;},
    x => {x.declarations.entries.push(clone(x.declarations.entries[0]));},
    x => {x.layouts.entries[0].fields[0].declaration_id = 'missing';},
    x => {x.layouts.units.offset = 'bytes';},
    x => {x.layouts.entries[0].size_bytes = Number.MAX_SAFE_INTEGER + 1;},
    x => {x.layouts.entries[0].size_bytes = 1.5;},
    x => {x.layouts.entries[0].fields[0].offset_bits = -1;},
    x => {x.layouts.status = 'unknown';},
    x => {x.layouts.status = 'incomplete-type';},
  ]) {const malformed = clone(d); mutate(malformed); await reject(() => C.validate(malformed));}
  const arithmetic = clone(d), outer = arithmetic.layouts.entries.find(x => x.declaration_id === root.id);
  const rows = outer.fields.find(x => x.declaration_id === field(d, 'rows').id);
  rows.type.element.element.size_bits = 24; rows.type.element.size_bits = 72; rows.type.size_bits = 144;
  await stamp(outer, 'layout-v1'); await reject(() => C.validate(arithmetic), /dimensions|stride/);
  const dependency = clone(narrow), target = field(narrow, 'stable');
  const relation = {from: {kind: 'macro', name: 'FLAG'}, to: target.id, kind: 'potential-layout',
    evidence: [{source: target.source, configurations: [narrow.configuration.id], description: 'Manual schema fixture; no discovery claim.'}]};
  relation.id = 'dependency-v1:' + await C.sha256(C.canonical(relation));
  dependency.dependencies = {...dependency.dependencies, status: 'partial', coverage: 'partial', relations: [relation]};
  await C.validate(dependency); ++checks;
  const ambiguousCoverage = clone(dependency); ambiguousCoverage.dependencies.coverage = 'declared-complete';
  await reject(() => C.validate(ambiguousCoverage), /coverage mismatch/);
  const badDependency = clone(dependency); badDependency.dependencies.relations[0].to = 'missing';
  await stamp(badDependency.dependencies.relations[0], 'dependency-v1'); await reject(() => C.validate(badDependency), /dangling/);
  // Historical two-root fixtures remain a regression after the authored catalog expands.
  const mapping = JSON.parse(fs.readFileSync(require('node:path').resolve(__dirname, '../../../structures/layouts.json'), 'utf8'));
  mapping.entries = mapping.entries.filter(entry => ['task', 'recount_track'].includes(entry.display_name));
  for (const name of ['release-t8103', 'release-vmapple', 'development-t8103', 'development-vmapple']) {
    assert.equal(C.mapChapters(byName.get(name), mapping, {requireAll: true}).entries.length, 2); ++checks;
  }
  assert.throws(() => C.canonical([undefined])); assert.throws(() => C.canonical(Array(2))); assert.throws(() => C.canonical({x: NaN})); checks += 3;
  process.stdout.write(C.canonical({contract: 'platydoc.contract-verification', version: 1, cases: evidence.map(x => x.name), assertions: checks, documents}) + '\n');
})().catch(error => {process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
