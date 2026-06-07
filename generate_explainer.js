const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, BorderStyle, WidthType, ShadingType,
  VerticalAlign, HeadingLevel, PageBreak, TableLayoutType
} = require('docx');
const fs = require('fs');

// ─── Color constants ───────────────────────────────────────────────────────
const NAVY      = '0F172A';
const BLUE      = '3B82F6';
const GREEN     = '10B981';
const GREY_TEXT = '64748B';
const BODY_TEXT = '374151';
const RED_BG    = 'FEF2F2';
const RED_TEXT  = 'DC2626';
const BLUE_BG   = 'EFF6FF';
const GREEN_BG  = 'ECFDF5';
const GREY_BG   = 'F8FAFC';
const WHITE     = 'FFFFFF';
const GREEN_DRK = '059669';

// ─── Width constants ───────────────────────────────────────────────────────
const PAGE_WIDTH    = 9026; // A4 content width with 1440 margins on each side
const COL3          = Math.floor(PAGE_WIDTH / 3); // ~3008
const COL3_R        = PAGE_WIDTH - COL3 * 2;       // remainder for last col

// ─── Helper: no border ────────────────────────────────────────────────────
const noBorder = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder, insideH: noBorder, insideV: noBorder };

// ─── Helper: standard cell borders ────────────────────────────────────────
function stdBorder(color = 'CCCCCC') {
  const b = { style: BorderStyle.SINGLE, size: 4, color };
  return { top: b, bottom: b, left: b, right: b };
}

// ─── Helper: spacer paragraph ─────────────────────────────────────────────
function spacer(pt = 6) {
  return new Paragraph({ children: [new TextRun('')], spacing: { before: 0, after: pt * 20 } });
}

// ─── Helper: text run builder ─────────────────────────────────────────────
function tr(text, opts = {}) {
  return new TextRun({
    text,
    font: 'Arial',
    bold: opts.bold || false,
    italics: opts.italic || false,
    size: (opts.size || 11) * 2,
    color: opts.color || '000000',
  });
}

// ─── Helper: centered paragraph ───────────────────────────────────────────
function centeredPara(runs, spacingAfter = 0) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: spacingAfter },
    children: Array.isArray(runs) ? runs : [runs],
  });
}

// ─── Helper: bullet paragraph ─────────────────────────────────────────────
function bullet(text, bold_prefix = '') {
  const children = [];
  if (bold_prefix) {
    children.push(tr(bold_prefix + ' ', { bold: true, size: 11, color: BODY_TEXT }));
  }
  children.push(tr(text, { size: 11, color: BODY_TEXT }));
  return new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    children,
    spacing: { after: 80 },
  });
}

// ─── Helper: full-width single-cell shaded box ────────────────────────────
function shadedBox(children, bgColor, leftBorderColor = null) {
  const leftBorder = leftBorderColor
    ? { style: BorderStyle.SINGLE, size: 24, color: leftBorderColor }
    : noBorder;
  return new Table({
    width: { size: PAGE_WIDTH, type: WidthType.DXA },
    columnWidths: [PAGE_WIDTH],
    layout: TableLayoutType.FIXED,
    borders: {
      top: noBorder,
      bottom: noBorder,
      left: leftBorder,
      right: noBorder,
      insideH: noBorder,
      insideV: noBorder,
    },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: PAGE_WIDTH, type: WidthType.DXA },
            shading: { fill: bgColor, type: ShadingType.CLEAR },
            margins: { top: 120, bottom: 120, left: 180, right: 180 },
            borders: {
              top: noBorder,
              bottom: noBorder,
              left: leftBorderColor ? { style: BorderStyle.SINGLE, size: 24, color: leftBorderColor } : noBorder,
              right: noBorder,
            },
            children,
          }),
        ],
      }),
    ],
  });
}

// ─── Helper: "What it does" feature box ───────────────────────────────────
function whatItDoesBox(text) {
  return shadedBox(
    [
      new Paragraph({
        spacing: { after: 60 },
        children: [
          tr('What it does: ', { bold: true, size: 11, color: NAVY }),
          tr(text, { size: 11, color: BODY_TEXT }),
        ],
      }),
    ],
    BLUE_BG
  );
}

// ─── Helper: Heading 1 paragraph ──────────────────────────────────────────
function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 240, after: 200 },
    children: [tr(text, { bold: true, size: 22, color: NAVY })],
  });
}

// ─── Helper: Heading 2 paragraph ──────────────────────────────────────────
function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 120 },
    children: [tr(text, { bold: true, size: 16, color: BLUE })],
  });
}

// ─── Helper: navy accent bar (full-width table, 1 col) ────────────────────
function accentBar() {
  return new Table({
    width: { size: PAGE_WIDTH, type: WidthType.DXA },
    columnWidths: [PAGE_WIDTH],
    layout: TableLayoutType.FIXED,
    borders: noBorders,
    rows: [
      new TableRow({
        height: { value: 200, rule: 'exact' },
        children: [
          new TableCell({
            width: { size: PAGE_WIDTH, type: WidthType.DXA },
            shading: { fill: NAVY, type: ShadingType.CLEAR },
            borders: noBorders,
            children: [new Paragraph({ children: [new TextRun('')] })],
          }),
        ],
      }),
    ],
  });
}

