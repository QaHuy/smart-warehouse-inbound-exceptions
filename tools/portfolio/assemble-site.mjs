// Assembles the static GitHub Pages site into _site/ without external dependencies:
//   _site/index.html      web case study (site/index.html)
//   _site/assets/         screenshots and diagrams
//   _site/demo/           the static prototype
//   _site/downloads/      committed PDF and DOCX deliverables
import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const SITE = join(ROOT, '_site');

rmSync(SITE, { recursive: true, force: true });
mkdirSync(SITE, { recursive: true });

cpSync(join(ROOT, 'site', 'index.html'), join(SITE, 'index.html'));
cpSync(join(ROOT, 'assets'), join(SITE, 'assets'), { recursive: true, filter: (src) => !src.endsWith('.md') });
cpSync(join(ROOT, 'prototype'), join(SITE, 'demo'), { recursive: true });
mkdirSync(join(SITE, 'downloads'));
for (const name of readdirSync(join(ROOT, 'deliverables'))) {
  if (/\.(pdf|docx)$/.test(name)) cpSync(join(ROOT, 'deliverables', name), join(SITE, 'downloads', name));
}
for (const required of ['index.html', 'demo/index.html', 'downloads']) {
  if (!existsSync(join(SITE, required))) throw new Error(`Missing ${required} in _site`);
}
console.log(`Assembled ${SITE}`);
