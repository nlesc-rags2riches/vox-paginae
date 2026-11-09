"""Write `<dir>/1-1001/`: a fake single deed folder to try the single-deed notebook on.

Its scans look like a 1921 Drenthe deed on microfilm (two pages side by side), with
invented content. The same every run. Refuses to run if the folder exists.

Usage: uv run python scripts/fake_deed.py <dir>
"""

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

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
HAND_SIZE, LINE_H = 46, 62
AMOUNT_W = 150  # the amount column at a memorie page's right edge
ASSETS_TOTAL = "Totaal der baten"

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
    "assets": {
        "total": 10769,
        "items": [
            {
                "amount": 4800,
                "description": "Een woonhuis met schuur en erf, staande en gelegen te "
                "Oostdorp aan den Brink, kadastraal bekend gemeente Oostdorp sectie A "
                "nummer 214, groot achttien aren veertig centiaren",
            },
            {
                "amount": 1250,
                "description": "Een perceel bouwland, gelegen onder Oostdorp in de "
                "Noordesch, kadastraal bekend sectie B nummer 87",
            },
            {
                "amount": 640,
                "description": "Een perceel hooiland in het Oostermade, kadastraal "
                "bekend sectie C nummer 12",
            },
            {"amount": 1150, "description": "Drie koeien, een paard en twee varkens"},
            {"amount": 310, "description": "Landbouwgereedschappen en een boerenwagen"},
            {"amount": 225, "description": "Huisraad, kleeding en lijfgoederen"},
            {
                "amount": 500,
                "description": "Eene vordering ten laste van Hendrik Klein, "
                "arbeider te Westdorp, wegens geleend geld",
            },
            {
                "amount": 400,
                "description": "Twintig aandeelen in de Coöperatieve Zuivelfabriek "
                "te Oostdorp",
            },
            {"amount": 95, "description": "Rogge, haver en turf in voorraad"},
            {
                "amount": 1312,
                "description": "Tegoed op een spaarbankboekje bij de Spaarbank te "
                "Westdorp",
            },
            {"amount": 87, "description": "Contanten in kas"},
        ],
    },
    "liabilities": {"total": None, "items": []},
    "total": 10769,
}

# One (left, right) pair of page kinds per scan.
LAYOUT = [("cover", "memorie"), ("memorie", "blank")]

COVER_ROWS = [  # (printed label, the deceased's field written in by hand)
    ("Naam van den overledene", "full_name"),
    ("Beroep", None),
    ("Laatste woonplaats", "place_of_residence"),
    ("Datum van overlijden", "date_of_death"),
    ("Plaats van overlijden", None),
    ("Burgerlijke staat", None),
    ("Datum der memorie", None),
    ("Bedrag der baten", None),
    ("Bedrag der lasten", None),
    ("Zuiver saldo", None),
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


def memorie_lines(deed):
    """The memorie, as ``(text, amount)`` lines: its opening, then the assets with
    their total. An item's amount is on its last line; other lines have ``None``.
    """
    deceased = deed["deceased"]
    opening = (
        f"Memorie van aangifte der nalatenschap van {deceased['full_name']}, in "
        f"leven {deceased['profession']}, wonende te {deceased['place_of_residence']}, "
        f"overleden te {deceased['place_of_death']} den {deceased['date_of_death']}."
    )
    declarants = "Aangevers: " + " en ".join(deed["declarants"]) + "."
    # Short of the amount column: the hand wanders a little past the line's end.
    font, width = hand_font(), PAGE_W - 2 * MARGIN - AMOUNT_W - 40
    lines = [(t, None) for t in wrap_to_width(opening, font, width)]
    lines += [("", None)] + [(t, None) for t in wrap_to_width(declarants, font, width)]
    lines += [("", None), ("Baten", None)]
    for number, item in enumerate(deed["assets"]["items"], 1):
        wrapped = wrap_to_width(f"{number}. {item['description']}", font, width)
        lines += [(t, None) for t in wrapped[:-1]] + [(wrapped[-1], item["amount"])]
    lines += [("", None), (ASSETS_TOTAL, deed["assets"]["total"])]
    return lines


def cover_page(page, deed, rng, memorie_state):
    """The cover form: printed rows 1 to 10, some filled in by hand."""
    draw = ImageDraw.Draw(page)
    title = printed_font(40, bold=True)
    draw.text(
        (PAGE_W / 2, 110), "MEMORIE VAN SUCCESSIE", font=title, fill=25, anchor="mm"
    )
    draw.text(
        (PAGE_W / 2, 165), "Omslagvel", font=printed_font(30), fill=25, anchor="mm"
    )
    deel, nummer = deed["ref_reg"].split("#")
    office = f"Kantoor {deed['tax_office']}    Deel {deel}    No. {nummer}"
    draw.text((PAGE_W / 2, 220), office, font=printed_font(24), fill=25, anchor="mm")
    label_font = printed_font(24)
    for row, (label, field) in enumerate(COVER_ROWS):
        y = 320 + row * 100
        draw.text((MARGIN, y), f"{row + 1}.  {label}", font=label_font, fill=25)
        draw.line([(MARGIN, y + 80), (PAGE_W - MARGIN, y + 80)], fill=60, width=2)
        if field and deed["deceased"].get(field):
            write_by_hand(draw, (MARGIN + 60, y + 30), deed["deceased"][field], rng)


def memorie_page(page, deed, rng, memorie_state):
    """The next lines of ``memorie_state``, with the carried-over total at the top and the
    bottom when the memorie goes on past this page.
    """
    draw = ImageDraw.Draw(page)
    amount_x = PAGE_W - MARGIN - AMOUNT_W
    draw.line([(amount_x, MARGIN), (amount_x, PAGE_H - MARGIN)], fill=70, width=2)
    rows = (PAGE_H - 2 * MARGIN) // LINE_H

    def write_line(row, text, amount):
        y = MARGIN + row * LINE_H + rng.normal(0, 1)
        write_by_hand(draw, (MARGIN, y), text, rng)
        if amount is not None:
            write_by_hand(draw, (amount_x + 20, y), f"f {amount}", rng)

    row = 0
    if (
        memorie_state["carried"] and memorie_state["lines"]
    ):  # carried over from the page before
        write_line(row, "Transport", memorie_state["carried"])
        row += 1
    while memorie_state["lines"] and row < rows - 1:
        text, amount = memorie_state["lines"].pop(0)
        write_line(row, text, amount)
        if amount is not None and text != ASSETS_TOTAL:
            memorie_state["carried"] += amount
        row += 1
    if memorie_state["lines"]:
        write_line(row, "Transport", memorie_state["carried"])


PAGE_KINDS = {"cover": cover_page, "memorie": memorie_page, "blank": lambda *_: None}


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
    memorie_state = {"lines": memorie_lines(deed), "carried": 0}
    scans = []
    for number, kinds in enumerate(layout, 1):
        pages = [grey_paper(rng) for _ in kinds]
        for page, kind in zip(pages, kinds, strict=True):
            PAGE_KINDS[kind](page, deed, rng, memorie_state)
        scans.append(f"scan-{number:03d}.jpg")
        scan_on_film(number, pages, rng).save(folder / scans[-1], quality=85)
    assert not memorie_state["lines"], "the layout has too few memorie pages"
    metadata = {k: v for k, v in deed.items() if k != "declarants"} | {"scans": scans}
    (folder / "input.json").write_text(
        json.dumps({"metadata": metadata, "scans": []}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return folder


if __name__ == "__main__":
    try:
        print(write_fake_deed(sys.argv[1]))
    except FileExistsError as error:
        sys.exit(f"{error.filename} exists: nothing written.")
