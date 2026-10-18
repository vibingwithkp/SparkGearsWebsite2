"""Builds the free downloads on for-teams.html into downloads/.

Needs reportlab plus static instances of the site fonts (Big Shoulders Display
900 and Instrument Sans 400/600/700) in a fonts folder:

    python3 tools/build_pdfs.py path/to/fonts

Font files expected: BS-900.ttf, IS-400.ttf, IS-600.ttf, IS-700.ttf
Each file needs its own PostScript name (InstrumentSans-Bold and so on). Files cut
from the variable fonts with fontTools keep the default name, and then every weight
embeds as Regular, so rename them first.

Also writes downloads/code-snippets.json, which the site's PDF preview uses for
its copy-code buttons.

House style for the copy: no em dashes, en dashes for number ranges (5–8),
hyphenated compound modifiers (three-session, low-voltage), and sentence case
headings.
"""

import json
import os
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Preformatted, Spacer, Table, TableStyle,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "downloads")
LOGO = os.path.join(ROOT, "assets", "brand", "spark-gears-logo.png")

INK = colors.HexColor("#17150f")
MUTED = colors.HexColor("#5f594b")
RULE = colors.HexColor("#cfcac0")
CODE_BG = colors.HexColor("#f5f4f1")
TIP_BG = colors.HexColor("#fdf6e3")
YELLOW = colors.HexColor("#ffc233")

EMAIL = "sparkgearsinitiative@gmail.com"
PHONE = "571-429-9220"
SITE = "sparkgearsinitiative.org"

PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch
BODY_W = PAGE_W - 2 * MARGIN
DASH = "–"  # en dash, for ranges only


def register_fonts(font_dir):
    for name, file in [("Display", "BS-900.ttf"), ("Body", "IS-400.ttf"),
                       ("Body-Semi", "IS-600.ttf"), ("Body-Bold", "IS-700.ttf")]:
        pdfmetrics.registerFont(TTFont(name, os.path.join(font_dir, file)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body", boldItalic="Body-Bold")


# ---------- styles ----------

def styles():
    s = {}
    s["body"] = ParagraphStyle("body", fontName="Body", fontSize=9.8, leading=14.6, textColor=INK, spaceAfter=8)
    s["lede"] = ParagraphStyle("lede", parent=s["body"], fontSize=11, leading=16.4)
    s["small"] = ParagraphStyle("small", parent=s["body"], fontSize=8.4, leading=11.8, textColor=MUTED, spaceAfter=6)
    s["cell"] = ParagraphStyle("cell", parent=s["body"], fontSize=8.9, leading=12.4, spaceAfter=0)
    s["th"] = ParagraphStyle("th", parent=s["cell"], fontName="Body-Semi", textColor=MUTED, fontSize=8.4)
    s["bullet"] = ParagraphStyle("bullet", parent=s["body"], leftIndent=13, bulletIndent=1, spaceAfter=4, bulletFontName="Body")
    s["title"] = ParagraphStyle("title", fontName="Display", fontSize=38, leading=36, textColor=INK)
    s["h1"] = ParagraphStyle("h1", fontName="Body-Bold", fontSize=21, leading=25, textColor=INK, spaceAfter=10)
    s["kicker"] = ParagraphStyle("kicker", fontName="Body-Semi", fontSize=9, leading=12, textColor=MUTED, spaceAfter=3)
    s["h2"] = ParagraphStyle("h2", fontName="Body-Bold", fontSize=13.5, leading=17, textColor=INK, spaceBefore=14, spaceAfter=7)
    s["h3"] = ParagraphStyle("h3", fontName="Body-Bold", fontSize=10.6, leading=14, textColor=INK, spaceBefore=8, spaceAfter=5)
    s["intro"] = ParagraphStyle("intro", parent=s["body"])
    s["code"] = ParagraphStyle("code", fontName="Courier", fontSize=8, leading=10.4, textColor=INK)
    s["caption"] = ParagraphStyle("caption", fontName="Body-Semi", fontSize=8.2, leading=11, textColor=MUTED, spaceAfter=3)
    return s


S = None
HEAD_STYLES = ("h1", "h2", "h3", "kicker", "intro")


def P(text, style="body"):
    return Paragraph(text, S[style])


def h1(text):
    return P(text, "h1")


def h2(text):
    return P(text, "h2")


def h3(text):
    return P(text, "h3")


def bullets(items):
    return [Paragraph(t, S["bullet"], bulletText="•") for t in items]


def numbered(items):
    return [Paragraph(t, S["bullet"], bulletText=f"{i}.") for i, t in enumerate(items, 1)]


class Box(Flowable):
    """Empty tick box for printed checklists."""

    def wrap(self, aw, ah):
        return 9, 9

    def draw(self):
        self.canv.setStrokeColor(INK)
        self.canv.setLineWidth(0.8)
        self.canv.rect(0, -1, 8.5, 8.5, stroke=1, fill=0)


def checklist(items, width=None, style="bullet"):
    width = width or BODY_W
    t = Table([[Box(), Paragraph(i, ParagraphStyle("chk", parent=S[style], leftIndent=0, spaceAfter=0))] for i in items],
              colWidths=[16, width - 16])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 0), (0, -1), 4.4),
                           ("TOPPADDING", (1, 0), (1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    return t


def two_col_checklist(pairs):
    half = BODY_W / 2
    t = Table([[checklist([a for a, _ in pairs], half - 10, "cell"), checklist([b for _, b in pairs], half - 10, "cell")]],
              colWidths=[half, half])
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    return t


def table(rows, widths, header=True, valign="TOP", pad=4.5):
    """Plain ruled table: a dark rule under the header, hairlines between rows."""
    data = []
    for r_i, row in enumerate(rows):
        data.append([Paragraph(c, S["th" if header and r_i == 0 else "cell"]) if isinstance(c, str) else c for c in row])
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), valign),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad + 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, RULE),
    ]
    if header:
        cmds.append(("LINEBELOW", (0, 0), (-1, 0), 0.9, INK))
    else:
        cmds.append(("LINEABOVE", (0, 0), (-1, 0), 0.5, RULE))
    t.setStyle(TableStyle(cmds))
    return KeepTogether([t, Spacer(1, 6)]) if len(rows) <= 12 else t


EXPORTED = {}  # pdf filename -> its snippets
SNIPPETS = []  # code blocks in the PDF being built, exported for the site's copy buttons