// ══════════════════════════════════════════════════════════════════════════
// PAGE 1 — COVER
// ══════════════════════════════════════════════════════════════════════════
function buildCoverPage() {
  const content = [];

  // Top accent bar
  content.push(accentBar());
  content.push(spacer(18));

  // Product name
  content.push(centeredPara(
    tr('VirtualCA', { bold: true, size: 52, color: NAVY }),
    60
  ));

  // Tagline
  content.push(centeredPara(
    tr('Upload your Tally file. Get a full audit in 30 seconds.', { size: 18, color: BLUE }),
    200
  ));

  // Spacer
  content.push(spacer(10));

  // Subtitle box
  content.push(new Table({
    width: { size: PAGE_WIDTH, type: WidthType.DXA },
    columnWidths: [PAGE_WIDTH],
    layout: TableLayoutType.FIXED,
    borders: noBorders,
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: PAGE_WIDTH, type: WidthType.DXA },
            shading: { fill: BLUE_BG, type: ShadingType.CLEAR },
            margins: { top: 180, bottom: 180, left: 360, right: 360 },
            borders: noBorders,
            children: [
              centeredPara(
                tr('AI-Powered Accounting Intelligence for Indian SMBs & CA Firms', { bold: true, size: 13, color: NAVY }),
                80
              ),
              centeredPara(
                tr('Built for Tally users. Designed for India.', { italic: true, size: 11, color: GREY_TEXT }),
                0
              ),
            ],
          }),
        ],
      }),
    ],
  }));

  content.push(spacer(24));

  // Three stat pills
  const statCell = (bigText, bigColor, smallText) => new TableCell({
    width: { size: COL3, type: WidthType.DXA },
    borders: noBorders,
    margins: { top: 100, bottom: 100, left: 80, right: 80 },
    children: [
      centeredPara(tr(bigText, { bold: true, size: 24, color: bigColor }), 40),
      centeredPara(tr(smallText, { size: 9, color: GREY_TEXT }), 0),
    ],
  });

  content.push(new Table({
    width: { size: PAGE_WIDTH, type: WidthType.DXA },
    columnWidths: [COL3, COL3, COL3_R],
    layout: TableLayoutType.FIXED,
    borders: noBorders,
    rows: [
      new TableRow({
        children: [
          statCell('20+', NAVY, 'Accounting Rules Checked'),
          statCell('30 sec', BLUE, 'Full Audit Time'),
          statCell('9+', GREEN, 'Compliance Items Tracked'),
        ],
      }),
    ],
  }));

  content.push(spacer(24));

  // Bottom accent bar
  content.push(accentBar());

  // Page break
  content.push(new Paragraph({ children: [new PageBreak()] }));

  return content;
}

// ══════════════════════════════════════════════════════════════════════════
// PAGE 2 — THE PROBLEM
// ══════════════════════════════════════════════════════════════════════════
function buildProblemPage() {
  const content = [];

  content.push(h1('The Problem With Manual Accounting'));

  // Intro paragraph
  content.push(new Paragraph({
    spacing: { after: 200 },
    children: [
      tr(
        'Every Indian SMB using Tally faces the same invisible crisis. Books get updated every month, but errors pile up silently. By the time a CA reviews them — it\'s tax season, deadlines have passed, and penalties have already started accumulating. The problems aren\'t obvious. That is what makes them dangerous.',
        { size: 11, color: BODY_TEXT }
      ),
    ],
  }));

  // Problem block builder
  const problemBlock = (heading, body) => {
    const block = shadedBox(
      [
        new Paragraph({
          spacing: { after: 80 },
          children: [tr(heading, { bold: true, size: 12, color: RED_TEXT })],
        }),
        new Paragraph({
          spacing: { after: 0 },
          children: [tr(body, { size: 11, color: BODY_TEXT })],
        }),
      ],
      RED_BG,
      RED_TEXT
    );
    return block;
  };

  content.push(problemBlock(
    'Wrong Ledger Groupings — Invisible Until It\'s Too Late',
    'Accountants manually create ledger groups in Tally. TDS Receivable gets placed under Duties & Taxes instead of Current Assets. GST Input Credit lands under the wrong group. These errors don\'t cause Tally to crash — they silently distort your Balance Sheet and P&L. Your bank won\'t approve a loan based on wrong financials. Your auditor will flag it. You\'ll pay to fix it.'
  ));
  content.push(spacer(12));

  content.push(problemBlock(
    'Compliance Deadlines Are Missed Every Month',
    'TDS must be deposited by the 7th. GSTR-1 is due by the 11th. GSTR-3B by the 20th. Professional Tax by the 21st. Miss any one and the penalties compound — \u20b9200/day for TDS alone, plus 1.5% monthly interest. Most businesses have no system tracking these. They rely on memory or WhatsApp reminders.'
  ));
  content.push(spacer(12));

  content.push(problemBlock(
    'Bank Reconciliation Takes Days — And Is Done Wrong',
    'Matching your bank statement against Tally entries is done by hand. Rows are compared line by line across two Excel sheets. Duplicate entries go unnoticed. Unmatched transactions get ignored. It takes 2-3 days for a typical business. And the reconciliation is rarely 100% accurate.'
  ));
  content.push(spacer(12));

  content.push(new Paragraph({ children: [new PageBreak()] }));

  return content;
}

