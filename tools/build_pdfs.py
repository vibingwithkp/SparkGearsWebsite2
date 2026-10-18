"""Builds the free downloads on for-teams.html into downloads/.

Needs reportlab plus static instances of the site fonts (Big Shoulders Display
800/900 and Instrument Sans 400/500/600/700) in a fonts folder:

    python3 tools/build_pdfs.py path/to/fonts

Font files expected: BS-800.ttf, BS-900.ttf, IS-400.ttf, IS-500.ttf, IS-600.ttf, IS-700.ttf
"""

import os
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, CondPageBreak, Flowable, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Preformatted, Spacer, Table, TableStyle,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "downloads")
LOGO = os.path.join(ROOT, "assets", "brand", "spark-gears-logo.png")

INK = colors.HexColor("#17150f")
MUTED = colors.HexColor("#5f594b")
PAPER = colors.HexColor("#f4f0e6")
PAPER_2 = colors.HexColor("#ebe5d5")
YELLOW = colors.HexColor("#ffc233")
YELLOW_SOFT = colors.HexColor("#fff1c7")
LINE = colors.HexColor("#d8d2c2")
GREEN = colors.HexColor("#1f9d55")

EMAIL = "sparkgearsinitiative@gmail.com"
PHONE = "571-429-9220"
SITE = "sparkgearsinitiative.org"

PAGE_W, PAGE_H = letter
MARGIN = 0.7 * inch
BODY_W = PAGE_W - 2 * MARGIN


def register_fonts(font_dir):
    for name, file in [
        ("Display", "BS-900.ttf"), ("Display-800", "BS-800.ttf"),
        ("Body", "IS-400.ttf"), ("Body-Medium", "IS-500.ttf"),
        ("Body-Semi", "IS-600.ttf"), ("Body-Bold", "IS-700.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, os.path.join(font_dir, file)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")


# ---------- styles ----------

def styles():
    s = {}
    s["body"] = ParagraphStyle("body", fontName="Body", fontSize=9.6, leading=14, textColor=INK, spaceAfter=7)
    s["lede"] = ParagraphStyle("lede", parent=s["body"], fontSize=11.2, leading=16.5, spaceAfter=10)
    s["small"] = ParagraphStyle("small", parent=s["body"], fontSize=8.4, leading=11.6, textColor=MUTED, spaceAfter=0)
    s["cell"] = ParagraphStyle("cell", parent=s["body"], fontSize=8.8, leading=12.2, spaceAfter=0)
    s["cellb"] = ParagraphStyle("cellb", parent=s["cell"], fontName="Body-Semi")
    s["th"] = ParagraphStyle("th", fontName="Display-800", fontSize=9.5, leading=11, textColor=INK)
    s["bullet"] = ParagraphStyle("bullet", parent=s["body"], leftIndent=13, bulletIndent=1, spaceAfter=3.5)
    s["kicker"] = ParagraphStyle("kicker", fontName="Display-800", fontSize=10, leading=12, textColor=MUTED)
    s["title"] = ParagraphStyle("title", fontName="Display", fontSize=40, leading=36, textColor=INK, spaceAfter=0)
    s["h2"] = ParagraphStyle("h2", fontName="Display", fontSize=21, leading=21, textColor=INK, spaceBefore=6, spaceAfter=8)
    s["h3"] = ParagraphStyle("h3", fontName="Display-800", fontSize=13.5, leading=15, textColor=INK, spaceBefore=6, spaceAfter=5, keepWithNext=1)
    s["intro"] = ParagraphStyle("intro", parent=s["body"], keepWithNext=1)
    s["code"] = ParagraphStyle("code", fontName="Courier", fontSize=7.9, leading=10.2, textColor=INK)
    s["glance_k"] = ParagraphStyle("glance_k", fontName="Display-800", fontSize=8.6, leading=10, textColor=MUTED)
    s["glance_v"] = ParagraphStyle("glance_v", fontName="Body-Semi", fontSize=10, leading=13, textColor=INK)
    s["note_t"] = ParagraphStyle("note_t", fontName="Display-800", fontSize=10.5, leading=12, textColor=INK, spaceAfter=3)
    return s


S = None


def P(text, style="body"):
    return Paragraph(text, S[style])


def h2(text):
    return Heading(text.upper())


def h3(text):
    return P(text.upper(), "h3")


def bullets(items, style="bullet"):
    return [Paragraph(t, S[style], bulletText="•") for t in items]


def numbered(items):
    return [Paragraph(t, S["bullet"], bulletText=f"{i}.") for i, t in enumerate(items, 1)]


class Heading(Flowable):
    """Section heading with the small yellow square the website uses on labels."""

    def __init__(self, text):
        super().__init__()
        self.text = text
        self.para = Paragraph(text, S["h2"])
        self.keepWithNext = True

    def wrap(self, aw, ah):
        w, h = self.para.wrap(aw - 18, ah)
        self.h = h
        return aw, h + 14

    def drawOn(self, canv, x, y, _sW=0):
        canv.saveState()
        canv.setFillColor(YELLOW)
        canv.setStrokeColor(INK)
        canv.setLineWidth(1.2)
        canv.roundRect(x, y + self.h - 14, 10, 10, 2, stroke=1, fill=1)
        canv.restoreState()
        self.para.drawOn(canv, x + 18, y + 4)

    def getSpaceBefore(self):
        return 10


class Box(Flowable):
    """Empty tick box for printed checklists."""

    def wrap(self, aw, ah):
        return 9, 9

    def draw(self):
        self.canv.setStrokeColor(INK)
        self.canv.setLineWidth(0.9)
        self.canv.roundRect(0, -1, 8.5, 8.5, 1.2, stroke=1, fill=0)


def checklist(items, width=None, style="bullet"):
    width = width or BODY_W
    t = Table([[Box(), Paragraph(i, ParagraphStyle("chk", parent=S[style], leftIndent=0, spaceAfter=0))] for i in items],
              colWidths=[16, width - 16])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (0, -1), 4.2),
                           ("TOPPADDING", (1, 0), (1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def two_col_checklist(pairs):
    half = BODY_W / 2
    t = Table([[checklist([a for a, _ in pairs], half - 10, "cell"), checklist([b for _, b in pairs], half - 10, "cell")]],
              colWidths=[half, half])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 4)]))
    return t


def table(rows, widths, header=True, zebra=False, valign="TOP", pad=5):
    data = []
    for r_i, row in enumerate(rows):
        out = []
        for c in row:
            if isinstance(c, str):
                style = "th" if header and r_i == 0 else "cell"
                c = Paragraph(c.upper() if style == "th" else c, S[style])
            out.append(c)
        data.append(out)
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), valign),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad + 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("LINEBELOW", (0, 0), (-1, -1), 0.6, LINE),
        ("BOX", (0, 0), (-1, -1), 1.2, INK),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), YELLOW), ("LINEBELOW", (0, 0), (-1, 0), 1.2, INK)]
    if zebra:
        for i in range(1 if header else 0, len(data)):
            if i % 2 == 0:
                cmds.append(("BACKGROUND", (0, i), (-1, i), PAPER))
    t.setStyle(TableStyle(cmds))
    return KeepTogether([t]) if len(rows) <= 12 else t


def glance(pairs, cols=4):
    cells = [[P(k.upper(), "glance_k"), Spacer(1, 2), P(v, "glance_v")] for k, v in pairs]
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    for r in rows:
        while len(r) < cols:
            r.append("")
    t = Table(rows, colWidths=[BODY_W / cols] * cols)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 1.2, INK),
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, LINE),
    ]
    t.setStyle(TableStyle(cmds))
    return t


