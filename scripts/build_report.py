"""Build the EV market report assets from the source CSV."""

from __future__ import annotations

import csv
import html
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "ev_market_2026.csv"
DOCS_DIR = ROOT / "docs"
ASSETS_DIR = DOCS_DIR / "assets"
DATA_DIR = DOCS_DIR / "data"
REPORTS_DIR = ROOT / "reports"

NUMERIC_FIELDS: dict[str, Callable[[float], Any]] = {
    "year": lambda value: int(round(value)),
    "price_usd": float,
    "battery_capacity_kwh": float,
    "range_miles": float,
    "charging_speed_kw": float,
    "acceleration_0_60_mph": float,
    "top_speed_mph": float,
    "horsepower": float,
    "torque_nm": float,
    "seating_capacity": lambda value: int(round(value)),
    "cargo_volume_cubic_ft": float,
    "weight_kg": float,
    "safety_rating": lambda value: int(round(value)),
    "autopilot_level": lambda value: int(round(value)),
    "annual_sales_units": lambda value: int(round(value)),
    "customer_rating": float,
    "warranty_years": lambda value: int(round(value)),
}

PALETTE = [
    "#0f766e",
    "#2563eb",
    "#e11d48",
    "#d97706",
    "#7c3aed",
    "#059669",
    "#c2410c",
    "#0891b2",
    "#be123c",
    "#4f46e5",
]

SEGMENT_COLORS = {
    "Budget": "#0f766e",
    "Mid-range": "#2563eb",
    "Premium": "#d97706",
    "Luxury": "#e11d48",
}


