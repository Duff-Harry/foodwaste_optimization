"""
app.py
======
Streamlit web interface for the Food Waste Processing
Optimization Tool (PhD Research).
 
Tabs:
    1. Instructions
    2. Feed Inputs
    3. Economic Parameters
    4. Run Optimization
    5. Results — Pareto Front
    6. Results — Cost Breakdown
"""
 
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
 
from food_waste_database import (
    get_waste_types,
    get_composition,
    get_description,
    get_references,
    get_HHV,
    validate_composition,
)
from model.solver import run_optimization
 
# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Food Waste Optimization Tool",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
 
# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        color: #2E7D32;
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .sub-title {
        font-size: 1rem;
        color: #555;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1B5E20;
        border-bottom: 2px solid #A5D6A7;
        padding-bottom: 4px;
        margin-bottom: 12px;
    }
    .info-box {
        background: #F1F8E9;
        border-left: 4px solid #66BB6A;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    .warning-box {
        background: #FFF8E1;
        border-left: 4px solid #FFA000;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 12px;
    }
    .result-metric {
        background: #E8F5E9;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)
 
# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="main-title">♻️ Food Waste Processing Optimization</div>',
            unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Multi-objective optimization: minimize cost & GHG emissions '
    '| PhD Research Tool</div>',
    unsafe_allow_html=True
)
 
# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📋 Instructions",
    "🗑️ Feed Inputs",
    "💰 Economic Parameters",
    "⚙️ Run Optimization",
    "📈 Pareto Front",
    "📊 Cost Breakdown",
])
 
 
# ============================================================
# TAB 1 — INSTRUCTIONS
# ============================================================
with tab1:
    st.markdown('<div class="section-header">Welcome</div>', unsafe_allow_html=True)
    st.markdown("""
    This tool optimizes the processing of food waste using a **Mixed Integer Nonlinear
    Programming (MINLP)** model. It simultaneously minimizes **Net Annual Cost (NAC)**
    and **Greenhouse Gas (GHG) emissions** to generate a Pareto front of optimal solutions.
 
    **How to use this tool:**
 
    1. **Feed Inputs** — Select your food waste type or enter your own composition.
       Set the feed flow rate and operating hours.
 
    2. **Economic Parameters** — Set electricity cost, tipping fee, labor cost,
       capital recovery factor, and product selling prices.
 
    3. **Run Optimization** — Click the button to run the optimization.
       The BARON solver will find the optimal technology configuration.
 
    4. **Pareto Front** — View the trade-off between cost and GHG emissions
       across all Pareto-optimal solutions.
 
    5. **Cost Breakdown** — View the detailed cost breakdown for each solution.
    """)
 
    st.markdown('<div class="section-header">Technology Options</div>',
                unsafe_allow_html=True)
 
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**Mechanical Pretreatment**")
        st.markdown("- SHR — Shredder\n- MCR — Macerator\n- Bypass")
    with col2:
        st.markdown("**Biological Pretreatment**")
        st.markdown("- AER — Aerobic Biodigester\n- ENZ — Enzymatic Hydrolysis\n- Bypass")
    with col3:
        st.markdown("**Conversion Technology**")
        st.markdown("- HTL — Hydrothermal Liquefaction\n- AND — Anaerobic Digestion\n"
                    "- SLF — Sanitary Landfill\n- CMP — Composting\n"
                    "- WWT — Wastewater Treatment\n- INC — Incineration")
 
    st.markdown("""
    > **Note:** The model uses the **BARON** solver for global optimization of MINLP problems.
    > Each Pareto point may take 2–5 minutes to solve. With 10 Pareto points, expect
    > approximately 20–50 minutes total runtime.
    """)
 
 
