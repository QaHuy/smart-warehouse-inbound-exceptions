// HTML renderers for the web case study (GitHub Pages landing page), its print/PDF
// variant, and the one-page summary. All content comes from content.mjs.
import { meta, disclosure, snapshot, summary, whatIDid, decisions, skills, sections } from './content.mjs';

const escape = (text) => String(text)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export const inline = (text) => escape(text)
  .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  .replace(/`(.+?)`/g, '<code>$1</code>');

const DOWNLOADS = {
  casePdf: 'Smart-Warehouse-BA-Case-Study.pdf',
  caseDocx: 'Smart-Warehouse-BA-Case-Study.docx',
  onePager: 'Smart-Warehouse-BA-One-Pager.pdf',
};
export { DOWNLOADS };

const baseCss = `
:root {
  color-scheme: light;
  --navy-950: #071527; --navy-900: #10243e; --slate-700: #42536a; --slate-600: #5d6b7d;
  --slate-200: #dce3eb; --slate-100: #eef2f6; --slate-050: #f7f9fb; --white: #ffffff;
  --blue: #1d5f94; --amber: #9b6100; --amber-bg: #fff4d6; --green: #176b52; --red: #a63c32;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--white); color: var(--navy-950);
  font-family: Inter, Aptos, "Segoe UI", Arial, sans-serif; line-height: 1.5; }
code { font-family: Consolas, "Cascadia Mono", monospace; font-size: 0.88em;
  background: var(--slate-100); padding: 0.05em 0.3em; border-radius: 4px; }
.eyebrow { text-transform: uppercase; letter-spacing: 0.12em; font-weight: 700; color: var(--blue); }
.disclosure { background: var(--amber-bg); border-left: 4px solid var(--amber); }
.tiles { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); }
.tile { background: var(--slate-050); border: 1px solid var(--slate-200); border-radius: 10px; }
.tile b { display: block; color: var(--navy-900); }
.tile span { color: var(--slate-600); }
table { width: 100%; border-collapse: collapse; }
th { background: var(--navy-900); color: var(--white); text-align: left; font-weight: 600; }
td, th { border: 1px solid var(--slate-200); vertical-align: top; }
tr:nth-child(even) td { background: var(--slate-050); }
figure { margin: 0; }
figure img { width: 100%; height: auto; border: 1px solid var(--slate-200); border-radius: 8px; display: block; }
figcaption { color: var(--slate-600); }
.callout { border-left: 4px solid var(--blue); background: var(--slate-050); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; padding: 0; margin: 0; list-style: none; }
.chips li { background: var(--slate-100); border-radius: 999px; }
`;

function renderBlock(block, assetBase, print) {
  switch (block.type) {
    case 'p':
      return `<p>${inline(block.text)}</p>`;
    case 'h3':
      return `<h3>${inline(block.text)}</h3>`;
    case 'bullets':
      return `<ul>${block.items.map((item) => `<li>${inline(item)}</li>`).join('')}</ul>`;
    case 'callout':
      return `<div class="callout">${block.lines.map((line) => `<p>${inline(line)}</p>`).join('')}</div>`;
    case 'table': {
      const cols = block.widths.map((w) => `<col style="width:${w}%">`).join('');
      const head = block.head.map((h) => `<th scope="col">${inline(h)}</th>`).join('');
      const rows = block.rows.map((row) => `<tr>${row.map((c) => `<td>${inline(c)}</td>`).join('')}</tr>`).join('');
      return `<div class="table-wrap"><table><colgroup>${cols}</colgroup><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table></div>`;
    }
    case 'image': {
      const style = print && block.maxHeightPct ? ` style="max-width:${block.maxHeightPct}%"` : '';
      return `<figure${style}><img src="${assetBase}${block.src}" alt="${escape(block.alt)}" width="${block.width}" height="${block.height}" loading="lazy"><figcaption>${inline(block.caption)}</figcaption></figure>`;
    }
    default:
      throw new Error(`Unknown block type: ${block.type}`);
  }
}

