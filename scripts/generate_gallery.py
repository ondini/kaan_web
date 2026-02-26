from pathlib import Path
import json
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
IMAGES_DIR = ROOT_DIR / "assets" / "images"
OUTPUT_FILE = IMAGES_DIR / "gallery.json"
ORDER_FILE = IMAGES_DIR / "img_order.txt"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


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
    if "/" in entry:
        folder, filename = entry.split("/", 1)
        if folder in categories:
            if filename in categories[folder]:
                return f"{folder}/{filename}"
            matches = [file for file in categories[folder] if Path(file).stem == filename]
            if len(matches) == 1:
                return f"{folder}/{matches[0]}"
        return None

    matches = []
    for folder, files in categories.items():
        if entry in files:
            matches.append(f"{folder}/{entry}")
            continue
        for file in files:
            if Path(file).stem == entry:
                matches.append(f"{folder}/{file}")

    if len(matches) == 1:
        return matches[0]
    return None

def main() -> None:
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
