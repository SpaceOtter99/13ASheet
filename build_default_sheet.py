#!/usr/bin/env python3
import glob
import json
import os
from collections import defaultdict

from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

# your project’s STATS / DEFENCES constants
from data import STATS, DEFENCES

# ─── Auto-attr + auto-dict class ────────────────────────────────────────────
class AutoAttrDict(dict):
    """
    dict where missing keys auto-create new AutoAttrDict,
    and you can do d.foo as well as d['foo'].
    """
    def __getattr__(self, key):
        if key in self:
            val = self[key]
            # wrap nested normal dicts
            if isinstance(val, dict) and not isinstance(val, AutoAttrDict):
                val = AutoAttrDict(val)
                self[key] = val
            return val
        # auto-vivify missing
        val = AutoAttrDict()
        self[key] = val
        return val

    def __getitem__(self, key):
        if key in self:
            val = super().__getitem__(key)
            if isinstance(val, dict) and not isinstance(val, AutoAttrDict):
                val = AutoAttrDict(val)
                self[key] = val
            return val
        # auto-vivify missing
        val = AutoAttrDict()
        self[key] = val
        return val

    def __setattr__(self, key, value):
        self[key] = value

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            if isinstance(v, dict) and not isinstance(v, AutoAttrDict):
                v = AutoAttrDict(v)
            self[k] = v

# ─── helpers ────────────────────────────────────────────────────────────────
def make_autovivifying_dict():
    return defaultdict(make_autovivifying_dict)

def dictify(d):
    if isinstance(d, defaultdict):
        return {k: dictify(v) for k, v in d.items()}
    return d

def merge_defaults(existing, defaults):
    """
    Recursively add keys from `defaults` into `existing` only if they
    aren’t already present. Nested dicts are walked through.
    """
    for key, val in defaults.items():
        if isinstance(val, dict):
            if key not in existing or not isinstance(existing.get(key), dict):
                # if missing entirely, or type mismatch, take the whole dict
                existing[key] = val
            else:
                # merge deeper
                merge_defaults(existing[key], val)
        else:
            if key not in existing:
                existing[key] = val

# ─── main script ───────────────────────────────────────────────────────────
def main():
    here = os.path.dirname(__file__)
    templates_dir = os.path.join(here, "templates")
    out_path = os.path.join(here, "default_sheet.json")

    # Try loading existing defaults
    try:
        with open(out_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except FileNotFoundError:
        existing = {}

    env = Environment(loader=FileSystemLoader(templates_dir))
    env.globals['url_for'] = lambda *args, **kwargs: ''  # no‐op for url_for

    # Build a dummy_character that won't error on ANY attribute/item lookup
    dummy_character = AutoAttrDict()

    sheet = make_autovivifying_dict()
    context = {
        'STATS':     STATS,
        'DEFENCES':  DEFENCES,
        'character': dummy_character,
        'request':   dummy_character
    }

    for full in glob.glob(os.path.join(templates_dir, "*.html"), recursive=True):
        rel = os.path.relpath(full, templates_dir)
        tmpl = env.get_template(rel)
        rendered = tmpl.render(**context)
        soup = BeautifulSoup(rendered, "html.parser")
        tags = soup.find_all(attrs={"data-section": True, "data-key": True})
        print(f"Parsing {len(tags)} tags from {rel}")

        for tag in tags:
            sec = tag["data-section"]
            key = tag["data-key"]
            default = 0 if tag.get("type") == "number" else ""

            parts = key.split("-", 1)
            outer = parts[0]
            if len(parts) > 1:
                inner = parts[1]
                if default == 0 and inner == "base":
                    default = 10
                sheet[sec][outer][inner] = default
            else:
                sheet[sec][outer] = default

    # Turn our autovivifying defaultdict into a plain nested dict
    normal = dictify(sheet)

    # Merge only missing defaults into our existing file
    merge_defaults(existing, normal)

    # Write back out (preserves any pre-existing values)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, sort_keys=True)

    print(f"Wrote merged defaults to {out_path}")

if __name__ == "__main__":
    main()
