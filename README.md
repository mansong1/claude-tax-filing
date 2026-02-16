# Tax Filing Skill for Claude Code

A Claude Code skill that prepares income tax returns end-to-end — reads source documents, computes taxes, discovers PDF form fields, and fills the official forms.

## What It Does

1. **Reads** your W-2s, 1099s, brokerage statements, and prior-year returns
2. **Looks up** current-year tax brackets, deductions, and credits
3. **Computes** all the math — income, deductions, brackets, credits, capital gains
4. **Downloads** the official blank PDF forms from IRS.gov / FTB.ca.gov
5. **Discovers** field names in each PDF (XFA extraction, /TU tooltips, positional analysis)
6. **Fills** every form programmatically using pypdf
7. **Verifies** all fields were written correctly
8. **Presents** a summary with verification checklist, signing reminders, and payment instructions

## Year-Agnostic, Form-Agnostic

This skill doesn't hardcode tax brackets, deduction amounts, or field mappings. Each run:
- Looks up the correct year-specific values from authoritative sources
- Downloads that year's blank forms
- Discovers field names fresh from the downloaded PDFs

It can handle any fillable PDF tax form — federal, state, or otherwise — as long as it can research the form structure and field names.

## Installation

Tell Claude to install the skill from this repo:

> Download the tax-filing skill from https://github.com/robbalian/claude-tax-filing and install it to my .claude/skills/ directory

Or manually:

```bash
git clone https://github.com/robbalian/claude-tax-filing.git
cp -r claude-tax-filing/skills/tax-filing ~/.claude/skills/
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