def code(src, caption=None):
    pre = Preformatted(src.strip("\n"), S["code"])
    rows = [[pre]]
    if caption:
        rows.insert(0, [P(caption.upper(), "glance_k")])
    t = Table(rows, colWidths=[BODY_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("LINEBEFORE", (0, 0), (0, -1), 3, YELLOW),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([t, Spacer(1, 9)])


def note(title, body_items):
    content = [P(title.upper(), "note_t")]
    for b in body_items:
        content.append(P(b, "cell") if isinstance(b, str) else b)
        content.append(Spacer(1, 3))
    t = Table([[content]], colWidths=[BODY_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), YELLOW_SOFT),
        ("BOX", (0, 0), (-1, -1), 1.2, INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 11),
        ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return KeepTogether([t, Spacer(1, 10)])


def three_col_lists(cols):
    """cols: list of (title, [items]) side by side."""
    w = (BODY_W - 2 * 10) / len(cols)
    cells = []
    for title, items in cols:
        block = [P(title.upper(), "note_t"), Spacer(1, 2)]
        for it in items:
            block.append(Paragraph(it, ParagraphStyle("li", parent=S["cell"], leftIndent=10, bulletIndent=0, spaceAfter=3), bulletText="•"))
        cells.append(block)
    t = Table([cells], colWidths=[w] * len(cols), spaceBefore=0)
    cmds = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9), ("BOX", (0, 0), (-1, -1), 1.2, INK),
            ("LINEBEFORE", (1, 0), (-1, 0), 1.2, INK)]
    # first column paper, last column yellow, like the site's two-panel boxes
    cmds += [("BACKGROUND", (0, 0), (0, 0), colors.white), ("BACKGROUND", (-1, 0), (-1, 0), YELLOW)]
    if len(cols) == 3:
        cmds.append(("BACKGROUND", (1, 0), (1, 0), PAPER))
    t.setStyle(TableStyle(cmds))
    return t


def write_lines(n):
    """Blank ruled lines for filling in by hand."""
    t = Table([[""]] * n, colWidths=[BODY_W], rowHeights=[22] * n)
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.6, MUTED)]))
    return t


# ---------- page furniture ----------

class Doc(BaseDocTemplate):
    def __init__(self, path, title, kicker, subtitle, short):
        super().__init__(path, pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=MARGIN, bottomMargin=MARGIN + 6,
                         title=title, author="Spark Gears Initiative", subject=subtitle,
                         creator="Spark Gears Initiative")
        self.doc_title, self.kicker, self.subtitle, self.short = title, kicker, subtitle, short
        self.title_p = Paragraph(title.upper(), S["title"])
        self.title_h = self.title_p.wrap(BODY_W, 300)[1]
        self.sub_p = Paragraph(subtitle, ParagraphStyle("sub", parent=S["lede"], textColor=MUTED, spaceAfter=0))
        self.sub_h = self.sub_p.wrap(BODY_W * 0.86, 200)[1]
        self.head_h = 58 + self.title_h + 8 + self.sub_h + 16
        first = Frame(MARGIN, MARGIN + 6, BODY_W, PAGE_H - 2 * MARGIN - 6 - self.head_h - 14, id="first",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        later = Frame(MARGIN, MARGIN + 6, BODY_W, PAGE_H - 2 * MARGIN - 6 - 0.32 * inch, id="later",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="First", frames=[first], onPage=self.first_page, autoNextPageTemplate="Later"),
            PageTemplate(id="Later", frames=[later], onPage=self.later_page),
        ])

    def footer(self, c):
        c.setStrokeColor(INK)
        c.setLineWidth(0.8)
        c.line(MARGIN, MARGIN - 4, PAGE_W - MARGIN, MARGIN - 4)
        c.setFont("Body", 7.6)
        c.setFillColor(MUTED)
        c.drawString(MARGIN, MARGIN - 16, f"Spark Gears Initiative  |  {SITE}  |  {EMAIL}")
        c.drawRightString(PAGE_W - MARGIN, MARGIN - 16, f"{self.short}  |  Page {c.getPageNumber()}")

    def first_page(self, c, doc):
        c.saveState()
        c.setFillColor(YELLOW)
        c.rect(0, PAGE_H - 10, PAGE_W, 10, stroke=0, fill=1)
        top = PAGE_H - MARGIN + 8
        c.drawImage(LOGO, MARGIN, top - 30, 30, 30, mask="auto")
        c.setFillColor(INK)
        c.setFont("Display", 13)
        c.drawString(MARGIN + 38, top - 13, "SPARK GEARS")
        c.setFont("Display-800", 8.2)
        c.drawString(MARGIN + 38, top - 24, "INITIATIVE")
        c.setFont("Display-800", 9.5)
        c.setFillColor(MUTED)
        c.drawRightString(PAGE_W - MARGIN, top - 13, self.kicker.upper())
        c.setFont("Body", 8)
        c.drawRightString(PAGE_W - MARGIN, top - 24, "Free for FTC teams, schools, and libraries")
        # title
        h, sh = self.title_h, self.sub_h
        self.title_p.drawOn(c, MARGIN, top - 50 - h)
        self.sub_p.drawOn(c, MARGIN, top - 58 - h - sh)
        c.setStrokeColor(INK)
        c.setLineWidth(2)
        y = top - self.head_h
        c.line(MARGIN, y, PAGE_W - MARGIN, y)
        self.footer(c)
        c.restoreState()

    def later_page(self, c, doc):
        c.saveState()
        c.setFillColor(YELLOW)
        c.rect(0, PAGE_H - 6, PAGE_W, 6, stroke=0, fill=1)
        top = PAGE_H - MARGIN + 6
        c.setFont("Display-800", 9.5)
        c.setFillColor(INK)
        c.drawString(MARGIN, top - 6, self.doc_title.upper())
        c.setFillColor(MUTED)
        c.drawRightString(PAGE_W - MARGIN, top - 6, "SPARK GEARS INITIATIVE")
        c.setStrokeColor(INK)
        c.setLineWidth(0.8)
        c.line(MARGIN, top - 12, PAGE_W - MARGIN, top - 12)
        self.footer(c)
        c.restoreState()


def build(filename, title, kicker, subtitle, short, story):
    # headings never sit alone at the bottom of a page: bind each to the block after it
    def leads(f):
        return isinstance(f, Heading) or (isinstance(f, Paragraph) and f.style.name in ("h3", "intro"))

    fixed, i = [], 0
    while i < len(story):
        if leads(story[i]):
            group = []
            while i < len(story) and leads(story[i]):
                group.append(story[i])
                i += 1
            if i < len(story):
                nxt = story[i]
                group += nxt._content if isinstance(nxt, KeepTogether) else [nxt]
                i += 1
            fixed.append(KeepTogether(group))
        else:
            fixed.append(story[i])
            i += 1
    story = fixed
    path = os.path.join(OUT, filename)
    Doc(path, title, kicker, subtitle, short).build(story)
    print("wrote", os.path.relpath(path, ROOT))


def contact_block():
    title = ParagraphStyle("inv_t", parent=S["note_t"], textColor=YELLOW)
    body = ParagraphStyle("inv_b", parent=S["cell"], textColor=PAPER)
    items = [Paragraph("QUESTIONS? TALK TO A HUMAN.", title),
             Paragraph(f"Email <b>{EMAIL}</b> or call <b>{PHONE}</b>. Request a mentor and a supply kit at "
                       f"<b>{SITE}/for-teams.html</b>. We usually reply within two school days.", body)]
    t = Table([[items]], colWidths=[BODY_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), INK),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return KeepTogether([Spacer(1, 6), t])


# =====================================================================
# 1. Arduino workshop series
# =====================================================================