# ============================================================
# TAB 2 — FEED INPUTS
# ============================================================
with tab2:
    st.markdown('<div class="section-header">Food Waste Type</div>',
                unsafe_allow_html=True)
 
    waste_types = get_waste_types()
    selected_waste = st.selectbox(
        "Select food waste type",
        waste_types,
        index=0,
        help="Select a food waste type to auto-fill composition, "
             "or choose 'Custom' to enter your own data."
    )
 
    # Show description and references
    desc = get_description(selected_waste)
    refs = get_references(selected_waste)
    st.markdown(f'<div class="info-box">{desc}</div>', unsafe_allow_html=True)
    st.caption(f"References: {', '.join(refs)}")
 
    # Load composition
    comp = get_composition(selected_waste)
    is_custom = selected_waste == "Custom (Enter Your Own Data)"
 
    st.markdown('<div class="section-header">Feed Composition (Wet Basis)</div>',
                unsafe_allow_html=True)
 
    col1, col2, col3, col4 = st.columns(4)
 
    with col1:
        WATER = st.number_input("Water (WATER)", 0.0, 1.0,
                                float(comp["WATER"]),
                                step=0.001, format="%.4f",
                                disabled=not is_custom)
        CBH   = st.number_input("Carbohydrates (CBH)", 0.0, 1.0,
                                float(comp["CBH"]),
                                step=0.001, format="%.4f",
                                disabled=not is_custom)
 
    with col2:
        PRT   = st.number_input("Protein (PRT)", 0.0, 1.0,
                                float(comp["PRT"]),
                                step=0.001, format="%.4f",
                                disabled=not is_custom)
        FAT   = st.number_input("Fat / Lipid (FAT)", 0.0, 1.0,
                                float(comp["FAT"]),
                                step=0.001, format="%.4f",
                                disabled=not is_custom)
 
    with col3:
        OTH   = st.number_input("Other Organics (OTH)", 0.0, 1.0,
                                float(comp["OTH"]),
                                step=0.001, format="%.4f",
                                disabled=not is_custom)
        ASH   = st.number_input("Ash (ASH)", 0.0, 1.0,
                                float(comp["ASH"]),
                                step=0.001, format="%.4f",
                                disabled=not is_custom)
 
    with col4:
        FC    = st.number_input("Fixed Carbon (FC)", 0.0, 1.0,
                                float(comp["FIXED_CARBON"]),
                                step=0.001, format="%.4f",
                                disabled=not is_custom)
        total = WATER + CBH + PRT + FAT + OTH + ASH + FC
        st.metric("Sum of fractions", f"{total:.4f}",
                  delta=f"{total - 1.0:.4f}",
                  delta_color="off" if abs(total - 1.0) < 0.01 else "inverse")
 
    if abs(total - 1.0) > 0.01:
        st.markdown(
            '<div class="warning-box">⚠️ Fractions do not sum to 1.0. '
            'Please adjust the values.</div>',
            unsafe_allow_html=True
        )
 
    st.markdown('<div class="section-header">Operating Conditions</div>',
                unsafe_allow_html=True)
 
    col1, col2 = st.columns(2)
    with col1:
        Qf   = st.number_input("Feed flow rate (kg/hr)", 100.0, 50000.0,
                               1000.0, step=100.0,
                               help="Mass flow rate of food waste feed")
    with col2:
        Tann = st.number_input("Annual operating hours (hr/yr)", 1000.0, 8760.0,
                               7920.0, step=100.0,
                               help="Number of operating hours per year")
 
    # HHV display
    HHV = get_HHV(selected_waste)
    st.info(f"Higher Heating Value (HHV): **{HHV} MJ/kg** (wet basis)")
 
    # Store in session state
    st.session_state["composition"] = {
        "WATER": WATER, "CBH": CBH, "PRT": PRT, "FAT": FAT,
        "OTH": OTH, "ASH": ASH, "FIXED_CARBON": FC,
    }
    st.session_state["Qf"]   = Qf
    st.session_state["Tann"] = Tann
 
 
