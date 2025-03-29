import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# App title
st.set_page_config(layout="wide")
st.title("📊 Sensitivity & Scenario Analysis Tool")
st.write("Analyze business profitability by adjusting key financial factors.")

# --- User Inputs ---
st.header("📌 Business Inputs")

col1, col2 = st.columns(2)
with col1:
    with st.expander("Revenue"):
        sales_units = st.number_input("Sales/Service Units", min_value=1, value=1000, step=10)
        price_per_unit = st.number_input("Price per Unit ($)", min_value=0.0, value=50.0, step=0.5)

    with st.expander("Costs"):
        variable_cost_per_unit = st.number_input("Variable Cost per Unit ($)", min_value=0.0, value=20.0, step=0.5)
        fixed_cost = st.number_input("Total Fixed Costs ($)", min_value=0.0, value=5000.0, step=100.0)

with col2:
    with st.expander("Taxes and Investment"):
        tax_rate = st.slider("Tax Rate (%)", min_value=0, max_value=50, value=20, step=1)
        initial_investment = st.number_input("Initial Investment ($)", min_value=0.0, value=20000.0, step=100.0)

    with st.expander("NPV Parameters"):
        discount_rate = st.slider("Discount Rate (%)", min_value=1, max_value=20, value=10, step=1) / 100
        years = st.number_input("Investment Duration (Years)", min_value=1, value=5, step=1)

# --- Base Calculations ---
revenue = sales_units * price_per_unit
total_variable_cost = sales_units * variable_cost_per_unit
ebit = revenue - total_variable_cost - fixed_cost
tax_paid = ebit * (tax_rate / 100) if ebit > 0 else 0
net_income = ebit - tax_paid

# Generate cash flows and NPV
cash_flows = [net_income for _ in range(years)]
discounted_cash_flows = [cf / (1 + discount_rate)**(i+1) for i, cf in enumerate(cash_flows)]
npv = sum(discounted_cash_flows) - initial_investment

# --- Display Base Results ---
st.header("📈 Financial Summary")

metric1, metric2, metric3, metric4 = st.columns(4)
metric1.metric("Total Revenue", f"${revenue:,.2f}")
metric2.metric("EBIT", f"${ebit:,.2f}")
metric3.metric("Net Income", f"${net_income:,.2f}")
metric4.metric("NPV", f"${npv:,.2f}", "Profitable" if npv >= 0 else "Not Profitable")

# NPV Details
with st.expander("NPV Calculation Details"):
    df_npv = pd.DataFrame({
        "Year": range(1, years+1),
        "Cash Flow": cash_flows,
        "Discounted Cash Flow": discounted_cash_flows
    })
    st.dataframe(df_npv.style.format({
        "Cash Flow": "${:,.2f}", 
        "Discounted Cash Flow": "${:,.2f}"
    }))

# --- Sensitivity Analysis ---
st.header("📊 Sensitivity Analysis")

# Sensitivity parameters
sens_col1, sens_col2 = st.columns(2)
with sens_col1:
    sensitivity_range = st.slider("Percentage Change Range", 0, 50, 20, 5)
with sens_col2:
    sensitivity_steps = st.slider("Number of Steps", 3, 11, 5, 2)

# Generate sensitivity data
factors = ["Sales", "Price", "Variable Cost", "Fixed Cost"]
sensitivity_results = []

for factor in factors:
    for pct_change in np.linspace(-sensitivity_range, sensitivity_range, sensitivity_steps):
        # Apply percentage change to the current factor only
        if factor == "Sales":
            adj_sales = sales_units * (1 + pct_change/100)
            adj_price = price_per_unit
            adj_vc = variable_cost_per_unit
            adj_fc = fixed_cost
        elif factor == "Price":
            adj_sales = sales_units
            adj_price = price_per_unit * (1 + pct_change/100)
            adj_vc = variable_cost_per_unit
            adj_fc = fixed_cost
        elif factor == "Variable Cost":
            adj_sales = sales_units
            adj_price = price_per_unit
            adj_vc = variable_cost_per_unit * (1 + pct_change/100)
            adj_fc = fixed_cost
        else:  # Fixed Cost
            adj_sales = sales_units
            adj_price = price_per_unit
            adj_vc = variable_cost_per_unit
            adj_fc = fixed_cost * (1 + pct_change/100)

        # Recalculate financials with adjusted values
        adj_revenue = adj_sales * adj_price
        adj_ebit = adj_revenue - (adj_sales * adj_vc) - adj_fc
        adj_net_income = adj_ebit * (1 - tax_rate/100) if adj_ebit > 0 else adj_ebit
        adj_cash_flows = [adj_net_income] * years
        adj_discounted_cash_flows = [cf / (1 + discount_rate)**(i+1) for i, cf in enumerate(adj_cash_flows)]
        adj_npv = sum(adj_discounted_cash_flows) - initial_investment

        sensitivity_results.append({
            "Factor": factor,
            "Change (%)": pct_change,
            "NPV": adj_npv
        })

