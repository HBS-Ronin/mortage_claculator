# Dual Income & Post-Tax Salary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add UK post-tax take-home calculation (Income Tax + NI, 2024/25 rates) and an optional dual-income toggle so joint applicants can use the calculator accurately.

**Architecture:** `calculate_take_home_pay` is a new pure function in `calculations.py`. `layout.py` gains a partner income toggle switch and always-in-DOM partner salary slider. `callbacks.py` threads `combined_gross` and `combined_net` through all tab helpers — gross for lender multipliers, net for payment-to-income ratios.

**Tech Stack:** Python 3, Dash 2.x, Dash Bootstrap Components, Plotly, NumPy, pytest

---

## File Structure

| File | Action | What changes |
|------|--------|--------------|
| `calculations.py` | Modify | Add `calculate_take_home_pay(gross_salary)` |
| `tests/test_calculations.py` | Modify | Add 5 tests for `calculate_take_home_pay` |
| `layout.py` | Modify | Add partner toggle + `partner-income-section` with `salary-2-slider` below salary row |
| `callbacks.py` | Modify | Import `calculate_take_home_pay`; add `toggle_partner_section` callback; add `partner-income-toggle` + `salary-2-slider` inputs to `render_tab_content` and `update_breakdown_results`; update all 5 helper functions to use `combined_gross`/`combined_net` |

---

## Task 1: Add `calculate_take_home_pay` to `calculations.py`

**Files:**
- Modify: `calculations.py`
- Modify: `tests/test_calculations.py`

- [ ] **Step 1: Write failing tests first**

Append to `tests/test_calculations.py`:

```python
def test_take_home_zero():
    from calculations import calculate_take_home_pay
    assert calculate_take_home_pay(0) == pytest.approx(0)


def test_take_home_below_personal_allowance():
    from calculations import calculate_take_home_pay
    # £10,000 — below personal allowance and NI threshold, no deductions
    assert calculate_take_home_pay(10_000) == pytest.approx(10_000)


def test_take_home_basic_rate_only():
    from calculations import calculate_take_home_pay
    # £30,000 gross
    # IT:  (30000 - 12570) * 0.20 = 17430 * 0.20 = 3486.00
    # NI:  (30000 - 12570) * 0.08 = 17430 * 0.08 = 1394.40
    # Net: 30000 - 3486 - 1394.40 = 25119.60
    assert calculate_take_home_pay(30_000) == pytest.approx(25_119.60, abs=1)


def test_take_home_higher_rate():
    from calculations import calculate_take_home_pay
    # £60,000 gross
    # IT:  37700 * 0.20 + 9730 * 0.40 = 7540 + 3892 = 11432.00
    # NI:  37700 * 0.08 + 9730 * 0.02 = 3016 + 194.60 = 3210.60
    # Net: 60000 - 11432 - 3210.60 = 45357.40
    assert calculate_take_home_pay(60_000) == pytest.approx(45_357.40, abs=1)


def test_take_home_additional_rate():
    from calculations import calculate_take_home_pay
    # £130,000 gross
    # IT:  37700*0.20 + 74870*0.40 + 4860*0.45 = 7540 + 29948 + 2187 = 39675.00
    # NI:  37700*0.08 + 79730*0.02 = 3016 + 1594.60 = 4610.60
    # Net: 130000 - 39675 - 4610.60 = 85714.40
    assert calculate_take_home_pay(130_000) == pytest.approx(85_714.40, abs=1)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/danyalsiddiqui/Projects/mortage_repayment
python -m pytest tests/test_calculations.py -k "take_home" -v 2>&1 | head -20
```

Expected: `ImportError` or `AttributeError: module 'calculations' has no attribute 'calculate_take_home_pay'`

- [ ] **Step 3: Add `calculate_take_home_pay` to `calculations.py`**

Append to the end of `calculations.py`:

```python
def calculate_take_home_pay(gross_salary):
    """Return annual take-home pay after UK Income Tax and NI (2024/25 rates).

    Uses England/Wales/Northern Ireland rates. Scalar inputs only.
    """
    # Income Tax bands 2024/25
    _PA = 12_570      # personal allowance
    _BR_LIMIT = 50_270   # basic rate upper limit
    _HR_LIMIT = 125_140  # higher rate upper limit

    income_tax = 0.0
    if gross_salary > _PA:
        income_tax += min(gross_salary, _BR_LIMIT - _PA, gross_salary - _PA) * 0.20
    if gross_salary > _BR_LIMIT:
        income_tax += min(gross_salary - _BR_LIMIT, _HR_LIMIT - _BR_LIMIT) * 0.40
    if gross_salary > _HR_LIMIT:
        income_tax += (gross_salary - _HR_LIMIT) * 0.45

    # National Insurance Class 1 employee 2024/25
    _NI_LOWER = 12_570
    _NI_UPPER = 50_270

    ni = 0.0
    if gross_salary > _NI_LOWER:
        ni += min(gross_salary, _NI_UPPER) - _NI_LOWER
        ni *= 0.08
    if gross_salary > _NI_UPPER:
        ni += (gross_salary - _NI_UPPER) * 0.02

    return gross_salary - income_tax - ni
```

Wait — the NI computation above has a bug: the `ni *= 0.08` applies to the accumulated `ni` variable, not just the main band. Fix it as follows (replace the NI section with):

```python
    ni = 0.0
    if gross_salary > _NI_LOWER:
        main_ni_earnings = min(gross_salary, _NI_UPPER) - _NI_LOWER
        ni += main_ni_earnings * 0.08
    if gross_salary > _NI_UPPER:
        ni += (gross_salary - _NI_UPPER) * 0.02
```

The complete correct function to append:

```python
def calculate_take_home_pay(gross_salary):
    """Return annual take-home pay after UK Income Tax and NI (2024/25 rates).

    Uses England/Wales/Northern Ireland rates. Scalar inputs only.
    """
    _PA = 12_570
    _BR_LIMIT = 50_270
    _HR_LIMIT = 125_140

    income_tax = 0.0
    if gross_salary > _PA:
        income_tax += (min(gross_salary, _BR_LIMIT) - _PA) * 0.20
    if gross_salary > _BR_LIMIT:
        income_tax += (min(gross_salary, _HR_LIMIT) - _BR_LIMIT) * 0.40
    if gross_salary > _HR_LIMIT:
        income_tax += (gross_salary - _HR_LIMIT) * 0.45

    _NI_LOWER = 12_570
    _NI_UPPER = 50_270

    ni = 0.0
    if gross_salary > _NI_LOWER:
        ni += (min(gross_salary, _NI_UPPER) - _NI_LOWER) * 0.08
    if gross_salary > _NI_UPPER:
        ni += (gross_salary - _NI_UPPER) * 0.02

    return gross_salary - income_tax - ni
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
python -m pytest tests/test_calculations.py -v
```

