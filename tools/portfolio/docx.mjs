// Word (.docx) renderer for the case study. Content comes from content.mjs.
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  AlignmentType, BorderStyle, Document, ExternalHyperlink, Footer, HeadingLevel, ImageRun,
  LevelFormat, Packer, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} from 'docx';
import { meta, disclosure, snapshot, summary, whatIDid, skills, sections } from './content.mjs';

const NAVY = '10243E';
const BLUE = '1D5F94';
const SLATE = '5D6B7D';
const BORDER = 'DCE3EB';
const ROW_ALT = 'F7F9FB';
const AMBER_BG = 'FFF4D6';

// A4 with 18 mm margins.
const PAGE_W = 11906;
const MARGIN = 1020;
const CONTENT_W = PAGE_W - 2 * MARGIN; // DXA
const CONTENT_PX = Math.floor((CONTENT_W / 1440) * 96);

function runs(text, base = {}) {
  return String(text).split(/(\*\*.+?\*\*|`.+?`)/).filter(Boolean).map((part) => {
    if (part.startsWith('**')) return new TextRun({ ...base, text: part.slice(2, -2), bold: true });
    if (part.startsWith('`')) return new TextRun({ ...base, text: part.slice(1, -1), font: 'Consolas', size: 18 });
    return new TextRun({ ...base, text: part });
  });
}

const para = (text, opts = {}) => new Paragraph({ children: runs(text), spacing: { after: 120 }, ...opts });
const bullet = (text) => new Paragraph({ children: runs(text), numbering: { reference: 'bullets', level: 0 }, spacing: { after: 60 } });
const link = (label, url) => new ExternalHyperlink({ link: url, children: [new TextRun({ text: label, style: 'Hyperlink' })] });

function table(head, rows, widthsPct) {
  // Integer DXA widths that sum exactly to the content width.
  const widths = widthsPct.map((w) => Math.floor((w / 100) * CONTENT_W));
  widths[widths.length - 1] += CONTENT_W - widths.reduce((a, b) => a + b, 0);
  const border = { style: BorderStyle.SINGLE, size: 4, color: BORDER };
  const borders = { top: border, bottom: border, left: border, right: border };
  const cell = (text, i, header, shade) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    borders,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    shading: header ? { type: ShadingType.CLEAR, fill: NAVY, color: 'auto' }
      : shade ? { type: ShadingType.CLEAR, fill: ROW_ALT, color: 'auto' } : undefined,
    children: [new Paragraph({ children: runs(text, header ? { bold: true, color: 'FFFFFF', size: 18 } : { size: 18 }) })],
  });
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, i, true)) }),
      ...rows.map((row, r) => new TableRow({ cantSplit: true, children: row.map((c, i) => cell(c, i, false, r % 2 === 1)) })),
    ],
  });
}

function image(block, root) {
  const maxPx = block.maxHeightPct ? Math.floor(CONTENT_PX * (block.maxHeightPct / 100)) : CONTENT_PX;
  const width = Math.min(maxPx, block.width);
  const height = Math.round(width * (block.height / block.width));
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      keepNext: true,
      children: [new ImageRun({
        type: 'png',
        data: readFileSync(join(root, block.src)),
        transformation: { width, height },
        altText: { title: block.alt, description: block.alt, name: block.alt },
      })],
    }),
    new Paragraph({ children: runs(block.caption, { italics: true, color: SLATE, size: 17 }), spacing: { after: 200 } }),
  ];
}

function renderBlock(block, root) {
  switch (block.type) {
    case 'p': return [para(block.text)];
    case 'h3': return [new Paragraph({ heading: HeadingLevel.HEADING_2, children: runs(block.text) })];
    case 'bullets': return block.items.map(bullet);
    case 'callout': return block.lines.map((line) => new Paragraph({
      children: runs(line),
      spacing: { after: 100 },
      indent: { left: 200 },
      border: { left: { style: BorderStyle.SINGLE, size: 18, color: BLUE, space: 8 } },
    }));
    case 'table': return [table(block.head, block.rows, block.widths), new Paragraph({ spacing: { after: 120 }, children: [] })];
    case 'image': return image(block, root);
    default: throw new Error(`Unknown block type: ${block.type}`);
  }
}

