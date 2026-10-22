// SPDX-License-Identifier: GPL-2.0-only
// M5 offline worker adapter; preserves the accepted C-style layout presentation.
(() => {
  'use strict';
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
  function setupExplorer(client) {
    const byId = id => document.getElementById(id);
    const profile = byId('layout-profile'), selector = byId('layout-record');
    const directives = byId('layout-directives'), search = byId('layout-search');
    const apply = byId('layout-apply'), reset = byId('layout-reset');
    const message = byId('layout-status'), error = byId('layout-error');
    const tree = byId('layout-tree'), meta = byId('layout-meta'), config = byId('layout-config');
    let current = null;
    let viewGeneration = 0;
    const profiles = window.layoutRuntimeManifest.profiles;
    for (const entry of profiles) {const option = node('option', entry.label || entry.id, profile); option.value = entry.id;}
    profile.value = profiles.some(entry => entry.id === 'release-t8103') ? 'release-t8103' : profiles[0].id;
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
          const key = window.layoutHeaderMaps?.[profile.value]?.[field.location.file];
          if (key) {const link = node('a', `source line ${field.location.line}`, info); link.href = 'headers/' + key + '.txt';}
          else if (Object.hasOwn(current.request.files, field.location.file)) {
            const download = node('button', `Download source (line ${field.location.line})`, info); download.type = 'button';
            download.addEventListener('click', () => {const url = URL.createObjectURL(new Blob([current.request.files[field.location.file]], {type: 'text/plain'}));
              const link = document.createElement('a'); link.href = url; link.download = field.location.file.split('/').at(-1); link.click(); setTimeout(() => URL.revokeObjectURL(url), 0);});
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
          'Source profile computed in the offline compiler worker.';
      } else {
        tree.replaceChildren(); meta.hidden = true;
        message.textContent = 'No layout available for this configuration (' + result.status + ').';
      }
      error.textContent = result.diagnostics.map(d => `${d.severity}: ${d.message}`).join('\n');
    }
    async function run(overrides = {}, custom = false) {
      const mine = ++viewGeneration;
      clearLayout(); error.textContent = ''; window.layoutRuntimeCurrent = null; window.layoutCustomResult = null; window.layoutDependencyAnalysis = null;
      message.textContent = 'Analyzing in the compiler worker…';
      try {
        const value = await client.analyze(profile.value, {overrides});
        if (mine !== viewGeneration) return;
        window.layoutDependencyAnalysis = value.analysis;
        window.layoutRuntimeCurrent = value;
        showMetrics(value);
        publish(value.request, value.result, custom, value.contract);
        window.layoutCustomResult = custom ? value : null;
        document.documentElement.dataset.result = value.result.status === 'ok' ? 'ready' : 'compiler-error';
      } catch (failure) {
        if (mine !== viewGeneration) return;
        clearLayout(); error.textContent = failure.message; message.textContent = 'No layout available (' + failure.code + ').';
        window.layoutCustomResult = {error: failure.message, code: failure.code};
        document.documentElement.dataset.result = failure.code || 'error';
      }
    }
    function baseline() {directives.value = ''; return run();}
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
    apply.addEventListener('click', () => {
      try {const overrides = parseDirectives(directives.value); run(overrides, true);}
      catch (failure) {++viewGeneration; client.cancel(); clearLayout(); window.layoutRuntimeCurrent = null; window.layoutCustomResult = null; window.layoutDependencyAnalysis = null; error.textContent = failure.message;}
    });
    reset.addEventListener('click', baseline); profile.addEventListener('change', baseline);
    selector.addEventListener('change', render); search.addEventListener('input', filter);
    directives.addEventListener('input', () => {++viewGeneration; client.cancel(); clearLayout(); window.layoutRuntimeCurrent = null; window.layoutCustomResult = null; window.layoutDependencyAnalysis = null;
      message.textContent = 'Configuration changed. Apply it to compute a layout.';});
    let cancel = byId('layout-cancel');
    if (!cancel) {cancel = node('button', 'Cancel', apply.parentElement); cancel.id = 'layout-cancel';}
    cancel.addEventListener('click', () => {++viewGeneration; client.cancel(); clearLayout(); window.layoutRuntimeCurrent = null; window.layoutCustomResult = null; window.layoutDependencyAnalysis = null; message.textContent = 'Analysis cancelled. Apply or reset to restart.';});
    [apply, reset, profile, selector, directives, search, cancel].forEach(control => {control.disabled = false;});
    baseline();
  }
  function showMetrics(value = null) {
    if (value) window.layoutRuntimeLastMeasurement = {id: value.id, generation: value.generation, profile: value.profile, ...value.metrics};
    const output = document.getElementById('metrics');
    if (output) output.textContent = JSON.stringify({state: window.layoutRuntimeState, runtime: client.metrics,
      last_completed_request: window.layoutRuntimeLastMeasurement || null,
      note: 'Cache bytes count serialized JSON. Wasm capacity is not live heap or process RSS; retirement is checked after analysis.'}, null, 2);
  }
  const client = new LayoutRuntime.Client(window.layoutRuntimeManifest, {...(window.layoutRuntimeOptions || {}),
    onstate(state) {window.layoutRuntimeState = state; const status = document.getElementById('layout-status'); if (status) status.textContent = state.state + (state.message ? ': ' + state.message : ''); showMetrics();}});
  window.layoutRuntimeClient = client;
  window.addEventListener('pagehide', () => client.dispose(), {once: true});
  setupExplorer(client);
})();
