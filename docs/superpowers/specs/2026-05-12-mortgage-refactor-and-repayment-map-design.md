# Mortgage Calculator — Refactor & Repayment Map

**Date:** 2026-05-12  
**Scope:** Bug fixes, performance, deduplication, architecture split, new Repayment Map tab

---

## 1. Bug Fixes

### 1a. Zero-rate divide-by-zero in `generate_amortization_schedule`
`calculate_principal` already guards `monthly_rate == 0` with a branch to `principal / n_payments`. `generate_amortization_schedule` does not. Add the same guard:

```python
if monthly_rate == 0:
    monthly_payment = principal / n_payments
else:
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** n_payments) / ((1 + monthly_rate) ** n_payments - 1)
```

### 1b. Misleading fill in Income Analysis tab
The first `go.Scatter` trace uses `fill='tonexty'` with no preceding trace, which fills to the x-axis. Replace with `fill='tozeroy'` to make the intent explicit, or remove the fill entirely. Decision: **remove fill** — a plain line is less ambiguous.

---

## 2. Performance — Vectorise Contour Calculation

`render_affordability_tab` uses a Python double `for` loop (~100 × N iterations) to populate `house_values`. `calculate_principal` already supports numpy array inputs. Replace the loop with a single vectorised call using meshgrid arrays:

```python
house_values = calculate_principal(monthly_payment, R, T, down_payment_pct)
```

Expected speedup: ~50×. No change to `calculate_principal` required.

---

## 3. Deduplication — Shared Breakdown Card Builder

`render_breakdown_tab` and `update_breakdown_results` each build the same three Dash cards (Scenario Details, Affordability, Total Cost Breakdown) — ~60 lines duplicated.

Extract a module-level helper:

```python
def _build_breakdown_cards(rate, term, monthly_payment, down_payment_pct, salary, target_multiplier):
    # returns dbc.Container with the three cards
```

Both functions call this helper. `render_breakdown_tab` passes mid-range defaults; `update_breakdown_results` passes slider values.

---

## 4. Architecture — Module Split

Break the single 792-line `main.py` into four focused files:

| File | Responsibility |
|------|----------------|
| `calculations.py` | `calculate_principal`, `generate_amortization_schedule` |
| `layout.py` | `app.layout` definition (all Dash component trees) |
| `callbacks.py` | All `@app.callback` functions and tab render helpers |
| `app.py` | App instantiation (`Dash(...)`) and `if __name__ == "__main__"` entrypoint |

### Fix `suppress_callback_exceptions=True`
This flag is needed because the breakdown tab's sliders (`breakdown-rate-slider`, `breakdown-term-slider`, `breakdown-multiplier-slider`) are generated dynamically inside `render_breakdown_tab`, so they don't exist in the DOM when the callback is registered.

Fix: move these three sliders into the top-level layout (inside `layout.py`), hidden by default with `style={"display": "none"}` and shown only when the breakdown tab is active. The callback targets always exist, so the flag can be removed.

### Lazy tab rendering
Add `prevent_initial_call=True` to the main `render_tab_content` callback. Use `dash.callback_context` (already used in the breakdown callback) to skip computing tabs that are not active.

---

## 5. New Tab — Repayment Map

### Purpose
The inverse of the Affordability Map: given a fixed house price, show how monthly repayments vary across interest rates (x-axis) and loan terms (y-axis).

### Tab name
`"Repayment Map"` — inserted after "Scenario Comparison" as the 6th tab.

### In-tab controls (rendered at top of tab, inside a `dbc.Card`)

| Control | Type | Range | Step | Default |
|---------|------|-------|------|---------|
| House Price (£) | Slider | £100,000 – £500,000 | £1,000 | £250,000 |
| Loan Term Range (Years) | RangeSlider | 10 – 40 years | 1 year | [15, 35] |

The interest rate range comes from the existing global **Interest Rate Range** RangeSlider. Down payment % comes from the existing global **Down Payment** slider. These are read-only inputs from the global state — no duplication.

### Heatmap
- **X-axis:** interest rate (%) — range from global rate range slider, 100 evenly-spaced points
- **Y-axis:** loan term (years) — range from in-tab term range slider, 1-year steps
- **Cell value:** monthly repayment (£) — computed as:
  ```
  loan = house_price * (1 - down_payment_pct / 100)
  repayment = standard_mortgage_formula(loan, rate, term)
  ```
- **Colour scale:** `RdYlGn_r` (green = low repayment, red = high)
- **Hover template:** `Rate: X.XX% | Term: Y years | Repayment: £Z,ZZZ/mo`
- **Budget reference line:** a constraint contour line (same technique as the salary multiplier lines on the Affordability Map) drawn where `repayment == monthly_payment` (from the global **Monthly Payment** slider), annotated `"Budget: £X,XXX/mo"`. This shows the curve of all rate/term combinations that exactly hit the user's budget — cells to the lower-left are affordable, cells to the upper-right are over budget.

### Callback pattern
The in-tab sliders (`house-price-slider`, `repayment-term-range-slider`) live in the **top-level layout** (hidden by default, revealed when the Repayment Map tab is active) — same fix applied to the breakdown tab sliders. This avoids `suppress_callback_exceptions`.

A dedicated callback outputs to `dcc.Graph(id="repayment-map-graph")`:

```python
@app.callback(
    Output("repayment-map-graph", "figure"),
    Input("house-price-slider", "value"),
    Input("repayment-term-range-slider", "value"),
    Input("rate-range-slider", "value"),
    Input("down-payment-slider", "value"),
    Input("payment-slider", "value"),
    prevent_initial_call=True,
)
def update_repayment_map(house_price, term_range, rate_range, down_payment_pct, monthly_payment):
    ...
```

Uses the same vectorised numpy approach as the fixed affordability contour.

---

## Out of Scope

- Joint income / dual salary
- Overpayment modelling
- Stamp duty calculator
- Tests (separate task)
- `.gitignore` / pinned requirements (separate task)
