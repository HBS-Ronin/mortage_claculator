# Mortgage Calculator Refactor & Repayment Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the single 792-line `main.py` into four focused modules, fix three bugs, vectorise the contour calculation, eliminate duplicated breakdown card code, remove `suppress_callback_exceptions`, and add a new Repayment Map tab.

**Architecture:** Extract pure calculation functions to `calculations.py`; define the full static Dash layout (including always-in-DOM breakdown and repayment map sections) in `layout.py`; register all callbacks via `register_callbacks(app)` in `callbacks.py`; wire everything together in `app.py`. Removing `suppress_callback_exceptions` is possible because the breakdown sliders and repayment graph div are promoted to always-in-DOM static layout nodes.

**Tech Stack:** Python 3, Dash 2.x, Dash Bootstrap Components, Plotly, NumPy, pandas, pytest

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `calculations.py` | Create | `calculate_principal`, `generate_amortization_schedule` — pure functions, no Dash imports |
| `layout.py` | Create | `get_layout()` — full Dash component tree incl. always-in-DOM breakdown/repayment sections |
| `callbacks.py` | Create | `register_callbacks(app)` — all callbacks + tab renderers + `_build_breakdown_cards` |
| `app.py` | Create | Dash instantiation, wires layout + callbacks, `if __name__` entrypoint |
| `tests/test_calculations.py` | Create | Unit tests for calculation functions |
| `main.py` | Delete | Replaced by the four files above |

---

## Task 1: Create `calculations.py` with array-safe functions

**Files:**
- Create: `calculations.py`
- Create: `tests/__init__.py`
- Create: `tests/test_calculations.py`

- [ ] **Step 1: Write failing tests for `calculate_principal`**

Create `tests/__init__.py` (empty) then create `tests/test_calculations.py`:

```python
import numpy as np
import pytest


def test_calculate_principal_basic():
    from calculations import calculate_principal
    # £1200/month, 5% annual rate, 25-year term, 10% down
    result = calculate_principal(1200, 0.05, 25, 10)
    assert abs(float(result) - 225_123) < 1000


def test_calculate_principal_zero_rate():
    from calculations import calculate_principal
    # At 0% rate: loan = payment * n_payments; house_value = loan (0% down)
    result = calculate_principal(1000, 0.0, 25, 0)
    assert float(result) == pytest.approx(1000 * 25 * 12)


def test_calculate_principal_down_payment():
    from calculations import calculate_principal
    # 10% down means house_value = loan / 0.9
    no_down = calculate_principal(1000, 0.05, 25, 0)
    with_down = calculate_principal(1000, 0.05, 25, 10)
    assert float(with_down) == pytest.approx(float(no_down) / 0.9, rel=1e-6)


def test_calculate_principal_array_inputs():
    from calculations import calculate_principal
    rates = np.array([0.03, 0.05, 0.07])
    terms = np.array([20.0, 25.0, 30.0])
    result = calculate_principal(1200, rates, terms, 10)
    assert result.shape == (3,)
    assert all(result > 0)
    # Lower rate should afford more
    assert result[0] > result[1] > result[2]


def test_calculate_principal_meshgrid():
    from calculations import calculate_principal
    rates = np.linspace(0.03, 0.07, 10)
    terms = np.arange(15, 36)
    R, T = np.meshgrid(rates, terms)
    result = calculate_principal(1200, R, T, 10)
    assert result.shape == R.shape
    assert np.all(result > 0)


def test_generate_amortization_schedule_basic():
    from calculations import generate_amortization_schedule
    schedule, payment = generate_amortization_schedule(300_000, 10, 0.05, 25)
    assert len(schedule) > 0
    assert payment > 0
    assert schedule[0]["Month"] == 1


def test_generate_amortization_schedule_zero_rate():
    from calculations import generate_amortization_schedule
    # At 0% every payment is equal principal, no interest
    schedule, payment = generate_amortization_schedule(300_000, 0, 0.0, 25)
    assert payment == pytest.approx(300_000 / (25 * 12), rel=1e-6)
    assert schedule[0]["Interest"] == "£0.00"


def test_generate_amortization_schedule_balance_reaches_zero():
    from calculations import generate_amortization_schedule
    schedule, _ = generate_amortization_schedule(200_000, 10, 0.04, 20)
    final_balance = float(schedule[-1]["Balance"].replace("£", "").replace(",", ""))
    assert final_balance == pytest.approx(0.0, abs=1.0)
```

