// SPDX-License-Identifier: GPL-2.0-only
// Resolve pinned classic-script assets from the nested handbook chapter.
(() => {
  'use strict';
  const config = window.layoutExplorerConfig;
  if (!config?.integrated || config.assetRoot !== '../layouts/') throw Error('Invalid handbook layout asset root');
  const subscribers = new Map(), original = LayoutRuntimeAssets.deliver;
  LayoutRuntimeAssets.deliver = (id, envelope) => {
    original(id, envelope);
    for (const receive of [...(subscribers.get(id) || [])]) receive(envelope);
  };
  const loadEnvelope = (asset, signal) => new Promise((resolve, reject) => {
    if (signal.aborted) {reject(Error('Layout asset loading cancelled')); return;}
    const script = document.createElement('script');
    let delivered = false, envelope;
    const receive = value => {if (!delivered) {delivered = true; envelope = value;}};
    const cleanup = () => {const group = subscribers.get(asset.id);group?.delete(receive);if (!group?.size) subscribers.delete(asset.id);script.remove();script.onload = script.onerror = null;signal.removeEventListener('abort', abort);};
    const abort = () => {cleanup();reject(Error('Layout asset loading cancelled'));};
    if (!subscribers.has(asset.id)) subscribers.set(asset.id, new Set());
    subscribers.get(asset.id).add(receive);
    script.onload = () => {cleanup();delivered ? resolve(envelope) : reject(Error('Layout asset did not register'));};
    script.onerror = () => {cleanup();reject(Error('Cannot load local layout asset: ' + asset.id));};
    signal.addEventListener('abort', abort, {once: true});
    script.src = config.assetRoot + asset.url;
    document.head.append(script);
  });
  window.layoutRuntimeOptions = {...(window.layoutRuntimeOptions || {}), loadEnvelope};
})();
