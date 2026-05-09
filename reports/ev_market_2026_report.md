# EV Market 2026 Detailed Report

## Scope

This report summarizes the local dataset [`ev_market_2026.csv`](../ev_market_2026.csv). The file contains 2,000 EV model records across 20 brands and model years 2020-2026. All metrics are calculated directly from the CSV.

## Executive Interpretation

The dataset is strongly volume-led by a small set of brands. Tesla is the largest single brand by annual sales, and the top three brands together hold 77.2% of total annual units. Segment performance is led by Premium, but the price-vs-range scatter shows that models with similar range can sit in very different price bands.

## Segment Readout

- **Premium**: 86.5M annual units, 33.4% share, $81,102 average price, 264 mile average range.
- **Mid-range**: 83.5M annual units, 32.2% share, $50,689 average price, 255 mile average range.
- **Luxury**: 66.0M annual units, 25.4% share, $127,340 average price, 275 mile average range.
- **Budget**: 23.4M annual units, 9.0% share, $29,321 average price, 236 mile average range.

## Top Models by Annual Sales

| Model | Segment | Annual sales | Price | Range | Rating |
| --- | --- | --- | --- | --- | --- |
| Tesla Model Y Standard (2025) | Premium | 499.7K | $85,878 | 188 mi | 3.42 |
| Tesla Model Y Long Range (2020) | Premium | 498.0K | $96,391 | 287 mi | 3.82 |
| Tesla Model Y Long Range (2024) | Premium | 497.6K | $85,409 | 338 mi | 4.06 |
| Tesla Model Y Long Range (2022) | Luxury | 494.9K | $112,383 | 270 mi | 3.77 |
| Tesla Model Y Base (2023) | Premium | 491.5K | $92,950 | 263 mi | 3.57 |
| Tesla Model Y Performance (2024) | Luxury | 490.7K | $141,349 | 409 mi | 4.51 |
| Tesla Model Y Standard (2023) | Mid-range | 490.5K | $53,432 | 289 mi | 3.93 |
| Tesla Model Y Long Range (2026) | Premium | 490.4K | $83,728 | 280 mi | 3.83 |
| Tesla Model Y Standard (2026) | Premium | 489.1K | $78,088 | 245 mi | 3.77 |
| Tesla Model Y Standard (2026) | Mid-range | 488.6K | $40,007 | 241 mi | 3.74 |

## Value Leaders

Value index = range miles per $1K of price, adjusted by customer rating. It is a quick screening metric, not a final investment score.

| Model | Segment | Value index | Price | Range | Price/range |
| --- | --- | --- | --- | --- | --- |
| BYD Atto 3 Performance (2026) | Budget | 11.28 | $31,933 | 430 mi | $74/mi |
| BYD Qin Base (2024) | Budget | 11.15 | $17,777 | 280 mi | $63/mi |
| BYD Leaf 50X Performance (2023) | Budget | 10.46 | $25,921 | 344 mi | $75/mi |
| BYD Seagull Base (2024) | Budget | 10.40 | $19,471 | 291 mi | $67/mi |
| BYD Qin Long Range (2023) | Budget | 10.24 | $27,058 | 385 mi | $70/mi |
| BYD Atto 3 Long Range (2024) | Budget | 10.15 | $25,254 | 355 mi | $71/mi |
| BYD Atto 3 Long Range (2025) | Budget | 9.87 | $26,098 | 367 mi | $71/mi |
| BYD Dolphin Long Range (2025) | Budget | 9.78 | $24,263 | 313 mi | $78/mi |
| BYD Seagull Base (2024) | Budget | 9.62 | $16,613 | 237 mi | $70/mi |
| BYD Qin Standard (2024) | Budget | 9.53 | $21,712 | 307 mi | $71/mi |

## Range Leaders

| Model | Segment | Range | Price | Charging speed | Annual sales |
| --- | --- | --- | --- | --- | --- |
| Volkswagen ID.4 Performance (2025) | Premium | 447 mi | $80,550 | 160 kW | 291.7K |
| Kia Picanto EV Performance (2020) | Mid-range | 444 mi | $51,182 | 158 kW | 106.5K |
| GM/Chevrolet Silverado EV Performance (2026) | Premium | 439 mi | $65,285 | 241 kW | 25.7K |
| Hyundai Ioniq 6 Performance (2025) | Luxury | 434 mi | $107,109 | 239 kW | 92.3K |
| Tesla Model S Performance (2024) | Mid-range | 433 mi | $64,261 | 323 kW | 145.5K |
| BYD Seagull Performance (2024) | Luxury | 431 mi | $117,282 | 194 kW | 111.1K |
| BYD Atto 3 Performance (2026) | Budget | 430 mi | $31,933 | 171 kW | 219.1K |
| Rivian R2 Performance (2025) | Luxury | 429 mi | $104,305 | 159 kW | 26.2K |
| Tesla Cybertruck Performance (2025) | Luxury | 428 mi | $116,078 | 234 kW | 150.7K |
| BMW i3 Performance (2024) | Luxury | 428 mi | $123,236 | 188 kW | 49.5K |

## Country Distribution

| Country | Annual sales | Share | Records |
| --- | --- | --- | --- |
| US | 110.9M | 42.8% | 774 |
| Germany | 64.7M | 24.9% | 531 |
| China | 51.0M | 19.7% | 313 |
| South Korea | 31.8M | 12.3% | 318 |
| Japan | 621.0K | 0.2% | 43 |
| Sweden | 270.6K | 0.1% | 21 |

## Body Type Distribution

| Body type | Annual sales | Share | Records |
| --- | --- | --- | --- |
| Truck | 58.5M | 22.6% | 427 |
| Hatchback | 42.8M | 16.5% | 324 |
| Coupe | 41.6M | 16.1% | 303 |
| Sedan | 41.2M | 15.9% | 301 |
| SUV | 39.4M | 15.2% | 364 |
| Van | 35.8M | 13.8% | 281 |

## Methodology

- Parsed numeric fields from the CSV and calculated unweighted model averages for price, range, charging speed, rating, and safety score.
- Calculated sales share using `annual_sales_units`.
- Generated dashboard JSON and SVG charts with `scripts/build_report.py`.
- Kept source data unchanged so every number can be audited back to the CSV.