def arduino():
    st = []
    st += [
        glance([
            ("Grades", "5 to 8"),
            ("Sessions", "3, about 55 to 70 min each"),
            ("Group size", "Any size, students work in pairs"),
            ("Experience", "None needed, for students or teachers"),
        ]),
        Spacer(1, 14),
        P("This is a three session Arduino mini-course for middle schoolers. Every session ends with something "
          "that lights up, beeps, or moves, so students see results within the first half hour. Along the way they "
          "practice the habit that matters most in engineering: wire it, upload it, test it, find what's wrong, "
          "and make it better.", "lede"),
        P("Each session stands on its own. A student who only shows up for session 2 can still finish the reaction "
          "game. Students who come to all three see the bigger idea: <b>hardware plus code makes interactive "
          "systems</b>, and the same few building blocks (pins, inputs, outputs, timing) show up in everything from "
          "a crosswalk signal to a robot arm."),
        Spacer(1, 4),
        three_col_lists([
            ("We provide", [
                "Every part for every pair: Arduino boards, USB cables, breadboards, LEDs, buttons, buzzers, "
                "servos, and wires (about $200 in parts)",
                "Lesson plans for all three sessions, with code you can copy",
                "A training call for your teachers or team. No Arduino experience needed",
                "A Spark Gears mentor on call while you run it",
            ]),
            ("The host provides", [
                "A room with tables and power outlets",
                "The students, plus sign-ups and marketing",
                "One or two adults or team members who attend the training",
                "About an hour before the first session to set up",
            ]),
            ("Students bring", [
                "A laptop: personal or school issued",
                "Chromebooks work through the free Arduino Cloud Editor",
                "Windows or Mac laptops can use the Arduino IDE",
            ]),
        ]),
        Spacer(1, 14),
        h2("What students walk away with"),
        table([
            ["Session", "They build", "They learn"],
            ["1. Traffic light", "Three LEDs that cycle green, yellow, red", "Digital outputs, resistors, breadboard rows, delay()"],
            ["2. Reaction game", "A game that times how fast you press a button", "Inputs, INPUT_PULLUP, random(), millis(), tone()"],
            ["3. Servo creature", "A cardboard creature that nods, flaps, or chomps", "Servo control, analog input, map(), designing behavior"],
        ], [1.25 * inch, 2.55 * inch, BODY_W - 3.8 * inch], zebra=True),
        Spacer(1, 12),
        h2("Before session 1"),
        P("Do this a few days ahead. Most first-day problems are laptop setup, not wiring.", "intro"),
        *numbered([
            "Test one laptop of every type students will bring. On Chromebooks, open "
            "<b>app.arduino.cc</b>, make a free account, and install the Arduino Cloud Agent when it asks. On "
            "Windows or Mac, install Arduino IDE 2 from <b>arduino.cc/en/software</b>.",
            "Upload the built-in Blink example (File, Examples, 01.Basics, Blink) to a board. If the little "
            "on-board LED blinks, that laptop type is ready.",
            "Count out parts into one bag per pair. Label the bags so cleanup is fast.",
            "If students are under 13, check how your school handles Arduino accounts. Some schools have teachers "
            "share one account across the room.",
        ]),
        note("Tip from our first workshops", [
            "Have one spare laptop already set up and tested. When a student's computer refuses to see the board, "
            "swap it in and keep them building instead of debugging drivers in front of the class.",
        ]),
    ]

    # Session 1
    st += [
        PageBreak(),
        P("SESSION 1  |  55 MINUTES", "kicker"),
        P("TRAFFIC LIGHT", "title"),
        Spacer(1, 10),
        P("Students wire red, yellow, and green LEDs on a breadboard and program them to run like a real traffic "
          "light. It's the simplest possible project that still feels like a real thing, and it teaches the two "
          "ideas every later session depends on: a pin can turn something on and off, and code runs one line at a "
          "time, in order.", "lede"),
        h3("Parts per pair"),
        table([
            ["Part", "Qty", "Notes"],
            ["Arduino Uno (or compatible) + USB cable", "1", "Check the cable carries data, not just power"],
            ["Half-size breadboard", "1", ""],
            ["LEDs: red, yellow, green", "1 each", "Long leg is positive (+)"],
            ["220 ohm resistors", "3", "Red, red, brown bands"],
            ["Jumper wires (male to male)", "6 to 8", "Extras for the challenge"],
        ], [2.9 * inch, 0.75 * inch, BODY_W - 3.65 * inch], zebra=True),
        Spacer(1, 10),
        h3("Run of session"),
        table([
            ["Time", "What happens", "Teaching notes"],
            ["0 to 8 min", "Plug in the Arduino, pick the board and port, upload Blink", "Walk the room. Every pair should see the on-board LED blink before moving on."],
            ["8 to 25 min", "Wire the three LEDs", "Show how breadboard rows connect. Each LED: pin to resistor to long leg, short leg to GND."],
            ["25 to 50 min", "Code the light sequence and tune the timing", "Start with just green, then add yellow and red. Let them pick their own timing."],
            ["50 to 55 min", "Show one or two working lights, then clean up", "Parts back in the bag, count the LEDs."],
        ], [0.95 * inch, 2.45 * inch, BODY_W - 3.4 * inch], zebra=True),
        Spacer(1, 10),
        h3("Wiring"),
        table([
            ["LED", "Arduino pin", "Path"],
            ["Red", "8", "Pin 8 to 220 ohm resistor to LED long leg. Short leg to GND rail."],
            ["Yellow", "9", "Pin 9 to 220 ohm resistor to LED long leg. Short leg to GND rail."],
            ["Green", "10", "Pin 10 to 220 ohm resistor to LED long leg. Short leg to GND rail."],
            ["GND rail", "GND", "One wire from any GND pin to the blue (minus) rail on the breadboard."],
        ], [0.9 * inch, 1.0 * inch, BODY_W - 1.9 * inch]),
        Spacer(1, 10),
        code("""
// Traffic light: green, then yellow, then red, forever
const int RED = 8;
const int YELLOW = 9;
const int GREEN = 10;

void setup() {
  pinMode(RED, OUTPUT);
  pinMode(YELLOW, OUTPUT);
  pinMode(GREEN, OUTPUT);
}

void loop() {
  digitalWrite(GREEN, HIGH);   // go
  delay(4000);
  digitalWrite(GREEN, LOW);

  digitalWrite(YELLOW, HIGH);  // slow down
  delay(1500);
  digitalWrite(YELLOW, LOW);

  digitalWrite(RED, HIGH);     // stop
  delay(4000);
  digitalWrite(RED, LOW);
}
""", "Starter code"),
        note("If it doesn't work", [
            "<b>LED stays dark:</b> it's probably in backwards. Flip it so the long leg faces the resistor.",
            "<b>Upload fails:</b> wrong port selected, or a charge-only USB cable. Try another cable first.",
            "<b>Two LEDs light at once:</b> a resistor or wire is in the same breadboard row as the wrong LED.",
        ]),
        h3("Finished early?"),
        *bullets([
            "Add a second set of three LEDs for the cross street. When one direction is green, the other must be red.",
            "Add a \"walk\" signal: a white LED that only turns on while both directions are red.",
            "Make yellow blink three times before turning red.",
        ]),
    ]

    # Session 2
    st += [
        PageBreak(),
        P("SESSION 2  |  55 MINUTES", "kicker"),
        P("REACTION TIME GAME", "title"),
        Spacer(1, 10),
        P("Students build a game: the LED turns on after a random wait, and the Arduino measures how fast you hit "
          "the button. A quick reaction plays a high \"win\" tone on the buzzer. This is where code starts "
          "<i>responding</i> to the real world instead of just running a script, and it gets competitive fast.",
          "lede"),
        h3("Parts per pair"),
        table([
            ["Part", "Qty", "Notes"],
            ["Arduino Uno + USB cable", "1", ""],
            ["Half-size breadboard", "1", ""],
            ["LED + 220 ohm resistor", "1 each", "Any color"],
            ["Push button (4 leg tactile)", "1", "No resistor needed, we use INPUT_PULLUP"],
            ["Piezo buzzer (passive)", "1", "Passive buzzers can play different pitches"],
            ["Jumper wires", "6", ""],
        ], [2.9 * inch, 0.75 * inch, BODY_W - 3.65 * inch], zebra=True),
        Spacer(1, 10),
        h3("Run of session"),
        table([
            ["Time", "What happens", "Teaching notes"],
            ["0 to 8 min", "Plug in and upload Blink as a test", "Same check as session 1. New students may need help picking the port."],
            ["8 to 18 min", "Wire the LED to pin 9", "Pin 9 to resistor to long leg, short leg to GND."],
            ["18 to 30 min", "Wire the button to pin 2 and GND", "Button straddles the center gap. One leg to pin 2, the diagonal leg to GND."],
            ["30 to 50 min", "Build the game: random wait, LED on, time the press, play a tone", "Have them open the Serial Monitor at 9600 baud to see their times."],
            ["50 to 55 min", "Class tournament, then clean up", "Fastest reaction in the room wins bragging rights."],
        ], [0.95 * inch, 2.45 * inch, BODY_W - 3.4 * inch], zebra=True),
        Spacer(1, 10),
        P("<b>Why no resistor on the button?</b> INPUT_PULLUP turns on a resistor that's built into the Arduino. "
          "The pin reads HIGH normally and LOW when the button is pressed. It feels backwards at first, so say it "
          "out loud: <i>pressed means LOW</i>."),
        Spacer(1, 2),
        code("""
// Reaction game: wait for the light, then press as fast as you can
const int LED = 9;
const int BUTTON = 2;
const int BUZZER = 8;

void setup() {
  pinMode(LED, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);   // pressed = LOW
  pinMode(BUZZER, OUTPUT);
  Serial.begin(9600);
  randomSeed(analogRead(A0));      // different random waits every time
}

void loop() {
  Serial.println("Get ready...");
  delay(random(2000, 5000));       // wait 2 to 5 seconds

  digitalWrite(LED, HIGH);
  unsigned long start = millis();
  while (digitalRead(BUTTON) == HIGH) {
    // wait here until the button is pressed
  }
  unsigned long reaction = millis() - start;
  digitalWrite(LED, LOW);

  Serial.print("Your time: ");
  Serial.print(reaction);
  Serial.println(" ms");

  if (reaction < 300) {
    tone(BUZZER, 1200, 300);       // fast: high tone
  } else {
    tone(BUZZER, 500, 300);        // slow: low tone
  }
  delay(2000);
}
""", "Starter code"),
        note("If it doesn't work", [
            "<b>Game finishes instantly with a time of 0:</b> the button is wired across the wrong pair of legs, "
            "so it always reads pressed. Rotate it 90 degrees.",
            "<b>No sound:</b> check the buzzer's + leg goes to pin 8. An active buzzer only plays one pitch, which is fine.",
            "<b>Serial Monitor shows junk characters:</b> set the baud rate to 9600.",
        ]),
        h3("Mods menu for fast finishers"),
        *bullets([
            "Play 3 rounds and print the average time.",
            "\"Too early\" penalty: if the button is already pressed when the LED comes on, play a buzz and restart.",
            "Make it harder every round by shrinking the 300 ms win threshold.",
            "Two player mode: a second button on pin 3, first press wins.",
        ]),
    ]

    # Session 3
    st += [
        PageBreak(),
        P("SESSION 3  |  70 MINUTES", "kicker"),
        P("SERVO CREATURE", "title"),
        Spacer(1, 10),
        P("Students attach a small servo motor to a cardboard creature and decide how it moves. A button steps "
          "through preset poses, or a knob (potentiometer) gives smooth control. This is the first taste of "
          "robotics: code that makes something physically move, and design choices about how it should feel.",
          "lede"),
        h3("Parts per pair"),
        table([
            ["Part", "Qty", "Notes"],
            ["Arduino Uno + USB cable", "1", ""],
            ["Half-size breadboard", "1", ""],
            ["SG90 micro servo with horns", "1", "Brown = GND, red = 5V, orange = signal"],
            ["Push button OR 10k potentiometer", "1", "Pairs choose one"],
            ["Jumper wires", "6", ""],
            ["Cardboard, foam, tape, markers, googly eyes", "Shared", "Set out a craft table"],
        ], [2.9 * inch, 0.75 * inch, BODY_W - 3.65 * inch], zebra=True),
        Spacer(1, 10),
        h3("Run of session"),
        table([
            ["Time", "What happens", "Teaching notes"],
            ["0 to 10 min", "Upload the Sweep example (File, Examples, Servo, Sweep)", "Proves the servo and wiring work before anyone writes code."],
            ["10 to 25 min", "Wire the SG90", "Brown to GND, red to 5V, orange to pin 9."],
            ["25 to 35 min", "Pick a control and wire it", "Button: pin 2 and GND. Knob: middle leg to A0, outer legs to 5V and GND."],
            ["35 to 50 min", "Code the behavior", "Button steps through poses. Knob maps position to angle."],
            ["50 to 70 min", "Build the creature and tune the motion", "Tape the servo horn to a jaw, wing, or head. Adjust angles until it looks alive."],
        ], [0.95 * inch, 2.45 * inch, BODY_W - 3.4 * inch], zebra=True),
        Spacer(1, 10),
        code("""
// Button version: each press moves the creature to its next pose
#include <Servo.h>

Servo creature;
const int BUTTON = 2;
int poses[] = {20, 90, 160};   // angles in degrees, change these
int pose = 0;

void setup() {
  creature.attach(9);
  pinMode(BUTTON, INPUT_PULLUP);
  creature.write(poses[pose]);
}

void loop() {
  if (digitalRead(BUTTON) == LOW) {
    pose = (pose + 1) % 3;           // 0, 1, 2, back to 0
    creature.write(poses[pose]);
    delay(250);
    while (digitalRead(BUTTON) == LOW) { }   // wait for release
  }
}
""", "Starter code: button"),
        code("""
// Knob version: turn the potentiometer, the creature follows
#include <Servo.h>

Servo creature;

void setup() {
  creature.attach(9);
}

void loop() {
  int knob = analogRead(A0);              // 0 to 1023
  int angle = map(knob, 0, 1023, 0, 180); // convert to 0 to 180 degrees
  creature.write(angle);
  delay(15);
}
""", "Starter code: knob"),
        note("If it doesn't work", [
            "<b>Servo twitches or the Arduino resets:</b> the servo is pulling too much power. Make sure nothing "
            "is blocking the horn, and don't run more than one servo off a laptop USB port.",
            "<b>Servo buzzes at the end of its travel:</b> it's being pushed past its limit. Keep angles between "
            "about 10 and 170.",
            "<b>Knob only works over part of its turn:</b> the outer legs are swapped or one isn't connected.",
        ]),
        h3("Ideas for creatures"),
        *bullets([
            "A crocodile whose jaw chomps on each button press.",
            "A bird that flaps faster the further you turn the knob (hint: change the delay, not the angle).",
            "A nodding head that says yes or no to questions.",
        ]),
        CondPageBreak(3.4 * inch),
        h2("Logistics and safety"),
        table([
            ["", ""],
            ["Target grades", "5 to 8. Younger students can do sessions 1 and 3 with more adult help."],
            ["Group size", "As many as your room and helpers can handle, working in pairs. One helper per 5 or 6 pairs works well."],
            ["Session length", "55 to 70 minutes each. They can run on three days in a row or once a week."],
            ["Safety", "Low voltage electronics only (5 volts from USB). No soldering, no power tools, no batteries over 9V. "
                       "Remind students not to bend LED legs back and forth, they snap."],
            ["Cleanup", "Every part goes back in its labeled bag. Count LEDs and servos before students leave."],
        ], [1.4 * inch, BODY_W - 1.4 * inch], header=False),
        contact_block(),
    ]
    build("spark-gears-arduino-workshop-series.pdf", "Arduino Workshop Series", "Lesson plan  |  3 sessions",
          "Three standalone, hands-on sessions for grades 5 to 8: a traffic light, a reaction time game, and a "
          "servo creature. Everything a team or teacher needs to run them.", "Arduino Workshop Series", st)


