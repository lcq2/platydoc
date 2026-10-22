// Run: node --test docs-ai/tools/book/tests/assets.test.mjs
// Executes the actual isolated book.js helpers/renderers. This is not a browser/layout test.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import vm from 'node:vm';
import { gzipSync, constants } from 'node:zlib';
import { randomBytes } from 'node:crypto';

const source = readFileSync(new URL('../assets/book.js', import.meta.url), 'utf8');
function implementation(name) {
  const pattern = new RegExp(`^([ \\t]*)(?:async )?function ${name}\\([^\\n]*\\) \\{\\n[\\s\\S]*?^\\1\\}`, 'm');
  const match = source.match(pattern);
  assert.ok(match, `Cannot locate production helper ${name}`);
  return match[0];
}
const fold = source.match(/^\s*const fold = .+;$/m)?.[0];
assert.ok(fold, 'Cannot locate production normalization helper');
const names = ['bookURL', 'searchable', 'queryParts', 'highlight', 'excerpt', 'renderResults', 'runSearch', 'base64Bytes', 'gunzip', 'unpack', 'sourceModel', 'sourceLine', 'sourceBytes', 'renderSource', 'loadFullSource', 'renderChapterNav', 'isStaticCodeBlock'];
const code = `${fold}\n${names.map(implementation).join('\n')}`;

// Minimal DOM surface for behavior checks. No HTML parser is provided: search rendering
// must preserve search and source strings as text, including markup-looking source literals.
class Element {
  constructor(tag) {
    this.tag = tag;
    this.children = [];
    this.attributes = {};
    this.listeners = {};
    this.className = '';
    this.dataset = {};
    this.classList = {
      add: name => { this.className += ` ${name}`; },
      contains: name => this.className.split(/\s+/).includes(name),
      remove: name => { this.className = this.className.split(/\s+/).filter(item => item !== name).join(' '); }
    };
  }
  append(...nodes) {
    for (const node of nodes) {
      if (node.tag === 'fragment') this.children.push(...node.children);
      else this.children.push(node);
    }
  }
  replaceChildren(...nodes) { this.children = []; this.append(...nodes); }
  set textContent(text) { this.children = [{ text: String(text) }]; }
  get textContent() { return this.children.map(node => node.text ?? node.textContent ?? '').join(''); }
  setAttribute(key, value) { this.attributes[key] = value; }
  removeAttribute(key) { delete this.attributes[key]; }
  before(node) { this.beforeNode = node; }
  addEventListener(key, handler) { this.listeners[key] = handler; }
  focus() { this.focused = true; }
}
function all(selector, scope) {
  const elements = [];
  function visit(node) {
    if (selector.startsWith('.') ? node.className?.split(/\s+/).includes(selector.slice(1)) : node.tag === selector) elements.push(node);
    for (const child of node.children || []) visit(child);
  }
  visit(scope);
  return elements;
}
function harness(rows = [], options = {}) {
  const context = {
    URL, Element, rows, root: new URL(options.root || 'file:///tmp/xnu-book/'),
    TextEncoder, TextDecoder, Blob, Response, atob, performance, setTimeout,
    DecompressionStream: options.native ? DecompressionStream : undefined,
    body: { dataset: { page: 'chapter.html' } },
    window: { addEventListener() {}, removeEventListener() {}, print() {} },
    say() {}, async copyText() { return true; },
    highlightSourceRange() {},
    document: {
      createElement: tag => new Element(tag),
      createDocumentFragment: () => new Element('fragment'),
      createTextNode: text => ({ text }),
      getElementById: () => null
    },
    $$: all,
    $: (selector, scope) => all(selector, scope)[0]
  };
  vm.createContext(context);
  vm.runInContext(`
    const searchInput = { value: '' };
    const searchResults = new Element('ol');
    const searchStatus = new Element('div');
    const searchPagination = new Element('div');
    let searchVersion = 0, matches = [], resultOffset = 0, visibleCount = 0, activeParts = [];
    const PAGE_SIZE = 20, DOM_LIMIT = 100;
    const sourceCode = new Element('div'), sourceMeta = new Element('p');
    const previous = new Element('button'), next = new Element('button');
    let sourceState = null, sourceFixture = null;
    ${code}
    async function getSearchRows() {
      return rows.map((row, index) => ({ row, index,
        title: searchable(row.title), heading: searchable(row.heading),
        chapter: searchable(row.chapter), text: searchable(row.text) }));
    }
    async function getSource() { return sourceFixture; }
    globalThis.subject = {
      bookURL, searchable, queryParts, highlight, excerpt, runSearch,
      sourceModel, sourceLine, sourceBytes, gunzip, unpack, renderChapterNav, isStaticCodeBlock,
      async fullSource(data, element) { sourceFixture = data; await loadFullSource(element); },
      searchResults, searchStatus, searchPagination, sourceCode, sourceMeta, previous, next,
      setQuery(value) { searchInput.value = value; },
      sourceWindow(state) { sourceState = state; renderSource(); }
    };
  `, context, { timeout: 1000 });
  return context.subject;
}