# ============================================================
# TAB 3 — ECONOMIC PARAMETERS
# ============================================================
with tab3:
    st.markdown('<div class="section-header">Operating Cost Parameters</div>',
                unsafe_allow_html=True)
 
    col1, col2, col3 = st.columns(3)
    with col1:
        C_elec = st.number_input("Electricity cost ($/kWh)", 0.01, 1.0,
                                 0.10, step=0.01, format="%.3f")
        C_tip  = st.number_input("Tipping fee ($/kg)", 0.0, 0.5,
                                 0.08, step=0.005, format="%.3f",
                                 help="Revenue received per kg of food waste processed")
    with col2:
        C_lbr  = st.number_input("Labor cost ($/hr)", 10.0, 100.0,
                                 30.0, step=1.0)
        CRF    = st.number_input("Capital recovery factor", 0.05, 0.30,
                                 0.11, step=0.01, format="%.3f",
                                 help="CRF = i(1+i)^n / ((1+i)^n - 1)")
    with col3:
        st.markdown("**CRF Guide**")
        st.caption("10 yr @ 10%: 0.163")
        st.caption("15 yr @ 10%: 0.131")
        st.caption("20 yr @ 10%: 0.117")
        st.caption("20 yr @ 8%:  0.102")
 
    st.markdown('<div class="section-header">Product Selling Prices</div>',
                unsafe_allow_html=True)
 
    col1, col2, col3 = st.columns(3)
    with col1:
        price_CH4         = st.number_input("Biomethane CH4 ($/kg)",
                                            0.0, 2.0, 0.185, step=0.01)
        price_BIOCRUDE    = st.number_input("Biocrude ($/kg)",
                                            0.0, 2.0, 0.48, step=0.01)
    with col2:
        price_COMPOST     = st.number_input("Compost ($/kg)",
                                            0.0, 0.5, 0.068, step=0.005)
        price_ELECTRICITY = st.number_input("Electricity ($/kWh)",
                                            0.0, 0.5, 0.10, step=0.01)
    with col3:
        price_BIOSOLIDS   = st.number_input("Biosolids ($/kg)",
                                            0.0, 0.5, 0.05, step=0.005)
 
    st.markdown('<div class="section-header">Solver Settings</div>',
                unsafe_allow_html=True)
 
    col1, col2 = st.columns(2)
    with col1:
        n_pareto = st.slider("Number of Pareto points", 3, 20, 10, step=1)
        time_lim = st.number_input("Time limit per point (seconds)",
                                   60, 1800, 300, step=60)
    with col2:
        gap = st.number_input("Optimality gap (%)", 0.5, 10.0, 2.0, step=0.5)
        st.caption(f"Estimated runtime: ~{n_pareto * time_lim // 60} minutes")
 
    # Store in session state
    st.session_state["econ"] = {
        "C_elec": C_elec, "C_tip": C_tip, "C_lbr": C_lbr, "CRF": CRF,
        "price_CH4": price_CH4, "price_BIOCRUDE": price_BIOCRUDE,
        "price_COMPOST": price_COMPOST, "price_ELECTRICITY": price_ELECTRICITY,
        "price_BIOSOLIDS": price_BIOSOLIDS,
        "n_pareto_pts": n_pareto,
        "time_limit": time_lim,
        "gap": gap / 100.0,
    }
 
 