class PageMark(Flowable):
    """Zero-size flowable that records which page a code block lands on."""

    def __init__(self, entry):
        super().__init__()
        self.entry = entry

    def wrap(self, aw, ah):
        return 0, 0

    def draw(self):
        self.entry["page"] = self.canv.getPageNumber()


def code(src, caption, label=None):
    entry = {"title": label or caption, "code": src.strip("\n") + "\n"}
    SNIPPETS.append(entry)
    t = Table([[Preformatted(src.strip("\n"), S["code"])]], colWidths=[BODY_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return KeepTogether([PageMark(entry), P(caption, "caption"), t, Spacer(1, 10)])


def tip(title, text):
    t = Table([[[P(f"<b>{title}</b>", "cell"), Spacer(1, 3), P(text, "cell")]]], colWidths=[BODY_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TIP_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 2.5, YELLOW),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    return KeepTogether([Spacer(1, 4), t, Spacer(1, 8)])


def write_lines(n):
    t = Table([[""]] * n, colWidths=[BODY_W], rowHeights=[22] * n)
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.5, MUTED)]))
    return t


def closing():
    t = Table([[P(f"Questions? Email <b>{EMAIL}</b> or call <b>{PHONE}</b>. You can request a mentor or a supply "
                  f"kit at {SITE}/for-teams.html.", "cell")]], colWidths=[BODY_W])
    t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.9, INK), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 0), (-1, -1), 9)]))
    return KeepTogether([Spacer(1, 14), t])


# ---------- page furniture ----------

class Doc(BaseDocTemplate):
    def __init__(self, path, title, doc_type, subtitle, short):
        super().__init__(path, pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=MARGIN, bottomMargin=MARGIN + 6,
                         title=title, author="Spark Gears Initiative", subject=subtitle,
                         creator="Spark Gears Initiative")
        self.doc_title, self.doc_type, self.short = title, doc_type, short
        self.title_p = Paragraph(title.upper(), S["title"])
        self.title_h = self.title_p.wrap(BODY_W, 300)[1]
        self.sub_p = Paragraph(subtitle, ParagraphStyle("sub", parent=S["lede"], textColor=MUTED, spaceAfter=0))
        self.sub_h = self.sub_p.wrap(BODY_W * 0.8, 200)[1]
        self.head_h = 56 + self.title_h + 8 + self.sub_h + 14
        first = Frame(MARGIN, MARGIN + 6, BODY_W, PAGE_H - 2 * MARGIN - 6 - self.head_h - 12, id="first",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        later = Frame(MARGIN, MARGIN + 6, BODY_W, PAGE_H - 2 * MARGIN - 6 - 0.3 * inch, id="later",
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="First", frames=[first], onPage=self.first_page, autoNextPageTemplate="Later"),
            PageTemplate(id="Later", frames=[later], onPage=self.later_page),
        ])

    def footer(self, c):
        c.setFont("Body", 7.6)
        c.setFillColor(MUTED)
        c.drawString(MARGIN, MARGIN - 14, f"Spark Gears Initiative  ·  {SITE}")
        c.drawRightString(PAGE_W - MARGIN, MARGIN - 14, f"{self.short}  ·  page {c.getPageNumber()}")

    def first_page(self, c, doc):
        c.saveState()
        c.setFillColor(YELLOW)
        c.rect(0, PAGE_H - 6, PAGE_W, 6, stroke=0, fill=1)
        top = PAGE_H - MARGIN + 10
        c.drawImage(LOGO, MARGIN, top - 24, 24, 24, mask="auto")
        c.setFillColor(INK)
        c.setFont("Body-Semi", 9.5)
        c.drawString(MARGIN + 31, top - 15.5, "Spark Gears Initiative")
        c.setFont("Body", 9)
        c.setFillColor(MUTED)
        c.drawRightString(PAGE_W - MARGIN, top - 15.5, self.doc_type)
        self.title_p.drawOn(c, MARGIN, top - 50 - self.title_h)
        self.sub_p.drawOn(c, MARGIN, top - 58 - self.title_h - self.sub_h)
        c.setStrokeColor(INK)
        c.setLineWidth(0.9)
        y = top - self.head_h
        c.line(MARGIN, y, PAGE_W - MARGIN, y)
        self.footer(c)
        c.restoreState()

    def later_page(self, c, doc):
        c.saveState()
        c.setFillColor(YELLOW)
        c.rect(0, PAGE_H - 6, PAGE_W, 6, stroke=0, fill=1)
        top = PAGE_H - MARGIN + 6
        c.setFont("Body-Semi", 8.4)
        c.setFillColor(MUTED)
        c.drawString(MARGIN, top - 6, self.doc_title)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.5)
        c.line(MARGIN, top - 12, PAGE_W - MARGIN, top - 12)
        self.footer(c)
        c.restoreState()


def build(filename, title, doc_type, subtitle, short, story):
    global SNIPPETS

    # headings never sit alone at the bottom of a page: bind each to the block after it
    def leads(f):
        return isinstance(f, Paragraph) and f.style.name in HEAD_STYLES

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

    path = os.path.join(OUT, filename)
    Doc(path, title, doc_type, subtitle, short).build(fixed)
    if SNIPPETS:
        EXPORTED[filename] = SNIPPETS
    SNIPPETS = []
    print("wrote", os.path.relpath(path, ROOT))


def r(a, b, unit=""):
    """Number range with an en dash: r(5, 8) -> 5–8."""
    return f"{a}{DASH}{b}{unit}"


# =====================================================================
# 1. Arduino workshop series
# =====================================================================