# =====================================================================
# 2. FTC intro camp
# =====================================================================

def ftc_camp():
    day_w = [0.95 * inch, 2.35 * inch, BODY_W - 3.3 * inch]
    st = [
        glance([
            ("Grades", "Rising 6th to 9th"),
            ("Length", "5 days, about 3 hours a day"),
            ("Group size", "5 to 8 per robot; two robots for 9 to 16"),
            ("Experience", "None needed"),
        ]),
        Spacer(1, 14),
        P("This week-long summer camp puts middle schoolers through the real process of building an FTC-scale "
          "robot. Campers split into one or two mini teams, and each team designs, builds, programs, and promotes "
          "its own robot with step-by-step help from experienced FIRST Tech Challenge students and mentors.", "lede"),
        P("Campers work on electronics, Java programming, mechanical design, and the troubleshooting that fills "
          "most of a real FTC season. They also do the parts people forget about: naming and branding a team, "
          "splitting up roles, and presenting their work. The week ends with a game-day test on a practice field and "
          "a showcase for families."),
        P("It's also a recruiting pipeline. A good number of campers go on to join or start an FTC team, and the "
          "host team gets outreach hours, photos, and a story for its engineering portfolio."),
        Spacer(1, 4),
        three_col_lists([
            ("We provide", [
                "Daily lesson plans for all five days",
                "Training for your mentors before camp",
                "Starter code, build guides, and a game-day score sheet",
                "Printed team materials: posters, stickers, name tags",
                "A Spark Gears mentor on call all week",
            ]),
            ("The host provides", [
                "A room with tables, outlets, and space for a practice field",
                "Campers, sign-ups, and marketing",
                "One FTC robot kit per mini team (a past season robot or a starter kit is fine)",
                "Mentors from your team for every day of camp",
            ]),
            ("Campers bring", [
                "A laptop: personal or school issued",
                "Closed-toe shoes",
                "A snack and a water bottle",
            ]),
        ]),
        Spacer(1, 6),
        P("No robot kit? Tell us when you request support. We'll help you find one to borrow or plan a smaller "
          "version of the camp around what you have.", "small"),
        Spacer(1, 10),
        h2("A typical day"),
        P("Every day follows the same rhythm so campers know what to expect and mentors can plan.", "intro"),
        table([
            ["Block", "Time", "What happens"],
            ["Warm-up", "15 min", "Quick challenge or question of the day, attendance, safety glasses on"],
            ["Mini-lesson", "20 to 30 min", "One new idea, taught with a demo on a real robot"],
            ["Team work", "75 to 90 min", "Teams build, wire, or code with mentors rotating between them"],
            ["Break", "15 min", "Snack, water, away from the tables"],
            ["Team work", "30 to 45 min", "Keep going, test, fix what broke"],
            ["Stand-up", "10 min", "Each team says what they finished, what's stuck, and the plan for tomorrow"],
        ], [1.15 * inch, 1.1 * inch, BODY_W - 2.25 * inch], zebra=True),
    ]

    st += [
        h2("Day by day"),
        h3("Day 1: Meet the challenge"),
        table([
            ["Block", "Activity", "Mentor notes"],
            ["Morning", "Introductions, camp rules, safety glasses. Watch the current FTC game reveal video together.",
             "Keep the video to about 5 minutes. Pause to point out scoring."],
            ["Mid", "Break into mini teams. Each team picks a name, a number, and draws a logo.",
             "Branding gets shy campers talking. Have markers and poster paper ready."],
            ["Late", "Tour a real FTC robot. Campers find the Control Hub, motors, servos, and battery.",
             "Let them hold parts. Let them drive it with a gamepad for a few minutes."],
            ["Wrap", "Each team picks one game task to focus on this week.", "Smaller goals finish. One task done well beats three half done."],
        ], day_w, zebra=True),
        Spacer(1, 8),
        h3("Day 2: Design and start building"),
        table([
            ["Block", "Activity", "Mentor notes"],
            ["Mini-lesson", "How drivetrains work, how to read a build guide, using hex keys and nuts safely.", "Show a finished drivetrain next to its parts."],
            ["Team work", "Sketch the robot on paper. Decide who builds the drivetrain and who builds the mechanism.", "Every camper gets a job. Rotate jobs each day."],
            ["Build", "Start the drivetrain: frame, motors, wheels.", "Check that motors are mounted the same way on both sides."],
        ], day_w, zebra=True),
        Spacer(1, 8),
        h3("Day 3: Keep building"),
        table([
            ["Block", "Activity", "Mentor notes"],
            ["Mini-lesson", "Wiring: Control Hub ports, motor and servo cables, keeping wires tidy.", "Show a messy wiring job next to a clean one."],
            ["Build", "Finish the drivetrain, wire it, start the scoring mechanism (intake, arm, or claw).", "Cable management matters. Loose wires cause most robot failures."],
            ["Test", "First drive test with sample code.", "Tape a box on the floor and have them drive in and out of it."],
        ], day_w, zebra=True),
        Spacer(1, 8),
        h3("Day 4: Program the robot"),
        table([
            ["Block", "Activity", "Mentor notes"],
            ["Mini-lesson", "Java in OnBot Java: what an OpMode is, gamepad input, setting motor power.", "OnBot Java runs in the browser from the Control Hub, nothing to install."],
            ["Code", "Write a TeleOp so a driver can control the robot, then map the mechanism to buttons.", "Start from the code below. Let campers change values and see what happens."],
            ["Stretch", "A 5 second autonomous that drives forward and parks.", "Timing based is fine. Encoders are a bonus."],
        ], day_w, zebra=True),
        Spacer(1, 8),
        h3("Day 5: Game day and showcase"),
        table([
            ["Block", "Activity", "Mentor notes"],
            ["Morning", "Final fixes and driver practice.", "Freeze the code an hour before the game. No last-second changes."],
            ["Game test", "Each team plays timed matches on the practice field and records scores.", "Use the score sheet. Cheer loudly."],
            ["Showcase", "Families come in. Each team presents its robot, team name, and what they learned.", "2 to 3 minutes per team. Every camper says one thing."],
        ], day_w, zebra=True),
    ]

    st += [
        PageBreak(),
        h2("Starter TeleOp code"),
        P("Paste this into OnBot Java on the Control Hub. In the robot configuration, name the drive motors "
          "<b>left</b> and <b>right</b>. Campers then add their own mechanism controls inside the loop."),
        code("""
package org.firstinspires.ftc.teamcode;

import com.qualcomm.robotcore.eventloop.opmode.LinearOpMode;
import com.qualcomm.robotcore.eventloop.opmode.TeleOp;
import com.qualcomm.robotcore.hardware.DcMotor;

@TeleOp(name = "Camp Drive")
public class CampDrive extends LinearOpMode {
    @Override
    public void runOpMode() {
        DcMotor left = hardwareMap.get(DcMotor.class, "left");
        DcMotor right = hardwareMap.get(DcMotor.class, "right");
        right.setDirection(DcMotor.Direction.REVERSE);

        waitForStart();

        while (opModeIsActive()) {
            double drive = -gamepad1.left_stick_y;   // push forward = drive forward
            double turn = gamepad1.right_stick_x;

            left.setPower(drive + turn);
            right.setPower(drive - turn);

            telemetry.addData("Drive", drive);
            telemetry.addData("Turn", turn);
            telemetry.update();
        }
    }
}
""", "CampDrive.java"),
        h2("Team roles"),
        P("Each camper takes one role per day and rotates, so everyone builds, codes, and drives at least once.", "intro"),
        table([
            ["Role", "What they do"],
            ["Builder", "Assembles and repairs the robot, keeps track of parts"],
            ["Programmer", "Writes and tests code, works with the driver to tune controls"],
            ["Driver", "Practices driving, gives feedback on what's hard to control"],
            ["Team captain", "Keeps the team on schedule, leads the daily stand-up"],
            ["Brand lead", "Logo, team poster, photos, and the showcase presentation"],
        ], [1.4 * inch, BODY_W - 1.4 * inch], zebra=True),
        Spacer(1, 12),
        h2("Logistics and safety"),
        table([
            ["", ""],
            ["Target grades", "Rising 6th through 9th graders. Strong 5th graders can join with a parent's okay."],
            ["Group size", "About 5 to 8 campers per robot. With two robots, run two teams of up to 8."],
            ["Daily length", "About 3 hours a day for 5 days. Mornings work best in summer."],
            ["Mentors", "At least 1 experienced mentor per team, plus 1 adult on site at all times."],
            ["Safety", "Safety glasses for every camper and mentor whenever a robot is powered or being built. "
                       "Closed-toe shoes. Robots are disabled when anyone reaches into them. Batteries are "
                       "unplugged when not in use and never charged unattended."],
            ["Families", "Invite families to the Day 5 showcase. It's the best photo opportunity of the week."],
        ], [1.4 * inch, BODY_W - 1.4 * inch], header=False),
        contact_block(),
    ]
    build("spark-gears-ftc-intro-camp.pdf", "FTC Intro Robotics Camp", "Camp plan  |  5 days",
          "A week-long summer camp where middle schoolers form mini teams and design, build, program, and present "
          "an FTC-scale robot.", "FTC Intro Robotics Camp", st)


