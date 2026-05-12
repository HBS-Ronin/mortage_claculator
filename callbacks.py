import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html, dash_table
import dash_bootstrap_components as dbc

from calculations import calculate_principal, generate_amortization_schedule, calculate_take_home_pay

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

    @app.callback(
        Output("partner-income-section", "style"),
        Input("partner-income-toggle", "value"),
    )
    def toggle_partner_section(partner_toggle):
        return {"display": "block"} if partner_toggle else {"display": "none"}

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

    # ── Repayment Map tab ─────────────────────────────────────────────────────

    @app.callback(
        Output("repayment-map-graph", "figure"),
        Input("house-price-slider", "value"),
        Input("repayment-term-range-slider", "value"),
        Input("rate-range-slider", "value"),
        Input("down-payment-slider", "value"),
        Input("payment-slider", "value"),
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