# ============================================================
# TAB 4 — RUN OPTIMIZATION
# ============================================================
with tab4:
    st.markdown('<div class="section-header">Ready to Optimize</div>',
                unsafe_allow_html=True)
 
    # Show summary of inputs
    comp_ss = st.session_state.get("composition", {})
    econ_ss = st.session_state.get("econ", {})
 
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Feed Summary**")
        st.write(f"- Feed rate: {st.session_state.get('Qf', 1000)} kg/hr")
        st.write(f"- Operating hours: {st.session_state.get('Tann', 7920)} hr/yr")
        st.write(f"- Waste type: {selected_waste}")
        if comp_ss:
            st.write(f"- Moisture: {comp_ss.get('WATER', 0)*100:.1f}%")
            st.write(f"- Protein: {comp_ss.get('PRT', 0)*100:.1f}%")
            st.write(f"- Fat: {comp_ss.get('FAT', 0)*100:.1f}%")
 
    with col2:
        st.markdown("**Economic Summary**")
        if econ_ss:
            st.write(f"- Electricity: ${econ_ss.get('C_elec', 0.1)}/kWh")
            st.write(f"- Tipping fee: ${econ_ss.get('C_tip', 0.08)}/kg")
            st.write(f"- Labor: ${econ_ss.get('C_lbr', 30)}/hr")
            st.write(f"- CRF: {econ_ss.get('CRF', 0.11)}")
            st.write(f"- Pareto points: {econ_ss.get('n_pareto_pts', 10)}")
 
    st.markdown(
        '<div class="warning-box">⚠️ The optimization may take '
        '<strong>20–50 minutes</strong> depending on solver settings. '
        'Do not close this window while running.</div>',
        unsafe_allow_html=True
    )
 
    if st.button("🚀 Run Optimization", type="primary", use_container_width=True):
 
        # Validate composition
        comp_val = st.session_state.get("composition", {})
        valid, msg = validate_composition(comp_val)
        if not valid:
            st.error(f"Invalid composition: {msg}")
        else:
            user_inputs = {
                "Qf":          st.session_state.get("Qf", 1000),
                "Tann":        st.session_state.get("Tann", 7920),
                "composition": comp_val,
                **st.session_state.get("econ", {}),
            }
 
            with st.spinner("Running optimization... This may take a while."):
                result = run_optimization(user_inputs)
 
            if result["status"] == "success":
                st.session_state["result"] = result
                st.success(f"✅ {result['message']}")
                st.balloons()
            else:
                st.error(f"❌ Optimization failed: {result['message']}")
 
 
# ============================================================
# TAB 5 — PARETO FRONT
# ============================================================
with tab5:
    st.markdown('<div class="section-header">Pareto Front Results</div>',
                unsafe_allow_html=True)
 
    result = st.session_state.get("result", None)
 
    if result is None:
        st.info("Run the optimization first in the **Run Optimization** tab.")
    else:
        df = result["pareto_df"]
        feasible = df[df["NAC"].notna()].copy()
 
        if feasible.empty:
            st.warning("No feasible Pareto points found.")
        else:
            # Key metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Min NAC", f"{result['NAC_min']:.3f} M$/yr",
                          help="Minimum Net Annual Cost")
            with col2:
                st.metric("Min GHG", f"{result['GHG_min']:.0f} t CO2-eq/yr",
                          help="Minimum GHG emissions")
            with col3:
                st.metric("Feasible points", len(feasible))
 
            # Pareto plot
            fig, ax = plt.subplots(figsize=(10, 6))
 
            color_map = {
                "HTL": "#7F77DD", "AND": "#1D9E75", "CMP": "#D4537E",
                "WWT": "#378ADD", "SLF": "#D85A30", "INC": "#BA7517",
            }
 
            for _, row in feasible.iterrows():
                color = color_map.get(row["Conv"], "#999999")
                ax.scatter(row["NAC"], row["GHG"],
                           color=color, s=120, zorder=5,
                           edgecolors="white", linewidth=1.5)
                ax.annotate(row["Pareto_pt"],
                            (row["NAC"], row["GHG"]),
                            textcoords="offset points",
                            xytext=(6, 4), fontsize=8)
 
            # Connect Pareto points
            sorted_f = feasible.sort_values("NAC")
            ax.plot(sorted_f["NAC"], sorted_f["GHG"],
                    "k--", linewidth=1, alpha=0.4, zorder=1)
 
            # Legend
            patches = [mpatches.Patch(color=c, label=t)
                       for t, c in color_map.items()]
            ax.legend(handles=patches, title="Conversion Tech",
                      loc="upper right", fontsize=9)
 
            ax.set_xlabel("Net Annual Cost (M$/yr)", fontsize=12)
            ax.set_ylabel("GHG Emissions (t CO2-eq/yr)", fontsize=12)
            ax.set_title("Pareto Front — Cost vs GHG Emissions", fontsize=13)
            ax.axhline(0, color="gray", linewidth=0.5, linestyle=":")
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
 
            # Results table
            st.markdown('<div class="section-header">Pareto Results Table</div>',
                        unsafe_allow_html=True)
            st.dataframe(
                feasible[[
                    "Pareto_pt", "Conv", "Bio", "Mech",
                    "HTLrec", "GasUpg", "STB", "NAC", "GHG", "Status"
                ]].reset_index(drop=True),
                use_container_width=True
            )
 
            # Download
            csv = df.to_csv(index=False)
            st.download_button("⬇️ Download Full Results CSV",
                               csv, "pareto_results.csv", "text/csv")
 
 
