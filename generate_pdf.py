"""
VirtualCA Pitch PDF Generator
Generates a beautiful, modern A4 pitch PDF using ReportLab canvas.
Single page, all sections fitted to A4 (595.27 x 841.89 pts).
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

# ─── Colour Palette ───────────────────────────────────────────────────────────
NAVY        = colors.HexColor('#0F172A')
INDIGO      = colors.HexColor('#6366F1')
INDIGO_DARK = colors.HexColor('#4F46E5')
INDIGO_DEEP = colors.HexColor('#4338CA')
EMERALD     = colors.HexColor('#10B981')
RED         = colors.HexColor('#EF4444')
AMBER       = colors.HexColor('#F59E0B')
PURPLE      = colors.HexColor('#8B5CF6')
PINK        = colors.HexColor('#EC4899')
WHITE       = colors.white
LIGHT_GREY  = colors.HexColor('#F8FAFC')
MID_GREY    = colors.HexColor('#94A3B8')
DARK_GREY   = colors.HexColor('#334155')
TEXT_DARK   = colors.HexColor('#1E293B')
TEXT_BODY   = colors.HexColor('#475569')
BORDER      = colors.HexColor('#E2E8F0')

PAGE_W, PAGE_H = A4   # 595.27 x 841.89 pts

# ─── Section heights (sum = 841) ──────────────────────────────────────────────
H_HERO     = 130
H_PROBLEM  = 150
H_SOLUTION = 155
H_FEATURES = 230
H_PRICING  = 132
H_FOOTER   = 44


# ─── Helper: draw rounded rect with fill only ─────────────────────────────────
def filled_round_rect(c, x, y, w, h, r, fill_color):
    c.setFillColor(fill_color)
    c.roundRect(x, y, w, h, r, fill=1, stroke=0)


def stroked_round_rect(c, x, y, w, h, r, stroke_color, line_width=0.75):
    c.setStrokeColor(stroke_color)
    c.setLineWidth(line_width)
    c.roundRect(x, y, w, h, r, fill=0, stroke=1)


def pill(c, x, y, w, h, bg, text_color, text, font_size=8):
    filled_round_rect(c, x, y, w, h, h / 2, bg)
    c.setFillColor(text_color)
    c.setFont('Helvetica-Bold', font_size)
    c.drawCentredString(x + w / 2, y + (h - font_size) / 2 + 1, text)


# ─── Section Drawers ──────────────────────────────────────────────────────────

def draw_hero(c, y_top):
    """Dark navy hero section."""
    h = H_HERO
    y = y_top - h

    # Background
    c.setFillColor(NAVY)
    c.rect(0, y, PAGE_W, h, fill=1, stroke=0)

    # Indigo accent bar at very top
    c.setFillColor(INDIGO)
    c.rect(0, y + h - 4, PAGE_W, 4, fill=1, stroke=0)

    # Decorative background circles
    c.setFillColor(colors.HexColor('#1E293B'))
    c.circle(PAGE_W - 25, y + h - 5, 80, fill=1, stroke=0)
    c.setFillColor(colors.HexColor('#243047'))
    c.circle(PAGE_W + 10, y + 10, 55, fill=1, stroke=0)

    # Brand name
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 36)
    logo_text = 'VirtualCA'
    c.drawString(36, y + h - 54, logo_text)

    # Indigo accent dot after logo
    logo_w = c.stringWidth(logo_text, 'Helvetica-Bold', 36)
    c.setFillColor(INDIGO)
    c.circle(36 + logo_w + 7, y + h - 40, 5, fill=1, stroke=0)

    # AI badge (top right)
    filled_round_rect(c, PAGE_W - 100, y + h - 50, 68, 20, 6, INDIGO)
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 8)
    c.drawCentredString(PAGE_W - 66, y + h - 43, 'AI-Powered')

    # Tagline
    c.setFillColor(colors.HexColor('#CBD5E1'))
    c.setFont('Helvetica', 13)
    c.drawString(36, y + h - 76,
                 'Upload your Tally file. Get a full audit in 30 seconds.')

    # Sub-label
    c.setFillColor(MID_GREY)
    c.setFont('Helvetica', 9)
    c.drawString(36, y + h - 96,
                 'Powered by AI  \u00b7  Built for Indian SMBs & CA Firms')

    # Thin bottom rule
    c.setStrokeColor(colors.HexColor('#1E293B'))
    c.setLineWidth(1)
    c.line(0, y, PAGE_W, y)

    return y  # bottom of section


def draw_problem(c, y_top):
    """White section with red-accented problem bullets."""
    h = H_PROBLEM
    y = y_top - h

    # BG
    c.setFillColor(WHITE)
    c.rect(0, y, PAGE_W, h, fill=1, stroke=0)

    # Section pill
    pill(c, 36, y + h - 32, 108, 18,
         colors.HexColor('#FEF2F2'), RED, 'THE PROBLEM', 8)

    # Heading
    c.setFillColor(TEXT_DARK)
    c.setFont('Helvetica-Bold', 18)
    c.drawString(36, y + h - 56, 'What Is Going Wrong?')

    bullets = [
        "Your accountant makes ledger grouping errors \u2014 you don't know until tax season.",
        "Compliance deadlines (TDS, GST, PT) are missed \u2014 resulting in penalties & interest.",
        "Bank reconciliation is done manually \u2014 taking days instead of minutes.",
    ]

    bullet_h = 32
    start_y = y + h - 80

    for i, text in enumerate(bullets):
        by = start_y - i * (bullet_h + 4)

        # Soft red card bg
        filled_round_rect(c, 36, by, PAGE_W - 72, bullet_h, 5,
                          colors.HexColor('#FFF5F5'))

        # Red left accent bar
        c.setFillColor(RED)
        c.roundRect(36, by, 4, bullet_h, 2, fill=1, stroke=0)

        # Red dot
        c.setFillColor(RED)
        c.circle(56, by + bullet_h / 2, 3.5, fill=1, stroke=0)

        # Text
        c.setFillColor(TEXT_DARK)
        c.setFont('Helvetica', 9)
        c.drawString(67, by + bullet_h / 2 - 4, text)

    # Bottom rule
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(36, y + 1, PAGE_W - 36, y + 1)

    return y


def draw_solution(c, y_top):
    """Light grey section with 3-step cards."""
    h = H_SOLUTION
    y = y_top - h

    # BG
    c.setFillColor(LIGHT_GREY)
    c.rect(0, y, PAGE_W, h, fill=1, stroke=0)

    # Section pill
    pill(c, 36, y + h - 32, 128, 18,
         colors.HexColor('#EEF2FF'), INDIGO, 'THE SOLUTION', 8)

    # Heading
    c.setFillColor(TEXT_DARK)
    c.setFont('Helvetica-Bold', 18)
    c.drawString(36, y + h - 56, 'What VirtualCA Does')

    steps = [
        ('01', 'Upload',  'Upload Tally Trial Balance, XML,\nBank Statement or GST file'),
        ('02', 'Analyze', 'AI engine checks 20+ accounting\nrules instantly'),
        ('03', 'Fix',     'Get exact errors, journal entries\nand Tally fix instructions'),
    ]
    step_colors = [INDIGO, EMERALD, AMBER]

    n = 3
    card_w = (PAGE_W - 72 - (n - 1) * 14) / n
    card_h = 82
    card_y = y + 10
    start_x = 36

    for i, (num, title, desc) in enumerate(steps):
        cx = start_x + i * (card_w + 14)

        # Shadow
        filled_round_rect(c, cx + 2, card_y - 2, card_w, card_h, 8,
                          colors.HexColor('#E2E8F0'))

        # Card
        filled_round_rect(c, cx, card_y, card_w, card_h, 8, WHITE)

        # Top colour stripe
        c.setFillColor(step_colors[i])
        c.roundRect(cx, card_y + card_h - 6, card_w, 6, 3, fill=1, stroke=0)
        c.rect(cx, card_y + card_h - 6, card_w, 3, fill=1, stroke=0)

        # Step number circle
        circle_cx = cx + 20
        circle_cy = card_y + card_h - 24
        c.setFillColor(step_colors[i])
        c.circle(circle_cx, circle_cy, 12, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(circle_cx, circle_cy - 3, num)

        # Title
        c.setFillColor(TEXT_DARK)
        c.setFont('Helvetica-Bold', 11)
        c.drawString(cx + 38, card_y + card_h - 22, title)

        # Description
        c.setFillColor(TEXT_BODY)
        c.setFont('Helvetica', 8)
        for j, line in enumerate(desc.split('\n')):
            c.drawString(cx + 10, card_y + card_h - 42 - j * 12, line)

        # Arrow
        if i < 2:
            arrow_x = cx + card_w + 7
            arrow_y = card_y + card_h / 2 - 5
            c.setFillColor(INDIGO)
            c.setFont('Helvetica-Bold', 16)
            c.drawCentredString(arrow_x, arrow_y, '\u2192')

    # Bottom rule
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(36, y + 1, PAGE_W - 36, y + 1)

    return y


def draw_features(c, y_top):
    """White section with 6 feature cards in 2×3 grid."""
    h = H_FEATURES
    y = y_top - h

    # BG
    c.setFillColor(WHITE)
    c.rect(0, y, PAGE_W, h, fill=1, stroke=0)

    # Section pill
    pill(c, 36, y + h - 32, 118, 18,
         colors.HexColor('#ECFDF5'), EMERALD, 'WHAT YOU GET', 8)

    # Heading
    c.setFillColor(TEXT_DARK)
    c.setFont('Helvetica-Bold', 18)
    c.drawString(36, y + h - 56, 'Powerful Features, Out of the Box')

    features = [
        ('Ledger Audit',        'Detects wrong groupings across 20 rules.\nFlags Critical vs Review errors.',         INDIGO),
        ('AI CA Chat',          'Ask questions about your own data.\nGet CA-level answers with journal entries.',     EMERALD),
        ('TDS Analysis',        'Section-wise TDS tracking (194C/194J/192).\nLate interest calculator included.',    AMBER),
        ('PT Analysis',         'West Bengal slabs (\u20b9110\u2013\u20b9200/month).\nEmployee-wise PT with Grips portal steps.', PURPLE),
        ('Bank Reconciliation', 'Auto-match bank statement vs Tally.\nFlags unmatched, duplicates, missing entries.', PINK),
        ('Compliance Calendar', 'TDS 7th, GSTR-1 11th, GSTR-3B 20th, PT 21st\u2014never miss a deadline.',          RED),
    ]
    initials = ['LA', 'AI', 'TD', 'PT', 'BR', 'CC']

    cols     = 2
    rows     = 3
    gap_x    = 14
    gap_y    = 10
    card_w   = (PAGE_W - 72 - gap_x) / cols
    card_h   = (h - 70 - (rows - 1) * gap_y) / rows
    start_x  = 36
    start_y  = y + h - 72

    for i, ((title, desc, accent), init) in enumerate(zip(features, initials)):
        col = i % cols
        row = i // cols
        cx = start_x + col * (card_w + gap_x)
        cy = start_y - row * (card_h + gap_y) - card_h

        # Border card
        c.setFillColor(WHITE)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.75)
        c.roundRect(cx, cy, card_w, card_h, 6, fill=1, stroke=1)

        # Left accent bar
        c.setFillColor(accent)
        c.roundRect(cx, cy, 4, card_h, 3, fill=1, stroke=0)
        c.rect(cx + 2, cy, 2, card_h, fill=1, stroke=0)

        # Accent circle icon
        icon_cx = cx + 20
        icon_cy = cy + card_h - 20
        c.setFillColor(accent)
        c.circle(icon_cx, icon_cy, 11, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 7)
        c.drawCentredString(icon_cx, icon_cy - 2.5, init)

        # Feature title
        c.setFillColor(TEXT_DARK)
        c.setFont('Helvetica-Bold', 10)
        c.drawString(cx + 38, cy + card_h - 16, title)

        # Description
        c.setFillColor(TEXT_BODY)
        c.setFont('Helvetica', 7.5)
        for j, line in enumerate(desc.split('\n')):
            c.drawString(cx + 38, cy + card_h - 30 - j * 11, line)

    # Bottom rule
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(0, y, PAGE_W, y)

    return y


def draw_pricing(c, y_top):
    """Indigo section with 4 pricing cards."""
    h = H_PRICING
    y = y_top - h

    # BG
    c.setFillColor(INDIGO)
    c.rect(0, y, PAGE_W, h, fill=1, stroke=0)

    # Top darker stripe
    c.setFillColor(INDIGO_DARK)
    c.rect(0, y + h - 4, PAGE_W, 4, fill=1, stroke=0)

    # Section pill
    pill(c, 36, y + h - 30, 160, 16,
         colors.HexColor('#EEF2FF'), INDIGO_DARK, 'TRANSPARENT PRICING', 7.5)

    # Heading
    c.setFillColor(WHITE)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(36, y + h - 52, 'Simple, Transparent Pricing')

    plans = [
        ('Free',    '\u20b90',        '2 uploads/month',               False),
        ('Starter', '\u20b9499/mo',   '10 uploads + AI chat',          False),
        ('Pro',     '\u20b91,499/mo', 'Unlimited + compliance alerts', True),
        ('CA Firm', '\u20b93,999/mo', 'Multi-client + team access',    False),
    ]

    n       = len(plans)
    card_w  = (PAGE_W - 72 - (n - 1) * 10) / n
    card_h  = 68
    card_y  = y + 8
    start_x = 36

    for i, (name, price, desc, highlight) in enumerate(plans):
        cx = start_x + i * (card_w + 10)

        if highlight:
            # White card
            filled_round_rect(c, cx - 3, card_y - 4, card_w + 6, card_h + 8, 8, WHITE)
            # POPULAR badge
            badge_w = 72
            filled_round_rect(c, cx + (card_w - badge_w) / 2,
                              card_y + card_h + 4, badge_w, 14, 5, EMERALD)
            c.setFillColor(WHITE)
            c.setFont('Helvetica-Bold', 7)
            c.drawCentredString(cx + card_w / 2, card_y + card_h + 7, 'MOST POPULAR')
            name_col  = INDIGO
            price_col = INDIGO_DARK
            desc_col  = TEXT_BODY
            btn_bg    = INDIGO
        else:
            # Translucent dark card
            filled_round_rect(c, cx, card_y, card_w, card_h, 8, INDIGO_DEEP)
            c.setStrokeColor(colors.HexColor('#818CF8'))
            c.setLineWidth(0.5)
            c.roundRect(cx, card_y, card_w, card_h, 8, fill=0, stroke=1)
            name_col  = colors.HexColor('#C7D2FE')
            price_col = WHITE
            desc_col  = colors.HexColor('#A5B4FC')
            btn_bg    = INDIGO

        # Plan name
        c.setFillColor(name_col)
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(cx + card_w / 2, card_y + card_h - 16, name)

        # Separator
        sep_color = colors.HexColor('#818CF8') if not highlight else BORDER
        c.setStrokeColor(sep_color)
        c.setLineWidth(0.4)
        c.line(cx + 8, card_y + card_h - 22, cx + card_w - 8, card_y + card_h - 22)

        # Price
        c.setFillColor(price_col)
        c.setFont('Helvetica-Bold', 14)
        c.drawCentredString(cx + card_w / 2, card_y + card_h - 38, price)

        # Description
        c.setFillColor(desc_col)
        c.setFont('Helvetica', 7)
        c.drawCentredString(cx + card_w / 2, card_y + card_h - 52, desc)

        # CTA button
        btn_h = 16
        filled_round_rect(c, cx + 8, card_y + 6, card_w - 16, btn_h, 5, btn_bg)
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 7)
        c.drawCentredString(cx + card_w / 2, card_y + 11, 'Get Started')

    return y


def draw_footer(c, y_top):
    """Dark navy footer."""
    h = H_FOOTER
    y = y_top - h

    c.setFillColor(NAVY)
    c.rect(0, y, PAGE_W, h, fill=1, stroke=0)

    # Top indigo accent
    c.setFillColor(INDIGO)
    c.rect(0, y + h - 2, PAGE_W, 2, fill=1, stroke=0)

    # Left text
    c.setFillColor(MID_GREY)
    c.setFont('Helvetica', 8.5)
    c.drawString(36, y + h - 18,
                 'VirtualCA  \u00b7  Built for India  \u00b7  Powered by Claude AI')

    # Right text
    c.setFillColor(colors.HexColor('#64748B'))
    c.setFont('Helvetica', 8.5)
    c.drawRightString(PAGE_W - 36, y + h - 18,
                      'Sagar Pathak  \u00b7  sagar@virtualca.in')

    # Bottom copyright
    c.setFillColor(colors.HexColor('#334155'))
    c.setFont('Helvetica', 7)
    c.drawCentredString(PAGE_W / 2, y + 10,
                        '\u00a9 2025 VirtualCA. All rights reserved.')

    return y


# ─── Main Build ───────────────────────────────────────────────────────────────

def build_pdf(output_path: str):
    c = Canvas(output_path, pagesize=A4)

    cursor = PAGE_H  # start at top of page

    cursor = draw_hero(c,     cursor)
    cursor = draw_problem(c,  cursor)
    cursor = draw_solution(c, cursor)
    cursor = draw_features(c, cursor)
    cursor = draw_pricing(c,  cursor)
    cursor = draw_footer(c,   cursor)

    c.save()
    print(f'PDF saved: {output_path}')
    print(f'Remaining space: {cursor:.2f} pts (should be ~0)')


if __name__ == '__main__':
    out = r'C:\Users\sagar\Downloads\tally_saas\VirtualCA_Pitch.pdf'
    build_pdf(out)
