// Render BPMN files to SVG using bpmn-js inside headless Chrome (--dump-dom).
// Usage: node tools/portfolio/render-bpmn.mjs <input.bpmn> <output.svg>
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const [input, output] = process.argv.slice(2);
const chrome = process.env.CHROME_PATH ?? 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const viewer = createRequire(import.meta.url).resolve('bpmn-js/dist/bpmn-viewer.production.min.js');
const xml = readFileSync(input, 'utf8');

const work = mkdtempSync(join(tmpdir(), 'bpmn-'));
const html = `<!doctype html><html><head><meta charset="utf-8">
<script src="${pathToFileURL(viewer).href}"></script></head>
<body><div id="c" style="width:2400px;height:1600px"></div><pre id="out"></pre>
<script>
(async () => {
  try {
    const viewer = new BpmnJS({ container: '#c' });
    await viewer.importXML(${JSON.stringify(xml)});
    const { svg } = await viewer.saveSVG();
    document.getElementById('out').textContent = 'SVGSTART' + svg + 'SVGEND';
  } catch (e) {
    document.getElementById('out').textContent = 'ERROR:' + e.message;
  }
})();
</script></body></html>`;
const page = join(work, 'render.html');
writeFileSync(page, html);

const dom = execFileSync(chrome, [
  '--headless=new', '--disable-gpu', '--allow-file-access-from-files',
  '--virtual-time-budget=8000', '--dump-dom', pathToFileURL(page).href,
], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });

const match = dom.match(/SVGSTART([\s\S]*?)SVGEND/);
if (!match) {
  console.error(dom.match(/ERROR:[^<]*/)?.[0] ?? 'No SVG produced');
  process.exit(1);
}
// The DOM dump HTML-escapes the <pre> text; undo the entities.
const svg = match[1]
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
writeFileSync(output, svg);
console.log(`wrote ${output} (${svg.length} bytes)`);
