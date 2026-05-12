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
