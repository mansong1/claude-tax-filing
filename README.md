# Tax Filing Skill for Claude Code

A Claude Code skill that prepares income tax returns end-to-end — reads source documents, computes taxes, and fills the official PDF forms.

## What It Does

1. **Reads** your W-2s, 1099s, brokerage statements, and prior-year returns
2. **Computes** all the math — income, deductions, brackets, credits, capital gains
3. **Downloads** the official blank PDF forms from IRS.gov / FTB.ca.gov
4. **Discovers** field names in each PDF (XFA extraction, /TU tooltips)
5. **Fills** every form programmatically using pypdf
6. **Verifies** all fields were written correctly
7. **Presents** a summary with verification checklist, signing reminders, and payment instructions

## Supported Forms

Currently handles:
- **Federal**: Form 1040, Schedule D, Form 8949
- **California**: Form 540

The skill is designed to be extensible — it can research and fill any PDF tax form given the right field discovery approach.

## Year-Agnostic

This skill works for **any tax year**. It does not hardcode tax brackets, standard deduction amounts, or field mappings. Each run:
- Looks up the correct year-specific values (brackets, deductions, credits)
- Downloads that year's blank forms
- Discovers field names fresh from the downloaded PDFs

## Installation

### Manual (any Claude setup)

Copy the `skills/tax-filing/` directory into your `.claude/skills/` folder:

```bash
cp -r skills/tax-filing ~/.claude/skills/
```

### Claude Code Plugin

```bash
/plugin marketplace add youruser/claude-tax-filing
/plugin install tax-filing
```

## Usage

Say any of:
- "do my taxes"
- "prepare my tax return"
- "fill my tax forms"

The skill walks through: gathering documents → confirming filing details → computing → filling PDFs → verification → filing instructions.

## Requirements

- Python 3.10+
- `pypdf` — for filling PDF forms
- `PyMuPDF` (`fitz`) — for discovering IRS XFA field names

```bash
pip install pypdf PyMuPDF
```

## Disclaimer

This is a tax preparation aid, not professional tax advice. Always review filled forms carefully and consult a tax professional for complex situations.
