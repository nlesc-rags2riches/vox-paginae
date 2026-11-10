"""Write `<dir>/1-1001/`: a fake single deed folder to try the single-deed notebook on.

Its scans look like a 1921 Drenthe deed on microfilm (two pages side by side), with
invented content. The same every run. Refuses to run if the folder exists.

Usage: uv run python scripts/fake_deed.py <dir>
"""

import json
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

FONTS = Path(__file__).resolve().parent / "fonts"
HAND_FONT = FONTS / "msmadi" / "MsMadi-Regular.ttf"
# The other hand picked for fake deeds; unused until a deed is written in a second hand.
OTHER_HAND_FONT = FONTS / "cedarvillecursive" / "Cedarville-Cursive.ttf"
PRINT_FONT = FONTS / "oldstandardtt" / "OldStandard-Regular.ttf"
PRINT_BOLD_FONT = FONTS / "oldstandardtt" / "OldStandard-Bold.ttf"

SEED = 1921
SCAN_W, SCAN_H = 2000, 1540
FILM_TOP, FILM_SIDE, GUTTER = 70, 60, 20  # black film around and between the pages
PAGE_W = (SCAN_W - 2 * FILM_SIDE - GUTTER) // 2
PAGE_H = SCAN_H - 2 * FILM_TOP
MARGIN = 70
HAND_SIZE, LINE_H = 34, 44
BIG_HAND_SIZE = 46  # the form's header, the balance and the memorie's side note
LABEL_SIZE = 18  # the form's printed questions
# The form's columns: question number, question, answer.
NUMBER_X, QUESTION_X, ANSWER_X = MARGIN, MARGIN + 60, int(PAGE_W * 0.6)
SIDE_RULE_X = MARGIN + 230  # the memorie page's left margin, for the side note
AMOUNT_W = 120  # the amount column beside a memorie item

# Amounts are Decimal, so totals add up to the cent.
ASSETS = [
    {
        "amount": Decimal("4812.50"),
        "description": "Een woonhuis met schuur en erf, staande en gelegen te "
        "Oostdorp aan den Brink, kadastraal bekend gemeente Oostdorp sectie A "
        "nummer 214, groot achttien aren veertig centiaren",
    },
    {
        "amount": Decimal("1250.75"),
        "description": "Een perceel bouwland, gelegen onder Oostdorp in de "
        "Noordesch, kadastraal bekend sectie B nummer 87",
    },
]
LIABILITIES = [{"amount": Decimal("145.35"), "description": "Kosten der begrafenis"}]
ASSETS_TOTAL = sum(item["amount"] for item in ASSETS)
LIABILITIES_TOTAL = sum(item["amount"] for item in LIABILITIES)

# Shaped like the `metadata` of `input.json`, plus `declarants`, which is only drawn.
DEED = {
    "aktenummer": None,
    "ref_reg": "1#1001",
    "tax_office": "Westdorp",
    "deceased": {
        "full_name": "Jan Modaal",
        "profession": "landbouwer",
        "date_of_death": "14 maart 1921",
        "place_of_residence": "Oostdorp",
        "place_of_death": "Oostdorp",
    },
    "declarants": [
        "Grietje Bos, weduwe van den overledene, zonder beroep",
        "Hendrik Modaal, landbouwer, zoon van den overledene",
    ],
    "assets": {"total": ASSETS_TOTAL, "items": ASSETS},
    "liabilities": {"total": LIABILITIES_TOTAL, "items": LIABILITIES},
    "total": ASSETS_TOTAL - LIABILITIES_TOTAL,
}

# One (left, right) pair of page kinds per scan.
LAYOUT = [
    ("previous_deed_end", "cover"),
    ("cover_back", "memorie"),
]

