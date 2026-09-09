#!/usr/bin/env python3
"""Build a portable plugin ZIP. No upload, credentials, runtime, or local preferences."""
import argparse
import json
from pathlib import Path
import zipfile


def package(output_dir):
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"{manifest['name']}-{manifest['version']}.zip"
    entries = [".codex-plugin", ".mcp.json", "skills", "scripts", "docs", "README.md", "LICENSE",
               "THIRD_PARTY_NOTICES.md", "VALIDATION.md"]
    files = []
    for entry in entries:
        path = root / entry
        if not path.exists():
            raise FileNotFoundError(f"Missing release component: {entry}")
        for item in sorted(path.rglob("*") if path.is_dir() else [path]):
            relative = item.relative_to(root)
            if not item.is_file() or "__pycache__" in relative.parts:
                continue
            if item.name == "preferences.json" or item.suffix == ".pyc":
                continue
            files.append((item, relative.as_posix()))
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for item, relative in files:
            archive.write(item, relative)
    return {"archive": str(target), "files": len(files), "size_bytes": target.stat().st_size,
            "uploaded": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory")
    print(json.dumps(package(parser.parse_args().output_directory), indent=2))
