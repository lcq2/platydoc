// SPDX-License-Identifier: GPL-2.0-only
// JSON stdin/stdout bridge; no downloads, filesystem inputs are explicit CLI paths.
const fs = require('node:fs');
const Contracts = require('../browser/contracts.js');
const Dependencies = require('../browser/dependencies.js');
(async () => {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  if (input.analysis) await Contracts.registerDependencyAnalysis(input.analysis);
  if (['create', 'discover'].includes(input.command)) {
    const documents = [];
    const policies = new Map();
    for (const entry of input.entries) {
      const metadata = {...(entry.metadata || {})};
      if (metadata.profile && !metadata.policy) {metadata.policy = await Contracts.createPolicy(entry.request, entry.result, {label: metadata.profile}); policies.set(metadata.profile, metadata.policy);}
      if (metadata.base_profile) {metadata.policy = policies.get(metadata.base_profile); if (!metadata.policy) throw new Error('Baseline policy must precede probe'); delete metadata.base_profile;}
      documents.push(await Contracts.create(entry.request, entry.result, metadata));
    }
    if (input.command === 'discover') {
      const analysis = await Dependencies.discover(input.entries.map((entry, index) => ({...entry, document: documents[index]})), {space_id: input.space_id});
      await Contracts.registerDependencyAnalysis(analysis);
      const attached = []; for (const document of documents) attached.push(await Dependencies.attach(document, analysis));
      process.stdout.write(Contracts.canonical({analysis, documents: attached}) + '\n');
    } else process.stdout.write(Contracts.canonical(documents) + '\n');
  } else if (input.command === 'map') {
    const bindings = [];
    for (const document of input.documents) {await Contracts.validate(document); bindings.push(Contracts.mapChapters(document, input.mapping, {requireAll: true}));}
    process.stdout.write(Contracts.canonical(bindings) + '\n');
  } else if (input.command === 'validate') {
    for (const document of input.documents) await Contracts.validate(document);
    process.stdout.write(Contracts.canonical(input.documents) + '\n');
  } else throw new Error('Unsupported contract bridge command');
})().catch(error => {process.stderr.write(error.stack + '\n'); process.exitCode = 1;});
