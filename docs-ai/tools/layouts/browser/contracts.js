// SPDX-License-Identifier: GPL-2.0-only
// Executable contracts shared by the native report tooling and file:// browser.
(function (root, factory) {
  const api = factory(typeof module === 'object' && module.exports ? require('node:crypto').webcrypto : root.crypto);
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.LayoutContracts = api;
})(globalThis, function (crypto) {
  'use strict';
  const VERSION = 1, MAX = Number.MAX_SAFE_INTEGER;
  const STATUSES = {'ok': 'success', 'invalid-request': 'invalid-configuration', 'error': 'compilation-error',
    'unavailable-type': 'incomplete-type', 'unsupported-layout': 'unsupported'};
  const REQUEST_KEYS = ['target', 'main', 'files', 'macros', 'records', 'include_dirs', 'forced_includes',
    'target_cpu', 'target_arch', 'target_features', 'language', 'blocks', 'kernel_mode', 'ptrauth_intrinsics', 'ptrauth_calls', 'observe_macros', 'trace_files', 'source_paths', 'trace_dependencies', 'dependency_files'];
  const fail = message => {throw new Error('Layout contract: ' + message);};
  function object(value, label) {
    if (!value || typeof value !== 'object' || Array.isArray(value) ||
        ![Object.prototype, null].includes(Object.getPrototypeOf(value))) fail(label + ' must be an object');
    return value;
  }
  function keys(value, required, optional = []) {
    object(value, 'document');
    for (const name of required) if (!Object.hasOwn(value, name)) fail('missing ' + name);
    for (const name of Object.keys(value)) if (![...required, ...optional].includes(name)) fail('unknown key ' + name);
  }
  const integer = (value, label, min = 0) => {
    if (!Number.isSafeInteger(value) || value < min) fail(label + ' must be an exact nonnegative integer');
  };
  const string = (value, label) => {if (typeof value !== 'string') fail(label + ' must be a string');};
  const bool = (value, label) => {if (typeof value !== 'boolean') fail(label + ' must be boolean');};
  const array = (value, label) => {if (!Array.isArray(value)) fail(label + ' must be an array'); return value;};
  const unique = (values, label) => {if (new Set(values).size !== values.length) fail('duplicate ' + label);};
  const hashPattern = /^[a-f0-9]{64}$/;
  const declarationPattern = /^decl-v1:[a-f0-9]{64}$/;
  const macroPattern = /^[A-Za-z_][A-Za-z_0-9]*$/;
  // Independently authored CE stand-ins support only these original UBC roots.
  // They are never a source of advertised ABI/type/layout information.
  function guardUBC(requested, paths, exposed = null) {
    if (!paths.some(path => path.startsWith('/inputs/layout-compat/'))) return;
    if (JSON.stringify(requested?.records) !== JSON.stringify(['ubc_info', 'cs_blob']))
      fail('Layout-only CE context permits only ubc_info and cs_blob.');
    const unavailable = /\b(?:PlatydocUnavailableCEContext|PlatydocOpaqueCEKernelAPI|CEContext_t|CEKernelAPI_t)\b/;
    for (const value of Object.values(requested.macros || {})) {
      const replacement = typeof value === 'string' ? value : value?.replacement || '';
      if (unavailable.test(replacement) || /\b(?:sizeof|_Alignof|__alignof|__alignof__|alignof|typeof|__typeof|__typeof__|offsetof|__builtin_offsetof)\b/.test(replacement)) fail('Layout-only CE context forbids macro type queries or stand-in references.');
    }
    if (exposed !== null) {
      const text = canonical(exposed);
      if (unavailable.test(text) || text.includes('/inputs/layout-compat/') || text.includes('layout-compatibility/'))
        fail('Layout-only CE stand-in-dependent types/declarations/layouts cannot be published.');
    }
  }
  // This bound source-entry/probe contract identifies the supported catalog
  // lane. Generic API analyses need not carry Platydoc's source-profile probes.
  const requiresPAC = requested => requested?.target === 'arm64e-apple-ios' && requested.ptrauth_calls === true && requested.ptrauth_intrinsics === true &&
    requested.source_paths?.[requested.main] === 'analysis-entry/inputs/request.c' &&
    ['PLATYDOC_PTRAUTH_CALLS', 'PLATYDOC_PTRAUTH_INTRINSICS'].every(name => requested.observe_macros?.includes(name));
  function validateMandatoryPAC(configuration) {
    if (!requiresPAC(configuration.requested) && !requiresPAC(configuration.policy.baseline.requested)) return;
    const required = ['__arm64e__', 'PLATYDOC_PTRAUTH_CALLS', 'PLATYDOC_PTRAUTH_INTRINSICS'];
    // Narrow header contexts may never include the source defining these names.
    // Preserve their baseline value only where that source definition was observed.
    for (const name of ['HAS_APPLE_PAC', 'CPU_HAS_APPLE_PAC']) if (configuration.policy.derived.includes(name)) required.push(name);
    for (const name of required) {
      const value = configuration.effective.macros[name];
      if (value?.state !== 'defined' || value.replacement !== '1') fail('Mandatory iOS PAC context requires effective ' + name + '=1; layouts with disabled PAC fields cannot be published.');
    }
    for (const option of ['-fptrauth-calls', '-fptrauth-intrinsics']) if (!configuration.effective.frontend_options?.includes(option))
      fail('Mandatory iOS PAC context requires compiler option ' + option + '.');
  }
  function canonical(value) {
    if (value === null || typeof value === 'boolean' || typeof value === 'string') return JSON.stringify(value);
    if (typeof value === 'number') {integer(value, 'JSON number'); return String(value);}
    if (Array.isArray(value)) return '[' + Array.from({length: value.length}, (_, index) => {if (!Object.hasOwn(value, index)) fail('sparse JSON array'); return canonical(value[index]);}).join(',') + ']';
    object(value, 'JSON value');
    return '{' + Object.keys(value).sort().map(name => JSON.stringify(name) + ':' + canonical(value[name])).join(',') + '}';
  }
  const copy = value => JSON.parse(canonical(value));
  async function sha256(value) {
    const bytes = typeof value === 'string' ? new TextEncoder().encode(value) : value;
    return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(x => x.toString(16).padStart(2, '0')).join('');
  }
  const identity = async (prefix, value) => prefix + ':' + await sha256(canonical(value));
  const header = name => ({contract: 'platydoc.' + name, version: VERSION});
  function version(value, name) {
    if (value.contract !== 'platydoc.' + name || value.version !== VERSION) fail('unsupported ' + name + ' version');
  }
  function state(value, effective = false) {
    if (value === null) return {state: 'undefined'};
    if (!effective) return {state: 'defined', replacement: value};
    return {state: 'defined', replacement: value.replacement, function_like: value.function_like,
      location: value.location || null};
  }
  function macroState(value, effective) {
    if (value.state === 'undefined') keys(value, ['state']);
    else {
      keys(value, effective ? ['state', 'replacement', 'function_like', 'location'] : ['state', 'replacement']);
      if (value.state !== 'defined') fail('unknown macro state');
      string(value.replacement, 'macro replacement');
      if (/[\r\n\0]/.test(value.replacement)) fail('multiline macro replacement');
      if (effective) {bool(value.function_like, 'function_like'); if (value.location !== null) location(value.location);}
    }
  }
  function location(value) {
    keys(value, ['file', 'line', 'column', 'offset_bytes']);
    string(value.file, 'location file');
    for (const name of ['line', 'column', 'offset_bytes']) integer(value[name], name);
  }
  function bareSourcePoint(value, inputs) {
    keys(value, ['file', 'line', 'column', 'offset_bytes', 'source_path', 'sha256']);
    location(Object.fromEntries(['file', 'line', 'column', 'offset_bytes'].map(k => [k, value[k]])));
    string(value.source_path, 'physical source path');
    if (!hashPattern.test(value.sha256)) fail('invalid source hash');
    const input = inputs.get(value.file);
    if (!value.file || !value.source_path || !input || input.sha256 !== value.sha256 ||
        input.source_path !== value.source_path || value.offset_bytes > input.bytes || value.line < 1 || value.column < 1)
      fail('source point is not bound to supplied physical bytes');
  }
  function sourcePoint(value, inputs) {
    keys(value, ['file', 'line', 'column', 'offset_bytes', 'source_path', 'sha256', 'include_sites']);
    const {include_sites, ...bare} = value; bareSourcePoint(bare, inputs);
    for (const site of array(include_sites, 'source include context')) bareSourcePoint(site, inputs);
  }
  function sourceAnchor(value, inputs) {
    keys(value, ['spelling', 'expansions', 'includes'], ['generated_token']); sourcePoint(value.spelling, inputs);
    if (value.generated_token !== undefined) {
      string(value.generated_token, 'generated macro token');
      if (!value.generated_token.length || new TextEncoder().encode(value.generated_token).length > 4096 ||
          !value.expansions.length) fail('invalid generated macro token anchor');
    }
    for (const frame of array(value.expansions, 'macro expansion frames')) {
      keys(frame, ['begin', 'end', 'caller']);
      for (const name of ['begin', 'end', 'caller']) sourcePoint(frame[name], inputs);
    }
    for (const point of array(value.includes, 'include chain')) sourcePoint(point, inputs);
  }
  function type(value, declarations) {
    keys(value, ['kind', 'spelling', 'aliases', 'size_bits', 'alignment_bits'],
      ['record_id', 'element', 'count', 'flexible', 'pointee', 'bound_kind']);
    string(value.spelling, 'type spelling');
    for (const number of ['size_bits', 'alignment_bits']) if (value[number] !== null) integer(value[number], number, number === 'alignment_bits' ? 1 : 0);
    const aliases = array(value.aliases, 'type aliases'); unique(aliases, 'type alias');
    for (const id of aliases) if (declarations.get(id)?.kind !== 'alias') fail('dangling alias reference');
    if (value.kind === 'array') {
      if (!Object.hasOwn(value, 'element') || !Object.hasOwn(value, 'count') || !Object.hasOwn(value, 'flexible')) fail('incomplete array type');
      bool(value.flexible, 'flexible');
      if (value.bound_kind !== (value.count === null ? 'incomplete' : 'constant')) fail('array bound kind mismatch');
      if (value.count !== null) integer(value.count, 'array count');
      if ((value.count === null) !== value.flexible) fail('unknown array bounds are supported only for flexible tails');
      type(value.element, declarations);
    } else if (value.kind === 'record') {
      if (!['struct', 'union'].includes(declarations.get(value.record_id)?.kind)) fail('dangling record reference');
    } else if (value.kind === 'pointer') {
      if (!Object.hasOwn(value, 'pointee')) fail('pointer target metadata missing');
      type(value.pointee, declarations);
    } else if (value.kind !== 'scalar') fail('unknown type kind');
    const specific = {array: ['element', 'count', 'flexible', 'bound_kind'], record: ['record_id'], pointer: ['pointee'], scalar: []}[value.kind];
    for (const name of ['element', 'count', 'flexible', 'record_id', 'pointee', 'bound_kind'])
      if (Object.hasOwn(value, name) && !specific.includes(name)) fail('type kind/key mismatch');
  }
  function assertRequest(request) {
    object(request, 'request'); keys(request, ['target', 'main', 'files'], REQUEST_KEYS.filter(k => !['target', 'main', 'files'].includes(k)));
    string(request.target, 'target'); string(request.main, 'main'); object(request.files, 'files');
    for (const [path, value] of Object.entries(request.files)) {
      if (!path.startsWith('/inputs/') || /[\0\r\n\\]/.test(path) || path.split('/').some(s => s === '.' || s === '..')) fail('invalid virtual path');
      string(value, 'file bytes');
    }
    if (!Object.hasOwn(request.files, request.main)) fail('missing main input');
    guardUBC(request, Object.keys(request.files));
    object(request.macros || {}, 'request macros');
    for (const [name, value] of Object.entries(request.macros || {})) {
      if (!macroPattern.test(name)) fail('invalid macro name');
      if (value !== null && (typeof value !== 'string' || /[\r\n\0]/.test(value))) fail('invalid macro value');
    }
  }
  function resolution(base, overrides, policy = {}, options = {}) {
    assertRequest(base); object(overrides, 'overrides');
    if (policy.contract) keys(policy, ['contract', 'version', 'id', 'label', 'editable', 'derived', 'compiler_reserved_prefixes', 'constraints', 'baseline']);
    else keys(policy, [], ['id', 'editable', 'derived', 'constraints', 'compiler_reserved_prefixes']);
    const editable = policy.editable || [], derived = policy.derived || [];
    unique(array(editable, 'editable names'), 'editable name'); unique(array(derived, 'derived names'), 'derived name');
    const issues = [], protectedChanges = [];
    for (const [name, value] of Object.entries(overrides)) {
      const changed = !Object.hasOwn(base.macros || {}, name) || base.macros[name] !== value;
      if (!changed) continue;
      if (requiresPAC(base) && name === '__arm64e__' && value !== '1') issues.push('Mandatory iOS PAC context requires __arm64e__=1; this directive could remove PAC-dependent fields.');
      if (!macroPattern.test(name) || (value !== null && (typeof value !== 'string' || /[\0\r\n]/.test(value)))) issues.push('Invalid macro directive: ' + name);
      if (!options.whatIf && (policy.compiler_reserved_prefixes || ['__']).some(prefix => name.startsWith(prefix))) issues.push('Compiler-reserved macro cannot be edited: ' + name);
      if (derived.includes(name) || !editable.includes(name)) protectedChanges.push(name);
    }
    const request = {...copy(base), macros: {...(base.macros || {}), ...overrides}};
    guardUBC(request, Object.keys(request.files));
    for (const constraint of policy.constraints || []) {
      keys(constraint, ['name', 'values']);
      if (!macroPattern.test(constraint.name)) fail('invalid constraint name');
      if (!constraint.values.some(value => canonical(value?.state ? value : state(value)) === canonical(state(request.macros[constraint.name] ?? null)))) issues.push('Constraint rejected ' + constraint.name);
    }
    if (protectedChanges.length && !options.whatIf) issues.push('Protected/derived macro edits require explicit what-if analysis');
    const changed = Object.entries(overrides).some(([name, value]) => !Object.hasOwn(base.macros || {}, name) || base.macros[name] !== value);
    return {request, resolution: {status: issues.length ? 'invalid-configuration' : options.whatIf || changed ? 'what-if' : 'validated',
      policy_id: policy.id || null, protected_changes: protectedChanges.sort(), issues}};
  }
  async function bindingFor(request, result) {
    let parsed = true; try {assertRequest(request);} catch (_) {parsed = false;}
    const inputs = parsed ? await Promise.all(Object.entries(request.files).sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(async ([path, bytes]) => ({
      path, source_path: request.source_paths?.[path] || path, sha256: await sha256(bytes), bytes: new TextEncoder().encode(bytes).length}))) : [];
    const requested = parsed ? Object.fromEntries(Object.entries(copy(request)).filter(([key]) => key !== 'files')) : null;
    if (requested) requested.macros = Object.fromEntries(Object.entries(request.macros || {}).sort().map(([k, v]) => [k, state(v)]));
    const effective = {compiler: result.compiler || null, frontend_options: result.options || null,
      target: result.target || null, driver_target: result.driver_target || null,
      macros: Object.fromEntries(Object.entries(result.effective_macros || {}).sort().map(([k, v]) => [k, state(v, true)]))};
    return {requested, submitted_request: parsed ? null : request, inputs, effective};
  }
  const baselineFor = binding => ({requested: binding.requested, inputs: binding.inputs,
    compiler: binding.effective.compiler, frontend_options: binding.effective.frontend_options});
  async function createPolicy(request, result, settings = {}) {
    const binding = await bindingFor(request, result);
    const policy = {...header('configuration-policy'), label: settings.label || null,
      editable: settings.editable || [], derived: settings.derived || Object.entries(result.effective_macros || {})
        .filter(([, value]) => value?.location?.file).map(([name]) => name).sort(),
      compiler_reserved_prefixes: ['__'], constraints: settings.constraints || [], baseline: baselineFor(binding)};
    return {id: await identity('policy-v1', policy), ...policy};
  }
  function contextShape(context) {
    keys(context, ['requested', 'inputs', 'compiler', 'frontend_options']);
    const paths = new Set();
    for (const input of array(context.inputs, 'baseline inputs')) {
      keys(input, ['path', 'source_path', 'sha256', 'bytes']);
      string(input.path, 'input path'); string(input.source_path, 'physical source path'); integer(input.bytes, 'input bytes');
      if (!input.path.startsWith('/inputs/') || input.path.split('/').some(p => p === '.' || p === '..') || !input.source_path || /[\0\r\n\\]/.test(input.source_path) || paths.has(input.path) || !hashPattern.test(input.sha256)) fail('invalid baseline input identity');
      paths.add(input.path);
    }
    if (context.requested !== null) {
      const requested = context.requested;
      keys(requested, ['target', 'main', 'macros'], REQUEST_KEYS.filter(k => !['target', 'main', 'files', 'macros'].includes(k)));
      string(requested.target, 'baseline target'); string(requested.main, 'baseline main');
      if (!paths.has(requested.main)) fail('baseline main missing from inputs');
      for (const [name, value] of Object.entries(object(requested.macros, 'baseline macros'))) {
        if (!macroPattern.test(name)) fail('invalid baseline macro name'); macroState(value, false);
      }
      for (const key of ['include_dirs', 'forced_includes', 'records', 'observe_macros', 'target_features', 'dependency_files'])
        if (Object.hasOwn(requested, key)) for (const value of array(requested[key], key)) string(value, key);
      for (const key of ['blocks', 'kernel_mode', 'ptrauth_intrinsics', 'ptrauth_calls', 'trace_files', 'trace_dependencies']) if (Object.hasOwn(requested, key)) bool(requested[key], key);
      for (const key of ['target_cpu', 'target_arch', 'language']) if (Object.hasOwn(requested, key)) string(requested[key], key);
      if (requested.source_paths) for (const [path, value] of Object.entries(object(requested.source_paths, 'source paths')))
        if (!paths.has(path) || context.inputs.find(input => input.path === path).source_path !== value) fail('invalid baseline source path');
    }
    if (context.compiler !== null) {
      keys(context.compiler, ['version', 'revision', 'engine_sha256']);
      for (const value of Object.values(context.compiler)) string(value, 'compiler identity');
      if (!hashPattern.test(context.compiler.engine_sha256)) fail('invalid engine source hash');
    }
    if (context.frontend_options !== null) for (const value of array(context.frontend_options, 'frontend options')) string(value, 'frontend option');
  }
  async function validatePolicy(policy) {
    keys(policy, ['contract', 'version', 'id', 'label', 'editable', 'derived', 'compiler_reserved_prefixes', 'constraints', 'baseline']);
    version(policy, 'configuration-policy');
    if (policy.label !== null) string(policy.label, 'policy label');
    for (const key of ['editable', 'derived', 'compiler_reserved_prefixes']) {
      unique(array(policy[key], key), key);
      for (const name of policy[key]) if (typeof name !== 'string' || !macroPattern.test(name)) fail('invalid policy name/prefix');
    }
    if (!policy.compiler_reserved_prefixes.includes('__')) fail('compiler-reserved prefix protection missing');
    if (policy.editable.some(name => policy.derived.includes(name) || policy.compiler_reserved_prefixes.some(prefix => name.startsWith(prefix))))
      fail('editable settings overlap derived/compiler settings');
    for (const constraint of array(policy.constraints, 'policy constraints')) {
      keys(constraint, ['name', 'values']); if (!policy.editable.includes(constraint.name)) fail('constraint is not an editable setting');
      for (const value of array(constraint.values, 'constraint values')) macroState(value, false);
      unique(constraint.values.map(canonical), 'constraint value');
      if (!constraint.values.length || !constraint.values.some(value => canonical(value) === canonical(policy.baseline.requested?.macros?.[constraint.name] || {state: 'undefined'}))) fail('policy baseline violates constraint');
    }
    contextShape(policy.baseline);
    const {id, ...material} = policy;
    if (id !== await identity('policy-v1', material)) fail('configuration policy hash mismatch');
  }
  function normalizeType(type) {
    const result = copy(type);
    if (result.kind === 'array') {result.bound_kind = result.count === null ? 'incomplete' : 'constant'; result.element = normalizeType(result.element);}
    if (result.kind === 'pointer') result.pointee = normalizeType(result.pointee);
    return result;
  }
  function resolvedPolicy(binding, policy, classification) {
    const current = binding.requested?.macros || {}, baseline = policy.baseline.requested?.macros || {};
    const changes = [...new Set([...Object.keys(current), ...Object.keys(baseline)])]
      .filter(name => canonical(current[name] || {state: 'undefined'}) !== canonical(baseline[name] || {state: 'undefined'}));
    const issues = [];
    for (const name of changes) if (classification !== 'what-if' && policy.compiler_reserved_prefixes.some(prefix => name.startsWith(prefix))) issues.push('Compiler-reserved macro cannot be edited: ' + name);
    for (const constraint of policy.constraints)
      if (!constraint.values.some(value => canonical(value) === canonical(current[constraint.name] || {state: 'undefined'}))) issues.push('Constraint rejected ' + constraint.name);
    const protectedChanges = changes.filter(name => policy.derived.includes(name) || !policy.editable.includes(name)).sort();
    if (protectedChanges.length && !['what-if', 'invalid'].includes(classification)) issues.push('Protected/derived macro edits require explicit what-if analysis');
    if (classification === 'what-if') {
      const context = requested => requested === null ? null : Object.fromEntries(Object.entries(requested).filter(([key]) => !['macros', 'observe_macros'].includes(key)));
      if (canonical(context(binding.requested)) !== canonical(context(policy.baseline.requested)) || canonical(binding.inputs) !== canonical(policy.baseline.inputs) ||
          canonical(binding.effective.compiler) !== canonical(policy.baseline.compiler)) issues.push('What-if macro policy does not authorize compiler/source context edits');
    }
    return {status: issues.length || classification === 'invalid' ? 'invalid-configuration' : classification === 'what-if' ? 'what-if' : 'validated',
      policy_id: policy.id, protected_changes: protectedChanges, issues};
  }
  async function create(request, result, metadata = {}) {
    if (request?.files && typeof request.files === 'object') guardUBC(request, Object.keys(request.files));
    if (result.schema !== 2 || !Object.hasOwn(STATUSES, result.status)) fail('transport schema/status unsupported');
    const binding = await bindingFor(request, result);
    if (metadata.profile && !metadata.policy) fail('validated profile requires an explicit baseline policy');
    const policy = metadata.policy || await createPolicy(request, result);
    await validatePolicy(policy);
    const matchesBaseline = canonical(policy.baseline) === canonical(baselineFor(binding));
    const classification = result.status === 'invalid-request' ? 'invalid' : metadata.whatIf ? 'what-if' : metadata.profile ? 'validated-profile' : 'analysis';
    if (classification === 'validated-profile' && (!matchesBaseline || policy.label !== metadata.profile)) fail('profile differs from validated baseline policy');
    const resolution = resolvedPolicy(binding, policy, classification);
    if (metadata.resolution && canonical(metadata.resolution) !== canonical(resolution)) fail('configuration resolution differs from policy');
    if (resolution.issues.length && result.status !== 'invalid-request') fail('configuration violates persisted policy: ' + resolution.issues.join('; '));
    const configID = await identity('config-v1', {...binding, policy});
    const configuration = {...header('configuration'), id: configID, classification, profile: metadata.profile || null,
      context: binding.effective.compiler && binding.requested ? 'complete' : 'partial', ...binding, policy, resolution};
    const entries = [], variants = [];
    for (const declaration of result.declarations || []) {
      const {complete, underlying_type, ...entry} = declaration;
      entries.push(copy(entry));
      const variant = {declaration_id: entry.id, configuration_id: configID,
        complete: complete ?? null, underlying_type: underlying_type ? normalizeType(underlying_type) : null};
      variants.push({id: await identity('variant-v1', variant), ...variant});
    }
    const layouts = [];
    for (const record of result.records) {
      const layout = {declaration_id: record.id, configuration_id: configID,
        size_bytes: record.size_bytes, alignment_bytes: record.alignment_bytes,
        fields: record.fields.map(({id, offset_bits, bit_width, anonymous_record, type: fieldType}, index) => ({
          declaration_id: id, presence: 'present', offset_bits, bit_width, anonymous_record,
          flexible_tail: fieldType.kind === 'array' && fieldType.count === null && index === record.fields.length - 1, type: normalizeType(fieldType)}))};
      layouts.push({id: await identity('layout-v1', layout), ...layout});
    }
    const diagnostics = [];
    for (const [sequence, diagnostic] of result.diagnostics.entries()) {
      const entry = {sequence, severity: diagnostic.severity, message: diagnostic.message,
        compiler_code: diagnostic.id ?? null, location: diagnostic.location && Object.keys(diagnostic.location).length ? diagnostic.location : null};
      diagnostics.push({id: await identity('diagnostic-v1', entry), ...entry});
    }
    const document = {...header('layout-set'), source: metadata.source || {release: null, revision: null}, configuration,
      declarations: {...header('declarations'), entries, variants},
      layouts: {...header('layouts'), status: STATUSES[result.status], units: {size: 'bytes', alignment: 'bytes', offset: 'bits', bit_width: 'bits'}, entries: layouts},
      dependencies: {...header('dependencies'), status: 'not-computed', coverage: 'unknown', configuration_ids: [configID], relations: []},
      diagnostics: {...header('diagnostics'), entries: diagnostics}};
    await validate(document);
    return document;
  }
  const dependencyAnalyses = new Map();
  const dependencyAPI = () => typeof module === 'object' && module.exports ? require('./dependencies.js') : globalThis.LayoutDependencies;
  async function registerDependencyAnalysis(analysis) {
    await dependencyAPI().validate(analysis); dependencyAnalyses.set(analysis.id, analysis); return analysis;
  }
  async function validate(document, options = {}) {
    canonical(document); // Reject floats, unsafe integers, undefined and exotic objects everywhere.
    keys(document, ['contract', 'version', 'source', 'configuration', 'declarations', 'layouts', 'dependencies', 'diagnostics']);
    version(document, 'layout-set');
    keys(document.source, ['release', 'revision']);
    for (const value of Object.values(document.source)) if (value !== null) string(value, 'source identity');
    const c = document.configuration;
    keys(c, ['contract', 'version', 'id', 'classification', 'profile', 'context', 'requested', 'submitted_request', 'inputs', 'effective', 'policy', 'resolution']);
    version(c, 'configuration');
    if (!['validated-profile', 'what-if', 'analysis', 'invalid'].includes(c.classification)) fail('unknown configuration classification');
    if (!['complete', 'partial'].includes(c.context)) fail('unknown context completeness');
    if (c.profile !== null) string(c.profile, 'profile');
    const inputs = new Map();
    for (const input of array(c.inputs, 'inputs')) {
      keys(input, ['path', 'source_path', 'sha256', 'bytes']);
      string(input.path, 'input path'); string(input.source_path, 'source path'); integer(input.bytes, 'input bytes');
      if (!hashPattern.test(input.sha256) || inputs.has(input.path)) fail('invalid/duplicate input identity');
      inputs.set(input.path, input);
    }
    if (c.requested !== null) {
      keys(c.requested, ['target', 'main', 'macros'], REQUEST_KEYS.filter(k => !['target', 'main', 'files', 'macros'].includes(k)));
      if (c.submitted_request !== null) fail('complete request also has unparsed request');
      string(c.requested.target, 'requested target'); string(c.requested.main, 'main');
      if (!inputs.has(c.requested.main)) fail('requested main missing from inputs');
      for (const [name, value] of Object.entries(object(c.requested.macros, 'requested macros'))) {
        if (!macroPattern.test(name)) fail('invalid requested macro name'); macroState(value, false);
      }
      for (const name of ['include_dirs', 'forced_includes', 'target_features', 'records', 'observe_macros'])
        if (Object.hasOwn(c.requested, name)) for (const value of array(c.requested[name], name)) string(value, name);
      for (const name of ['blocks', 'kernel_mode', 'ptrauth_intrinsics', 'ptrauth_calls', 'trace_files', 'trace_dependencies']) if (Object.hasOwn(c.requested, name)) bool(c.requested[name], name);
      for (const name of ['target_cpu', 'target_arch', 'language']) if (Object.hasOwn(c.requested, name)) string(c.requested[name], name);
      if (c.requested.source_paths) for (const [path, physical] of Object.entries(object(c.requested.source_paths, 'source paths')))
        if (inputs.get(path)?.source_path !== physical) fail('source-path map differs from inputs');
    }
    keys(c.effective, ['compiler', 'frontend_options', 'target', 'driver_target', 'macros']);
    if (c.effective.compiler !== null) {
      keys(c.effective.compiler, ['version', 'revision', 'engine_sha256']);
      if (!hashPattern.test(c.effective.compiler.engine_sha256)) fail('invalid compiler wrapper hash');
      for (const value of Object.values(c.effective.compiler)) string(value, 'compiler identity');
    }
    if (c.effective.frontend_options !== null)
      for (const option of array(c.effective.frontend_options, 'frontend options')) string(option, 'frontend option');
    if (c.effective.target !== null) string(c.effective.target, 'effective target');
    if (c.effective.driver_target !== null) {
      keys(c.effective.driver_target, ['cpu', 'features', 'source_option']);
      string(c.effective.driver_target.cpu, 'CPU'); string(c.effective.driver_target.source_option, 'source target option');
      for (const feature of array(c.effective.driver_target.features, 'driver features')) string(feature, 'driver feature');
    }
    for (const [name, value] of Object.entries(object(c.effective.macros, 'effective macros'))) {
      if (!macroPattern.test(name)) fail('invalid effective macro name'); macroState(value, true);
    }
    if (c.context === 'complete' && (!c.effective.compiler || !c.requested || !c.effective.frontend_options)) fail('fabricated complete compiler context');
    keys(c.resolution, ['status', 'policy_id', 'protected_changes', 'issues']);
    if (!['validated', 'what-if', 'invalid-configuration'].includes(c.resolution.status)) fail('unknown resolution status');
    if (c.resolution.policy_id !== null) string(c.resolution.policy_id, 'policy ID');
    for (const key of ['protected_changes', 'issues']) for (const value of array(c.resolution[key], key)) string(value, key);
    if (c.classification === 'validated-profile' && (!c.profile || c.resolution.status !== 'validated' || c.resolution.issues.length || c.resolution.protected_changes.length))
      fail('unvalidated configuration labeled as profile');
    if (c.classification === 'what-if' && c.resolution.status !== 'what-if') fail('what-if resolution mismatch');
    contextShape(baselineFor(c));
    await validatePolicy(c.policy);
    if (c.resolution.policy_id !== c.policy.id) fail('resolution policy reference mismatch');
    const expectedResolution = resolvedPolicy(c, c.policy, c.classification);
    if (canonical(c.resolution) !== canonical(expectedResolution)) fail('persisted configuration resolution differs from policy');
    const binding = {requested: c.requested, submitted_request: c.submitted_request, inputs: c.inputs, effective: c.effective, policy: c.policy};
    if (c.classification === 'validated-profile' && (c.policy.label !== c.profile ||
        canonical(c.policy.baseline) !== canonical(baselineFor(binding)))) fail('validated profile differs from policy baseline');
    if (c.id !== await identity('config-v1', binding)) fail('configuration hash mismatch');
    const d = document.declarations;
    keys(d, ['contract', 'version', 'entries', 'variants']); version(d, 'declarations');
    const declarations = new Map();
    const barePointKey = p => new TextEncoder().encode(p.source_path).length + ':' + p.source_path + ':' + p.sha256 + ':' + p.offset_bytes;
    const pointKey = p => barePointKey(p) + p.include_sites.map(site => '|via:' + barePointKey(site)).join('');
    const anchorKey = a => pointKey(a.spelling) + a.expansions.map(f => '|begin:' + pointKey(f.begin) + '|end:' + pointKey(f.end) + '|caller:' + pointKey(f.caller)).join('') +
      a.includes.map(p => '|include:' + pointKey(p)).join('') +
      (a.generated_token === undefined ? '' : '|generated-token:' + new TextEncoder().encode(a.generated_token).length + ':' + a.generated_token);
    for (const entry of array(d.entries, 'declarations')) {
      keys(entry, ['id', 'kind', 'ast_kind', 'name', 'source', 'scope'], ['owner_id']);
      if (!declarationPattern.test(entry.id) || declarations.has(entry.id)) fail('invalid/duplicate declaration identity');
      if (!['struct', 'union', 'field', 'alias'].includes(entry.kind)) fail('unknown declaration kind');
      string(entry.name, 'declaration name'); string(entry.ast_kind, 'AST kind');
      sourceAnchor(entry.source, inputs);
      let material = entry.ast_kind + '|' + anchorKey(entry.source);
      for (const scope of array(entry.scope, 'lexical scopes')) {
        keys(scope, ['kind', 'source']); string(scope.kind, 'scope kind'); sourceAnchor(scope.source, inputs);
        material += '|scope:' + scope.kind + ':' + anchorKey(scope.source);
      }
      if (entry.id !== 'decl-v1:' + await sha256(material)) fail('declaration source identity mismatch');
      declarations.set(entry.id, entry);
    }
    for (const entry of declarations.values()) {
      if (entry.kind === 'field') {
        if (!['struct', 'union'].includes(declarations.get(entry.owner_id)?.kind)) fail('dangling field owner');
      } else if (Object.hasOwn(entry, 'owner_id')) fail('non-field has field owner');
    }
    const variants = new Map();
    for (const variant of array(d.variants, 'declaration variants')) {
      keys(variant, ['id', 'declaration_id', 'configuration_id', 'complete', 'underlying_type']);
      if (!declarations.has(variant.declaration_id) || variant.configuration_id !== c.id || variants.has(variant.declaration_id)) fail('invalid/duplicate declaration variant');
      const {id, ...material} = variant;
      if (id !== await identity('variant-v1', material)) fail('declaration variant hash mismatch');
      if (declarations.get(variant.declaration_id).kind === 'alias') {
        if (variant.complete !== null || variant.underlying_type === null) fail('invalid alias variant');
        type(variant.underlying_type, declarations);
      } else {
        if (variant.underlying_type !== null) fail('non-alias has alias underlying type');
        if (['struct', 'union'].includes(declarations.get(variant.declaration_id).kind)) bool(variant.complete, 'record completeness');
        else if (variant.complete !== null) fail('field has record completeness');
      }
      variants.set(variant.declaration_id, variant);
    }
    if (variants.size !== declarations.size) fail('missing declaration variants');
    const l = document.layouts;
    keys(l, ['contract', 'version', 'status', 'units', 'entries']); version(l, 'layouts');
    if (!Object.values(STATUSES).includes(l.status)) fail('unknown result status');
    if (canonical(l.units) !== canonical({size: 'bytes', alignment: 'bytes', offset: 'bits', bit_width: 'bits'})) fail('ambiguous layout units');
    const layouts = new Map();
    for (const layout of array(l.entries, 'layouts')) {
      keys(layout, ['id', 'declaration_id', 'configuration_id', 'size_bytes', 'alignment_bytes', 'fields']);
      const declaration = declarations.get(layout.declaration_id);
      if (!declaration || !['struct', 'union'].includes(declaration.kind) || layouts.has(layout.declaration_id) ||
          layout.configuration_id !== c.id || !variants.get(layout.declaration_id).complete) fail('invalid layout reference');
      integer(layout.size_bytes, 'structure size'); integer(layout.alignment_bytes, 'structure alignment', 1);
      if (!Number.isSafeInteger(layout.size_bytes * 8)) fail('structure bit size is unsafe');
      unique(array(layout.fields, 'fields').map(f => f.declaration_id), 'field layout');
      for (const field of layout.fields) {
        keys(field, ['declaration_id', 'presence', 'offset_bits', 'bit_width', 'anonymous_record', 'flexible_tail', 'type']);
        if (declarations.get(field.declaration_id)?.owner_id !== layout.declaration_id || field.presence !== 'present') fail('invalid field presence/owner');
        integer(field.offset_bits, 'field offset'); bool(field.anonymous_record, 'anonymous record'); bool(field.flexible_tail, 'flexible tail');
        if (field.flexible_tail !== (field.type.kind === 'array' && field.type.count === null && field === layout.fields.at(-1))) fail('flexible tail context mismatch');
        if (field.bit_width !== null) integer(field.bit_width, 'bit-field width');
        type(field.type, declarations);
        const occupied = field.bit_width ?? field.type.size_bits ?? 0;
        if (field.offset_bits > layout.size_bytes * 8 || occupied > layout.size_bytes * 8 - field.offset_bits) fail('field exceeds structure storage');
        if (declaration.kind === 'union' && field.offset_bits !== 0) fail('union member does not overlap at zero');
      }
      const {id, ...material} = layout;
      if (id !== await identity('layout-v1', material)) fail('layout hash mismatch');
      layouts.set(layout.declaration_id, layout);
    }
    function checkType(value, requireEmbedded) {
      if (value.kind === 'record') {
        const referenced = layouts.get(value.record_id);
        if (requireEmbedded && !referenced) fail('missing embedded-record layout');
        if (referenced && (value.size_bits !== referenced.size_bytes * 8)) fail('record type/layout dimensions disagree');
      } else if (value.kind === 'array') {
        checkType(value.element, requireEmbedded);
        if (value.count !== null) {
          const size = value.count * value.element.size_bits;
          if (value.element.size_bits === null || !Number.isSafeInteger(size) || value.size_bits !== size) fail('array dimensions/stride disagree');
        }
      } else if (value.kind === 'pointer') checkType(value.pointee, false);
    }
    for (const layout of layouts.values()) for (const field of layout.fields) checkType(field.type, true);
    for (const variant of variants.values()) if (variant.underlying_type) checkType(variant.underlying_type, false);
    const active = new Set(), visited = new Set();
    function walk(id) {
      if (active.has(id)) fail('embedded record cycle');
      if (visited.has(id)) return; active.add(id);
      function children(t) {if (t.kind === 'record') walk(t.record_id); else if (t.kind === 'array') children(t.element);}
      for (const field of layouts.get(id).fields) children(field.type);
      active.delete(id); visited.add(id);
    }
    for (const id of layouts.keys()) walk(id);
    const aliasActive = new Set(), aliasVisited = new Set();
    function aliasWalk(id) {
      if (aliasActive.has(id)) fail('alias cycle');
      if (aliasVisited.has(id)) return; aliasActive.add(id);
      function references(t) {
        for (const alias of t.aliases) aliasWalk(alias);
        if (t.kind === 'array') references(t.element); else if (t.kind === 'pointer') references(t.pointee);
      }
      references(variants.get(id).underlying_type); aliasActive.delete(id); aliasVisited.add(id);
    }
    for (const declaration of declarations.values()) if (declaration.kind === 'alias') aliasWalk(declaration.id);
    const deps = document.dependencies;
    if (deps.version === 2) {
      keys(deps, ['contract', 'version', 'status', 'coverage', 'configuration_ids', 'analysis_id', 'roots']);
      if (deps.contract !== 'platydoc.dependencies' || deps.status !== 'partial' || deps.coverage !== 'partial' || canonical(deps.configuration_ids) !== canonical([c.id]) || canonical(deps.roots) !== canonical(l.entries.map(entry => entry.declaration_id).sort())) fail('invalid dependency reference');
      const analysis = options.analysis || dependencyAnalyses.get(deps.analysis_id);
      if (!analysis || analysis.id !== deps.analysis_id) fail('missing shared dependency analysis');
      await dependencyAPI().validate(analysis, [document]);
    } else {
    keys(deps, ['contract', 'version', 'status', 'coverage', 'configuration_ids', 'relations']); version(deps, 'dependencies');
    if (!['not-computed', 'partial', 'complete'].includes(deps.status) || !['unknown', 'partial', 'declared-complete'].includes(deps.coverage)) fail('unknown dependency coverage');
    unique(array(deps.configuration_ids, 'dependency configurations'), 'dependency configuration');
    if (!deps.configuration_ids.includes(c.id) || deps.configuration_ids.some(id => !/^config-v1:[a-f0-9]{64}$/.test(id))) fail('invalid dependency configuration reference');
    if (deps.coverage !== {'not-computed': 'unknown', partial: 'partial', complete: 'declared-complete'}[deps.status]) fail('dependency status/coverage mismatch');
    if (deps.status === 'not-computed' && (deps.coverage !== 'unknown' || deps.relations.length)) fail('uncomputed dependency claims');
    const relationIDs = [];
    for (const relation of array(deps.relations, 'dependencies')) {
      keys(relation, ['id', 'from', 'to', 'kind', 'evidence']); relationIDs.push(relation.id);
      if (!declarations.has(relation.to)) fail('dangling dependency target');
      if (relation.from.kind === 'macro') {
        keys(relation.from, ['kind', 'name']);
        if (!Object.hasOwn(c.requested?.macros || {}, relation.from.name) && !Object.hasOwn(c.effective.macros, relation.from.name)) fail('unobserved dependency macro');
      } else {
        keys(relation.from, ['kind', 'id']);
        if (relation.from.kind !== 'declaration' || !declarations.has(relation.from.id)) fail('dangling dependency origin');
      }
      if (!['potential-layout', 'observed-layout-change', 'embedded-storage', 'pointer-reference', 'alias-resolution'].includes(relation.kind)) fail('unknown dependency relation');
      if (!array(relation.evidence, 'dependency evidence').length) fail('dependency lacks evidence');
      for (const evidence of relation.evidence) {
        keys(evidence, ['source', 'configurations', 'description']); string(evidence.description, 'evidence description');
        if (evidence.source !== null) sourceAnchor(evidence.source, inputs);
        const configurations = array(evidence.configurations, 'evidence configurations'); unique(configurations, 'evidence configuration');
        if (!configurations.length || configurations.some(id => !deps.configuration_ids.includes(id))) fail('dangling evidence configuration');
        if (relation.kind === 'observed-layout-change' && configurations.length < 2) fail('layout change requires comparative evidence');
        if (evidence.source === null && configurations.length < 2) fail('dependency evidence has no source or comparison');
      }
      const {id, ...material} = relation;
      if (id !== await identity('dependency-v1', material)) fail('dependency relation hash mismatch');
    }
    unique(relationIDs, 'dependency relation');
    }
    const diagnostics = document.diagnostics;
    keys(diagnostics, ['contract', 'version', 'entries']); version(diagnostics, 'diagnostics');
    for (const [sequence, entry] of array(diagnostics.entries, 'diagnostics').entries()) {
      keys(entry, ['id', 'sequence', 'severity', 'message', 'compiler_code', 'location']);
      if (entry.sequence !== sequence || !['note', 'warning', 'error', 'fatal'].includes(entry.severity)) fail('invalid diagnostic sequence/severity');
      string(entry.message, 'diagnostic message');
      if (entry.compiler_code !== null) integer(entry.compiler_code, 'compiler diagnostic code');
      if (entry.location !== null) location(entry.location);
      const {id, ...material} = entry;
      if (id !== await identity('diagnostic-v1', material)) fail('diagnostic hash mismatch');
    }
    const hasError = diagnostics.entries.some(d => ['error', 'fatal'].includes(d.severity));
    guardUBC(c.requested, [...inputs.keys()], l.status === 'success' ? {declarations: d, layouts: l} : null);
    if (l.status === 'success') validateMandatoryPAC(c);
    if (l.status === 'success' && (hasError || c.context !== 'complete' || c.resolution.status === 'invalid-configuration')) fail('success has errors/incomplete context');
    if (l.status !== 'success' && (l.entries.length || d.entries.length || !hasError)) fail('failure publishes trusted layouts/declarations or lacks an error');
    if (l.status === 'invalid-configuration' && c.classification !== 'invalid') fail('invalid status/configuration mismatch');
    return document;
  }
  function resolvePath(document, rootDeclarationId, steps, options = {}) {
    const layouts = new Map(document.layouts.entries.map(l => [l.declaration_id, l]));
    const declarations = new Map(document.declarations.entries.map(d => [d.id, d]));
    if (document.layouts.status !== 'success' || !layouts.has(rootDeclarationId)) fail('root layout unavailable');
    let current = {kind: 'record', record_id: rootDeclarationId}, root = 0, local = 0, fieldID = null;
    let flexible = false, bounds = 'static', unions = [];
    const add = n => {integer(n, 'relative bit offset'); if (!Number.isSafeInteger(root + n)) fail('root offset overflow'); root += n;};
    for (const step of array(steps, 'path steps')) {
      if (current.kind === 'pointer') fail('pointer boundary: pointee is a separate object');
      if (current.kind === 'record') {
        const layout = layouts.get(current.record_id);
        if (!layout) fail('embedded layout unavailable');
        const matches = layout.fields.filter(f => f.declaration_id === step || declarations.get(f.declaration_id).name === step);
        if (matches.length !== 1) fail('unknown or ambiguous field step');
        const field = matches[0]; fieldID = field.declaration_id; local = field.offset_bits; add(local);
        if (declarations.get(current.record_id).kind === 'union') unions.push({declaration_id: current.record_id, field_id: fieldID});
        current = field.type; flexible ||= field.flexible_tail;
      } else if (current.kind === 'array') {
        keys(step, ['index']); integer(step.index, 'array index');
        let count = current.count;
        if (count === null) {
          count = options.runtimeLengths?.[fieldID];
          if (count === undefined && !options.allowFlexiblePreview) fail('flexible-array index requires runtime length or explicit preview');
          if (count === undefined) bounds = 'runtime-unchecked-preview'; else {integer(count, 'runtime array length'); bounds = 'runtime-length-supplied';}
        }
        if (count !== undefined && count !== null && step.index >= count) fail('array index out of bounds');
        if (!Number.isSafeInteger(current.element.size_bits)) fail('array stride unavailable');
        local = step.index * current.element.size_bits; add(local); current = current.element;
      } else fail('scalar field has no embedded children');
    }
    return {root_offset_bits: root, local_offset_bits: local, field_id: fieldID, type: current,
      pointer_boundary: current.kind === 'pointer', union_members: unions, flexible_tail: flexible, bounds};
  }
  function mergePresence(documents) {
    const definitions = new Map(), fields = new Map(), configurations = [], immutable = new Map();
    for (const document of documents) {
      const config = document.configuration.id; configurations.push(config);
      if (document.layouts.status !== 'success') continue;
      for (const declaration of document.declarations.entries) {
        const previous = immutable.get(declaration.id);
        if (previous && canonical(previous) !== canonical(declaration)) fail('conflicting declaration identity across configurations');
        immutable.set(declaration.id, declaration);
      }
      for (const declaration of document.declarations.entries)
        if (declaration.kind === 'field') fields.set(declaration.id, declaration.owner_id);
      for (const layout of document.layouts.entries) {
        if (!definitions.has(layout.declaration_id)) definitions.set(layout.declaration_id, new Map());
        definitions.get(layout.declaration_id).set(config, new Set(layout.fields.map(f => f.declaration_id)));
      }
    }
    unique(configurations, 'configuration in presence matrix');
    return [...fields].sort(([a], [b]) => a < b ? -1 : a > b ? 1 : 0).map(([field, owner]) => ({
      declaration_id: field, owner_id: owner, configurations: Object.fromEntries(configurations.map(config => {
        const observed = definitions.get(owner)?.get(config);
        return [config, !observed ? 'unknown' : observed.has(field) ? 'present' : 'absent'];
      }))}));
  }
  function mapChapters(document, mapping, options = {}) {
    keys(mapping, ['contract', 'version', 'source', 'entries']); version(mapping, 'layout-chapters');
    if (canonical(mapping.source) !== canonical(document.source)) fail('chapter mapping source release mismatch');
    const bindings = [], selectors = [];
    for (const entry of array(mapping.entries, 'chapter mapping entries')) {
      keys(entry, ['source_path', 'source_sha256', 'offset_bytes', 'kind', 'display_name', 'chapters']);
      string(entry.source_path, 'mapping source path'); string(entry.display_name, 'mapping display name'); integer(entry.offset_bytes, 'mapping byte anchor');
      if (!hashPattern.test(entry.source_sha256) || !['struct', 'union', 'alias'].includes(entry.kind)) fail('invalid chapter declaration selector');
      if (!array(entry.chapters, 'chapters').length) fail('chapter mapping has no destination');
      for (const chapter of entry.chapters)
        if (typeof chapter !== 'string' || !/^[A-Za-z0-9_/-]+\.md#[a-z0-9_-]+$/.test(chapter) || chapter.split('/').some(p => p === '..')) fail('invalid handbook chapter destination');
      selectors.push(canonical([entry.source_path, entry.source_sha256, entry.offset_bytes, entry.kind]));
      const found = document.declarations.entries.filter(declaration => declaration.kind === entry.kind &&
        declaration.source.spelling.source_path === entry.source_path && declaration.source.spelling.sha256 === entry.source_sha256 &&
        declaration.source.spelling.offset_bytes === entry.offset_bytes);
      if (found.length > 1 || (options.requireAll && found.length !== 1)) fail('chapter source selector is missing or ambiguous');
      if (found.length) bindings.push({declaration_id: found[0].id, chapters: copy(entry.chapters)});
    }
    unique(selectors, 'chapter selector');
    return {...header('chapter-bindings'), configuration_id: document.configuration.id, entries: bindings};
  }
  return {VERSION, canonical, sha256, createPolicy, create, validate, registerDependencyAnalysis, resolveConfiguration: resolution, resolvePath, mergePresence, mapChapters};
});