Expected: all 13 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add calculations.py tests/test_calculations.py
git commit -m "feat: add calculate_take_home_pay with UK 2024/25 tax and NI rates"
```

---

## Task 2: Update `layout.py` — add partner income toggle and slider

**Files:**
- Modify: `layout.py`

The partner income section must be **always in the DOM** (hidden by default) so the callback targets `partner-income-toggle` and `salary-2-slider` always exist — consistent with the existing pattern for `breakdown-section` and `repayment-section`.

- [ ] **Step 1: Replace the salary row in `layout.py`**

In `layout.py`, find the salary row (lines 51–68, the third `dbc.Row` inside the global controls `dbc.CardBody`):

```python
                    dbc.Row([
                        dbc.Col([
                            html.Label("Annual Salary (£)", className="fw-bold"),
                            dcc.Slider(
                                id="salary-slider", min=20000, max=150000, step=100, value=50000,
                                marks={i: f"£{i // 1000}k" for i in range(20000, 151000, 20000)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ], md=6),
                        dbc.Col([
                            html.Label("Salary Multiplier Range", className="fw-bold"),
                            dcc.RangeSlider(
                                id="multiplier-range-slider", min=2, max=6, step=0.5, value=[3.5, 5],
                                marks={i: f"{i}x" for i in range(2, 7)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ], md=6),
                    ]),
```

Replace with:

```python
                    dbc.Row([
                        dbc.Col([
                            html.Label("Annual Salary — Person 1 (£)", className="fw-bold"),
                            dbc.Checklist(
                                id="partner-income-toggle",
                                options=[{"label": "Add Partner Income", "value": "active"}],
                                value=[],
                                switch=True,
                                inline=True,
                                className="mb-1",
                            ),
                            dcc.Slider(
                                id="salary-slider", min=20000, max=150000, step=100, value=50000,
                                marks={i: f"£{i // 1000}k" for i in range(20000, 151000, 20000)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ], md=6),
                        dbc.Col([
                            html.Label("Salary Multiplier Range", className="fw-bold"),
                            dcc.RangeSlider(
                                id="multiplier-range-slider", min=2, max=6, step=0.5, value=[3.5, 5],
                                marks={i: f"{i}x" for i in range(2, 7)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ], md=6),
                    ]),
                    # Partner income section — always in DOM, hidden until toggle on
                    html.Div(
                        id="partner-income-section",
                        style={"display": "none"},
                        children=[
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Annual Salary — Partner (£)", className="fw-bold"),
                                    dcc.Slider(
                                        id="salary-2-slider",
                                        min=0, max=150_000, step=1_000, value=0,
                                        marks={i: f"£{i // 1000}k" for i in range(0, 151_000, 30_000)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ], md=6),
                            ], className="mt-3"),
                        ],
                    ),
```

- [ ] **Step 2: Verify layout imports cleanly**

```bash
cd /Users/danyalsiddiqui/Projects/mortage_repayment
python -c "from layout import get_layout; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add layout.py
git commit -m "feat: add partner income toggle and salary-2-slider to layout"
```

---

## Task 3: Update `callbacks.py` — dual income inputs and post-tax metrics

**Files:**
- Modify: `callbacks.py`

This task makes all changes to `callbacks.py` in one pass:
1. Update import to include `calculate_take_home_pay`
2. Add `toggle_partner_section` callback
3. Add `partner-income-toggle` and `salary-2-slider` inputs to `render_tab_content` and `update_breakdown_results`
4. Update all 5 helper functions

**Helper function convention after this task:**
- `combined_gross` = `salary_1 + effective_salary_2` — used for lender multipliers
- `combined_net` = `calculate_take_home_pay(salary_1) + calculate_take_home_pay(effective_salary_2)` — used for payment-to-income %

- [ ] **Step 1: Update the import line at the top of `callbacks.py`**

Find:
```python
from calculations import calculate_principal, generate_amortization_schedule
```

Replace with:
```python
from calculations import calculate_principal, generate_amortization_schedule, calculate_take_home_pay
```

- [ ] **Step 2: Add `toggle_partner_section` callback inside `register_callbacks`**

After the existing `toggle_section_visibility` callback (after line 29, before the `render_tab_content` callback), add:

```python
    @app.callback(
        Output("partner-income-section", "style"),
        Input("partner-income-toggle", "value"),
    )
    def toggle_partner_section(partner_toggle):
        return {"display": "block"} if partner_toggle else {"display": "none"}
```

- [ ] **Step 3: Replace the `render_tab_content` callback**

Find and replace the entire `render_tab_content` callback (lines ~33–58):

```python
    @app.callback(
        Output("tab-content", "children"),
        Input("tabs", "active_tab"),
        Input("payment-slider", "value"),
        Input("down-payment-slider", "value"),
        Input("rate-range-slider", "value"),
        Input("term-range-slider", "value"),
        Input("salary-slider", "value"),
        Input("multiplier-range-slider", "value"),
        Input("partner-income-toggle", "value"),
        Input("salary-2-slider", "value"),
        prevent_initial_call=False,
    )
    def render_tab_content(active_tab, monthly_payment, down_payment_pct,
                           rate_range, term_range, salary_1, multiplier_range,
                           partner_toggle, salary_2):
        effective_salary_2 = (salary_2 or 0) if partner_toggle else 0
        combined_gross = salary_1 + effective_salary_2
        combined_net = (calculate_take_home_pay(salary_1)
                        + calculate_take_home_pay(effective_salary_2))
        partner_active = bool(partner_toggle)

        if active_tab == "tab-affordability":
            return _render_affordability_tab(monthly_payment, down_payment_pct,
                                             rate_range, term_range, combined_gross, multiplier_range)
        if active_tab == "tab-income":
            return _render_income_tab(monthly_payment, down_payment_pct, rate_range, term_range,
                                      combined_gross, combined_net, multiplier_range,
                                      salary_1, effective_salary_2, partner_active)
        if active_tab == "tab-amortization":
            return _render_amortization_tab(monthly_payment, down_payment_pct,
                                            rate_range, term_range, combined_gross, combined_net)
        if active_tab == "tab-comparison":
            return _render_comparison_tab(monthly_payment, down_payment_pct,
                                          rate_range, term_range, combined_gross, multiplier_range)
        return html.Div()
```

- [ ] **Step 4: Replace the `update_breakdown_results` callback**

Find and replace the entire `update_breakdown_results` callback (lines ~62–77):

```python
    @app.callback(
        Output("breakdown-results", "children"),
        Input("breakdown-rate-slider", "value"),
        Input("breakdown-term-slider", "value"),
        Input("breakdown-multiplier-slider", "value"),
        Input("payment-slider", "value"),
        Input("down-payment-slider", "value"),
        Input("salary-slider", "value"),
        Input("tabs", "active_tab"),
        Input("partner-income-toggle", "value"),
        Input("salary-2-slider", "value"),
    )
    def update_breakdown_results(rate, term, target_multiplier,
                                 monthly_payment, down_payment_pct, salary_1, active_tab,
                                 partner_toggle, salary_2):
        if active_tab != "tab-breakdown":
            return html.Div()
        effective_salary_2 = (salary_2 or 0) if partner_toggle else 0
        combined_gross = salary_1 + effective_salary_2
        combined_net = (calculate_take_home_pay(salary_1)
                        + calculate_take_home_pay(effective_salary_2))
        return _build_breakdown_cards(rate, term, monthly_payment,
                                      down_payment_pct, combined_gross, combined_net,
                                      target_multiplier)
```

- [ ] **Step 5: Replace `_render_affordability_tab`**

Find and replace the entire `_render_affordability_tab` function:

```python
def _render_affordability_tab(monthly_payment, down_payment_pct, rate_range, term_range,
                               combined_gross, multiplier_range):
    annual_rates = np.linspace(rate_range[0], rate_range[1], 100) / 100
    terms = np.arange(term_range[0], term_range[1] + 1, 1)
    R, T = np.meshgrid(annual_rates, terms)
    house_values = calculate_principal(monthly_payment, R, T, down_payment_pct)

    fig = go.Figure(data=go.Contour(
        z=house_values,
        x=annual_rates * 100,
        y=terms,
        colorscale="Viridis",
        contours=dict(showlines=True),
        colorbar=dict(title="House Value [£]"),
        hovertemplate=(
            "Rate: %{x:.2f}%<br>Term: %{y} years<br>"
            "House Value: £%{z:,.0f}<extra></extra>"
        ),
    ))

    annotations = []
    for idx, multiplier in enumerate(multiplier_range):
        salary_based_value = combined_gross * multiplier
        fig.add_contour(
            z=house_values, x=annual_rates * 100, y=terms,
            contours=dict(type="constraint", operation="=", value=salary_based_value),
            line=dict(color="rgba(255,255,255,0.8)", width=3, dash="dash"),
            showscale=False, hoverinfo="skip",
            name=f"{multiplier}x salary",
        )
        mid_rate_idx = len(annual_rates) // 2
        annotation_y = next(
            (term for i, term in enumerate(terms)
             if abs(house_values[i, mid_rate_idx] - salary_based_value) < salary_based_value * 0.1),
            term_range[0] + (term_range[1] - term_range[0]) * (0.2 + idx * 0.5),
        )
        annotations.append(dict(
            x=annual_rates[-1] * 100 - 0.3, y=annotation_y,
            text=f"{multiplier}x: £{salary_based_value:,.0f}",
            xanchor="right", yanchor="middle",
            bgcolor="rgba(0,0,0,0.7)", font=dict(color="white", size=10),
            showarrow=False, borderpad=4,
        ))

    fig.update_layout(
        xaxis_title="Interest Rate [%]", yaxis_title="Term [Years]",
        title=f"Max House Value for £{monthly_payment}/month with {down_payment_pct}% Down",
        height=600, hovermode="closest", showlegend=False, annotations=annotations,
    )
    return dcc.Graph(figure=fig, style={"height": "100%"})
```

- [ ] **Step 6: Replace `_render_income_tab`**

Find and replace the entire `_render_income_tab` function:

```python
def _render_income_tab(monthly_payment, down_payment_pct, rate_range, term_range,
                        combined_gross, combined_net, multiplier_range,
                        salary_1, salary_2, partner_active):
    mid_rate = (rate_range[0] + rate_range[1]) / 2 / 100
    mid_term = (term_range[0] + term_range[1]) // 2

    payment_based_value = float(calculate_principal(monthly_payment, mid_rate, mid_term, down_payment_pct))
    multipliers = np.linspace(multiplier_range[0], multiplier_range[1], 50)
    salary_based_values = combined_gross * multipliers
    mid_multiplier = (multiplier_range[0] + multiplier_range[1]) / 2
    salary_based_value = combined_gross * mid_multiplier

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=multipliers, y=salary_based_values,
        mode="lines", name="Salary-Based Affordability",
        line=dict(color="blue", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=[multiplier_range[0], multiplier_range[1]],
        y=[payment_based_value, payment_based_value],
        mode="lines",
        name=f"Payment-Based: £{payment_based_value:,.0f}",
        line=dict(color="green", width=3, dash="dash"),
    ))

    for ratio_pct in [25, 30]:
        max_monthly = (combined_net / 12) * (ratio_pct / 100)
        ratio_house = float(calculate_principal(max_monthly, mid_rate, mid_term, down_payment_pct))
        ratio_mult = ratio_house / combined_gross
        if multiplier_range[0] <= ratio_mult <= multiplier_range[1]:
            fig.add_trace(go.Scatter(
                x=[multiplier_range[0], multiplier_range[1]],
                y=[ratio_house, ratio_house],
                mode="lines",
                name=f"{ratio_pct}% of take-home",
                line=dict(color="orange" if ratio_pct == 25 else "red", width=2, dash="dot"),
            ))

    for mult in [3, 4, 4.5, 5]:
        if multiplier_range[0] <= mult <= multiplier_range[1]:
            val = combined_gross * mult
            fig.add_trace(go.Scatter(
                x=[mult], y=[val], mode="markers+text",
                name=f"{mult}x salary",
                marker=dict(size=12, color="red"),
                text=f"£{val:,.0f}", textposition="top center",
            ))

    title = (
        f"Income-Based Affordability (Combined Salary: £{combined_gross:,})"
        if partner_active
        else f"Income-Based Affordability (Salary: £{combined_gross:,})"
    )
    fig.update_layout(
        title=title,
        xaxis_title="Salary Multiplier", yaxis_title="House Value [£]",
        height=400, showlegend=True, hovermode="x unified",
        legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=0.01,
                    bgcolor="rgba(255,255,255,0.8)", bordercolor="rgba(0,0,0,0.2)", borderwidth=1),
    )

    payment_to_net_ratio = (monthly_payment * 12) / combined_net * 100
    loan_to_income = (payment_based_value * (1 - down_payment_pct / 100)) / combined_gross

    if partner_active:
        salary_display = (
            f"£{combined_gross:,} gross "
            f"(Person 1: £{salary_1:,} + Partner: £{salary_2:,})"
        )
    else:
        salary_display = f"£{combined_gross:,}"

    return dbc.Container([
        dbc.Row([dbc.Col([dcc.Graph(figure=fig)], md=12)], className="mb-3"),
        dbc.Row([
            dbc.Col([dbc.Card([
                dbc.CardHeader("Income Analysis", className="fw-bold"),
                dbc.CardBody([
                    html.P([html.Strong("Annual Salary: "), salary_display]),
                    html.P([html.Strong("Annual Take-Home: "), f"£{combined_net:,.0f}"]),
                    html.P([html.Strong("Annual Payment: "),
                            f"£{monthly_payment * 12:,} ({payment_to_net_ratio:.1f}% of take-home)"]),
                    html.P([
                        html.Strong("Payment to Take-Home Ratio: "),
                        f"{payment_to_net_ratio:.1f}%",
                        html.Span(
                            " ✓ Within recommended 35%" if payment_to_net_ratio <= 35
                            else " ⚠ Above recommended 35%",
                            className="text-success" if payment_to_net_ratio <= 35 else "text-warning",
                        ),
                    ]),
                    html.P([html.Strong("Loan to Income Ratio: "), f"{loan_to_income:.2f}x"]),
                ]),
            ], className="mb-3")], md=6),
            dbc.Col([dbc.Card([
                dbc.CardHeader("Salary vs Payment-Based Comparison", className="fw-bold"),
                dbc.CardBody([
                    html.P([html.Strong("Payment-Based Max: "), f"£{payment_based_value:,.0f}"]),
                    html.P([html.Strong(f"Salary-Based Max ({mid_multiplier}x): "),
                            f"£{salary_based_value:,.0f}"]),
                    html.Hr(),
                    html.P([
                        html.Strong("Difference: "),
                        f"£{abs(payment_based_value - salary_based_value):,.0f}",
                        html.Span(
                            f" (Payment approach {'higher' if payment_based_value > salary_based_value else 'lower'})",
                            className="text-muted",
                        ),
                    ]),
                    html.P([html.Strong("Effective Multiplier: "),
                            f"{payment_based_value / combined_gross:.2f}x salary"]),
                ]),
            ], className="mb-3")], md=6),
        ]),
        dbc.Row([dbc.Col([dbc.Alert([
            html.H6("💡 Lender Guidelines", className="alert-heading"),
            html.P("Most UK lenders offer 4-4.5x salary. Some offer up to 5-5.5x for higher earners or joint applications."),
            html.P("Higher multipliers mean larger loans and more interest paid over time.", className="mb-0"),
        ], color="info")], md=12)]),
    ])
```

- [ ] **Step 7: Replace `_render_amortization_tab`**

Find and replace the entire `_render_amortization_tab` function:

```python
def _render_amortization_tab(monthly_payment, down_payment_pct, rate_range, term_range,
                              combined_gross, combined_net):
    mid_rate = (rate_range[0] + rate_range[1]) / 2 / 100
    mid_term = (term_range[0] + term_range[1]) // 2

    house_value = float(calculate_principal(monthly_payment, mid_rate, mid_term, down_payment_pct))
    schedule, actual_payment = generate_amortization_schedule(
        house_value, down_payment_pct, mid_rate, mid_term
    )
    df = pd.DataFrame(schedule)

    effective_multiplier = house_value / combined_gross
    payment_to_income = (actual_payment * 12) / combined_net * 100

    return dbc.Container([
        html.H5("Amortization Schedule (First 30 years)", className="mb-3"),
        html.P(f"Based on: £{house_value:,.0f} house, {mid_rate * 100:.2f}% rate, {mid_term} year term"),
        html.P([
            html.Strong("Actual monthly payment: "),
            f"£{actual_payment:.2f}",
            html.Span(f" ({payment_to_income:.1f}% of annual take-home)", className="text-muted ms-2"),
        ], className="mb-3"),
        html.P([html.Strong("Salary multiplier: "), f"{effective_multiplier:.2f}x"], className="mb-3"),
        dash_table.DataTable(
            data=df.to_dict("records"),
            columns=[{"name": i, "id": i} for i in df.columns],
            style_table={"height": "500px", "overflowY": "auto"},
            style_cell={"textAlign": "left", "padding": "8px"},
            style_header={"backgroundColor": "rgb(230,230,230)", "fontWeight": "bold"},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "rgb(248,248,248)"}
            ],
            page_size=20,
        ),
    ])
```

- [ ] **Step 8: Replace `_render_comparison_tab`**

Find and replace the entire `_render_comparison_tab` function:

```python
def _render_comparison_tab(monthly_payment, down_payment_pct, rate_range, term_range,
                            combined_gross, multiplier_range):
    scenarios = [
        {"name": "Best Case",    "rate": rate_range[0] / 100, "term": term_range[1]},
        {"name": "Average Case", "rate": sum(rate_range) / 2 / 100, "term": (term_range[0] + term_range[1]) // 2},
        {"name": "Worst Case",   "rate": rate_range[1] / 100, "term": term_range[0]},
    ]

    comparison_data = []
    house_values = []
    for s in scenarios:
        hv = float(calculate_principal(monthly_payment, s["rate"], s["term"], down_payment_pct))
        loan = hv * (1 - down_payment_pct / 100)
        total_paid = monthly_payment * s["term"] * 12
        comparison_data.append({
            "Scenario": s["name"],
            "Rate": f"{s['rate'] * 100:.2f}%",
            "Term": f"{s['term']} years",
            "House Value": f"£{hv:,.0f}",
            "Salary Multiplier": f"{hv / combined_gross:.2f}x",
            "Total Paid": f"£{total_paid:,.0f}",
            "Total Interest": f"£{total_paid - loan:,.0f}",
        })
        house_values.append(hv)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[s["name"] for s in scenarios], y=house_values,
        text=[f"£{v:,.0f}" for v in house_values], textposition="auto",
        marker_color=["green", "orange", "red"], name="House Value",
    ))
    for multiplier in multiplier_range:
        fig.add_hline(
            y=combined_gross * multiplier, line_dash="dot", line_color="blue",
            annotation_text=f"{multiplier}x salary", annotation_position="left",
        )
    fig.update_layout(title="House Value Comparison Across Scenarios",
                      yaxis_title="House Value [£]", height=400)

    df = pd.DataFrame(comparison_data)
    return dbc.Container([
        html.H5("Scenario Comparison", className="mb-3"),
        dbc.Row([dbc.Col([dcc.Graph(figure=fig)], md=12)]),
        dbc.Row([dbc.Col([
            html.H6("Detailed Comparison", className="mt-3 mb-2"),
            dash_table.DataTable(
                data=df.to_dict("records"),
                columns=[{"name": i, "id": i} for i in df.columns],
                style_cell={"textAlign": "left", "padding": "10px"},
                style_header={"backgroundColor": "rgb(230,230,230)", "fontWeight": "bold"},
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": "rgb(248,248,248)"}
                ],
            ),
        ], md=12)]),
    ])
