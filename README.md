# Mortgage Affordability Calculator

An interactive web application for mortgage affordability analysis with multiple visualization modes and detailed financial breakdowns.

## Features

### 🎛️ Interactive Controls
- **Monthly Payment Slider**: Adjust your target monthly payment (£500-£3000)
- **Down Payment Slider**: Set your down payment percentage (5-40%)
- **Interest Rate Range**: Customize the interest rate range to explore (2-8%)
- **Loan Term Range**: Select the loan term range in years (10-40 years)
- **Annual Salary Slider**: Input your annual salary (£20k-£150k)
- **Salary Multiplier Range**: Set typical lender multiplier range (2x-6x)

### 📊 Five Analysis Tabs

#### 1. Affordability Map
- Interactive contour plot showing house values across different interest rates and loan terms
- Hover over any point to see exact values
- Visual representation of how rate and term affect affordability
- Color-coded visualization for quick insights
- Salary multiplier reference lines overlaid on the map

#### 2. Income Analysis
- **Salary-Based Affordability Chart**: Visualize how salary multipliers affect your buying power
- **Payment to Salary Ratio**: Check if your monthly payments are within the recommended 30-35% of salary
- **Loan to Income Ratio**: See your loan amount as a multiple of your salary
- **Comparison View**: Direct comparison between payment-based and salary-based affordability
- **Lender Guidelines**: Built-in guidance on typical UK mortgage multipliers (4-5.5x salary)
- **Visual Indicators**: Green/amber warnings for healthy vs. stretched ratios

#### 3. Detailed Breakdown
- Comprehensive financial summary with three information cards:
  - **Scenario Details**: Current interest rate, term, payment settings, and annual salary
  - **Affordability**: Maximum house value, loan amount, down payment required, and salary multiplier
  - **Total Cost Breakdown**: Total amount paid, total interest, and overall cost including down payment
- Uses mid-range values from your selected ranges
- Visual indicators showing if salary multiplier is within typical lending limits

#### 4. Amortization Schedule
- Month-by-month payment breakdown for the first 30 years
- Shows principal vs interest for each payment
- Displays remaining balance over time
- Paginated table for easy navigation
- Based on calculated actual monthly payment
- Shows payment as percentage of annual salary
- Displays effective salary multiplier

#### 5. Scenario Comparison
- Compares three scenarios side-by-side:
  - **Best Case**: Lowest rate with longest term
  - **Average Case**: Mid-range rate and term
  - **Worst Case**: Highest rate with shortest term
- Visual bar chart comparison with salary multiplier reference lines
- Detailed table with house values, salary multipliers, total paid, and total interest for each scenario
- Shows how different rate/term combinations affect your effective borrowing multiplier

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python3 main.py
```

3. Open your browser and navigate to:
```
http://127.0.0.1:8050/
```

## Dependencies

- `numpy`: Numerical calculations
- `pandas`: Data manipulation and table generation
- `plotly`: Interactive visualizations
- `dash`: Web application framework
- `dash-bootstrap-components`: Bootstrap styling for Dash

## How It Works

The calculator uses the standard mortgage formula:

```
M = P × [r(1 + r)^n] / [(1 + r)^n - 1]
```

Where:
- M = Monthly payment
- P = Principal (loan amount)
- r = Monthly interest rate
- n = Number of payments

The application solves this formula in reverse to determine the maximum house value you can afford based on your monthly payment budget, then adjusts for down payment percentage.

## Usage Tips

1. **Start with your income**: Input your annual salary to see realistic affordability limits
2. **Set your budget**: Adjust monthly payment slider - try to keep payments under 35% of your annual salary
3. **Check salary multipliers**: Use the Income Analysis tab to see if you're within typical lending limits (4-5x)
4. **Adjust down payment**: Higher down payment = more house for same monthly payment
5. **Explore rates**: See how interest rate changes affect affordability
6. **Compare scenarios**: Use the comparison tab to understand best/worst cases across rates and terms
7. **Check amortization**: Review how much of your payment goes to interest vs principal
8. **Balance approaches**: The Income Analysis tab helps you find the sweet spot between what you can afford monthly and what lenders will approve based on salary

## License

This project is open source and available for personal and educational use.
