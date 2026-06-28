from pathlib import Path
import json
import platform
import shutil
import subprocess
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
IMAGES_DIR = ROOT_DIR / "assets" / "images"
OUTPUT_FILE = IMAGES_DIR / "gallery.json"
ORDER_FILE = IMAGES_DIR / "img_order.txt"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def convert_pngs_to_webp() -> None:
    """Convert PNG images to WebP and remove original PNG files."""
    is_macos = platform.system() == "Darwin"
    if is_macos:
        image_converter = shutil.which("magick") or shutil.which("convert")
        if not image_converter:
            raise RuntimeError(
                "ImageMagick is required on macOS but was not found in PATH"
            )
    else:
        image_converter = shutil.which("ffmpeg")
        if not image_converter:
            raise RuntimeError("ffmpeg is required but was not found in PATH")

    for folder in sorted(IMAGES_DIR.iterdir()):
        if not folder.is_dir():
            continue

        for png_file in sorted(folder.glob("*.png")):
            webp_file = png_file.with_suffix(".webp")
            if is_macos:
                cmd = [
                    image_converter,
                    str(png_file),
                    "-resize",
                    "2000x",
                    "-quality",
                    "96",
                    str(webp_file),
                ]
            else:
                cmd = [
                    image_converter,
                    "-i",
                    str(png_file),
                    "-vf",
                    "scale=2000:-1",
                    "-compression_level",
                    "3",
                    "-q:v",
                    "96",
                    str(webp_file),
                ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    f"Failed to convert {png_file} to WebP:\n{result.stderr.strip()}"
                )

            png_file.unlink()
            print(f"Converted {png_file.name} -> {webp_file.name}")


def read_order_file() -> list[tuple[str, str]]:
    """Read order file and return list of (basename, description) tuples."""
    if not ORDER_FILE.exists():
        return []

    entries = []
    for raw_line in ORDER_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        
        # Parse format: "basename - description"
        if " - " in line:
            parts = line.split(" - ", 1)
            basename = parts[0].strip()
            description = parts[1].strip()
        else:
            basename = line.strip()
            description = ""
        
        entries.append((basename, description))
    return entries


def normalize_order_entry(entry: str, categories: dict[str, list[str]]) -> Optional[str]:
    entry_stem = Path(entry).stem

    if "/" in entry:
        folder, filename = entry.split("/", 1)
        filename_stem = Path(filename).stem
        if folder in categories:
            if filename in categories[folder]:
                return f"{folder}/{filename}"
            matches = [
                file
                for file in categories[folder]
                if Path(file).stem == filename or Path(file).stem == filename_stem
            ]
            if len(matches) == 1:
                return f"{folder}/{matches[0]}"
        return None

    matches = []
    for folder, files in categories.items():
        if entry in files:
            matches.append(f"{folder}/{entry}")
            continue
        for file in files:
            if Path(file).stem == entry or Path(file).stem == entry_stem:
                matches.append(f"{folder}/{file}")

    if len(matches) == 1:
        return matches[0]
    return None

def main() -> None:
    convert_pngs_to_webp()

    categories = {}
    for folder in sorted(IMAGES_DIR.iterdir()):
        if not folder.is_dir():
            continue
        files = sorted(
            [
                p.name
                for p in folder.iterdir()
                if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
            ]
        )
        if files:
            categories[folder.name] = files

    order_entries = read_order_file()
    home_order = []
    descriptions = {}
    
    for basename, description in order_entries:
        normalized = normalize_order_entry(basename, categories)
        print(f"Normalized '{basename}' to '{normalized}' with description '{description}'")
        if normalized:
            home_order.append(normalized)
            if description:
                descriptions[normalized] = description

    data = {
        "categories": categories,
        "homeOrder": home_order,
        "descriptions": descriptions
    }
    OUTPUT_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
