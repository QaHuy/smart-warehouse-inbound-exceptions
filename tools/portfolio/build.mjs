// Regenerates the recruiter deliverables from content.mjs:
//   assets/diagrams/to-be-at-a-glance.png   (from the hand-authored SVG)
//   site/index.html                         (web case study / GitHub Pages landing page)
//   deliverables/*.pdf, deliverables/*.docx (printable case study, one-pager, Word)
// Requires Node 20+, the `docx` dev dependency, and a local Chrome/Edge (CHROME_PATH to override).
import { existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { renderCaseStudy, renderOnePager, DOWNLOADS } from './html.mjs';
import { buildDocx } from './docx.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const OUT = join(ROOT, 'deliverables');
const TMP = join(ROOT, '.build');

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
  ].filter(Boolean);
  const found = candidates.find((path) => existsSync(path));
  if (!found) throw new Error('Chrome or Edge not found; set CHROME_PATH.');
  return found;
}

const chrome = findChrome();
const headless = (args) => execFileSync(chrome, ['--headless=new', '--disable-gpu', '--hide-scrollbars',
  '--allow-file-access-from-files', ...args], { stdio: ['ignore', 'ignore', 'ignore'] });

function svgToPng(svgRel, pngRel, width, height) {
  const page = join(TMP, 'svg.html');
  writeFileSync(page, `<!doctype html><html><body style="margin:0"><img src="${pathToFileURL(join(ROOT, svgRel)).href}" style="display:block"></body></html>`);
  headless(['--force-device-scale-factor=2', `--window-size=${width},${height}`, `--screenshot=${join(ROOT, pngRel)}`, pathToFileURL(page).href]);
}

function htmlToPdf(html, pdfName) {
  const page = join(TMP, `${pdfName}.html`);
  writeFileSync(page, html);
  headless(['--no-pdf-header-footer', `--print-to-pdf=${join(OUT, pdfName)}`, pathToFileURL(page).href]);
}

rmSync(TMP, { recursive: true, force: true });
mkdirSync(TMP, { recursive: true });
mkdirSync(OUT, { recursive: true });
mkdirSync(join(ROOT, 'site'), { recursive: true });

svgToPng('assets/diagrams/to-be-at-a-glance.svg', 'assets/diagrams/to-be-at-a-glance.png', 1200, 370);
console.log('diagram  assets/diagrams/to-be-at-a-glance.png');

writeFileSync(join(ROOT, 'site', 'index.html'), renderCaseStudy({ assetBase: '' }));
console.log('web      site/index.html');

const fileBase = `${pathToFileURL(ROOT).href}/`;
htmlToPdf(renderCaseStudy({ assetBase: fileBase, print: true }), DOWNLOADS.casePdf);
htmlToPdf(renderOnePager({ assetBase: fileBase }), DOWNLOADS.onePager);
const onePagerPages = (readFileSync(join(OUT, DOWNLOADS.onePager), 'latin1').match(/\/Type\s*\/Page(?!s)/g) ?? []).length;
if (onePagerPages !== 1) throw new Error(`One-pager must fit on 1 page; got ${onePagerPages}. Shorten content.mjs.`);
console.log(`pdf      deliverables/${DOWNLOADS.casePdf}, deliverables/${DOWNLOADS.onePager}`);

writeFileSync(join(OUT, DOWNLOADS.caseDocx), await buildDocx(ROOT));
console.log(`docx     deliverables/${DOWNLOADS.caseDocx}`);

rmSync(TMP, { recursive: true, force: true });
