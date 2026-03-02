#!/usr/bin/env python3
"""Discover all form field names, types, and metadata in a PDF.

Replaces ad-hoc inline Python for field discovery. Tries both pypdf
(/TU tooltips) and PyMuPDF (XFA <speak> descriptions).

Usage:
    python discover_fields.py form.pdf
    python discover_fields.py form.pdf --page 2
    python discover_fields.py form.pdf --search "routing"
    python discover_fields.py form.pdf --type Btn
    python discover_fields.py form.pdf --xfa-only
"""

import argparse
import sys


def discover_acroform(pdf_path, page_filter=None, search=None, type_filter=None):
    """Dump all AcroForm fields using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(pdf_path)
    fields = []

    for pi, page in enumerate(reader.pages):
        if page_filter is not None and pi != page_filter:
            continue
        annots = page.get("/Annots") or []
        for annot in annots:
            obj = annot.get_object()
            t = str(obj.get("/T", ""))
            tu = str(obj.get("/TU", ""))
            ft = str(obj.get("/FT", ""))
            v = str(obj.get("/V", ""))
            as_val = str(obj.get("/AS", ""))
            rect = obj.get("/Rect", [])

            # Get parent info
            parent_ref = obj.get("/Parent")
            pname = ""
            if parent_ref:
                pobj = parent_ref.get_object()
                pname = str(pobj.get("/T", ""))

            # Get /AP/N keys for radio buttons
            ap = obj.get("/AP", {})
            n_keys = []
            if "/N" in ap:
                n_keys = list(ap["/N"].keys())

            # Determine display name
            name = t if t else f"(parent: {pname})"
            field_type = ft.replace("/", "") if ft else "?"

            # Apply filters
            if type_filter and field_type != type_filter:
                continue
            if search:
                searchable = f"{t} {tu} {pname}".lower()
                if search.lower() not in searchable:
                    continue

            fields.append({
                "page": pi,
                "name": name,
                "parent": pname,
                "type": field_type,
                "tooltip": tu if tu and tu != "None" else "",
                "value": v if v and v != "None" else "",
                "as": as_val if as_val and as_val != "None" else "",
                "ap_n_keys": n_keys,
                "rect": [round(float(r), 1) for r in rect] if rect else [],
            })

    return fields


def discover_xfa(pdf_path, search=None):
    """Extract XFA field descriptions using PyMuPDF (fitz).

    Finds the XFA template by parsing /AcroForm -> /XFA array to locate the
    template xref directly. Does NOT use brute-force xref scanning (unreliable).

    Uses regex instead of xml.etree.ElementTree because IRS XFA XML has
    unbound namespace prefixes and line-breaks inside closing tags that
    break XML parsers.
    """
    try:
        import fitz
    except ImportError:
        print("  PyMuPDF (fitz) not installed — skipping XFA discovery", file=sys.stderr)
        return []

    import re

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"  Cannot open PDF: {e}", file=sys.stderr)
        return []

    # Phase 1: Find XFA template xref via /AcroForm -> /XFA array
    template_xref = None
    for i in range(1, doc.xref_length()):
        try:
            obj = doc.xref_object(i)
            if '/XFA' in obj:
                match = re.search(r'\(template\)\s+(\d+)\s+0\s+R', obj)
                if match:
                    template_xref = int(match.group(1))
                    break
        except Exception:
            continue

    if template_xref is None:
        doc.close()
        return []

    # Phase 2: Extract fields using regex (NOT XML parser)
    stream = doc.xref_stream(template_xref)
    text = stream.decode('utf-8', errors='replace')
    xfa_fields = []

    for m in re.finditer(r'<(?:field|exclGroup)\s+[^>]*name="([^"]+)"', text):
        name = m.group(1)
        chunk = text[m.start():m.start() + 2000]
        speak_m = re.search(
            r'<speak[^>]*\n?>(.*?)</speak\s*\n?\s*>', chunk, re.DOTALL
        )
        speak = ""
        if speak_m:
            speak = speak_m.group(1).strip()
            if 'Cat. No.' in speak:
                speak = ""

        if not name:
            continue
        if search and search.lower() not in f"{name} {speak}".lower():
            continue
        xfa_fields.append({"name": name, "speak": speak})

    doc.close()
    return xfa_fields


def main():
    parser = argparse.ArgumentParser(
        description="Discover PDF form field names, types, and metadata."
    )
    parser.add_argument("pdf", help="Path to PDF form")
    parser.add_argument("--page", type=int, default=None,
                        help="Only show fields on this page (0-indexed)")
    parser.add_argument("--search", "-s", default=None,
                        help="Filter fields by keyword (searches name, tooltip, parent)")
    parser.add_argument("--type", "-t", default=None, dest="type_filter",
                        help="Filter by field type: Tx (text), Btn (checkbox/radio), Ch (choice)")
    parser.add_argument("--xfa-only", action="store_true",
                        help="Only show XFA field descriptions (skip AcroForm)")

    args = parser.parse_args()

    if not args.xfa_only:
        print(f"=== AcroForm Fields: {args.pdf} ===")
        fields = discover_acroform(args.pdf, args.page, args.search, args.type_filter)
        if fields:
            for f in fields:
                parts = [f"Page {f['page']}", f"Name={f['name']}"]
                if f["parent"]:
                    parts.append(f"Parent={f['parent']}")
                parts.append(f"Type={f['type']}")
                if f["tooltip"]:
                    parts.append(f"TU={f['tooltip'][:100]}")
                if f["value"]:
                    parts.append(f"V={f['value']}")
                if f["as"]:
                    parts.append(f"AS={f['as']}")
                if f["ap_n_keys"]:
                    parts.append(f"AP/N={f['ap_n_keys']}")
                if f["rect"]:
                    parts.append(f"Rect={f['rect']}")
                print("  " + " | ".join(parts))
            print(f"\n  Total: {len(fields)} fields")
        else:
            print("  No AcroForm fields found (or none matched filters)")

    print(f"\n=== XFA Field Descriptions: {args.pdf} ===")
    xfa = discover_xfa(args.pdf, args.search)
    if xfa:
        for f in xfa:
            speak = f": {f['speak']}" if f["speak"] else ""
            print(f"  {f['name']}{speak}")
        print(f"\n  Total: {len(xfa)} XFA fields")
    else:
        print("  No XFA template found (or PyMuPDF not installed)")


if __name__ == "__main__":
    main()
