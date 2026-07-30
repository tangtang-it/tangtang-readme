#!/usr/bin/env python3
"""糖糖it 动画 GIF 渲染工具 — 将命名 SVG 图层渲染为紧凑的 GitHub 安全动画 GIF。"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from PIL import Image, ImageChops
except ImportError as exc:
    raise SystemExit("需要 Pillow 库: python3 -m pip install Pillow") from exc


SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="糖糖it GIF 渲染器：从 JSON 动效规格将命名 SVG 图层编码为动画 GIF。"
    )
    parser.add_argument("input_svg", type=Path, help="输入 SVG 文件路径")
    parser.add_argument("output_gif", type=Path, help="输出 GIF 文件路径")
    parser.add_argument("--spec", required=True, type=Path, help="JSON 动效规格文件")
    parser.add_argument(
        "--keep-frames",
        type=Path,
        help="将渲染的图层和 PNG 帧保留在此目录中（新建或空目录）",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(f"🍬 错误: {message}")


def load_spec(path: Path) -> dict:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"找不到动效规格文件: {path}")
    except json.JSONDecodeError as exc:
        fail(f"动效规格 JSON 无效: {exc}")

    defaults = {
        "width": 1200,
        "fps": 30,
        "duration": 5.0,
        "colors": 192,
        "dither": "none",
        "transparent_color": "#ff00ff",
        "alpha_threshold": 128,
        "clip_to_base_alpha": False,
        "max_size_mb": 2.0,
        "reveals": [],
        "layers": [],
    }
    defaults.update(spec)
    return defaults


def validate_spec(spec: dict) -> None:
    if not 1 <= int(spec["fps"]) <= 60:
        fail("帧率 fps 必须在 1-60 之间")
    if float(spec["duration"]) <= 0:
        fail("时长 duration 必须为正数")
    if int(spec["width"]) <= 0:
        fail("宽度 width 必须为正数")
    if not 2 <= int(spec["colors"]) <= 256:
        fail("颜色数 colors 必须在 2-256 之间")
    if float(spec["max_size_mb"]) <= 0:
        fail("最大文件大小 max_size_mb 必须为正数")


def check_resvg() -> str:
    """检查 resvg 或其他 SVG 渲染工具是否可用。"""
    for tool in ["resvg", "rsvg-convert", "inkscape"]:
        path = shutil.which(tool)
        if path:
            return tool
    return None


def render_svg_to_png(svg_path: Path, png_path: Path, width: int, tool: str) -> None:
    """将 SVG 渲染为 PNG。"""
    if tool == "resvg":
        cmd = ["resvg", "-w", str(width), str(svg_path), str(png_path)]
    elif tool == "rsvg-convert":
        cmd = ["rsvg-convert", "-w", str(width), "-o", str(png_path), str(svg_path)]
    elif tool == "inkscape":
        cmd = ["inkscape", str(svg_path), f"--export-width={width}", "--export-filename", str(png_path)]
    else:
        # 如果没有工具，尝试用 cairosvg
        try:
            import cairosvg
            cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=width)
            return
        except ImportError:
            fail(
                "未找到 SVG 渲染工具。请安装 resvg、librsvg2 (rsvg-convert)、Inkscape 或 cairosvg:\n"
                "  - 推荐: cargo install resvg\n"
                "  - 或 pip install cairosvg"
            )

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        fail(f"SVG 渲染失败 ({tool}): {exc.stderr.decode() if exc.stderr else exc}")
    except FileNotFoundError:
        fail(f"找不到渲染工具: {tool}")


def set_layer_visibility(root: ET.Element, visible_layers: set[str]) -> None:
    """设置指定图层可见，其他隐藏。"""
    ns = {"svg": SVG_NS}
    # 处理带 id 的 g 元素作为图层
    for g in root.iter(f"{{{SVG_NS}}}g"):
        layer_id = g.get("id", "")
        if layer_id in visible_layers:
            if "style" in g.attrib:
                style = g.attrib["style"].replace("display:none", "").replace("display: none", "")
                g.attrib["style"] = style.strip(";") + ";display:inline"
            else:
                g.attrib["style"] = "display:inline"
        elif layer_id and any(spec.get("layer") == layer_id for spec in []):
            pass  # 不在目标集合中的命名图层保持原样


def generate_frames(spec: dict, input_svg: Path, frames_dir: Path, tool: str) -> list[Path]:
    """根据规格生成所有帧。"""
    tree = ET.parse(input_svg)
    root = tree.getroot()

    total_frames = int(spec["fps"] * spec["duration"])
    frame_paths = []

    base_layers = set()
    for layer_spec in spec.get("layers", []):
        if layer_spec.get("base", False):
            base_layers.add(layer_spec["name"])

    for i in range(total_frames):
        t = i / spec["fps"]
        visible = set(base_layers)

        # 处理 reveals: 在指定时间后显示图层
        for reveal in spec.get("reveals", []):
            start = reveal.get("start", 0)
            duration = reveal.get("duration", 0)
            layer = reveal.get("layer", "")
            if t >= start:
                if duration == 0 or t <= start + duration:
                    visible.add(layer)

        # 创建当前帧的 SVG
        frame_tree = copy.deepcopy(tree)
        frame_root = frame_tree.getroot()
        set_layer_visibility(frame_root, visible)

        frame_svg = frames_dir / f"frame_{i:04d}.svg"
        frame_tree.write(frame_svg, encoding="utf-8", xml_declaration=True)

        # 渲染为 PNG
        frame_png = frames_dir / f"frame_{i:04d}.png"
        render_svg_to_png(frame_svg, frame_png, spec["width"], tool)
        frame_paths.append(frame_png)

    return frame_paths


def create_gif(frame_paths: list[Path], output: Path, spec: dict) -> None:
    """将帧序列合并为 GIF。"""
    if not frame_paths:
        fail("没有帧可用于生成 GIF")

    frames = []
    duration_ms = int(1000 / spec["fps"])

    for fp in frame_paths:
        img = Image.open(fp).convert("RGBA")
        # 处理透明背景
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        background.paste(img, mask=img.split()[3])
        frames.append(background.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=spec["colors"]))

    # 保存 GIF
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
        disposal=2,
    )

    # 检查文件大小
    size_mb = output.stat().st_size / (1024 * 1024)
    if size_mb > spec["max_size_mb"]:
        print(f"⚠️  警告: GIF 文件大小为 {size_mb:.2f}MB，超过推荐上限 {spec['max_size_mb']}MB")
        print("   建议: 减少 duration、降低 fps、减少 colors、或缩短循环")


def main() -> int:
    args = parse_args()

    print("🍬 糖糖it GIF 动画渲染器")
    print(f"输入 SVG: {args.input_svg}")
    print(f"输出 GIF: {args.output_gif}")
    print(f"动效规格: {args.spec}")

    if not args.input_svg.is_file():
        fail(f"找不到输入 SVG: {args.input_svg}")

    spec = load_spec(args.spec)
    validate_spec(spec)

    print(f"参数: {spec['fps']}fps, {spec['duration']}s, {spec['width']}px宽, {spec['colors']}色")

    tool = check_resvg()
    if tool:
        print(f"渲染工具: {tool}")
    else:
        print("渲染工具: cairosvg (内置)")

    with tempfile.TemporaryDirectory() as tmpdir:
        frames_dir = Path(tmpdir) / "frames"
        frames_dir.mkdir()

        if args.keep_frames:
            args.keep_frames.mkdir(parents=True, exist_ok=True)
            frames_dir = args.keep_frames / "frames"
            frames_dir.mkdir(exist_ok=True)

        print("正在渲染帧...")
        frame_paths = generate_frames(spec, args.input_svg, frames_dir, tool)
        print(f"已生成 {len(frame_paths)} 帧")

        print("正在编码 GIF...")
        create_gif(frame_paths, args.output_gif, spec)

    size_mb = args.output_gif.stat().st_size / (1024 * 1024)
    print(f"✅ 完成! 输出: {args.output_gif} ({size_mb:.2f}MB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())