# (number, printed question, handwritten answer). The answers are invented filler.
PREVIOUS_DEED_ROWS = [
    (30, "Aanwijzing van de boeking der verschuldigde rechten en boeten", None),
    (31, "Aanwijzing van de posten tot nader onderzoek", None),
    (32, "Dagteekening waarop het bevel der rechtbank is beteekend", None),
    (33, "Aanwijzing der beschikkingen, waarbij de termijn is verlengd", None),
    (34, "Dagteekening waarop de eed moet worden afgelegd", "9 februari 1921"),
    (35, "Dagteekening waarop de eed is afgelegd", "9 februari 1921"),
]
COVER_ROWS = [
    (
        1,
        "Aanwijzing der beschikkingen, waarbij de termijn tot aangifte is verlengd",
        None,
    ),
    (2, "Dagteekening waarop de aangifte moet worden ingeleverd", None),
    (3, "Dagteekening van de inlevering der memorie van aangifte", "2 april 1921"),
    (4, "Aanwijzing van het dagregister", "D. 3  bl. 12  nº. 417"),
    (5, "Dagteekening van de inlevering der nadere memoriën", None),
    (6, "Aanwijzing van het dagregister wat de nadere memoriën betreft", None),
    (7, "Aanwijzing van de tafel der sterfgevallen", "D. 8  bl. 51  nº. 96"),
    (8, "Aanwijzing van de tafel der testamenten", None),
    (9, "Aanwijzing der boeking van het sterfgeval op het memoriaal nº. 14", None),
    (10, "Aanwijzing der boeking van het sterfgeval op het memoriaal nº. 15", None),
]
COVER_BACK_ROWS = [
    (12, "Waarde der onroerende zaken, onderworpen aan het recht van overgang", None),
    (13, "Zuiver bedrag bij schenking verkregen", None),
    (14, "Boeking der schenking op het memoriaal nº. 15", None),
    (15, "Aanwijzing der beschikkingen, waarbij de termijn is verlengd", None),
    (16, "Dagteekening waarop de eed moet worden afgelegd", "20 april 1921"),
    (17, "Dagteekening waarop de eed is afgelegd", "20 april 1921"),
    (18, "Aanwijzing van de boeking der verzuimde eedsaflegging", None),
    (19, "Dagteekening der machtiging voor het beëedigen der aangifte", None),
]


def hand_font(size=HAND_SIZE):
    return ImageFont.truetype(HAND_FONT, size)


def printed_font(size, bold=False):
    return ImageFont.truetype(PRINT_BOLD_FONT if bold else PRINT_FONT, size)


def write_by_hand(draw, xy, text, rng, font=None):
    """Write ``text`` at ``xy`` word by word, each a little off the line, in uneven ink."""
    font = font or hand_font()
    x, y = xy
    for word in text.split():
        ink = int(rng.integers(10, 60))
        draw.text((x, y + rng.normal(0, 1.5)), word, font=font, fill=ink)
        x += font.getlength(word + " ") + rng.normal(0, 1.5)


def write_crooked(page, xy, lines, rng, angle):
    """Write ``lines`` by hand from ``xy`` down, the whole note turned ``angle`` degrees."""
    layer = Image.new("L", page.size, 255)
    draw, font = ImageDraw.Draw(layer), hand_font(BIG_HAND_SIZE)
    for number, line in enumerate(lines):
        write_by_hand(draw, (xy[0], xy[1] + number * 60), line, rng, font)
    layer = layer.rotate(angle, Image.Resampling.BICUBIC, center=xy, fillcolor=255)
    page.paste(ImageChops.darker(page, layer))


def wrap_to_width(text, font, width):
    """``text`` cut into lines no wider than ``width`` pixels."""
    lines = [""]
    for word in text.split():
        candidate = f"{lines[-1]} {word}".strip()
        if font.getlength(candidate) <= width or not lines[-1]:
            lines[-1] = candidate
        else:
            lines.append(word)
    return lines


def dotted_line(draw, x0, x1, y):
    """The dotted line a form's blank is filled in on."""
    for x in range(int(x0), int(x1), 9):
        draw.line([(x, y), (x + 2, y)], fill=50, width=2)


