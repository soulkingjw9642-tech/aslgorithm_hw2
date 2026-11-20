"""Compare chaining and linear probing on the same deterministic workloads."""

import csv
import random
from pathlib import Path
from typing import Type

from src.hash_table import HashTable
from src.linear_probing import LinearProbingHashTable

CAPACITY = 10007
LOAD_FACTORS = tuple(step / 10 for step in range(1, 10))
OUTPUT_DIR = Path(__file__).parent
TableType = Type[HashTable] | Type[LinearProbingHashTable]


def _average_probes(
    table_type: TableType, keys: list[str], misses: list[str]
) -> tuple[float, float]:
    table = table_type(capacity=CAPACITY, max_load_factor=None)
    for index, key in enumerate(keys):
        table.put(key, f"value-{index}")

    successful = 0
    for key in keys:
        table.get(key)
        successful += table.last_lookup_probes

    unsuccessful = 0
    for key in misses:
        try:
            table.get(key)
        except KeyError:
            unsuccessful += table.last_lookup_probes
    return successful / len(keys), unsuccessful / len(misses)


def measure(
    target_alpha: float, keys: list[str], misses: list[str]
) -> tuple[float, float, int, float, float, float, float, float, float, float, float]:
    item_count = round(CAPACITY * target_alpha)
    actual_alpha = item_count / CAPACITY
    selected_keys = keys[:item_count]
    selected_misses = misses[:item_count]
    chain_success, chain_failure = _average_probes(
        HashTable, selected_keys, selected_misses
    )
    linear_success, linear_failure = _average_probes(
        LinearProbingHashTable, selected_keys, selected_misses
    )
    return (
        target_alpha,
        actual_alpha,
        item_count,
        chain_success,
        1 + actual_alpha / 2,
        chain_failure,
        actual_alpha,
        linear_success,
        0.5 * (1 + 1 / (1 - actual_alpha)),
        linear_failure,
        0.5 * (1 + 1 / (1 - actual_alpha) ** 2),
    )


def _measurements() -> list[
    tuple[float, float, int, float, float, float, float, float, float, float, float]
]:
    generator = random.Random(2026)
    max_items = round(CAPACITY * max(LOAD_FACTORS))
    keys = [f"key-{generator.getrandbits(64)}-{index}" for index in range(max_items)]
    misses = [
        f"missing-{generator.getrandbits(64)}-{index}" for index in range(max_items)
    ]
    return [measure(alpha, keys, misses) for alpha in LOAD_FACTORS]


def write_csv(rows: list[tuple[float, ...]]) -> Path:
    output = OUTPUT_DIR / "comparison_results.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(
            (
                "target_load_factor",
                "actual_load_factor",
                "items",
                "chaining_success_measured",
                "chaining_success_theory",
                "chaining_failure_measured",
                "chaining_failure_theory",
                "linear_success_measured",
                "linear_success_theory",
                "linear_failure_measured",
                "linear_failure_theory",
            )
        )
        for row in rows:
            writer.writerow(
                (f"{row[0]:.1f}", f"{row[1]:.5f}", row[2])
                + tuple(f"{value:.4f}" for value in row[3:])
            )
    return output


def _svg_panel(
    rows: list[tuple[float, ...]],
    x: float,
    y: float,
    width: float,
    height: float,
    y_max: float,
    title: str,
    series: tuple[tuple[str, str, int, bool], ...],
) -> list[str]:
    elements = [f'<text x="{x + width / 2}" y="{y - 15}" text-anchor="middle" font-family="sans-serif" font-size="16">{title}</text>']
    for tick in range(5):
        tick_value = y_max * tick / 4
        tick_y = y + height - height * tick / 4
        elements.append(
            f'<line x1="{x}" y1="{tick_y:.1f}" x2="{x + width}" y2="{tick_y:.1f}" stroke="#ddd"/>'
        )
        elements.append(
            f'<text x="{x - 8}" y="{tick_y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="10">{tick_value:.1f}</text>'
        )
    for tick in range(1, 10, 2):
        alpha = tick / 10
        tick_x = x + width * (alpha - 0.1) / 0.8
        elements.append(
            f'<text x="{tick_x:.1f}" y="{y + height + 18}" text-anchor="middle" font-family="sans-serif" font-size="10">{alpha:.1f}</text>'
        )
    elements.extend(
        (
            f'<line x1="{x}" y1="{y + height}" x2="{x + width}" y2="{y + height}" stroke="#333"/>',
            f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + height}" stroke="#333"/>',
        )
    )
    for legend_index, (label, color, index, dashed) in enumerate(series):
        points = []
        for row in rows:
            alpha = row[1]
            value = row[index]
            point_x = x + width * (alpha - 0.1) / 0.8
            point_y = y + height - height * value / y_max
            points.append((point_x, point_y))
        coordinates = " ".join(f"{px:.1f},{py:.1f}" for px, py in points)
        dash = ' stroke-dasharray="6 4"' if dashed else ""
        elements.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="2"{dash}/>'
        )
        legend_x = x + 12
        legend_y = y + height + 42 + legend_index * 18
        elements.append(
            f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 24}" y2="{legend_y}" stroke="{color}" stroke-width="2"{dash}/>'
        )
        elements.append(
            f'<text x="{legend_x + 30}" y="{legend_y + 4}" font-family="sans-serif" font-size="10">{label}</text>'
        )
    return elements