- [ ] **Step 2: Run tests to verify they all fail**

```bash
cd /Users/danyalsiddiqui/Projects/mortage_repayment
python -m pytest tests/test_calculations.py -v 2>&1 | head -30
```

Expected: `ModuleNotFoundError: No module named 'calculations'`

- [ ] **Step 3: Create `calculations.py`**

```python
import numpy as np


def calculate_principal(monthly_payment, annual_rate, term_years, down_payment_pct):
    """Return max house value affordable at the given monthly payment.

    Supports scalar and numpy array inputs for annual_rate and term_years.
    Uses np.where to handle zero-rate edge case without branching on arrays.
    """
    n_payments = term_years * 12
    monthly_rate = annual_rate / 12
    safe_rate = np.where(monthly_rate == 0, np.finfo(float).eps, monthly_rate)
    principal = np.where(
        monthly_rate == 0,
        monthly_payment * n_payments,
        monthly_payment
        * ((1 + safe_rate) ** n_payments - 1)
        / (safe_rate * (1 + safe_rate) ** n_payments),
    )
    return principal / (1 - down_payment_pct / 100)


def generate_amortization_schedule(house_value, down_payment_pct, annual_rate, term_years):
    """Return (schedule, monthly_payment) for the given mortgage.

    schedule is a list of dicts with Month, Payment, Principal, Interest, Balance.
    Capped at 360 months (30 years) for display.
    """
    principal = house_value * (1 - down_payment_pct / 100)
    monthly_rate = annual_rate / 12
    n_payments = int(term_years * 12)

    if monthly_rate == 0:
        monthly_payment = principal / n_payments
    else:
        monthly_payment = (
            principal
            * (monthly_rate * (1 + monthly_rate) ** n_payments)
            / ((1 + monthly_rate) ** n_payments - 1)
        )

    schedule = []
    remaining_balance = principal

    for month in range(1, min(n_payments + 1, 361)):
        interest_payment = remaining_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        remaining_balance -= principal_payment
        schedule.append({
            "Month": month,
            "Payment": f"£{monthly_payment:.2f}",
            "Principal": f"£{principal_payment:.2f}",
            "Interest": f"£{interest_payment:.2f}",
            "Balance": f"£{max(0, remaining_balance):.2f}",
        })
        if remaining_balance <= 0:
            break

    return schedule, monthly_payment
```

- [ ] **Step 4: Run tests to verify they all pass**

```bash
python -m pytest tests/test_calculations.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add calculations.py tests/__init__.py tests/test_calculations.py
git commit -m "feat: extract calculations module with zero-rate fix and array support"
```

---

## Task 2: Create `layout.py`

**Files:**
- Create: `layout.py`

The layout promotes the breakdown controls and the repayment map section to always-in-DOM nodes. This is what allows `suppress_callback_exceptions` to be removed. A section-visibility callback (in Task 3) shows/hides them based on the active tab.

- [ ] **Step 1: Create `layout.py`**