// ══════════════════════════════════════════════════════════════════════════
// PAGE 3 — SOLUTION + HOW IT WORKS
// ══════════════════════════════════════════════════════════════════════════
function buildSolutionPage() {
  const content = [];

  content.push(h1('What VirtualCA Does'));

  content.push(new Paragraph({
    spacing: { after: 200 },
    children: [
      tr(
        'VirtualCA is a web-based platform that reads your Tally data — in any format — and runs a complete accounting audit automatically. It checks every ledger against 20+ accounting rules, calculates compliance deadlines, detects TDS shortfalls, reconciles your bank statement, and answers your questions like a real CA. Everything in under 30 seconds.',
        { size: 11, color: BODY_TEXT }
      ),
    ],
  }));

  // How it works — 3-column table
  const stepCell = (numText, numColor, titleText, bodyText, tagText) => new TableCell({
    width: { size: COL3, type: WidthType.DXA },
    borders: {
      top: noBorder,
      bottom: noBorder,
      left: noBorder,
      right: { style: BorderStyle.SINGLE, size: 4, color: 'CCCCCC' },
    },
    margins: { top: 160, bottom: 160, left: 160, right: 160 },
    children: [
      new Paragraph({
        spacing: { after: 80 },
        children: [tr(numText, { bold: true, size: 28, color: numColor })],
      }),
      new Paragraph({
        spacing: { after: 80 },
        children: [tr(titleText, { bold: true, size: 13, color: NAVY })],
      }),
      new Paragraph({
        spacing: { after: 80 },
        children: [tr(bodyText, { size: 11, color: BODY_TEXT })],
      }),
      new Paragraph({
        spacing: { after: 0 },
        children: [tr(tagText, { size: 9, color: GREY_TEXT, italic: true })],
      }),
    ],
  });

  content.push(new Table({
    width: { size: PAGE_WIDTH, type: WidthType.DXA },
    columnWidths: [COL3, COL3, COL3_R],
    layout: TableLayoutType.FIXED,
    borders: noBorders,
    rows: [
      new TableRow({
        children: [
          stepCell('01', BLUE, 'Upload Your File',
            'Upload your Tally Trial Balance (Excel), Tally XML, Ledger Dump, Bank Statement CSV, or GST JSON file. VirtualCA auto-detects the format and maps your columns.',
            'Supported: Excel \u00b7 XML \u00b7 CSV \u00b7 JSON'),
          stepCell('02', GREEN, 'AI Runs The Audit',
            'The analysis engine checks every ledger against 20+ rules. Wrong groupings are flagged. Balances are verified. Compliance deadlines are calculated. TDS sections are tallied. All in seconds.',
            'Result: Critical Errors \u00b7 Review Items \u00b7 All Clear'),
          stepCell('03', NAVY, 'Get Exact Fix Instructions',
            'Every error comes with: the accounting rule violated, the correct ledger group, an auto-generated journal entry, and step-by-step Tally navigation path. Your team can fix it in minutes.',
            'Output: Journal Entries \u00b7 Tally Paths \u00b7 Export Ready'),
        ],
      }),
    ],
  }));

  content.push(new Paragraph({ children: [new PageBreak()] }));

  return content;
}

