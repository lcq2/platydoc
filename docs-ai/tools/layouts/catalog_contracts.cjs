// SPDX-License-Identifier: GPL-2.0-only
// Bounded JSON bridge for handbook generation and independent cache validation.
const fs = require('node:fs');
const C = require('./browser/contracts.js');
(async () => {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  const documents = [], bindings = [];
  for (const entry of input.entries) {
    const policy = await C.createPolicy(entry.request, entry.result, {label: entry.profile});
    const document = await C.create(entry.request, entry.result, {source: input.source, policy, profile: entry.profile});
    if (entry.document) {
      await C.validate(entry.document);
      if (C.canonical(document) !== C.canonical(entry.document)) throw Error('Cached contract differs from its complete request/result');
    }
    documents.push(document);
    bindings.push(C.mapChapters(document, input.mapping, {requireAll: !input.partial}));
  }
  process.stdout.write(C.canonical({documents, bindings}) + '\n');
})().catch(error => {process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