def question_table(draw, rows, top, bottom, rng):
    """The form's numbered questions, spread evenly from ``top`` to ``bottom``, each
    with its answer column.
    """
    for x in (QUESTION_X - 12, ANSWER_X):
        draw.line([(x, top), (x, bottom)], fill=70, width=2)
    font, row_h = printed_font(LABEL_SIZE), (bottom - top) / len(rows)
    for row, (number, question, answer) in enumerate(rows):
        y = top + row * row_h + 15
        draw.text((NUMBER_X, y), f"{number}.", font=font, fill=25)
        width = ANSWER_X - QUESTION_X - 20
        for line, text in enumerate(wrap_to_width(question, font, width)):
            draw.text((QUESTION_X, y + line * 22), text, font=font, fill=25)
        if answer:
            write_by_hand(draw, (ANSWER_X + 20, y - 8), answer, rng)


def previous_deed_end_page(page, deed, rng, memorie):
    """The last page of the deed before: the back of its cover form, signed."""
    draw = ImageDraw.Draw(page)
    draw.line([(MARGIN, 90), (PAGE_W - MARGIN, 90)], fill=40, width=3)
    question_table(draw, PREVIOUS_DEED_ROWS, 100, 960, rng)
    font, signature = printed_font(LABEL_SIZE), hand_font(BIG_HAND_SIZE)
    draw.text((MARGIN + 60, 1010), "De Ontvanger,", font=font, fill=25)
    write_by_hand(draw, (MARGIN + 40, 1060), "J. Brink", rng, signature)
    draw.text((ANSWER_X + 40, 990), "Gezien", font=font, fill=25)
    draw.text((ANSWER_X + 20, 1030), "De Inspecteur,", font=font, fill=25)
    write_by_hand(draw, (ANSWER_X + 30, 1080), "A. Mulder", rng, signature)
    draw.line([(ANSWER_X, 1150), (PAGE_W - MARGIN, 1140)], fill=40, width=2)


def cover_page(page, deed, rng, memorie):
    """The cover form: the printed header, filled in by hand, then questions 1 to 10."""
    draw = ImageDraw.Draw(page)
    left_center = MARGIN + 110
    draw.text(
        (left_center, 95),
        "(I. M. Art. 292.)",
        font=printed_font(15),
        fill=25,
        anchor="mm",
    )
    bold = printed_font(22, bold=True)
    draw.text((left_center, 140), "Nº. 91.", font=bold, fill=25, anchor="mm")
    draw.text((left_center, 185), "SUCCESSIE.", font=bold, fill=25, anchor="mm")
    draw.line([(left_center - 30, 210), (left_center + 30, 210)], fill=40, width=2)
    deel, nummer = deed["ref_reg"].split("#")
    font, big_hand = printed_font(LABEL_SIZE), hand_font(BIG_HAND_SIZE)
    draw.text((MARGIN, 255), f"REG. {deel}, Nº.", font=font, fill=25)
    write_by_hand(draw, (MARGIN + 110, 228), f"{deel}/{nummer}", rng, big_hand)

    x0, x1 = MARGIN + 260, PAGE_W - MARGIN
    title = printed_font(20, bold=True)
    draw.text((x0, 80), "OMSLAGVEL behoorende tot de memorie", font=title, fill=25)
    draw.text((x0, 108), "van aangifte der nalatenschap van", font=title, fill=25)
    deceased = deed["deceased"]
    write_by_hand(draw, (x0 + 40, 138), deceased["full_name"], rng, big_hand)
    dotted_line(draw, x0, x1, 190)
    blanks = [
        ("gewoond hebbende te", deceased["place_of_residence"]),
        ("overleden te", deceased["place_of_death"]),
        ("den", deceased["date_of_death"]),
    ]
    for line, (label, answer) in enumerate(blanks):
        y = 205 + line * 45
        draw.text((x0, y), label, font=title, fill=25)
        start = x0 + title.getlength(label) + 10
        write_by_hand(draw, (start + 10, y - 26), answer, rng, big_hand)
        dotted_line(draw, start, x1, y + 23)
    draw.line([(MARGIN, 345), (x1, 345)], fill=30, width=4)
    question_table(draw, COVER_ROWS, 355, PAGE_H - MARGIN, rng)


