#!/usr/bin/env python3
"""
Generate per-resource Maestro flows from the live mobile-content-api catalog.

Output: .maestro/flows/generated/<type>/<abbreviation>.yaml

Each generated flow:
  - Opens the resource via godtools://.../tool/<type>/<abbrev>/en
  - Asserts the real catalog name appears
  - Asserts the real catalog description fragment appears (when assertable)
  - Walks every page in the manifest, screenshotting each one
  - Backs out via Home/back

Run:
    python3 .maestro/scripts/generate_flows.py [--api stage|prod] [--lang en]

Requires: requests (pip install requests). Or use stdlib urllib fallback.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAESTRO_DIR = ROOT / ".maestro"
GENERATED_DIR = MAESTRO_DIR / "flows" / "generated"
APP_ID = "org.cru.godtools.beta"
DEEP_LINK_HOST = "godtools://org.cru.godtools"

API_BY_ENV = {
    "stage": "https://mobile-content-api-stage.cru.org",
    "prod": "https://mobile-content-api.cru.org",
}

MANIFEST_NS = "https://mobile-content-api.cru.org/xmlns/manifest"


def http_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def http_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8")


def fetch_resources(api: str) -> dict:
    qs = urllib.parse.urlencode({
        "filter[system]": "GodTools",
        "include": "latest-translations,attachments",
    })
    return http_json(f"{api}/resources?{qs}")


def english_id(api: str) -> str:
    langs = http_json(f"{api}/languages")
    for entry in langs["data"]:
        if entry["attributes"]["code"] == "en":
            return entry["id"]
    raise RuntimeError("English language id not found")


def yaml_str(s: str) -> str:
    """Quote a string safely for YAML and clamp length."""
    if s is None:
        return '""'
    s = s.replace("\r", " ").replace("\n", " ").strip()
    s = re.sub(r"\s+", " ", s)
    s = s[:120]
    return json.dumps(s, ensure_ascii=False)


def parse_manifest_pages(xml_text: str) -> list[str]:
    """Return ordered list of page filenames from a tract/lesson manifest."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    ns = {"m": MANIFEST_NS}
    return [p.get("filename", f"page-{i}") for i, p in enumerate(root.findall("m:pages/m:page", ns))]


def slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "page"


def emit_flow(resource: dict, translation: dict | None, manifest_pages: list[str]) -> tuple[Path, str]:
    attrs = resource["attributes"]
    abbrev = attrs["abbreviation"]
    rtype = attrs["resource-type"]
    name = (translation["attributes"].get("translated-name") if translation else None) or attrs.get("name", "")
    description = (translation["attributes"].get("translated-description") if translation else None) or attrs.get("description", "") or ""
    description_lead = description.split(".")[0].strip() if description else ""

    out_dir = GENERATED_DIR / rtype
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{abbrev}.yaml"

    deeplink = f"{DEEP_LINK_HOST}/tool/{rtype}/{abbrev}/en"

    page_count = len(manifest_pages)

    lines: list[str] = []
    lines.append(f"appId: {APP_ID}")
    lines.append(f"name: {rtype.upper()} - {name} ({abbrev})")
    lines.append("tags:")
    lines.append(f"  - generated")
    lines.append(f"  - {rtype}")
    lines.append(f"  - tool-{abbrev}")
    lines.append("---")
    lines.append("- launchApp:")
    lines.append("    stopApp: true")
    lines.append("- runFlow: ../../../helpers/dismiss_onboarding.yaml")
    lines.append(f"- openLink: {json.dumps(deeplink)}")

    # Permission/dialog handling on first deep-link
    lines.append("- runFlow:")
    lines.append("    when:")
    lines.append("      platform: iOS")
    lines.append('      visible: "Open"')
    lines.append("    commands:")
    lines.append('      - tapOn: "Open"')

    # Assert the screen id matching the resource type, so a regression that
    # silently routes the deep link elsewhere fails fast instead of hiding
    # behind name-text matches that may overlap across screens.
    SCREEN_ID_BY_TYPE = {
        "tract": "Tract",
        "lesson": "Lesson",
        "cyoa": "Choose Your Own Adventure",
        "article": "Articles",
    }
    screen_id = SCREEN_ID_BY_TYPE.get(rtype)
    if screen_id:
        lines.append("- assertVisible:")
        lines.append(f"    id: {json.dumps(screen_id)}")

    # Assert resource title appears - real content
    lines.append(f"- assertVisible: {yaml_str(name)}")

    # Description lead is a strong signal but can be long; only assert if shortish & informative
    if description_lead and len(description_lead) >= 20 and len(description_lead) <= 80:
        lines.append(f"- assertVisible: {yaml_str(description_lead)}")

    # Capture initial screenshot. Path is templated via SNAPSHOT_DIR env var.
    page_label_0 = manifest_pages[0] if manifest_pages else "open"
    lines.append(f"- takeScreenshot: \"${{SNAPSHOT_DIR}}/{abbrev}/00-{slug(page_label_0)}\"")

    # Walk pages by swipe (works for tract/cyoa/lesson alike).
    # Page count comes from the manifest. If 0 (manifest fetch failed), fall back to 5.
    walk_count = page_count if page_count > 0 else 5
    for i in range(1, walk_count):
        lines.append("- swipe:")
        lines.append("    start: 90%, 50%")
        lines.append("    end: 10%, 50%")
        page_label = manifest_pages[i] if i < len(manifest_pages) else f"page-{i}"
        lines.append(f"- takeScreenshot: \"${{SNAPSHOT_DIR}}/{abbrev}/{i:02d}-{slug(page_label)}\"")

    return out_path, "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", choices=API_BY_ENV.keys(), default="stage")
    parser.add_argument("--lang", default="en", help="language code to generate flows for (currently only en supported)")
    args = parser.parse_args()

    api = API_BY_ENV[args.api]
    print(f"Fetching catalog from {api} ...", file=sys.stderr)
    catalog = fetch_resources(api)
    en_lang_id = english_id(api)

    # Index translations by id; pick English per resource
    included = {(item["type"], item["id"]): item for item in catalog.get("included", [])}

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    skipped = 0
    for resource in catalog["data"]:
        rels = resource.get("relationships", {})
        translations = rels.get("latest-translations", {}).get("data", [])
        en_translation = None
        for t in translations:
            cand = included.get((t["type"], t["id"]))
            if cand is None:
                continue
            lang_rel = cand.get("relationships", {}).get("language", {}).get("data", {})
            if lang_rel.get("id") == en_lang_id:
                en_translation = cand
                break

        manifest_pages: list[str] = []
        if en_translation:
            manifest_name = en_translation["attributes"].get("manifest-name")
            if manifest_name:
                try:
                    xml_text = http_text(f"{api}/translations/files/{manifest_name}")
                    manifest_pages = parse_manifest_pages(xml_text)
                except Exception as e:
                    print(f"  warn: manifest fetch failed for {resource['attributes']['abbreviation']}: {e}", file=sys.stderr)

        if not en_translation:
            print(f"  skip: {resource['attributes']['abbreviation']} (no English translation)", file=sys.stderr)
            skipped += 1
            continue

        out_path, body = emit_flow(resource, en_translation, manifest_pages)
        out_path.write_text(body, encoding="utf-8")
        written += 1
        print(f"  wrote {out_path.relative_to(ROOT)} ({len(manifest_pages)} pages)")

    print(f"\nGenerated {written} flow(s); skipped {skipped}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
