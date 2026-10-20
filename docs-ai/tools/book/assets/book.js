/* Progressive enhancement for the offline XNU book. No modules, fetch, or network services. */
(() => {
  'use strict';
  function init() {
    const body = document.body;
    const $ = (selector, scope = document) => scope.querySelector(selector);
    const $$ = (selector, scope = document) => Array.from(scope.querySelectorAll(selector));
    const root = new URL(body.dataset.root || './', document.baseURI);
    const content = $('#content');
    const nav = $('#chapter-nav');
    const menu = $('#menu-toggle');
    const mobile = window.matchMedia('(max-width: 850px)');
    let hasChapterNav = Boolean(nav?.querySelector('a, summary'));
    if (menu && !hasChapterNav) menu.hidden = true;
    const stored = {
      get(key) { try { return localStorage.getItem(key); } catch (_) { return null; } },
      set(key, value) { try { localStorage.setItem(key, value); } catch (_) { /* file:// storage may be unavailable */ } }
    };
    const announce = document.createElement('div');
    announce.className = 'sr-only';
    announce.setAttribute('role', 'status');
    announce.setAttribute('aria-live', 'polite');
    body.append(announce);
    function say(text) { announce.textContent = text; }
    function bookURL(path) {
      try {
        const url = new URL(path, root);
        if (url.protocol !== root.protocol || url.origin !== root.origin || !url.pathname.startsWith(root.pathname)) return null;
        return url;
      } catch (_) { return null; }
    }
    function plainClick(event) {
      return event.button === 0 && !event.ctrlKey && !event.metaKey && !event.shiftKey && !event.altKey;
    }
    function editable(target) {
      return target instanceof Element && Boolean(target.closest('input, textarea, select, [contenteditable]:not([contenteditable="false"])'));
    }

    /* Theme follows the OS until the reader chooses an explicit setting. */
    const themeButton = $('#theme-toggle');
    const darkPreference = window.matchMedia('(prefers-color-scheme: dark)');
    const initialTheme = stored.get('xnu-book-theme');
    let explicitTheme = initialTheme === 'light' || initialTheme === 'dark' ? initialTheme : null;
    document.documentElement.dataset.theme = explicitTheme || (darkPreference.matches ? 'dark' : 'light');
    function currentTheme() { return document.documentElement.dataset.theme || (darkPreference.matches ? 'dark' : 'light'); }
    function updateThemeButton() {
      if (!themeButton) return;
      const dark = currentTheme() === 'dark';
      themeButton.textContent = dark ? 'Light' : 'Dark';
      themeButton.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme');
      themeButton.title = themeButton.getAttribute('aria-label');
    }
    themeButton?.addEventListener('click', () => {
      const next = currentTheme() === 'dark' ? 'light' : 'dark';
      explicitTheme = next;
      document.documentElement.dataset.theme = next;
      stored.set('xnu-book-theme', next);
      updateThemeButton();
    });
    darkPreference.addEventListener?.('change', () => {
      if (!explicitTheme) document.documentElement.dataset.theme = darkPreference.matches ? 'dark' : 'light';
      updateThemeButton();
    });
    updateThemeButton();

    /* Mobile chapter drawer. In the absence of JS, navigation remains in normal flow. */
    const backdrop = document.createElement('button');
    backdrop.className = 'nav-backdrop';
    backdrop.type = 'button';
    backdrop.hidden = true;
    backdrop.tabIndex = -1;
    backdrop.setAttribute('aria-label', 'Close chapter navigation');
    body.append(backdrop);
    function setNav(open, restoreFocus = false) {
      const visible = Boolean(open && mobile.matches && hasChapterNav);
      body.classList.toggle('nav-open', visible);
      backdrop.hidden = !visible;
      menu?.setAttribute('aria-expanded', String(visible));
      if (nav) {
        nav.inert = mobile.matches && !visible;
        if (visible) {
          const first = $('a[aria-current="page"], a.active, a, summary', nav);
          first?.focus({ preventScroll: true });
        }
      }
      if (!visible && restoreFocus) menu?.focus({ preventScroll: true });
    }
    menu?.setAttribute('aria-controls', 'chapter-nav');
    menu?.addEventListener('click', () => setNav(!body.classList.contains('nav-open'), true));
    backdrop.addEventListener('click', () => setNav(false, true));
    nav?.addEventListener('click', event => {
      if (event.target.closest('a') && mobile.matches) setNav(false);
    });
    mobile.addEventListener?.('change', () => setNav(false));
    setNav(false);
    function activateChapterNav() {
      if (!nav) return;
      hasChapterNav = Boolean(nav.querySelector('a, summary'));
      if (menu) menu.hidden = !hasChapterNav;
      setNav(false);
      const here = new URL(location.href);
      let active = $('a[aria-current="page"], a.active', nav);
      if (!active) active = $$('a[href]', nav).find(link => {
        const url = new URL(link.href);
        return url.pathname === here.pathname && !url.hash;
      });
      if (active) {
        active.setAttribute('aria-current', 'page');
        active.classList.add('active');
        for (let parent = active.parentElement; parent && parent !== nav; parent = parent.parentElement) {
          if (parent.tagName === 'DETAILS') parent.open = true;
        }
        requestAnimationFrame(() => {
          const linkRect = active.getBoundingClientRect();
          const navRect = nav.getBoundingClientRect();
          if (linkRect.top < navRect.top || linkRect.bottom > navRect.bottom) nav.scrollTop += linkRect.top - navRect.top - nav.clientHeight / 3;
        });
      }
    }
    activateChapterNav();

    /* Modal management also restores focus when loading fails or Escape is used. */
    const dialogFocus = new WeakMap();
    const dialogs = $$('dialog');
    function showDialog(dialog) {
      if (!dialog || dialog.open) return;
      const trigger = document.activeElement;
      setNav(false);
      dialogFocus.set(dialog, mobile.matches && trigger?.closest('#chapter-nav') ? menu : trigger);
      if (typeof dialog.showModal === 'function') dialog.showModal();
      else {
        dialog.setAttribute('open', '');
        dialog.classList.add('dialog-fallback');
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-modal', 'true');
      }
    }
    function restoreDialogFocus(dialog) {
      const target = dialogFocus.get(dialog);
      if (target?.isConnected && !target.closest('[inert]')) target.focus({ preventScroll: true });
    }
    function closeDialog(dialog) {
      if (!dialog?.open) return;
      if (typeof dialog.close === 'function') dialog.close();
      else { dialog.removeAttribute('open'); restoreDialogFocus(dialog); }
    }
    dialogs.forEach(dialog => {
      dialog.addEventListener('close', () => restoreDialogFocus(dialog));
      dialog.addEventListener('click', event => {
        if (event.target !== dialog) return;
        const rect = dialog.getBoundingClientRect();
        if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) closeDialog(dialog);
      });
      dialog.addEventListener('keydown', event => {
        if (event.key === 'Escape' && typeof dialog.close !== 'function') { event.preventDefault(); closeDialog(dialog); }
        if (event.key !== 'Tab' || !dialog.classList.contains('dialog-fallback')) return;
        const focusable = $$('a[href], button:not([disabled]), input:not([disabled]), [tabindex="0"]', dialog).filter(el => !el.hidden);
        const first = focusable[0], last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      });
    });
    $$('[data-close-search], [data-close-diagram], [data-close-source]').forEach(button => {
      button.addEventListener('click', () => closeDialog(button.closest('dialog')));
    });

    /* Keep heading URLs copyable without introducing duplicate heading IDs. */
    function addHeadingAnchors(scope) {
      if (!scope) return;
      $$('h1[id], h2[id], h3[id], h4[id], h5[id], h6[id]', scope).forEach(heading => {
        if ($('.heading-anchor', heading)) return;
        const anchor = document.createElement('a');
        anchor.className = 'heading-anchor';
        anchor.href = '#' + encodeURIComponent(heading.id);
        anchor.textContent = '#';
        anchor.setAttribute('aria-label', 'Link to ' + heading.textContent.trim());
        anchor.title = 'Link to this section';
        heading.append(anchor);
      });
    }
    addHeadingAnchors(content);
    async function copyText(text) {
      if (navigator.clipboard?.writeText) {
        try { await navigator.clipboard.writeText(text); return true; } catch (_) { /* fall back on local pages */ }
      }
      const focused = document.activeElement;
      const field = document.createElement('textarea');
      field.value = text;
      field.className = 'sr-only';
      field.setAttribute('aria-label', 'Text to copy');
      body.append(field);
      field.select();
      let copied = false;
      try { copied = document.execCommand('copy'); } catch (_) { /* selection remains available in original block */ }
      field.remove();
      focused?.focus({ preventScroll: true });
      return copied;
    }
    if (content) $$('pre', content).forEach(pre => {
      if (pre.matches('[data-source-full]') || pre.closest('.source-browser') || $('.source-line', pre) || pre.parentElement.classList.contains('code-block')) return;
      const wrapper = document.createElement('div');
      wrapper.className = 'code-block';
      pre.before(wrapper);
      wrapper.append(pre);
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'copy-code';
      button.textContent = 'Copy';
      button.setAttribute('aria-label', 'Copy code to clipboard');
      wrapper.append(button);
      let reset;
      button.addEventListener('click', async () => {
        const copied = await copyText(pre.textContent);
        button.textContent = copied ? 'Copied' : 'Select to copy';
        say(copied ? 'Code copied to clipboard.' : 'Clipboard unavailable. Select the code and copy it manually.');
        clearTimeout(reset);
        reset = setTimeout(() => { button.textContent = 'Copy'; }, 2200);
      });
    });

    /* Classic scripts are intentionally used: fetch and module imports fail on many file:// setups. */
    const scripts = new Map();
    function loadScript(url) {
      const key = url.href;
      if (scripts.has(key)) return scripts.get(key);
      const promise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        const finish = error => {
          clearTimeout(timer);
          script.onload = script.onerror = null;
          if (error) { scripts.delete(key); script.remove(); reject(error); }
          else resolve();
        };
        const timer = setTimeout(() => finish(new Error('The local index did not finish loading.')), 20000);
        script.src = key;
        script.async = true;
        script.onload = () => finish();
        script.onerror = () => finish(new Error('The local data file could not be opened.'));
        document.head.append(script);
      });
      scripts.set(key, promise);
      return promise;
    }

    function base64Bytes(value) {
      const binary = atob(value);
      return Uint8Array.from(binary, char => char.charCodeAt(0));
    }
    /* Local fallback for older browsers without DecompressionStream. The generator emits
       one gzip member. Decode RFC 1951 blocks, then verify its RFC 1952 size and CRC32. */
    function gunzip(bytes) {
      const fail = () => { throw new Error('The compressed local data is damaged or unsupported.'); };
      if (bytes.length < 18 || bytes[0] !== 31 || bytes[1] !== 139 || bytes[2] !== 8 || (bytes[3] & 224)) fail();
      const trailer = bytes.length - 8;
      const word = at => (bytes[at] | bytes[at + 1] << 8 | bytes[at + 2] << 16 | bytes[at + 3] << 24) >>> 0;
      const crcTable = new Uint32Array(256);
      for (let n = 0; n < 256; n++) {
        let value = n;
        for (let bit = 0; bit < 8; bit++) value = value & 1 ? 0xedb88320 ^ value >>> 1 : value >>> 1;
        crcTable[n] = value >>> 0;
      }
      function crc(data, end = data.length) {
        let value = 0xffffffff;
        for (let n = 0; n < end; n++) value = crcTable[(value ^ data[n]) & 255] ^ value >>> 8;
        return (value ^ 0xffffffff) >>> 0;
      }
      let cursor = 10;
      if (bytes[3] & 4) {
        if (cursor + 2 > trailer) fail();
        const length = bytes[cursor] | bytes[cursor + 1] << 8; cursor += 2 + length;
      }
      for (const flag of [8, 16]) if (bytes[3] & flag) {
        while (cursor < trailer && bytes[cursor]) cursor++;
        cursor++;
      }
      if (bytes[3] & 2) {
        if (cursor + 2 > trailer || (crc(bytes, cursor) & 65535) !== (bytes[cursor] | bytes[cursor + 1] << 8)) fail();
        cursor += 2;
      }
      if (cursor >= trailer) fail();
      const size = word(trailer + 4);
      if (size > 256 * 1024 * 1024) fail();
      const output = new Uint8Array(size);
      let position = 0, bitPosition = cursor * 8;
      function read(count) {
        if (bitPosition + count > trailer * 8) fail();
        let value = 0;
        for (let bit = 0; bit < count; bit++, bitPosition++) value |= ((bytes[bitPosition >>> 3] >>> (bitPosition & 7)) & 1) << bit;
        return value;
      }
      function tree(lengths, kind = 'literal') {
        const counts = new Uint16Array(16), next = new Uint16Array(16), levels = [];
        let maximum = 0, available = 1;
        for (const length of lengths) { if (length > 15) fail(); if (length) { counts[length]++; maximum = Math.max(maximum, length); } }
        for (let bits = 1, code = 0; bits <= maximum; bits++) {
          available = available * 2 - counts[bits];
          if (available < 0) fail();
          code = (code + counts[bits - 1]) << 1; next[bits] = code;
          levels[bits] = new Map();
        }
        // The code-length alphabet must be complete. Literal/distance alphabets
        // permit a single one-bit symbol; an unused distance alphabet may be empty.
        if (!maximum ? kind !== 'distance' : available > 0 && (kind === 'codes' || maximum !== 1)) fail();
        lengths.forEach((length, symbol) => {
          if (!length) return;
          let value = next[length]++, reversed = 0;
          for (let bit = 0; bit < length; bit++) { reversed = reversed << 1 | value & 1; value >>>= 1; }
          levels[length].set(reversed, symbol);
        });
        return { levels, maximum };
      }
      function decode(table) {
        let code = 0;
        for (let bits = 1; bits <= table.maximum; bits++) {
          code |= read(1) << (bits - 1);
          const symbol = table.levels[bits].get(code);
          if (symbol !== undefined) return symbol;
        }
        fail();
      }
      const lengthBase = [3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31, 35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258];
      const lengthBits = [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0];
      const distanceBase = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145, 8193, 12289, 16385, 24577];
      const distanceBits = [0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13];
      let final = false;
      while (!final) {
        final = Boolean(read(1));
        const type = read(2);
        if (type === 0) {
          bitPosition = (bitPosition + 7) & ~7;
          const length = read(16), inverse = read(16);
          if ((length ^ inverse) !== 65535 || position + length > size) fail();
          for (let n = 0; n < length; n++) output[position++] = read(8);
          continue;
        }
        if (type === 3) fail();
        let literals, distances;
        if (type === 1) {
          literals = tree(Array.from({ length: 288 }, (_, n) => n < 144 ? 8 : n < 256 ? 9 : n < 280 ? 7 : 8));
          distances = tree(Array(32).fill(5), 'distance');
        } else {
          const literalCount = read(5) + 257, distanceCount = read(5) + 1, codeCount = read(4) + 4;
          if (literalCount > 286) fail();
          const order = [16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15];
          const codeLengths = Array(19).fill(0);
          for (let n = 0; n < codeCount; n++) codeLengths[order[n]] = read(3);
          const codeTree = tree(codeLengths, 'codes'), lengths = [];
          while (lengths.length < literalCount + distanceCount) {
            const symbol = decode(codeTree);
            if (symbol < 16) lengths.push(symbol);
            else {
              if (symbol === 16 && !lengths.length) fail();
              const count = symbol === 16 ? read(2) + 3 : symbol === 17 ? read(3) + 3 : read(7) + 11;
              const value = symbol === 16 ? lengths[lengths.length - 1] : 0;
              if (lengths.length + count > literalCount + distanceCount) fail();
              for (let n = 0; n < count; n++) lengths.push(value);
            }
          }
          if (!lengths[256]) fail();
          literals = tree(lengths.slice(0, literalCount)); distances = tree(lengths.slice(literalCount), 'distance');
        }
        while (true) {
          const symbol = decode(literals);
          if (symbol === 256) break;
          if (symbol < 256) { if (position >= size) fail(); output[position++] = symbol; continue; }
          if (symbol > 285) fail();
          const length = lengthBase[symbol - 257] + read(lengthBits[symbol - 257]);
          const distanceSymbol = decode(distances);
          if (distanceSymbol > 29) fail();
          const distance = distanceBase[distanceSymbol] + read(distanceBits[distanceSymbol]);
          if (distance > position || position + length > size) fail();
          for (let n = 0; n < length; n++, position++) output[position] = output[position - distance];
        }
      }
      if (position !== size || Math.ceil(bitPosition / 8) !== trailer || crc(output) !== word(trailer)) fail();
      return output;
    }
    async function unpack(value) {
      if (!value || value.schema !== 2 || value.encoding !== 'gzip-base64') return value;
      const bytes = base64Bytes(value.data);
      let plain;
      if (typeof DecompressionStream === 'function') {
        const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
        plain = new Uint8Array(await new Response(stream).arrayBuffer());
      } else {
        plain = gunzip(bytes);
      }
      return JSON.parse(new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(plain));
    }

    /* One small local navigation record replaces a repeated tree in every chapter. */
    function renderChapterNav(parts, container) {
      if (!Array.isArray(parts)) throw new Error('The chapter index has an unexpected format.');
      const fragment = document.createDocumentFragment();
      const label = document.createElement('div'); label.className = 'nav-heading'; label.textContent = 'CONTENTS';
      fragment.append(label);
      for (const part of parts) {
        const details = document.createElement('details'); details.className = 'nav-part';
        const summary = document.createElement('summary');
        const number = document.createElement('span'); number.className = 'part-number';
        number.textContent = String(part.part).padStart(2, '0');
        summary.append(number, document.createTextNode(' ' + part.title));
        const list = document.createElement('ol');
        for (const page of part.pages || []) {
          const url = bookURL(page.url);
          if (!url) continue;
          const item = document.createElement('li'), link = document.createElement('a');
          const pageNumber = document.createElement('span'); pageNumber.className = 'nav-number';
          pageNumber.textContent = page.number;
          link.href = url.href; link.append(pageNumber, document.createTextNode(' ' + page.title));
          if (page.url === body.dataset.page) {
            link.classList.add('active'); link.setAttribute('aria-current', 'page'); details.open = true;
          }
          item.append(link); list.append(item);
        }
        details.append(summary, list); fragment.append(details);
      }
      container.replaceChildren(fragment);
    }
    async function loadChapterNav() {
      const container = nav?.matches('[data-shared-nav]') ? nav : $('[data-shared-nav]', nav || document);
      if (!container) return;
      try {
        if (!window.XNU_NAV) {
          const url = body.dataset.navIndex ? new URL(body.dataset.navIndex, document.baseURI) : bookURL(container.dataset.sharedNav || 'assets/navigation.js');
          if (!url) throw new Error('The chapter-index URL is invalid.');
          await loadScript(url);
        }
        renderChapterNav(await unpack(window.XNU_NAV), container);
        activateChapterNav();
      } catch (_) { /* The static Contents link remains available if a local asset cannot load. */ }
    }
    loadChapterNav();

    const fold = value => String(value || '').normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
    function searchable(value) {
      const original = String(value || '');
      const raw = fold(original).replace(/\s+/g, ' ');
      const expanded = fold(original.replace(/([a-z\d])([A-Z])/g, '$1 $2')).replace(/[_\W]+/g, ' ').trim();
      return raw + '\n' + expanded;
    }
    function queryParts(query) {
      const parts = [];
      for (const match of query.matchAll(/"([^"]+)"|(\S+)/g)) {
        const part = fold(match[1] || match[2]).trim();
        if (part && !parts.includes(part)) parts.push(part);
      }
      return parts.slice(0, 16);
    }
    function highlight(element, text, parts) {
      const needles = [...new Set(parts.flatMap(part => [part, ...part.split(/[_\s]+/)]))].filter(part => part.length > 1).sort((a, b) => b.length - a.length);
      if (!needles.length) { element.textContent = text; return; }
      const escaped = needles.map(part => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
      const pattern = new RegExp(escaped.join('|'), 'gi');
      let cursor = 0;
      for (const match of text.matchAll(pattern)) {
        element.append(document.createTextNode(text.slice(cursor, match.index)));
        const mark = document.createElement('mark');
        mark.textContent = match[0];
        element.append(mark);
        cursor = match.index + match[0].length;
      }
      element.append(document.createTextNode(text.slice(cursor)));
    }

    /* Search uses AND matching, phrase matching, and extra weight for title/heading/identifier hits. */
    const searchDialog = $('#search-dialog');
    const searchInput = $('#search-input');
    const searchResults = $('#search-results');
    const searchStatus = $('#search-status');
    let searchRows = null, searchLoad = null, searchVersion = 0, searchTimer;
    let matches = [], resultOffset = 0, visibleCount = 0, activeParts = [];
    const PAGE_SIZE = 20, DOM_LIMIT = 100;
    const searchPagination = document.createElement('div');
    searchPagination.className = 'search-pagination';
    searchResults?.after(searchPagination);
    searchStatus?.setAttribute('role', 'status');
    searchStatus?.setAttribute('aria-live', 'polite');
    if (searchInput) searchInput.maxLength = 240;
    async function getSearchRows() {
      if (searchRows) return searchRows;
      if (!searchLoad) searchLoad = (async () => {
        if (!window.XNU_SEARCH) {
          if (!body.dataset.searchIndex) throw new Error('This book has no search index.');
          await loadScript(new URL(body.dataset.searchIndex, document.baseURI));
        }
        const rows = await unpack(window.XNU_SEARCH);
        if (!Array.isArray(rows)) throw new Error('The search index has an unexpected format.');
        searchRows = rows.map((row, index) => ({
          row, index,
          title: searchable(row.title), heading: searchable(row.heading),
          chapter: searchable(row.chapter), text: searchable(row.text)
        }));
        return searchRows;
      })().catch(error => { searchLoad = null; throw error; });
      return searchLoad;
    }
    function excerpt(text, parts) {
      text = String(text || '').replace(/\s+/g, ' ').trim();
      const lower = fold(text);
      const found = parts.map(part => lower.indexOf(part)).filter(index => index >= 0);
      const start = found.length ? Math.max(0, Math.min(...found) - 65) : 0;
      const end = Math.min(text.length, start + 260);
      return (start ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
    }
    function renderResults(append) {
      if (!searchResults || !searchStatus) return;
      if (!append) { searchResults.replaceChildren(); visibleCount = 0; }
      const end = Math.min(matches.length, resultOffset + visibleCount + PAGE_SIZE);
      const fragment = document.createDocumentFragment();
      for (let i = resultOffset + visibleCount; i < end; i++) {
        const row = matches[i].entry.row;
        const url = bookURL(row.url);
        if (!url) continue;
        const item = document.createElement('li');
        const chapter = document.createElement('div');
        chapter.className = 'search-result-chapter';
        chapter.textContent = row.chapter || row.title || 'XNU source book';
        const link = document.createElement('a');
        link.className = 'search-result-link';
        link.href = url.href;
        const title = row.heading && row.heading !== row.title ? row.heading + ' · ' + row.title : (row.title || row.heading || 'Untitled section');
        highlight(link, title, activeParts);
        const snippet = document.createElement('p');
        snippet.className = 'search-result-snippet';
        highlight(snippet, excerpt(row.text, activeParts), activeParts);
        item.append(chapter, link, snippet);
        fragment.append(item);
      }
      visibleCount = end - resultOffset;
      searchResults.append(fragment);
      searchPagination.replaceChildren();
      searchStatus.textContent = matches.length ? `${matches.length.toLocaleString()} matching sections · showing ${resultOffset + 1}–${end}.` : 'No matching sections. Try fewer words or a shorter identifier.';
      const makeButton = (text, handler) => {
        const button = document.createElement('button');
        button.type = 'button'; button.textContent = text;
        button.addEventListener('click', handler); searchPagination.append(button);
      };
      if (resultOffset > 0) makeButton('Previous results', () => {
        resultOffset = Math.max(0, resultOffset - DOM_LIMIT); renderResults(false);
        $('.search-result-link', searchResults)?.focus();
      });
      if (end < matches.length) makeButton(visibleCount < DOM_LIMIT ? 'Show more' : 'Next results', () => {
        const previousCount = searchResults.children.length;
        if (visibleCount >= DOM_LIMIT) { resultOffset += visibleCount; renderResults(false); }
        else renderResults(true);
        const links = $$('.search-result-link', searchResults);
        links[visibleCount <= PAGE_SIZE ? 0 : previousCount]?.focus();
      });
    }
    async function runSearch() {
      if (!searchInput || !searchResults || !searchStatus) return;
      const version = ++searchVersion;
      const query = searchInput.value.trim();
      if (query.length < 2) {
        searchResults.replaceChildren(); searchPagination.replaceChildren();
        searchStatus.textContent = 'Search every chapter. Use function names, keywords, or "quoted phrases".';
        return;
      }
      searchStatus.textContent = 'Searching chapters…';
      try {
        const rows = await getSearchRows();
        if (version !== searchVersion) return;
        activeParts = queryParts(query);
        if (!activeParts.length) return;
        const phrase = fold(query.replace(/"/g, '')).replace(/\s+/g, ' ');
        matches = [];
        for (const entry of rows) {
          const all = entry.title + '\n' + entry.heading + '\n' + entry.chapter + '\n' + entry.text;
          if (!activeParts.every(part => all.includes(part))) continue;
          let score = 0;
          for (const part of activeParts) {
            if (entry.title.includes(part)) score += 35;
            if (entry.heading.includes(part)) score += 50;
            if (entry.chapter.includes(part)) score += 12;
            if (entry.text.includes(part)) score += 3;
            if (part.includes('_') && entry.heading.includes(part)) score += 25;
          }
          if (entry.heading.split('\n')[0] === phrase) score += 120;
          if (entry.title.split('\n')[0] === phrase) score += 100;
          if (phrase.length > 2 && entry.heading.includes(phrase)) score += 30;
          matches.push({ entry, score });
        }
        matches.sort((a, b) => b.score - a.score || a.entry.index - b.entry.index);
        resultOffset = 0;
        renderResults(false);
      } catch (error) {
        if (version !== searchVersion) return;
        searchResults.replaceChildren(); searchPagination.replaceChildren();
        searchStatus.textContent = `${error.message} Check that the assets folder is beside the generated book, then type to retry.`;
      }
    }
    function openSearch() {
      if (!searchDialog || !searchInput) return;
      showDialog(searchDialog);
      searchInput.focus(); searchInput.select();
      runSearch();
    }
    $('#search-open')?.addEventListener('click', openSearch);
    searchResults?.addEventListener('click', event => {
      if (event.target.closest('a.search-result-link') && plainClick(event)) closeDialog(searchDialog);
    });
    searchInput?.addEventListener('input', () => {
      ++searchVersion;
      clearTimeout(searchTimer);
      searchTimer = setTimeout(runSearch, 140);
    });
    searchDialog?.addEventListener('keydown', event => {
      if (event.key !== 'ArrowDown' && event.key !== 'ArrowUp') return;
      const links = $$('.search-result-link', searchResults);
      if (!links.length) return;
      const index = links.indexOf(document.activeElement);
      if (document.activeElement === searchInput && event.key === 'ArrowDown') { event.preventDefault(); links[0].focus(); }
      else if (index >= 0) {
        event.preventDefault();
        if (event.key === 'ArrowUp' && index === 0) searchInput.focus();
        else links[Math.max(0, Math.min(links.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)))].focus();
      }
    });
    document.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase() === 'k') {
        event.preventDefault(); openSearch();
      } else if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !editable(event.target) && !dialogs.some(dialog => dialog.open)) {
        event.preventDefault(); openSearch();
      } else if (event.key === 'Escape' && body.classList.contains('nav-open')) setNav(false, true);
      if (event.key === 'Tab' && mobile.matches && body.classList.contains('nav-open')) {
        const targets = [menu, ...$$('a, summary, button', nav)].filter(el => el && el.getClientRects().length);
        const first = targets[0], last = targets[targets.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    });

    /* The index page has its own instant filter; it does not load full-book search. */
    function setupIndexFilter() {
      const indexInput = $('#index-filter');
      if (!indexInput || indexInput.dataset.ready) return;
      indexInput.dataset.ready = 'true';
      const entries = $$('.index-entry').map(element => ({ element, term: searchable(element.dataset.term || element.textContent) }));
      const groups = $$('.index-group');
      const status = document.createElement('p');
      status.className = 'index-filter-status'; status.setAttribute('role', 'status');
      indexInput.after(status);
      const filter = () => {
        const parts = queryParts(indexInput.value);
        let count = 0;
        for (const entry of entries) { entry.element.hidden = !parts.every(part => entry.term.includes(part)); if (!entry.element.hidden) count++; }
        groups.forEach(group => { group.hidden = !$('.index-entry:not([hidden])', group); });
        status.textContent = `${count.toLocaleString()} of ${entries.length.toLocaleString()} index entries`;
      };
      indexInput.addEventListener('input', filter); filter();
    }
    async function loadConceptIndex() {
      const container = $('#concept-content[data-index-payload]');
      if (!container) { setupIndexFilter(); return; }
      container.setAttribute('aria-busy', 'true');
      const status = document.createElement('p'); status.className = 'local-load-status';
      status.setAttribute('role', 'status'); status.textContent = 'Loading the complete local concept index…';
      container.before(status);
      try {
        const url = bookURL(container.dataset.indexPayload);
        if (!url) throw new Error('The concept-index URL is invalid.');
        if (!window.XNU_CONCEPT_INDEX) await loadScript(url);
        const html = await unpack(window.XNU_CONCEPT_INDEX);
        if (typeof html !== 'string') throw new Error('The concept index has an unexpected format.');
        // This is the complete trusted HTML fragment emitted by the local book generator.
        container.innerHTML = html;
        addHeadingAnchors(container);
        setupIndexFilter();
        status.remove();
        scrollToHash();
      } catch (error) {
        status.textContent = error.message + ' ';
        const retry = document.createElement('button'); retry.type = 'button'; retry.textContent = 'Retry loading index';
        retry.addEventListener('click', () => { status.remove(); loadConceptIndex(); });
        status.append(retry);
      } finally { container.removeAttribute('aria-busy'); }
    }
    loadConceptIndex();

    /* SVGs stay local; clicking opens a larger view, with optional native-size zoom. */
    const diagramDialog = $('#diagram-dialog');
    const diagramImage = $('#diagram-image');
    const diagramCaption = $('#diagram-caption');
    if (diagramDialog && diagramImage) {
      diagramImage.tabIndex = 0;
      diagramImage.setAttribute('role', 'button');
      const zoom = () => {
        const zoomed = diagramImage.classList.toggle('is-zoomed');
        diagramImage.setAttribute('aria-label', zoomed ? 'Fit diagram to window' : 'Show diagram at full size');
        diagramImage.setAttribute('aria-pressed', String(zoomed));
      };
      diagramImage.addEventListener('click', zoom);
      diagramImage.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); zoom(); } });
      $$('figure.diagram a.diagram-link').forEach(link => link.addEventListener('click', event => {
        if (!plainClick(event)) return;
        event.preventDefault();
        diagramImage.src = link.href;
        diagramImage.alt = $('img', link)?.alt || 'Kernel implementation diagram';
        diagramImage.classList.remove('is-zoomed');
        diagramImage.setAttribute('aria-label', 'Show diagram at full size');
        diagramImage.setAttribute('aria-pressed', 'false');
        if (diagramCaption) diagramCaption.textContent = $('figcaption', link.closest('figure'))?.textContent || diagramImage.alt;
        showDialog(diagramDialog);
      }));
    }

    /* A decoded source is shared by the full-file view, excerpt windows and exact downloads. */
    const sources = new Map();
    function sourceModel(data, key) {
      if (!data || data.schema !== 2 || data.path !== key || !Array.isArray(data.styles) || !Array.isArray(data.tokens)) {
        throw new Error('The source payload has an unexpected format.');
      }
      if (!data.styles.every(style => typeof style === 'string' && /^[a-zA-Z0-9_ -]*$/.test(style))) {
        throw new Error('The source payload contains an invalid syntax style.');
      }
      for (const token of data.tokens) {
        if (!Array.isArray(token) || !Number.isInteger(token[0]) || token[0] < 0 || token[0] >= data.styles.length || typeof token[1] !== 'string') {
          throw new Error('The source payload contains an invalid token.');
        }
      }
      const text = data.tokens.map(token => token[1]).join('');
      // Match the codec's physical lines, including CRLF across tokens; no phantom final row.
      const breaks = /\r\n|\r|\n/g;
      const ranges = [];
      let start = 0, match;
      while ((match = breaks.exec(text))) { ranges.push([start, match.index]); start = match.index + match[0].length; }
      if (start < text.length) ranges.push([start, text.length]);
      if (!Number.isSafeInteger(data.line_count) || data.line_count !== ranges.length) {
        throw new Error('The source payload line count does not match its text.');
      }
      const lines = ranges.map(() => []);
      let offset = 0, row = 0;
      for (const [style, value] of data.tokens) {
        const tokenEnd = offset + value.length;
        while (row < ranges.length && ranges[row][1] <= offset) row++;
        let current = row;
        while (current < ranges.length && ranges[current][0] < tokenEnd) {
          const from = Math.max(offset, ranges[current][0]), to = Math.min(tokenEnd, ranges[current][1]);
          if (to > from) lines[current].push([style, value.slice(from - offset, to - offset)]);
          if (ranges[current][1] >= tokenEnd) break;
          current++;
        }
        offset = tokenEnd;
      }
      const aliases = new Map();
      for (const [name, line] of Object.entries(data.aliases || {})) {
        if (!name || /^L\d+(?:-L\d+)?$/.test(name) || !Number.isInteger(line) || line < 1 || line > lines.length) {
          throw new Error('The source payload contains an invalid heading anchor.');
        }
        if (!aliases.has(line)) aliases.set(line, []);
        aliases.get(line).push(name);
      }
      return { ...data, text, lines, aliases };
    }
    async function getSource(key, payloadPath) {
      if (!sources.has(key)) {
        const promise = (async () => {
          const payload = bookURL(payloadPath);
          if (!payload) throw new Error('The source-payload URL is invalid.');
          if (!Object.prototype.hasOwnProperty.call(window.XNU_SOURCES || {}, key)) await loadScript(payload);
          const data = await unpack(window.XNU_SOURCES?.[key]);
          const model = sourceModel(data, key);
          if (!bookURL(model.url)) throw new Error('The full source-file URL is invalid.');
          return model;
        })().catch(error => { sources.delete(key); throw error; });
        sources.set(key, promise);
      }
      return sources.get(key);
    }
    function sourceLine(data, number, url, full) {
      const line = document.createElement(full ? 'span' : 'div'); line.className = 'source-line';
      if (full) {
        line.id = 'L' + number;
        for (const name of data.aliases.get(number) || []) {
          const alias = document.createElement('span'); alias.id = name; alias.className = 'source-alias';
          alias.setAttribute('aria-hidden', 'true'); line.append(alias);
        }
      }
      const lineno = document.createElement('a'); lineno.className = full ? 'line-number' : 'lineno';
      lineno.textContent = String(number); lineno.href = full ? '#L' + number : url.href.split('#')[0] + '#L' + number;
      lineno.setAttribute('aria-label', 'Source line ' + number);
      const code = document.createElement('span'); code.className = 'line-code';
      for (const [style, text] of data.lines[number - 1]) {
        const className = data.styles[style];
        if (!className) code.append(document.createTextNode(text));
        else { const span = document.createElement('span'); span.className = className; span.textContent = text; code.append(span); }
      }
      line.append(lineno, code);
      return line;
    }
    function sourceBytes(data) {
      return data.raw_base64 === undefined ? new TextEncoder().encode(data.text) : base64Bytes(data.raw_base64);
    }
    function scrollToHash() {
      let id;
      try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
      if (id) document.getElementById(id)?.scrollIntoView({ block: 'start' });
    }
    function highlightSourceRange() {
      $$('.source-line.is-highlighted', content || document).forEach(line => line.classList.remove('is-highlighted'));
      const match = location.hash.match(/^#L(\d+)(?:-L(\d+))?$/);
      if (!match) { scrollToHash(); return; }
      const start = Number(match[1]), end = Number(match[2] || match[1]);
      if (!Number.isSafeInteger(start) || !Number.isSafeInteger(end) || start < 1 || end < start) return;
      $$('.source-line[id]', content || document).forEach(line => {
        const number = Number(line.id.slice(1));
        if (number >= start && number <= end) line.classList.add('is-highlighted');
      });
      document.getElementById('L' + start)?.scrollIntoView({ block: 'center' });
    }
    window.addEventListener('hashchange', highlightSourceRange);
    if (/^#L\d/.test(location.hash)) requestAnimationFrame(highlightSourceRange);

    /* Keep the complete DOM for native Find, selection, printing and linkable line/heading IDs. */
    async function loadFullSource(pre) {
      const key = pre.dataset.source, payload = pre.dataset.sourcePayload;
      let code = $('code', pre);
      if (!code) { code = document.createElement('code'); pre.append(code); }
      let controls = pre.previousElementSibling;
      if (!controls?.classList.contains('source-file-controls')) {
        controls = document.createElement('div'); controls.className = 'source-file-controls'; pre.before(controls);
      }
      const status = document.getElementById('source-load-status') || document.createElement('span');
      status.className = 'local-load-status'; status.setAttribute('role', 'status');
      const copy = document.createElement('button'); copy.type = 'button'; copy.textContent = 'Copy full source'; copy.disabled = true;
      const print = document.createElement('button'); print.type = 'button'; print.textContent = 'Print full source'; print.disabled = true;
      controls.replaceChildren(copy, print, status);
      pre.setAttribute('aria-busy', 'true');
      status.textContent = 'Loading local source…';
      let model = null, nextLine = 1, complete = false;
      function appendChunk(force = false) {
        if (!model || complete) return;
        const fragment = document.createDocumentFragment(), until = performance.now() + 12;
        do {
          if (nextLine > model.lines.length) break;
          fragment.append(sourceLine(model, nextLine++, null, true));
        } while (force || (nextLine % 250 !== 0 || performance.now() < until));
        code.append(fragment);
        complete = nextLine > model.lines.length;
        status.textContent = complete ? (model.lines.length ? `${model.lines.length.toLocaleString()} lines · browser Find searches the complete file.` : 'This source file is empty.') : `Preparing source lines ${(nextLine - 1).toLocaleString()} of ${model.lines.length.toLocaleString()}…`;
        if (complete) { pre.removeAttribute('aria-busy'); copy.disabled = print.disabled = false; }
      }
      const beforePrint = () => { appendChunk(true); };
      window.addEventListener('beforeprint', beforePrint);
      try {
        model = await getSource(key, payload);
        code.replaceChildren();
        while (!complete) {
          appendChunk();
          if (!complete) await new Promise(resolve => setTimeout(resolve, 0));
        }
        copy.addEventListener('click', async () => {
          const copied = await copyText(model.text);
          say(copied ? 'Full source copied to clipboard.' : 'Clipboard unavailable. Use the source download button.');
          copy.textContent = copied ? 'Copied' : 'Copy unavailable';
          setTimeout(() => { copy.textContent = 'Copy full source'; }, 2200);
        });
        print.addEventListener('click', () => window.print());
        highlightSourceRange();
      } catch (error) {
        pre.removeAttribute('aria-busy'); status.textContent = error.message + ' ';
        const retry = document.createElement('button'); retry.type = 'button'; retry.textContent = 'Retry source';
        retry.addEventListener('click', () => loadFullSource(pre)); status.append(retry);
      } finally { window.removeEventListener('beforeprint', beforePrint); }
    }
    $$('pre[data-source-full]').forEach(loadFullSource);
    document.addEventListener('click', async event => {
      const button = event.target.closest('.source-download[data-source][data-source-payload]');
      if (!button || !plainClick(event)) return;
      event.preventDefault();
      const wasDisabled = button.disabled; button.disabled = true;
      try {
        const data = await getSource(button.dataset.source, button.dataset.sourcePayload);
        const url = URL.createObjectURL(new Blob([sourceBytes(data)], { type: 'application/octet-stream' }));
        const link = document.createElement('a'); link.href = url; link.download = data.path.split('/').pop();
        body.append(link); link.click(); link.remove();
        setTimeout(() => URL.revokeObjectURL(url), 60000);
        say('Source download prepared.');
      } catch (error) { say(error.message + ' Reopen the source page to retry.'); }
      finally { button.disabled = wasDisabled; }
    });

    /* Excerpts and full-file pages use the same token stream; neither contains duplicated HTML. */
    const sourceDialog = $('#source-dialog');
    const sourceCode = $('#source-code');
    const sourceTitle = $('#source-title');
    const sourceMeta = $('#source-meta');
    const sourceFull = $('#source-full-link');
    let sourceVersion = 0, sourceState = null;
    if (sourceDialog && sourceCode) {
      sourceCode.classList.add('source-preview-code');
      let previous = $('#source-prev'), next = $('#source-next');
      if (!previous || !next) {
        const controls = document.createElement('div'); controls.className = 'source-preview-controls';
        if (!previous) { previous = document.createElement('button'); previous.id = 'source-prev'; previous.type = 'button'; previous.textContent = 'Earlier lines'; controls.append(previous); }
        if (!next) { next = document.createElement('button'); next.id = 'source-next'; next.type = 'button'; next.textContent = 'Later lines'; controls.append(next); }
        sourceCode.after(controls);
      }
      function renderSource() {
        const state = sourceState;
        if (!state) return;
        const end = Math.min(state.data.lines.length, state.last);
        const fragment = document.createDocumentFragment();
        for (let number = state.first; number <= end; number++) {
          const line = sourceLine(state.data, number, state.url, false);
          if (number >= state.start && number <= state.end) line.classList.add('is-highlighted');
          fragment.append(line);
        }
        sourceCode.replaceChildren(fragment);
        sourceCode.scrollTop = 0;
        if (sourceMeta) sourceMeta.textContent = state.data.lines.length ? `Cited lines ${state.start}–${state.end} · showing ${state.first}–${end} of ${state.data.lines.length.toLocaleString()}.` + (state.end - state.start >= 100 ? ' Long citation: open the full file to see the complete range.' : '') : 'This source file is empty.';
        previous.disabled = state.first <= 1;
        next.disabled = end >= state.data.lines.length;
      }
      previous.addEventListener('click', () => { if (sourceState) { sourceState.first = Math.max(1, sourceState.first - 80); sourceState.last = Math.min(sourceState.data.lines.length, sourceState.first + 99); renderSource(); } });
      next.addEventListener('click', () => { if (sourceState) { sourceState.first = Math.min(sourceState.data.lines.length, Math.max(sourceState.first + 1, sourceState.last - 19)); sourceState.last = Math.min(sourceState.data.lines.length, sourceState.first + 99); renderSource(); } });
      document.addEventListener('click', async event => {
        const link = event.target.closest('a.source-link[data-source]');
        if (!link || !plainClick(event) || !link.dataset.sourcePayload) return;
        const payload = bookURL(link.dataset.sourcePayload);
        if (!payload) return;
        event.preventDefault();
        const version = ++sourceVersion;
        const key = link.dataset.source;
        sourceState = null; previous.disabled = next.disabled = true;
        if (sourceTitle) sourceTitle.textContent = key;
        if (sourceMeta) sourceMeta.textContent = 'Loading local source excerpt…';
        sourceCode.replaceChildren(); sourceCode.setAttribute('aria-busy', 'true');
        if (sourceFull) sourceFull.href = link.href;
        showDialog(sourceDialog);
        try {
          const data = await getSource(key, link.dataset.sourcePayload);
          if (version !== sourceVersion) return;
          const url = bookURL(data.url);
          const requestedStart = Number(link.dataset.start || 1);
          const requestedEnd = Number(link.dataset.end || requestedStart);
          const start = Number.isSafeInteger(requestedStart) ? Math.max(1, Math.min(data.lines.length, requestedStart)) : 1;
          const end = Number.isSafeInteger(requestedEnd) ? Math.max(start, Math.min(data.lines.length, requestedEnd)) : start;
          url.hash = data.lines.length ? `L${start}` + (end !== start ? `-L${end}` : '') : '';
          const first = Math.max(1, start - 8);
          sourceState = { data, url, start, end, first, last: Math.min(data.lines.length, end + 8, first + 99) };
          if (sourceFull) sourceFull.href = url.href;
          if (sourceTitle) sourceTitle.textContent = data.path || key;
          renderSource();
        } catch (error) {
          if (version !== sourceVersion) return;
          if (sourceMeta) sourceMeta.textContent = `${error.message} Use “Open full source” or reopen this citation to retry.`;
        } finally { if (version === sourceVersion) sourceCode.removeAttribute('aria-busy'); }
      });
    }

    /* Highlight the latest heading above the reading line, including short/intervening sections. */
    const toc = $('#page-toc');
    if (toc && content) {
      const targets = $$('a[href]', toc).map(link => {
        let id;
        try { id = decodeURIComponent(new URL(link.href).hash.slice(1)); } catch (_) { return null; }
        const heading = id ? document.getElementById(id) : null;
        return heading && content.contains(heading) ? { link, heading } : null;
      }).filter(Boolean);
      let queued = false, active = null;
      function updateToc() {
        queued = false;
        let chosen = targets[0];
        const readingLine = ($('.book-header')?.getBoundingClientRect().bottom || 0) + 38;
        for (const target of targets) {
          if (target.heading.getBoundingClientRect().top <= readingLine) chosen = target;
          else break;
        }
        if (!chosen || chosen === active) return;
        active?.link.classList.remove('active'); active?.link.removeAttribute('aria-current');
        chosen.link.classList.add('active'); chosen.link.setAttribute('aria-current', 'location'); active = chosen;
        const linkRect = chosen.link.getBoundingClientRect(), tocRect = toc.getBoundingClientRect();
        if (linkRect.top < tocRect.top || linkRect.bottom > tocRect.bottom) toc.scrollTop += linkRect.top - tocRect.top - toc.clientHeight / 3;
      }
      const schedule = () => { if (!queued) { queued = true; requestAnimationFrame(updateToc); } };
      window.addEventListener('scroll', schedule, { passive: true });
      window.addEventListener('resize', schedule);
      if ('ResizeObserver' in window) new ResizeObserver(schedule).observe(content);
      schedule();
    }
    body.classList.add('js-ready');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
