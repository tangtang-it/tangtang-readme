#!/usr/bin/env python3
"""糖糖it README 审计工具 — 检查本地 README 图片引用和 SVG 基础兼容性。"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


MARKDOWN_IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
HTML_IMAGE = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.I)
HTML_ALT = re.compile(r"\balt=[\"']([^\"']*)[\"']", re.I)
UNSAFE_SVG_TAGS = {"script", "foreignObject"}


def local_target(src: str, base: Path) -> Path | None:
    if src.startswith(("http://", "https://", "data:", "#")):
        return None
    clean = src.split("#", 1)[0].split("?", 1)[0]
    return (base / clean).resolve()


def audit_svg(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [f"无效的 SVG XML: {exc}"]

    if "viewBox" not in root.attrib:
        issues.append("缺少 viewBox 属性")

    title_found = False
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "title":
            title_found = True
        if tag in UNSAFE_SVG_TAGS:
            issues.append(f"包含 GitHub 不支持的 <{tag}> 标签")
    if not title_found:
        issues.append("缺少 <title> 标签（无障碍访问）")
    return issues


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: audit_readme.py /path/to/README.md", file=sys.stderr)
        return 2

    readme = Path(sys.argv[1]).expanduser().resolve()
    if not readme.is_file():
        print(f"错误：找不到 README 文件: {readme}")
        return 2

    text = readme.read_text(encoding="utf-8")
    sources = MARKDOWN_IMAGE.findall(text)
    html_tags = re.findall(r"<img\b[^>]*>", text, flags=re.I)
    sources.extend(HTML_IMAGE.findall(text))

    warnings: list[str] = []
    for tag in html_tags:
        match = HTML_ALT.search(tag)
        if not match or not match.group(1).strip():
            warnings.append(f"HTML 图片缺少有效的 alt 文本: {tag[:100]}")

    checked = 0
    for src in dict.fromkeys(sources):
        target = local_target(src, readme.parent)
        if target is None:
            continue
        checked += 1
        if not target.is_file():
            warnings.append(f"图片不存在: {src}")
            continue
        if target.suffix.lower() == ".svg":
            for issue in audit_svg(target):
                warnings.append(f"{src}: {issue}")

    print(f"🍬 糖糖it README 审计工具")
    print(f"README: {readme}")
    print(f"检查本地图片: {checked} 个")
    if warnings:
        print("\n发现问题：")
        for warning in warnings:
            print(f"  - {warning}")
        return 1
    print("✅ 通过：图片引用和 SVG 基础检查没问题！")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())