def arduino():
    time_w = [0.85 * inch, 2.4 * inch, BODY_W - 3.25 * inch]
    parts_w = [2.9 * inch, 0.7 * inch, BODY_W - 3.6 * inch]
    st = [
        P(f"This is the Arduino course we run for middle schoolers, written up so your team can run it too. "
          f"Students work in pairs and build something different in each session. The sessions don't depend on "
          f"each other, so a student who only makes it to the second one can still finish the reaction game.", "lede"),
        P(f"It's meant for grades {r(5, 8)}. Each session takes {r(55, 70)} minutes, and group size is limited "
          f"mostly by how many helpers you have. Nobody needs Arduino experience, and that includes whoever is "
          f"teaching."),
        P("Most students have never used a breadboard. The first twenty minutes of session 1 will feel slow. "
          "By session 3 most pairs wire their circuits without asking for help."),
        h2("Who brings what"),
        P("<b>We send</b> parts for every pair (Arduino boards, breadboards, LEDs, buttons, buzzers, servos, and "
          "jumper wires, about $200 worth), the lesson plans in this packet, and a training call for whoever is "
          "teaching. A Spark Gears mentor is on call while you run each session."),
        P("<b>The host</b> provides a room with tables and outlets, recruits the students, and sends one or two "
          "adults or team members to the training call. Plan on an hour of setup before the first session."),
        P("<b>Students</b> bring a laptop. School Chromebooks work, and so do Windows and Mac laptops. Setup for "
          "each is below."),
        h2("What each session covers"),
        table([
            ["Session", "Students build", "New ideas"],
            ["1. Traffic light", "Three LEDs that cycle green, yellow, red", "Digital outputs, resistors, breadboard rows, delay()"],
            ["2. Reaction game", "A game that times how fast you press a button", "Reading a button, INPUT_PULLUP, random(), millis(), tone()"],
            ["3. Servo creature", "A cardboard creature with a moving part", "Servos, analog input, map()"],
        ], [1.25 * inch, 2.55 * inch, BODY_W - 3.8 * inch]),
        h2("Laptop setup, a few days before session 1"),
        P("Most first-day problems are laptop problems, not wiring problems. Test one laptop of every kind "
          "students will bring, and test it on the school's own network."),
        *numbered([
            "<b>Chromebooks.</b> Open <b>app.arduino.cc</b> in Chrome and sign in, or install the free Arduino "
            "Cloud for Chromebook app from Google Play. Nothing else needs to be installed. Plug in the board, "
            "click Detect Device, choose its port, and upload.",
            "<b>Windows and Mac.</b> Install Arduino IDE 2 from <b>arduino.cc/en/software</b>. The browser editor "
            "also works on these laptops, but it needs Arduino's Cloud Agent installed first.",
            "On every laptop, upload the Blink example (File, Examples, 01.Basics, Blink). If the small on-board "
            "LED starts blinking, that laptop is ready.",
            "Count parts into one bag per pair and label the bags. Cleanup goes much faster.",
            "If students are under 13, ask the school how it handles Arduino accounts. Some teachers sign in "
            "once and share one account across the room.",
        ]),
        P("<b>Chromebook boards.</b> Arduino only supports uploading from a Chromebook to some boards. The Uno R3 "
          "and Uno R4 are on the list, and they're what we send. Many inexpensive Uno clones won't upload from a "
          "Chromebook even though they work fine on a Windows laptop."),
        P("<b>Serial Monitor.</b> Some schools have found the Serial Monitor stays blank on their Chromebooks. "
          "Session 2 prints reaction times there. The buzzer still gives feedback without it, so the game works "
          "either way, but check it during your test."),
        tip("Tip from our first workshops",
            "Have one spare laptop already set up and tested. When a student's computer refuses to see the board, "
            "swap it in and keep them building instead of debugging drivers in front of the class."),
    ]

    # Session 1
    st += [
        PageBreak(),
        P(f"Session 1 · 55 minutes", "kicker"),
        h1("Traffic light"),
        P("Pairs wire a red, a yellow, and a green LED and program them to cycle like a stoplight. Plan for "
          "wiring to take most of the period. Once the first LED lights up, the other two usually take a few "
          "minutes. The code is short, so there's time to experiment with the timing at the end."),
        h3("Parts per pair"),
        table([
            ["Part", "Qty", "Notes"],
            ["Arduino Uno + USB cable", "1", "Make sure the cable carries data. Some only charge."],
            ["Half-size breadboard", "1", ""],
            ["LEDs (red, yellow, green)", "1 each", "The longer leg is positive"],
            ["220-ohm resistors", "3", "Bands are red, red, brown"],
            ["Male-to-male jumper wires", r(6, 8), "Extras for the challenge"],
        ], parts_w),
        h3("Timing"),
        table([
            ["Time", "What happens", "Notes for the teacher"],
            [r(0, 8, " min"), "Plug in, choose the board and port, upload Blink", "Walk the room. Every pair should see the on-board LED blink before moving on."],
            [r(8, 25, " min"), "Wire the three LEDs", "Show how breadboard rows connect. Each LED goes pin, resistor, long leg. The short leg goes to GND."],
            [r(25, 50, " min"), "Code the sequence and adjust the timing", "Start with green only, then add yellow and red. Let pairs choose their own timing."],
            [r(50, 55, " min"), "Show a few working lights, then clean up", "Parts back in the bag. Count the LEDs."],
        ], time_w),
        h3("Wiring"),
        table([
            ["LED", "Pin", "Path"],
            ["Red", "8", "Pin 8 to a 220-ohm resistor to the LED's long leg. Short leg to the GND rail."],
            ["Yellow", "9", "Pin 9 to a 220-ohm resistor to the LED's long leg. Short leg to the GND rail."],
            ["Green", "10", "Pin 10 to a 220-ohm resistor to the LED's long leg. Short leg to the GND rail."],
            ["GND rail", "GND", "One wire from any GND pin to the blue rail on the breadboard."],
        ], [0.9 * inch, 0.6 * inch, BODY_W - 1.5 * inch]),
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
""", "Starter code", "Session 1, traffic light"),
        h3("If it doesn't work"),
        *bullets([
            "<b>An LED stays dark.</b> It's probably in backwards. Turn it around so the long leg faces the resistor.",
            "<b>Upload fails.</b> Check the port, then try a different USB cable. Charge-only cables are common.",
            "<b>Two LEDs light at once.</b> A wire or resistor is sharing a breadboard row with the wrong LED.",
        ]),
        h3("For pairs who finish early"),
        *bullets([
            "Add a second set of LEDs for the cross street. When one direction is green, the other has to be red.",
            "Add a white walk light that only comes on while both directions are red.",
            "Make the yellow light blink three times before it turns red.",
        ]),
    ]

    # Session 2
    st += [
        PageBreak(),
        P("Session 2 · 55 minutes", "kicker"),
        h1("Reaction-time game"),
        P("The LED comes on after a random wait and you hit the button as fast as you can. The Arduino times the "
          "press and plays a high beep if you were quick, a low one if you weren't. Reading a button is the new "
          "skill this week. Leave time at the end, because most pairs keep playing once it works."),
        h3("Parts per pair"),
        table([
            ["Part", "Qty", "Notes"],
            ["Arduino Uno + USB cable", "1", ""],
            ["Half-size breadboard", "1", ""],
            ["LED and 220-ohm resistor", "1 each", "Any color"],
            ["Four-leg tactile button", "1", "No resistor needed, see below"],
            ["Passive piezo buzzer", "1", "Passive buzzers can play different pitches"],
            ["Jumper wires", "6", ""],
        ], parts_w),
        h3("Timing"),
        table([
            ["Time", "What happens", "Notes for the teacher"],
            [r(0, 8, " min"), "Plug in and upload Blink as a test", "New students may need help finding the port."],
            [r(8, 18, " min"), "Wire the LED to pin 9", "Pin 9, resistor, long leg. Short leg to GND."],
            [r(18, 30, " min"), "Wire the button to pin 2 and GND", "The button straddles the center gap. One leg to pin 2, the diagonal leg to GND."],
            [r(30, 50, " min"), "Write the game and test it", "Open the Serial Monitor at 9600 baud to see the times."],
            [r(50, 55, " min"), "Class tournament, then clean up", "Fastest reaction in the room wins bragging rights."],
        ], time_w),
        P("<b>Why the button has no resistor.</b> INPUT_PULLUP switches on a resistor inside the Arduino. The pin "
          "reads HIGH until the button is pressed, then reads LOW. Students find this backwards at first. Say it "
          "out loud a couple of times. Pressed means LOW."),
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
""", "Starter code", "Session 2, reaction-time game"),
        h3("If it doesn't work"),
        *bullets([
            "<b>The game ends instantly with a time of 0.</b> The button is turned the wrong way, so it always "
            "reads as pressed. Rotate it 90 degrees.",
            "<b>No sound.</b> Check that the buzzer's + leg goes to pin 8. An active buzzer plays only one pitch, "
            "which is fine for this.",
            "<b>The Serial Monitor shows garbage.</b> Set the baud rate to 9600.",
        ]),
        h3("Changes to try"),
        *bullets([
            "Play three rounds and print the average.",
            "Add a false-start penalty. If the button is already down when the LED comes on, buzz and restart.",
            "Shrink the 300 ms target a little every round.",
            "Two-player mode with a second button on pin 3. First press wins.",
        ]),
    ]

    # Session 3
    st += [
        PageBreak(),
        P("Session 3 · 70 minutes", "kicker"),
        h1("Servo creature"),
        P("Half of this session is cardboard and tape. Each pair builds a creature around a micro servo and then "
          "decides how it should move, using either a button that steps through poses or a knob for smooth "
          "control. It runs longer than the other two because the building takes a while, and nobody wants to "
          "stop."),
        h3("Parts per pair"),
        table([
            ["Part", "Qty", "Notes"],
            ["Arduino Uno + USB cable", "1", ""],
            ["Half-size breadboard", "1", ""],
            ["SG90 micro servo with horns", "1", "Brown is GND, red is 5V, orange is signal"],
            ["Button or 10k potentiometer", "1", "Each pair picks one"],
            ["Jumper wires", "6", ""],
            ["Cardboard, foam, tape, markers", "Shared", "Set up a craft table"],
        ], parts_w),
        h3("Timing"),
        table([
            ["Time", "What happens", "Notes for the teacher"],
            [r(0, 10, " min"), "Upload the Sweep example (File, Examples, Servo, Sweep)", "This proves the servo works before anyone writes code."],
            [r(10, 25, " min"), "Wire the SG90", "Brown to GND, red to 5V, orange to pin 9."],
            [r(25, 35, " min"), "Pick a control and wire it", "Button to pin 2 and GND. For the knob, middle leg to A0 and the outer legs to 5V and GND."],
            [r(35, 50, " min"), "Code the movement", "The button steps through poses. The knob sets the angle directly."],
            [r(50, 70, " min"), "Build the creature and tune it", "Tape the servo horn to a jaw or a wing. Adjust angles until it looks alive."],
        ], time_w),
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
""", "Starter code, button version", "Session 3, servo creature (button)"),
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
""", "Starter code, knob version", "Session 3, servo creature (knob)"),
        h3("If it doesn't work"),
        *bullets([
            "<b>The servo twitches or the Arduino keeps resetting.</b> The servo is drawing too much power. Make "
            "sure nothing is jamming the horn, and run only one servo from a laptop's USB port.",
            "<b>The servo buzzes at the end of its swing.</b> It's being pushed past its limit. Keep angles "
            "between about 10 and 170.",
            "<b>The knob only works for part of its turn.</b> An outer leg isn't connected, or the outer legs "
            "are swapped.",
        ]),
        h3("Creature ideas"),
        *bullets([
            "A crocodile whose jaw snaps shut on every button press.",
            "A bird that flaps faster as the knob turns. Change the delay, not the angle.",
        ]),
        h2("Logistics and safety"),
        table([
            ["Grades", f"{r(5, 8)}. Younger students can do sessions 1 and 3 with more adult help."],
            ["Group size", "As many pairs as you have helpers for. One helper for every five or six pairs works for us."],
            ["Length", f"{r(55, 70)} minutes each. Run them on three days in a row or once a week."],
            ["Safety", "Everything runs on 5 volts from USB. There's no soldering and no power tools. Remind "
                       "students not to bend LED legs back and forth, because they snap."],
            ["Cleanup", "Every part goes back in its labeled bag. Count the LEDs and servos before students leave."],
        ], [1.1 * inch, BODY_W - 1.1 * inch], header=False),
        closing(),
    ]
    build("spark-gears-arduino-workshop-series.pdf", "Arduino Workshop Series", "Lesson plans",
          f"Lesson plans for a three-session Arduino course, grades {r(5, 8)}.", "Arduino Workshop Series", st)


