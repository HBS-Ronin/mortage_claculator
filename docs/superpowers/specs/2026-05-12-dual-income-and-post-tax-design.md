# Dual Income & Post-Tax Salary Design

**Date:** 2026-05-12
**Scope:** Add UK post-tax take-home calculation and optional dual-income support

---

## Background

The current app uses gross (pre-tax) salary for all metrics. This is correct for lender salary-multiplier calculations (lenders always use gross), but misleading for the "payment as % of income" affordability metric — a mortgage consuming 28% of gross salary actually consumes ~40% of take-home pay. Users need both numbers to assess real affordability.

Dual income adds a second person's salary so joint applicants can use the calculator accurately.

---

## 1. Post-Tax Calculation

### New function: `calculate_take_home_pay`

Add to `calculations.py`:

```python
def calculate_take_home_pay(gross_salary: float) -> float:
```

Uses 2024/25 UK rates:

**Income Tax:**
| Band | Rate | Range |
|------|------|-------|
| Personal allowance | 0% | £0 – £12,570 |
| Basic rate | 20% | £12,571 – £50,270 |
| Higher rate | 40% | £50,271 – £125,140 |
| Additional rate | 45% | > £125,140 |

**National Insurance Class 1 (employee):**
| Band | Rate | Range |
|------|------|-------|
| Below threshold | 0% | £0 – £12,570 |
| Main rate | 8% | £12,571 – £50,270 |
| Upper rate | 2% | > £50,270 |

Returns annual take-home pay (gross minus income tax minus NI). Scalar inputs only — no array support needed (called with slider values, not meshgrids).

### Where gross vs net is used

| Metric | Uses |
|--------|------|
| Salary multiplier lines on Affordability Map | Gross — lenders use gross |
| Salary multiplier in Comparison & Amortization tabs | Gross |
| Loan-to-income ratio | Gross |
| Lender guideline text (4–4.5x, etc.) | Gross |
| **Payment as % of income** | **Net take-home** |
| Income Analysis salary breakdown card | Both — shows `£X gross / £Y take-home` |
| Breakdown tab "Payment to Salary" | Net take-home |

---

## 2. Dual Income

### UI: optional toggle in global controls

A `dbc.Switch(id="partner-income-toggle", label="Add Partner Income")` sits below the Person 1 salary slider in the global controls card.

When toggled on, `html.Div(id="partner-income-section")` becomes visible. It contains:

| Control | ID | Range | Step | Default |
|---------|----|-------|------|---------|
| Partner Salary (£) | `salary-2-slider` | £0 – £150,000 | £1,000 | £0 |

The section is **always in the DOM** (hidden by default) to avoid `suppress_callback_exceptions`. A callback drives `style={"display": "block/none"}` on `partner-income-section`.

Default value of £0 means partner income has zero effect until the user sets it — existing single-income behaviour is fully preserved.

### Combined income in calculations

All salary-using callbacks receive both `partner-income-toggle` and `salary-2-slider` as Inputs. The effective partner salary is resolved inside each callback:

```python
effective_salary_2 = salary_2 if partner_toggle else 0
combined_gross = salary_1 + effective_salary_2
combined_net   = calculate_take_home_pay(salary_1) + calculate_take_home_pay(effective_salary_2)
```

This keeps the slider's last value intact when the toggle is turned off without requiring a reset callback.

- `combined_gross` → salary multiplier lines, loan-to-income, lender guidelines
- `combined_net` → payment-to-income % metric

### Label changes when partner income active

| Location | Single income | Dual income |
|----------|--------------|-------------|
| Income Analysis header | "Annual Salary: £X" | "Combined Salary: £X (Person 1: £A + Partner: £B)" |
| Salary multiplier label | "Xx salary" | "Xx combined salary" |
| Payment ratio label | "X% of take-home" | "X% of combined take-home" |

---

## 3. File Changes

| File | Change |
|------|--------|
| `calculations.py` | Add `calculate_take_home_pay(gross_salary)` |
| `calculations.py` | Add `calculate_take_home_pay` tests to `tests/test_calculations.py` |
| `layout.py` | Add `partner-income-toggle` switch + `partner-income-section` with `salary-2-slider` below `salary-slider` in global controls |
| `callbacks.py` | Add `toggle_partner_income` callback (Input: toggle, Output: partner-income-section style) |
| `callbacks.py` | Add `salary_2` input to all callbacks that use `salary`: `render_tab_content`, `update_breakdown_results` |
| `callbacks.py` | Update all salary computations to use `combined_gross` / `combined_net` as appropriate |

---

## 4. Out of Scope

- Student loan repayment
- Pension contributions
- Scottish income tax rates (use England/Wales/NI rates throughout)
- Tax year selector (hardcode 2024/25)
- Per-person breakdown of tax in the UI (combined figures only)