function coverPage() {
  const tileW = Math.floor(CONTENT_W / snapshot.length);
  const tileWidths = snapshot.map(() => tileW);
  tileWidths[tileWidths.length - 1] += CONTENT_W - tileW * snapshot.length;
  const none = { style: BorderStyle.SINGLE, size: 4, color: 'FFFFFF' };
  const tiles = new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: tileWidths,
    rows: [new TableRow({ children: snapshot.map((t, i) => new TableCell({
      width: { size: tileWidths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: ROW_ALT, color: 'auto' },
      borders: { top: none, bottom: none, left: none, right: none },
      margins: { top: 100, bottom: 100, left: 120, right: 120 },
      children: [
        new Paragraph({ children: [new TextRun({ text: t.value, bold: true, size: 30, color: NAVY })] }),
        new Paragraph({ children: [new TextRun({ text: t.label, size: 17, color: SLATE })] }),
      ],
    })) })],
  });

  return [
    new Paragraph({ children: [new TextRun({ text: `BUSINESS ANALYSIS CASE STUDY · ${meta.author.toUpperCase()}`, bold: true, color: BLUE, size: 18 })], spacing: { after: 80 } }),
    new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun(meta.title)] }),
    new Paragraph({ children: [new TextRun({ text: meta.subtitle, size: 24, color: SLATE })], spacing: { after: 160 } }),
    new Paragraph({ children: [new TextRun({ text: 'Live demo: ', bold: true }), link(meta.demoUrl, meta.demoUrl)], spacing: { after: 40 } }),
    new Paragraph({ children: [new TextRun({ text: 'Repository: ', bold: true }), link(meta.repoUrl, meta.repoUrl)], spacing: { after: 200 } }),
    new Paragraph({
      children: [new TextRun({ text: 'Scope disclosure. ', bold: true }), new TextRun(disclosure)],
      shading: { type: ShadingType.CLEAR, fill: AMBER_BG, color: 'auto' },
      border: { left: { style: BorderStyle.SINGLE, size: 24, color: '9B6100', space: 6 } },
      spacing: { after: 200 },
    }),
    tiles,
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('Problem')] }),
    para(summary.problem),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('Goal')] }),
    para(summary.goal),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('My role')] }),
    para(summary.role),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('What I did')] }),
    ...whatIDid.map(bullet),
    new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('Skills demonstrated')] }),
    para(skills.join(' · ')),
  ];
}

export async function buildDocx(root) {
  const children = [...coverPage()];
  sections.forEach((s, i) => {
    children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(`${i + 1}. ${s.title}`)] }));
    s.blocks.forEach((b) => children.push(...renderBlock(b, root)));
  });

  const doc = new Document({
    creator: meta.author,
    title: `${meta.title} — Business Analysis Case Study`,
    description: disclosure,
    styles: {
      default: { document: { run: { font: 'Calibri', size: 21, color: '071527' }, paragraph: { spacing: { line: 276 } } } },
      paragraphStyles: [
        { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal', run: { size: 48, bold: true, color: NAVY }, paragraph: { spacing: { after: 80 } } },
        { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 32, bold: true, color: NAVY }, paragraph: { spacing: { before: 0, after: 160 }, outlineLevel: 0 } },
        { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true, run: { size: 24, bold: true, color: NAVY }, paragraph: { spacing: { before: 240, after: 100 }, keepNext: true, outlineLevel: 1 } },
      ],
    },
    numbering: {
      config: [{ reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 240 } } } }] }],
    },
    sections: [{
      properties: { page: { size: { width: PAGE_W, height: 16838 }, margin: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN } } },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({ text: `Smart Warehouse BA case study · v${meta.version} · synthetic data · page `, size: 16, color: SLATE }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, color: SLATE }),
          ],
        })] }),
      },
      children,
    }],
  });
  return Packer.toBuffer(doc);
}