```

- [ ] **Step 9: Replace `_build_breakdown_cards`**

Find and replace the entire `_build_breakdown_cards` function:

```python
def _build_breakdown_cards(rate, term, monthly_payment, down_payment_pct,
                            combined_gross, combined_net, target_multiplier):
    """Shared helper used by update_breakdown_results."""
    rate_decimal = rate / 100
    house_value = float(calculate_principal(monthly_payment, rate_decimal, term, down_payment_pct))
    loan_amount = house_value * (1 - down_payment_pct / 100)
    down_payment_amount = house_value * (down_payment_pct / 100)
    total_paid = monthly_payment * term * 12
    total_interest = total_paid - loan_amount
    effective_multiplier = house_value / combined_gross
    payment_to_net_ratio = (monthly_payment * 12) / combined_net * 100
    target_house_value = combined_gross * target_multiplier

    return dbc.Container([
        dbc.Row([
            dbc.Col([dbc.Card([
                dbc.CardHeader("Scenario Details", className="fw-bold"),
                dbc.CardBody([
                    html.P([html.Strong("Interest Rate: "), f"{rate:.2f}%"]),
                    html.P([html.Strong("Loan Term: "), f"{term} years"]),
                    html.P([html.Strong("Monthly Payment: "), f"£{monthly_payment:,.2f}"]),
                    html.P([html.Strong("Down Payment: "), f"{down_payment_pct}%"]),
                    html.P([html.Strong("Annual Salary: "), f"£{combined_gross:,}"]),
                    html.P([html.Strong("Annual Take-Home: "), f"£{combined_net:,.0f}"]),
                    html.P([
                        html.Strong("Payment to Take-Home: "),
                        f"{payment_to_net_ratio:.1f}%",
                        html.Span(
                            " ✓" if payment_to_net_ratio <= 35 else " ⚠",
                            className="text-success" if payment_to_net_ratio <= 35 else "text-warning",
                        ),
                    ]),
                ]),
            ], className="mb-3")], md=6),
            dbc.Col([dbc.Card([
                dbc.CardHeader("Affordability", className="fw-bold"),
                dbc.CardBody([
                    html.H4(f"£{house_value:,.0f}", className="text-primary"),
                    html.P("Maximum House Value (Payment-Based)", className="text-muted"),
                    html.Hr(),
                    html.P([html.Strong("Loan Amount: "), f"£{loan_amount:,.0f}"]),
                    html.P([html.Strong("Down Payment: "), f"£{down_payment_amount:,.0f}"]),
                    html.P([
                        html.Strong("Effective Multiplier: "),
                        f"{effective_multiplier:.2f}x",
                        html.Span(
                            " ✓" if effective_multiplier <= 5 else " ⚠",
                            className="text-success" if effective_multiplier <= 5 else "text-warning",
                        ),
                    ]),
                    html.Hr(),
                    html.P([html.Strong(f"Target ({target_multiplier}x salary): "),
                            f"£{target_house_value:,.0f}"], className="text-info"),
                    html.P([
                        html.Strong("Difference: "),
                        f"£{abs(house_value - target_house_value):,.0f}",
                        html.Span(
                            f" ({'over' if house_value > target_house_value else 'under'} target)",
                            className="text-muted",
                        ),
                    ]),
                ]),
            ], className="mb-3")], md=6),
        ]),
        dbc.Row([dbc.Col([dbc.Card([
            dbc.CardHeader("Total Cost Breakdown", className="fw-bold"),
            dbc.CardBody([
                html.P([html.Strong("Total Paid Over Life: "), f"£{total_paid:,.0f}"]),
                html.P([html.Strong("Total Interest Paid: "), f"£{total_interest:,.0f}"],
                       className="text-danger"),
                html.P([html.Strong("Interest as % of Loan: "),
                        f"{(total_interest / loan_amount * 100):.1f}%"]),
                html.Hr(),
                html.P([html.Strong("Total Cost (incl. down payment): "),
                        f"£{total_paid + down_payment_amount:,.0f}"], className="fw-bold"),
            ]),
        ])], md=12)]),
    ], fluid=True)