// ══════════════════════════════════════════════════════════════════════════
// PAGE 4 — TIME & MONEY SAVINGS
// ══════════════════════════════════════════════════════════════════════════
function buildSavingsPage() {
  const content = [];

  content.push(h1('How VirtualCA Saves You Time & Money'));

  // Comparison table
  const col1 = Math.floor(PAGE_WIDTH * 0.28);
  const col2 = Math.floor(PAGE_WIDTH * 0.36);
  const col3 = PAGE_WIDTH - col1 - col2;

  const headerRow = new TableRow({
    tableHeader: true,
    children: [
      new TableCell({
        width: { size: col1, type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        borders: stdBorder(NAVY),
        children: [new Paragraph({ children: [tr('Task', { bold: true, size: 11, color: WHITE })] })],
      }),
      new TableCell({
        width: { size: col2, type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        borders: stdBorder(NAVY),
        children: [new Paragraph({ children: [tr('WITHOUT VirtualCA', { bold: true, size: 11, color: WHITE })] })],
      }),
      new TableCell({
        width: { size: col3, type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        borders: stdBorder(NAVY),
        children: [new Paragraph({ children: [tr('WITH VirtualCA', { bold: true, size: 11, color: WHITE })] })],
      }),
    ],
  });

  const tableRows = [
    ['Monthly ledger audit', '2\u20133 hours (manual CA review)', '30 seconds (automated)'],
    ['Bank reconciliation', '2\u20133 days per month', 'Under 5 minutes'],
    ['TDS tracking', 'Manual Excel sheet', 'Auto section-wise with interest calc'],
    ['Compliance deadline tracking', 'Memory / WhatsApp', 'Live calendar with overdue alerts'],
    ['Fixing ledger errors', 'CA charges \u20b92,000\u2013\u20b95,000 per visit', 'Step-by-step fix inside the app'],
    ['Error discovery', 'At year-end during audit', 'Real-time, every upload'],
    ['PT calculation (WB)', 'Manual slab lookup per employee', 'Automated with journal entries'],
  ];

  const dataRows = tableRows.map((row, idx) => {
    const bg = idx % 2 === 0 ? WHITE : GREY_BG;
    return new TableRow({
      children: row.map((cell, cIdx) => {
        const width = cIdx === 0 ? col1 : cIdx === 1 ? col2 : col3;
        return new TableCell({
          width: { size: width, type: WidthType.DXA },
          shading: { fill: bg, type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          borders: stdBorder('CCCCCC'),
          children: [new Paragraph({
            children: [tr(cell, { size: 10, color: BODY_TEXT, bold: cIdx === 0 })],
          })],
        });
      }),
    });
  });

  content.push(new Table({
    width: { size: PAGE_WIDTH, type: WidthType.DXA },
    columnWidths: [col1, col2, col3],
    layout: TableLayoutType.FIXED,
    rows: [headerRow, ...dataRows],
  }));

  content.push(spacer(16));

  // Savings callout box
  content.push(shadedBox(
    [
      new Paragraph({
        spacing: { after: 100 },
        children: [tr('The Real Cost of Not Auditing Regularly', { bold: true, size: 12, color: GREEN_DRK })],
      }),
      bullet('TDS late deposit penalty: \u20b9200 per day + 1.5% monthly interest (Section 201(1A))'),
      bullet('GSTR late filing: \u20b950/day (\u20b920/day for NIL returns) + 18% interest'),
      bullet('PT late deposit (Kolkata): Penalty up to 2x the tax amount'),
      bullet('Wrong ledger grouping caught at audit: CA rectification fee \u20b95,000\u2013\u20b920,000'),
      bullet('Bank loan rejection due to wrong Balance Sheet: Opportunity cost \u2014 unlimited'),
    ],
    GREEN_BG
  ));

  content.push(new Paragraph({ children: [new PageBreak()] }));

  return content;
}

// ══════════════════════════════════════════════════════════════════════════
// PAGES 5-7 — FEATURES IN DETAIL
// ══════════════════════════════════════════════════════════════════════════
function buildFeaturesPages() {
  const content = [];

  content.push(h1('Features \u2014 In Detail'));

  // ── Feature 1: Smart File Upload ──────────────────────────────────────
  content.push(h2('Smart File Upload & Data Mapping'));
  content.push(whatItDoesBox(
    'VirtualCA accepts your data in 5 different formats \u2014 however Tally exported it. You don\'t need to reformat anything. Just upload and the system handles the rest.'
  ));
  content.push(spacer(8));
  content.push(bullet('Supports: Tally Trial Balance (Excel/CSV), Tally XML export, Ledger Dump (Excel), Bank Statement (CSV/Excel from any bank \u2014 HDFC, ICICI, SBI, Axis, Kotak), GST JSON (GSTR-2A/2B from GST portal)'));
  content.push(bullet('Auto-detects column headers and maps them to required fields (Ledger Name, Group, Closing Balance, Dr/Cr)'));
  content.push(bullet('If column names are non-standard, a Data Mapping Screen lets you manually correct the mapping with dropdowns'));
  content.push(bullet('Chart of Accounts Mapping: if you use custom group names in Tally, you can map them to standard Tally groups so the analysis engine can read them correctly'));
  content.push(bullet('Mapping preferences are saved per company \u2014 you never re-map the same file twice'));
  content.push(bullet('Drag & drop or click-to-browse upload interface'));
  content.push(spacer(12));

  // ── Feature 2: Ledger Analysis Engine ────────────────────────────────
  content.push(h2('Ledger Analysis Engine \u2014 20 Accounting Rules'));
  content.push(whatItDoesBox(
    'The core of VirtualCA. Every ledger in your Trial Balance is checked against 20 accounting rules derived from Indian accounting standards (AS), double-entry principles, and Tally\'s own grouping logic. Errors are classified as Critical or Review.'
  ));
  content.push(spacer(8));
  content.push(bullet('TDS Receivable: must be under Current Assets \u2014 not Duties & Taxes (Critical)'));
  content.push(bullet('TDS Payable: must be under Duties & Taxes \u2014 not Current Assets (Critical)'));
  content.push(bullet('GST Input Tax Credit (ITC): must be Current Assets (Critical)'));
  content.push(bullet('GST Output Tax Payable: must be Duties & Taxes (Critical)'));
  content.push(bullet('Bank Interest Received: must be Indirect Incomes \u2014 not Indirect Expenses (Critical)'));
  content.push(bullet('Capital / Partner\'s Capital: must be Capital Account \u2014 not Loans (Critical)'));
  content.push(bullet('Drawings: must be Capital Account \u2014 not Indirect Expenses (Critical)'));
  content.push(bullet('Prepaid Expenses: must be Current Assets \u2014 not Indirect Expenses (Critical)'));
  content.push(bullet('Loan from Director: must be Loans (Liability) \u2014 not Capital Account (Critical)'));
  content.push(bullet('Interest Payable: must be Current Liabilities \u2014 not Indirect Expenses (Critical)'));
  content.push(bullet('Salary: must be Indirect Expenses \u2014 not Direct Expenses (Review)'));
  content.push(bullet('Depreciation: must be Indirect Expenses \u2014 not Direct Expenses (Review)'));
  content.push(bullet('Accrued Income: must be Current Assets \u2014 not Indirect Incomes (Review)'));
  content.push(bullet('Security Deposit (paid): must be Loans & Advances (Asset) \u2014 not Fixed Assets (Review)'));
  content.push(bullet('Security Deposit (received): must be Current Liabilities \u2014 not Loans (Review)'));
  content.push(bullet('Advance from Customer: must be Current Liabilities \u2014 not Sundry Creditors (Review)'));
  content.push(bullet('PT Payable: must be Duties & Taxes (Review)'));
  content.push(bullet('Debtor with credit balance: flagged for review (may indicate unposted payment or wrong entry)'));
  content.push(bullet('Creditor with debit balance: flagged for review (may indicate advance payment not cleared)'));
  content.push(bullet('Suspense Account with non-zero balance: Critical \u2014 indicates unposted or unresolved entries'));
  content.push(bullet('Opening balance mismatch (Dr total \u2260 Cr total): Critical'));
  content.push(bullet('Sales Returns exceeding Sales: Critical'));
  content.push(bullet('Dormant ledgers (zero balance, no transactions in FY): Review'));
  content.push(spacer(12));

  // ── Feature 3: Error Explanation ─────────────────────────────────────
  content.push(h2('Error Explanation & Auto-Correction Journal Entry'));
  content.push(whatItDoesBox(
    'Every error flagged by the engine comes with a full explanation \u2014 not just \'wrong group\'. VirtualCA tells you why the error matters, which accounting principle was violated, and gives you the exact journal entry needed to fix it.'
  ));
  content.push(spacer(8));
  content.push(bullet('Plain-English explanation of why the error occurred and its financial impact'));
  content.push(bullet('Accounting rule cited: AS-2, Matching Principle, Double Entry, Indian GAAP, etc.'));
  content.push(bullet('Three-column view: Current (Wrong) Group \u2192 Problem \u2192 Correct Group'));
  content.push(bullet('Auto-generated journal entry: Dr and Cr lines with amounts, ready to post in Tally'));
  content.push(bullet('Note on whether the fix requires a journal voucher or just a ledger re-grouping in Tally'));
  content.push(bullet('Step-by-step Tally navigation path: exact menu path to fix the error (e.g., Gateway of Tally \u2192 Accounts Info \u2192 Ledgers \u2192 Alter)'));
  content.push(spacer(12));

  // ── Feature 4: Fix Workflow ───────────────────────────────────────────
  content.push(h2('Fix Workflow & Team Collaboration'));
  content.push(whatItDoesBox(
    'VirtualCA is not just for analysis \u2014 it is a workflow tool. Errors can be assigned to team members, tracked through resolution, and commented on. Every change is logged with user name and timestamp.'
  ));
  content.push(spacer(8));
  content.push(bullet('Each error has a workflow status: Open \u2192 In Progress \u2192 Resolved \u2192 Ignored'));
  content.push(bullet('Assign any error to a specific team member (accountant, CA, intern)'));
  content.push(bullet('Comment thread on each error: discuss the fix, attach notes, ask questions'));
  content.push(bullet('Mark Resolved button with confirmation'));
  content.push(bullet('Fix Workflow Status Bar: shows live count of Open / In Progress / Resolved / Ignored'));
  content.push(bullet('Last updated by [user] at [time] \u2014 full audit trail'));
  content.push(bullet('Filter errors by status, severity, or assigned person'));
  content.push(spacer(12));

  // ── Feature 5: Ledger Drill-Down ──────────────────────────────────────
  content.push(h2('Ledger Drill-Down \u2014 Full Transaction History'));
  content.push(whatItDoesBox(
    'Click any ledger in the results to see its complete transaction history. Opening balance, every debit and credit, and all related vouchers \u2014 without going back to Tally.'
  ));
  content.push(spacer(8));
  content.push(bullet('Opening Balance, Total Debits, Total Credits, Closing Balance for the ledger'));
  content.push(bullet('Full transaction table: Date \u00b7 Voucher No \u00b7 Narration \u00b7 Dr/Cr Amount'));
  content.push(bullet('Related Vouchers panel: Voucher Number \u00b7 Date \u00b7 Type \u00b7 Party \u00b7 Amount'));
  content.push(bullet('Drill into specific suspicious transactions directly from the error card'));
  content.push(bullet('Useful for: finding which voucher caused a credit balance in a debtor, or locating an uncleared suspense entry'));
  content.push(spacer(12));

  // ── Feature 6: Export to Tally ────────────────────────────────────────
  content.push(h2('Export to Tally \u2014 XML, Excel, CSV'));
  content.push(whatItDoesBox(
    'After analysis, VirtualCA generates export files that can be directly imported into Tally or shared with your accountant. No manual data entry for corrections.'
  ));
  content.push(spacer(8));
  content.push(bullet('Tally XML: generates a Tally-compatible import file with all corrections (journal vouchers, ledger group changes)'));
  content.push(bullet('Excel Correction Sheet: a formatted spreadsheet listing every error with the corrected group and journal entry \u2014 ready to send to your accountant'));
  content.push(bullet('Tally Import CSV: simplified format for bulk ledger updates'));
  content.push(bullet('Step-by-step XML import instructions included in the app (Gateway of Tally \u2192 Import Data \u2192 Vouchers)'));
  content.push(bullet('Summary shown before export: "7 corrections ready to export"'));
  content.push(spacer(12));

  // ── Feature 7: Bank Reconciliation ───────────────────────────────────
  content.push(h2('Bank Reconciliation \u2014 Auto-Match in Minutes'));
  content.push(whatItDoesBox(
    'Upload your bank statement and your Tally bank ledger export. VirtualCA automatically matches entries, flags unmatched transactions, identifies duplicates, and shows you exactly what needs attention.'
  ));
  content.push(spacer(8));
  content.push(bullet('Upload two files: Bank Statement (CSV/Excel from any bank) + Tally Bank Ledger (Excel export)'));
  content.push(bullet('Matching algorithm: exact match on date + amount; probable match within \u00b13 days; flags ambiguous cases'));
  content.push(bullet('Results in 4 categories:'));
  content.push(bullet('Matched: entries confirmed in both bank and Tally'));
  content.push(bullet('Unmatched: in bank but not in Tally (missing Tally entry \u2014 suggested journal entry provided)'));
  content.push(bullet('Tally Only: in Tally but not in bank (possible outstanding cheque or error)'));
  content.push(bullet('Duplicates: same amount + same date appearing twice in Tally'));
  content.push(bullet('Each unmatched entry shows narration, bank reference, amount, why it is missing, and the journal entry to create'));
  content.push(bullet('Summary: Matched 131 (91.6%) | Unmatched 7 | Tally Only 3 | Duplicates 2'));
  content.push(bullet('Results stored per session \u2014 reopen any previous reconciliation'));
  content.push(spacer(12));

  // ── Feature 8: TDS Analysis ──────────────────────────────────────────
  content.push(h2('TDS Analysis \u2014 Section-Wise Tracking & Interest Calculator'));
  content.push(whatItDoesBox(
    'VirtualCA reads your vouchers, identifies TDS deducted and deposited per section, calculates the gap, and tells you exactly how much interest you owe \u2014 before the tax department tells you.'
  ));
  content.push(spacer(8));
  content.push(bullet('Sections tracked: 192 (Salary), 194C (Contractors), 194J (Professional), 194I (Rent), 194H (Commission), 194D, 194A'));
  content.push(bullet('Section-wise table: Deducted vs Deposited vs Pending vs Status for each section'));
  content.push(bullet('Late Payment Interest Calculator: 1% per month for non-deduction, 1.5% per month for non-deposit (Section 201(1A))'));
  content.push(bullet('26AS Reconciliation: import Form 26AS \u2192 compare deductor-wise amounts against books \u2192 flag mismatches'));
  content.push(bullet('Summary cards: Total Deducted \u00b7 Total Deposited \u00b7 Total Pending \u00b7 Total Late Interest'));
  content.push(bullet('Identifies exactly which sections are overdue and by how many months'));
  content.push(spacer(12));

  // ── Feature 9: Professional Tax ──────────────────────────────────────
  content.push(h2('Professional Tax Analysis \u2014 West Bengal Slabs'));
  content.push(whatItDoesBox(
    'Built specifically for businesses in Kolkata and West Bengal. VirtualCA reads your payroll ledgers, applies WB PT slabs per employee, generates journal entries, and gives you deposit instructions for the Grips portal.'
  ));
  content.push(spacer(8));
  content.push(bullet('WB PT Slab table applied automatically:'));
  content.push(bullet('Up to \u20b910,000 gross salary \u2192 Nil'));
  content.push(bullet('\u20b910,001\u2013\u20b915,000 \u2192 \u20b9110/month'));
  content.push(bullet('\u20b915,001\u2013\u20b925,000 \u2192 \u20b9130/month'));
  content.push(bullet('\u20b925,001\u2013\u20b940,000 \u2192 \u20b9150/month'));
  content.push(bullet('Above \u20b940,000 \u2192 \u20b9200/month'));
  content.push(bullet('Employee-wise PT table: Employee Name \u00b7 Gross Salary \u00b7 Slab \u00b7 PT Due'));
  content.push(bullet('Auto-generated journal entries for:'));
  content.push(bullet('Salary deduction entry: Dr Salary A/c | Cr PT Payable (Duties & Taxes)'));
  content.push(bullet('Deposit entry: Dr PT Payable | Cr Bank A/c'));
  content.push(bullet('Step-by-step Grips portal deposit instructions (wbifms.gov.in)'));
  content.push(bullet('Due date alert: PT must be deposited by 21st of every month'));
  content.push(bullet('Checks if PT Payable ledger has been cleared by due date'));
  content.push(spacer(12));

  // ── Feature 10: AI CA Chat ───────────────────────────────────────────
  content.push(h2('AI CA Chat \u2014 Your Accountant Is Always Available'));
  content.push(whatItDoesBox(
    'Ask any accounting question about your actual uploaded data and get a CA-level answer \u2014 with journal entries, Tally navigation paths, and compliance notes. The AI has read your entire file before you ask.'
  ));
  content.push(spacer(8));
  content.push(bullet('Powered by Anthropic Claude \u2014 the most advanced AI model available'));
  content.push(bullet('Context-aware: the AI knows your company name, FY, all ledgers, all errors, TDS status, PT status before you type a word'));
  content.push(bullet('Greets you with a data-connected summary: \'Your file has 7 critical errors. Bank Interest \u20b925,000 is mis-booked...\''));
  content.push(bullet('Ask anything: \'Why is my profit low this month?\', \'Which TDS sections are overdue?\', \'Give me journal entries for all critical errors\''));
  content.push(bullet('Quick-ask chips: pre-loaded context-aware questions for one-click answers'));
  content.push(bullet('Answers include: ledger names and amounts from your actual data, journal entries in Tally Dr/Cr format, Tally navigation paths, section numbers and penalty amounts'));
  content.push(bullet('Chat history stored per session'));
  content.push(spacer(12));

  // ── Feature 11: Compliance Calendar ──────────────────────────────────
  content.push(h2('Compliance Calendar \u2014 Never Miss a Deadline'));
  content.push(whatItDoesBox(
    'A live calendar of all Indian compliance due dates \u2014 pre-loaded and automatically calculated for the current month. Mark items done, see what is overdue, and know exactly what is coming up.'
  ));
  content.push(spacer(8));
  content.push(bullet('Pre-loaded compliance items:'));
  content.push(bullet('7th every month: TDS Deposit (Section 200) \u2014 penalty \u20b9200/day + 1.5%/month if missed'));
  content.push(bullet('11th every month: GSTR-1 (outward supplies)'));
  content.push(bullet('20th every month: GSTR-3B (summary return)'));
  content.push(bullet('21st every month: PT Deposit \u2014 Kolkata/WB via Grips portal'));
  content.push(bullet('Last day of month: Salary payment (deduct PT and TDS)'));
  content.push(bullet('15 Jun / 15 Sep / 15 Dec / 15 Mar: Advance Tax installments'));
  content.push(bullet('31 Jul / 31 Oct / 31 Jan / 31 May: TDS Quarterly Returns'));
  content.push(bullet('31 July: ITR Filing (non-audit cases)'));
  content.push(bullet('31 October: ITR Filing (audit cases)'));
  content.push(bullet('Status badges: OVERDUE (pulsing) \u00b7 X DAYS LEFT \u00b7 DONE'));
  content.push(bullet('Mark Done button \u2014 records who marked it and when'));
  content.push(bullet('Summary: Overdue count \u00b7 Due This Week count \u00b7 Completed This Month'));
  content.push(bullet('Penalty notes shown alongside each item'));
  content.push(spacer(12));

  // ── Feature 12: History & Multi-Upload ───────────────────────────────
  content.push(h2('Upload History & Multi-Period Analysis'));
  content.push(whatItDoesBox(
    'Every file you upload is stored and accessible. Review any previous analysis, compare across financial years, and track how your compliance score improves over time.'
  ));
  content.push(spacer(8));
  content.push(bullet('Full upload history table: File Name \u00b7 Uploaded By \u00b7 Date \u00b7 Period \u00b7 Result tags \u00b7 View Report'));
  content.push(bullet('Search by file name or filter by status'));
  content.push(bullet('Click any row to reopen the full results for that upload'));
  content.push(bullet('Each upload stores: critical count, review count, ok count \u2014 for trend tracking'));
  content.push(bullet('Multi-user: see who uploaded what and when'));
  content.push(spacer(12));

  // ── Feature 13: Admin Panel ───────────────────────────────────────────
  content.push(h2('Admin Panel & Multi-User Team Access'));
  content.push(whatItDoesBox(
    'Add your accountants, CA, and team members to the same company account. Control who can see what. Track all activity.'
  ));
  content.push(spacer(8));
  content.push(bullet('Roles: Admin \u00b7 Accountant \u00b7 Viewer'));
  content.push(bullet('Admin: add/remove users, see all uploads, manage billing'));
  content.push(bullet('Accountant: upload files, run analysis, fix errors, comment on workflow'));
  content.push(bullet('Viewer: read-only access to results and reports'));
  content.push(bullet('Invite by email'));
  content.push(bullet('All uploads are scoped to your company \u2014 no data mixing between clients'));
  content.push(bullet('CA firms: manage multiple client companies from one account'));
  content.push(spacer(12));

  content.push(new Paragraph({ children: [new PageBreak()] }));

  return content;
}

// ══════════════════════════════════════════════════════════════════════════
// WHO SHOULD USE THIS
// ══════════════════════════════════════════════════════════════════════════
function buildWhoPage() {
  const content = [];

  content.push(h1('Who Should Use VirtualCA'));

  const c1 = Math.floor(PAGE_WIDTH * 0.22);
  const c2 = Math.floor(PAGE_WIDTH * 0.30);
  const c3 = PAGE_WIDTH - c1 - c2;

  const headerRow = new TableRow({
    tableHeader: true,
    children: [
      new TableCell({
        width: { size: c1, type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        borders: stdBorder(NAVY),
        children: [new Paragraph({ children: [tr('User', { bold: true, size: 11, color: WHITE })] })],
      }),
      new TableCell({
        width: { size: c2, type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        borders: stdBorder(NAVY),
        children: [new Paragraph({ children: [tr('Their Problem', { bold: true, size: 11, color: WHITE })] })],
      }),
      new TableCell({
        width: { size: c3, type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 120, right: 120 },
        borders: stdBorder(NAVY),
        children: [new Paragraph({ children: [tr('How VirtualCA Helps', { bold: true, size: 11, color: WHITE })] })],
      }),
    ],
  });

  const whoRows = [
    [
      'SMB Owner / Director',
      'Does not know if books are accurate. Depends entirely on accountant.',
      'Upload the file yourself. See the audit report. Ask the AI questions. No CA needed for routine checks.'
    ],
    [
      'In-House Accountant',
      'Makes ledger grouping mistakes. Misses compliance deadlines.',
      'Get instant feedback on every upload. Know the exact fix before the month closes.'
    ],
    [
      'CA Firm',
      'Reviews multiple client files manually. Repeating the same audit steps every month.',
      'Run automated audits for all clients. Assign fixes to juniors. Track resolution. Export to Tally directly.'
    ],
    [
      'Startup Finance Team',
      'No dedicated CA. Misses TDS deposits. Wrong books during fundraising.',
      'Live compliance calendar. TDS tracker. Clean financials whenever an investor asks.'
    ],
  ];

  const dataRows = whoRows.map((row, idx) => {
    const bg = idx % 2 === 0 ? WHITE : GREY_BG;
    return new TableRow({
      children: [
        new TableCell({
          width: { size: c1, type: WidthType.DXA },
          shading: { fill: bg, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 120, right: 120 },
          borders: stdBorder('CCCCCC'),
          children: [new Paragraph({ children: [tr(row[0], { bold: true, size: 10, color: NAVY })] })],
        }),
        new TableCell({
          width: { size: c2, type: WidthType.DXA },
          shading: { fill: bg, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 120, right: 120 },
          borders: stdBorder('CCCCCC'),
          children: [new Paragraph({ children: [tr(row[1], { size: 10, color: BODY_TEXT })] })],
        }),
        new TableCell({
          width: { size: c3, type: WidthType.DXA },
          shading: { fill: bg, type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 120, right: 120 },
          borders: stdBorder('CCCCCC'),
          children: [new Paragraph({ children: [tr(row[2], { size: 10, color: BODY_TEXT })] })],
        }),
      ],
    });
  });

  content.push(new Table({
    width: { size: PAGE_WIDTH, type: WidthType.DXA },
    columnWidths: [c1, c2, c3],
    layout: TableLayoutType.FIXED,
    rows: [headerRow, ...dataRows],
  }));

  content.push(new Paragraph({ children: [new PageBreak()] }));

  return content;
}

// ══════════════════════════════════════════════════════════════════════════
// CLOSING PAGE
// ══════════════════════════════════════════════════════════════════════════
function buildClosingPage() {
  const content = [];

  content.push(spacer(40));

  content.push(centeredPara(
    tr('VirtualCA', { bold: true, size: 32, color: NAVY }),
    120
  ));

  content.push(centeredPara(
    tr('AI-powered. Built for India. Designed for Tally.', { size: 14, color: BODY_TEXT }),
    200
  ));

  content.push(spacer(20));

  content.push(centeredPara(
    tr(
      'This document provides an overview of the VirtualCA platform currently in development. Features described reflect the planned product scope.',
      { italic: true, size: 10, color: GREY_TEXT }
    ),
    0
  ));

  return content;
}

// ══════════════════════════════════════════════════════════════════════════
// ASSEMBLE DOCUMENT
// ══════════════════════════════════════════════════════════════════════════
const doc = new Document({
  numbering: {
    config: [
      {
        reference: 'bullets',
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: '\u2022',
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: {
                indent: { left: 720, hanging: 360 },
              },
            },
          },
        ],
      },
      {
        reference: 'numbers',
        levels: [
          {
            level: 0,
            format: LevelFormat.DECIMAL,
            text: '%1.',
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: {
                indent: { left: 720, hanging: 360 },
              },
            },
          },
        ],
      },
    ],
  },
  styles: {
    default: {
      document: {
        run: { font: 'Arial', size: 22 },
      },
    },
    paragraphStyles: [
      {
        id: 'Heading1',
        name: 'Heading 1',
        basedOn: 'Normal',
        next: 'Normal',
        quickFormat: true,
        run: { size: 44, bold: true, font: 'Arial', color: NAVY },
        paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0 },
      },
      {
        id: 'Heading2',
        name: 'Heading 2',
        basedOn: 'Normal',
        next: 'Normal',
        quickFormat: true,
        run: { size: 32, bold: true, font: 'Arial', color: BLUE },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 },
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: {
            width: 11906,
            height: 16838,
          },
          margin: {
            top: 1440,
            bottom: 1440,
            left: 1440,
            right: 1440,
          },
        },
      },
      children: [
        ...buildCoverPage(),
        ...buildProblemPage(),
        ...buildSolutionPage(),
        ...buildSavingsPage(),
        ...buildFeaturesPages(),
        ...buildWhoPage(),
        ...buildClosingPage(),
      ],
    },
  ],
});

const OUTPUT_PATH = 'C:\\Users\\sagar\\Downloads\\tally_saas\\VirtualCA_Explainer.docx';

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(OUTPUT_PATH, buffer);
  console.log('Document written to:', OUTPUT_PATH);
}).catch(err => {
  console.error('Error generating document:', err);
  process.exit(1);
});