# =====================================================================
# 3. Robotics and automation course
# =====================================================================

def robotics_course():
    wk_w = [1.05 * inch, BODY_W - 1.05 * inch]

    def week(label, title, topics, lab, outcome, prep):
        rows = [
            ["Topics", P(topics, "cell")],
            ["Lab", P(lab, "cell")],
            ["Outcome", P(outcome, "cell")],
            ["Prep", P(prep, "cell")],
        ]
        rows = [[P(r[0].upper(), "th"), r[1]] for r in rows]
        t = Table([[P(f"{label.upper()}  |  {title.upper()}", "th"), ""]] + rows, colWidths=wk_w)
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("BACKGROUND", (0, 0), (-1, 0), YELLOW),
            ("LINEBELOW", (0, 0), (-1, 0), 1.2, INK),
            ("BOX", (0, 0), (-1, -1), 1.2, INK),
            ("LINEBELOW", (0, 1), (-1, -1), 0.6, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return KeepTogether([t, Spacer(1, 10)])

    st = [
        glance([
            ("Grades", "6 to 9"),
            ("Length", "9 weeks, 1 session a week"),
            ("Session", "2 to 2.5 hours"),
            ("Capstone", "Maze-solving robot. Kits go home"),
        ]),
        Spacer(1, 14),
        P("This is a nine week, build-first robotics course. No technical background is needed. Each class is a "
          "short lesson followed by a long lab where students build, code, and troubleshoot. The first five weeks "
          "cover the fundamentals one piece at a time. The last four put them together into a robot that finds its "
          "own way through a maze, and students keep their kits when it's over.", "lede"),
        P("It's designed for teams and partners who want to run something longer than a one-day event: an after "
          "school club, a library series, or a weekend program at a community center."),
        h2("Course at a glance"),
        table([
            ["Week", "Topic or project", "Skills learned"],
            ["1", "Arduino 101 and LEDs", "Circuit basics, setting up the editor"],
            ["2", "Inputs and breadboards", "Digital vs analog, wiring"],
            ["3", "Sensors", "Reading inputs, if statements"],
            ["4", "Servos", "Motor control, PWM"],
            ["5", "Integrated project", "Combining inputs, outputs, and logic"],
            ["6", "Robot base build", "Chassis, mounting, wiring safety"],
            ["7", "Bumpers and sensors", "Prototyping, first drive tests"],
            ["8", "Navigation code", "Autonomous programming"],
            ["9", "Capstone showcase", "Testing, debugging, presenting"],
        ], [0.7 * inch, 2.6 * inch, BODY_W - 3.3 * inch], zebra=True),
        Spacer(1, 12),
        h2("How each session runs"),
        table([
            ["Part", "Time", "What happens"],
            ["Concept of the day", "20 to 30 min", "Short talk and live demo of the new component or idea"],
            ["Lab time", "60 to 75 min", "Students build and code with instructors circulating"],
            ["Break", "15 min", "Snack and movement, away from the benches"],
            ["Project work", "30 to 45 min", "Troubleshoot, improve, and save working code"],
        ], [1.6 * inch, 1.1 * inch, BODY_W - 2.7 * inch], zebra=True),
    ]

    st += [
        h2("Weekly plan"),
        week("Week 1", "Introduction and Arduino basics",
             "Lab safety, the course plan, a tour of the Arduino board and its pins, what each kit part does, setting "
             "up the editor.",
             "Breadboard practice, powering an LED, uploading and editing the Blink example.",
             "Every student powers and programs their first circuit.",
             "Test every laptop type in advance. Pre-sort kits so each student gets one bag."),
        week("Week 2", "Digital vs analog inputs",
             "Digital and analog signals, series vs parallel circuits, reading a resistor.",
             "Read a push button. Read a potentiometer and print the values to the Serial Monitor.",
             "Modify Blink to react to a button, then make an LED that dims with a knob.",
             "Have a multimeter on hand to show voltage changing as the knob turns."),
        week("Week 3", "Sensors and conditionals",
             "What sensors do, using if statements to react to sensor readings.",
             "Test limit switches and a color sensor. Print readings and set thresholds.",
             "An LED or buzzer turns on when a sensor changes state.",
             "Bring a few colored cards for the color sensor so readings are consistent."),
        week("Week 4", "Servo motors and output control",
             "How servos work, pulse width modulation (PWM), positional vs continuous servos.",
             "Control a servo's position with a button or a potentiometer.",
             "Each student completes a simple moving part.",
             "Show both servo types side by side. Students mix them up later if they don't see the difference now."),
        week("Week 5", "Combining inputs and outputs",
             "Using sensors and motors in the same program, a step-by-step way to troubleshoot.",
             "Build a security gate: a servo arm lifts when a sensor is triggered, with a buzzer alarm.",
             "Students demo a working system and explain how they debugged it.",
             "This is the midpoint. Check in with students who are behind before the capstone starts."),
        week("Weeks 6 and 7", "Capstone planning and chassis",
             "What maze solving is, bumper logic, a simple design process: plan, build, test, change.",
             "Plan the build in steps, assemble the robot base, mount the Arduino and battery, wire safely.",
             "The robot drives with simple code and the bumpers are tested.",
             "Set up the practice maze by the end of week 6 so students can test against real walls."),
        week("Weeks 8 and 9", "Programming, testing, and showcase",
             "Autonomous navigation, loop strategies, tuning turn times, cleaning up code.",
             "Fine-tune navigation, run timed maze trials, then the final showcase in week 9.",
             "A finished maze-solving robot. All kits go home with students.",
             "Invite families to week 9. Print certificates ahead of time."),
    ]

    st += [
        CondPageBreak(4 * inch),
        h2("The capstone robot"),
        P("The robot drives on two continuous rotation servos and uses two limit switches on the front as "
          "bumpers. When a bumper hits a wall, the robot backs up, turns away, and tries again. It's a simple "
          "strategy, but it gets through most beginner mazes, and students can improve it in a dozen ways."),
        code("""
// Bump-and-turn maze robot
#include <Servo.h>

Servo leftWheel, rightWheel;
const int LEFT_BUMP = 2;
const int RIGHT_BUMP = 3;

void drive(int l, int r) { leftWheel.write(l); rightWheel.write(r); }
void forward()   { drive(180, 0); }    // wheels face opposite ways
void reverse()   { drive(0, 180); }
void turnLeft()  { drive(0, 0); }
void turnRight() { drive(180, 180); }

void setup() {
  leftWheel.attach(9);
  rightWheel.attach(10);
  pinMode(LEFT_BUMP, INPUT_PULLUP);
  pinMode(RIGHT_BUMP, INPUT_PULLUP);
}

void loop() {
  if (digitalRead(LEFT_BUMP) == LOW) {        // hit on the left
    reverse();   delay(400);
    turnRight(); delay(350);
  } else if (digitalRead(RIGHT_BUMP) == LOW) { // hit on the right
    reverse();   delay(400);
    turnLeft();  delay(350);
  } else {
    forward();
  }
}
""", "Starter capstone code"),
        P("Turn times depend on the battery, the floor, and the wheels. Have students measure a 90 degree turn on "
          "their own robot and change the 350 to match.", "small"),
        Spacer(1, 8),
        h3("Suggested capstone rubric"),
        table([
            ["Area", "Points", "What full points looks like"],
            ["Maze navigation", "40", "Robot reaches the end of the maze in at least one of three runs"],
            ["Code reliability", "30", "Code is readable, commented, and works the same way run after run"],
            ["Documentation", "20", "A short build log: what they tried, what broke, how they fixed it"],
            ["Showcase", "10", "Explains how the robot decides what to do"],
        ], [1.5 * inch, 0.7 * inch, BODY_W - 2.2 * inch], zebra=True),
    ]

    st += [
        CondPageBreak(4 * inch),
        h2("Materials"),
        three_col_lists([
            ("In each student kit", [
                "Arduino Uno or compatible (not a Mega)",
                "Breadboard and jumper wire set",
                "Resistors and LEDs",
                "Positional servo and 2 continuous rotation servos",
                "2 limit switches and a color sensor",
                "Robot chassis with wheels",
                "USB cable",
            ]),
            ("Instructor supplies", [
                "Maze walls (cardboard or foam board works)",
                "Tape, zip ties, and spare parts",
                "A few extra charged battery packs",
                "Projector for demos",
            ]),
            ("Students bring", [
                "A laptop with Google Chrome",
                "School Chromebooks are fine",
                "Windows or Mac laptops are fine",
                "A snack and a water bottle",
            ]),
        ]),
        Spacer(1, 12),
        h2("Staffing and tips"),
        P("<b>Staff:</b> 1 lead instructor and 1 assistant for every 10 students. An FTC team can easily cover "
          "this with 3 or 4 members rotating weeks."),
        *bullets([
            "<b>Debug in small steps.</b> Check wiring and code after every change so problems are easy to find.",
            "<b>Save every working version.</b> Have students save a copy with the week number before changing "
            "anything (maze_week8_v2).",
            "<b>Show, don't just tell.</b> Pass new components around and project a close-up before students wire them.",
            "<b>Pair students thoughtfully.</b> Put a more confident student with one who's newer. Both learn more.",
            "<b>Keep a parts bin.</b> Something will break every week. A spare servo saves a whole lesson.",
        ]),
        Spacer(1, 6),
        h3("Extensions for students who finish early"),
        *bullets([
            "Line following with an IR sensor instead of bumpers.",
            "Wall following: keep one bumper lightly touching the wall to trace the maze.",
            "Add an ultrasonic distance sensor so the robot turns before it hits anything.",
        ]),
        contact_block(),
    ]
    build("spark-gears-robotics-automation-course.pdf", "Robotics and Automation Course", "Syllabus  |  9 weeks",
          "A nine week, hands-on course for grades 6 to 9 that ends with every student building a maze-solving "
          "Arduino robot they get to keep.", "Robotics and Automation Course", st)


# =====================================================================
# 4. Outreach event roadmap
# =====================================================================

def roadmap():
    st = [
        P("Running your first outreach event can feel like a lot. It's really five steps, and you don't have to do "
          "them alone. This roadmap is the same plan our mentors walk teams through. Use it with or without a Spark "
          "Gears kit.", "lede"),
        h2("The five steps"),
    ]
    steps = [
        ("1", "Pick your event", "6 to 8 weeks out", [
            "Choose a format from the table below. For a first event, a library station or school demo is the "
            "easiest to pull off.",
            "Find a host: your public library, a teacher at a nearby elementary or middle school, a community center, "
            "or a scout troop. Ask early. Libraries plan their calendars months ahead.",
            "Agree on a date, a time, a room, and roughly how many kids to expect.",
        ]),
        ("2", "Plan it with a mentor", "4 to 6 weeks out", [
            "Request support at sparkgearsinitiative.org/for-teams.html. A Spark Gears mentor is assigned to your team.",
            "Meet with your mentor to pick activities, set a timeline, and divide jobs on your team.",
            "Make a flyer and send it to your host to share. Post it on your team's social media.",
            "Fill out the run-of-show template so everyone knows their job on event day.",
        ]),
        ("3", "Get the kit", "2 to 3 weeks out", [
            "Request a supply kit. Rookie teams and Title I schools get priority.",
            "Open it the day it arrives and check everything against the list. Test every electronic part.",
            "Print activity sheets, sign-in sheets, and the volunteer hour log.",
            "Do a full practice run with your team. Time each activity.",
        ]),
        ("4", "Run it", "Event day", [
            "Arrive at least an hour early to set up stations and test robots.",
            "Your mentor is on call the whole time, and in person when we can reach you in the DC, Maryland, and "
            "Virginia area.",
            "Assign one person to take photos (with permission) and one to count attendance.",
            "Have every volunteer sign in and out on the hour log.",
        ]),
        ("5", "Log the impact", "Within a week", [
            "Send the signed hour log to us and we'll verify volunteer hours.",
            "Write down the numbers while they're fresh: attendees, ages, volunteers, hours, sign-ups.",
            "Thank your host. Ask if you can come back next season.",
            "Add the event to your engineering portfolio with a photo and two or three sentences.",
        ]),
    ]
    for num, title, when, items in steps:
        head = Table([[P(f"0{num}", "title"), [P(title.upper(), "h3"), P(when.upper(), "kicker")]]],
                     colWidths=[0.75 * inch, BODY_W - 0.75 * inch])
        head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                  ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("TOPPADDING", (0, 0), (-1, -1), 0)]))
        box = Table([[[head, Spacer(1, 4), checklist(items, BODY_W - 24)]]], colWidths=[BODY_W])
        box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.2, INK), ("LEFTPADDING", (0, 0), (-1, -1), 12),
                                 ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 10),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
        st += [KeepTogether([box, Spacer(1, 10)])]

    st += [
        CondPageBreak(3.5 * inch),
        h2("Pick a format"),
        table([
            ["Format", "Length", "Audience", "Good first event?"],
            ["Library STEM station", "2 to 4 hours", "Drop-in, all ages, families", "Yes. Low pressure and flexible"],
            ["School robotics demo", "About 1 hour", "A classroom or assembly", "Yes. Short and easy to schedule"],
            ["Arduino workshop", "1 to 3 sessions", "Grades 5 to 8, in pairs", "Yes, with our lesson plans"],
            ["Intro robotics camp", "5 days", "Grades 6 to 9, mini teams", "Better for a second or third event"],
        ], [1.75 * inch, 1.1 * inch, 1.9 * inch, BODY_W - 4.75 * inch], zebra=True),
        Spacer(1, 12),
        h2("What to record for your portfolio"),
        table([
            ["Number", "How to get it"],
            ["Attendees", "Sign-in sheet or a tally counter at the door"],
            ["Age range", "Ask the host, or add a grade column to the sign-in sheet"],
            ["Volunteers and hours", "The volunteer hour log"],
            ["Follow-ups", "Kids or parents who asked about joining a team or a camp"],
            ["Photos", "Wide shots of the room and close-ups of hands on robots. Get permission for faces."],
        ], [1.8 * inch, BODY_W - 1.8 * inch], zebra=True),
        contact_block(),
    ]
    build("spark-gears-outreach-roadmap.pdf", "Outreach Event Roadmap", "Planning guide",
          "The five-step plan from picking an event to logging its impact, with a checklist and timeline for each step.",
          "Outreach Event Roadmap", st)