function row(number, overrides = {}) {
  return {
    title: `Runtime discussion ${number}`, chapter: 'Kernel runtime',
    heading: `Wait queue variant ${number}`,
    text: 'waitq_assert_wait64_locked records an abort-safe wait.',
    url: `runtime.html#variant-${number}`, ...overrides
  };
}
function payload(text, options = {}) {
  const lines = text ? text.split(/\r\n|\r|\n/) : [];
  if (/[\r\n]$/.test(text)) lines.pop();
  return {
    schema: 2, path: 'test.c', url: '_sources/test.c.html', language: 'C',
    styles: ['', 'kt', 'c1'], tokens: [[options.style || 0, text]],
    aliases: {}, line_count: lines.length, ...options
  };
}
function envelope(value, options = {}) {
  return { schema: 2, encoding: 'gzip-base64', data: gzipSync(JSON.stringify(value), options).toString('base64') };
}

test('identifiers, camel case, diacritics, quotes and query bounds', () => {
  const ui = harness();
  assert.ok(ui.searchable('waitq_assert_wait64_locked').includes('waitq assert wait64 locked'));
  assert.ok(ui.searchable('taskGetState').includes('task get state'));
  assert.ok(ui.searchable('Résumé').includes('resume'));
  assert.deepEqual(Array.from(ui.queryParts('"task lock" vm_map vm_map')), ['task lock', 'vm_map']);
  assert.equal(ui.queryParts(Array.from({ length: 30 }, (_, i) => `word${i}`).join(' ')).length, 16);
});

test('offline root URLs reject foreign protocols and paths escaping the book', () => {
  const ui = harness();
  assert.equal(ui.bookURL('_sources/osfmk/kern/ast.c.html#L20-L24').href,
    'file:///tmp/xnu-book/_sources/osfmk/kern/ast.c.html#L20-L24');
  for (const path of ['../private.txt', 'file:///etc/passwd', 'https://example.com/', 'javascript:alert(1)']) {
    assert.equal(ui.bookURL(path), null, path);
  }
});

test('highlighting escapes regex characters and never parses search text as HTML', () => {
  const ui = harness();
  const target = new Element('p');
  ui.highlight(target, 'call a+b (test) <script>bad()</script>', ['a+b', '(test)']);
  assert.deepEqual(target.children.filter(node => node.tag === 'mark').map(node => node.textContent), ['a+b', '(test)']);
  assert.equal(target.textContent, 'call a+b (test) <script>bad()</script>');
  assert.ok(target.children.some(node => node.text?.includes('<script>')));
  assert.equal(target.innerHTML, undefined);
});

test('AND matching and exact identifier heading outrank body-only matches', async () => {
  const ui = harness([
    row(0), row(1, { heading: 'waitq_assert_wait64_locked' }),
    row(2, { heading: 'vm_fault', text: 'A page fault does not contain the other query.' })
  ]);
  ui.setQuery('waitq_assert_wait64_locked');
  await ui.runSearch();
  assert.equal(ui.searchResults.children.length, 2);
  assert.ok(all('.search-result-link', ui.searchResults)[0].textContent.startsWith('waitq_assert_wait64_locked'));
  ui.setQuery('waitq_assert_wait64_locked nonexistent');
  await ui.runSearch();
  assert.equal(ui.searchResults.children.length, 0);
  assert.match(ui.searchStatus.textContent, /No matching sections/);
});