# Create DataFrame and plot
df_sensitivity = pd.DataFrame(sensitivity_results)

if not df_sensitivity.empty:
    fig_sens = px.line(
        df_sensitivity, 
        x="Change (%)", 
        y="NPV", 
        color="Factor",
        title=f"NPV Sensitivity Analysis (±{sensitivity_range}%)",
        labels={"NPV": "NPV ($)", "Change (%)": "Percentage Change"},
        markers=True
    )
    fig_sens.update_layout(
        hovermode="x unified",
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f"
    )
    st.plotly_chart(fig_sens, use_container_width=True)
    
    # Show sensitivity table
    with st.expander("View Sensitivity Data"):
        st.dataframe(df_sensitivity.pivot_table(
            index="Change (%)", 
            columns="Factor", 
            values="NPV"
        ).style.format("${:,.2f}"))

# --- Scenario Analysis ---
st.header("🌐 Scenario Analysis")

# Scenario selection
scenario = st.radio("Select Scenario", 
                   ["Base Case", "Best Case", "Worst Case", "Custom Scenario"],
                   horizontal=True)

if scenario == "Best Case":
    changes = {
        "Sales": 20,
        "Price": 10,
        "Variable Cost": -10,
        "Fixed Cost": -5
    }
elif scenario == "Worst Case":
    changes = {
        "Sales": -15,
        "Price": -5,
        "Variable Cost": 10,
        "Fixed Cost": 10
    }
elif scenario == "Custom Scenario":
    changes = {
        "Sales": st.number_input("Sales Change (%)", value=0, step=1),
        "Price": st.number_input("Price Change (%)", value=0, step=1),
        "Variable Cost": st.number_input("Variable Cost Change (%)", value=0, step=1),
        "Fixed Cost": st.number_input("Fixed Cost Change (%)", value=0, step=1)
    }
else:  # Base Case
    changes = {
        "Sales": 0,
        "Price": 0,
        "Variable Cost": 0,
        "Fixed Cost": 0
    }

# Apply scenario changes
adj_sales = sales_units * (1 + changes["Sales"]/100)
adj_price = price_per_unit * (1 + changes["Price"]/100)
adj_vc = variable_cost_per_unit * (1 + changes["Variable Cost"]/100)
adj_fc = fixed_cost * (1 + changes["Fixed Cost"]/100)

# Recalculate financials
adj_revenue = adj_sales * adj_price
adj_ebit = adj_revenue - (adj_sales * adj_vc) - adj_fc
adj_net_income = adj_ebit * (1 - tax_rate/100) if adj_ebit > 0 else adj_ebit
adj_cash_flows = [adj_net_income] * years
adj_discounted_cash_flows = [cf / (1 + discount_rate)**(i+1) for i, cf in enumerate(adj_cash_flows)]
adj_npv = sum(adj_discounted_cash_flows) - initial_investment

# Display scenario comparison
scenario_col1, scenario_col2 = st.columns(2)

with scenario_col1:
    st.metric("Scenario NPV", 
              f"${adj_npv:,.2f}", 
              delta=f"${adj_npv - npv:,.2f} vs Base Case")

with scenario_col2:
    st.metric("Profitability Change", 
              "Improved" if adj_npv > npv else "Worsened",
              delta=f"{(adj_npv - npv)/abs(npv)*100:.1f}%" if npv != 0 else "N/A")

# Scenario comparison chart
scenario_data = pd.DataFrame({
    "Metric": ["Revenue", "EBIT", "Net Income", "NPV"],
    "Base Case": [revenue, ebit, net_income, npv],
    scenario: [adj_revenue, adj_ebit, adj_net_income, adj_npv]
})

fig_scenario = px.bar(
    scenario_data.melt(id_vars="Metric"), 
    x="Metric", 
    y="value", 
    color="variable",
    barmode="group",
    title=f"Scenario Comparison: Base Case vs {scenario}",
    labels={"value": "Amount ($)", "variable": "Scenario"}
)
fig_scenario.update_layout(yaxis_tickprefix="$")
st.plotly_chart(fig_scenario, use_container_width=True)

# Show scenario details
with st.expander("Scenario Details"):
    st.dataframe(scenario_data.style.format({
        "Base Case": "${:,.2f}",
        scenario: "${:,.2f}"
    }))