```python
import dash_bootstrap_components as dbc
from dash import dcc, html


def get_layout():
    return dbc.Container(
        fluid=True,
        style={"padding": "20px"},
        children=[
            html.H2("Mortgage Affordability Calculator", className="text-center mb-4"),

            # ── Global controls ──────────────────────────────────────────────
            dbc.Card(
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Monthly Payment (£)", className="fw-bold"),
                            dcc.Slider(
                                id="payment-slider", min=500, max=3000, step=10, value=1200,
                                marks={i: f"£{i}" for i in range(500, 3001, 500)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ], md=6),
                        dbc.Col([
                            html.Label("Down Payment (%)", className="fw-bold"),
                            dcc.Slider(
                                id="down-payment-slider", min=5, max=40, step=5, value=10,
                                marks={i: f"{i}%" for i in range(5, 41, 5)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ], md=6),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Interest Rate Range (%)", className="fw-bold"),
                            dcc.RangeSlider(
                                id="rate-range-slider", min=2, max=8, step=0.5, value=[4, 5],
                                marks={i: f"{i}%" for i in range(2, 9)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ], md=6),
                        dbc.Col([
                            html.Label("Loan Term Range (Years)", className="fw-bold"),
                            dcc.RangeSlider(
                                id="term-range-slider", min=10, max=40, step=1, value=[15, 35],
                                marks={i: f"{i}y" for i in range(10, 41, 5)},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ], md=6),
                    ], className="mb-3"),
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
                ]),
                className="mb-4",
            ),

            # ── Tab navigation ───────────────────────────────────────────────
            dbc.Tabs([
                dbc.Tab(label="Affordability Map",   tab_id="tab-affordability"),
                dbc.Tab(label="Income Analysis",     tab_id="tab-income"),
                dbc.Tab(label="Detailed Breakdown",  tab_id="tab-breakdown"),
                dbc.Tab(label="Amortization Schedule", tab_id="tab-amortization"),
                dbc.Tab(label="Scenario Comparison", tab_id="tab-comparison"),
                dbc.Tab(label="Repayment Map",       tab_id="tab-repayment"),
            ], id="tabs", active_tab="tab-affordability", className="mb-3"),

            # ── Dynamic content for simple tabs (affordability/income/amortization/comparison)
            html.Div(id="tab-content"),

            # ── Breakdown section — always in DOM so its callback target exists ──
            html.Div(
                id="breakdown-section",
                style={"display": "none"},
                children=[
                    dbc.Card([
                        dbc.CardHeader("Adjust Parameters", className="fw-bold"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Interest Rate (%)", className="fw-bold"),
                                    dcc.Slider(
                                        id="breakdown-rate-slider", min=2, max=8, step=0.1, value=4.5,
                                        marks={i: f"{i}%" for i in range(2, 9)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ], md=6),
                                dbc.Col([
                                    html.Label("Loan Term (Years)", className="fw-bold"),
                                    dcc.Slider(
                                        id="breakdown-term-slider", min=10, max=40, step=1, value=25,
                                        marks={i: f"{i}y" for i in range(10, 41, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ], md=6),
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Target Salary Multiplier", className="fw-bold"),
                                    dcc.Slider(
                                        id="breakdown-multiplier-slider", min=2, max=6, step=0.1, value=4.25,
                                        marks={i: f"{i}x" for i in range(2, 7)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ], md=12),
                            ]),
                        ]),
                    ], className="mb-4"),
                    html.Div(id="breakdown-results"),
                ],
            ),

            # ── Repayment map section — always in DOM so its graph callback target exists ──
            html.Div(
                id="repayment-section",
                style={"display": "none"},
                children=[
                    dbc.Card([
                        dbc.CardHeader("Repayment Map Controls", className="fw-bold"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    html.Label("House Price (£)", className="fw-bold"),
                                    dcc.Slider(
                                        id="house-price-slider",
                                        min=100_000, max=500_000, step=1_000, value=250_000,
                                        marks={i: f"£{i // 1000}k" for i in range(100_000, 500_001, 100_000)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ], md=6),
                                dbc.Col([
                                    html.Label("Loan Term Range (Years)", className="fw-bold"),
                                    dcc.RangeSlider(
                                        id="repayment-term-range-slider",
                                        min=10, max=40, step=1, value=[15, 35],
                                        marks={i: f"{i}y" for i in range(10, 41, 5)},
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    ),
                                ], md=6),
                            ]),
                        ]),
                    ], className="mb-4"),
                    dcc.Graph(id="repayment-map-graph"),
                ],
            ),
        ],
    )
```

- [ ] **Step 2: Verify the layout file imports cleanly**

```bash
python -c "from layout import get_layout; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add layout.py
git commit -m "feat: add layout module with always-in-DOM breakdown and repayment map sections"
```

---

## Task 3: Create `callbacks.py`

**Files:**
- Create: `callbacks.py`

This file registers all callbacks. Key changes vs `main.py`:
- `render_tab_content` handles only 4 tabs (affordability, income, amortization, comparison)
- `toggle_section_visibility` shows/hides breakdown-section and repayment-section
- `_build_breakdown_cards` eliminates the ~60-line duplication
- Contour loop replaced with vectorised numpy call
- `fill='tonexty'` removed from Income Analysis first trace
- `update_repayment_map` is the new Repayment Map callback

- [ ] **Step 1: Create `callbacks.py`**