const caseCss = `
${baseCss}
body { font-size: 16px; background: var(--slate-050); }
.wrap { max-width: 980px; margin: 0 auto; padding: 0 16px; }
header.hero { background: var(--navy-950); color: var(--white); padding: 48px 0 40px; }
header.hero .eyebrow { color: #9cc7ec; font-size: 13px; margin: 0 0 12px; }
header.hero h1 { font-size: clamp(30px, 5vw, 46px); line-height: 1.08; margin: 0 0 12px; letter-spacing: -0.02em; }
header.hero p.sub { color: var(--slate-200); font-size: 18px; margin: 0 0 24px; max-width: 760px; }
.actions { display: flex; flex-wrap: wrap; gap: 10px; }
.btn { display: inline-block; padding: 10px 16px; border-radius: 8px; font-weight: 600; text-decoration: none;
  border: 1px solid #3c5677; color: var(--white); }
.btn.primary { background: #2f7bbf; border-color: #2f7bbf; }
.btn:focus-visible, a:focus-visible { outline: 3px solid #f2b84b; outline-offset: 2px; }
main { padding: 28px 0 56px; }
.card { background: var(--white); border: 1px solid var(--slate-200); border-radius: 14px; padding: 24px; margin-bottom: 20px; }
.disclosure { padding: 12px 16px; border-radius: 8px; margin: 0 0 20px; font-size: 15px; }
.tiles { gap: 12px; margin-bottom: 20px; }
.tile { padding: 14px; }
.tile b { font-size: 24px; }
.tile span { font-size: 13px; }
.summary-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
.summary-grid h3 { margin-top: 0; }
h2 { font-size: 26px; margin: 0 0 14px; letter-spacing: -0.01em; }
h2 .num { color: var(--blue); margin-right: 8px; }
h3 { font-size: 18px; margin: 22px 0 8px; }
.table-wrap { overflow-x: auto; margin: 8px 0 16px; }
table { font-size: 14.5px; min-width: 560px; }
td, th { padding: 8px 10px; }
figure { margin: 12px 0 18px; }
figcaption { font-size: 13.5px; margin-top: 6px; }
.callout { padding: 6px 16px; border-radius: 8px; margin: 8px 0 16px; }
.chips li { padding: 4px 12px; font-size: 14px; }
nav.toc ol { columns: 2; margin: 0; padding-left: 20px; }
nav.toc a { color: var(--blue); }
footer { color: var(--slate-600); font-size: 14px; padding: 0 0 40px; }
footer a { color: var(--blue); }
@media screen and (max-width: 760px) {
  .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .summary-grid { grid-template-columns: 1fr; }
  nav.toc ol { columns: 1; }
  .card { padding: 18px; }
}
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }

/* Print / PDF */
@page { size: A4; margin: 16mm 15mm 16mm; }
body.print { background: var(--white); font-size: 10.5pt; }
body.print header.hero { padding: 0 0 6mm; background: var(--white); color: var(--navy-950); border-bottom: 2px solid var(--navy-900); margin-bottom: 5mm; }
body.print header.hero .eyebrow { color: var(--blue); }
body.print header.hero p.sub { color: var(--slate-700); font-size: 12pt; margin-bottom: 3mm; }
body.print header.hero h1 { font-size: 24pt; }
body.print .wrap { max-width: none; padding: 0; }
body.print main { padding: 0; }
body.print .card { border: 0; padding: 0; margin: 0 0 7mm; background: none; }
body.print .summary-grid { grid-template-columns: 1fr; gap: 0; }
body.print .summary-grid h3 { margin-top: 10pt; }
body.print .chips li { font-size: 9pt; padding: 1pt 7pt; }
body.print code { white-space: nowrap; }
body.print table { min-width: 0; font-size: 9pt; }
body.print td, body.print th { padding: 3pt 5pt; }
body.print tr, body.print figure, body.print .callout { break-inside: avoid; }
body.print h2, body.print h3 { break-after: avoid; }
body.print .tile b { font-size: 16pt; }
body.print .links { font-size: 9.5pt; color: var(--slate-700); margin: 0; }
body.print .links a { color: var(--blue); }
body.print nav.toc { display: none; }
`;

