// SPDX-License-Identifier: GPL-2.0-only
// Standalone real-header proof and compact C-style layout browser.
(async () => {
  const status = document.getElementById('status');
  const metrics = {user_agent: navigator.userAgent, protocol: location.protocol,
    startup_ms: null, parse_ms: [], peak_linear_memory_bytes: 0, parity: 'running'};
  const hex = value => '0x' + value.toString(16);
  const canonical = value => Array.isArray(value) ? value.map(canonical) :
    value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])])) : value;
  const equal = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
  function node(tag, text, parent) {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (parent) parent.append(element);
    return element;
  }
  function table(parent, title, headings, rows) {
    const t = node('table', undefined, parent);
    node('caption', title, t);
    const head = node('tr', undefined, node('thead', undefined, t));
    headings.forEach(text => node('th', text, head));
    const body = node('tbody', undefined, t);
    for (const row of rows) {
      const tr = node('tr', undefined, body);
      row.forEach(text => node('td', String(text), tr));
    }
  }
  function analyze(engine, request) {
    const source = JSON.stringify(request);
    const ptr = engine._malloc(engine.lengthBytesUTF8(source) + 1);
    if (!ptr) throw new Error('input allocation failed');
    let response = 0;
    try {
      engine.stringToUTF8(source, ptr, engine.lengthBytesUTF8(source) + 1);
      response = engine._layout_analyze(ptr);
      if (!response) throw new Error('analysis allocation failed');
      return JSON.parse(engine.UTF8ToString(response));
    } finally {
      if (response) engine._layout_free(response);
      engine._free(ptr);
      metrics.peak_linear_memory_bytes = Math.max(metrics.peak_linear_memory_bytes, engine.HEAPU8.buffer.byteLength);
    }
  }
  function show(name, request, result) {
    const supported = /^(release|development)-/.test(name);
    const section = node('section', undefined, document.getElementById('results'));
    node('h2', name, section);
    node('p', supported ? 'Supported analysis profile; native comparison passed.' :
      'Diagnostic or what-if test, outside the four supported profiles. Native comparison passed.', section);
    if (name === 'probe-header-redefinition')
      node('p', 'Requested DEBUG=1; the generated debug.h redefines it to 0. The effective value and warning appear below.', section);
    if (name === 'probe-defined-zero-task-suspend')
      node('p', 'CONFIG_TASK_SUSPEND_STATS=0 still adds fields: task.h tests whether the macro is defined with #ifdef.', section);
    const records = Object.fromEntries(result.records.map(record => [record.name, record]));
    if (supported) {
      const tr = node('tr', undefined, document.getElementById('summary'));
      [name, hex(records.recount_track.size_bytes), hex(records.task.size_bytes), hex(records.task.alignment_bytes), 'Passed']
        .forEach(value => node('td', String(value), tr));
    }
    for (const name of ['recount_track', 'task']) {
      const record = records[name];
      if (!record) continue;
      const details = node('details', undefined, section);
      node('summary', `${name}: ${hex(record.size_bytes)} bytes, alignment ${hex(record.alignment_bytes)}`, details);
      const wanted = new Set(['rt_pad', 'rt_sync', 'rt_usage', 'lock', 'ref_count', 'active', 'task_uniqueid',
        'suspend_count', 'ref_group', 'ref_group_lock', 't_suspend_stats', 't_suspend_sources', 'user_stop_count']);
      table(details, 'Selected immediate fields', ['Field', 'Offset in bytes', 'Offset in bits'],
        record.fields.filter(field => wanted.has(field.name)).map(field => [field.name, hex(field.offset_bits / 8), hex(field.offset_bits)]));
    }
    if (result.effective_macros) {
      const keys = ['CONFIG_PERVASIVE_CPI', 'CONFIG_PERVASIVE_ENERGY', 'CONFIG_TASK_SUSPEND_STATS', 'DEVELOPMENT', 'DEBUG', 'RECOUNT_SECURE_METRICS'];
      const details = node('details', undefined, section);
      node('summary', 'Effective configuration', details);
      table(details, 'Final macro definitions after preprocessing', ['Macro', 'Value'], keys.map(key =>
        [key, result.effective_macros[key]?.replacement ?? 'undefined']));
    }
    for (const diagnostic of result.diagnostics)
      node('pre', `${diagnostic.severity}: ${diagnostic.message}`, section);
    if (result.status !== 'ok') node('p', `Result: ${result.status}. No layout is published.`, section);
    const details = node('details', undefined, section);
    node('summary', 'Complete compiler result', details);
    let materialized = false;
    details.addEventListener('toggle', () => {
      if (details.open && !materialized) {node('pre', JSON.stringify(result, null, 2), details); materialized = true;}
    });
  }
  function setupExplorer(engine, results, contracts) {
    const byId = id => document.getElementById(id);
    const profile = byId('layout-profile'), selector = byId('layout-record');
    const directives = byId('layout-directives'), search = byId('layout-search');
    const apply = byId('layout-apply'), reset = byId('layout-reset');
    const message = byId('layout-status'), error = byId('layout-error');
    const tree = byId('layout-tree'), meta = byId('layout-meta'), config = byId('layout-config');
    let current = null;
    const profiles = window.layoutCases.map((entry, index) => ({...entry, result: results[index], contract: contracts[index]}))
      .filter(entry => /^(release|development)-/.test(entry.name));
    for (const entry of profiles) {
      const option = node('option', entry.name, profile); option.value = entry.name;
    }
    profile.value = 'release-t8103';
    const selected = () => profiles.find(entry => entry.name === profile.value);
    const clearLayout = () => {current = null; tree.replaceChildren(); meta.hidden = true; config.replaceChildren();};
    const offset = bits => {
      if (!Number.isSafeInteger(bits) || bits < 0) throw new Error('Offset exceeds exact numeric range');
      const bytes = Math.floor(bits / 8), remainder = bits % 8;
      return `(+${hex(bytes)}${remainder ? ' + ' + remainder + 'b' : ''})`;
    };
    const offsetTitle = bits => `${Math.floor(bits / 8)} bytes${bits % 8 ? ' + ' + bits % 8 + ' bits' : ''} (${bits} bits)`;
    function declaration(type, name, records) {
      // Arrays are expanded from the compiler's element types, including typedef
      // arrays. Parenthesized abstract pointer declarators need the name inside
      // their parentheses: int (*callback)(int), int (*rows)[4].
      if (type.kind === 'array')
        return declaration(type.element, name + '[' + (type.count ?? '') + ']', records);
      const record = type.kind === 'record' ? records?.get(type.record_id) : null;
      if (record && !record.name) return record.kind + ' { … }' + (name ? ' ' + name : '');
      const spelling = type.spelling || type.kind;
      const pointer = /\((\s*[*^][^()]*)\)/;
      if (pointer.test(spelling)) return spelling.replace(pointer, (_, inner) => '(' + inner + (/\w$/.test(inner) ? ' ' : '') + name + ')');
      return spelling + (name ? ' ' + name : '');
    }
    function filter() {
      const query = search.value.trim().toLowerCase();
      const nodes = [...tree.querySelectorAll('.field-node')];
      for (const item of nodes.reverse()) {
        const own = item.dataset.fieldPath.toLowerCase().includes(query);
        const child = [...item.querySelectorAll('.field-node')].some(n => !n.hidden);
        item.hidden = Boolean(query) && !own && !child;
        if (query && child && item.tagName === 'DETAILS') item.open = true;
      }
    }
    function render() {
      tree.replaceChildren();
      if (!current || current.result.status !== 'ok') return;
      const records = new Map(current.result.records.map(record => [record.id, record]));
      const root = current.result.records.find(record => record.name === selector.value);
      if (!root) {meta.hidden = true; return;}
      meta.hidden = false;
      meta.textContent = `sizeof(${root.kind} ${root.name}) = ${hex(root.size_bytes)} · alignment = ${hex(root.alignment_bytes)}`;
      meta.title = `Size ${root.size_bytes} bytes; alignment ${root.alignment_bytes} bytes`;
      node('div', `${root.kind} ${root.name} {`, tree).className = 'record-brace';
      function item(parent, type, path, rootBits, localBits, field, ancestors = new Set(), preview = false, steps = []) {
        const resolved = LayoutContracts.resolvePath(current.contract, root.id, steps, {allowFlexiblePreview: true});
        if (rootBits !== resolved.root_offset_bits || localBits !== resolved.local_offset_bits) throw new Error('Layout path/contract offset mismatch');
        rootBits = resolved.root_offset_bits; localBits = resolved.local_offset_bits;
        const record = type.kind === 'record' ? records.get(type.record_id) : null;
        const expandable = record || type.kind === 'array';
        const element = node(expandable ? 'details' : 'div', undefined, parent);
        element.className = 'field-node' + (preview ? ' element-preview' : ''); element.dataset.fieldPath = path;
        element.dataset.rootBits = String(rootBits); element.dataset.localBits = String(localBits);
        const heading = node(expandable ? 'summary' : 'div', undefined, element);
        heading.className = 'declaration-row';
        heading.title = `${path}\nRoot offset: ${offsetTitle(rootBits)}\nLocal offset: ${offsetTitle(localBits)}\nCompiler type: ${type.spelling}`;
        const gutter = node('span', offset(rootBits), heading); gutter.className = 'field-offset';
        gutter.title = `Root offset: ${offsetTitle(rootBits)}; local offset: ${offsetTitle(localBits)}`;
        const code = node('code', undefined, heading); code.className = 'field-declaration';
        const name = field ? field.name : '';
        const width = field?.bit_width;
        const suffix = width !== null && width !== undefined ? ' : ' + width : '';
        let text = declaration(type, name, records) + suffix + ';';
        if (preview) text = (record ? record.kind + (record.name ? ' ' + record.name : '') : declaration(type, '', records)) +
          ' /* selected ' + path.slice(path.lastIndexOf('[')) + ' */';
        node('span', text, code).className = record ? 'declaration-closed' : 'field-name';
        if (record) {
          const annotation = preview ? 'selected ' + path.slice(path.lastIndexOf('[')) : name || 'anonymous';
          node('span', `${record.kind}${record.name ? ' ' + record.name : ''} { /* ${annotation} */`, code).className = 'declaration-open';
        }
        const size = node('span', undefined, heading); size.className = 'field-size';
        size.textContent = width !== null && width !== undefined ? width + 'b' :
          Number.isSafeInteger(type.size_bits) && type.size_bits % 8 === 0 ? hex(type.size_bits / 8) : '—';
        size.title = width !== null && width !== undefined ? `Bit-field width: ${width} bits` :
          Number.isSafeInteger(type.size_bits) ? `Size ${type.size_bits / 8} bytes (${type.size_bits} bits); alignment ${hex(type.alignment_bits / 8)} bytes` : 'Variable or incomplete size';
        if (type.kind === 'pointer') heading.title += '\nPointer value only; pointed-to storage is not embedded here.';
        // Full paths and local offsets remain available without repeating them
        // on every declaration row. Source links are revealed with the metadata.
        const info = node('details', undefined, element); info.className = 'field-info';
        node('summary', 'ⓘ', info).setAttribute('aria-label', 'Field details for ' + path);
        node('div', `${path} · local ${offset(localBits)} · root ${offset(rootBits)}`, info);
        if (field?.location?.file) {
          const key = window.layoutHeaderMaps[profile.value]?.[field.location.file];
          if (key) {
            const link = node('a', `source line ${field.location.line}`, info);
            link.href = 'headers/' + key + '.txt';
          }
        }
        if (record) {
          if (ancestors.has(record.id)) throw new Error('Unexpected embedded record cycle');
          const next = new Set(ancestors); next.add(record.id);
          const children = node('div', undefined, element); children.className = 'field-children';
          for (const [index, nested] of record.fields.entries())
            item(children, nested.type, path + '.' + (nested.name || `<anonymous ${index}>`),
              rootBits + nested.offset_bits, nested.offset_bits, nested, next, false, [...steps, nested.id]);
          node('div', '}' + (name ? ' ' + name : '') + ';', children).className = 'record-close';
        } else if (type.kind === 'array') {
          const stride = type.element?.size_bits;
          if (!Number.isSafeInteger(stride)) {node('p', 'Element size is unavailable.', element); return;}
          const count = type.count;
          const panel = node('div', undefined, element); panel.className = 'array-preview';
          node('small', count === null ? 'Flexible tail preview; runtime length unknown.' :
            `Element preview · count ${hex(count)} · stride ${hex(stride / 8)} bytes`, panel);
          if (count === 0) return;
          const label = node('label', 'Index ', panel);
          const input = node('input', undefined, label);
          input.type = 'number'; input.min = '0'; input.step = '1'; input.value = '0';
          input.setAttribute('aria-label', 'Element index for ' + path);
          if (count !== null) input.max = String(count - 1);
          const children = node('div', undefined, panel); children.className = 'field-children';
          const redraw = () => {
            children.replaceChildren();
            const index = Number(input.value);
            if (input.value === '' || !Number.isSafeInteger(index) || index < 0 || (count !== null && index >= count) ||
                !Number.isSafeInteger(index * stride) || !Number.isSafeInteger(rootBits + index * stride)) {
              node('p', 'Enter a valid element index within the fixed array, or a safe index for a flexible tail.', children); return;
            }
            item(children, type.element, path + '[' + index + ']', rootBits + index * stride, index * stride, null, ancestors, true, [...steps, {index}]);
            filter();
          };
          input.addEventListener('input', redraw); redraw();
        }
      }
      for (const [index, field] of root.fields.entries())
        item(tree, field.type, root.name + '.' + (field.name || `<anonymous ${index}>`), field.offset_bits, field.offset_bits, field, new Set(), false, [field.id]);
      node('div', '};', tree).className = 'record-brace';
      if (current.contract.dependencies.version === 2) {
        const analysis = current.contract.dependencies.analysis_id === window.layoutDependencyAnalysis?.id ? window.layoutDependencyAnalysis : window.layoutCustomDependencyAnalysis;
        if (analysis) {
          const details = node('details', undefined, tree); node('summary', 'Configuration dependencies (partial discovery)', details);
          const edges = new Map(analysis.edges.map(edge => [edge.id, edge]));
          const nodes = new Map(analysis.nodes.map(node => [node.id, node]));
          table(details, 'Potential controls and observed interventions', ['Macro', 'Evidence', 'Reason path'],
            LayoutDependencies.controlsFor(analysis, root.id).map(control => [control.macro,
              (nodes.get('macro:' + control.macro)?.details.category || 'preprocessor-macro') +
              (current.contract.configuration.policy.derived.includes(control.macro) ? '; header-derived' : current.contract.configuration.policy.compiler_reserved_prefixes.some(prefix => control.macro.startsWith(prefix)) ? '; compiler-reserved' : '') + '; ' + control.classification +
              (control.observed_no_change.length ? '; unchanged in ' + control.observed_no_change.length + ' controlled comparisons' : ''),
              control.paths.map(path => path.map(id => {const edge = edges.get(id); const at = nodes.get(edge.to);
                return edge.kind + ' → ' + (at.name || at.details.kind) + (at.source_id ? ' [' + analysis.sources.find(source => source.id === at.source_id).source_path + ':' + at.range.begin_bytes + ' bytes]' : '');}).join(' → ')).join(' | ')]));
          node('p', 'All manual edits are what-if analyses; changing compiler-query or reserved macro text does not enable a compiler feature. Coverage is limited to supplied configurations and indexed evidence. Unvisited branches remain unknown. Pointer references do not propagate embedded storage dependencies.', details);
        }
      }
      filter();
    }
    function showConfiguration(request, result) {
      config.replaceChildren();
      const macros = result.effective_macros || {};
      const keys = [...new Set([...Object.keys(request.macros), ...Object.keys(macros)])].sort();
      table(config, 'Requested and effective preprocessor definitions', ['Macro', 'Requested directive', 'Effective replacement', 'Definition origin'],
        keys.map(key => {
          const requested = Object.hasOwn(request.macros, key) ?
            request.macros[key] === null ? '#undef ' + key : '#define ' + key + ' ' + request.macros[key] : 'header/compiler';
          const effective = Object.hasOwn(macros, key) ? macros[key] : undefined;
          return [key, requested, effective === undefined ? 'not observed' : effective === null ? 'undefined' : effective.replacement || '(empty)',
            effective?.location?.file ? `${effective.location.file}:${effective.location.line}` : effective ? 'compiler/command line' : '—'];
        }));
      node('p', 'These target settings describe upstream Clang only; they do not imply support for Apple-private compiler features.', config);
      node('pre', JSON.stringify({requested_context: Object.fromEntries(Object.entries(request).filter(([key]) =>
        !['files', 'macros', 'observe_macros'].includes(key))), frontend_options: result.options}, null, 2), config);
    }
    function publish(request, result, custom, contract) {
      current = {request, result, contract}; error.textContent = '';
      showConfiguration(request, result);
      if (result.status === 'ok') {
        render();
        message.textContent = custom ? 'What-if layout computed with the displayed compiler and inputs; not a verified build profile.' :
          'Verified profile: browser and native compiler results match.';
      } else {
        tree.replaceChildren(); meta.hidden = true;
        message.textContent = 'No layout available for this configuration (' + result.status + ').';
      }
      error.textContent = result.diagnostics.map(d => `${d.severity}: ${d.message}`).join('\n');
    }
    function baseline() {
      directives.value = ''; error.textContent = ''; clearLayout();
      const entry = selected(); publish(entry.request, entry.result, false, entry.contract);
      window.layoutCustomResult = null;
    }
    function parseDirectives(text) {
      const overrides = Object.create(null);
      for (const [index, raw] of text.split(/\r?\n/).entries()) {
        const line = raw.trim(); if (!line || line.startsWith('//')) continue;
        let match = /^#\s*undef\s+([A-Za-z_][A-Za-z0-9_]*)\s*$/.exec(line);
        if (match) {overrides[match[1]] = null; continue;}
        match = /^#\s*define\s+([A-Za-z_][A-Za-z0-9_]*)(?:\s+(.*))?$/.exec(line);
        if (!match || line.endsWith('\\')) throw new Error('Line ' + (index + 1) + ': use an object-like #define or #undef on one line.');
        overrides[match[1]] = match[2] || '';
      }
      return overrides;
    }
    apply.addEventListener('click', async () => {
      clearLayout(); error.textContent = ''; window.layoutCustomResult = null;
      message.textContent = 'Analyzing configuration…';
      [apply, reset, profile, selector, directives, search].forEach(control => {control.disabled = true;});
      try {
        const base = selected().request;
        const overrides = parseDirectives(directives.value);
        const resolved = LayoutContracts.resolveConfiguration(base, overrides, selected().contract.configuration.policy, {whatIf: true});
        if (resolved.resolution.status === 'invalid-configuration') throw new Error(resolved.resolution.issues.join('\n'));
        const request = {...resolved.request,
          observe_macros: [...new Set([...base.observe_macros, ...Object.keys(base.macros), ...Object.keys(overrides)])].sort()};
        await new Promise(resolve => setTimeout(resolve, 0));
        const result = analyze(engine, request);
        let contract = await LayoutContracts.create(request, result, {source: selected().contract.source,
          policy: selected().contract.configuration.policy, whatIf: true});
        if (window.layoutDependencyAnalysis) {
          const baseline = selected();
          const entries = [{name: baseline.name, request: baseline.request, result: baseline.result, document: baseline.contract},
            {name: 'manual-what-if', request, result, document: contract}];
          const analysis = await LayoutDependencies.discover(entries, {space_id: baseline.name + '-baseline-and-manual-what-if'});
          await LayoutContracts.registerDependencyAnalysis(analysis);
          contract = await LayoutDependencies.attach(contract, analysis);
          window.layoutCustomDependencyAnalysis = analysis;
        }
        publish(request, result, true, contract);
        window.layoutCustomResult = {request, result, contract};
      } catch (failure) {
        clearLayout(); error.textContent = failure.message; message.textContent = 'No layout available.';
        window.layoutCustomResult = {error: failure.message};
      } finally {
        [apply, reset, profile, selector, directives, search].forEach(control => {control.disabled = false;});
      }
    });
    reset.addEventListener('click', baseline); profile.addEventListener('change', baseline);
    selector.addEventListener('change', render); search.addEventListener('input', filter);
    // Edits invalidate the visible layout immediately, avoiding stale offsets.
    directives.addEventListener('input', () => {clearLayout(); window.layoutCustomResult = null;
      message.textContent = 'Configuration changed. Apply it to compute a layout.';});
    [apply, reset, profile, selector, directives, search].forEach(control => {control.disabled = false;});
    baseline();
  }
  try {
    const engine = await createLayoutEngine({wasmBinary: decodeLayoutWasm(),
      printErr: text => {document.getElementById('stderr').textContent += text + '\n';},
      onAbort: message => {throw new Error(String(message));}});
    metrics.startup_ms = performance.now() - window.layoutProofStart;
    const results = [], contracts = [];
    for (let i = 0; i < window.layoutCases.length; ++i) {
      const {name, request} = window.layoutCases[i];
      status.textContent = 'Analyzing ' + name + '…';
      await new Promise(resolve => setTimeout(resolve, 0));
      const before = performance.now();
      const result = analyze(engine, request);
      metrics.parse_ms.push(performance.now() - before);
      if (!equal(result, window.layoutExpected[i])) throw new Error('Native/browser mismatch: ' + name);
      const expected = window.layoutExpectedContracts[i];
      const contract = await LayoutContracts.create(request, result, {source: expected.source,
        policy: expected.configuration.policy, profile: expected.configuration.profile,
        whatIf: expected.configuration.classification === 'what-if'});
      const expectedBase = window.layoutExpectedDependencyAnalysis ? LayoutDependencies.baseDocument(expected) : expected;
      if (LayoutContracts.canonical(contract) !== LayoutContracts.canonical(expectedBase)) throw new Error('Contract/native mismatch: ' + name);
      contracts.push(contract);
      results.push(result);
      show(name, request, result);
    }
    if (window.layoutExpectedDependencyAnalysis) {
      status.textContent = 'Discovering configuration dependencies…';
      const entries = window.layoutCases.map((entry, index) => ({...entry, result: results[index], document: contracts[index]}));
      const analysis = await LayoutDependencies.discover(entries, {space_id: 'xnu-pilot'});
      if (LayoutContracts.canonical(analysis) !== LayoutContracts.canonical(window.layoutExpectedDependencyAnalysis)) throw new Error('Dependency analysis/native mismatch');
      await LayoutContracts.registerDependencyAnalysis(analysis);
      for (let index = 0; index < contracts.length; ++index) {
        contracts[index] = await LayoutDependencies.attach(contracts[index], analysis);
        await LayoutContracts.validate(contracts[index]);
        if (LayoutContracts.canonical(contracts[index]) !== LayoutContracts.canonical(window.layoutExpectedContracts[index])) throw new Error('Dependency contract mismatch');
      }
      window.layoutDependencyAnalysis = analysis;
    }
    metrics.linear_memory_before_repeats_bytes = engine.HEAPU8.buffer.byteLength;
    status.textContent = 'Checking repeated analysis…';
    for (let i = 0; i < 30; ++i) {
      const index = i % window.layoutCases.length;
      if (!equal(analyze(engine, window.layoutCases[index].request), results[index]))
        throw new Error('Repeated analysis changed result');
      await new Promise(resolve => setTimeout(resolve, 0));
    }
    metrics.linear_memory_after_repeats_bytes = engine.HEAPU8.buffer.byteLength;
    metrics.parity = 'passed'; metrics.cases = results.length; metrics.repeated_requests = 30;
    window.layoutProofResults = results;
    window.layoutContractSets = contracts;
    setupExplorer(engine, results, contracts);
    status.textContent = 'All four profiles and ' + (results.length - 4) + ' diagnostic/what-if tests match native Clang. Thirty repeated requests passed.';
    document.documentElement.dataset.result = 'passed';
  } catch (error) {
    metrics.parity = 'failed'; metrics.error = error.stack || String(error);
    status.textContent = 'Failed: ' + error.message;
    document.documentElement.dataset.result = 'failed';
  }
  metrics.total_ms = performance.now() - window.layoutProofStart;
  document.getElementById('metrics').textContent = JSON.stringify(metrics, null, 2);
  window.layoutProofMetrics = metrics;
})();