# =====================================================================
# 2. FTC intro camp
# =====================================================================

def ftc_camp():
    day_w = [0.95 * inch, 2.45 * inch, BODY_W - 3.4 * inch]
    st = [
        P(f"The camp is for rising {r('6th', '9th')} graders. Campers split into one or two mini teams, "
          f"and each team builds and programs its own robot with help from the students on your FTC team. "
          f"Nobody needs to have built or coded anything before.", "lede"),
        P("Each day starts with a short lesson on one topic. After that, teams spend most of the block working on "
          "their robot while your mentors move between tables. On the last day teams play timed matches on a "
          "practice field, and families come in for a short showcase."),
        P("A camp is more work for the host team than a one-day event. It's also the outreach most likely to "
          "turn into new members, since campers leave having done the actual work of an FTC team for a week."),
        P(f"Plan on about 3 hours a day. One robot can handle {r(5, 8)} campers. With two robots you can take up "
          f"to 16."),
        h2("Who brings what"),
        P("<b>We send</b> daily lesson plans, the starter code and build notes, a score sheet for game day, and "
          "printed posters, stickers, and name tags. We also train your mentors before camp, and a Spark Gears "
          "mentor is on call all week."),
        P("<b>The host team</b> provides the room, recruits campers, and staffs every day with its own members. "
          "You'll also need one FTC robot kit per mini team. A robot from a past season works fine. If you don't "
          "have one, tell us when you request support and we'll help you find one or scale the camp down."),
        P("<b>Campers</b> bring a laptop, closed-toe shoes, and their own snack and water."),
        h2("A typical day"),
        table([
            ["Block", "Time", "What happens"],
            ["Warm-up", "15 min", "A quick challenge or question, attendance, safety glasses on"],
            ["Lesson", r(20, 30, " min"), "One new topic, taught with a demo on a real robot"],
            ["Team work", r(75, 90, " min"), "Teams build, wire, or code. Mentors rotate between them."],
            ["Break", "15 min", "Snack and water, away from the tables"],
            ["Team work", r(30, 45, " min"), "Keep going, test, and fix what broke"],
            ["Stand-up", "10 min", "Each team says what got done, what's stuck, and tomorrow's plan"],
        ], [1.1 * inch, 1.05 * inch, BODY_W - 2.15 * inch]),
        h2("Day by day"),
        h3("Day 1. Meet the challenge"),
        table([
            ["Block", "Activity", "Notes for mentors"],
            ["Morning", "Introductions, camp rules, and safety glasses. Watch the current FTC game reveal video together.",
             "Keep the video to about 5 minutes. Pause it to explain scoring."],
            ["Midday", "Split into mini teams. Each team picks a name and number and draws a logo.",
             "Branding gets quiet campers talking. Have markers and poster paper out."],
            ["Afternoon", "Tour a real FTC robot. Campers find the Control Hub, motors, servos, and battery.",
             "Let them hold parts and drive it with a gamepad for a few minutes."],
            ["Wrap-up", "Each team picks one game task to focus on for the week.",
             "Small goals get finished. One task done well beats three half done."],
        ], day_w),
        h3("Day 2. Design and start building"),
        table([
            ["Block", "Activity", "Notes for mentors"],
            ["Lesson", "How drivetrains work, reading a build guide, and using hex keys safely.", "Put a finished drivetrain next to a pile of its parts."],
            ["Team work", "Sketch the robot on paper and decide who builds the drivetrain and who builds the mechanism.", "Every camper gets a job. Rotate jobs each day."],
            ["Build", "Start the drivetrain, with the frame, motors, and wheels.", "Check that the motors are mounted the same way on both sides."],
        ], day_w),
        h3("Day 3. Keep building"),
        table([
            ["Block", "Activity", "Notes for mentors"],
            ["Lesson", "Wiring the Control Hub and keeping cables tidy.", "Show a messy wiring job next to a clean one."],
            ["Build", "Finish and wire the drivetrain, then start the scoring mechanism.", "Loose wires cause most robot failures. Zip-tie as you go."],
            ["Test", "First drive with the sample code.", "Tape a square on the floor and have drivers park inside it."],
        ], day_w),
        h3("Day 4. Program the robot"),
        table([
            ["Block", "Activity", "Notes for mentors"],
            ["Lesson", "OnBot Java basics. What an OpMode is and how gamepad input sets motor power.", "OnBot Java runs in a browser connected to the Control Hub, so there's nothing to install."],
            ["Code", "Write a TeleOp from the starter code, then map the mechanism to buttons.", "Let campers change numbers and see what happens."],
            ["Stretch", "A 5-second autonomous routine that drives forward and parks.", "Timing-based is fine. Encoders are a bonus."],
        ], day_w),
        h3("Day 5. Game day and showcase"),
        table([
            ["Block", "Activity", "Notes for mentors"],
            ["Morning", "Last fixes and driver practice.", "Freeze the code an hour before the matches."],
            ["Matches", "Each team plays timed matches on the practice field and records its scores.", "Use the score sheet. Cheer loudly."],
            ["Showcase", "Families come in. Each team presents its robot and what it learned.", f"{r(2, 3)} minutes per team. Every camper says one thing."],
        ], day_w),
        h2("Starter TeleOp code"),
        P("Paste this into OnBot Java. In the robot configuration, name the drive motors <b>left</b> and "
          "<b>right</b>. Campers add their mechanism controls inside the loop.", "intro"),
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
""", "CampDrive.java", "CampDrive.java (TeleOp)"),
        h2("Team roles"),
        P("Campers rotate roles each day so everyone gets time building, coding, and driving."),
        table([
            ["Role", "What they do"],
            ["Builder", "Assembles and repairs the robot and keeps track of parts"],
            ["Programmer", "Writes and tests code and tunes the controls with the driver"],
            ["Driver", "Practices driving and reports what's hard to control"],
            ["Captain", "Keeps the team on schedule and leads the stand-up"],
            ["Brand lead", "Logo, poster, photos, and the showcase talk"],
        ], [1.3 * inch, BODY_W - 1.3 * inch]),
        h2("Logistics and safety"),
        table([
            ["Grades", f"Rising {r('6th', '9th')} graders. A strong 5th grader can join with a parent's okay."],
            ["Group size", f"{r(5, 8)} campers per robot. Two robots means two teams of up to 8."],
            ["Daily length", "About 3 hours. Mornings work best in summer."],
            ["Mentors", "At least one experienced mentor per team, plus an adult on site the whole time."],
            ["Safety", "Everyone wears safety glasses while a robot is powered or being built. Closed-toe shoes only. "
                       "Disable the robot before anyone reaches into it. Unplug batteries when they're not in use, "
                       "and never leave one charging unattended."],
            ["Families", "Invite them to the day 5 showcase. It's the best photo opportunity of the week."],
        ], [1.1 * inch, BODY_W - 1.1 * inch], header=False),
        closing(),
    ]
    build("spark-gears-ftc-intro-camp.pdf", "FTC Intro Robotics Camp", "Camp plan",
          "A five-day plan for a middle school robotics camp run by an FTC team.", "FTC Intro Robotics Camp", st)


# =====================================================================
# 3. Robotics and automation course
# =====================================================================

def robotics_course():
    wk_w = [0.85 * inch, BODY_W - 0.85 * inch]

    def week(label, title, topics, lab, outcome, prep):
        head = Paragraph(f"<b>{label}.</b> {title}", ParagraphStyle("wk", parent=S["cell"], fontSize=9.8))
        rows = [[head, ""]] + [[Paragraph(k, S["th"]), Paragraph(v, S["cell"])] for k, v in
                               [("Topics", topics), ("Lab", lab), ("Goal", outcome), ("Prep", prep)]]
        t = Table(rows, colWidths=wk_w)
        t.setStyle(TableStyle([
            ("SPAN", (0, 0), (-1, 0)),
            ("LINEBELOW", (0, 0), (-1, 0), 0.9, INK),
            ("LINEBELOW", (0, 1), (-1, -1), 0.5, RULE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        return KeepTogether([t, Spacer(1, 12)])

    st = [
        P(f"The class meets once a week for {r(2, 2.5)} hours. Each one "
          f"opens with a short demo and then turns into lab time. Weeks {r(1, 5)} introduce one part at a time. "
          f"In weeks {r(6, 9)} students build a robot that finds its own way through a maze, and they take the "
          f"kit home when the course ends.", "lede"),
        P("It suits an after-school club or a library program that wants something longer than a one-day event. "
          "Students don't need any technical background."),
        h2("The nine weeks"),
        table([
            ["Week", "Topic", "Skills"],
            ["1", "Arduino basics and LEDs", "Circuits, setting up the editor"],
            ["2", "Inputs and breadboards", "Digital and analog signals, wiring"],
            ["3", "Sensors", "Reading inputs, if statements"],
            ["4", "Servos", "Motor control, PWM"],
            ["5", "Combined project", "Using inputs and outputs together"],
            ["6", "Robot chassis", "Mounting and safe wiring"],
            ["7", "Bumpers", "Prototyping, first drive tests"],
            ["8", "Navigation code", "Autonomous programming"],
            ["9", "Showcase", "Testing, debugging, presenting"],
        ], [0.6 * inch, 2.3 * inch, BODY_W - 2.9 * inch]),
        h2("How a class runs"),
        table([
            ["Part", "Time", "What happens"],
            ["Demo", r(20, 30, " min"), "A short talk and a live demo of the week's new part"],
            ["Lab", r(60, 75, " min"), "Students build and code while instructors circulate"],
            ["Break", "15 min", "Snack, away from the benches"],
            ["Project time", r(30, 45, " min"), "Troubleshoot, improve, and save working code"],
        ], [1.3 * inch, 1.05 * inch, BODY_W - 2.35 * inch]),
        h2("Week by week"),
        week("Week 1", "Arduino basics",
             "Lab safety, the course plan, the Arduino board and its pins, what's in the kit, setting up the editor.",
             "Practice on the breadboard, light an LED, and upload and change the Blink example.",
             "Every student programs a working circuit.",
             "Test every kind of laptop ahead of time. Bag the kits so each student gets one."),
        week("Week 2", "Digital and analog inputs",
             "Digital versus analog signals, series and parallel circuits, reading resistor bands.",
             "Read a push button. Read a potentiometer and print its values to the Serial Monitor.",
             "Change Blink so it reacts to a button, then make an LED that dims with a knob.",
             "Bring a multimeter to show the voltage changing as the knob turns."),
        week("Week 3", "Sensors and if statements",
             "What sensors measure, and using if statements to react to readings.",
             "Test limit switches and a color sensor. Print the readings and pick thresholds.",
             "An LED or buzzer turns on when a sensor changes state.",
             "Bring a few colored cards so color readings are consistent."),
        week("Week 4", "Servos",
             "How servos work, pulse width modulation, and the difference between positional and continuous servos.",
             "Control a servo's position with a button or a potentiometer.",
             "Each student has a working moving part.",
             "Show both servo types side by side now. Students mix them up later if they don't see the difference early."),
        week("Week 5", "Putting inputs and outputs together",
             "Sensors and motors in the same program, and a step-by-step way to troubleshoot.",
             "Build a security gate. A servo arm lifts when a sensor is triggered, and a buzzer sounds.",
             "Students demo the gate and explain how they found their bugs.",
             "This is the halfway point. Check in with anyone who's behind before the robot build starts."),
        week(f"Weeks {r(6, 7)}", "Planning and building the robot",
             "How maze solving works, bumper logic, and planning a build in steps.",
             "Assemble the chassis, mount the Arduino and battery, and wire everything safely.",
             "The robot drives with simple code and both bumpers register a hit.",
             "Have the practice maze set up by the end of week 6 so students can test against real walls."),
        week(f"Weeks {r(8, 9)}", "Navigation and the showcase",
             "Autonomous navigation, loops, tuning turn times, and cleaning up code.",
             "Tune the robot, run timed maze trials, then hold the showcase in week 9.",
             "A finished maze-solving robot. Every kit goes home with its builder.",
             "Invite families to week 9 and print certificates ahead of time."),
        h2("The maze robot"),
        P("Two continuous-rotation servos drive the robot, and two limit switches on the front act as bumpers. "
          "When a bumper hits a wall, the robot backs up and turns away. It's a crude strategy, but it gets "
          "through most beginner mazes, and there's plenty of room to improve on it.", "intro"),
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
""", "Starter code for the maze robot", "Bump-and-turn maze robot"),
        P("Turn times depend on the battery, the floor, and the wheels. Have students time a 90-degree turn on "
          "their own robot and replace the 350 with that number.", "small"),
        h3("Suggested grading"),
        table([
            ["Area", "Points", "Full points"],
            ["Maze run", "40", "The robot reaches the end in at least one of three tries"],
            ["Code", "30", "Readable, commented, and behaves the same way every run"],
            ["Build log", "20", "Notes on what they tried, what broke, and how they fixed it"],
            ["Showcase", "10", "Can explain how the robot decides what to do"],
        ], [1.2 * inch, 0.7 * inch, BODY_W - 1.9 * inch]),
        h2("Materials"),
        P("<b>Each student kit</b> has an Arduino Uno or compatible board (not a Mega), a breadboard and jumper "
          "wires, resistors and LEDs, one positional servo, two continuous-rotation servos, two limit switches, a "
          "color sensor, a robot chassis with wheels, and a USB cable."),
        P("<b>Instructors</b> need maze walls (cardboard or foam board works), tape, zip ties, spare parts, a few "
          "charged battery packs, and a projector for demos."),
        P("<b>Students</b> bring a laptop with Google Chrome. School Chromebooks are fine if the board is a "
          "genuine Uno R3 or R4, since many clones won't upload from ChromeOS. They should also bring a snack "
          "and water."),
        h2("Staffing and tips"),
        P("Plan on a lead instructor plus one assistant for every 10 students. Three or four members of an FTC "
          "team can cover that by taking turns."),
        *bullets([
            "Have students check their wiring and code after every change. Small steps make bugs easy to find.",
            "Save a copy of working code with the week in the name (maze_week8_v2) before changing anything.",
            "Pass new parts around and put a close-up on the projector before anyone wires them.",
            "Pair a confident student with one who's newer. Both learn more.",
            "Keep a bin of spare parts. Something breaks every week, and a spare servo can save a lesson.",
        ]),
        h3("For students who finish early"),
        *bullets([
            "Swap the bumpers for an IR sensor and follow a line instead.",
            "Wall following. Keep one bumper lightly touching the wall and trace the maze.",
            "Add an ultrasonic sensor so the robot turns before it hits anything.",
        ]),
        closing(),
    ]
    build("spark-gears-robotics-automation-course.pdf", "Robotics and Automation Course", "Syllabus",
          f"A nine-week syllabus for grades {r(6, 9)}, ending with a maze-solving robot.",
          "Robotics and Automation Course", st)