export function renderCaseStudy({ assetBase = '', print = false } = {}) {
  const links = print
    ? `<p class="links">Live demo: <a href="${meta.demoUrl}">${meta.demoUrl}</a><br>Repository: <a href="${meta.repoUrl}">${meta.repoUrl}</a></p>`
    : `<div class="actions">
        <a class="btn primary" href="demo/">Open live demo</a>
        <a class="btn" href="downloads/${DOWNLOADS.casePdf}">Case study (PDF)</a>
        <a class="btn" href="downloads/${DOWNLOADS.caseDocx}">Case study (Word)</a>
        <a class="btn" href="downloads/${DOWNLOADS.onePager}">One-page summary (PDF)</a>
        <a class="btn" href="${meta.repoUrl}">Repository</a>
      </div>`;

  const toc = sections.map((s, i) => `<li><a href="#${s.id}">${escape(s.title)}</a></li>`).join('');
  const body = sections.map((s, i) => `
    <section class="card section${i === 0 ? ' first' : ''}" id="${s.id}" aria-labelledby="${s.id}-h">
      <h2 id="${s.id}-h"><span class="num">${i + 1}.</span>${escape(s.title)}</h2>
      ${s.blocks.map((b) => renderBlock(b, assetBase, print)).join('\n')}
    </section>`).join('\n');

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Warehouse BA Case Study</title>
<meta name="description" content="${escape(meta.subtitle)} by ${escape(meta.author)}. Requirements, BPMN, traceability, and 14/14 passing UAT on a synthetic WMS/WCS case.">
<style>${caseCss}</style>
</head>
<body class="${print ? 'print' : ''}">
<header class="hero">
  <div class="wrap">
    <p class="eyebrow">Business analysis portfolio · ${escape(meta.author)}</p>
    <h1>${escape(meta.title)}</h1>
    <p class="sub">${escape(meta.subtitle)} — from problem framing and stakeholder analysis to traceable requirements, process models, and executed UAT.</p>
    ${links}
  </div>
</header>
<main class="wrap">
  <p class="disclosure"><strong>Scope disclosure.</strong> ${escape(disclosure)}</p>
  <div class="tiles">${snapshot.map((t) => `<div class="tile"><b>${escape(t.value)}</b><span>${escape(t.label)}</span></div>`).join('')}</div>
  <section class="card" aria-label="Summary">
    <div class="summary-grid">
      <div><h3>Problem</h3><p>${inline(summary.problem)}</p></div>
      <div><h3>Goal</h3><p>${inline(summary.goal)}</p></div>
      <div><h3>My role</h3><p>${inline(summary.role)}</p></div>
    </div>
    <h3>What I did</h3>
    <ul>${whatIDid.map((x) => `<li>${inline(x)}</li>`).join('')}</ul>
    <h3>Skills demonstrated</h3>
    <ul class="chips">${skills.map((s) => `<li>${escape(s)}</li>`).join('')}</ul>
  </section>
  <nav class="toc card" aria-label="Contents"><h2>Contents</h2><ol>${toc}</ol></nav>
  ${body}
</main>
<footer class="wrap">
  <p>Version ${meta.version} · ${meta.date} · All examples are synthetic. Source and full artefacts: <a href="${meta.repoUrl}">${meta.repoUrl}</a></p>
</footer>
</body>
</html>`;
}

const onePagerCss = `
${baseCss}
@page { size: A4; margin: 11mm 12mm; }
body { font-size: 8.9pt; line-height: 1.38; }
header { display: flex; justify-content: space-between; align-items: flex-end; gap: 6mm;
  border-bottom: 2px solid var(--navy-900); padding-bottom: 2.5mm; margin-bottom: 2.5mm; }
header .eyebrow { font-size: 7.5pt; margin: 0 0 1mm; }
h1 { font-size: 17.5pt; line-height: 1.08; margin: 0; letter-spacing: -0.01em; }
header .sub { margin: 1mm 0 0; color: var(--slate-700); font-size: 9.5pt; }
header .links { text-align: right; font-size: 8pt; color: var(--slate-700); white-space: nowrap; }
header .links a { color: var(--blue); text-decoration: none; }
header .links b { color: var(--navy-950); }
.disclosure { padding: 1.6mm 3mm; font-size: 8pt; margin: 0 0 2.5mm; }
.tiles { gap: 2mm; margin-bottom: 2.5mm; }
.tile { padding: 1.6mm 2.5mm; }
.tile b { font-size: 12.5pt; }
.tile span { font-size: 7.5pt; }
h2 { font-size: 10pt; margin: 2.2mm 0 1mm; color: var(--navy-900); text-transform: uppercase; letter-spacing: 0.06em; }
p { margin: 0 0 1.4mm; }
ul { margin: 0 0 1.4mm; padding-left: 4.2mm; }
li { margin-bottom: 0.8mm; }
.cols { display: grid; grid-template-columns: 1.08fr 0.92fr; gap: 5mm; }
figure img { border-radius: 4px; }
figcaption { font-size: 7.3pt; margin-top: 0.8mm; }
table { font-size: 7.9pt; }
td, th { padding: 1mm 1.6mm; }
.skills { color: var(--slate-700); }
footer { margin-top: 2mm; font-size: 7.3pt; color: var(--slate-600); border-top: 1px solid var(--slate-200); padding-top: 1.5mm; }
`;

export function renderOnePager({ assetBase = '' } = {}) {
  const decisionRows = decisions.map(([id, name, rule]) => `<tr><td><b>${escape(name)}</b></td><td>${inline(rule)}</td></tr>`).join('');
  return `<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Smart Warehouse BA One-Pager</title><style>${onePagerCss}</style></head>
<body>
<header>
  <div>
    <p class="eyebrow">Business analysis case study · ${escape(meta.author)} · sole BA, self-directed</p>
    <h1>${escape(meta.title)}</h1>
    <p class="sub">${escape(meta.subtitle)}</p>
  </div>
  <div class="links">
    <b>Live demo</b> <a href="${meta.demoUrl}">${meta.demoUrl.replace('https://', '')}</a><br>
    <b>Full case study</b> <a href="${meta.siteUrl}">${meta.siteUrl.replace('https://', '')}</a><br>
    <b>Repository</b> <a href="${meta.repoUrl}">${meta.repoUrl.replace('https://', '')}</a>
  </div>
</header>
<p class="disclosure"><strong>Scope disclosure.</strong> ${escape(disclosure)}</p>
<div class="tiles">${snapshot.map((t) => `<div class="tile"><b>${escape(t.value)}</b><span>${escape(t.label)}</span></div>`).join('')}</div>
<figure>
  <img src="${assetBase}assets/diagrams/to-be-at-a-glance.png" alt="To-Be inbound flow at a glance: happy path on top, controlled exception paths below">
</figure>
<div class="cols">
  <div>
    <h2>Problem</h2><p>${inline(summary.problem)}</p>
    <h2>Goal</h2><p>${inline(summary.goal)}</p>
    <h2>What I did</h2>
    <ul>${whatIDid.map((x) => `<li>${inline(x)}</li>`).join('')}</ul>
  </div>
  <div>
    <h2>Key decisions</h2>
    <table><tbody>${decisionRows}</tbody></table>
    <h2>Results — and what is not claimed</h2>
    <ul>
      <li><b>14 / 14</b> automated UAT cases pass, including negative paths, duplicate events, and metric reconciliation.</li>
      <li>Traceability BN → FR → BR → US → UAT with <b>0 orphaned requirements</b>.</li>
      <li>Not claimed: interviews, site observation, measured benefit, or real device integration — next step is discovery with real users.</li>
    </ul>
    <h2>Skills demonstrated</h2>
    <p class="skills">${skills.map(escape).join(' · ')}</p>
  </div>
</div>
<footer>Version ${meta.version} · ${meta.date} · Synthetic data only. Full artefacts (SRS, user stories, BPMN, OpenAPI, SQL, RTM, UAT) are in the repository.</footer>
</body>
</html>`;
}
