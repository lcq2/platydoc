// SPDX-License-Identifier: GPL-2.0-only
const fs = require('node:fs');
const assert = require('node:assert/strict');
const C = require('../browser/contracts.js');
(async () => {
  const evidence = JSON.parse(fs.readFileSync(0, 'utf8'));
  const clone = value => JSON.parse(JSON.stringify(value));
  const {request, result} = evidence.baseline;
  const policy = await C.createPolicy(request, result, {label: 'release-t8103--kernel'});
  const baseline = await C.create(request, result, {policy, profile: policy.label});
  let assertions = 1;
  for (const replacement of [null, '0', '', '(0)', '2']) {
    const resolved = C.resolveConfiguration(request, {__arm64e__: replacement}, policy, {whatIf: true});
    assert.equal(resolved.resolution.status, 'invalid-configuration');
    assert.match(resolved.resolution.issues.join('\n'), /Mandatory iOS PAC context/); assertions += 2;
  }
  assert.equal(C.resolveConfiguration(request, {CONFIG_PERVASIVE_CPI: '0'}, policy, {whatIf: true}).resolution.status, 'what-if');
  assert.equal(C.resolveConfiguration(request, {__arm64e__: '1'}, policy, {whatIf: true}).resolution.status, 'what-if'); assertions += 2;
  await assert.rejects(() => C.create(evidence.disabled.request, evidence.disabled.result, {policy, whatIf: true}), /Mandatory iOS PAC context/); ++assertions;
  // Rehash every affected reference: the cache/import guard must reject the PAC
  // state itself, rather than merely catching an unrelated checksum mismatch.
  for (const name of ['__arm64e__', 'PLATYDOC_PTRAUTH_CALLS', 'PLATYDOC_PTRAUTH_INTRINSICS', 'HAS_APPLE_PAC']) {
    const bad = clone(baseline), c = bad.configuration;
    c.effective.macros[name] = {state: 'undefined'};
    const binding = Object.fromEntries(['requested', 'submitted_request', 'inputs', 'effective', 'policy'].map(key => [key, c[key]]));
    c.id = 'config-v1:' + await C.sha256(C.canonical(binding));
    for (const [collection, prefix] of [[bad.declarations.variants, 'variant-v1'], [bad.layouts.entries, 'layout-v1']]) {
      for (const value of collection) {
        value.configuration_id = c.id;
        const {id, ...material} = value;
        value.id = prefix + ':' + await C.sha256(C.canonical(material));
      }
    }
    bad.dependencies.configuration_ids = [c.id];
    await assert.rejects(() => C.validate(bad), /Mandatory iOS PAC context/); ++assertions;
  }
  const narrowPolicy = await C.createPolicy(evidence.narrow.request, evidence.narrow.result, {label: 'release-t8103--security'});
  assert.equal((await C.create(evidence.narrow.request, evidence.narrow.result, {policy: narrowPolicy, profile: narrowPolicy.label})).layouts.status, 'success'); ++assertions;
  assert.equal((await C.create(evidence.generic.request, evidence.generic.result)).layouts.status, 'success'); ++assertions;
  process.stdout.write(JSON.stringify({status: 'passed', assertions}) + '\n');
})().catch(error => {process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