def cover_back_page(page, deed, rng, memorie):
    """The back of the cover form: questions 11 to 19. Question 11 holds the balance,
    filled in by hand: the assets, the liabilities and what is left.
    """
    draw = ImageDraw.Draw(page)
    font = printed_font(LABEL_SIZE)
    draw.line([(MARGIN, 90), (PAGE_W - MARGIN, 90)], fill=40, width=3)
    for x in (QUESTION_X - 12, ANSWER_X):
        draw.line([(x, 90), (x, 430)], fill=70, width=2)
    draw.text((NUMBER_X, 110), "11.", font=font, fill=25)
    draw.text(
        (QUESTION_X, 110), "Opgave van den staat des boedels:", font=font, fill=25
    )
    liabilities = deed["liabilities"]["total"]
    balance = [
        ("1°. Baten", f"f {deed['assets']['total']}"),
        ("2°. Lasten en schulden", f"f {liabilities}" if liabilities else "nihil"),
        ("3°. Saldo", f"f {deed['total']}"),
        ("4°. Vermeerdering bij nadere memoriën", None),
    ]
    big_hand = hand_font(BIG_HAND_SIZE)
    for line, (label, amount) in enumerate(balance):
        y = 160 + line * 55 + (25 if line >= 2 else 0)  # a gap above the saldo
        draw.text((QUESTION_X + 30, y), label, font=font, fill=25)
        if amount:
            write_by_hand(draw, (ANSWER_X + 40, y - 24), amount, rng, big_hand)
    # Under the liabilities: the line the saldo is worked out under.
    draw.line([(ANSWER_X + 30, 260), (ANSWER_X + 260, 260)], fill=40, width=2)
    question_table(draw, COVER_BACK_ROWS, 430, PAGE_H - MARGIN, rng)


def memorie_lines(deed):
    """The memorie, as ``(text, amount, kind)`` lines: its opening paragraph, then the
    assets and the liabilities under their headings. ``kind`` is "text", "heading" or
    "item"; an item's amount is on its last line, other lines have ``None``.
    """
    deceased = deed["deceased"]
    opening = (
        f"Memorie van aangifte der nalatenschap van {deceased['full_name']}, in "
        f"leven {deceased['profession']}, wonende te {deceased['place_of_residence']}, "
        f"overleden te {deceased['place_of_death']} den {deceased['date_of_death']}. "
        "De ondergeteekenden " + " en ".join(deed["declarants"]) + ", ten dezen "
        "woonplaats kiezende ten kantore van den ontvanger te "
        f"{deed['tax_office']}, verklaren dat de overledene geen uiterste "
        "wilsbeschikking heeft gemaakt en dat zijne nalatenschap bestaat uit:"
    )
    font, x0 = hand_font(), SIDE_RULE_X + 20
    text_width = PAGE_W - MARGIN - x0
    # Short of the amount column: the hand wanders a little past the line's end.
    item_width = text_width - AMOUNT_W - 40
    lines = [(t, None, "text") for t in wrap_to_width(opening, font, text_width)]
    for heading, type_ in (("Actief", "assets"), ("Passief", "liabilities")):
        lines += [(heading, None, "heading")]
        for item in deed[type_]["items"]:
            wrapped = wrap_to_width(item["description"], font, item_width)
            lines += [(t, None, "item") for t in wrapped[:-1]]
            lines += [(wrapped[-1], item["amount"], "item")]
    return lines


