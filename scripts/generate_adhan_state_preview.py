#!/usr/bin/env python3
import os


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
source_path = os.path.join(
    project_root,
    "prayerclock-preview-v25-monday-thursday-fasting-dedup.svg",
)
target_path = os.path.join(project_root, "prayerclock-adhan-state-preview.svg")

with open(source_path, encoding="utf-8") as source_file:
    svg = source_file.read()

svg = svg.replace(
    '<text x="298" y="70" fill="#8fcfc5" font-size="10" font-weight="700">AKTUELL</text>',
    '<text x="298" y="70" fill="#f1d686" font-size="10" font-weight="700">ADHĀN · MAGHRIB</text>',
)
svg = svg.replace(
    '<text x="51" y="318" fill="#80959b" font-size="11" font-weight="700">NÄCHSTES GEBET · DHUHR</text>',
    '<text x="51" y="318" fill="#d8bd70" font-size="11" font-weight="700">ADHĀN WIRD GESPROCHEN · MAGHRIB</text>',
)
svg = svg.replace(
    '<g transform="translate(510 181) scale(1.11)" fill="none">',
    """<g transform="translate(510 181)" fill="none" stroke="#ffe9aa">
      <circle r="77" opacity=".48"><animate attributeName="r" values="73;79;75;82;73" dur="4.8s" repeatCount="indefinite"/><animate attributeName="opacity" values=".2;.62;.28;.72;.2" dur="4.8s" repeatCount="indefinite"/></circle>
      <circle r="84" opacity=".22"><animate attributeName="r" values="80;87;82;90;80" dur="4.8s" repeatCount="indefinite"/><animate attributeName="opacity" values=".08;.35;.14;.42;.08" dur="4.8s" repeatCount="indefinite"/></circle>
    </g>
    <g transform="translate(510 181) scale(1.11)" fill="none">
      <animateTransform attributeName="transform" additive="sum" type="scale" values="1;1.035;1.012;1.05;1" dur="4.8s" repeatCount="indefinite"/>""",
)

with open(target_path, "w", encoding="utf-8") as target_file:
    target_file.write(svg)

print(target_path)