# =====================================================================
# 4. Outreach event roadmap
# =====================================================================

def roadmap():
    st = [
        P("These are the steps our mentors walk teams through before a first outreach event. You can follow "
          "them without a Spark Gears kit. Most teams start about two months out, but a school demo can be "
          "pulled together in a few weeks.", "lede"),
    ]
    steps = [
        ("1", "Pick your event", f"{r(6, 8)} weeks out", [
            "Choose a format from the table at the end. A library station or a school demo is the easiest first event.",
            "Find a host. Public libraries, a teacher at a nearby school, community centers, and scout troops all "
            "work. Ask early, because libraries book months ahead.",
            "Agree on a date, a time, a room, and about how many kids to expect.",
        ]),
        ("2", "Plan it with a mentor", f"{r(4, 6)} weeks out", [
            f"Request support at {SITE}/for-teams.html. We'll assign a Spark Gears mentor to your team.",
            "Meet with your mentor to choose activities, set a timeline, and split up jobs.",
            "Make a flyer. Send it to your host and post it on your team's accounts.",
            "Fill in the run-of-show template so everyone knows their job on the day.",
        ]),
        ("3", "Get the kit", f"{r(2, 3)} weeks out", [
            "Request a supply kit. Rookie teams and Title I schools get priority.",
            "Open it the day it arrives and check it against the list. Test every electronic part.",
            "Print activity sheets, a sign-in sheet, and the volunteer hour log.",
            "Do a full practice run with your team and time each activity.",
        ]),
        ("4", "Run it", "Event day", [
            "Get there at least an hour early to set up and test robots.",
            "Your mentor is on call the whole time. If you're in the DC, Maryland, or Virginia area, they may come in person.",
            "Give one person the camera (ask before photographing kids) and another the attendance count.",
            "Have every volunteer sign in and out on the hour log.",
        ]),
        ("5", "Log the impact", "Within a week", [
            "Send us the signed hour log and we'll verify the hours.",
            "Write down attendance, ages, volunteers, and hours while you still remember them.",
            "Thank your host and ask about coming back next season.",
            "Add the event to your engineering portfolio with a photo and a few sentences.",
        ]),
    ]
    for num, title, when, items in steps:
        st += [P(f"{num}. {title} <font name='Body' color='#5f594b' size='10'>&nbsp;&nbsp;{when}</font>", "h2"),
               checklist(items)]

    st += [
        h2("Choosing a format"),
        table([
            ["Format", "Length", "Audience", "As a first event"],
            ["Library STEM station", r(2, 4, " hours"), "Drop-in, families", "Good. Low pressure and flexible."],
            ["School robotics demo", "About an hour", "A class or an assembly", "Good. Short and easy to schedule."],
            ["Arduino workshop", f"{r(1, 3)} sessions", f"Grades {r(5, 8)}, in pairs", "Good, using our lesson plans."],
            ["Intro robotics camp", "5 days", f"Grades {r(6, 9)}, mini teams", "Better as a second or third event."],
        ], [1.65 * inch, 1.05 * inch, 1.75 * inch, BODY_W - 4.45 * inch]),
        h2("What to write down for your portfolio"),
        table([
            ["Number", "How to get it"],
            ["Attendance", "A sign-in sheet, or a tally counter at the door"],
            ["Ages", "Ask the host, or add a grade column to the sign-in sheet"],
            ["Volunteer hours", "The volunteer hour log"],
            ["Follow-ups", "Kids or parents who asked about joining a team or a camp"],
            ["Photos", "Wide shots of the room and close-ups of hands on robots. Get permission before showing faces."],
        ], [1.5 * inch, BODY_W - 1.5 * inch]),
        closing(),
    ]
    build("spark-gears-outreach-roadmap.pdf", "Outreach Event Roadmap", "Planning guide",
          "How to plan a first outreach event, from finding a host to logging volunteer hours.",
          "Outreach Event Roadmap", st)