# =====================================================================
# 5. Run-of-show template
# =====================================================================

def field_row(labels, widths):
    cells = [[P(l.upper(), "glance_k"), Spacer(1, 16)] for l in labels]
    t = Table([cells], colWidths=widths)
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.2, INK), ("INNERGRID", (0, 0), (-1, -1), 0.8, INK),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("LEFTPADDING", (0, 0), (-1, -1), 7)]))
    return t


def run_of_show():
    q = BODY_W / 4
    st = [
        P("Fill this out with your team a week before the event and bring printed copies. Example times assume a "
          "2 hour event starting at 10:00. Cross them out and write your own.", "body"),
        Spacer(1, 4),
        field_row(["Event name", "Date"], [q * 3, q]),
        field_row(["Location and room", "Start time", "End time"], [q * 2, q, q]),
        field_row(["Host contact (name and phone)", "Spark Gears mentor (name and phone)"], [q * 2, q * 2]),
        Spacer(1, 12),
        h2("Roles"),
        table([
            ["Role", "Name", "Job"],
            ["Event lead", "", "Runs the timeline, talks to the host, makes the calls"],
            ["Station leads", "", "One per station. Runs the activity and keeps the line moving"],
            ["Greeter", "", "Welcomes families, handles sign-in, points people to stations"],
            ["Photographer", "", "Photos and video. Asks permission before photographing faces"],
            ["Floater", "", "Fixes robots, refills supplies, covers breaks"],
        ], [1.3 * inch, 1.9 * inch, BODY_W - 3.2 * inch], valign="MIDDLE", pad=8),
        Spacer(1, 12),
        h2("Timeline"),
        table([
            ["Time", "What happens", "Who"],
            ["8:45", "Team meets at location. Unload supplies.", ""],
            ["9:00", "Set up tables and stations. Charge and test every robot.", ""],
            ["9:40", "Walk-through: each station lead runs their activity once.", ""],
            ["9:50", "Final huddle. Confirm roles and break schedule.", ""],
            ["10:00", "Doors open. Greeter starts sign-in.", ""],
            ["10:05", "Quick welcome: who we are, what FIRST is (2 minutes).", ""],
            ["10:10", "Stations running.", ""],
            ["11:00", "Robot demo or driving challenge for everyone.", ""],
            ["11:15", "Stations running.", ""],
            ["11:50", "Wrap up. Hand out flyers about joining a team.", ""],
            ["12:00", "Event ends. Teardown starts.", ""],
            ["12:30", "Team debrief: what worked, what to change.", ""],
        ], [0.8 * inch, BODY_W - 2.2 * inch, 1.4 * inch], valign="MIDDLE", pad=6),
    ]
    st += [
        PageBreak(),
        h2("Stations"),
        table([
            ["Station", "Activity", "Supplies", "Lead"],
            ["1", "", "", ""],
            ["2", "", "", ""],
            ["3", "", "", ""],
            ["4", "", "", ""],
        ], [0.7 * inch, 2.4 * inch, 2.4 * inch, BODY_W - 5.5 * inch], valign="MIDDLE", pad=18),
        Spacer(1, 12),
        h2("Packing list"),
    ]
    pack = [
        ["Robots, controllers, and charged batteries", "Battery charger and power strip"],
        ["Supply kit and spare parts", "Laptops and chargers"],
        ["Printed activity sheets", "Sign-in sheet and volunteer hour log"],
        ["Team banner, flyers, and stickers", "Tape, zip ties, scissors, markers"],
        ["Safety glasses", "First aid kit and water"],
    ]
    st += [two_col_checklist(pack), Spacer(1, 12), h2("Teardown")]
    tear = [
        ["Count robots, batteries, and controllers", "Pack the supply kit and count small parts"],
        ["Unplug and pack all chargers", "Pick up trash and wipe tables"],
        ["Put the room back the way you found it", "Collect the sign-in sheet and hour log"],
        ["Thank the host in person", "Group photo with the team"],
    ]
    st += [two_col_checklist(tear), Spacer(1, 12), h2("If something goes wrong")]
    st += [table([
        ["Problem", "Plan"],
        ["A robot breaks", "Swap to the backup activity at that station. The floater fixes it off to the side."],
        ["Way more kids than expected", "Shorten each turn, combine two stations, or run a group demo while kids wait."],
        ["Nobody shows up for 20 minutes", "Send two people with a robot to the library entrance or lobby to bring people in."],
        ["Someone gets hurt", "Stop the activity, get the host and an adult, use the first aid kit. Call 911 if it's serious."],
    ], [1.9 * inch, BODY_W - 1.9 * inch], zebra=True)]
    st += [Spacer(1, 12), h2("Debrief notes"), write_lines(5)]
    build("spark-gears-run-of-show.pdf", "Event Run-of-Show", "Template  |  Print and fill in",
          "A timeline for event day: setup, stations, roles, and teardown. Fill it out with your team the week before.",
          "Event Run-of-Show", st)