test('quoted phrases distinguish word order, while identifier components remain searchable', async () => {
  const ui = harness([
    row(0, { text: 'The task lock guards mutation.' }),
    row(1, { text: 'Take the lock before inspecting the task.' }),
    row(2)
  ]);
  ui.setQuery('"task lock"');
  await ui.runSearch();
  assert.equal(ui.searchResults.children.length, 1);
  ui.setQuery('waitq assert wait64 locked');
  await ui.runSearch();
  assert.equal(ui.searchResults.children.length, 1);
});

test('Show more stays bounded at 100 nodes, and next/previous batches preserve reachability', async () => {
  const ui = harness(Array.from({ length: 125 }, (_, i) => row(i)));
  ui.setQuery('waitq_assert_wait64_locked');
  await ui.runSearch();
  assert.equal(ui.searchResults.children.length, 20);
  for (let i = 0; i < 4; i++) ui.searchPagination.children.at(-1).listeners.click();
  assert.equal(ui.searchResults.children.length, 100);
  assert.equal(ui.searchPagination.children.at(-1).textContent, 'Next results');
  ui.searchPagination.children.at(-1).listeners.click();
  assert.equal(ui.searchResults.children.length, 20);
  assert.match(ui.searchStatus.textContent, /101–120/);
  ui.searchPagination.children.at(-1).listeners.click();
  assert.equal(ui.searchResults.children.length, 25);
  assert.match(ui.searchStatus.textContent, /101–125/);
  ui.searchPagination.children[0].listeners.click();
  assert.equal(ui.searchResults.children.length, 20);
  assert.match(ui.searchStatus.textContent, /1–20/);
});

test('source window retains generated syntax, highlights exact range and links individual lines', () => {
  const ui = harness();
  ui.sourceWindow({
    first: 12, last: 32, start: 20, end: 24,
    url: new URL('file:///tmp/xnu-book/_sources/ast.c.html#L20-L24'),
    data: ui.sourceModel(payload(Array.from({ length: 300 }, (_, i) => `line_${i + 1}`).join('\n'), { style: 1 }), 'test.c')
  });
  assert.equal(ui.sourceCode.children.length, 21);
  assert.equal(ui.sourceCode.children.filter(line => line.className.includes('is-highlighted')).length, 5);
  assert.equal(ui.sourceCode.children[8].children[0].href, 'file:///tmp/xnu-book/_sources/ast.c.html#L20');
  assert.equal(ui.sourceCode.children[0].children[1].textContent, 'line_12');
  assert.equal(ui.sourceCode.children[0].children[1].children[0].className, 'kt');
  assert.equal(ui.sourceCode.children[0].children[1].innerHTML, undefined);
  assert.match(ui.sourceMeta.textContent, /showing 12–32 of 300/);
  assert.equal(ui.previous.disabled, false);
  assert.equal(ui.next.disabled, false);
});

test('source boundaries disable unavailable context and disclose truncated long citations', () => {
  const ui = harness();
  ui.sourceWindow({
    first: 1, last: 100, start: 1, end: 400, url: new URL('file:///tmp/xnu-book/source.html'),
    data: ui.sourceModel(payload('source\n'.repeat(400)), 'test.c')
  });
  assert.equal(ui.sourceCode.children.length, 100);
  assert.equal(ui.previous.disabled, true);
  assert.equal(ui.next.disabled, false);
  assert.match(ui.sourceMeta.textContent, /Long citation/);
  ui.sourceWindow({ first: 350, last: 449, start: 395, end: 400,
    url: new URL('file:///tmp/xnu-book/source.html'),
    data: ui.sourceModel(payload('source\n'.repeat(400)), 'test.c') });
  assert.equal(ui.sourceCode.children.length, 51);
  assert.equal(ui.next.disabled, true);
});