```python
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html, dash_table
import dash_bootstrap_components as dbc

from calculations import calculate_principal, generate_amortization_schedule

_SIMPLE_TABS = {"tab-affordability", "tab-income", "tab-amortization", "tab-comparison"}


def register_callbacks(app):

    # ── Section visibility ────────────────────────────────────────────────────

    @app.callback(
        Output("tab-content", "style"),
        Output("breakdown-section", "style"),
        Output("repayment-section", "style"),
        Input("tabs", "active_tab"),
    )
    def toggle_section_visibility(active_tab):
        show = {"display": "block"}
        hide = {"display": "none"}
        return (
            show if active_tab in _SIMPLE_TABS else hide,
            show if active_tab == "tab-breakdown" else hide,
            show if active_tab == "tab-repayment" else hide,
        )

    # ── Simple tabs ───────────────────────────────────────────────────────────

    @app.callback(
        Output("tab-content", "children"),
        Input("tabs", "active_tab"),
        Input("payment-slider", "value"),
        Input("down-payment-slider", "value"),
        Input("rate-range-slider", "value"),
        Input("term-range-slider", "value"),
        Input("salary-slider", "value"),
        Input("multiplier-range-slider", "value"),
        prevent_initial_call=False,
    )
    def render_tab_content(active_tab, monthly_payment, down_payment_pct,
                           rate_range, term_range, salary, multiplier_range):
        if active_tab == "tab-affordability":
            return _render_affordability_tab(monthly_payment, down_payment_pct,
                                             rate_range, term_range, salary, multiplier_range)
        if active_tab == "tab-income":
            return _render_income_tab(monthly_payment, down_payment_pct,
                                      rate_range, term_range, salary, multiplier_range)
        if active_tab == "tab-amortization":
            return _render_amortization_tab(monthly_payment, down_payment_pct,
                                            rate_range, term_range, salary)
        if active_tab == "tab-comparison":
            return _render_comparison_tab(monthly_payment, down_payment_pct,
                                          rate_range, term_range, salary, multiplier_range)
        return html.Div()  # breakdown and repayment map use their own sections

    # ── Breakdown tab ─────────────────────────────────────────────────────────

    @app.callback(
        Output("breakdown-results", "children"),
        Input("breakdown-rate-slider", "value"),
        Input("breakdown-term-slider", "value"),
        Input("breakdown-multiplier-slider", "value"),
        Input("payment-slider", "value"),
        Input("down-payment-slider", "value"),
        Input("salary-slider", "value"),
        Input("tabs", "active_tab"),
        prevent_initial_call=True,
    )
    def update_breakdown_results(rate, term, target_multiplier,
                                 monthly_payment, down_payment_pct, salary, active_tab):
        if active_tab != "tab-breakdown":
            return html.Div()
        return _build_breakdown_cards(rate, term, monthly_payment,
                                      down_payment_pct, salary, target_multiplier)

    # ── Repayment Map tab ─────────────────────────────────────────────────────

    @app.callback(
        Output("repayment-map-graph", "figure"),
        Input("house-price-slider", "value"),
        Input("repayment-term-range-slider", "value"),
        Input("rate-range-slider", "value"),
        Input("down-payment-slider", "value"),
        Input("payment-slider", "value"),
        prevent_initial_call=True,
    )
    def update_repayment_map(house_price, term_range, rate_range,
                             down_payment_pct, monthly_payment_budget):
        loan = house_price * (1 - down_payment_pct / 100)
        annual_rates = np.linspace(rate_range[0], rate_range[1], 100) / 100
        terms = np.arange(term_range[0], term_range[1] + 1, 1)
        R, T = np.meshgrid(annual_rates, terms)

        monthly_rates = R / 12
        n_payments = T * 12
        safe_rate = np.where(monthly_rates == 0, np.finfo(float).eps, monthly_rates)
        repayments = np.where(
            monthly_rates == 0,
            loan / n_payments,
            loan * safe_rate * (1 + safe_rate) ** n_payments
            / ((1 + safe_rate) ** n_payments - 1),
        )

        fig = go.Figure(data=go.Heatmap(
            z=repayments,
            x=annual_rates * 100,
            y=terms,
            colorscale="RdYlGn_r",
            colorbar=dict(title="Monthly Repayment (£)"),
            hovertemplate=(
                "Rate: %{x:.2f}%<br>Term: %{y} years<br>"
                "Repayment: £%{z:,.0f}/mo<extra></extra>"
            ),
        ))

        fig.add_contour(
            z=repayments,
            x=annual_rates * 100,
            y=terms,
            contours=dict(type="constraint", operation="=", value=monthly_payment_budget),
            line=dict(color="rgba(0, 0, 200, 0.85)", width=3, dash="dash"),
            showscale=False,
            hoverinfo="skip",
            name=f"Budget: £{monthly_payment_budget:,.0f}/mo",
        )

        down_pct_label = f"{down_payment_pct}% down"
        fig.update_layout(
            title=(
                f"Monthly Repayments — £{house_price:,.0f} house, {down_pct_label}<br>"
                f"<sup>Dashed line = your budget (£{monthly_payment_budget:,.0f}/mo)</sup>"
            ),
            xaxis_title="Interest Rate (%)",
            yaxis_title="Loan Term (Years)",
            height=600,
            showlegend=False,
        )
        return fig


# ── Tab render helpers ────────────────────────────────────────────────────────

def _render_affordability_tab(monthly_payment, down_payment_pct, rate_range, term_range,
                               salary, multiplier_range):
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
        salary_based_value = salary * multiplier
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


def _render_income_tab(monthly_payment, down_payment_pct, rate_range, term_range,
                        salary, multiplier_range):
    mid_rate = (rate_range[0] + rate_range[1]) / 2 / 100
    mid_term = (term_range[0] + term_range[1]) // 2

    payment_based_value = float(calculate_principal(monthly_payment, mid_rate, mid_term, down_payment_pct))
    multipliers = np.linspace(multiplier_range[0], multiplier_range[1], 50)
    salary_based_values = salary * multipliers
    mid_multiplier = (multiplier_range[0] + multiplier_range[1]) / 2
    salary_based_value = salary * mid_multiplier

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
        max_monthly = (salary / 12) * (ratio_pct / 100)
        ratio_house = float(calculate_principal(max_monthly, mid_rate, mid_term, down_payment_pct))
        ratio_mult = ratio_house / salary
        if multiplier_range[0] <= ratio_mult <= multiplier_range[1]:
            fig.add_trace(go.Scatter(
                x=[multiplier_range[0], multiplier_range[1]],
                y=[ratio_house, ratio_house],
                mode="lines",
                name=f"{ratio_pct}% payment ratio",
                line=dict(color="orange" if ratio_pct == 25 else "red", width=2, dash="dot"),
            ))

    for mult in [3, 4, 4.5, 5]:
        if multiplier_range[0] <= mult <= multiplier_range[1]:
            val = salary * mult
            fig.add_trace(go.Scatter(
                x=[mult], y=[val], mode="markers+text",
                name=f"{mult}x salary",
                marker=dict(size=12, color="red"),
                text=f"£{val:,.0f}", textposition="top center",
            ))

    fig.update_layout(
        title=f"Income-Based Affordability Analysis (Salary: £{salary:,})",
        xaxis_title="Salary Multiplier", yaxis_title="House Value [£]",
        height=400, showlegend=True, hovermode="x unified",
        legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=0.01,
                    bgcolor="rgba(255,255,255,0.8)", bordercolor="rgba(0,0,0,0.2)", borderwidth=1),
    )

    payment_to_salary_ratio = (monthly_payment * 12) / salary * 100
    loan_to_income = (payment_based_value * (1 - down_payment_pct / 100)) / salary

    return dbc.Container([
        dbc.Row([dbc.Col([dcc.Graph(figure=fig)], md=12)], className="mb-3"),
        dbc.Row([
            dbc.Col([dbc.Card([
                dbc.CardHeader("Income Analysis", className="fw-bold"),
                dbc.CardBody([
                    html.P([html.Strong("Annual Salary: "), f"£{salary:,}"]),
                    html.P([html.Strong("Annual Payment: "),
                            f"£{monthly_payment * 12:,} ({payment_to_salary_ratio:.1f}% of salary)"]),
                    html.P([
                        html.Strong("Payment to Salary Ratio: "),
                        f"{payment_to_salary_ratio:.1f}%",
                        html.Span(
                            " ✓ Within recommended 30-35%" if payment_to_salary_ratio <= 35
                            else " ⚠ Above recommended 30-35%",
                            className="text-success" if payment_to_salary_ratio <= 35 else "text-warning",
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
                            f"{payment_based_value / salary:.2f}x salary"]),
                ]),
            ], className="mb-3")], md=6),
        ]),
        dbc.Row([dbc.Col([dbc.Alert([
            html.H6("💡 Lender Guidelines", className="alert-heading"),
            html.P("Most UK lenders offer 4-4.5x salary. Some offer up to 5-5.5x for higher earners."),
            html.P("Higher multipliers mean larger loans and more interest paid over time.", className="mb-0"),
        ], color="info")], md=12)]),
    ])


def _render_amortization_tab(monthly_payment, down_payment_pct, rate_range, term_range, salary):
    mid_rate = (rate_range[0] + rate_range[1]) / 2 / 100
    mid_term = (term_range[0] + term_range[1]) // 2

    house_value = float(calculate_principal(monthly_payment, mid_rate, mid_term, down_payment_pct))
    schedule, actual_payment = generate_amortization_schedule(
        house_value, down_payment_pct, mid_rate, mid_term
    )
    df = pd.DataFrame(schedule)

    effective_multiplier = house_value / salary
    payment_to_income = (actual_payment * 12) / salary * 100

    return dbc.Container([
        html.H5("Amortization Schedule (First 30 years)", className="mb-3"),
        html.P(f"Based on: £{house_value:,.0f} house, {mid_rate * 100:.2f}% rate, {mid_term} year term"),
        html.P([
            html.Strong("Actual monthly payment: "),
            f"£{actual_payment:.2f}",
            html.Span(f" ({payment_to_income:.1f}% of annual salary)", className="text-muted ms-2"),
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


def _render_comparison_tab(monthly_payment, down_payment_pct, rate_range, term_range,
                            salary, multiplier_range):
    scenarios = [
        {"name": "Best Case",    "rate": rate_range[0] / 100, "term": term_range[1]},
        {"name": "Average Case", "rate": sum(rate_range) / 2 / 100, "term": (term_range[0] + term_range[1]) // 2},
        {"name": "Worst Case",   "rate": rate_range[1] / 100, "term": term_range[0]},
    ]

    comparison_data = []
    for s in scenarios:
        hv = float(calculate_principal(monthly_payment, s["rate"], s["term"], down_payment_pct))
        loan = hv * (1 - down_payment_pct / 100)
        total_paid = monthly_payment * s["term"] * 12
        comparison_data.append({
            "Scenario": s["name"],
            "Rate": f"{s['rate'] * 100:.2f}%",
            "Term": f"{s['term']} years",
            "House Value": f"£{hv:,.0f}",
            "Salary Multiplier": f"{hv / salary:.2f}x",
            "Total Paid": f"£{total_paid:,.0f}",
            "Total Interest": f"£{total_paid - loan:,.0f}",
        })

    house_values = [float(calculate_principal(monthly_payment, s["rate"], s["term"], down_payment_pct))
                    for s in scenarios]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[s["name"] for s in scenarios], y=house_values,
        text=[f"£{v:,.0f}" for v in house_values], textposition="auto",
        marker_color=["green", "orange", "red"], name="House Value",
    ))
    for multiplier in multiplier_range:
        fig.add_hline(
            y=salary * multiplier, line_dash="dot", line_color="blue",
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


def _build_breakdown_cards(rate, term, monthly_payment, down_payment_pct, salary, target_multiplier):
    """Shared helper used by update_breakdown_results."""
    rate_decimal = rate / 100
    house_value = float(calculate_principal(monthly_payment, rate_decimal, term, down_payment_pct))
    loan_amount = house_value * (1 - down_payment_pct / 100)
    down_payment_amount = house_value * (down_payment_pct / 100)
    total_paid = monthly_payment * term * 12
    total_interest = total_paid - loan_amount
    effective_multiplier = house_value / salary
    payment_to_salary_ratio = (monthly_payment * 12) / salary * 100
    target_house_value = salary * target_multiplier

    return dbc.Container([
        dbc.Row([
            dbc.Col([dbc.Card([
                dbc.CardHeader("Scenario Details", className="fw-bold"),
                dbc.CardBody([
                    html.P([html.Strong("Interest Rate: "), f"{rate:.2f}%"]),
                    html.P([html.Strong("Loan Term: "), f"{term} years"]),
                    html.P([html.Strong("Monthly Payment: "), f"£{monthly_payment:,.2f}"]),
                    html.P([html.Strong("Down Payment: "), f"{down_payment_pct}%"]),
                    html.P([html.Strong("Annual Salary: "), f"£{salary:,}"]),
                    html.P([
                        html.Strong("Payment to Salary: "),
                        f"{payment_to_salary_ratio:.1f}%",
                        html.Span(
                            " ✓" if payment_to_salary_ratio <= 35 else " ⚠",
                            className="text-success" if payment_to_salary_ratio <= 35 else "text-warning",
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

- [ ] **Step 2: Verify `callbacks.py` imports cleanly (no Dash app needed for import check)**

```bash
python -c "from callbacks import register_callbacks; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add callbacks.py
git commit -m "feat: add callbacks module — vectorised contour, no duplication, repayment map"
```

---

## Task 4: Create `app.py` and remove `main.py`

**Files:**
- Create: `app.py`
- Delete: `main.py`

- [ ] **Step 1: Create `app.py`**

```python
import dash_bootstrap_components as dbc
from dash import Dash

