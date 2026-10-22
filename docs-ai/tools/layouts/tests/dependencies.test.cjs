// SPDX-License-Identifier: GPL-2.0-only
const assert = require('node:assert/strict');
const fs = require('node:fs');
const C = require('../browser/contracts.js');
const D = require('../browser/dependencies.js');
(async () => {
  const {entries} = JSON.parse(fs.readFileSync(0, 'utf8'));
  for (const entry of entries) entry.document = await C.create(entry.request, entry.result);
  const analysis = await D.discover(entries, {space_id: 'synthetic-dependencies'});
  await C.registerDependencyAnalysis(analysis);
  for (const entry of entries) await C.validate(await D.attach(entry.document, analysis));
  let assertions = entries.length;
  const root = name => analysis.nodes.find(node => node.kind === 'declaration' && node.details.kind === 'record' && node.name === name).id;
  const control = (name, macro) => D.controlsFor(analysis, root(name)).find(control => control.macro === macro);
  for (const [record, macro] of [['Direct','DEFINED_FLAG'], ['Interacting','FLAG_A'], ['Interacting','FLAG_B'],
    ['Embedded','LEAF_EXTRA'], ['Embedded','COUNT'], ['Aliased','TYPE_WIDE'], ['Generated','MACRO_WIDE'],
    ['EnumBound','ENUM_EXTRA'], ['Packing','PACKED'], ['Alignment','ALIGNMENT'], ['Width','WIDTH'],
    ['DerivedBound','FIRST_GATE'], ['DerivedBound','SECOND_GATE'], ['DerivedBound','FALLBACK_GATE']]) {
    assert.equal(control(record, macro)?.classification, 'demonstrated', record + ':' + macro); ++assertions;
  }
  assert.equal(control('NoEffect', 'NOOP').classification, 'potential'); ++assertions;
  assert.ok(control('NoEffect', 'NOOP').observed_no_change.length); ++assertions;
  assert.equal(control('Inactive', 'NEVER_ENABLED').classification, 'potential'); ++assertions;
  assert.deepEqual(D.controlsFor(analysis, root('PointerOnly')), []); ++assertions;
  assert.deepEqual(D.controlsFor(analysis, root('Unrelated')), []); ++assertions;
  assert.ok(!analysis.controls.some(control => ['COMMENT_FLAG', 'STRING_FLAG', 'FUNCTION_ONLY', 'DEPENDENCY_SUPPORT_H'].includes(control.macro))); ++assertions;
  assert.equal(analysis.configurations.length, entries.length - 1); ++assertions;
  assert.equal(analysis.space.cases.length, entries.length); ++assertions;
  const base = entries.find(entry => entry.name === 'dep-base').document.configuration.id;
  const first = entries.find(entry => entry.name === 'dep-a').document.configuration.id;
  const both = entries.find(entry => entry.name === 'dep-ab').document.configuration.id;
  const interaction = analysis.comparisons.find(comparison => comparison.from === first && comparison.to === both);
  assert.equal(interaction.attribution, 'single-macro-intervention'); ++assertions;
  assert.ok(interaction.effects.find(effect => effect.declaration_id === root('Interacting')).components.includes('field-presence')); ++assertions;
  const alone = analysis.comparisons.find(comparison => comparison.from === base && comparison.to === first);
  assert.deepEqual(alone.effects.find(effect => effect.declaration_id === root('Interacting')).components, []); ++assertions;
  const rewrite = async mutate => {const copy = JSON.parse(JSON.stringify(analysis)); mutate(copy); delete copy.id; copy.id = 'dependency-analysis-v1:' + await C.sha256(C.canonical(copy)); return copy;};
  for (const mutate of [copy => copy.edges[0].to = 'missing', copy => copy.coverage.discovery = 'complete',
    copy => copy.sources[0].size_bytes = -1, copy => copy.controls[0].paths[0] = ['missing'],
    copy => copy.observations[0].value = 'fabricated', copy => copy.observations[0].macros = {},
    copy => copy.nodes.find(node => node.kind === 'macro').details.category = 'editable-feature',
    copy => copy.comparisons.find(comparison => comparison.changed_macros.length !== 1).attribution = 'single-macro-intervention']) {
    await assert.rejects(async () => D.validate(await rewrite(mutate))); ++assertions;
  }
  const scanned = D.scan('/* π */\r\n#if FIRST && \\\r\n SECOND\r\nstruct Root {int x;};\r\n#endif\r\n');
  assert.equal(scanned.branches[0].begin_bytes, Buffer.byteLength('/* π */\r\n')); ++assertions;
  assert.deepEqual(scanned.branches[0].identifiers, ['FIRST', 'SECOND']); ++assertions;
  assert.equal(D.scan('#ifndef G\n#define G\n#endif\n#if FLAG\nint x;\n#endif\n').branches[0].include_guard, false); ++assertions;
  assert.deepEqual(D.scan('#if __has_feature(ptrauth_calls) && __has_include("a.h") && FLAG\n#endif\n').branches[0].identifiers, ['FLAG']); ++assertions;
  for (const [expression, expected] of [['1+FLAG', ['FLAG']], ['2-OTHER', ['OTHER']], ['0xFFUL', []], ['201710L', []], ['1e+10+FLAG', ['FLAG']]]) {
    assert.deepEqual(D.scan('#if ' + expression + '\n#endif\n').branches[0].identifiers, expected); ++assertions;
  }
  process.stdout.write(JSON.stringify({status:'passed', cases:entries.length, assertions, configurations:analysis.configurations.length,
    nodes:analysis.nodes.length, edges:analysis.edges.length, controls:analysis.controls.length}) + '\n');
})().catch(error => {process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
