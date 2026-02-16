---
name: tax-filing
description: Prepare and fill federal and state tax return PDF forms
user_invocable: true
triggers:
  - do my taxes
  - prepare tax return
  - fill tax forms
  - file taxes
  - tax preparation
---

# Tax Filing Skill

Prepare federal (IRS) and state (CA) income tax returns by extracting data from source documents, computing taxes, and filling official PDF forms.

**Year-agnostic**: This skill works for any tax year. You must look up the correct tax brackets, standard deduction amounts, exemption credits, and other year-specific values for the tax year being filed. Do NOT hardcode or assume values from a previous year.

## Workflow

### Step 1: Gather Source Documents

Ask the user for:
- W-2 (wages, withholding)
- 1099-INT (interest income)
- 1099-DIV (dividends, qualified dividends)
- 1099-B / brokerage CSV (capital gains/losses)
- Any other 1099s, K-1s, or income documents
- Prior year tax return (to check for capital loss carryover, etc.)

Read files from the working directory. Parse CSVs, extract numbers from PDFs, or ask the user to provide key figures.

### Step 2: Confirm Filing Details

Ask the user:
- Filing status (Single, MFJ, MFS, HOH, QSS)
- Dependents (number, names)
- State of residence
- Standard vs. itemized deduction preference
- Digital asset / cryptocurrency transactions (Yes/No) — note: stock trades are NOT digital assets
- Health coverage status (for CA)
- Any estimated tax payments made
- Any other credits or adjustments

### Step 3: Look Up Year-Specific Values

Before computing, research the correct values for the tax year being filed:
- **Federal tax brackets** (for the filing status)
- **Standard deduction** amount
- **Qualified dividends / capital gains** 0%/15%/20% bracket thresholds
- **CA tax brackets** (for the filing status)
- **CA standard deduction** amount
- **CA personal exemption credit** amount
- Any other year-specific thresholds (EITC, AMT, etc.)

Use IRS.gov and FTB.ca.gov as authoritative sources. Do NOT reuse prior-year amounts.

### Step 4: Compute Federal Return

Follow this sequence:

1. **Gross Income**: Sum W-2 wages (Line 1a), interest (2b), dividends (3b), capital gain/loss (7), other income
2. **Adjustments**: Student loan interest, HSA, IRA, etc. → Line 10
3. **AGI**: Gross income minus adjustments → Line 11
4. **Deductions**: Standard deduction or Schedule A → Line 12-14
5. **Taxable Income**: AGI minus deductions → Line 15
6. **Tax Computation**:
   - If qualified dividends or capital gains exist: use QDCG Tax Worksheet
   - Otherwise: use tax tables or bracket computation
7. **Credits**: Child tax credit, education, etc. → Lines 19-21
8. **Other Taxes**: SE tax, penalty, etc. → Lines 23
9. **Total Tax**: Line 24
10. **Payments**: W-2 withholding (25a), estimated payments (26), credits (27-31) → Line 33
11. **Refund/Owed**: Line 34-37 (overpaid/refund) or Line 37 (amount owed)

### Step 5: Compute Capital Gains (if applicable)

If the user has stock/option sales:
1. Fill **Form 8949** with individual transactions (Part I short-term, Part II long-term)
2. Fill **Schedule D** with totals from Form 8949
3. Apply $3,000 capital loss limitation (Schedule D Line 21)
4. Calculate carryover for next year
5. Report net gain/loss on 1040 Line 7

### Step 6: Compute State Return (CA Form 540)

1. Start with federal AGI (Line 13)
2. Apply CA subtractions (Line 14) and additions (Line 16) → CA AGI (Line 17)
3. Subtract CA standard deduction → Taxable income (Line 19)
4. Look up tax from CA tax table or compute from brackets → Line 31
5. Subtract exemption credits → Line 33
6. Add any special taxes (mental health tax on income over $1M, AMT) → Total tax (Line 64)
7. Subtract CA withholding (W-2 box 17) → Refund/Owed

### Step 7: Download Blank PDF Forms

Download the correct tax year forms. **Critical**: Use `/irs-prior/` for non-current-year forms.

```
# Federal forms - from IRS (replace YEAR with e.g. 2025)
https://www.irs.gov/pub/irs-prior/f1040--YEAR.pdf
https://www.irs.gov/pub/irs-prior/f8949--YEAR.pdf
https://www.irs.gov/pub/irs-prior/f1040sd--YEAR.pdf

# If current year, try /irs-pdf/ first:
https://www.irs.gov/pub/irs-pdf/f1040.pdf

# California - from FTB
https://www.ftb.ca.gov/forms/YEAR/YEAR-540.pdf
```

### Step 8: Discover Field Names & Fill PDF Forms

**Every tax year, you MUST discover field names fresh.** Field names and mappings can change between years. Do not assume prior-year field names are correct.

Use `scripts/fill_forms.py` which provides the `fill_pdf()` function. Write a year-specific fill script that:
1. Discovers field names for each downloaded form (see below)
2. Defines field name → value dictionaries for each form
3. Defines checkbox dictionaries
4. Calls `fill_pdf()` for each form

#### Discovering Field Names

Different forms require different PDF libraries for field discovery.

**IRS forms (1040, Schedule D, 8949)** — try XFA first: Use **PyMuPDF (fitz)** to extract the XFA template stream. The AcroForm fields typically have NO `/TU` tooltips — field names like `f1_32[0]` are opaque. The XFA template XML contains `<assist><speak>` elements with exact human-readable descriptions for every field.

