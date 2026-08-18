"""
app.py
======
ECO-FAST - Food Waste Processing Optimization Tool
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import base64
import os
import requests
import time

from food_waste_database import (
    get_waste_types, get_composition, get_description,
    get_references, get_HHV, validate_composition,
)


st.set_page_config(
    page_title="ECO-FAST",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown("""
<style>
    .stApp { background-color: #D4D0C8; }
    header[data-testid="stHeader"] { display: none !important; }
    .block-container { padding-top: 0rem !important; margin-top: 0rem !important; }
    [data-testid="stAppViewContainer"] { padding-top: 0rem !important; }
    [data-testid="stToolbar"] { display: none !important; }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #D4D0C8;
        border-bottom: 2px solid #808080;
        gap: 0px; padding: 0px 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #D4D0C8;
        border: 1px solid #808080;
        border-bottom: none;
        border-radius: 4px 4px 0 0;
        padding: 6px 16px;
        font-size: 13px;
        color: #000000;
        margin-right: 2px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        border-bottom: 2px solid #FFFFFF !important;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #FFFFFF;
        border: 1px solid #808080;
        border-top: none;
        padding: 16px;
    }
    .stButton button {
        background-color: #D4D0C8 !important;
        border: 2px solid #808080 !important;
        border-radius: 3px !important;
        color: #000000 !important;
        font-size: 12px !important;
        padding: 4px 12px !important;
    }
    .stButton button:hover { background-color: #BDB9B0 !important; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    .stNumberInput input:disabled,
    .stTextInput input:disabled {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }
    .stNumberInput label,
    .stTextInput label,
    .stSelectbox label,
    .stSlider label {
        color: #000000 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }
    .stSelectbox div[data-baseweb="select"] {
        color: #000000 !important;
        opacity: 1 !important;
    }
    .ej-score-high { color: #CC0000; font-weight: bold; }
    .ej-score-med  { color: #FF8800; font-weight: bold; }
    .ej-score-low  { color: #2E8B57; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================
def section_header(text, top=6, bottom=6):
    st.markdown(
        f'<div style="font-weight:bold; font-size:18px; color:#1a1a1a; '
        f'padding-top:{top}px; padding-bottom:{bottom}px; '
        f'line-height:1.6; overflow:visible;">{text}</div>',
        unsafe_allow_html=True,
    )

def nav_buttons(save_key, tab_index, save_action=None):
    pass

def fetch_ejscreen(zipcode):
    try:
        geo_url = (
            "https://geocoding.geo.census.gov/geocoder/locations/address"
            f"?zip={zipcode}&benchmark=Public_AR_Current&format=json"
        )
        geo_r = requests.get(geo_url, timeout=10)
        geo_data = geo_r.json()
        matches = geo_data.get("result", {}).get("addressMatches", [])
        if not matches:
            return None
        coords = matches[0]["coordinates"]
        lat, lon = coords["y"], coords["x"]

        fcc_url = (
            f"https://geo.fcc.gov/api/census/block/find"
            f"?latitude={lat}&longitude={lon}&format=json"
        )
        fcc_r = requests.get(fcc_url, timeout=10)
        fcc_data = fcc_r.json()
        fips = fcc_data.get("Block", {}).get("FIPS", "")
        if not fips or len(fips) < 12:
            return None
        bg_fips = fips[:12]

        arcgis_url = (
            "https://ejscreen.epa.gov/arcgis/rest/services/ejscreen/"
            "ejscreen_indexes_usa_2024_public/MapServer/0/query"
            f"?where=ID='{bg_fips}'&outFields=*&f=json"
        )
        ej_r = requests.get(arcgis_url, timeout=15)
        ej_data = ej_r.json()
        features = ej_data.get("features", [])
        if not features:
            return None
        attrs = features[0].get("attributes", {})

        return {
            "lat": lat, "lon": lon,
            "pct_minority":   (attrs.get("MINORPCT",  0) or 0) * 100,
            "pct_lowincome":  (attrs.get("LOWINCPCT", 0) or 0) * 100,
            "pct_less_hs":    (attrs.get("LESSHSPCT", 0) or 0) * 100,
            "pm25":           attrs.get("PM25",  0) or 0,
            "ozone":          attrs.get("OZONE", 0) or 0,
            "diesel_pm":      attrs.get("DSLPM", 0) or 0,
            "superfund_prox": attrs.get("PNPL",  0) or 0,
            "ej_index":       attrs.get("EJSCREEN_SCORE_2", 0) or 0,
            "ej_pctile":      attrs.get("P_EJDX_D2", 0) or 0,
        }
    except Exception:
        return None

def ej_risk_label(pctile):
    if pctile >= 80:
        return '<span class="ej-score-high">HIGH</span>'
    elif pctile >= 50:
        return '<span class="ej-score-med">MODERATE</span>'
    else:
        return '<span class="ej-score-low">LOW</span>'


# ============================================================
# HEADER
# ============================================================
def img_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

try:
    rowan_b64 = img_to_base64("rowan_logo.png")
    njdep_b64 = img_to_base64("njdep_logo.png")
    st.markdown(f"""
    <div style="background-color:#D4D0C8; padding:1px 16px;
                display:flex; align-items:center; justify-content:space-between;">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="background:#2E8B57; color:white; font-weight:900;
                        font-size:24px; width:56px; height:56px;
                        display:flex; align-items:center; justify-content:center;
                        border-radius:12px; font-family:Arial; flex-shrink:0;">EF</div>
            <div>
                <div style="font-size:24px; font-weight:bold;
                            font-family:Arial; color:#000; line-height:1.2;">ECO-FAST</div>
                <div style="font-size:12px; font-family:Arial; color:#444;">
                    Ecological Impact of Food Waste Recycle Effluent</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:1px;">
            <img src="data:image/png;base64,{rowan_b64}"
                 style="height:70px; width:135px; object-fit:contain;
                        mix-blend-mode:multiply; background:transparent;">
            <img src="data:image/png;base64,{njdep_b64}"
                 style="height:70px; width:70px; object-fit:contain;
                        mix-blend-mode:multiply; background:transparent;">
        </div>
    </div>
    <hr style="margin:0; border-color:#808080;">
    """, unsafe_allow_html=True)
except:
    st.markdown("<hr style='margin:2px 0 0 0; border-color:#808080;'>",
                unsafe_allow_html=True)

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Instructions",
    "Feed Inputs",
    "Technology Specifications",
    "Cost Specifications",
    "Results",
    "Environmental Justice",
])

# ============================================================
# TAB 1 - INSTRUCTIONS
# ============================================================
with tab1:
    section_header("Purpose")
    st.markdown(
        "ECO-FAST is a decision-support tool for the selection and design of food waste processing systems. "
        "Given a food waste stream, the tool evaluates all possible processing pathways from the superstructure "
        "and provides three types of results:"
    )
    st.markdown(
        "**Lowest Cost Pathway:** the processing pathway that minimizes net annual cost regardless of emissions  \n"
        "**Lowest Emissions Pathway:** the processing pathway that minimizes greenhouse gas emissions regardless of cost  \n"
        "**Lowest Cost & Emissions Pathway:** the processing pathway that represents the best balance of cost and emissions"
    )

    section_header("Food Waste Superstructure")
    if os.path.exists("Superstructure.tif"):
        col_left, col_mid, col_right = st.columns([1, 3, 1])
        with col_mid:
            st.image("Superstructure.tif", use_container_width=True)
    else:
        st.info("Place Superstructure.tif in the project folder to display the diagram.")

    st.markdown("")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        section_header("Pretreatment")
        st.markdown("- **Mechanical:** Shredding (SHR), Maceration (MCR)\n- **Biological:** Aerobic biodigestion (AER), Enzymatic hydrolysis (ENZ)")
    with col_b:
        section_header("Conversion")
        st.markdown("- Hydrothermal liquefaction (HTL)\n- Anaerobic digestion (AND)\n- Composting (CMP)\n- Sanitary landfill (SLF)\n- Wastewater treatment (WWT)\n- Incineration (INC)")
    with col_c:
        section_header("Recovery & Upgrading")
        st.markdown("- Centrifugation (CEN), Filtration (FLT)\n- Amine scrubbing (ABS), PSA gas upgrading\n- Steam turbine (STB)")

    st.markdown("")
    section_header("How to Use")
    st.markdown(
        "1. **Feed Inputs:** Define your food waste type, composition, flow rate, operating hours, and facility zip code.\n"
        "2. **Technology Specifications:** Review and adjust default values for each technology.\n"
        "3. **Cost Specifications:** Configure economic parameters and solver settings.\n"
        "4. **Results:** Select an objective and run the optimization.\n"
        "5. **Environmental Justice:** View the EPA EJScreen assessment for your facility location."
    )


# ============================================================
# TAB 2 - FEED INPUTS
# ============================================================
with tab2:
    col_left, col_right = st.columns([1, 1])

    with col_left:
        section_header("Food Waste Type")
        waste_types = get_waste_types()
        selected_waste = st.selectbox(
            "Food Waste Type", waste_types,
            index=None,
            placeholder="Select a food waste type...",
            label_visibility="collapsed"
        )

        if selected_waste is None:
            st.info("Please select a food waste type to continue.")
            st.stop()

        section_header("Feed Stream Conditions")
        col_flow, col_flow_unit = st.columns([2, 1])
        with col_flow:
            Qf_input = st.number_input("Feed flow rate", 0.0, 1000000.0,
                                       1000.0, step=100.0,
                                       label_visibility="collapsed")
        with col_flow_unit:
            flow_unit = st.selectbox("Flow unit",
                                     ["kg/hr", "t/day", "lb/hr", "kg/day"],
                                     label_visibility="collapsed")

        flow_conversions = {"kg/hr": 1.0, "t/day": 1000.0/24.0,
                            "lb/hr": 0.453592, "kg/day": 1.0/24.0}
        Qf = Qf_input * flow_conversions[flow_unit]

        col_hr, col_hr_unit = st.columns([2, 1])
        with col_hr:
            Tann_input = st.number_input("Operating hours", 0.0, 10000.0,
                                         7920.0, step=100.0,
                                         label_visibility="collapsed")
        with col_hr_unit:
            hr_unit = st.selectbox("Hours unit",
                                   ["hr/yr", "days/yr", "weeks/yr"],
                                   label_visibility="collapsed")

        hr_conversions = {"hr/yr": 1.0, "days/yr": 24.0, "weeks/yr": 168.0}
        Tann = Tann_input * hr_conversions[hr_unit]

        section_header("Facility Location")
        zipcode = st.text_input(
            "Facility zip code (US only)",
            placeholder="e.g. 08028",
            label_visibility="collapsed"
        )
        if zipcode:
            st.caption(f"Zip code: {zipcode} — EJ data will appear in the Environmental Justice tab.")
            st.session_state["zipcode"] = zipcode
        else:
            st.caption("Enter a zip code to enable Environmental Justice assessment.")
            st.session_state["zipcode"] = None

        section_header("Composition (wet basis)")
        is_custom = selected_waste == "Custom (Enter Your Own Data)"
        comp = get_composition(selected_waste)

        if st.session_state.get("_last_waste") != selected_waste:
            for k in ["comp_water", "comp_cbh", "comp_prt", "comp_fat",
                      "comp_oth", "comp_ash", "comp_fc"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.session_state["_last_waste"] = selected_waste

        c1, c2 = st.columns(2)
        with c1:
            WATER = st.number_input("Water",          0.0, 1.0, float(comp["WATER"]),        0.001, format="%.4f", disabled=not is_custom, key="comp_water")
            PRT   = st.number_input("Protein",        0.0, 1.0, float(comp["PRT"]),          0.001, format="%.4f", disabled=not is_custom, key="comp_prt")
            OTH   = st.number_input("Other Organics", 0.0, 1.0, float(comp["OTH"]),          0.001, format="%.4f", disabled=not is_custom, key="comp_oth")
            FC    = st.number_input("Fixed Carbon",   0.0, 1.0, float(comp["FIXED_CARBON"]), 0.001, format="%.4f", disabled=not is_custom, key="comp_fc")
        with c2:
            CBH   = st.number_input("Carbohydrates",  0.0, 1.0, float(comp["CBH"]),          0.001, format="%.4f", disabled=not is_custom, key="comp_cbh")
            FAT   = st.number_input("Fat / Lipid",    0.0, 1.0, float(comp["FAT"]),          0.001, format="%.4f", disabled=not is_custom, key="comp_fat")
            ASH   = st.number_input("Ash",            0.0, 1.0, float(comp["ASH"]),          0.001, format="%.4f", disabled=not is_custom, key="comp_ash")
            total = WATER + CBH + PRT + FAT + OTH + ASH + FC
            st.text_input("Total Mass Fraction", value=f"{total:.4f}", disabled=True)

        if abs(total - 1.0) >= 0.01:
            st.error(f"Composition must sum to 1.0 (currently {total:.4f}).")

    with col_right:
        section_header("Energy & Organic Content")
        HHV = get_HHV(selected_waste)
        TS  = (1 - WATER) * 100
        VS  = (CBH + PRT + FAT + OTH) * 100
        CN  = round((0.43270 * (CBH + PRT + FAT + OTH)) /
                    max(0.07170 * PRT, 0.0001), 2)

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f"<div style='text-align:center'>Higher Heating Value<br><b>(HHV)</b><br>{HHV:.2f} MJ/kg</div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"<div style='text-align:center'>Volatile Solids<br><b>(VS)</b><br>{VS:.2f} %</div>", unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"<div style='text-align:center'>Total Solids<br><b>(TS)</b><br>{TS:.2f} %</div>", unsafe_allow_html=True)
        with col_m4:
            st.markdown(f"<div style='text-align:center'>C/N Ratio<br><b>(C/N)</b><br>{CN:.1f}</div>", unsafe_allow_html=True)

        section_header("Composition Breakdown", top=80, bottom=0)
        st.markdown('<div style="margin-bottom:-60px;"></div>', unsafe_allow_html=True)

        labels = ["Water", "Protein", "Fat / Lipid", "Fixed Carbon",
                  "Other Organics", "Carbohydrates", "Ash"]
        values = [WATER*100, PRT*100, FAT*100, FC*100,
                  OTH*100, CBH*100, ASH*100]
        colors = ["#D3D1C7", "#378ADD", "#1D9E75", "#7F77DD",
                  "#D4537E", "#D85A30", "#BA7517"]

        fig, ax = plt.subplots(figsize=(5, 4))
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")
        wedges, _ = ax.pie(
            values, labels=None, colors=colors,
            startangle=90, counterclock=False,
            wedgeprops=dict(width=0.5, edgecolor="white", linewidth=1.5)
        )
        legend_labels = [f"{l}: {v:.2f}%" for l, v in zip(labels, values)]
        ax.legend(wedges, legend_labels,
                  loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                  fontsize=8, frameon=False)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

    st.session_state["composition"] = {
        "WATER": WATER, "CBH": CBH, "PRT": PRT, "FAT": FAT,
        "OTH": OTH, "ASH": ASH, "FIXED_CARBON": FC,
    }
    st.session_state["Qf"]   = Qf
    st.session_state["Tann"] = Tann
    st.session_state["selected_waste"] = selected_waste


# ============================================================
# TAB 3 - TECHNOLOGY SPECIFICATIONS
# ============================================================
with tab3:
    st.markdown("Select a technology to review and adjust its default parameters.")

    tech_options = [
        "Hydrothermal Liquefaction",
        "Anaerobic Digestion",
        "Aerobic Biodigestion",
        "Enzymatic Hydrolysis",
        "Composting",
        "Wastewater Treatment",
        "Sanitary Landfill",
        "Incineration",
        "Shredding",
        "Maceration",
        "Centrifugation",
        "Filtration",
        "Amine Scrubbing",
        "Pressure Swing Adsorption",
        "Steam Turbine",
    ]

    selected_tech = st.selectbox(
        "Select Technology", tech_options, index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")

    if selected_tech == "Hydrothermal Liquefaction":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Product Yield Fractions")
            yBIOCRUDE = st.number_input("Biocrude yield",      0.0, 1.0, 0.35, 0.01, format="%.3f")
            yCHAR     = st.number_input("Char yield",          0.0, 1.0, 0.10, 0.01, format="%.3f")
            yAQ       = st.number_input("Aqueous phase yield", 0.0, 1.0, 0.40, 0.01, format="%.3f")
            yGAS      = st.number_input("Gas product yield",   0.0, 1.0, 0.15, 0.01, format="%.3f")
            total_htl = yBIOCRUDE + yCHAR + yAQ + yGAS
            st.text_input("Sum of yield fractions", value=f"{total_htl:.3f}", disabled=True)
        with col2:
            section_header("Operating Conditions")
            T_HTL     = st.number_input("Reaction temperature [C]", 200.0, 400.0, 340.0, 5.0)
            theta_HTL = st.number_input("Residence time [min]",       10.0, 120.0,  60.0, 5.0)
            rDry_HTL  = st.number_input("Dry solid loading [%]",       1.0,  30.0,   7.0, 0.5)
        st.session_state["htl_params"] = {
            "yBIOCRUDE": yBIOCRUDE, "yCHAR": yCHAR, "yAQ": yAQ, "yGAS": yGAS,
            "T_HTL": T_HTL, "theta_HTL": theta_HTL, "rDry_HTL": rDry_HTL,
        }

    elif selected_tech == "Anaerobic Digestion":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Biogas Production")
            BMP_scen    = st.number_input("Biochemical methane potential [mL CH4/g VS]", 0.0, 2000.0, 802.91, 10.0)
            eta_cap_AND = st.number_input("Biogas capture efficiency",  0.0, 1.0, 0.98, 0.01, format="%.2f")
            eta_OTH_AND = st.number_input("Other organics degradation", 0.0, 1.0, 0.30, 0.01, format="%.2f")
        with col2:
            section_header("Operating Conditions")
            theta_AND   = st.number_input("Hydraulic retention time [hr]",       100.0, 1500.0, 720.0, 10.0)
            OLR_AND     = st.number_input("Organic loading rate [kg VS/m3/day]",   0.5,   10.0,   2.5,  0.1)
            epsilon_AND = st.number_input("Vessel fill fraction",                  0.0,    1.0,   0.85, 0.01, format="%.2f")
        st.session_state["and_params"] = {
            "BMP_scen": BMP_scen, "eta_cap_AND": eta_cap_AND,
            "eta_OTH_AND": eta_OTH_AND, "theta_AND": theta_AND,
            "epsilon_AND": epsilon_AND,
        }

    elif selected_tech == "Aerobic Biodigestion":
        section_header("Component Degradation Fractions")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            fdeg_CBH = st.number_input("Carbohydrates", 0.0, 1.0, 0.40, 0.01, format="%.2f")
        with c2:
            fdeg_PRT = st.number_input("Protein",       0.0, 1.0, 0.30, 0.01, format="%.2f")
        with c3:
            fdeg_FAT = st.number_input("Fat / Lipid",   0.0, 1.0, 0.15, 0.01, format="%.2f")
        with c4:
            fdeg_OTH = st.number_input("Other organics",0.0, 1.0, 0.20, 0.01, format="%.2f")
        col1, col2 = st.columns(2)
        with col1:
            section_header("Operating Conditions")
            theta_AER = st.number_input("Hydraulic retention time [hr]",        1.0, 100.0, 24.0, 1.0)
            Rw_AER    = st.number_input("Water addition ratio [kg/kg dry feed]", 0.0,  10.0,  1.5, 0.1)
        st.session_state["aer_params"] = {
            "fdeg_CBH": fdeg_CBH, "fdeg_PRT": fdeg_PRT,
            "fdeg_FAT": fdeg_FAT, "fdeg_OTH": fdeg_OTH,
            "theta_AER": theta_AER, "Rw_AER": Rw_AER,
        }

    elif selected_tech == "Enzymatic Hydrolysis":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Hydrolysis Parameters")
            eta_ENZ = st.number_input("Hydrolysis efficiency",                0.0, 1.0, 0.85, 0.01, format="%.2f")
            r_enz   = st.number_input("Enzyme dose [kg enzyme/kg dry solids]", 0.0, 0.1, 0.02, 0.001, format="%.3f")
            HRT_ENZ = st.number_input("Hydraulic retention time [hr]",         1.0, 24.0, 6.0, 0.5)
        st.session_state["enz_params"] = {"eta_ENZ": eta_ENZ, "r_enz": r_enz, "HRT_ENZ": HRT_ENZ}

    elif selected_tech == "Composting":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Degradation")
            fdeg_CMP    = st.number_input("Volatile solids degradation fraction", 0.0, 1.0, 0.50, 0.01, format="%.2f")
            eta_OTH_CMP = st.number_input("Other organics degradation",           0.0, 1.0, 0.60, 0.01, format="%.2f")
            theta_CMP   = st.number_input("Composting time [hr]",                24.0, 500.0, 120.0, 10.0)
        with col2:
            section_header("Emission Factors")
            EF_CH4_CMP = st.number_input("CH4 emission factor [kg/kg wet feed]", 0.0, 0.1,  0.0040,  0.0001, format="%.4f")
            EF_N2O_CMP = st.number_input("N2O emission factor [kg/kg wet feed]", 0.0, 0.01, 0.00030, 0.00001, format="%.5f")
        st.session_state["cmp_params"] = {
            "fdeg_CMP": fdeg_CMP, "eta_OTH_CMP": eta_OTH_CMP, "theta_CMP": theta_CMP,
        }

    elif selected_tech == "Wastewater Treatment":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Treatment Parameters")
            fBOD        = st.number_input("BOD fraction of volatile solids",      0.0,  2.0, 1.20, 0.01)
            SRT_day     = st.number_input("Sludge retention time [days]",          1.0, 30.0, 10.0, 1.0)
            X_MLSS      = st.number_input("Mixed liquor suspended solids [g/L]",   1.0, 10.0,  3.0, 0.1)
        with col2:
            section_header("Operating Conditions")
            HRT_WWT_min = st.number_input("Minimum hydraulic retention time [hr]", 1.0, 24.0,  6.0, 0.5)
        st.session_state["wwt_params"] = {
            "fBOD": fBOD, "SRT_day": SRT_day, "X_MLSS": X_MLSS, "HRT_WWT_min": HRT_WWT_min,
        }

    elif selected_tech == "Sanitary Landfill":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Methane Generation")
            DOC_value = st.number_input("Degradable organic carbon fraction", 0.0, 1.0, 0.358, 0.001, format="%.3f")
            MCF_value = st.number_input("Methane correction factor",          0.0, 1.0, 0.60,  0.01,  format="%.2f")
            F_value   = st.number_input("Fraction of CH4 in landfill gas",    0.0, 1.0, 0.576, 0.001, format="%.3f")
        with col2:
            section_header("Site Parameters")
            CAP_SLF   = st.number_input("Gas capture efficiency", 0.0, 1.0,  0.65, 0.01, format="%.2f")
            OX        = st.number_input("Oxidation factor",       0.0, 1.0,  0.10, 0.01, format="%.2f")
            Depth_SLF = st.number_input("Landfill depth [m]",     1.0, 30.0, 10.0, 1.0)
        st.session_state["slf_params"] = {
            "DOC_value": DOC_value, "MCF_value": MCF_value, "F_value": F_value,
            "CAP_SLF": CAP_SLF, "OX": OX, "Depth_SLF": Depth_SLF,
        }

    elif selected_tech == "Incineration":
        section_header("Efficiency Parameters")
        c1, c2, c3 = st.columns(3)
        with c1:
            eta_INC    = st.number_input("Combustion efficiency", 0.0, 1.0, 0.98, 0.01, format="%.2f")
        with c2:
            eta_boiler = st.number_input("Boiler efficiency",     0.0, 1.0, 0.80, 0.01, format="%.2f")
        with c3:
            eta_turb   = st.number_input("Turbine efficiency",    0.0, 1.0, 0.30, 0.01, format="%.2f")
        st.session_state["inc_params"] = {
            "eta_INC": eta_INC, "eta_boiler": eta_boiler, "eta_turb": eta_turb,
        }

    elif selected_tech == "Shredding":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Shredding Parameters")
            eta_SHR = st.number_input("Shredding efficiency", 0.0, 1.0, 0.99, 0.01, format="%.2f")
        st.session_state["shr_params"] = {"eta_SHR": eta_SHR}

    elif selected_tech == "Maceration":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Maceration Parameters")
            Rw_MCR = st.number_input("Water addition ratio [kg water/kg dry feed]", 0.0, 10.0, 2.0, 0.1)
        st.session_state["mcr_params"] = {"Rw_MCR": Rw_MCR}

    elif selected_tech == "Centrifugation":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Centrifugation Parameters")
            st.markdown("Separates biocrude from the HTL aqueous phase and char.")
            eta_CEN = st.number_input("Centrifuge separation efficiency", 0.0, 1.0, 0.95, 0.01, format="%.2f")
        with col2:
            section_header("Retention Factors (fixed)")
            st.text_input("Biocrude retention",      value="0.95", disabled=True)
            st.text_input("Char retention",          value="0.98", disabled=True)
            st.text_input("Aqueous phase retention", value="0.10", disabled=True)
        st.session_state["cen_params"] = {"eta_CEN": eta_CEN}

    elif selected_tech == "Filtration":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Filtration Parameters")
            st.markdown("Further separates char and solids from the biocrude stream.")
            eta_FLT = st.number_input("Filtration efficiency", 0.0, 1.0, 0.98, 0.01, format="%.2f")
        with col2:
            section_header("Retention Factors (fixed)")
            st.text_input("Biocrude pass-through", value="0.05", disabled=True)
            st.text_input("Char retention",        value="0.98", disabled=True)
            st.text_input("Aqueous retention",     value="0.10", disabled=True)
        st.session_state["flt_params"] = {"eta_FLT": eta_FLT}

    elif selected_tech == "Amine Scrubbing":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Amine Scrubbing Parameters")
            eta_ABS = st.number_input("CO2 removal efficiency",             0.0, 1.0, 0.95, 0.01, format="%.2f")
            r_amine = st.number_input("Amine circulation rate [kg/m3 gas]", 0.0, 5.0, 0.30, 0.01)
        with col2:
            section_header("Operating Conditions")
            T_ABS   = st.number_input("Absorption temperature [C]",   20.0,  60.0,  40.0, 1.0)
            T_regen = st.number_input("Regeneration temperature [C]",  80.0, 140.0, 120.0, 5.0)
        st.session_state["abs_params"] = {
            "eta_ABS": eta_ABS, "r_amine": r_amine, "T_ABS": T_ABS, "T_regen": T_regen,
        }

    elif selected_tech == "Pressure Swing Adsorption":
        col1, col2 = st.columns(2)
        with col1:
            section_header("PSA Parameters")
            eta_PSA    = st.number_input("CH4 recovery efficiency", 0.0, 1.0, 0.92, 0.01, format="%.2f")
            purity_PSA = st.number_input("Biomethane purity [%]",  90.0, 100.0, 97.0, 0.5)
        with col2:
            section_header("Operating Conditions")
            P_ads = st.number_input("Adsorption pressure [bar]",  1.0, 20.0, 7.0, 0.5)
            P_des = st.number_input("Desorption pressure [bar]",  0.01, 2.0, 0.1, 0.01)
        st.session_state["psa_params"] = {
            "eta_PSA": eta_PSA, "purity_PSA": purity_PSA, "P_ads": P_ads, "P_des": P_des,
        }

    elif selected_tech == "Steam Turbine":
        col1, col2 = st.columns(2)
        with col1:
            section_header("Steam Turbine Parameters")
            eta_turb_STB = st.number_input("Turbine isentropic efficiency", 0.0, 1.0, 0.30, 0.01, format="%.2f")
            eta_boil_STB = st.number_input("Boiler efficiency",             0.0, 1.0, 0.80, 0.01, format="%.2f")
            eta_mech_STB = st.number_input("Mechanical efficiency",         0.0, 1.0, 0.95, 0.01, format="%.2f")
        with col2:
            section_header("Operating Conditions")
            P_steam_STB = st.number_input("Steam pressure [bar]",   1.0, 100.0, 40.0, 1.0)
            T_steam_STB = st.number_input("Steam temperature [C]", 100.0, 500.0, 350.0, 10.0)
        st.session_state["stb_params"] = {
            "eta_turb_STB": eta_turb_STB, "eta_boil_STB": eta_boil_STB, "eta_mech_STB": eta_mech_STB,
        }

    st.session_state["feed_params"] = {
        "BMP_scen": st.session_state.get("and_params", {}).get("BMP_scen", 802.91),
        "fdeg_CMP": st.session_state.get("cmp_params", {}).get("fdeg_CMP", 0.50),
        "C_frac": 0.4327, "H_frac": 0.0605, "O_frac": 0.4289,
        "N_frac": 0.0717, "S_frac": 0.0062,
    }


# ============================================================
# TAB 4 - COST SPECIFICATIONS
# ============================================================
with tab4:
    col_left4, col_right4 = st.columns([1, 1])

    with col_left4:
        section_header("Economic Parameters")
        C_elec = st.number_input("Electricity cost [$/kWh]", 0.01, 1.0, 0.10, 0.01, format="%.3f")
        C_tip  = st.number_input("Tipping fee [$/kg]",       0.0,  0.5, 0.08, 0.005, format="%.3f")
        C_lbr  = st.number_input("Labor cost [$/hr]",        10.0, 100.0, 30.0, 1.0)

        section_header("Capital Recovery Factor")
        col_lt, col_dr = st.columns(2)
        with col_lt:
            plant_life = st.number_input("Plant lifetime [years]", 5, 40, 20, 1)
        with col_dr:
            discount_r = st.number_input("Discount rate [%]", 1.0, 20.0, 7.0, 0.5, format="%.1f")
        r   = discount_r / 100.0
        CRF = (r * (1 + r) ** plant_life) / ((1 + r) ** plant_life - 1)
        st.text_input("Capital recovery factor (CRF)", value=f"{CRF:.4f}", disabled=True)

        section_header("Product Selling Prices")
        price_CH4         = st.number_input("Biomethane [$/kg]",   0.0, 2.0, 0.185, 0.01)
        price_BIOCRUDE    = st.number_input("Biocrude [$/kg]",     0.0, 2.0, 0.48,  0.01)
        price_COMPOST     = st.number_input("Compost [$/kg]",      0.0, 0.5, 0.068, 0.005)
        price_ELECTRICITY = st.number_input("Electricity [$/kWh]", 0.0, 0.5, 0.10,  0.01)
        price_BIOSOLIDS   = st.number_input("Biosolids [$/kg]",    0.0, 0.5, 0.05,  0.005)

    with col_right4:
        section_header("Solver Settings")
        n_pareto = st.slider(
            "Trade-off Resolution (Pareto points)", 3, 20, 10, 1,
            help="More points = finer trade-off curve but longer runtime"
        )
        time_lim = st.number_input(
            "Time limit per point [seconds]", 60, 1800, 300, 60,
            help="Higher = more accurate solution but slower"
        )
        gap = st.number_input(
            "Optimality gap [%]", 0.5, 10.0, 2.0, 0.5,
            help="Lower = closer to global optimum but slower"
        )

        section_header("Input Summary")
        comp_ss  = st.session_state.get("composition", {})
        htl_p    = st.session_state.get("htl_params", {})
        and_p    = st.session_state.get("and_params", {})
        waste    = st.session_state.get("selected_waste", "Not selected")
        Qf_val   = st.session_state.get("Qf",   1000)
        Tann_val = st.session_state.get("Tann", 7920)
        VS_val   = (
            comp_ss.get("CBH", 0) + comp_ss.get("PRT", 0) +
            comp_ss.get("FAT", 0) + comp_ss.get("OTH", 0)
        ) * 100

        st.dataframe(
            pd.DataFrame({
                "Parameter": [
                    "Waste type", "Feed rate [kg/hr]", "Operating hours [hr/yr]",
                    "Moisture [%]", "Volatile solids [%]", "HTL biocrude yield",
                    "AND BMP [mL/g VS]", "Electricity cost [$/kWh]",
                    "Tipping fee [$/kg]", "CRF", "Pareto points",
                ],
                "Value": [
                    waste, f"{Qf_val:.1f}", f"{Tann_val:.0f}",
                    f"{comp_ss.get('WATER', 0)*100:.2f}", f"{VS_val:.2f}",
                    f"{htl_p.get('yBIOCRUDE', 0.35):.3f}",
                    f"{and_p.get('BMP_scen', 802.91):.2f}",
                    f"{C_elec:.3f}", f"{C_tip:.3f}", f"{CRF:.4f}", str(n_pareto),
                ]
            }),
            use_container_width=True, hide_index=True, height=390
        )

    st.session_state["econ"] = {
        "C_elec": C_elec, "C_tip": C_tip, "C_lbr": C_lbr, "CRF": CRF,
        "price_CH4": price_CH4, "price_BIOCRUDE": price_BIOCRUDE,
        "price_COMPOST": price_COMPOST, "price_ELECTRICITY": price_ELECTRICITY,
        "price_BIOSOLIDS": price_BIOSOLIDS,
        "n_pareto_pts": n_pareto, "time_limit": time_lim, "gap": gap / 100.0,
    }


# ============================================================
# TAB 5 - RESULTS
# ============================================================
with tab5:
    section_header("Select Optimization Objective")
    st.markdown("")

    selected_obj = st.radio(
        "Optimization objective",
        options=[
            "Lowest Cost Pathway",
            "Lowest Emissions Pathway",
            "Lowest Cost & Emissions Pathway",
        ],
        index=2,
        label_visibility="collapsed",
        horizontal=True,
    )

    st.markdown("")
    col_run = st.columns([3, 1, 3])
    with col_run[1]:
        run_clicked = st.button("Run Optimization", key="run_btn")

    if run_clicked:
        comp_val = st.session_state.get("composition", {})
        valid, msg = validate_composition(comp_val)
        if not valid:
            st.error(f"Invalid composition: {msg}")
        else:
            user_inputs = {
                "Qf":          st.session_state.get("Qf", 1000),
                "Tann":        st.session_state.get("Tann", 7920),
                "composition": comp_val,
                "objective":   selected_obj,
                **st.session_state.get("econ", {}),
                **st.session_state.get("feed_params", {}),
            }
            with st.spinner("Optimization running in background... checking every 5 seconds."):
                try:
                    r = requests.post("http://localhost:8000/optimize", json=user_inputs, timeout=10)
                    job_id = r.json()["job_id"]
                    data = {"status": "running"}
                    while data["status"] not in ["complete", "error"]:
                        time.sleep(5)
                        status_r = requests.get(f"http://localhost:8000/status/{job_id}", timeout=10)
                        data = status_r.json()
                    if data["status"] == "complete":
                        data["pareto_df"] = pd.DataFrame(data["pareto_df"])
                        st.session_state["result"] = data
                        st.session_state["result_objective"] = selected_obj
                        st.success("Optimization complete!")
                    else:
                        st.error(f"Optimization failed: {data['message']}")
                except Exception as e:
                    st.error(f"Could not connect to optimization server: {e}. Make sure uvicorn api:app --port 8000 is running.")

    st.markdown("---")

    result     = st.session_state.get("result", None)
    result_obj = st.session_state.get("result_objective", "Lowest Cost & Emissions Pathway")

    if result is None:
        st.info("Select an objective above and click Run Optimization to see results.")
    else:
        if selected_obj != result_obj:
            st.warning(
                f"These results were computed for **{result_obj}**. "
                f"Click **Run Optimization** to recompute for **{selected_obj}**."
            )

        df       = result["pareto_df"]
        feasible = df[df["NAC"].notna()].copy()

        # Pick best row based on objective
        if result_obj == "Lowest Cost Pathway":
            best = feasible.loc[feasible["NAC"].idxmin()]
        elif result_obj == "Lowest Emissions Pathway":
            best = feasible.loc[feasible["GHG"].idxmin()]
        else:
            # Balanced: pick the Pareto point closest to the ideal
            # (min-cost, min-emissions) corner, using normalized NAC/GHG.
            nac_min, nac_max = feasible["NAC"].min(), feasible["NAC"].max()
            ghg_min, ghg_max = feasible["GHG"].min(), feasible["GHG"].max()
            nac_range = nac_max - nac_min
            ghg_range = ghg_max - ghg_min
            nac_norm = (feasible["NAC"] - nac_min) / nac_range if nac_range > 0 else 0
            ghg_norm = (feasible["GHG"] - ghg_min) / ghg_range if ghg_range > 0 else 0
            distance = np.sqrt(nac_norm ** 2 + ghg_norm ** 2)
            best = feasible.loc[distance.idxmin()]

        conv_map = {
            "HTL": "Hydrothermal Liquefaction", "AND": "Anaerobic Digestion",
            "CMP": "Composting",                "WWT": "Wastewater Treatment",
            "SLF": "Sanitary Landfill",         "INC": "Incineration",
        }
        bio_map  = {"AER": "Aerobic Biodigestion", "ENZ": "Enzymatic Hydrolysis"}
        mech_map = {"SHR": "Shredding", "MCR": "Maceration"}

        def is_selected(val):
            return str(val) not in ["-", "0", "nan", "None", "BYP_bio", "BYP1", "BYP2"] and val is not None

        econ      = st.session_state.get("econ", {})
        Qf_v      = st.session_state.get("Qf",   1000)
        Tann_v    = st.session_state.get("Tann", 7920)
        comp_ss   = st.session_state.get("composition", {})
        conv_tech = str(best.get("Conv", ""))
        gasupg    = str(best.get("GasUpg", ""))
        stb_tech  = str(best.get("STB", ""))
        feed_tpy  = Qf_v * Tann_v / 1000

        # ── Product rows ──────────────────────────────────────
        product_rows = []

        if conv_tech == "HTL":
            htl_p     = st.session_state.get("htl_params", {})
            yBIOCRUDE = htl_p.get("yBIOCRUDE", 0.35)
            DS        = 1 - comp_ss.get("WATER", 0)
            bc_tpy    = feed_tpy * DS * yBIOCRUDE
            price_bc  = econ.get("price_BIOCRUDE", 0.48)
            product_rows.append({
                "Product":               "Biocrude",
                "Output [t/yr]":         f"{bc_tpy:.1f}",
                "Market price [$/kg]":   f"{price_bc:.3f}",
                "Total revenue [M$/yr]": f"{bc_tpy * 1000 * price_bc / 1e6:.4f}",
            })

        if conv_tech == "AND" or gasupg in ["ABS", "PSA"]:
            and_p     = st.session_state.get("and_params", {})
            BMP       = and_p.get("BMP_scen", 802.91)
            VS        = (comp_ss.get("CBH",0) + comp_ss.get("PRT",0) +
                         comp_ss.get("FAT",0) + comp_ss.get("OTH",0))
            ch4_tpy   = feed_tpy * VS * BMP * 0.000716
            price_ch4 = econ.get("price_CH4", 0.185)
            product_rows.append({
                "Product":               "Biomethane",
                "Output [t/yr]":         f"{ch4_tpy:.1f}",
                "Market price [$/kg]":   f"{price_ch4:.3f}",
                "Total revenue [M$/yr]": f"{ch4_tpy * 1000 * price_ch4 / 1e6:.4f}",
            })

        if conv_tech == "CMP":
            cmp_p     = st.session_state.get("cmp_params", {})
            fdeg      = cmp_p.get("fdeg_CMP", 0.50)
            VS        = (comp_ss.get("CBH",0) + comp_ss.get("PRT",0) +
                         comp_ss.get("FAT",0) + comp_ss.get("OTH",0))
            cmp_tpy   = feed_tpy * VS * (1 - fdeg)
            price_cmp = econ.get("price_COMPOST", 0.068)
            product_rows.append({
                "Product":               "Compost",
                "Output [t/yr]":         f"{cmp_tpy:.1f}",
                "Market price [$/kg]":   f"{price_cmp:.3f}",
                "Total revenue [M$/yr]": f"{cmp_tpy * 1000 * price_cmp / 1e6:.4f}",
            })

        if conv_tech == "WWT":
            VS       = (comp_ss.get("CBH",0) + comp_ss.get("PRT",0) +
                        comp_ss.get("FAT",0) + comp_ss.get("OTH",0))
            bs_tpy   = feed_tpy * VS * 0.20
            price_bs = econ.get("price_BIOSOLIDS", 0.05)
            product_rows.append({
                "Product":               "Biosolids",
                "Output [t/yr]":         f"{bs_tpy:.1f}",
                "Market price [$/kg]":   f"{price_bs:.3f}",
                "Total revenue [M$/yr]": f"{bs_tpy * 1000 * price_bs / 1e6:.4f}",
            })

        if conv_tech == "INC" or is_selected(stb_tech):
            elec_mwh   = feed_tpy * 15.0 * 0.30 / 3.6
            price_elec = econ.get("price_ELECTRICITY", 0.10)
            product_rows.append({
                "Product":               "Electricity",
                "Output [t/yr]":         f"{elec_mwh:.1f} MWh/yr",
                "Market price [$/kg]":   f"{price_elec:.3f} /kWh",
                "Total revenue [M$/yr]": f"{elec_mwh * 1000 * price_elec / 1e6:.4f}",
            })

        # ── Show cost/emissions sections based on objective ────
        show_cost = result_obj != "Lowest Emissions Pathway"
        show_ghg  = result_obj != "Lowest Cost Pathway"

        # ── Summary metrics ────────────────────────────────────
        if show_cost and show_ghg:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.metric("Net Annual Cost", f"{float(best.get('NAC', 0) or 0):.3f} M$/yr")
            with col_m2:
                st.metric("GHG Emissions", f"{float(best.get('GHG', 0) or 0):,.1f} t CO₂-eq/yr")
        elif show_cost:
            st.metric("Net Annual Cost", f"{float(best.get('NAC', 0) or 0):.3f} M$/yr")
        else:
            st.metric("GHG Emissions", f"{float(best.get('GHG', 0) or 0):,.1f} t CO₂-eq/yr")

        # ── Columns ───────────────────────────────────────────
        if show_cost:
            col_left5, col_right5 = st.columns(2)
        else:
            col_left5  = st.container()
            col_right5 = None

        with col_left5:
            section_header("Technologies in Optimal Pathway")
            tech_rows = [
                {
                    "Stage":      "Pretreatment (mechanical)",
                    "Technology": mech_map.get(str(best.get("Mech","")), "—"),
                    "Selected":   "Yes" if is_selected(best.get("Mech","")) else "No",
                },
                {
                    "Stage":      "Pretreatment (biological)",
                    "Technology": bio_map.get(str(best.get("Bio","")), "—"),
                    "Selected":   "Yes" if is_selected(best.get("Bio","")) else "No",
                },
                {
                    "Stage":      "Conversion",
                    "Technology": conv_map.get(conv_tech, conv_tech),
                    "Selected":   "Yes",
                },
                {
                    "Stage":      "Gas upgrading",
                    "Technology": "Amine Scrubbing" if gasupg == "ABS" else
                                  "Pressure Swing Adsorption" if gasupg == "PSA" else "—",
                    "Selected":   "Yes" if is_selected(gasupg) else "No",
                },
                {
                    "Stage":      "HTL liquid recovery",
                    "Technology": "Centrifugation" if str(best.get("HTLrec","")) == "CEN" else
                                  "Filtration" if str(best.get("HTLrec","")) == "FLT" else "—",
                    "Selected":   "Yes" if is_selected(best.get("HTLrec","")) else "No",
                },
                {
                    "Stage":      "Steam turbine",
                    "Technology": "Steam Turbine" if is_selected(stb_tech) else "—",
                    "Selected":   "Yes" if is_selected(stb_tech) else "No",
                },
            ]
            st.dataframe(pd.DataFrame(tech_rows), use_container_width=True,
                         hide_index=True, height=245)

            section_header("Product Outputs")
            if product_rows:
                st.dataframe(pd.DataFrame(product_rows), use_container_width=True,
                             hide_index=True, height=int(45 + len(product_rows) * 35))
            else:
                st.info("No marketable products identified for this pathway.")

        if show_cost:
          with col_right5:
            section_header("Cost breakdown")
            cost_labels = ["Capital","Working\nCapital","Insurance",
                           "Utilities","Labor","Overhead","Raw\nMaterials","Disposal"]
            cost_cols   = ["CCAC","CCWC","CCINS","CCUC","CCLB","CCOC","CCRM","CDISP"]
            cost_colors = ["#4878CF","#6ACC65","#D65F5F","#B47CC7",
                           "#C4AD66","#77BEDB","#F0A500","#A9A9A9"]
            cost_vals   = [float(best.get(c, 0) or 0) for c in cost_cols]

            fig1, ax1 = plt.subplots(figsize=(5, 2.8))
            fig1.patch.set_facecolor("white")
            ax1.set_facecolor("white")
            ax1.bar(cost_labels, cost_vals, color=cost_colors,
                    edgecolor="white", linewidth=0.5)
            ax1.set_ylabel("Cost [M$/yr]", fontsize=9)
            ax1.tick_params(axis='x', labelsize=7)
            ax1.grid(True, alpha=0.2, axis="y", linestyle="--")
            ax1.spines["top"].set_visible(False)
            ax1.spines["right"].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig1)
            plt.close()

            section_header("Revenue breakdown")
            price_tip = econ.get("C_tip", 0.08)
            rev_tip   = feed_tpy * 1000 * price_tip / 1e6
            total_rev = float(best.get("REV", 0) or 0)
            prod_rev  = max(0, total_rev - rev_tip)

            fig2, ax2 = plt.subplots(figsize=(5, 2.8))
            fig2.patch.set_facecolor("white")
            ax2.set_facecolor("white")
            ax2.bar(["Tipping fee", "Product\nrevenue", "Total\nrevenue"],
                    [rev_tip, prod_rev, total_rev],
                    color=["#2E8B57","#1D9E75","#378ADD"],
                    edgecolor="white", linewidth=0.5)
            ax2.set_ylabel("Revenue [M$/yr]", fontsize=9)
            ax2.tick_params(axis='x', labelsize=8)
            ax2.grid(True, alpha=0.2, axis="y", linestyle="--")
            ax2.spines["top"].set_visible(False)
            ax2.spines["right"].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig2)
            plt.close()

        if show_ghg:
            st.markdown("---")
            section_header("Emissions breakdown")
            ghg_labels = ["Indirect\n(Electricity)", "Direct\n(Process)",
                          "Aqueous/Char\nDisposal", "Displacement\nCredits"]
            ghg_cols   = ["GHG_IND", "GHG_DIR", "GHG_AQ", "GHG_DISP"]
            ghg_colors = ["#378ADD", "#D85A30", "#B47CC7", "#1D9E75"]
            ghg_vals   = [float(best.get(c, 0) or 0) for c in ghg_cols]
            # Displacement credits reduce total emissions, so show as negative
            ghg_vals[3] = -ghg_vals[3]

            fig3, ax3 = plt.subplots(figsize=(8, 3))
            fig3.patch.set_facecolor("white")
            ax3.set_facecolor("white")
            ax3.bar(ghg_labels, ghg_vals, color=ghg_colors,
                    edgecolor="white", linewidth=0.5)
            ax3.axhline(y=0, color="black", linewidth=0.8)
            ax3.set_ylabel("GHG Emissions [t CO₂-eq/yr]", fontsize=9)
            ax3.tick_params(axis='x', labelsize=8)
            ax3.grid(True, alpha=0.2, axis="y", linestyle="--")
            ax3.spines["top"].set_visible(False)
            ax3.spines["right"].set_visible(False)
            plt.tight_layout()
            st.pyplot(fig3)
            plt.close()
            st.caption(
                f"**Total GHG Emissions: {float(best.get('GHG', 0) or 0):,.1f} t CO₂-eq/yr** "
                "= Indirect + Direct + Aqueous/Char − Displacement Credits"
            )

        if result_obj == "Lowest Cost & Emissions Pathway":
            st.markdown("---")
            section_header("Pareto Front — All Trade-off Solutions")
            if not feasible.empty:
                color_map = {
                    "HTL": "#7F77DD", "AND": "#1D9E75", "CMP": "#D4537E",
                    "WWT": "#378ADD", "SLF": "#D85A30", "INC": "#BA7517",
                }
                fig_p, ax_p = plt.subplots(figsize=(10, 4))
                fig_p.patch.set_facecolor("white")
                ax_p.set_facecolor("white")
                for _, row in feasible.iterrows():
                    color = color_map.get(str(row["Conv"]), "#999999")
                    ax_p.scatter(row["NAC"], row["GHG"], color=color, s=100,
                                 zorder=5, edgecolors="black", linewidth=0.8)
                    ax_p.annotate(str(row["Pareto_pt"]), (row["NAC"], row["GHG"]),
                                  textcoords="offset points", xytext=(5, 3), fontsize=8)
                sorted_f = feasible.sort_values("NAC")
                ax_p.plot(sorted_f["NAC"], sorted_f["GHG"], "k--", linewidth=1, alpha=0.5)
                patches = [mpatches.Patch(color=c, label=conv_map.get(t, t))
                           for t, c in color_map.items()
                           if t in feasible["Conv"].values]
                ax_p.legend(handles=patches, title="Conversion technology", fontsize=9)
                ax_p.set_xlabel("Net Annual Cost [M$/yr]", fontsize=10)
                ax_p.set_ylabel("GHG Emissions [t CO2-eq/yr]", fontsize=10)
                ax_p.grid(True, alpha=0.3, linestyle="--")
                ax_p.spines["top"].set_visible(False)
                ax_p.spines["right"].set_visible(False)
                plt.tight_layout()
                st.pyplot(fig_p)
                plt.close()

        st.markdown("---")
        csv = df.to_csv(index=False)
        st.download_button("Download Results CSV", csv, "pareto_results.csv", "text/csv")


# ============================================================
# ============================================================
# TAB 6 - ENVIRONMENTAL JUSTICE
# ============================================================
with tab6:

    CENSUS_API_KEY = "3d8f6af9980c901549cd2ba01f6ad14ffed8fa20"

    section_header("Environmental Justice Assessment")
    st.markdown(
        "This tab calculates the Environmental Justice (EJ) burden of each food waste "
        "processing pathway using the methodology of Joseph & Kamanmalek (2026) and "
        "Greer et al. (2024). The EJ Index combines pathway emissions with community "
        "vulnerability to identify the most equitable processing option."
    )

    zipcode = st.session_state.get("zipcode")
    result  = st.session_state.get("result", None)

    if not zipcode:
        st.info("Enter a facility zip code in the Feed Inputs tab to enable the EJ assessment.")
        st.stop()

    # ============================================================
    # HELPER FUNCTIONS
    # ============================================================

    @st.cache_data(show_spinner=False)
    def get_coords_from_zip(zc):
        known_coords = {
            "08028": (39.7026, -75.1121),
            "07102": (40.7357, -74.1724),
            "10001": (40.7484, -73.9967),
            "19104": (39.9526, -75.1652),
            "07030": (40.7440, -74.0324),
            "08901": (40.4774, -74.4432),
            "07001": (40.5851, -74.2771),
            "08103": (39.9526, -75.1196),
            "07306": (40.7178, -74.0431),
            "10451": (40.8282, -73.9265),
        }
        zc = str(zc).strip().zfill(5)
        if zc in known_coords:
            return known_coords[zc]
        try:
            url = f"https://api.zippopotam.us/us/{zc}"
            r   = requests.get(url, timeout=10)
            if r.status_code == 200:
                place = r.json()["places"][0]
                return float(place["latitude"]), float(place["longitude"])
        except:
            pass
        return None, None

    @st.cache_data(show_spinner=False)
    def get_census_demographics(zc, api_key):
        try:
            zc = str(zc).strip().zfill(5)

            # Step 1 — get city and state
            city  = "Unknown"
            state = "Unknown"
            try:
                zip_url = f"https://api.zippopotam.us/us/{zc}"
                zip_r   = requests.get(zip_url, timeout=10)
                if zip_r.status_code == 200:
                    zip_data = zip_r.json()
                    city  = zip_data["places"][0]["place name"]
                    state = zip_data["places"][0]["state abbreviation"]
            except:
                pass

            # Step 2 — Census API with key
            census_url = (
                f"https://api.census.gov/data/2023/acs/acs5"
                f"?get=B03002_001E,B03002_003E,"
                f"B17001_001E,B17001_002E,B01003_001E"
                f"&for=zip%20code%20tabulation%20area:{zc}"
                f"&key={api_key}"
            )
            cr    = requests.get(census_url, timeout=15)
            cdata = cr.json()

            if len(cdata) >= 2:
                headers = cdata[0]
                values  = cdata[1]
                row     = dict(zip(headers, values))

                total_pop    = float(row.get("B01003_001E", 0) or 0)
                total_race   = float(row.get("B03002_001E", 1) or 1)
                white_alone  = float(row.get("B03002_003E", 0) or 0)
                pov_universe = float(row.get("B17001_001E", 1) or 1)
                pov_below    = float(row.get("B17001_002E", 0) or 0)

                pct_poc       = max(0, ((total_race - white_alone) / total_race) * 100)
                pct_lowincome = max(0, (pov_below / pov_universe) * 100)
                data_source   = "U.S. Census ACS 2023 5-year estimates (zip code level)"

            else:
                raise ValueError("No data returned")

            # National averages ACS 2022
            NAT_AVG_POC       = 40.0
            NAT_AVG_LOWINCOME = 29.0
            demo_index        = (pct_poc + pct_lowincome) / 2
            nat_demo_index    = (NAT_AVG_POC + NAT_AVG_LOWINCOME) / 2

            return {
                "total_pop":         total_pop,
                "pct_poc":           round(pct_poc, 1),
                "pct_lowincome":     round(pct_lowincome, 1),
                "demo_index":        round(demo_index, 2),
                "nat_demo_index":    round(nat_demo_index, 2),
                "nat_avg_poc":       NAT_AVG_POC,
                "nat_avg_lowincome": NAT_AVG_LOWINCOME,
                "city":              city,
                "state":             state,
                "data_source":       data_source,
            }

        except Exception as e:
            # Fallback to state level estimates
            state_defaults = {
                "NJ": {"pct_poc": 43.2, "pct_lowincome": 26.1, "total_pop": 20000},
                "NY": {"pct_poc": 57.8, "pct_lowincome": 32.4, "total_pop": 25000},
                "PA": {"pct_poc": 31.2, "pct_lowincome": 29.8, "total_pop": 18000},
                "CA": {"pct_poc": 63.4, "pct_lowincome": 31.2, "total_pop": 30000},
                "TX": {"pct_poc": 59.1, "pct_lowincome": 33.6, "total_pop": 22000},
                "FL": {"pct_poc": 47.2, "pct_lowincome": 30.1, "total_pop": 21000},
                "GA": {"pct_poc": 51.3, "pct_lowincome": 31.4, "total_pop": 19000},
                "IL": {"pct_poc": 45.6, "pct_lowincome": 30.2, "total_pop": 21000},
                "OH": {"pct_poc": 28.4, "pct_lowincome": 30.1, "total_pop": 17000},
                "NC": {"pct_poc": 40.2, "pct_lowincome": 29.8, "total_pop": 18000},
            }
            defaults = state_defaults.get(state, {
                "pct_poc": 40.0, "pct_lowincome": 29.0, "total_pop": 20000,
            })
            NAT_AVG_POC       = 40.0
            NAT_AVG_LOWINCOME = 29.0
            demo_index        = (defaults["pct_poc"] + defaults["pct_lowincome"]) / 2
            nat_demo_index    = (NAT_AVG_POC + NAT_AVG_LOWINCOME) / 2
            return {
                "total_pop":         defaults["total_pop"],
                "pct_poc":           defaults["pct_poc"],
                "pct_lowincome":     defaults["pct_lowincome"],
                "demo_index":        round(demo_index, 2),
                "nat_demo_index":    round(nat_demo_index, 2),
                "nat_avg_poc":       NAT_AVG_POC,
                "nat_avg_lowincome": NAT_AVG_LOWINCOME,
                "city":              city,
                "state":             state,
                "data_source":       "State-level ACS estimates (Census API unavailable)",
            }

    def calculate_ej_index(ghg_tpy, demo_index, nat_demo_index, population):
        return ghg_tpy * (demo_index / 100 - nat_demo_index / 100) * population

    def ej_concern_label(ej_val, ej_min, ej_max):
        if ej_max == ej_min:
            return "🟡 MODERATE"
        norm = (ej_val - ej_min) / (ej_max - ej_min)
        if norm >= 0.67:
            return "🔴 HIGH"
        elif norm >= 0.33:
            return "🟡 MODERATE"
        else:
            return "🟢 LOW"

    # ============================================================
    # FETCH DATA
    # ============================================================
    with st.spinner(f"Loading data for zip code {zipcode}..."):
        lat, lon    = get_coords_from_zip(zipcode)
        census_data = get_census_demographics(zipcode, CENSUS_API_KEY)

    if census_data is None:
        st.warning(
            f"Could not retrieve demographic data for zip code {zipcode}. "
            "Please check the zip code and try again."
        )
        st.stop()

    # ============================================================
    # SECTION 1 — MAP
    # ============================================================
    section_header("Facility Location & Buffer Zones")
    st.markdown(
        "Buffer zones of **1 km**, **3 km**, and **5 km** are drawn around "
        "the facility location following Joseph & Kamanmalek (2026)."
    )

    if lat and lon:
        try:
            import folium
            from streamlit_folium import st_folium

            m_map = folium.Map(
                location=[lat, lon],
                zoom_start=12,
                tiles="CartoDB positron"
            )
            folium.Circle(
                location=[lat, lon], radius=5000,
                color="#2E8B57", weight=2,
                fill=True, fill_opacity=0.07,
                tooltip="5 km — Broader community"
            ).add_to(m_map)
            folium.Circle(
                location=[lat, lon], radius=3000,
                color="#FF8800", weight=2,
                fill=True, fill_opacity=0.10,
                tooltip="3 km — Surrounding neighborhood"
            ).add_to(m_map)
            folium.Circle(
                location=[lat, lon], radius=1000,
                color="#CC0000", weight=2,
                fill=True, fill_opacity=0.15,
                tooltip="1 km — Immediate impact zone"
            ).add_to(m_map)
            folium.Marker(
                location=[lat, lon],
                tooltip=(
                    f"Facility — {census_data['city']}, "
                    f"{census_data['state']} {zipcode}"
                ),
                icon=folium.Icon(color="red", icon="info-sign")
            ).add_to(m_map)
            legend_html = """
            <div style="position:fixed; bottom:30px; left:30px; z-index:1000;
                        background:white; padding:12px 16px;
                        border:1px solid #ccc; border-radius:8px;
                        font-size:12px; font-family:Arial;">
                <b>Buffer Zones</b><br>
                <span style="color:#CC0000;">&#9679;</span>
                1 km &nbsp;Immediate impact<br>
                <span style="color:#FF8800;">&#9679;</span>
                3 km &nbsp;Neighborhood<br>
                <span style="color:#2E8B57;">&#9679;</span>
                5 km &nbsp;Broader community
            </div>
            """
            m_map.get_root().html.add_child(folium.Element(legend_html))
            st_folium(m_map, width=700, height=420, returned_objects=[])

        except ImportError:
            st.warning("Run: python -m pip install folium streamlit-folium")
    else:
        st.info(f"Map unavailable for zip code {zipcode}.")

    # ============================================================
    # SECTION 2 — COMMUNITY PROFILE
    # ============================================================
    st.markdown("---")
    section_header("Community Profile")
    st.markdown(
        f"Demographics for **{census_data['city']}, "
        f"{census_data['state']} ({zipcode})** "
        "compared to national averages.  \n"
        f"Source: {census_data['data_source']}."
    )

    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.metric(
            "Total Population",
            f"{int(census_data['total_pop']):,}"
        )
    with col_p2:
        delta_poc = census_data["pct_poc"] - census_data["nat_avg_poc"]
        st.metric(
            "People of Color",
            f"{census_data['pct_poc']:.1f}%",
            delta=f"{delta_poc:+.1f}% vs national",
            delta_color="inverse"
        )
    with col_p3:
        delta_li = census_data["pct_lowincome"] - census_data["nat_avg_lowincome"]
        st.metric(
            "Low Income",
            f"{census_data['pct_lowincome']:.1f}%",
            delta=f"{delta_li:+.1f}% vs national",
            delta_color="inverse"
        )
    with col_p4:
        delta_di = census_data["demo_index"] - census_data["nat_demo_index"]
        st.metric(
            "Demographic Index",
            f"{census_data['demo_index']:.1f}%",
            delta=f"{delta_di:+.1f}% vs national",
            delta_color="inverse"
        )

    # ============================================================
    # SECTION 3 — EJ INDEX PER PATHWAY
    # ============================================================
    st.markdown("---")
    section_header("Environmental Justice Index by Pathway")
    st.markdown(
        "The EJ Index combines **pathway GHG emissions** with "
        "**community vulnerability** to show which processing option "
        "places the least burden on the surrounding community.  \n"
        "**Lower EJ Index = more equitable outcome.**"
    )
    st.caption(
        "EJ Index = GHG Emissions (t CO₂-eq/yr) × "
        "(Local Demographic Index − National Average) × Population  \n"
        "Following Greer et al. (2024) Equation 2 and "
        "EJScreen methodology (U.S. EPA, 2023)"
    )

    if result is None:
        st.info(
            "Run the optimization in the **Results** tab first "
            "to calculate pathway-specific EJ scores."
        )
    else:
        df       = result["pareto_df"]
        feasible = df[df["GHG"].notna()].copy()

        if feasible.empty:
            st.warning("No feasible results found. Please re-run the optimization.")
        else:
            conv_map_full = {
                "HTL": "Hydrothermal Liquefaction",
                "AND": "Anaerobic Digestion",
                "CMP": "Composting",
                "WWT": "Wastewater Treatment",
                "SLF": "Sanitary Landfill",
                "INC": "Incineration",
            }
            color_map_ej = {
                "HTL": "#7F77DD",
                "AND": "#1D9E75",
                "CMP": "#D4537E",
                "WWT": "#378ADD",
                "SLF": "#D85A30",
                "INC": "#BA7517",
            }

            # Get lowest GHG per conversion technology
            pathway_ghg = {}
            for conv in conv_map_full.keys():
                subset = feasible[feasible["Conv"] == conv]
                if not subset.empty:
                    pathway_ghg[conv] = subset["GHG"].min()

            if not pathway_ghg:
                st.warning("No pathway GHG data found. Please re-run optimization.")
                st.stop()

            # Calculate EJ Index per pathway
            demo_idx   = census_data["demo_index"]
            nat_idx    = census_data["nat_demo_index"]
            population = census_data["total_pop"]

            ej_rows = []
            for conv, ghg in pathway_ghg.items():
                ej_index = calculate_ej_index(
                    ghg, demo_idx, nat_idx, population
                )
                ej_rows.append({
                    "conv_code":          conv,
                    "Technology":         conv_map_full[conv],
                    "GHG (t CO₂-eq/yr)": round(ghg, 1),
                    "EJ Index":           round(ej_index, 0),
                })

            ej_df  = (pd.DataFrame(ej_rows)
                        .sort_values("EJ Index")
                        .reset_index(drop=True))
            ej_min = ej_df["EJ Index"].min()
            ej_max = ej_df["EJ Index"].max()

            ej_df["EJ Rank"]    = range(1, len(ej_df) + 1)
            ej_df["EJ Concern"] = ej_df["EJ Index"].apply(
                lambda x: ej_concern_label(x, ej_min, ej_max)
            )

            st.dataframe(
                ej_df[[
                    "EJ Rank", "Technology",
                    "GHG (t CO₂-eq/yr)", "EJ Index", "EJ Concern"
                ]],
                use_container_width=True,
                hide_index=True
            )

            fig_ej, ax_ej = plt.subplots(figsize=(8, 3.5))
            fig_ej.patch.set_facecolor("white")
            ax_ej.set_facecolor("white")
            techs  = ej_df["Technology"].tolist()
            values = ej_df["EJ Index"].tolist()
            colors = [
                color_map_ej.get(c, "#999999")
                for c in ej_df["conv_code"].tolist()
            ]
            ax_ej.barh(
                techs, values,
                color=colors, edgecolor="white", linewidth=0.5
            )
            ax_ej.set_xlabel(
                "EJ Index — higher = greater burden on vulnerable communities",
                fontsize=9
            )
            ax_ej.axvline(x=0, color="black", linewidth=0.8, linestyle="--")
            ax_ej.spines["top"].set_visible(False)
            ax_ej.spines["right"].set_visible(False)
            ax_ej.grid(True, alpha=0.2, axis="x", linestyle="--")
            plt.tight_layout()
            st.pyplot(fig_ej)
            plt.close()

            # ============================================================
            # SECTION 4 — RECOMMENDATION
            # ============================================================
            st.markdown("---")
            section_header("EJ Recommendation")

            best_pathway  = ej_df.iloc[0]
            worst_pathway = ej_df.iloc[-1]

            if demo_idx > nat_idx:
                st.warning(
                    f"⚠️ The community around this facility has a "
                    f"Demographic Index of **{demo_idx:.1f}%** — "
                    f"above the national average of **{nat_idx:.1f}%**. "
                    f"This population is more vulnerable and EJ "
                    f"considerations are especially important here."
                )
            else:
                st.success(
                    f"✅ The community around this facility has a "
                    f"Demographic Index of **{demo_idx:.1f}%** — "
                    f"at or below the national average of {nat_idx:.1f}%. "
                    "Standard pathway selection applies, but community "
                    "engagement is still recommended."
                )

            ej_diff = abs(worst_pathway["EJ Index"] - best_pathway["EJ Index"])
            st.markdown(
                f"**Most equitable pathway:** "
                f"{best_pathway['Technology']} — "
                f"EJ Index: **{best_pathway['EJ Index']:,.0f}**  \n"
                f"**Least equitable pathway:** "
                f"{worst_pathway['Technology']} — "
                f"EJ Index: **{worst_pathway['EJ Index']:,.0f}**  \n\n"
                f"Selecting **{best_pathway['Technology']}** over "
                f"**{worst_pathway['Technology']}** reduces the EJ "
                f"burden on this community by "
                f"**{ej_diff:,.0f} EJ Index units**."
            )

            # ============================================================
            # SECTION 5 — CITATIONS
            # ============================================================
            st.markdown("---")
            with st.expander("Methodology & Citations"):
                st.markdown("""
**Buffer Zone Analysis**
Buffer zones of 1 km, 3 km, and 5 km are drawn around the facility
location following Joseph & Kamanmalek (2026), who applied this method
to 142 landfills in South Carolina using ArcGIS Pro 3.2.2.

**Demographic Index**
Demographic Index = (% people of color + % low income) ÷ 2
Following the EJScreen Technical Documentation (U.S. EPA, 2023).

**EJ Index Formula**
EJ Index = Pathway GHG Emissions × (Local Demographic Index −
National Demographic Index) × Population
Following Greer et al. (2024) Equation 2 — Exposure Disparity
formula from the Port of Oakland environmental justice study.

**References**
- Joseph & Kamanmalek (2026). Environmental Sociology, Vol. 12,
  No. 2, pp. 390–414
- Greer, Bin Thaneya & Horvath (2024). Environmental Science &
  Technology, 58, 8135–8148. DOI: 10.1021/acs.est.3c07728
- U.S. EPA (2023). EJScreen Technical Documentation v2.2
- U.S. Census Bureau. ACS 2023 5-Year Estimates
                """)