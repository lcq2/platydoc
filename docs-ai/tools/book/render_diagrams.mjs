#!/usr/bin/env node
// Offline Mermaid renderer. Node built-ins + system Chromium; no npm dependencies.
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const COMMAND_TIMEOUT = 30000;

/** Small reusable CDP pipe client for build rendering and local-book browser QA. */
export class Browser {
  constructor(process, directory) {
    this.process = process;
    this.directory = directory;
    this.nextId = 0;
    this.pending = new Map();
    this.buffer = '';
    this.stderr = '';
    process.stderr.on('data', data => {
      this.stderr = (this.stderr + data.toString()).slice(-8000);
    });
    process.stdio[4].setEncoding('utf8');
    for (const pipe of [process.stdio[3], process.stdio[4]]) {
      pipe.on('error', error => this.failPending(new Error(`${error.message}: ${this.stderr}`)));
    }
    process.stdio[4].on('data', data => {
      this.buffer += data;
      let end;
      while ((end = this.buffer.indexOf('\0')) >= 0) {
        const frame = this.buffer.slice(0, end);
        this.buffer = this.buffer.slice(end + 1);
        if (!frame) continue;
        const message = JSON.parse(frame);
        const pending = this.pending.get(message.id);
        if (!pending) continue;
        clearTimeout(pending.timer);
        this.pending.delete(message.id);
        if (message.error) pending.reject(new Error(JSON.stringify(message.error)));
        else pending.resolve(message.result);
      }
    });
    process.on('error', error => this.failPending(error));
    process.on('exit', (code, signal) => {
      this.failPending(new Error(`Chromium exited (${code ?? signal}): ${this.stderr}`));
    });
  }