test('source tokens keep styles and literal text across CRLF, CR, LF, Unicode and BOM', () => {
  const ui = harness();
  const text = '\ufeffα😀 <script>\r\n\r\nthird\rfourth\nlast\f\u2028x';
  const data = payload(text, {
    tokens: [[0, '\ufeffα😀 '], [1, '<script>\r'], [2, '\n\r'], [0, '\nthird\r'], [1, 'fourth\nlast\f\u2028x']],
    aliases: { 'source-heading': 3 }
  });
  const model = ui.sourceModel(data, 'test.c');
  assert.equal(model.lines.length, 5);
  assert.deepEqual(Array.from(model.lines, runs => runs.map(run => run[1]).join('')),
    ['\ufeffα😀 <script>', '', 'third', 'fourth', 'last\f\u2028x']);
  assert.deepEqual(Buffer.from(ui.sourceBytes(model)), Buffer.from(text));
  const first = ui.sourceLine(model, 1, null, true);
  assert.equal(first.id, 'L1');
  assert.equal(first.children[1].textContent, '\ufeffα😀 <script>');
  assert.equal(first.children[1].children[1].className, 'kt');
  assert.equal(first.children[1].innerHTML, undefined);
  const third = ui.sourceLine(model, 3, null, true);
  assert.equal(third.children[0].id, 'source-heading');
  assert.equal(third.children[1].href, '#L3');
});

test('empty and terminal-newline sources have exact line counts and no phantom lines', () => {
  const ui = harness();
  for (const [text, count] of [['', 0], ['\n', 1], ['\r\n', 1], ['a', 1], ['a\n', 1], ['a\n\n', 2], ['a\rb', 2]]) {
    const model = ui.sourceModel(payload(text), 'test.c');
    assert.equal(model.lines.length, count, JSON.stringify(text));
    assert.equal(model.text, text);
  }
  assert.throws(() => ui.sourceModel(payload('one', { line_count: 2 }), 'test.c'), /line count/);
  assert.throws(() => ui.sourceModel(payload('one'), 'wrong.c'), /format/);
  assert.throws(() => ui.sourceModel(payload('one', { tokens: [[999, 'one']] }), 'test.c'), /token/);
  assert.throws(() => ui.sourceModel(payload('one', { aliases: { L1: 1 } }), 'test.c'), /anchor/);
});

test('invalid UTF-8 downloads use preserved original bytes rather than replacement text', () => {
  const ui = harness();
  const bytes = Buffer.from([0xef, 0xbb, 0xbf, 0xff, 0x0d, 0x0a]);
  const model = ui.sourceModel(payload('\ufeff�\r\n', { raw_base64: bytes.toString('base64') }), 'test.c');
  assert.deepEqual(Buffer.from(ui.sourceBytes(model)), bytes);
});

test('full source materializes every line, syntax run and heading alias before enabling tools', async () => {
  const ui = harness();
  const model = ui.sourceModel(payload('one\n\nthree\n', { style: 1, aliases: { 'third-section': 3 } }), 'test.c');
  const pre = new Element('pre'); pre.dataset.source = 'test.c'; pre.dataset.sourcePayload = 'assets/sources/test.js';
  await ui.fullSource(model, pre);
  const lines = all('.source-line', pre);
  assert.deepEqual(lines.map(line => line.id), ['L1', 'L2', 'L3']);
  assert.equal(all('.source-alias', pre)[0].id, 'third-section');
  assert.deepEqual(all('.line-code', pre).map(line => line.textContent), ['one', '', 'three']);
  assert.equal(pre.attributes['aria-busy'], undefined);
  assert.ok(pre.beforeNode.children.slice(0, 2).every(button => button.disabled === false));
  assert.match(pre.beforeNode.textContent, /3 lines.*complete file/);
});

