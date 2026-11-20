"""Compare separate-chaining lookup costs with expected probe counts."""

import csv
import random
from pathlib import Path

from src.hash_table import HashTable

CAPACITY = 1009
LOAD_FACTORS = tuple(step / 4 for step in range(1, 17))
OUTPUT_DIR = Path(__file__).parent


def measure(load_factor: float) -> tuple[float, float, float, float, float, int]:
    item_count = round(CAPACITY * load_factor)
    table = HashTable(capacity=CAPACITY, max_load_factor=None)
    generator = random.Random(2026)
    keys = [
        f"key-{generator.getrandbits(64)}-{index}" for index in range(item_count)
    ]
    for index, key in enumerate(keys):
        table.put(key, f"value-{index}")

    successful = 0
    for key in keys:
        table.get(key)
        successful += table.last_lookup_probes

    unsuccessful = 0
    for index in range(item_count):
        try:
            table.get(f"missing-{generator.getrandbits(64)}-{index}")
        except KeyError:
            unsuccessful += table.last_lookup_probes

    return (
        load_factor,
        successful / item_count,
        1 + load_factor / 2,
        unsuccessful / item_count,
        load_factor,
        item_count,
    )


def write_csv(rows: list[tuple[float, float, float, float, float, int]]) -> Path:
    output = OUTPUT_DIR / "probe_results.csv"
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(
            (
                "load_factor",
                "items",
                "successful_measured",
                "successful_theory",
                "unsuccessful_measured",
                "unsuccessful_theory",
            )
        )
        for alpha, successful, successful_theory, unsuccessful, unsuccessful_theory, items in rows:
            writer.writerow(
                (
                    f"{alpha:.2f}",
                    items,
                    f"{successful:.4f}",
                    f"{successful_theory:.4f}",
                    f"{unsuccessful:.4f}",
                    f"{unsuccessful_theory:.4f}",
                )
            )
    return output


def write_svg(rows: list[tuple[float, float, float, float, float, int]]) -> Path:
    width, height = 960, 520
    left, top, plot_width, plot_height = 80, 45, 820, 380

    def point(alpha: float, probes: float) -> tuple[float, float]:
        x = left + alpha / 4 * plot_width
        y = top + plot_height - probes / 4 * plot_height
        return x, y

    series = (
        ("Successful (measured)", "#1769aa", 1),
        ("Successful (theory)", "#1769aa", 2),
        ("Unsuccessful (measured)", "#d1495b", 3),
        ("Unsuccessful (theory)", "#d1495b", 4),
    )
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<title>Separate chaining lookup probes by load factor</title>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="480" y="25" text-anchor="middle" font-family="sans-serif" font-size="18">Chaining lookup cost vs. load factor</text>',
    ]
    for tick in range(5):
        y = top + plot_height - tick / 4 * plot_height
        elements.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}" stroke="#ddd"/>'
        )
        elements.append(
            f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" font-family="sans-serif" font-size="12">{tick}</text>'
        )
        x = left + tick / 4 * plot_width
        elements.append(
            f'<text x="{x:.1f}" y="{top + plot_height + 22}" text-anchor="middle" font-family="sans-serif" font-size="12">{tick}</text>'
        )
    elements.extend(
        (
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#333"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#333"/>',
            f'<text x="{left + plot_width / 2}" y="{height - 18}" text-anchor="middle" font-family="sans-serif" font-size="13">Load factor (α)</text>',
            f'<text transform="translate(20 {top + plot_height / 2}) rotate(-90)" text-anchor="middle" font-family="sans-serif" font-size="13">Average node visits</text>',
        )
    )
    for label, color, index in series:
        points = [point(row[0], row[index]) for row in rows]
        points_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        dash = ' stroke-dasharray="6 4"' if index in (2, 4) else ""
        elements.append(
            f'<polyline points="{points_text}" fill="none" stroke="{color}" stroke-width="2"{dash}/>'
        )
        for x, y in points:
            elements.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{color}"/>'
            )
        legend_index = index - 1
        legend_x = 110 + (legend_index % 2) * 370
        legend_y = 470 + (legend_index // 2) * 20
        elements.append(
            f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 28}" y2="{legend_y}" stroke="{color}" stroke-width="2"{dash}/>'
        )
        elements.append(
            f'<text x="{legend_x + 36}" y="{legend_y + 4}" font-family="sans-serif" font-size="12">{label}</text>'
        )
    elements.append("</svg>")
    output = OUTPUT_DIR / "probe_results.svg"
    output.write_text("\n".join(elements) + "\n", encoding="utf-8")
    return output


def main() -> None:
    rows = [measure(alpha) for alpha in LOAD_FACTORS]
    csv_path = write_csv(rows)
    svg_path = write_svg(rows)
    print(f"Wrote {csv_path}")
    print(f"Wrote {svg_path}")
    print(" α     success measured/theory    failure measured/theory")
    for alpha, success, success_theory, failure, failure_theory, items in rows:
        print(
            f"{alpha:4.2f}   {success:7.3f}/{success_theory:7.3f}"
            f"          {failure:7.3f}/{failure_theory:7.3f}"
        )


if __name__ == "__main__":
    main()