  failPending(error) {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(error);
    }
    this.pending.clear();
  }

  static async launch(options = {}) {
    const directory = await mkdtemp(path.join(tmpdir(), 'xnu-diagram-browser-'));
    const executable = options.executable || process.env.CHROMIUM_PATH || '/usr/bin/chromium';
    const child = spawn(executable, [
      '--headless=new', '--no-sandbox', '--disable-dev-shm-usage',
      '--disable-gpu', '--no-first-run', '--no-default-browser-check',
      '--disable-background-networking', '--disable-component-update',
      '--disable-extensions', '--disable-sync', '--metrics-recording-only',
      '--allow-file-access-from-files', '--remote-debugging-pipe',
      `--user-data-dir=${directory}`, 'about:blank',
    ], { stdio: ['ignore', 'ignore', 'pipe', 'pipe', 'pipe'] });
    const browser = new Browser(child, directory);
    try {
      const { targetId } = await browser.send('Target.createTarget', { url: 'about:blank' }, null);
      const { sessionId } = await browser.send('Target.attachToTarget', { targetId, flatten: true }, null);
      browser.sessionId = sessionId;
      await browser.send('Page.enable');
      await browser.send('Runtime.enable');
      await browser.send('Network.enable');
      // This renderer must not silently retrieve modules, fonts or images online.
      await browser.send('Network.setBlockedURLs', { urls: ['http://*', 'https://*'] });
      return browser;
    } catch (error) {
      await browser.close();
      throw error;
    }
  }

  send(method, params = {}, sessionId = this.sessionId, timeout = COMMAND_TIMEOUT) {
    const id = ++this.nextId;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP ${method} exceeded ${timeout} ms`));
      }, timeout);
      this.pending.set(id, { resolve, reject, timer });
      const message = { id, method, params };
      if (sessionId) message.sessionId = sessionId;
      this.process.stdio[3].write(JSON.stringify(message) + '\0', error => {
        if (!error) return;
        clearTimeout(timer);
        this.pending.delete(id);
        reject(error);
      });
    });
  }

  async evaluate(expression, timeout = COMMAND_TIMEOUT) {
    const result = await this.send('Runtime.evaluate', {
      expression, awaitPromise: true, returnByValue: true,
      timeout, userGesture: false,
    }, this.sessionId, timeout + 1000);
    if (result.exceptionDetails) {
      throw new Error(result.exceptionDetails.exception?.description
        || result.exceptionDetails.text || 'Browser evaluation failed');
    }
    return result.result.value;
  }

  async navigate(url) {
    const result = await this.send('Page.navigate', { url });
    if (result.errorText) throw new Error(result.errorText);
    await this.evaluate(`new Promise((resolve, reject) => {
      const limit = Date.now() + 15000;
      const check = () => {
        if (document.readyState === 'complete' && location.href === ${JSON.stringify(url)}) resolve(true);
        else if (Date.now() > limit) reject(new Error('Page load timed out'));
        else setTimeout(check, 20);
      };
      check();
    })`);
  }

  async close() {
    if (this.process.exitCode === null && this.process.signalCode === null) {
      try { await this.send('Browser.close', {}, null, 2000); } catch {}
      if (this.process.exitCode === null && this.process.signalCode === null) {
        this.process.kill('SIGKILL');
        await new Promise(resolve => {
          this.process.once('exit', resolve);
          setTimeout(resolve, 1000).unref();
        });
      }
    }
    this.failPending(new Error('Browser closed'));
    await rm(this.directory, { recursive: true, force: true, maxRetries: 3 });
  }
}

async function renderBrowserBatch(request) {
  const browser = await Browser.launch();
  try {
    const page = path.join(browser.directory, 'render.html');
    await writeFile(page, '<!doctype html><meta charset="utf-8"><title>Offline diagram render</title><body></body>');
    await browser.navigate(pathToFileURL(page).href);
    await browser.evaluate(`(async () => {
      window.mermaid = (await import(${JSON.stringify(pathToFileURL(request.entry).href)})).default;
      return true;
    })()`);
    const rendered = [];
    for (const item of request.diagrams) {
      try {
        const result = await browser.evaluate(`(async () => {
          const item = ${JSON.stringify(item)};
          const config = ${JSON.stringify(request.config)};
          document.body.replaceChildren();
          window.mermaid.initialize({...config, deterministicIDSeed: item.key});
          const {svg} = await window.mermaid.render('diagram_' + item.key, item.source);
          const documentSvg = new DOMParser().parseFromString(svg, 'image/svg+xml');
          const root = documentSvg.documentElement;
          if (root.localName !== 'svg' || documentSvg.querySelector('parsererror')) throw new Error('Invalid SVG result');
          if (documentSvg.querySelector('foreignObject')) throw new Error('Renderer emitted HTML foreignObject labels');
          if (documentSvg.querySelector('script')) throw new Error('Renderer emitted a script');
          const ns = 'http://www.w3.org/2000/svg';
          const title = documentSvg.createElementNS(ns, 'title');
          title.id = 'title_' + item.key;
          title.textContent = item.label || 'Architecture diagram';
          const description = documentSvg.createElementNS(ns, 'desc');
          description.id = 'desc_' + item.key;
          description.textContent = 'Source diagram:\\n' + item.source;
          root.prepend(title, description);
          root.setAttribute('role', 'img');
          root.setAttribute('aria-labelledby', title.id);
          root.setAttribute('aria-describedby', description.id);
          root.setAttribute('data-renderer', 'Mermaid ${request.version}');
          root.setAttribute('style', 'background: #fff; font-family: Arial, Helvetica, sans-serif;');
          return {key: item.key, svg: new XMLSerializer().serializeToString(root)};
        })()`, request.render_timeout_ms || COMMAND_TIMEOUT);
        rendered.push(result);
      } catch (error) {
        rendered.push({ key: item.key, error: String(error.message || error), label: item.label });
      }
    }
    return rendered;
  } finally {
    await browser.close();
  }
}

const xml = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;').replaceAll('"', '&quot;');

function plain(value) {
  if (Array.isArray(value)) value = value.join('\n');
  return String(value ?? '')
    .replace(/ﬂ°°(\d+)¶ß/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/ﬂ°([^¶]+)¶ß/g, (_, name) => `&${name};`)
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/#(\d+);/g, (_, n) => String.fromCodePoint(Number(n)))
    .replace(/&(?:amp|lt|gt|quot|apos);/g, entity =>
      ({ '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&apos;': "'" }[entity]))
    .replace(/^`|`$/g, '');
}

function accessibleSvg(svg, item, renderer) {
  return svg.replace(/<!DOCTYPE[\s\S]*?>/g, '').replace(/<svg\b([^>]*)>/, (_, attrs) =>
    `<svg${attrs} role="img" aria-labelledby="title_${item.key}" aria-describedby="desc_${item.key}" data-renderer="${xml(renderer)}">`
    + `<title id="title_${item.key}">${xml(item.label || 'Architecture diagram')}</title>`
    + `<desc id="desc_${item.key}">${xml('Source diagram:\n' + item.source)}</desc>`);
}

async function graphSvg(data, item, version) {
  const quote = value => JSON.stringify(String(value));
  const nodes = new Map(data.nodes.map(node => [node.id, node]));
  const groups = new Map(data.nodes.filter(node => node.isGroup).map(node => [node.id, node]));
  const allowed = new Set(['squareRect', 'rect', 'diamond', 'stateStart', 'stateEnd']);
  for (const node of nodes.values()) {
    if (!allowed.has(node.shape)) throw new Error(`Unsupported fallback graph shape: ${node.shape}`);
    if (node.link || node.img || node.icon || node.cssStyles?.length || node.cssCompiledStyles?.length) {
      throw new Error('Fallback does not support custom graph images, links or styles');
    }
    if (node.isGroup && node.dir) throw new Error('Fallback does not support a separate subgraph direction');
  }
  const dot = [
    'digraph diagram {',
    `graph [rankdir=${quote(data.direction || 'TB')}, bgcolor="white", pad="0.3", nodesep="0.35", ranksep="0.65", compound=true, fontname="DejaVu Sans", fontsize=16];`,
    'node [shape=box, style="rounded,filled", fillcolor="#e8f0fa", color="#516c91", fontcolor="#172a46", fontname="DejaVu Sans", fontsize=14, margin="0.14,0.10"];',
    'edge [color="#516c91", fontcolor="#172a46", fontname="DejaVu Sans", fontsize=12, arrowsize=0.7];',
  ];
  function emit(parent) {
    for (const node of nodes.values()) {
      if ((node.parentId || undefined) !== parent) continue;
      if (node.isGroup) {
        dot.push(`subgraph ${quote('cluster_' + node.id)} { label=${quote(plain(node.label))}; color="#9aaabd"; style=rounded;`);
        // An invisible anchor preserves edges whose endpoint is the group itself.
        dot.push(`${quote(node.id)} [label="", shape=point, width=0, height=0, style=invis];`);
        emit(node.id);
        dot.push('}');
      } else {
        const shape = { diamond: 'diamond', stateStart: 'circle', stateEnd: 'doublecircle' }[node.shape] || 'box';
        const special = node.shape === 'stateStart' || node.shape === 'stateEnd';
        dot.push(`${quote(node.id)} [label=${quote(special ? '' : plain(node.label))}, shape=${shape}`
          + (special ? ', width=0.17, height=0.17, fixedsize=true, fillcolor="#172a46", style=filled' : '') + '];');
      }
    }
  }
  emit(undefined);
  for (const edge of data.edges) {
    if (!nodes.has(edge.start) || !nodes.has(edge.end)) throw new Error('Graph edge has an unresolved endpoint');
    if ([edge.arrowTypeStart, edge.arrowTypeEnd].some(arrow =>
      arrow && !['none', 'arrow_point', 'arrow_barb'].includes(arrow))
      || ![undefined, 'normal', 'dotted'].includes(edge.thickness)
      || ![undefined, 'normal', 'dotted'].includes(edge.pattern)
      || edge.cssCompiledStyles?.length) {
      throw new Error('Fallback does not support this graph edge style');
    }
    const start = edge.arrowTypeStart && edge.arrowTypeStart !== 'none';
    const end = edge.arrowTypeEnd && edge.arrowTypeEnd !== 'none';
    const attributes = [
      `label=${quote(plain(edge.label))}`, `dir=${start ? (end ? 'both' : 'back') : (end ? 'forward' : 'none')}`,
      `style=${edge.pattern === 'dotted' ? 'dashed' : 'solid'}`,
    ];
    if (groups.has(edge.start)) attributes.push(`ltail=${quote('cluster_' + edge.start)}`);
    if (groups.has(edge.end)) attributes.push(`lhead=${quote('cluster_' + edge.end)}`);
    dot.push(`${quote(edge.start)} -> ${quote(edge.end)} [${attributes.join(',')}];`);
  }
  dot.push('}');
  const svg = await new Promise((resolve, reject) => {
    const child = spawn('dot', ['-Tsvg'], { stdio: ['pipe', 'pipe', 'pipe'] });
    let output = '', error = '';
    const timer = setTimeout(() => {
      child.kill('SIGKILL'); reject(new Error('Graphviz exceeded 15 seconds'));
    }, 15000);
    child.stdout.setEncoding('utf8');
    child.stdout.on('data', text => {
      output += text;
      if (output.length > 16 * 1024 * 1024) child.kill('SIGKILL');
    });
    child.stderr.on('data', text => { error = (error + text).slice(-4000); });
    child.on('error', err => { clearTimeout(timer); reject(err); });
    child.on('close', code => {
      clearTimeout(timer);
      if (code === 0) resolve(output);
      else reject(new Error(`Graphviz failed (${code}): ${error}`));
    });
    child.stdin.on('error', err => { clearTimeout(timer); reject(err); });
    child.stdin.end(dot.join('\n'));
  });
  return accessibleSvg(svg, item, `Mermaid ${version} parser + Graphviz`);
}

function wrapped(value, columns) {
  return plain(value).split('\n').flatMap(line => {
    if (!line) return [''];
    const lines = [];
    let current = '';
    for (const word of line.split(/\s+/)) {
      if (current && current.length + word.length + 1 > columns) {
        lines.push(current); current = '';
      }
      current += (current ? ' ' : '') + word;
    }
    lines.push(current);
    return lines;
  });
}

function sequenceSvg(db, item, version) {
  const actors = [...db.getActors()];
  if (!actors.length) throw new Error('Sequence has no actors');
  if (actors.some(([, actor]) => actor.type !== 'participant')) {
    throw new Error('Fallback supports participant boxes, not actor icons');
  }
  if (db.getBoxes().length) throw new Error('Fallback does not support participant boxes');
  const events = db.getMessages(), line = db.LINETYPE;
  const supported = new Set([
    line.SOLID, line.DOTTED, line.NOTE, line.LOOP_START, line.LOOP_END,
    line.ALT_START, line.ALT_ELSE, line.ALT_END, line.OPT_START, line.OPT_END,
  ]);
  const gap = 270, margin = 250, width = Math.max(700, margin * 2 + (actors.length - 1) * gap);
  const positions = new Map(actors.map(([id], index) => [id, margin + index * gap]));
  const shapes = [], frameShapes = [], frames = [];
  const text = (x, y, lines, anchor = 'middle', size = 14) =>
    `<text x="${x}" y="${y}" text-anchor="${anchor}" font-size="${size}">`
    + lines.map((label, index) => `<tspan x="${x}" dy="${index ? 19 : 0}">${xml(label)}</tspan>`).join('') + '</text>';
  const actorHeight = Math.max(58, ...actors.map(([id, actor]) =>
    wrapped(actor.description || id, 27).length * 19 + 20));
  let y = actorHeight + 52;
  for (const event of events) {
    if (!supported.has(event.type) || event.activate || event.centralConnection) {
      throw new Error(`Unsupported fallback sequence event ${event.type}`);
    }
    const label = plain(event.message);
    if ([line.LOOP_START, line.ALT_START, line.OPT_START].includes(event.type)) {
      const kind = { [line.LOOP_START]: 'loop', [line.ALT_START]: 'alt', [line.OPT_START]: 'opt' }[event.type];
      frames.push({ y: y - 18, depth: frames.length, kind });
      shapes.push(text(35 + frames.length * 12, y, wrapped(`${kind} — ${label}`, Math.floor((width - 100) / 8)), 'start'));
      y += 38;
      continue;
    }
    if ([line.LOOP_END, line.ALT_END, line.OPT_END].includes(event.type)) {
      const frame = frames.pop();
      if (!frame) throw new Error('Sequence frame end without start');
      const kind = { [line.LOOP_END]: 'loop', [line.ALT_END]: 'alt', [line.OPT_END]: 'opt' }[event.type];
      if (frame.kind !== kind) throw new Error('Mismatched sequence control frame');
      const x = 25 + frame.depth * 12;
      frameShapes.push(`<rect x="${x}" y="${frame.y}" width="${width - 2 * x}" height="${y - frame.y}" rx="3" fill="none" stroke="#8c9cb0"/>`);
      y += 25;
      continue;
    }
    if (event.type === line.ALT_ELSE) {
      if (frames.at(-1)?.kind !== 'alt') throw new Error('Sequence else outside alt');
      const x = 25 + (frames.length - 1) * 12;
      shapes.push(`<path d="M ${x} ${y - 12} H ${width - x}" stroke="#8c9cb0" stroke-dasharray="5 4" fill="none"/>`);
      shapes.push(text(x + 12, y + 7, wrapped(`else — ${label}`, Math.floor((width - 100) / 8)), 'start'));
      y += 43;
      continue;
    }
    if (!positions.has(event.from) || !positions.has(event.to)) throw new Error('Unknown sequence participant');
    const a = positions.get(event.from), b = positions.get(event.to);
    if (event.type === line.NOTE) {
      let left, right;
      if (event.placement === db.PLACEMENT.LEFTOF) {
        right = a - 15; left = right - 290;
      } else if (event.placement === db.PLACEMENT.RIGHTOF) {
        left = a + 15; right = left + 290;
      } else {
        left = Math.min(a, b) - 125; right = Math.max(a, b) + 125;
      }
      left = Math.max(10, left); right = Math.min(width - 10, right);
      const lines = wrapped(label, Math.max(10, Math.floor((right - left - 20) / 8)));
      const height = lines.length * 19 + 20;
      shapes.push(`<rect x="${left}" y="${y - 14}" width="${right - left}" height="${height}" rx="3" fill="#fff5d6" stroke="#a99150"/>`);
      shapes.push(text((left + right) / 2, y + 4, lines));
      y += height + 22;
      continue;
    }
    const self = a === b, available = self ? 235 : Math.abs(b - a) - 15;
    const labels = wrapped(label, Math.max(18, Math.floor(available / 8)));
    const center = self ? a + 110 : (a + b) / 2;
    shapes.push(text(center, y, labels));
    y += labels.length * 19 + 5;
    const arrow = self ? `M ${a} ${y} h 90 v 24 h -90` : `M ${a} ${y} H ${b}`;
    shapes.push(`<path d="${arrow}" fill="none" stroke="#516c91" stroke-width="1.5" marker-end="url(#arrow_${item.key})"`
      + (event.type === line.DOTTED ? ' stroke-dasharray="6 4"' : '') + '/>');
    y += self ? 60 : 38;
  }
  if (frames.length) throw new Error('Unclosed sequence control frame');
  const height = y + 30, actorShapes = [];
  for (const [id, actor] of actors) {
    const x = positions.get(id), label = wrapped(actor.description || id, 27);
    actorShapes.push(`<path d="M ${x} ${15 + actorHeight} V ${height - 15}" fill="none" stroke="#a0adbd" stroke-dasharray="5 4"/>`);
    actorShapes.push(`<rect x="${x - 115}" y="15" width="230" height="${actorHeight}" rx="5" fill="#e8f0fa" stroke="#516c91"/>`);
    actorShapes.push(text(x, 15 + actorHeight / 2 - (label.length - 1) * 9.5 + 5, label, 'middle', 15));
  }
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`
    + '<style>text { font-family: DejaVu Sans, Arial, sans-serif; fill: #172a46; }</style>'
    + `<defs><marker id="arrow_${item.key}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#516c91"/></marker></defs>`
    + `<rect width="${width}" height="${height}" fill="white"/>`
    + actorShapes.join('') + frameShapes.join('') + shapes.join('') + '</svg>';
  return accessibleSvg(svg, item, `Mermaid ${version} parser + native SVG sequence`);
}

async function renderParsedBatch(request) {
  const mermaid = (await import(pathToFileURL(request.entry).href)).default;
  // Mermaid's parser shares a DOM-based sanitizer with its browser renderer.
  // This adapter parses text only: it never inserts labels into HTML, all DOT
  // strings are quoted, and all SVG label content is XML-escaped below.
  // The pinned vendor modules remain byte-for-byte unchanged.
  const { g: purifier } = await import('./vendor/mermaid/chunk-XL5YO2U3.js');
  purifier.sanitize = value => String(value);
  purifier.addHook = () => {};
  mermaid.initialize({ ...request.config, securityLevel: 'loose' });
  const result = [];
  for (const item of request.diagrams) {
    try {
      const diagram = await mermaid.mermaidAPI.getDiagramFromText(item.source);
      let svg;
      if (diagram.type === 'sequence') svg = sequenceSvg(diagram.db, item, request.version);
      else if (['flowchart-v2', 'stateDiagram'].includes(diagram.type)) {
        const data = diagram.db.getData();
        data.direction ||= diagram.db.getDirection?.();
        svg = await graphSvg(data, item, request.version);
      } else throw new Error(`Fallback does not support diagram type ${diagram.type}`);
      result.push({ key: item.key, svg });
    } catch (error) {
      result.push({ key: item.key, label: item.label, error: String(error.message || error) });
    }
  }
  return result;
}

export async function renderBatch(request) {
  if (request.backend === 'parsed-svg') return renderParsedBatch(request);
  try {
    return await renderBrowserBatch(request);
  } catch (error) {
    if (request.backend === 'browser') throw error;
    process.stderr.write(`Chromium unavailable; using pinned Mermaid parser + Graphviz/native SVG: ${error.message}\n`);
    return renderParsedBatch(request);
  }
}

async function main() {
  let input = '';
  for await (const chunk of process.stdin) input += chunk;
  const request = JSON.parse(input);
  const result = await renderBatch(request);
  process.stdout.write(JSON.stringify(result));
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => {
    process.stderr.write(String(error.stack || error) + '\n');
    process.exitCode = 1;
  });
}