```

- [ ] **Step 10: Verify imports and run tests**

```bash
cd /Users/danyalsiddiqui/Projects/mortage_repayment
python -c "from callbacks import register_callbacks; print('OK')"
python -m pytest tests/ -v
```

Expected: `OK` then all 13 tests PASS.

- [ ] **Step 11: Smoke-test the app starts**

```bash
python app.py &
sleep 3
curl -s http://127.0.0.1:8050/_dash-layout | grep -c "partner-income-toggle" && echo "Toggle present"
curl -s http://127.0.0.1:8050/_dash-layout | grep -c "salary-2-slider" && echo "Salary-2 present"
kill %1
```

Expected: `1` / `Toggle present`, then `1` / `Salary-2 present`

- [ ] **Step 12: Commit**

```bash
git add callbacks.py
git commit -m "feat: dual income toggle and post-tax take-home ratio across all tabs"
```

---

## Self-Review

**Spec coverage:**

| Requirement | Task |
|-------------|------|
| `calculate_take_home_pay` with 2024/25 IT + NI rates | Task 1 |
| Gross → multipliers (lender metric unchanged) | Tasks 1+3 — `combined_gross` used for all multiplier lines |
| Net → payment-to-income % (Income Analysis, Breakdown, Amortization) | Task 3 — `payment_to_net_ratio` and `payment_to_income` use `combined_net` |
| Income Analysis card shows both gross and take-home | Task 3 — `_render_income_tab` shows "Annual Salary" + "Annual Take-Home" |
| `dbc.Checklist(switch=True)` toggle in global controls | Task 2 |
| `salary-2-slider` always in DOM (hidden), £0–£150k, default £0 | Task 2 |
| `toggle_partner_section` callback shows/hides `partner-income-section` | Task 3 step 2 |
| All salary-using callbacks receive `partner-income-toggle` + `salary-2-slider` | Task 3 steps 3+4 |
| `effective_salary_2 = 0` when toggle off | Task 3 — inline in both callbacks |
| Dual income label: "Person 1: £A + Partner: £B" | Task 3 — `_render_income_tab` `salary_display` |
| 25%/30% reference lines now use `combined_net` | Task 3 — `_render_income_tab` |
| Tests for all 5 tax bands + zero + below PA | Task 1 |