# =====================================================================
# 6. Volunteer hour log
# =====================================================================

def hour_log():
    q = BODY_W / 4
    st = [
        P("Every volunteer signs in when they arrive and out when they leave, including setup and teardown time. "
          "After the event, have your host or Spark Gears mentor sign the bottom and email a photo or scan to "
          f"<b>{EMAIL}</b>. We'll verify the hours within a week.", "body"),
        Spacer(1, 4),
        field_row(["Team name and number", "Event date"], [q * 3, q]),
        field_row(["Event name and location", "Event type"], [q * 3, q]),
        Spacer(1, 12),
    ]
    rows = [["#", "Volunteer name", "Role", "Time in", "Time out", "Hours", "Initials"]]
    rows += [[str(i), "", "", "", "", "", ""] for i in range(1, 13)]
    rows.append(["", "", "", "", P("<b>TOTAL</b>", "cell"), "", ""])
    w = [0.35 * inch, 2.15 * inch, 1.25 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch]
    w.append(BODY_W - sum(w))
    t = table(rows, w, valign="MIDDLE", pad=5)
    t.setStyle(TableStyle([("INNERGRID", (0, 0), (-1, -1), 0.6, LINE), ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, PAPER]),
                           ("BACKGROUND", (0, -1), (-1, -1), YELLOW_SOFT), ("LINEABOVE", (0, -1), (-1, -1), 1.2, INK),
                           ("ROWHEIGHT", (0, 1), (-1, -1), 22)]))
    t._argH = [None] + [21] * (len(rows) - 1)
    st += [t, Spacer(1, 14)]
    sign = Table([[
        [P("VERIFIED BY (HOST OR MENTOR)", "glance_k"), Spacer(1, 26)],
        [P("SIGNATURE", "glance_k"), Spacer(1, 26)],
        [P("DATE", "glance_k"), Spacer(1, 26)],
    ]], colWidths=[q * 1.6, q * 1.6, q * 0.8])
    sign.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.2, INK), ("INNERGRID", (0, 0), (-1, -1), 0.8, INK),
                              ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7),
                              ("TOPPADDING", (0, 0), (-1, -1), 5)]))
    st += [sign, Spacer(1, 8),
           P("Count hours to the nearest quarter hour. Use the event start and end times for anyone who forgot to "
             "sign out, and note it in the Initials column.", "small")]
    build("spark-gears-volunteer-hour-log.pdf", "Volunteer Hour Log", "Form  |  Print and fill in",
          "Track your team's hours at the event so we can verify them afterward.", "Volunteer Hour Log", st)


if __name__ == "__main__":
    register_fonts(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "fonts"))
    S = styles()
    os.makedirs(OUT, exist_ok=True)
    arduino()
    ftc_camp()
    robotics_course()
    roadmap()
    run_of_show()
    hour_log()