# ============================================================
# TAB 6 — COST BREAKDOWN
# ============================================================
with tab6:
    st.markdown('<div class="section-header">Cost Breakdown</div>',
                unsafe_allow_html=True)
 
    result = st.session_state.get("result", None)
 
    if result is None:
        st.info("Run the optimization first in the **Run Optimization** tab.")
    else:
        df = result["pareto_df"]
        feasible = df[df["NAC"].notna()].copy()
 
        if feasible.empty:
            st.warning("No feasible points to display.")
        else:
            # Cost breakdown bar chart
            cost_cols   = ["CCAC", "CCWC", "CCINS", "CCUC",
                           "CCLB", "CCOC", "CCRM", "CDISP", "CTIP"]
            cost_labels = ["Capital", "Working Capital", "Insurance",
                           "Utilities", "Labor", "Overhead",
                           "Raw Materials", "Disposal", "Tipping Fee"]
            cost_colors = ["#4878CF", "#6ACC65", "#D65F5F", "#B47CC7",
                           "#C4AD66", "#77BEDB", "#F0A500", "#A9A9A9", "#5A5A5A"]
 
            df_plot = feasible.drop_duplicates(
                subset=["Conv", "NAC", "GHG"]
            ).reset_index(drop=True)
 
            techs = [f"{r['Conv']}\n({r['GasUpg'] if r['GasUpg'] != '-' else r['HTLrec'] if r['HTLrec'] != '-' else 'direct'})"
                     for _, r in df_plot.iterrows()]
 
            x      = np.arange(len(df_plot))
            width  = 0.5
            bottom = np.zeros(len(df_plot))
 
            fig, ax = plt.subplots(figsize=(12, 6))
 
            for col, label, color in zip(cost_cols, cost_labels, cost_colors):
                vals = df_plot[col].fillna(0).to_numpy()
                ax.bar(x, vals, width, bottom=bottom, label=label,
                       color=color, edgecolor="white", linewidth=0.5)
                bottom += vals
 
            # Revenue as negative bar
            ax.bar(x, -df_plot["REV"].fillna(0).to_numpy(), width,
                   label="Revenue", color="#2E8B57",
                   edgecolor="white", linewidth=0.5, hatch="///")
 
            # NAC markers
            for idx in range(len(df_plot)):
                ax.scatter(idx, df_plot.loc[idx, "NAC"],
                           color="black", zorder=5, s=60, marker="D")
 
            ax.set_xticks(x)
            ax.set_xticklabels(techs, fontsize=9)
            ax.set_ylabel("Cost (M$/yr)", fontsize=12)
            ax.set_title("Annual Cost Breakdown by Conversion Technology",
                         fontsize=12)
            ax.legend(loc="upper left", fontsize=8, ncol=2, framealpha=0.9)
            ax.axhline(0, color="black", linewidth=0.8)
            ax.grid(True, alpha=0.2, axis="y", linestyle="--")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()
 
            # Cost table
            st.markdown('<div class="section-header">Detailed Cost Table (M$/yr)</div>',
                        unsafe_allow_html=True)
            st.dataframe(
                feasible[[
                    "Pareto_pt", "Conv", "CCAC", "CCWC", "CCINS",
                    "CCUC", "CCLB", "CCOC", "CCRM", "CDISP",
                    "CTIP", "REV", "CCTC", "NAC"
                ]].reset_index(drop=True),
                use_container_width=True
            )
 