# =====================================================================
# 5. Run-of-show template
# =====================================================================

def field_row(labels, widths):
    cells = [[P(label, "th"), Spacer(1, 16)] for label in labels]
    t = Table([cells], colWidths=widths)
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, INK), ("INNERGRID", (0, 0), (-1, -1), 0.6, INK),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("LEFTPADDING", (0, 0), (-1, -1), 7)]))
    return t


def run_of_show():
    q = BODY_W / 4
    st = [
        P("The sample times assume a two-hour event starting at 10:00. Cross them out and write in your own."),
        field_row(["Event name", "Date"], [q * 3, q]),
        field_row(["Location and room", "Start time", "End time"], [q * 2, q, q]),
        field_row(["Host contact (name and phone)", "Spark Gears mentor (name and phone)"], [q * 2, q * 2]),
        h2("Roles"),
        table([
            ["Role", "Name", "Job"],
            ["Event lead", "", "Runs the timeline and talks to the host"],
            ["Station leads", "", "One per station. Runs the activity and keeps the line moving."],
            ["Greeter", "", "Welcomes families, runs sign-in, points people to stations"],
            ["Photographer", "", "Takes photos and video. Asks before photographing faces."],
            ["Floater", "", "Fixes robots, refills supplies, covers breaks"],
        ], [1.25 * inch, 1.9 * inch, BODY_W - 3.15 * inch], valign="MIDDLE", pad=7),
        h2("Timeline"),
        table([
            ["Time", "What happens", "Who"],
            ["8:45", "Team arrives and unloads.", ""],
            ["9:00", "Set up tables and stations. Charge and test every robot.", ""],
            ["9:40", "Each station lead runs their activity once for the team.", ""],
            ["9:50", "Huddle. Confirm roles and breaks.", ""],
            ["10:00", "Doors open and sign-in starts.", ""],
            ["10:05", "Two-minute welcome. Who we are and what FIRST is.", ""],
            ["10:10", "Stations open.", ""],
            ["11:00", "Robot demo or driving challenge for everyone.", ""],
            ["11:15", "Stations reopen.", ""],
            ["11:50", "Wrap up. Hand out flyers about joining a team.", ""],
            ["12:00", "Event ends and teardown starts.", ""],
            ["12:30", "Team debrief.", ""],
        ], [0.75 * inch, BODY_W - 2.15 * inch, 1.4 * inch], valign="MIDDLE", pad=6),
        h2("Stations"),
        table([
            ["Station", "Activity", "Supplies", "Lead"],
            ["1", "", "", ""], ["2", "", "", ""], ["3", "", "", ""], ["4", "", "", ""],
        ], [0.7 * inch, 2.4 * inch, 2.4 * inch, BODY_W - 5.5 * inch], valign="MIDDLE", pad=16),
        h2("Packing list"),
        two_col_checklist([
            ("Robots, controllers, and charged batteries", "Battery charger and power strip"),
            ("Supply kit and spare parts", "Laptops and chargers"),
            ("Printed activity sheets", "Sign-in sheet and hour log"),
            ("Team banner, flyers, and stickers", "Tape, zip ties, scissors, markers"),
            ("Safety glasses", "First aid kit and water"),
        ]),
        h2("Teardown"),
        two_col_checklist([
            ("Count robots, batteries, and controllers", "Pack the kit and count small parts"),
            ("Unplug and pack all chargers", "Pick up trash and wipe tables"),
            ("Put the room back the way you found it", "Collect the sign-in sheet and hour log"),
            ("Thank the host in person", "Take a team photo"),
        ]),
        h2("If something goes wrong"),
        table([
            ["Problem", "Plan"],
            ["A robot breaks", "Switch that station to its backup activity. The floater fixes the robot off to the side."],
            ["Far more kids than expected", "Shorten turns, combine two stations, or run a group demo for kids who are waiting."],
            ["Nobody shows up for 20 minutes", "Send two people with a robot to the lobby or library entrance."],
            ["Someone gets hurt", "Stop the activity and get the host. Use the first aid kit, and call 911 if it's serious."],
        ], [1.9 * inch, BODY_W - 1.9 * inch]),
        h2("Debrief notes"),
        write_lines(5),
    ]
    build("spark-gears-run-of-show.pdf", "Event Run-of-Show", "Template",
          "Fill this in with your team the week before the event, then bring printed copies.",
          "Event Run-of-Show", st)


