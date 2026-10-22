// SPDX-License-Identifier: GPL-2.0-only
// Visual preview over saved compiler outputs; no compiler or runtime is started.
(() => {
  'use strict';
  document.body.classList.add('js-ready');
  const data = window.LayoutMockupData;
  if (!data?.profiles?.length) {document.getElementById('layout-tree').textContent = 'Recorded layout data is unavailable.'; return;}
  const $ = id => document.getElementById(id);
  const el = (tag, text, parent, className) => {const value = document.createElement(tag); if (text !== undefined) value.textContent = text; if (className) value.className = className; if (parent) parent.append(value); return value;};
  const state = {profile: data.defaultProfile || 'release-t8103', root: 'recount_track', cpi: true, energy: true, hex: true,
    selected: 'recount_track.rt_usage.ru_metrics[1].rm_cycles', expanded: new Set(['recount_track.rt_usage','recount_track.rt_usage.ru_metrics']), indices: new Map(), query: '', all: false};
  let fields = new Map();
  const number = value => state.hex ? '0x' + value.toString(16) : String(value);
  const offset = bits => '+' + number(Math.floor(bits / 8)) + (bits % 8 ? ' + ' + bits % 8 + 'b' : '');
  const effective = (result, name) => result.effective_macros?.[name]?.replacement;
  const chosen = () => data.profiles.find(profile => profile.id === (state.profile === 'release-t8103' ?
    state.cpi ? state.energy ? 'release-t8103' : 'probe-no-energy' : state.energy ? 'probe-no-cpi' : 'probe-neither-counter' : state.profile));
  const sourceURL = location => location?.file?.startsWith('/inputs/xnu/') ? data.bookRoot + '_sources/xnu/' + location.file.slice('/inputs/xnu/'.length) + '.html#L' + location.line : null;
  for (const link of document.querySelectorAll('[data-book]')) link.href = data.bookRoot + link.dataset.book;
  const baselineProfiles = data.profiles.filter(profile => /^(release|development)-/.test(profile.id));
  for (const profile of baselineProfiles) {const option = el('option', profile.label || profile.id, $('profile-select')); option.value = profile.id;}
  $('profile-select').value = state.profile;
  $('source-edition').textContent = data.source.release + ' · ARM64 Darwin';
  const types = type => type.kind === 'array' ? types(type.element) : type.spelling || type.kind;
  function declaration(type, name, records) {
    if (type.kind === 'array') return declaration(type.element, name + '[' + (type.count ?? '') + ']', records);
    const record = type.kind === 'record' ? records?.get(type.record_id) : null;
    if (record && !record.name) return record.kind + ' { … }' + (name ? ' ' + name : '');
    const spelling = type.spelling || type.kind;
    const pointer = /\((\s*[*^][^()]*)\)/;
    if (pointer.test(spelling)) return spelling.replace(pointer, (_, inner) => '(' + inner + (/\w$/.test(inner) ? ' ' : '') + name + ')');
    return spelling + (name ? ' ' + name : '');
  }
  function inspect(field) {
    if (!field) return;
    state.selected = field.path;
    for (const row of document.querySelectorAll('.declaration-row')) row.classList.toggle('selected', row.dataset.path === field.path);
    $('selected-name').textContent = field.name;
    $('selected-type').textContent = field.type.spelling;
    $('selected-path').textContent = field.path;
    $('selected-root').textContent = offset(field.rootBits);
    $('selected-root-decimal').textContent = Math.floor(field.rootBits / 8) + ' bytes · ' + field.rootBits + ' bits';
    $('selected-local').textContent = offset(field.localBits);
    $('selected-size').textContent = field.bitWidth !== null ? field.bitWidth + ' bits' : field.type.size_bits === null ? 'Variable' : number(field.type.size_bits / 8) + ' B';
    $('selected-align').textContent = field.type.alignment_bits === null ? '—' : number(field.type.alignment_bits / 8) + ' B';
    $('path-steps').replaceChildren();
    for (const step of field.steps) {const item = el('li', step.name, $('path-steps')); el('span', offset(step.bits) + ' from parent', item);}
    const url = sourceURL(field.location);
    $('selected-source').hidden = !url; if (url) $('selected-source').href = url;
    $('selected-source').textContent = field.location ? 'Open ' + field.location.file.split('/').at(-1) + ' ↗' : 'Open source ↗';
    $('source-location').textContent = field.location ? field.location.file.replace('/inputs/xnu/', '') + ':' + field.location.line : 'Source location unavailable';
    $('field-note').textContent = field.type.kind === 'pointer' ? 'This field stores a pointer. Its referent belongs to another object and is not embedded here.' : field.path.includes('[') ?
      'The root offset includes the selected array element. Local offset starts at the immediate parent.' : 'Root offset starts at the enclosing object. Local offset starts at this field’s immediate parent.';
  }
  function render() {
    const profile = chosen();
    if (!profile) return;
    const result = profile.result, records = new Map(result.records.map(record => [record.id, record]));
    const root = result.records.find(record => record.name === state.root);
    if (!root) return;
    fields = new Map(); $('layout-tree').replaceChildren();
    $('size-value').textContent = number(root.size_bytes) + ' B'; $('align-value').textContent = number(root.alignment_bytes) + ' B';
    $('hex-button').setAttribute('aria-pressed', String(state.hex)); $('decimal-button').setAttribute('aria-pressed', String(!state.hex));
    $('byte-format').textContent = state.hex ? 'hexadecimal bytes' : 'decimal bytes';
    const manual = state.profile === 'release-t8103';
    $('cpi-toggle').disabled = !manual; $('energy-toggle').disabled = !manual;
    $('cpi-toggle').checked = manual ? state.cpi : effective(result, 'CONFIG_PERVASIVE_CPI') === '1';
    $('energy-toggle').checked = manual ? state.energy : effective(result, 'CONFIG_PERVASIVE_ENERGY') === '1';
    const macroNames = ['CONFIG_PERVASIVE_CPI', 'CONFIG_PERVASIVE_ENERGY', 'CONFIG_SPTM', 'CONFIG_TASK_SUSPEND_STATS'];
    const requested = profile.request.macros || {};
    const directive = (name, value) => value === null ? '#undef ' + name : '#define ' + name + (value ? ' ' + value : '');
    $('directives').textContent = macroNames.map(name => Object.hasOwn(requested, name) ? directive(name, requested[name]) : '// ' + name + ': not requested; see effective value below').join('\n') +
      '\n\n// Effective after preprocessing\n' + macroNames.map(name => '// ' + name + ' = ' + (result.effective_macros?.[name] === null ? 'undefined' : effective(result, name) ?? 'not observed')).join('\n') +
      '\n\n// All requested directives\n' + Object.entries(requested).sort(([a],[b]) => a < b ? -1 : a > b ? 1 : 0).map(([name,value]) => directive(name,value)).join('\n');
    $('config-limitation').textContent = !manual ? 'Flag switches are available only for the saved Release · T8103 variants.' : state.root === 'task' ?
      'These saved CPI/energy variants change recount storage. The task layout remains unchanged; pointer referents are separate objects.' : 'Four saved combinations demonstrate how CPI and energy metrics change recount_track.';
    const chapter = state.root === 'task' ? 'structures/task-and-shared-ro.html' : 'subsystems/runtime/recount-and-resource-attribution.html';
    $('chapter-link').href = data.bookRoot + chapter;
    $('chapter-link').textContent = (state.root === 'task' ? 'Task & shared read-only state' : 'Recount & resource attribution') + ' →';
    const brace = el('div', undefined, $('layout-tree'), 'root-brace'); el('span', root.kind + ' ', brace, 'keyword'); el('span', root.name + ' {', brace);
    const renderField = (field, parent, prefix, rootBase, depth, steps, stack = new Set()) => {
      const path = prefix + '.' + field.name, type = field.type;
      const rootBits = rootBase + field.offset_bits;
      const record = type.kind === 'record' ? records.get(type.record_id) : null;
      const expandable = Boolean(record || type.kind === 'array');
      const opened = Boolean(state.query || state.all || state.expanded.has(path));
      const descriptor = {path, name: field.name || '(anonymous)', type, rootBits, localBits: field.offset_bits, bitWidth: field.bit_width,
        location: field.location, steps: [...steps, {name: field.name || '(anonymous)', bits: field.offset_bits}]};
      fields.set(path, descriptor);
      const wrapper = el('div', undefined, parent, 'field-node');
      const row = el('div', undefined, wrapper, 'declaration-row'); row.dataset.path = path; row.dataset.rootBits = rootBits; row.dataset.localBits = field.offset_bits;
      el('span', '(' + offset(rootBits) + ')', row, 'field-offset');
      const code = el('div', undefined, row, 'field-code'); code.style.setProperty('--depth', depth);
      if (expandable) {const toggle = el('button', opened ? '▾' : '▸', code, 'disclosure'); toggle.type = 'button'; toggle.setAttribute('aria-label', (opened ? 'Collapse ' : 'Expand ') + path); toggle.setAttribute('aria-expanded', String(opened));
        toggle.addEventListener('click', () => {state.all = false; if (opened) state.expanded.delete(path); else state.expanded.add(path); render();});
      } else el('span', '', code, 'disclosure-spacer');
      const select = el('button', undefined, code, 'field-select'); select.type = 'button'; select.setAttribute('aria-label', path + ', root offset ' + rootBits + ' bits');
      const label = record && opened ? record.kind + (record.name ? ' ' + record.name : '') + ' { /* ' + field.name + ' */' : declaration(type, field.name, records) + (field.bit_width !== null ? ' : ' + field.bit_width : '') + ';';
      const nameAt = label.lastIndexOf(field.name);
      if (nameAt >= 0 && field.name) {el('span', label.slice(0, nameAt), select, 'field-type'); el('span', field.name, select, 'field-name'); el('span', label.slice(nameAt + field.name.length), select);}
      else select.textContent = label;
      select.addEventListener('click', () => inspect(descriptor)); row.addEventListener('click', event => {if (!event.target.closest('button')) inspect(descriptor);});
      row.title = path + '\nLocal: ' + offset(field.offset_bits) + '; root: ' + offset(rootBits);
      el('span', field.bit_width !== null ? field.bit_width + 'b' : type.size_bits === null ? '—' : number(type.size_bits / 8), row, 'field-size');
      if (opened && record && !stack.has(record.id)) {const next = new Set([...stack, record.id]); for (const nested of record.fields) renderField(nested, wrapper, path, rootBits, depth + 1, descriptor.steps, next);
        const close = el('div', '} ' + field.name + ';', wrapper, 'record-close'); close.style.setProperty('--depth', depth);}
      if (opened && type.kind === 'array') {
        const count = type.count;
        const index = state.indices.has(path) ? state.indices.get(path) : path.endsWith('.ru_metrics') && count > 1 ? 1 : 0;
        if (count !== 0 && Number.isSafeInteger(type.element?.size_bits)) {
          const panel = el('div', undefined, wrapper, 'array-choice'); panel.style.setProperty('--depth', depth);
          const label = el('label', 'Preview element ', panel), input = el('input', undefined, label); input.type = 'number'; input.min = '0'; input.step = '1'; if (count !== null) input.max = String(count - 1); input.value = String(index); input.setAttribute('aria-label', 'Array index for ' + path);
          el('span', 'of ' + (count ?? 'unknown') + ' · stride ' + number(type.element.size_bits / 8) + ' B', panel);
          input.addEventListener('change', () => {const next = Number(input.value); if (input.value === '' || !Number.isSafeInteger(next) || next < 0 || !Number.isSafeInteger(next * type.element.size_bits) || !Number.isSafeInteger(rootBits + next * type.element.size_bits) || count !== null && next >= count) {input.setCustomValidity('Choose an index within this array.'); input.reportValidity(); return;} input.setCustomValidity(''); state.indices.set(path, next);
            if (state.selected.startsWith(path + '[')) state.selected = state.selected.replace(path + '[' + index + ']', path + '[' + next + ']'); render();});
          const element = type.element, elementRoot = rootBits + index * element.size_bits, elementPath = path + '[' + index + ']';
          const elementRecord = element.kind === 'record' ? records.get(element.record_id) : null;
          if (elementRecord) {const open = el('div', elementRecord.kind + (elementRecord.name ? ' ' + elementRecord.name : '') + ' { /* element [' + index + '] */', wrapper, 'record-close'); open.style.setProperty('--depth', depth);
            const elementSteps = [...descriptor.steps, {name: '[' + index + ']', bits: index * element.size_bits}];
            for (const nested of elementRecord.fields) renderField(nested, wrapper, elementPath, elementRoot, depth + 1, elementSteps, new Set([...stack, elementRecord.id]));
            const close = el('div', '}', wrapper, 'record-close'); close.style.setProperty('--depth', depth);}
          else {
            const preview = {path: elementPath, name: '[' + index + ']', type: element, rootBits: elementRoot, localBits: index * element.size_bits,
              bitWidth: null, location: field.location, steps: [...descriptor.steps, {name: '[' + index + ']', bits: index * element.size_bits}]};
            fields.set(elementPath, preview);
            const row = el('div', undefined, wrapper, 'declaration-row'); row.dataset.path = elementPath; row.dataset.rootBits = elementRoot; row.dataset.localBits = preview.localBits;
            el('span', '(' + offset(elementRoot) + ')', row, 'field-offset');
            const code = el('div', undefined, row, 'field-code'); code.style.setProperty('--depth', depth + 1);
            el('span', '', code, 'disclosure-spacer');
            const choose = el('button', (element.spelling || element.kind) + ' /* selected [' + index + '] */', code, 'field-select'); choose.type = 'button'; choose.setAttribute('aria-label', 'Select ' + elementPath);
            choose.addEventListener('click', () => inspect(preview));
            el('span', number(element.size_bits / 8), row, 'field-size');
          }
        }
      }
      const ownMatch = !state.query || path.toLowerCase().includes(state.query) || type.spelling.toLowerCase().includes(state.query);
      const childMatch = [...wrapper.querySelectorAll('.field-node')].some(child => !child.hidden);
      wrapper.hidden = !ownMatch && !childMatch;
    };
    for (const field of root.fields) renderField(field, $('layout-tree'), root.name, 0, 0, []);
    el('div', '};', $('layout-tree'), 'root-brace');
    const selected = fields.get(state.selected) || [...fields.values()].find(field => field.path.toLowerCase().includes(state.query)) || fields.values().next().value;
    inspect(selected);
    if (![...$('layout-tree').querySelectorAll('.field-node')].some(field => !field.hidden)) el('p', 'No matching fields in this recorded layout.', $('layout-tree'), 'empty-fields');
    $('announce').textContent = state.root + ': ' + root.size_bytes + ' bytes; recorded configuration ' + profile.id;
    window.layoutMockupState = {profile: profile.id, root: state.root, selected: state.selected, size_bytes: root.size_bytes};
  }
  $('root-select').addEventListener('change', event => {state.root = event.target.value; state.selected = state.root === 'recount_track' ? 'recount_track.rt_usage.ru_metrics[1].rm_cycles' : 'task.ref_count'; state.query = ''; $('field-search').value = ''; render();});
  $('profile-select').addEventListener('change', event => {state.profile = event.target.value; state.cpi = state.energy = true; render();});
  $('cpi-toggle').addEventListener('change', event => {state.cpi = event.target.checked; render();});
  $('energy-toggle').addEventListener('change', event => {state.energy = event.target.checked; render();});
  $('field-search').addEventListener('input', event => {state.query = event.target.value.trim().toLowerCase(); render();});
  $('hex-button').addEventListener('click', () => {state.hex = true; render();}); $('decimal-button').addEventListener('click', () => {state.hex = false; render();});
  $('expand-all').addEventListener('click', () => {state.all = true; render();}); $('collapse-all').addEventListener('click', () => {state.all = false; state.expanded.clear(); render();});
  $('theme-toggle').addEventListener('click', () => {const dark = document.documentElement.dataset.theme !== 'dark'; document.documentElement.dataset.theme = dark ? 'dark' : 'light'; $('theme-toggle').setAttribute('aria-label', 'Switch to ' + (dark ? 'light' : 'dark') + ' theme');});
  $('nav-toggle').addEventListener('click', () => {const open = document.body.classList.toggle('nav-open'); $('nav-toggle').setAttribute('aria-expanded', String(open));});
  document.addEventListener('keydown', event => {if (event.key === '/' && !['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName)) {event.preventDefault(); $('field-search').focus();} if (event.key === 'Escape') {document.body.classList.remove('nav-open'); $('nav-toggle').setAttribute('aria-expanded', 'false'); $('config-details').open = false;}});
  render();
})();
