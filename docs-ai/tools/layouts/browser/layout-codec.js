// SPDX-License-Identifier: GPL-2.0-only
// RFC1951/1952 fallback reused from book/assets/book.js (GPL-2.0-only).
(function (root, factory) {
  const api = factory(typeof module === 'object' && module.exports ? require('node:crypto').webcrypto : root.crypto);
  if (typeof module === 'object' && module.exports) module.exports = api; else root.LayoutCodec = api;
})(globalThis, function (crypto) {
  'use strict';
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

  async function sha256(bytes) {return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), byte => byte.toString(16).padStart(2, '0')).join('');}
  async function decode(envelope, expected, options = {}) {
    if (options.signal?.aborted) throw new Error('Asset decoding cancelled');
    if (!envelope || envelope.schema !== 2 || envelope.encoding !== 'gzip-base64' || typeof envelope.data !== 'string') throw new Error('Invalid compressed asset envelope');
    if (!expected || !Number.isSafeInteger(expected.bytes) || expected.bytes < 0 || expected.bytes > 64 * 1024 * 1024 || !/^[a-f0-9]{64}$/.test(expected.sha256)) throw new Error('Invalid asset identity');
    if (envelope.data.length > 96 * 1024 * 1024) throw new Error('Compressed asset exceeds bound');
    const bytes = Uint8Array.from(atob(envelope.data), character => character.charCodeAt(0));
    let plain;
    if (!options.fallback && typeof DecompressionStream === 'function') {
      const reader = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip')).getReader();
      const chunks = []; let size = 0;
      const cancel = () => {reader.cancel().catch(() => {});}; options.signal?.addEventListener('abort', cancel, {once: true});
      try {while (true) {if (options.signal?.aborted) throw new Error('Asset decoding cancelled'); const {value, done} = await reader.read(); if (done) break; size += value.length; if (size > expected.bytes) throw new Error('Decoded asset exceeds declared size'); chunks.push(value);}}
      finally {options.signal?.removeEventListener('abort', cancel); await reader.cancel().catch(() => {}); reader.releaseLock();}
      plain = new Uint8Array(size); let offset = 0; for (const chunk of chunks) {plain.set(chunk, offset); offset += chunk.length;}
    } else {
      if (bytes.length < 8 || new DataView(bytes.buffer).getUint32(bytes.length - 4, true) !== expected.bytes) throw new Error('Gzip size mismatch');
      plain = gunzip(bytes);
    }
    if (options.signal?.aborted) throw new Error('Asset decoding cancelled');
    if (plain.length !== expected.bytes || await sha256(plain) !== expected.sha256) throw new Error('Asset integrity mismatch');
    return plain;
  }
  return {decode, sha256, gunzip};
});