def ensure_dirs() -> None:
    for directory in (ASSETS_DIR, DATA_DIR, REPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def parse_rows() -> list[dict[str, Any]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        for field, caster in NUMERIC_FIELDS.items():
            raw_value = row.get(field, "")
            row[field] = None if raw_value == "" else caster(float(raw_value))
        row["model_name"] = f"{row['brand']} {row['model']}"
        row["vehicle_label"] = (
            f"{row['brand']} {row['model']} {row['variant']} ({row['year']})"
        )
        row["price_per_mile"] = (
            row["price_usd"] / row["range_miles"] if row["range_miles"] else None
        )
        row["value_index"] = (
            (row["range_miles"] / (row["price_usd"] / 1000))
            * (row["customer_rating"] / 5)
            if row["price_usd"] and row["customer_rating"]
            else None
        )
    return rows


def compact_number(value: float) -> str:
    absolute = abs(value)
    if absolute >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if absolute >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def money(value: float) -> str:
    return f"${value:,.0f}"


def money_compact(value: float) -> str:
    return f"${compact_number(value)}"


def pct(value: float) -> str:
    return f"{value:.1%}"


def svg_text(value: Any) -> str:
    return html.escape(str(value), quote=True)


def group_sum(rows: list[dict[str, Any]], key: str, value: str) -> list[dict[str, Any]]:
    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        totals[str(row[key])] += float(row[value] or 0)
        counts[str(row[key])] += 1
    return [
        {"name": name, "value": totals[name], "records": counts[name]}
        for name in sorted(totals, key=totals.get, reverse=True)
    ]


def summarize_group(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    total_sales = sum(float(row["annual_sales_units"] or 0) for row in rows)
    for row in rows:
        groups[str(row[key])].append(row)

    summary = []
    for name, items in groups.items():
        sales = sum(float(row["annual_sales_units"] or 0) for row in items)
        summary.append(
            {
                "name": name,
                "records": len(items),
                "sales": sales,
                "sales_share": sales / total_sales if total_sales else 0,
                "avg_price": mean(float(row["price_usd"]) for row in items),
                "avg_range": mean(float(row["range_miles"]) for row in items),
                "avg_rating": mean(float(row["customer_rating"]) for row in items),
                "avg_safety": mean(float(row["safety_rating"]) for row in items),
            }
        )
    return sorted(summary, key=lambda item: item["sales"], reverse=True)


def compute_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_sales = sum(float(row["annual_sales_units"] or 0) for row in rows)
    brand_sales = group_sum(rows, "brand", "annual_sales_units")
    segment_summary = summarize_group(rows, "market_segment")
    country_sales = group_sum(rows, "country_of_origin", "annual_sales_units")
    body_sales = group_sum(rows, "body_type", "annual_sales_units")

    top_models = sorted(
        rows, key=lambda row: float(row["annual_sales_units"] or 0), reverse=True
    )[:12]
    value_leaders = sorted(
        rows, key=lambda row: float(row["value_index"] or 0), reverse=True
    )[:12]
    range_leaders = sorted(
        rows, key=lambda row: float(row["range_miles"] or 0), reverse=True
    )[:12]
    performance_leaders = sorted(
        rows,
        key=lambda row: (
            float(row["acceleration_0_60_mph"] or 99),
            -float(row["annual_sales_units"] or 0),
        ),
    )[:12]

    return {
        "record_count": len(rows),
        "brand_count": len({row["brand"] for row in rows}),
        "year_min": min(int(row["year"]) for row in rows),
        "year_max": max(int(row["year"]) for row in rows),
        "total_sales_units": total_sales,
        "avg_price_usd": mean(float(row["price_usd"]) for row in rows),
        "median_price_usd": median(float(row["price_usd"]) for row in rows),
        "avg_range_miles": mean(float(row["range_miles"]) for row in rows),
        "median_range_miles": median(float(row["range_miles"]) for row in rows),
        "avg_charging_speed_kw": mean(
            float(row["charging_speed_kw"]) for row in rows
        ),
        "avg_customer_rating": mean(float(row["customer_rating"]) for row in rows),
        "avg_safety_rating": mean(float(row["safety_rating"]) for row in rows),
        "avg_price_per_mile": mean(float(row["price_per_mile"]) for row in rows),
        "top_brand": brand_sales[0],
        "top_segment": segment_summary[0],
        "top_three_brand_share": sum(item["value"] for item in brand_sales[:3])
        / total_sales,
        "brand_sales": brand_sales,
        "segment_summary": segment_summary,
        "country_sales": country_sales,
        "body_sales": body_sales,
        "top_models": top_models,
        "value_leaders": value_leaders,
        "range_leaders": range_leaders,
        "performance_leaders": performance_leaders,
    }


def write_bar_svg(
    path: Path,
    data: list[dict[str, Any]],
    title: str,
    subtitle: str,
    value_formatter: Callable[[float], str],
) -> None:
    width, height = 960, 560
    left, top, right, bottom = 220, 92, 82, 70
    chart_width = width - left - right
    chart_height = height - top - bottom
    max_value = max(float(item["value"]) for item in data) or 1
    row_height = chart_height / len(data)
    grid_values = [max_value * i / 4 for i in range(1, 5)]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        ".bg{fill:#fbfcfd}.title{font:700 26px Arial, sans-serif;fill:#111827}.subtitle{font:14px Arial, sans-serif;fill:#64748b}.axis{font:12px Arial, sans-serif;fill:#64748b}.label{font:600 14px Arial, sans-serif;fill:#1f2937}.value{font:700 13px Arial, sans-serif;fill:#111827}.grid{stroke:#e5e7eb;stroke-width:1}.bar{rx:5;ry:5}",
        "</style>",
        '<rect class="bg" width="100%" height="100%" rx="12"/>',
        f'<text class="title" x="32" y="42">{svg_text(title)}</text>',
        f'<text class="subtitle" x="32" y="66">{svg_text(subtitle)}</text>',
    ]

    for value in grid_values:
        x = left + (value / max_value) * chart_width
        parts.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + chart_height}"/>')
        parts.append(
            f'<text class="axis" x="{x:.1f}" y="{height - 35}" text-anchor="middle">{svg_text(value_formatter(value))}</text>'
        )

    for index, item in enumerate(data):
        y = top + index * row_height + 7
        bar_height = max(row_height - 14, 16)
        value = float(item["value"])
        bar_width = max((value / max_value) * chart_width, 2)
        color = PALETTE[index % len(PALETTE)]
        parts.append(
            f'<text class="label" x="{left - 18}" y="{y + bar_height / 2 + 5:.1f}" text-anchor="end">{svg_text(item["name"])}</text>'
        )
        parts.append(
            f'<rect class="bar" x="{left}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{color}"/>'
        )
        parts.append(
            f'<text class="value" x="{left + bar_width + 10:.1f}" y="{y + bar_height / 2 + 5:.1f}">{svg_text(value_formatter(value))}</text>'
        )

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def polar_to_cartesian(cx: float, cy: float, radius: float, angle: float) -> tuple[float, float]:
    radians = math.radians(angle - 90)
    return cx + radius * math.cos(radians), cy + radius * math.sin(radians)


def donut_path(
    cx: float,
    cy: float,
    outer_radius: float,
    inner_radius: float,
    start_angle: float,
    end_angle: float,
) -> str:
    large_arc = 1 if end_angle - start_angle > 180 else 0
    outer_start = polar_to_cartesian(cx, cy, outer_radius, end_angle)
    outer_end = polar_to_cartesian(cx, cy, outer_radius, start_angle)
    inner_start = polar_to_cartesian(cx, cy, inner_radius, start_angle)
    inner_end = polar_to_cartesian(cx, cy, inner_radius, end_angle)
    return (
        f"M {outer_start[0]:.3f} {outer_start[1]:.3f} "
        f"A {outer_radius} {outer_radius} 0 {large_arc} 0 {outer_end[0]:.3f} {outer_end[1]:.3f} "
        f"L {inner_start[0]:.3f} {inner_start[1]:.3f} "
        f"A {inner_radius} {inner_radius} 0 {large_arc} 1 {inner_end[0]:.3f} {inner_end[1]:.3f} Z"
    )


def write_donut_svg(path: Path, data: list[dict[str, Any]], title: str, subtitle: str) -> None:
    width, height = 960, 560
    cx, cy = 288, 306
    outer, inner = 170, 94
    total = sum(float(item["value"]) for item in data) or 1
    angle = 0.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        ".bg{fill:#fbfcfd}.title{font:700 26px Arial, sans-serif;fill:#111827}.subtitle{font:14px Arial, sans-serif;fill:#64748b}.center{font:700 30px Arial, sans-serif;fill:#111827}.center2{font:13px Arial, sans-serif;fill:#64748b}.legend{font:600 16px Arial, sans-serif;fill:#1f2937}.legend2{font:13px Arial, sans-serif;fill:#64748b}",
        "</style>",
        '<rect class="bg" width="100%" height="100%" rx="12"/>',
        f'<text class="title" x="32" y="42">{svg_text(title)}</text>',
        f'<text class="subtitle" x="32" y="66">{svg_text(subtitle)}</text>',
    ]

    for index, item in enumerate(data):
        value = float(item["value"])
        sweep = value / total * 360
        color = SEGMENT_COLORS.get(str(item["name"]), PALETTE[index % len(PALETTE)])
        path_data = donut_path(cx, cy, outer, inner, angle, angle + sweep)
        parts.append(f'<path d="{path_data}" fill="{color}"/>')
        angle += sweep

    parts.append(f'<text class="center" x="{cx}" y="{cy - 6}" text-anchor="middle">{svg_text(compact_number(total))}</text>')
    parts.append(f'<text class="center2" x="{cx}" y="{cy + 18}" text-anchor="middle">annual sales units</text>')

    for index, item in enumerate(data):
        y = 176 + index * 70
        color = SEGMENT_COLORS.get(str(item["name"]), PALETTE[index % len(PALETTE)])
        share = float(item["value"]) / total
        parts.append(f'<rect x="560" y="{y}" width="18" height="18" rx="4" fill="{color}"/>')
        parts.append(f'<text class="legend" x="594" y="{y + 15}">{svg_text(item["name"])}</text>')
        parts.append(
            f'<text class="legend2" x="594" y="{y + 38}">{svg_text(compact_number(float(item["value"])))} units | {svg_text(pct(share))}</text>'
        )

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_scatter_svg(path: Path, rows: list[dict[str, Any]], title: str, subtitle: str) -> None:
    width, height = 960, 560
    left, top, right, bottom = 92, 88, 52, 78
    chart_width = width - left - right
    chart_height = height - top - bottom
    min_x = min(float(row["range_miles"]) for row in rows)
    max_x = max(float(row["range_miles"]) for row in rows)
    min_y = min(float(row["price_usd"]) for row in rows)
    max_y = max(float(row["price_usd"]) for row in rows)
    min_sales = min(float(row["annual_sales_units"]) for row in rows)
    max_sales = max(float(row["annual_sales_units"]) for row in rows)

    def x_scale(value: float) -> float:
        return left + (value - min_x) / (max_x - min_x) * chart_width

    def y_scale(value: float) -> float:
        return top + chart_height - (value - min_y) / (max_y - min_y) * chart_height

    def radius(value: float) -> float:
        if max_sales == min_sales:
            return 4
        return 2.2 + math.sqrt((value - min_sales) / (max_sales - min_sales)) * 6.5

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        ".bg{fill:#fbfcfd}.title{font:700 26px Arial, sans-serif;fill:#111827}.subtitle{font:14px Arial, sans-serif;fill:#64748b}.axis{font:12px Arial, sans-serif;fill:#64748b}.axisTitle{font:700 13px Arial, sans-serif;fill:#374151}.grid{stroke:#e5e7eb;stroke-width:1}.legend{font:600 12px Arial, sans-serif;fill:#374151}",
        "</style>",
        '<rect class="bg" width="100%" height="100%" rx="12"/>',
        f'<text class="title" x="32" y="42">{svg_text(title)}</text>',
        f'<text class="subtitle" x="32" y="66">{svg_text(subtitle)}</text>',
    ]

    for index in range(5):
        x_value = min_x + (max_x - min_x) * index / 4
        x = x_scale(x_value)
        parts.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + chart_height}"/>')
        parts.append(
            f'<text class="axis" x="{x:.1f}" y="{height - 42}" text-anchor="middle">{x_value:.0f}</text>'
        )
        y_value = min_y + (max_y - min_y) * index / 4
        y = y_scale(y_value)
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + chart_width}" y2="{y:.1f}"/>')
        parts.append(
            f'<text class="axis" x="{left - 14}" y="{y + 4:.1f}" text-anchor="end">{svg_text(money_compact(y_value))}</text>'
        )

    for row in rows:
        segment = str(row["market_segment"])
        color = SEGMENT_COLORS.get(segment, "#64748b")
        parts.append(
            f'<circle cx="{x_scale(float(row["range_miles"])):.1f}" cy="{y_scale(float(row["price_usd"])):.1f}" r="{radius(float(row["annual_sales_units"])):.2f}" fill="{color}" opacity="0.32"/>'
        )

    parts.append(
        f'<text class="axisTitle" x="{left + chart_width / 2}" y="{height - 14}" text-anchor="middle">Range miles</text>'
    )
    parts.append(
        f'<text class="axisTitle" x="22" y="{top + chart_height / 2}" transform="rotate(-90 22 {top + chart_height / 2})" text-anchor="middle">Price USD</text>'
    )

    for index, (segment, color) in enumerate(SEGMENT_COLORS.items()):
        x = 620 + index * 80
        parts.append(f'<circle cx="{x}" cy="42" r="6" fill="{color}"/>')
        parts.append(f'<text class="legend" x="{x + 12}" y="46">{svg_text(segment)}</text>')

    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def write_data_files(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    serializable_summary = {
        key: value
        for key, value in summary.items()
        if key
        not in {
            "top_models",
            "value_leaders",
            "range_leaders",
            "performance_leaders",
        }
    }
    (DATA_DIR / "summary.json").write_text(
        json.dumps(serializable_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (DATA_DIR / "ev_market_2026.json").write_text(
        json.dumps(rows, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def clean_markdown(text: str) -> str:
    lines = text.strip().splitlines()
    return "\n".join(line[8:] if line.startswith("        ") else line for line in lines) + "\n"


def build_readme(summary: dict[str, Any]) -> str:
    top_brand = summary["top_brand"]
    top_segment = summary["top_segment"]
    kpi_rows = [
        ["Records", f"{summary['record_count']:,}"],
        ["Brands", f"{summary['brand_count']:,}"],
        ["Year coverage", f"{summary['year_min']}-{summary['year_max']}"],
        ["Total annual sales", compact_number(summary["total_sales_units"])],
        ["Average price", money(summary["avg_price_usd"])],
        ["Median range", f"{summary['median_range_miles']:.0f} miles"],
        ["Average charging speed", f"{summary['avg_charging_speed_kw']:.1f} kW"],
        ["Average customer rating", f"{summary['avg_customer_rating']:.2f}/5"],
    ]
    brand_rows = [
        [
            item["name"],
            compact_number(item["value"]),
            pct(item["value"] / summary["total_sales_units"]),
        ]
        for item in summary["brand_sales"][:8]
    ]
    segment_rows = [
        [
            item["name"],
            f"{item['records']:,}",
            compact_number(item["sales"]),
            pct(item["sales_share"]),
            money(item["avg_price"]),
            f"{item['avg_range']:.0f} mi",
        ]
        for item in summary["segment_summary"]
    ]
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    return clean_markdown(
        f"""
        # EV Market 2026 Dashboard Report

        Professional analytics report and dashboard layer built from [`ev_market_2026.csv`](ev_market_2026.csv). The analysis is scoped to the dataset in this repository; it does not claim to be an external market forecast.

        **Open the dashboard:** [docs/index.html](docs/index.html)  
        **Detailed report:** [reports/ev_market_2026_report.md](reports/ev_market_2026_report.md)

        ## Executive Snapshot

        {markdown_table(["Metric", "Value"], kpi_rows)}

        ## Key Findings

        - **Sales concentration is high.** {top_brand["name"]} leads with {compact_number(top_brand["value"])} annual units, while the top three brands represent {pct(summary["top_three_brand_share"])} of all annual sales in the dataset.
        - **{top_segment["name"]} is the largest market segment by sales volume.** It accounts for {pct(top_segment["sales_share"])} of annual units with an average listed price of {money(top_segment["avg_price"])}.
        - **The model-level opportunity is not only price.** Range, charging speed, customer rating, and sales velocity vary widely, so the dashboard includes a price-vs-range view and sortable top-model tables.

        ## Charts

        ![Top brands by annual sales](docs/assets/top_brands_sales.svg)

        ![Market segment sales mix](docs/assets/market_segment_mix.svg)

        ![Price versus range scatter](docs/assets/price_range_scatter.svg)

        ![Country sales distribution](docs/assets/country_sales.svg)

        ## Brand Leaderboard

        {markdown_table(["Brand", "Annual sales", "Share"], brand_rows)}

        ## Segment Summary

        {markdown_table(["Segment", "Records", "Annual sales", "Share", "Avg price", "Avg range"], segment_rows)}

        ## Repository Structure

        - `docs/index.html` - interactive dashboard layer for GitHub Pages or local review.
        - `docs/assets/` - generated SVG charts used by this report.
        - `docs/data/` - generated JSON data and summary extracts.
        - `reports/ev_market_2026_report.md` - detailed professional write-up.
        - `scripts/build_report.py` - reproducible report and dashboard builder.

        ## Rebuild

        ```powershell
        python scripts/build_report.py
        ```

        Generated on {generated}.
        """
    )


def build_detail_report(summary: dict[str, Any]) -> str:
    top_model_rows = [
        [
            row["vehicle_label"],
            row["market_segment"],
            compact_number(row["annual_sales_units"]),
            money(row["price_usd"]),
            f"{row['range_miles']:.0f} mi",
            f"{row['customer_rating']:.2f}",
        ]
        for row in summary["top_models"][:10]
    ]
    value_rows = [
        [
            row["vehicle_label"],
            row["market_segment"],
            f"{row['value_index']:.2f}",
            money(row["price_usd"]),
            f"{row['range_miles']:.0f} mi",
            f"${row['price_per_mile']:.0f}/mi",
        ]
        for row in summary["value_leaders"][:10]
    ]
    range_rows = [
        [
            row["vehicle_label"],
            row["market_segment"],
            f"{row['range_miles']:.0f} mi",
            money(row["price_usd"]),
            f"{row['charging_speed_kw']:.0f} kW",
            compact_number(row["annual_sales_units"]),
        ]
        for row in summary["range_leaders"][:10]
    ]
    country_rows = [
        [
            item["name"],
            compact_number(item["value"]),
            pct(item["value"] / summary["total_sales_units"]),
            f"{item['records']:,}",
        ]
        for item in summary["country_sales"][:10]
    ]
    body_rows = [
        [
            item["name"],
            compact_number(item["value"]),
            pct(item["value"] / summary["total_sales_units"]),
            f"{item['records']:,}",
        ]
        for item in summary["body_sales"]
    ]
    segment_commentary = "\n".join(
        f"- **{item['name']}**: {compact_number(item['sales'])} annual units, "
        f"{pct(item['sales_share'])} share, {money(item['avg_price'])} average price, "
        f"{item['avg_range']:.0f} mile average range."
        for item in summary["segment_summary"]
    )

    return clean_markdown(
        f"""
        # EV Market 2026 Detailed Report

        ## Scope

        This report summarizes the local dataset [`ev_market_2026.csv`](../ev_market_2026.csv). The file contains {summary['record_count']:,} EV model records across {summary['brand_count']} brands and model years {summary['year_min']}-{summary['year_max']}. All metrics are calculated directly from the CSV.

        ## Executive Interpretation

        The dataset is strongly volume-led by a small set of brands. {summary['top_brand']['name']} is the largest single brand by annual sales, and the top three brands together hold {pct(summary['top_three_brand_share'])} of total annual units. Segment performance is led by {summary['top_segment']['name']}, but the price-vs-range scatter shows that models with similar range can sit in very different price bands.

        ## Segment Readout

        {segment_commentary}

        ## Top Models by Annual Sales

        {markdown_table(["Model", "Segment", "Annual sales", "Price", "Range", "Rating"], top_model_rows)}

        ## Value Leaders

        Value index = range miles per $1K of price, adjusted by customer rating. It is a quick screening metric, not a final investment score.

        {markdown_table(["Model", "Segment", "Value index", "Price", "Range", "Price/range"], value_rows)}

        ## Range Leaders

        {markdown_table(["Model", "Segment", "Range", "Price", "Charging speed", "Annual sales"], range_rows)}

        ## Country Distribution

        {markdown_table(["Country", "Annual sales", "Share", "Records"], country_rows)}

        ## Body Type Distribution

        {markdown_table(["Body type", "Annual sales", "Share", "Records"], body_rows)}

        ## Methodology

        - Parsed numeric fields from the CSV and calculated unweighted model averages for price, range, charging speed, rating, and safety score.
        - Calculated sales share using `annual_sales_units`.
        - Generated dashboard JSON and SVG charts with `scripts/build_report.py`.
        - Kept source data unchanged so every number can be audited back to the CSV.
        """
    )


def build_dashboard_html(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    data_json = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    template = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EV Market 2026 Dashboard</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --ink: #111827;
      --muted: #64748b;
      --line: #e5e7eb;
      --teal: #0f766e;
      --blue: #2563eb;
      --rose: #e11d48;
      --amber: #d97706;
      --violet: #7c3aed;
      --green: #059669;
      --radius: 8px;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      background: var(--bg);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      background:
        linear-gradient(180deg, #ffffff 0%, #f6f7f9 42%, #eef2f5 100%);
      min-height: 100vh;
    }

    header {
      padding: 24px clamp(16px, 4vw, 48px) 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(255, 255, 255, 0.92);
      position: sticky;
      top: 0;
      z-index: 5;
      backdrop-filter: blur(12px);
    }

    .topline {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: end;
      max-width: 1440px;
      margin: 0 auto;
    }

    h1 {
      margin: 0 0 6px;
      font-size: clamp(1.55rem, 2.4vw, 2.35rem);
      line-height: 1.12;
      letter-spacing: 0;
    }

    .subtitle {
      color: var(--muted);
      margin: 0;
      font-size: 0.96rem;
      line-height: 1.5;
    }

    .source {
      color: var(--muted);
      font-size: 0.82rem;
      text-align: right;
      white-space: nowrap;
    }

    main {
      max-width: 1440px;
      margin: 0 auto;
      padding: 22px clamp(16px, 4vw, 48px) 42px;
    }

    .filters {
      display: grid;
      grid-template-columns: repeat(4, minmax(160px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }

    label {
      display: grid;
      gap: 6px;
      color: #374151;
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      min-height: 42px;
      padding: 0 12px;
      background: var(--panel);
      color: var(--ink);
      font: inherit;
    }

    .kpis {
      display: grid;
      grid-template-columns: repeat(6, minmax(150px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }

    .kpi,
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: 0 8px 26px rgba(15, 23, 42, 0.04);
    }

    .kpi {
      padding: 14px;
      min-height: 104px;
      display: grid;
      align-content: space-between;
    }

    .kpi span {
      color: var(--muted);
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
      line-height: 1.25;
    }

    .kpi strong {
      font-size: clamp(1.26rem, 2vw, 1.8rem);
      line-height: 1.05;
      word-break: break-word;
    }

    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(360px, 0.8fr);
      gap: 14px;
      align-items: start;
    }

    .panel {
      padding: 16px;
      min-width: 0;
      overflow: hidden;
    }

    .panel h2 {
      margin: 0 0 4px;
      font-size: 1rem;
      letter-spacing: 0;
    }

    .panel p {
      margin: 0 0 12px;
      color: var(--muted);
      font-size: 0.86rem;
    }

    .chart {
      width: 100%;
      min-height: 330px;
    }

    .chart svg {
      width: 100%;
      height: auto;
      display: block;
    }

    .wide {
      grid-column: 1 / -1;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }

    th,
    td {
      padding: 10px 9px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }

    th {
      color: #374151;
      font-size: 0.74rem;
      text-transform: uppercase;
      background: #f8fafc;
    }

    td.num,
    th.num {
      text-align: right;
      white-space: nowrap;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      padding: 2px 8px;
      border-radius: 999px;
      background: #eef2ff;
      color: #3730a3;
      font-weight: 700;
      font-size: 0.78rem;
      white-space: nowrap;
    }

    @media (max-width: 1080px) {
      .filters {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }

      .kpis {
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }

      .grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 680px) {
      header {
        position: static;
      }

      .topline,
      .filters,
      .kpis {
        grid-template-columns: 1fr;
      }

      .source {
        text-align: left;
        white-space: normal;
      }

      main {
        padding-inline: 12px;
      }

      .panel {
        padding: 12px;
      }

      th:nth-child(4),
      td:nth-child(4),
      th:nth-child(5),
      td:nth-child(5) {
        display: none;
      }
    }
  </style>
</head>
<body>
  <header>
    <div class="topline">
      <div>
        <h1>EV Market 2026 Dashboard</h1>
        <p class="subtitle">Analysis of models, brands, segments, prices, range, and annual sales from the repository CSV.</p>
      </div>
      <div class="source">Source: ev_market_2026.csv<br>Generated: __GENERATED__</div>
    </div>
  </header>

  <main>
    <section class="filters" aria-label="Dashboard filters">
      <label>Segment
        <select id="segmentFilter"></select>
      </label>
      <label>Brand
        <select id="brandFilter"></select>
      </label>
      <label>Country
        <select id="countryFilter"></select>
      </label>
      <label>Year
        <select id="yearFilter"></select>
      </label>
    </section>

    <section class="kpis" aria-label="Key metrics">
      <article class="kpi"><span>Records</span><strong id="kpiRecords">-</strong></article>
      <article class="kpi"><span>Annual sales</span><strong id="kpiSales">-</strong></article>
      <article class="kpi"><span>Avg price</span><strong id="kpiPrice">-</strong></article>
      <article class="kpi"><span>Avg range</span><strong id="kpiRange">-</strong></article>
      <article class="kpi"><span>Avg charging</span><strong id="kpiCharge">-</strong></article>
      <article class="kpi"><span>Avg rating</span><strong id="kpiRating">-</strong></article>
    </section>

    <section class="grid">
      <article class="panel">
        <h2>Top brands by annual sales</h2>
        <p>Aggregated sales volume by selected filters.</p>
        <div id="brandChart" class="chart"></div>
      </article>
      <article class="panel">
        <h2>Market segment mix</h2>
        <p>Sales share by segment.</p>
        <div id="segmentChart" class="chart"></div>
      </article>
      <article class="panel wide">
        <h2>Price vs range</h2>
        <p>Each point is a vehicle record; size reflects annual sales.</p>
        <div id="scatterChart" class="chart"></div>
      </article>
      <article class="panel">
        <h2>Country distribution</h2>
        <p>Origin countries ranked by annual sales.</p>
        <div id="countryChart" class="chart"></div>
      </article>
      <article class="panel">
        <h2>Body type mix</h2>
        <p>Sales volume across body types.</p>
        <div id="bodyChart" class="chart"></div>
      </article>
      <article class="panel wide">
        <h2>Top model records</h2>
        <p>Highest annual sales after filters are applied.</p>
        <div style="overflow-x:auto">
          <table>
            <thead>
              <tr>
                <th>Model</th>
                <th>Segment</th>
                <th class="num">Sales</th>
                <th class="num">Price</th>
                <th class="num">Range</th>
                <th class="num">Rating</th>
              </tr>
            </thead>
            <tbody id="modelTable"></tbody>
          </table>
        </div>
      </article>
    </section>
  </main>

  <script id="dataset" type="application/json">__DATA_JSON__</script>
  <script>
    const DATA = JSON.parse(document.getElementById("dataset").textContent);
    const COLORS = ["#0f766e", "#2563eb", "#e11d48", "#d97706", "#7c3aed", "#059669", "#c2410c", "#0891b2", "#be123c", "#4f46e5"];
    const SEGMENT_COLORS = { "Budget": "#0f766e", "Mid-range": "#2563eb", "Premium": "#d97706", "Luxury": "#e11d48" };
    const nf = new Intl.NumberFormat("en-US");
    const moneyFmt = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

    const esc = (value) => String(value).replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    })[char]);

    const compact = (value) => {
      const abs = Math.abs(value);
      if (abs >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
      if (abs >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
      if (abs >= 1e3) return `${(value / 1e3).toFixed(1)}K`;
      return nf.format(Math.round(value));
    };

    const avg = (rows, field) => rows.length ? rows.reduce((sum, row) => sum + Number(row[field] || 0), 0) / rows.length : 0;
    const sum = (rows, field) => rows.reduce((total, row) => total + Number(row[field] || 0), 0);

    function groupSum(rows, field, valueField = "annual_sales_units") {
      const map = new Map();
      rows.forEach((row) => {
        const key = row[field];
        const current = map.get(key) || { name: key, value: 0, records: 0 };
        current.value += Number(row[valueField] || 0);
        current.records += 1;
        map.set(key, current);
      });
      return [...map.values()].sort((a, b) => b.value - a.value);
    }

    function populateSelect(id, values, label) {
      const select = document.getElementById(id);
      select.innerHTML = `<option value="">All ${label}</option>` + values
        .map((value) => `<option value="${esc(value)}">${esc(value)}</option>`)
        .join("");
      select.addEventListener("change", render);
    }

    function setupFilters() {
      populateSelect("segmentFilter", [...new Set(DATA.map((row) => row.market_segment))].sort(), "segments");
      populateSelect("brandFilter", [...new Set(DATA.map((row) => row.brand))].sort(), "brands");
      populateSelect("countryFilter", [...new Set(DATA.map((row) => row.country_of_origin))].sort(), "countries");
      populateSelect("yearFilter", [...new Set(DATA.map((row) => row.year))].sort((a, b) => a - b), "years");
    }

    function filteredRows() {
      const segment = document.getElementById("segmentFilter").value;
      const brand = document.getElementById("brandFilter").value;
      const country = document.getElementById("countryFilter").value;
      const year = document.getElementById("yearFilter").value;
      return DATA.filter((row) =>
        (!segment || row.market_segment === segment) &&
        (!brand || row.brand === brand) &&
        (!country || row.country_of_origin === country) &&
        (!year || String(row.year) === year)
      );
    }

    function barChart(targetId, data, options = {}) {
      const width = 900;
      const height = 340;
      const left = options.left || 150;
      const top = 20;
      const right = 72;
      const bottom = 42;
      const rows = data.slice(0, options.limit || 10);
      const maxValue = Math.max(1, ...rows.map((item) => item.value));
      const chartWidth = width - left - right;
      const chartHeight = height - top - bottom;
      const rowHeight = chartHeight / Math.max(rows.length, 1);
      const bars = rows.map((item, index) => {
        const y = top + index * rowHeight + 6;
        const barHeight = Math.max(16, rowHeight - 12);
        const barWidth = Math.max(2, (item.value / maxValue) * chartWidth);
        const color = options.colorMap?.[item.name] || COLORS[index % COLORS.length];
        return `
          <text x="${left - 12}" y="${y + barHeight / 2 + 5}" text-anchor="end" class="label">${esc(item.name)}</text>
          <rect x="${left}" y="${y}" width="${barWidth}" height="${barHeight}" rx="5" fill="${color}"></rect>
          <text x="${left + barWidth + 8}" y="${y + barHeight / 2 + 5}" class="value">${compact(item.value)}</text>
        `;
      }).join("");
      document.getElementById(targetId).innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" role="img">
          <style>
            .label{font:700 13px Arial,sans-serif;fill:#1f2937}
            .value{font:700 12px Arial,sans-serif;fill:#111827}
            .axis{font:12px Arial,sans-serif;fill:#64748b}
            .grid{stroke:#e5e7eb;stroke-width:1}
          </style>
          <line x1="${left}" x2="${left + chartWidth}" y1="${top + chartHeight}" y2="${top + chartHeight}" class="grid"></line>
          ${bars || `<text x="${width / 2}" y="${height / 2}" text-anchor="middle" class="axis">No records</text>`}
        </svg>
      `;
    }

    function arcPath(cx, cy, outerRadius, innerRadius, startAngle, endAngle) {
      const polar = (radius, angle) => {
        const radians = (angle - 90) * Math.PI / 180;
        return [cx + radius * Math.cos(radians), cy + radius * Math.sin(radians)];
      };
      const largeArc = endAngle - startAngle > 180 ? 1 : 0;
      const [osx, osy] = polar(outerRadius, endAngle);
      const [oex, oey] = polar(outerRadius, startAngle);
      const [isx, isy] = polar(innerRadius, startAngle);
      const [iex, iey] = polar(innerRadius, endAngle);
      return `M ${osx} ${osy} A ${outerRadius} ${outerRadius} 0 ${largeArc} 0 ${oex} ${oey} L ${isx} ${isy} A ${innerRadius} ${innerRadius} 0 ${largeArc} 1 ${iex} ${iey} Z`;
    }

    function donutChart(targetId, data) {
      const width = 440;
      const height = 340;
      const cx = 160;
      const cy = 170;
      const outer = 118;
      const inner = 66;
      const total = Math.max(1, data.reduce((sumValue, item) => sumValue + item.value, 0));
      let angle = 0;
      const paths = data.map((item, index) => {
        const sweep = item.value / total * 360;
        const color = SEGMENT_COLORS[item.name] || COLORS[index % COLORS.length];
        const path = `<path d="${arcPath(cx, cy, outer, inner, angle, angle + sweep)}" fill="${color}"></path>`;
        angle += sweep;
        return path;
      }).join("");
      const legend = data.map((item, index) => {
        const color = SEGMENT_COLORS[item.name] || COLORS[index % COLORS.length];
        const y = 76 + index * 44;
        return `
          <rect x="310" y="${y}" width="14" height="14" rx="4" fill="${color}"></rect>
          <text x="332" y="${y + 12}" class="legend">${esc(item.name)}</text>
          <text x="332" y="${y + 30}" class="muted">${compact(item.value)} | ${((item.value / total) * 100).toFixed(1)}%</text>
        `;
      }).join("");
      document.getElementById(targetId).innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" role="img">
          <style>
            .center{font:800 24px Arial,sans-serif;fill:#111827}
            .muted{font:12px Arial,sans-serif;fill:#64748b}
            .legend{font:700 13px Arial,sans-serif;fill:#1f2937}
          </style>
          ${paths}
          <text x="${cx}" y="${cy - 4}" text-anchor="middle" class="center">${compact(total)}</text>
          <text x="${cx}" y="${cy + 18}" text-anchor="middle" class="muted">units</text>
          ${legend}
        </svg>
      `;
    }

    function scatterChart(targetId, rows) {
      const width = 900;
      const height = 380;
      const left = 72;
      const top = 20;
      const right = 24;
      const bottom = 48;
      const chartWidth = width - left - right;
      const chartHeight = height - top - bottom;
      const xVals = rows.map((row) => Number(row.range_miles));
      const yVals = rows.map((row) => Number(row.price_usd));
      const salesVals = rows.map((row) => Number(row.annual_sales_units));
      const minX = Math.min(...xVals);
      const maxX = Math.max(...xVals);
      const minY = Math.min(...yVals);
      const maxY = Math.max(...yVals);
      const minSales = Math.min(...salesVals);
      const maxSales = Math.max(...salesVals);
      const scaleX = (value) => left + ((value - minX) / Math.max(1, maxX - minX)) * chartWidth;
      const scaleY = (value) => top + chartHeight - ((value - minY) / Math.max(1, maxY - minY)) * chartHeight;
      const radius = (value) => 2.4 + Math.sqrt((value - minSales) / Math.max(1, maxSales - minSales)) * 7;
      const grid = Array.from({ length: 5 }, (_, index) => {
        const xValue = minX + (maxX - minX) * index / 4;
        const yValue = minY + (maxY - minY) * index / 4;
        const x = scaleX(xValue);
        const y = scaleY(yValue);
        return `
          <line x1="${x}" y1="${top}" x2="${x}" y2="${top + chartHeight}" class="grid"></line>
          <text x="${x}" y="${height - 16}" text-anchor="middle" class="axis">${xValue.toFixed(0)}</text>
          <line x1="${left}" y1="${y}" x2="${left + chartWidth}" y2="${y}" class="grid"></line>
          <text x="${left - 10}" y="${y + 4}" text-anchor="end" class="axis">${moneyFmt.format(yValue / 1000)}K</text>
        `;
      }).join("");
      const circles = rows.map((row) => {
        const color = SEGMENT_COLORS[row.market_segment] || "#64748b";
        return `<circle cx="${scaleX(Number(row.range_miles))}" cy="${scaleY(Number(row.price_usd))}" r="${radius(Number(row.annual_sales_units))}" fill="${color}" opacity="0.34"><title>${esc(row.vehicle_label)} | ${moneyFmt.format(row.price_usd)} | ${row.range_miles} mi</title></circle>`;
      }).join("");
      document.getElementById(targetId).innerHTML = `
        <svg viewBox="0 0 ${width} ${height}" role="img">
          <style>
            .grid{stroke:#e5e7eb;stroke-width:1}
            .axis{font:12px Arial,sans-serif;fill:#64748b}
            .title{font:700 12px Arial,sans-serif;fill:#374151}
          </style>
          ${grid}
          ${circles || `<text x="${width / 2}" y="${height / 2}" text-anchor="middle" class="axis">No records</text>`}
          <text x="${left + chartWidth / 2}" y="${height - 2}" text-anchor="middle" class="title">Range miles</text>
        </svg>
      `;
    }

    function renderTable(rows) {
      const topRows = [...rows].sort((a, b) => b.annual_sales_units - a.annual_sales_units).slice(0, 12);
      document.getElementById("modelTable").innerHTML = topRows.map((row) => `
        <tr>
          <td><strong>${esc(row.vehicle_label)}</strong><br><span style="color:#64748b">${esc(row.drive_type)} · ${esc(row.body_type)}</span></td>
          <td><span class="pill">${esc(row.market_segment)}</span></td>
          <td class="num">${compact(row.annual_sales_units)}</td>
          <td class="num">${moneyFmt.format(row.price_usd)}</td>
          <td class="num">${nf.format(Math.round(row.range_miles))} mi</td>
          <td class="num">${Number(row.customer_rating).toFixed(2)}</td>
        </tr>
      `).join("") || `<tr><td colspan="6">No records match the current filters.</td></tr>`;
    }

    function render() {
      const rows = filteredRows();
      document.getElementById("kpiRecords").textContent = nf.format(rows.length);
      document.getElementById("kpiSales").textContent = compact(sum(rows, "annual_sales_units"));
      document.getElementById("kpiPrice").textContent = moneyFmt.format(avg(rows, "price_usd"));
      document.getElementById("kpiRange").textContent = `${avg(rows, "range_miles").toFixed(0)} mi`;
      document.getElementById("kpiCharge").textContent = `${avg(rows, "charging_speed_kw").toFixed(1)} kW`;
      document.getElementById("kpiRating").textContent = `${avg(rows, "customer_rating").toFixed(2)}/5`;
      barChart("brandChart", groupSum(rows, "brand"), { limit: 10 });
      donutChart("segmentChart", groupSum(rows, "market_segment"));
      scatterChart("scatterChart", rows);
      barChart("countryChart", groupSum(rows, "country_of_origin"), { limit: 8, left: 138 });
      barChart("bodyChart", groupSum(rows, "body_type"), { limit: 8, left: 138 });
      renderTable(rows);
    }

    setupFilters();
    render();
  </script>
</body>
</html>
"""
    return template.replace("__DATA_JSON__", data_json).replace("__GENERATED__", generated)


def main() -> None:
    ensure_dirs()
    rows = parse_rows()
    summary = compute_summary(rows)

    write_bar_svg(
        ASSETS_DIR / "top_brands_sales.svg",
        summary["brand_sales"][:10],
        "Top brands by annual sales",
        "Aggregated annual_sales_units by brand",
        compact_number,
    )
    write_donut_svg(
        ASSETS_DIR / "market_segment_mix.svg",
        [
            {"name": item["name"], "value": item["sales"], "records": item["records"]}
            for item in summary["segment_summary"]
        ],
        "Market segment sales mix",
        "Share of annual_sales_units by segment",
    )
    write_scatter_svg(
        ASSETS_DIR / "price_range_scatter.svg",
        rows,
        "Price vs range by segment",
        "Point size represents annual sales units",
    )
    write_bar_svg(
        ASSETS_DIR / "country_sales.svg",
        summary["country_sales"][:10],
        "Country distribution by annual sales",
        "Aggregated annual_sales_units by country of origin",
        compact_number,
    )
    write_data_files(rows, summary)
    (ROOT / "README.md").write_text(build_readme(summary), encoding="utf-8")
    (REPORTS_DIR / "ev_market_2026_report.md").write_text(
        build_detail_report(summary), encoding="utf-8"
    )
    (DOCS_DIR / "index.html").write_text(
        build_dashboard_html(rows, summary), encoding="utf-8"
    )

    print(f"Built report for {len(rows):,} rows.")
    print(f"Dashboard: {DOCS_DIR / 'index.html'}")
    print(f"Report: {ROOT / 'README.md'}")


if __name__ == "__main__":
    main()