test('gzip fallback decodes stored, fixed and dynamic blocks, overlaps, multiblock and optional headers', () => {
  const ui = harness();
  const values = [Buffer.alloc(0), Buffer.from('hello'), Buffer.from('a'.repeat(120000)), randomBytes(90000),
    Buffer.from('Unicode 😀, α, résumé. source_symbol();\r\n'.repeat(6000))];
  for (const value of values) {
    for (const options of [{ level: 0 }, { strategy: constants.Z_FIXED }, { level: 9 }]) {
      assert.deepEqual(Buffer.from(ui.gunzip(gzipSync(value, options))), value);
    }
  }
  const base = gzipSync('optional header');
  const header = Buffer.from(base.subarray(0, 10)); header[3] = 4 | 8 | 16;
  const extra = Buffer.from([3, 0, 9, 8, 7]);
  const named = Buffer.concat([header, extra, Buffer.from('test.c\0comment\0'), base.subarray(10)]);
  assert.equal(Buffer.from(ui.gunzip(named)).toString(), 'optional header');
});

test('gzip fallback rejects malformed headers, reserved blocks, truncation, wrong size and CRC', () => {
  const ui = harness();
  const good = gzipSync('source source source');
  const badCRC = Buffer.from(good); badCRC[badCRC.length - 8] ^= 1;
  const badSize = Buffer.from(good); badSize[badSize.length - 4] ^= 1;
  const badBlock = Buffer.from(good); badBlock[10] = (badBlock[10] & ~6) | 6;
  const badHeader = Buffer.from(good); badHeader[3] |= 128;
  // Complete code-length alphabet, but only EOB at length 2: an invalid incomplete literal tree.
  const incompleteTree = Buffer.from('H4sIAAAAAAAA/wWAAQQAAABAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAA=', 'base64');
  for (const value of [badCRC, badSize, badBlock, badHeader, incompleteTree, good.subarray(0, 12), good.subarray(0, good.length - 1)]) {
    assert.throws(() => ui.gunzip(value), /damaged|unsupported/);
  }
});

test('generic envelopes preserve source, search arrays and complete concept HTML in both decoders', async () => {
  const values = [payload('\ufeffhello\r\n'), [row(1), row(2)], '<dl><dt>α &amp; β</dt><dd>Entire index 😀</dd></dl>'];
  for (const native of [false, true]) {
    const ui = harness([], { native });
    for (const value of values) assert.equal(JSON.stringify(await ui.unpack(envelope(value))), JSON.stringify(value));
  }
});

test('shared navigation builds active parts and keeps project-relative URLs and text safe', () => {
  const ui = harness([], { root: 'https://example.github.io/xnu-docs/' });
  const container = new Element('aside');
  ui.renderChapterNav([{ part: 3, title: 'Runtime <core>', pages: [
    { number: '3.1', title: 'AST & wait', url: 'chapter.html' },
    { number: '3.2', title: 'Source', url: '_sources/osfmk/kern/ast.c.html' }
  ] }], container);
  assert.equal(container.children[1].open, true);
  const links = all('a', container);
  assert.equal(links[0].href, 'https://example.github.io/xnu-docs/chapter.html');
  assert.equal(links[0].attributes['aria-current'], 'page');
  assert.equal(links[1].href, 'https://example.github.io/xnu-docs/_sources/osfmk/kern/ast.c.html');
  assert.match(container.textContent, /Runtime <core>/);
  assert.equal(ui.bookURL('../escape'), null);
});

test('static code Copy enhancement leaves the interactive explorer and source viewers untouched', () => {
  const ui = harness();
  const pre = new Element('pre');
  pre.matches = () => false;
  pre.closest = () => null;
  pre.parentElement = new Element('div');
  assert.equal(ui.isStaticCodeBlock(pre), true, 'Ordinary authored code keeps Copy controls');
  pre.closest = selector => selector === '#structure-layout-explorer' ? new Element('section') : null;
  assert.equal(ui.isStaticCodeBlock(pre), false, 'Dynamic layout diagnostics/directives must not acquire wrappers or Copy overlays');
  pre.closest = selector => selector === '.source-browser' ? new Element('main') : null;
  assert.equal(ui.isStaticCodeBlock(pre), false);
  pre.closest = () => null;
  pre.matches = selector => selector === '[data-source-full]';
  assert.equal(ui.isStaticCodeBlock(pre), false);
});