# =====================================================================
# 6. Volunteer hour log
# =====================================================================

def hour_log():
    q = BODY_W / 4
    st = [
        P("Volunteers sign in when they arrive and out when they leave, including setup and teardown. After the "
          f"event, have your host or Spark Gears mentor sign the bottom, then email a photo of the sheet to "
          f"<b>{EMAIL}</b>. We'll verify the hours within a week."),
        field_row(["Team name and number", "Event date"], [q * 3, q]),
        field_row(["Event name and location", "Event type"], [q * 3, q]),
        Spacer(1, 14),
    ]
    rows = [["#", "Volunteer name", "Role", "Time in", "Time out", "Hours", "Initials"]]
    rows += [[str(i), "", "", "", "", "", ""] for i in range(1, 13)]
    rows.append(["", "", "", "", P("<b>Total</b>", "cell"), "", ""])
    w = [0.35 * inch, 2.15 * inch, 1.25 * inch, 0.8 * inch, 0.8 * inch, 0.7 * inch]
    w.append(BODY_W - sum(w))
    data = [[Paragraph(c, S["th"]) for c in rows[0]]] + rows[1:]
    t = Table(data, colWidths=w, rowHeights=[None] + [22] * (len(rows) - 1))
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, INK), ("INNERGRID", (0, 0), (-1, -1), 0.5, RULE),
                           ("LINEBELOW", (0, 0), (-1, 0), 0.8, INK), ("LINEABOVE", (0, -1), (-1, -1), 0.8, INK),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 6)]))
    st += [t, Spacer(1, 14)]
    sign = Table([[
        [P("Verified by (host or mentor)", "th"), Spacer(1, 26)],
        [P("Signature", "th"), Spacer(1, 26)],
        [P("Date", "th"), Spacer(1, 26)],
    ]], colWidths=[q * 1.6, q * 1.6, q * 0.8])
    sign.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.8, INK), ("INNERGRID", (0, 0), (-1, -1), 0.6, INK),
                              ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 7),
                              ("TOPPADDING", (0, 0), (-1, -1), 5)]))
    st += [sign, Spacer(1, 8),
           P("Round to the nearest quarter hour. If someone forgot to sign out, use the event's end time and "
             "note it in the Initials column.", "small")]
    build("spark-gears-volunteer-hour-log.pdf", "Volunteer Hour Log", "Form",
          "A sign-in sheet for volunteer hours at your event.", "Volunteer Hour Log", st)


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
    with open(os.path.join(OUT, "code-snippets.json"), "w") as f:
        json.dump(EXPORTED, f, indent=1)
    print("wrote downloads/code-snippets.json")