from layout import get_layout
from callbacks import register_callbacks

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = get_layout()
register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)
```

- [ ] **Step 2: Verify the app starts without errors**

```bash
python app.py &
sleep 3
curl -s http://127.0.0.1:8050/ | grep -c "Mortgage" && echo "App serving OK"
kill %1
```

Expected: `1` then `App serving OK`

- [ ] **Step 3: Delete `main.py`**

```bash
rm main.py
```

- [ ] **Step 4: Run the full test suite to confirm nothing regressed**

```bash
python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py && git rm main.py
git commit -m "feat: wire app.py entrypoint, remove main.py"
```

---

## Task 5: Manual verification of all tabs

- [ ] **Start the app**

```bash
python app.py
```

Open `http://127.0.0.1:8050/` in a browser.

- [ ] **Affordability Map tab** — contour renders immediately; hover shows rate/term/value; salary multiplier dashed lines appear; adjust sliders and confirm the map updates.

- [ ] **Income Analysis tab** — chart shows two lines (salary-based and payment-based); no shaded fill area under the first trace; salary context cards show correct figures.

- [ ] **Detailed Breakdown tab** — three cards render when tab is first visited; adjusting the breakdown sliders updates the cards; global payment/salary sliders also update cards.

- [ ] **Amortization Schedule tab** — table renders with Month/Payment/Principal/Interest/Balance columns; first row interest is larger than last row interest.