```python
import fitz, xml.etree.ElementTree as ET
doc = fitz.open("form.pdf")
for i in range(1, doc.xref_length()):
    try:
        stream = doc.xref_stream(i)
        if stream and b'<template' in stream:
            root = ET.fromstring(stream.decode('utf-8', errors='replace'))
            for field in root.iter():
                if field.tag.endswith('}field'):
                    name = field.get('name', '')
                    for child in field.iter():
                        if child.tag.endswith('}speak'):
                            print(f"{name}: {child.text}")
                            break
            break
    except: continue
```

**CA Form 540** — use pypdf `/TU` tooltips:

```python
from pypdf import PdfReader
reader = PdfReader("ca540.pdf")
for page in reader.pages:
    for annot in page.get("/Annots", []):
        obj = annot.get_object()
        print(f"{obj.get('/T')}: {obj.get('/TU')}")
```

**When neither XFA nor /TU is available**: List all field names, positions (`/Rect`), and types; map by visual layout; use trial fills and manual verification.

For **filling** all forms, always use pypdf via `fill_forms.py`.

### Step 9: Verify and Fix

After filling:
1. Read back field values programmatically to confirm they were written
2. Cross-check key numbers: AGI, taxable income, tax, refund
3. Fix any misaligned fields by re-examining field names
4. Re-run the fill script after corrections

### Step 10: Present Results & Filing Instructions

After all forms are filled and verified, present a celebration + checklist + action items:

#### Celebration & Summary Table
Start with a brief celebratory note (e.g. "Your taxes are done! 🎉"), then show the key numbers:

| | Federal | State |
|---|---------|-------|
| AGI | ... | ... |
| Taxable Income | ... | ... |
| Tax | ... | ... |
| Withholding | ... | ... |
| **Refund** / **Amount Owed** | ... | ... |

#### Verification Checklist
Show what was checked/verified with checkmarks:
- ✅ W-2 wages, withholding matched to source
- ✅ 1099-INT / 1099-DIV amounts matched
- ✅ Capital gains/losses computed, Form 8949 filled
- ✅ Schedule D totals verified, $3,000 loss limitation applied
- ✅ Capital loss carryover from prior year applied
- ✅ Federal tax computed via QDCG worksheet (or brackets)
- ✅ State tax computed from brackets + exemption credits
- ✅ All PDF fields programmatically verified
- ✅ Checkboxes (filing status, digital assets, etc.) confirmed
- (Include/exclude items as relevant to the specific return)

#### Capital Loss Carryover (if applicable)
Note the carryover amounts for next year (short-term and long-term separately).

#### ⚠️ CRITICAL: Sign Your Returns!
**You MUST sign and date your returns before mailing or e-filing.** Unsigned returns are not valid and will be rejected.
- Federal 1040: Sign on Page 2, "Sign Here" section
- CA 540: Sign on Side 6, "Sign Here" section

#### Payment Instructions (if taxes are owed)
If the user OWES taxes (not getting a refund), make this **prominent and unmissable**:
- **Federal**: Pay via IRS Direct Pay (irs.gov/payments), EFTPS, or mail a check with Form 1040-V
- **California**: Pay via FTB Web Pay (ftb.ca.gov), or mail a check with the return
- **Deadline**: April 15 (or extension deadline). Late payments incur penalties + interest.
- **Filing an extension extends the filing deadline but NOT the payment deadline.** Taxes owed are still due April 15.

#### Filing Options
- E-file options (IRS Free File, CalFile, etc.)
- Mailing addresses for paper filing
- Payment due date

## Key Gotchas

### PDF Form Filling
- **Remove XFA**: Delete `/XFA` from `/AcroForm` dictionary to force AcroForm rendering
- **NeedAppearances**: Set to `True` so PDF viewers regenerate field appearances
- **auto_regenerate=False**: Pass this to `update_page_form_field_values` to avoid corruption
- **Checkboxes**: Set both `/V` and `/AS` to `/1` (checked) or `/Off` (unchecked)
- **Field names**: Walk the `/Parent` chain to build fully-qualified field paths
- **IRS field name `[0]` suffix**: IRS XFA-based forms have `/T` values like `f1_04[0]` (with `[0]` suffix). When using `update_page_form_field_values`, field keys MUST include the `[0]` suffix to match. Use a helper like `add_suffix()` to append `[0]` to all text field keys.
- **IRS checkbox matching**: The `fill_forms.py` `_get_full_name()` builds deeply nested paths (e.g. `topmostSubform[0].Page1[0].c1_3[0]`) that won't match short keys. For IRS forms, match checkboxes by `/T` value directly on each annotation instead of using the full path. Write a custom `fill_irs_pdf()` function that does this.

### IRS Form 1040 (historically stable field patterns)
- First few fields (e.g. `f1_01`, `f1_02`, `f1_03`) are often **fiscal year header fields**, NOT name fields — always verify via XFA discovery
- Address fields are often nested under a `ReadOrder` parent
- The digital assets question is about **cryptocurrency**, not stock trades
- Some checkboxes near Line 7 may be misidentified — always verify by XFA `<speak>` text, not by y-position

### IRS Schedule D & Form 8949
- Schedule D may have read-only fields (e.g. `_RO` suffix) — don't try to fill those
- Form 8949 checkboxes for Box A/B/C (and D/E/F) are typically 3-way radio buttons, not Yes/No pairs

### CA Form 540
- Field names often follow a `540-PPNN` pattern: PP = page number, NN = sequential field number
- Field numbers are sequential per page, **NOT** form line numbers
- Checkbox fields often end with `" CB"` suffix (note the space)
- Radio buttons (filing status, account type) use named AP keys — inspect `/AP/N` keys to find the correct value

### Downloading Forms
- For prior-year IRS forms: use `irs.gov/pub/irs-prior/` (NOT `/irs-pdf/`)
- `/irs-pdf/` always has the **current** year's forms