def memorie_page(page, deed, rng, memorie):
    """The next lines of ``memorie``, all by hand, with a crooked note in the margin."""
    draw = ImageDraw.Draw(page)
    draw.line([(SIDE_RULE_X, 40), (SIDE_RULE_X, PAGE_H - 40)], fill=50, width=2)
    deel, nummer = deed["ref_reg"].split("#")
    side_note = [f"{deel}/{nummer}", "ingel. den", "2 april 1921", "Dagr. 3/417"]
    write_crooked(page, (MARGIN - 30, MARGIN + 20), side_note, rng, angle=9)
    x0, x1 = SIDE_RULE_X + 20, PAGE_W - MARGIN
    amount_x = x1 - AMOUNT_W
    rows = (PAGE_H - 2 * MARGIN) // LINE_H
    for row in range(rows):
        if not memorie:
            break
        text, amount, kind = memorie.pop(0)
        top = MARGIN + row * LINE_H
        y = top + rng.normal(0, 1)
        x = x0
        if kind == "heading":
            x = (x0 + amount_x) / 2 - hand_font().getlength(text) / 2
        if kind == "item":
            draw.line([(amount_x, top), (amount_x, top + LINE_H)], fill=70, width=2)
        write_by_hand(draw, (x, y), text, rng)
        if amount is not None:
            write_by_hand(draw, (amount_x + 15, y), f"f {amount}", rng)


PAGE_KINDS = {
    "previous_deed_end": previous_deed_end_page,
    "cover": cover_page,
    "cover_back": cover_back_page,
    "memorie": memorie_page,
}


def grey_paper(rng):
    """Grey paper with blotches, uneven from page to page."""
    blotches = rng.normal(0, 14, (14, 20)).astype(np.float32)
    blotches = np.asarray(
        Image.fromarray(blotches, "F").resize(
            (PAGE_W, PAGE_H), Image.Resampling.BICUBIC
        )
    )
    paper = rng.normal(150, 5) + blotches
    return Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8), "L")


def scan_on_film(scan_number, pages, rng):
    """``pages`` side by side on black film with a frame counter, grainy and harsh."""
    scan = Image.new("L", (SCAN_W, SCAN_H), 8)
    for i, page in enumerate(pages):
        skewed = page.rotate(rng.normal(0, 0.3), Image.Resampling.BICUBIC, fillcolor=8)
        scan.paste(skewed, (FILM_SIDE + i * (PAGE_W + GUTTER), FILM_TOP))
    ImageDraw.Draw(scan).text(
        (SCAN_W - FILM_SIDE, SCAN_H - FILM_TOP / 2),
        f"{1000 + scan_number:05d}",
        font=printed_font(26),
        fill=200,
        anchor="rm",
    )
    scan = scan.filter(ImageFilter.GaussianBlur(0.8))
    pixels = np.asarray(scan, np.float32) + rng.normal(0, 9, (SCAN_H, SCAN_W))
    pixels = (pixels - 110) * 1.7 + 110  # harsh contrast, as on a microfilm print
    return Image.fromarray(np.clip(pixels, 0, 255).astype(np.uint8), "L")


def write_fake_deed(root, deed=DEED, layout=LAYOUT):
    """Write ``deed``'s single deed folder into ``root``: its scans as in ``layout``
    and its ``input.json``. Returns the folder.
    """
    folder = Path(root) / deed["ref_reg"].replace("#", "-")
    # Raises if it exists: an annotation there is never overwritten.
    folder.mkdir(parents=True)
    rng = np.random.default_rng(SEED)
    memorie = memorie_lines(deed)
    scans = []
    for number, kinds in enumerate(layout, 1):
        pages = [grey_paper(rng) for _ in kinds]
        for page, kind in zip(pages, kinds, strict=True):
            PAGE_KINDS[kind](page, deed, rng, memorie)
        scans.append(f"scan-{number:03d}.jpg")
        scan_on_film(number, pages, rng).save(folder / scans[-1], quality=85)
    assert not memorie, "the layout has too few memorie pages"
    metadata = {k: v for k, v in deed.items() if k != "declarants"} | {"scans": scans}
    (folder / "input.json").write_text(
        json.dumps(
            {"metadata": metadata, "scans": []},
            indent=2,
            ensure_ascii=False,
            default=float,  # amounts are JSON numbers, as in a real input.json
        ),
        encoding="utf-8",
    )
    return folder


if __name__ == "__main__":
    try:
        print(write_fake_deed(sys.argv[1]))
    except FileExistsError as error:
        sys.exit(f"{error.filename} exists: nothing written.")