- [ ] **Scenario Comparison tab** — bar chart and table both render; salary multiplier reference lines appear on chart.

- [ ] **Repayment Map tab** — heatmap renders showing green (low) to red (high) repayments; dashed budget contour line is visible; adjusting house price slider updates the heatmap; adjusting term range slider changes the y-axis rows; adjusting global rate range and down payment sliders also update the heatmap.

- [ ] **Commit verification**

```bash
git add -A
git status  # should show nothing untracked or modified
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered by |
|-----------------|------------|
| Bug: zero-rate in `generate_amortization_schedule` | Task 1 — `calculations.py` fix + test |
| Bug: `fill='tonexty'` removed | Task 3 — `_render_income_tab` has no `fill=` on first trace |
| Performance: vectorised contour | Task 3 — `_render_affordability_tab` uses `calculate_principal(monthly_payment, R, T, ...)` directly |
| Deduplication: `_build_breakdown_cards` | Task 3 — shared helper, called by `update_breakdown_results` |
| Architecture: module split | Tasks 1-4 — `calculations.py`, `layout.py`, `callbacks.py`, `app.py` |
| Architecture: remove `suppress_callback_exceptions` | Task 2+4 — breakdown/repayment sections always in DOM; `app.py` does not set this flag |
| Architecture: lazy tab rendering | Task 3 — `toggle_section_visibility` hides inactive sections; `update_breakdown_results` guards on `active_tab` |
| New tab: Repayment Map heatmap | Tasks 2+3 — `repayment-section` in layout, `update_repayment_map` callback |
| House price slider: £100k–£500k, step £1k, default £250k | Task 2 — `layout.py` |
| Loan term range slider (y-axis control) | Task 2 — `repayment-term-range-slider` in layout |
| Budget constraint contour line | Task 3 — `fig.add_contour` with `type="constraint"` |
| Colour scale green=low, red=high | Task 3 — `colorscale="RdYlGn_r"` |