def write_svg(rows: list[tuple[float, ...]]) -> Path:
    width, height = 1100, 620
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>Hash table lookup cost comparison</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="550" y="28" text-anchor="middle" font-family="sans-serif" font-size="20">Chaining vs. linear probing</text>',
        '<text x="550" y="600" text-anchor="middle" font-family="sans-serif" font-size="13">Load factor (alpha)</text>',
        '<text transform="translate(18 300) rotate(-90)" text-anchor="middle" font-family="sans-serif" font-size="13">Average visited nodes / slots</text>',
    ]
    success_series = (
        ("Chaining measured", "#1769aa", 3, False),
        ("Chaining theory", "#1769aa", 4, True),
        ("Linear measured", "#d1495b", 7, False),
        ("Linear theory", "#d1495b", 8, True),
    )
    failure_series = (
        ("Chaining measured", "#1769aa", 5, False),
        ("Chaining theory", "#1769aa", 6, True),
        ("Linear measured", "#d1495b", 9, False),
        ("Linear theory", "#d1495b", 10, True),
    )
    elements.extend(
        _svg_panel(rows, 80, 90, 430, 340, 7, "Successful search", success_series)
    )
    elements.extend(
        _svg_panel(rows, 620, 90, 430, 340, 65, "Unsuccessful search", failure_series)
    )
    elements.append("</svg>")
    output = OUTPUT_DIR / "comparison_results.svg"
    output.write_text("\n".join(elements) + "\n", encoding="utf-8")
    return output


def _pdf_escape(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return escaped.encode("ascii")


def write_report(rows: list[tuple[float, ...]]) -> Path:
    low, middle, high = rows[0], rows[4], rows[-1]
    page_one = [
        "Hash Table Lookup Cost: Chaining vs. Linear Probing",
        "Question: how does load factor affect average successful and failed lookups?",
        "Method",
        f"- Capacity: {CAPACITY} slots; target alpha values: 0.1 through 0.9.",
        "- Same deterministic key and miss sets were used for both implementations.",
        "- The experiment used a fixed capacity and did not resize during measurement.",
        "- Each stored key and each absent key was queried once; probes count visited",
        "  nodes for chaining and visited slots for linear probing.",
        "Theory (uniform hashing)",
        "- Chaining: success 1 + alpha/2; failure alpha.",
        "- Linear probing: success (1 + 1/(1-alpha))/2;",
        "  failure (1 + 1/(1-alpha)^2)/2.",
        "Selected results: measured average probes",
        "alpha   chain success   linear success   chain failure   linear failure",
    ]
    for row in (low, middle, high):
        page_one.append(
            f"{row[0]:.1f}       {row[3]:.3f}           {row[7]:.3f}"
            f"            {row[5]:.3f}           {row[9]:.3f}"
        )
    page_two = [
        "Interpretation",
        "- Chaining grows gradually: at alpha 0.9 its measured success/failure costs",
        f"  are {high[3]:.3f}/{high[5]:.3f}, near theory",
        f"  {high[4]:.3f}/{high[6]:.3f}.",
        "- Linear probing is efficient at low load, but primary clustering makes",
        "  failed searches grow sharply near a full table.",
        f"- At alpha 0.9, linear success/failure costs are {high[7]:.3f}/{high[9]:.3f};",
        f"  theory predicts {high[8]:.3f}/{high[10]:.3f}.",
        f"- At alpha 0.9, linear failure is {high[9]:.3f} vs. {high[10]:.3f} expected;",
        "  deterministic polynomial hashes and finite samples depart from uniform",
        "  independent hashing, with clustering amplifying the difference at high load.",
        "- The cost definitions differ slightly: chaining counts examined nodes;",
        "  linear probing counts every inspected slot, including the empty slot",
        "  that terminates an unsuccessful search.",
        "Conclusion",
        "- Keep load factor moderate for linear probing. Chaining tolerates heavier",
        "  loads more gracefully, at the cost of linked-list storage and pointer walks.",
        "Reproducibility: make experiment; see comparison_results.csv and .svg.",
    ]
    pages = (page_one, page_two)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [4 0 R 6 0 R] /Count 2 >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    for page_number, lines in enumerate(pages):
        content = bytearray()
        for line_number, line in enumerate(lines):
            font_size = 16 if line_number == 0 else 10
            y = 750 - line_number * 25
            content.extend(
                b"BT /F1 "
                + str(font_size).encode("ascii")
                + b" Tf 48 "
                + str(y).encode("ascii")
                + b" Td ("
                + _pdf_escape(line)
                + b") Tj ET\n"
            )
        page_id = 4 + page_number * 2
        content_id = page_id + 1
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>".encode(
                "ascii"
            )
        )
        objects.append(
            f"<< /Length {len(content)} >>\nstream\n".encode("ascii")
            + bytes(content)
            + b"endstream"
        )

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode(
            "ascii"
        )
    )
    output = OUTPUT_DIR / "hash-table-report.pdf"
    output.write_bytes(pdf)
    return output


def main() -> None:
    rows = _measurements()
    csv_path = write_csv(rows)
    svg_path = write_svg(rows)
    report_path = write_report(rows)
    print(f"Wrote {csv_path}")
    print(f"Wrote {svg_path}")
    print(f"Wrote {report_path}")
    print("alpha  chain success/failure  linear success/failure")
    for row in rows:
        print(
            f"{row[0]:.1f}    {row[3]:6.3f}/{row[5]:6.3f}"
            f"       {row[7]:6.3f}/{row[9]:6.3f}"
        )


if __name__ == "__main__":
    main()
