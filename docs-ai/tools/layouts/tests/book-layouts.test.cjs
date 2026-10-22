// SPDX-License-Identifier: GPL-2.0-only
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const test = require('node:test');
function setup() {
  const scripts = [], original = [];
  const context = {window: null, Map, Set, Error,
    layoutExplorerConfig: {integrated: true, assetRoot: '../layouts/'},
    LayoutRuntimeAssets: {deliver(...args) {original.push(args);}},
    document: {createElement() {return {remove() {this.removed = true;}};}, head: {append(script) {scripts.push(script);}}}};
  context.window = context;
  vm.runInNewContext(fs.readFileSync(require.resolve('../browser/book-layouts.js'), 'utf8'), context);
  return {context, scripts, original, load: context.layoutRuntimeOptions.loadEnvelope};
}
test('nested book assets resolve locally; simultaneous same-ID delivery survives one cancellation', async () => {
  const {context, scripts, load, original} = setup(), asset = {id: 'profile-a', url: 'assets/profile-a.js'};
  const old = new AbortController(), current = new AbortController();
  const rejected = load(asset, old.signal).then(() => {throw Error('Cancelled load resolved');}, error => error.message);
  const pending = load(asset, current.signal);
  old.abort();
  assert.match(await rejected, /cancelled/);
  assert.equal(scripts[0].removed, true);
  assert.equal(scripts[1].src, '../layouts/assets/profile-a.js');
  const envelope = {schema: 2, encoding: 'gzip-base64', data: 'verified later by LayoutCodec'};
  context.LayoutRuntimeAssets.deliver(asset.id, envelope);
  scripts[1].onload();
  assert.equal(await pending, envelope);
  assert.equal(scripts[1].removed, true);
  assert.equal(scripts[1].onload, null);
  assert.equal(original.length, 1, 'Existing runtime subscribers must still receive deliveries');
});
test('missing delivery/load error abort cleanly and later retry recovers', async () => {
  const {context, scripts, load} = setup(), asset = {id: 'a', url: 'assets/a.js'};
  let promise = load(asset, new AbortController().signal);
  scripts[0].onload();
  await assert.rejects(promise, /did not register/);
  promise = load(asset, new AbortController().signal);
  scripts[1].onerror();
  await assert.rejects(promise, /Cannot load/);
  promise = load(asset, new AbortController().signal);
  context.LayoutRuntimeAssets.deliver('a', {ok: true});scripts[2].onload();
  assert.equal((await promise).ok, true);
});
