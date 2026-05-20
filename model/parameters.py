"""
model/parameters.py
====================
Defines all GAMSPy scalars and indexed parameters.
 
Sections:
    A. Scalars — user inputs (feed, operating, economic)
    B. Scalars — fixed process constants per technology
    C. Scalars — GHG emission factors
    D. Scalars — Pareto optimization
    E. Indexed Parameters — feed, equipment, costs, prices
 
User-controllable scalars are clearly marked with ← USER INPUT
"""
 
from gamspy import Container, Parameter
 
 
# ============================================================
# HELPER
# ============================================================
def sc(m, name, val, desc=""):
    """Shorthand for creating a scalar Parameter."""
    return Parameter(m, name=name, description=desc, records=val)
 
 
# ============================================================
# SECTION A — USER INPUT SCALARS
# ============================================================
def build_user_scalars(m: Container, user_inputs: dict) -> dict:
    """
    Build scalars that the user can control via the app.
 
    Parameters
    ----------
    m : Container
    user_inputs : dict with keys:
        Qf, Tann, C_elec, C_tip, C_lbr, CRF,
        composition (dict)
 
    Returns
    -------
    dict of scalar Parameters
    """
    comp = user_inputs.get("composition", {
        "WATER":        0.75952,
        "CBH":          0.016745,
        "PRT":          0.108027,
        "FAT":          0.046492,
        "OTH":          0.020929,
        "ASH":          0.012427,
        "FIXED_CARBON": 0.035360,
    })
 
    scalars = {}
 
    # ── Feed ──────────────────────────────────────────────────────
    scalars["Qf"]       = sc(m, "Qf",       user_inputs.get("Qf",    1000),  "Feed flow rate kg/hr")         # ← USER INPUT
    scalars["x_MC"]     = sc(m, "x_MC",     comp.get("WATER", 0.75952),      "Moisture content wet basis")
    scalars["HHV_feed"] = sc(m, "HHV_feed", user_inputs.get("HHV_feed", 15.67), "HHV of feed MJ/kg")
 
    # Feed composition fractions (wet basis) from database
    scalars["f_CBH_wet"] = sc(m, "f_CBH_wet", comp.get("CBH",          0.016745))
    scalars["f_PRT_wet"] = sc(m, "f_PRT_wet", comp.get("PRT",          0.108027))
    scalars["f_FAT_wet"] = sc(m, "f_FAT_wet", comp.get("FAT",          0.046492))
    scalars["f_OTH_wet"] = sc(m, "f_OTH_wet", comp.get("OTH",          0.020929))
    scalars["f_ASH_wet"] = sc(m, "f_ASH_wet", comp.get("ASH",          0.012427))
    scalars["f_FC_wet"]  = sc(m, "f_FC_wet",  comp.get("FIXED_CARBON", 0.035360))
 
    # ── Ultimate analysis (dry basis) — fixed ─────────────────────
    scalars["C_frac"] = sc(m, "C_frac", 0.43270, "Carbon fraction dry basis")
    scalars["H_frac"] = sc(m, "H_frac", 0.06050, "Hydrogen fraction dry basis")
    scalars["O_frac"] = sc(m, "O_frac", 0.42890, "Oxygen fraction dry basis")
    scalars["N_frac"] = sc(m, "N_frac", 0.07170, "Nitrogen fraction dry basis")
    scalars["S_frac"] = sc(m, "S_frac", 0.00620, "Sulfur fraction dry basis")
 
    # ── Global operating ──────────────────────────────────────────
    scalars["Tann"]    = sc(m, "Tann",    user_inputs.get("Tann",   7920), "Annual operating hours")  # ← USER INPUT
    scalars["C_elec"]  = sc(m, "C_elec",  user_inputs.get("C_elec", 0.1),  "Electricity cost $/kWh")  # ← USER INPUT
    scalars["C_lbr"]   = sc(m, "C_lbr",   user_inputs.get("C_lbr",  30),   "Labor cost $/hr")         # ← USER INPUT
    scalars["C_tip"]   = sc(m, "C_tip",   user_inputs.get("C_tip",  0.08), "Tipping fee $/kg")        # ← USER INPUT
    scalars["CRF"]     = sc(m, "CRF",     user_inputs.get("CRF",    0.11), "Capital recovery factor") # ← USER INPUT
    scalars["C_stm"]   = sc(m, "C_stm",   0.012,   "Steam cost $/kg")
    scalars["epsv"]    = sc(m, "epsv",    0.01,    "Small epsilon for numerical stability")
    scalars["nc"]      = sc(m, "nc",      0.67,    "Cost scaling exponent")
    scalars["BMC_mult"]= sc(m, "BMC_mult",5.4,     "Bare module cost multiplier")
    scalars["Den_FW"]  = sc(m, "Den_FW",  1290,    "Food waste density kg/m3")
    scalars["MM"]      = sc(m, "MM",      1000000, "Big-M value")
 
    return scalars
 
 
# ============================================================
# SECTION B — FIXED PROCESS SCALARS PER TECHNOLOGY
# ============================================================
def build_process_scalars(m: Container) -> dict:
    """Build all fixed process constants."""
    scalars = {}
 
    # ── AER (Aerobic biodigester) ──────────────────────────────────
    scalars["V_AER_max"]  = sc(m, "V_AER_max",  2000,  "Max AER vessel volume m3")
    scalars["Rw_AER"]     = sc(m, "Rw_AER",     1.5,   "Water addition ratio AER kg/kg dry")
    scalars["theta_AER"]  = sc(m, "theta_AER",  24.0,  "AER HRT hours")
    scalars["eps_AER"]    = sc(m, "eps_AER",    0.80,  "AER vessel fill fraction")
    scalars["yCO2_AER"]   = sc(m, "yCO2_AER",   1.20,  "kg CO2/kg VS degraded AER")
    scalars["yH2O_AER"]   = sc(m, "yH2O_AER",   0.20,  "kg H2O/kg VS degraded AER")
 
    # ── ENZ (Enzymatic hydrolysis) ─────────────────────────────────
    scalars["V_ENZ_max"]  = sc(m, "V_ENZ_max",  500,   "Max ENZ vessel volume m3")
    scalars["r_enz"]      = sc(m, "r_enz",      0.02,  "Enzyme dose kg/kg dry solids")
    scalars["eta_ENZ"]    = sc(m, "eta_ENZ",    0.85,  "ENZ hydrolysis efficiency")
    scalars["HRT_ENZ"]    = sc(m, "HRT_ENZ",    6.0,   "ENZ HRT hours")
 
    # ── MCR (Macerator) ────────────────────────────────────────────
    scalars["Rw_MCR"]     = sc(m, "Rw_MCR",     2.0,   "MCR water addition ratio kg/kg dry")
 
    # ── SHR (Shredder) ─────────────────────────────────────────────
    scalars["eta_SHR"]    = sc(m, "eta_SHR",    0.99,  "SHR separation efficiency")
 
    # ── HTL (Hydrothermal liquefaction) ────────────────────────────
    scalars["rDry_HTL"]   = sc(m, "rDry_HTL",   7.0,   "HTL minimum water to dry solids ratio")
    scalars["rho_HTL"]    = sc(m, "rho_HTL",    1000.0,"HTL slurry density kg/m3")
    scalars["T_HTL"]      = sc(m, "T_HTL",      340.0, "HTL operating temperature C")
    scalars["T_amb"]      = sc(m, "T_amb",      25.0,  "Ambient temperature C")
    scalars["etaHX_HTL"]  = sc(m, "etaHX_HTL",  0.70,  "HTL heat exchanger efficiency")
    scalars["Cp_eff"]     = sc(m, "Cp_eff",     4.2,   "Effective heat capacity kJ/kg C")
    scalars["dh_steam"]   = sc(m, "dh_steam",   2046.5,"Steam latent heat kJ/kg")
    scalars["theta_HTL"]  = sc(m, "theta_HTL",  1.0,   "HTL HRT hours")
    scalars["eps_HTL"]    = sc(m, "eps_HTL",    0.85,  "HTL vessel fill fraction")
    scalars["Vm_STP"]     = sc(m, "Vm_STP",     22.414,"Molar volume at STP m3/kmol")
    scalars["HHV_HTLgas"] = sc(m, "HHV_HTLgas", 28.0,  "HTL gas HHV MJ/kg")
 
    # ── AND (Anaerobic digestion) ───────────────────────────────────
    scalars["rhoCH4"]      = sc(m, "rhoCH4",      0.000716,"CH4 density kg/L")
    scalars["theta_AND"]   = sc(m, "theta_AND",   720.0,   "AND HRT hours")
    scalars["epsilon_AND"] = sc(m, "epsilon_AND", 0.85,    "AND vessel fill fraction")
    scalars["eta_OTH_AND"] = sc(m, "eta_OTH_AND", 0.30,   "AND OTH degradation fraction")
    scalars["Rw_AND"]      = sc(m, "Rw_AND",      1.0,    "AND water addition ratio kg/kg dry")
    scalars["eta_cap_AND"] = sc(m, "eta_cap_AND", 0.98,   "AND biogas capture efficiency")
    scalars["MW_CH4"]      = sc(m, "MW_CH4",      16.04,  "Molecular weight CH4 g/mol")
    scalars["MW_CO2_AND"]  = sc(m, "MW_CO2_AND",  44.01,  "Molecular weight CO2 g/mol")
    scalars["eta_AND"]     = sc(m, "eta_AND",     1.0,    "AND VS degradation efficiency")
    scalars["BMP_scen"]    = sc(m, "BMP_scen",    802.91, "Biochemical methane potential mL/g VS")
 
    # ── SLF (Sanitary landfill) ────────────────────────────────────
    scalars["DOC_value"]      = sc(m, "DOC_value",      0.358,   "Degradable organic carbon fraction")
    scalars["DOC_f_value"]    = sc(m, "DOC_f_value",    0.77,    "DOC fraction that decomposes")
    scalars["MCF_value"]      = sc(m, "MCF_value",      0.6,     "Methane correction factor")
    scalars["F_value"]        = sc(m, "F_value",        0.576,   "Fraction of CH4 in landfill gas")
    scalars["density_CH4"]    = sc(m, "density_CH4",    0.717,   "CH4 density kg/m3")
    scalars["ratio_CH4_to_C"] = sc(m, "ratio_CH4_to_C", 1.3333, "CH4 to C mass ratio")
    scalars["Depth_SLF"]      = sc(m, "Depth_SLF",      10.0,   "Landfill depth m")
    scalars["ACRE"]           = sc(m, "ACRE",            4046.86,"m2 per acre")
    scalars["OX"]             = sc(m, "OX",              0.1,    "CH4 oxidation fraction")
    scalars["CAP_SLF"]        = sc(m, "CAP_SLF",         0.65,  "Landfill gas capture efficiency")
    scalars["MW1_CH4"]        = sc(m, "MW1_CH4",         16.0,  "CH4 molecular weight g/mol")
    scalars["MW1_CO2"]        = sc(m, "MW1_CO2",         44.0,  "CO2 molecular weight g/mol")
 
    # ── CMP (Composting) ───────────────────────────────────────────
    scalars["fdeg_CMP"]       = sc(m, "fdeg_CMP",       0.50,   "CMP VS degradation fraction")
    scalars["yCO2_CMP"]       = sc(m, "yCO2_CMP",       0.55,   "kg CO2/kg VS degraded CMP")
    scalars["yH2O_CMP"]       = sc(m, "yH2O_CMP",       0.45,   "kg H2O/kg VS degraded CMP")
    scalars["yNH3_CMP"]       = sc(m, "yNH3_CMP",       0.00,   "kg NH3/kg VS degraded CMP")
    scalars["EF_CH4_CMP_wet"] = sc(m, "EF_CH4_CMP_wet", 0.004, "CMP CH4 emission factor kg/kg wet")
    scalars["EF_N2O_CMP_wet"] = sc(m, "EF_N2O_CMP_wet", 0.0003,"CMP N2O emission factor kg/kg wet")
    scalars["theta_CMP"]      = sc(m, "theta_CMP",      120.0,  "CMP HRT hours")
    scalars["epsilon_CMP"]    = sc(m, "epsilon_CMP",    0.7,    "CMP vessel fill fraction")
    scalars["eta_OTH_CMP"]    = sc(m, "eta_OTH_CMP",    0.60,  "CMP OTH degradation fraction")
    scalars["yO2_air"]        = sc(m, "yO2_air",        0.232,  "O2 mass fraction in air")
    scalars["yN2_air"]        = sc(m, "yN2_air",        0.768,  "N2 mass fraction in air")
    scalars["EAR_CMP"]        = sc(m, "EAR_CMP",        2.5,   "Excess air ratio CMP")
    scalars["alpha_O2_CMP"]   = sc(m, "alpha_O2_CMP",   1.2,   "O2 demand per kg VS degraded CMP")
 
    # ── WWT (Wastewater treatment) ─────────────────────────────────
    scalars["HRT_WWT_min"] = sc(m, "HRT_WWT_min", 6.0,    "WWT minimum HRT hours")
    scalars["rho_ww"]      = sc(m, "rho_ww",      1000.0, "Wastewater density kg/m3")
    scalars["fBOD"]        = sc(m, "fBOD",        1.2,    "BOD/VS ratio")
    scalars["FM_day"]      = sc(m, "FM_day",      0.30,   "F/M ratio kg BOD/kg MLSS/day")
    scalars["X_MLSS"]      = sc(m, "X_MLSS",      3.0,    "MLSS concentration kg/m3")
    scalars["n_wwtp"]      = sc(m, "n_wwtp",      0.6,    "WWT yield coefficient kg VS/kg BOD")
    scalars["b_wwtp"]      = sc(m, "b_wwtp",      0.05,   "WWT decay coefficient 1/day")
    scalars["SRT_day"]     = sc(m, "SRT_day",     8.0,    "WWT sludge retention time days")
    scalars["yCO2_WWT"]    = sc(m, "yCO2_WWT",    1.467,  "kg CO2/kg VS degraded WWT")
    scalars["yH2O_WWT"]    = sc(m, "yH2O_WWT",    0.600,  "kg H2O/kg VS degraded WWT")
 
    # ── INC (Incineration) ─────────────────────────────────────────
    scalars["lambda_inc"]     = sc(m, "lambda_inc",     1.2,    "INC excess air ratio")
    scalars["EF_CH4_INC_wet"] = sc(m, "EF_CH4_INC_wet", 5.6e-7,"INC CH4 emission factor kg/kg wet")
    scalars["EF_N2O_INC_wet"] = sc(m, "EF_N2O_INC_wet", 5.6e-5,"INC N2O emission factor kg/kg wet")
 
    # ── STB (Steam turbine) ────────────────────────────────────────
    scalars["T_g_in"]        = sc(m, "T_g_in",        850.0,  "Flue gas inlet temperature C")
    scalars["T_g_out"]       = sc(m, "T_g_out",       400.0,  "Flue gas outlet temperature C")
    scalars["CP_g"]          = sc(m, "CP_g",          1.15,   "Flue gas heat capacity kJ/kg C")
    scalars["H2_steam"]      = sc(m, "H2_steam",      3277.9, "Steam enthalpy at turbine inlet kJ/kg")
    scalars["H1_water"]      = sc(m, "H1_water",      104.83, "Feedwater enthalpy kJ/kg")
    scalars["h1_value"]      = sc(m, "h1_value",      3500.0, "Turbine inlet enthalpy kJ/kg")
    scalars["h2_value"]      = sc(m, "h2_value",      2800.0, "Turbine outlet enthalpy kJ/kg")
    scalars["eta_turbine"]   = sc(m, "eta_turbine",   0.85,   "Turbine isentropic efficiency")
    scalars["eta_generator"] = sc(m, "eta_generator", 0.95,   "Generator efficiency")
    scalars["MM_ST"]         = sc(m, "MM_ST",         1e6,    "Big-M for STB constraints")
 
    # ── ABS/PSA (Gas upgrading) ────────────────────────────────────
    scalars["Pur_CH4"]      = sc(m, "Pur_CH4",      0.96,   "Required CH4 purity mole fraction")
    scalars["slipCH4_ABS"]  = sc(m, "slipCH4_ABS",  0.001,  "ABS CH4 slip fraction")
    scalars["etaCO2_ABS"]   = sc(m, "etaCO2_ABS",   0.985,  "ABS CO2 removal efficiency")
    scalars["e_el_ABS"]     = sc(m, "e_el_ABS",     0.12,   "ABS electricity use kWh/m3 gas")
    scalars["slipCH4_PSA"]  = sc(m, "slipCH4_PSA",  0.015,  "PSA CH4 slip fraction")
    scalars["etaCO2_PSA"]   = sc(m, "etaCO2_PSA",   0.97,   "PSA CO2 removal efficiency")
    scalars["e_el_PSA"]     = sc(m, "e_el_PSA",     0.25,   "PSA electricity use kWh/m3 gas")
 
    # ── Cost scalars ───────────────────────────────────────────────
    scalars["C_water"]           = sc(m, "C_water",           0.0053, "Water cost $/kg")
    scalars["C_enzyme"]          = sc(m, "C_enzyme",          2.00,   "Enzyme cost $/kg")
    scalars["C_amine"]           = sc(m, "C_amine",           2.50,   "Amine solution cost $/kg")
    scalars["C_pwt"]             = sc(m, "C_pwt",             0.00005,"Cooling water cost $/kg")
    scalars["C_disp_reject"]     = sc(m, "C_disp_reject",     0.055,  "Reject disposal cost $/kg")
    scalars["C_disp_aq"]         = sc(m, "C_disp_aq",         0.005,  "Aqueous phase disposal $/kg")
    scalars["C_disp_land"]       = sc(m, "C_disp_land",       0.055,  "Land disposal cost $/kg")
    scalars["C_disp_char"]       = sc(m, "C_disp_char",       0.055,  "Char disposal cost $/kg")
    scalars["C_disp_digestate"]  = sc(m, "C_disp_digestate",  0.005,  "Digestate disposal cost $/kg")
    scalars["r_wc"]              = sc(m, "r_wc",              0.15,   "Working capital fraction")
    scalars["r_ins"]             = sc(m, "r_ins",             0.01,   "Insurance fraction")
    scalars["amine_loss"]        = sc(m, "amine_loss",        0.01,   "Amine daily makeup fraction")
 
    # ── Cooling water ──────────────────────────────────────────────
    scalars["Cp_water"]     = sc(m, "Cp_water",     4.2,   "Cooling water heat capacity kJ/kg C")
    scalars["Tcw_out"]      = sc(m, "Tcw_out",      40.0,  "Cooling water outlet temperature C")
    scalars["Tcw_in"]       = sc(m, "Tcw_in",       20.0,  "Cooling water inlet temperature C")
    scalars["r_water_ABS"]  = sc(m, "r_water_ABS",  3.0,   "Water per kg CO2 absorbed ABS kg/kg")
    scalars["Eff_CNT"]      = sc(m, "Eff_CNT",      1.0,   "Centrifuge separation efficiency")
 
    return scalars
 
 
# ============================================================
# SECTION C — GHG EMISSION FACTORS
# ============================================================
def build_ghg_scalars(m: Container) -> dict:
    """Build all GHG emission factor scalars."""
    scalars = {}
 
    scalars["GWP_CH4"]           = sc(m, "GWP_CH4",           28.0,   "GWP of CH4 kg CO2-eq/kg")
    scalars["GWP_N2O"]           = sc(m, "GWP_N2O",           273.0,  "GWP of N2O kg CO2-eq/kg")
    scalars["EF_elec"]           = sc(m, "EF_elec",           0.386,  "Grid electricity EF kg CO2/kWh")
    scalars["EF_CH4_WWT"]        = sc(m, "EF_CH4_WWT",        0.01,   "WWT CH4 emission factor kg/kg VS")
    scalars["EF_N2O_WWT"]        = sc(m, "EF_N2O_WWT",        0.001,  "WWT N2O emission factor kg/kg VS")
    scalars["EF_HTLgas"]         = sc(m, "EF_HTLgas",         15.85,  "HTL gas combustion EF kg CO2/kg gas")
    scalars["EF_CH4_disp"]       = sc(m, "EF_CH4_disp",       2.75,   "CH4 displacement EF kg CO2/kg CH4")
    scalars["EF_BIOCRUDE_disp"]  = sc(m, "EF_BIOCRUDE_disp",  3.15,   "Biocrude displacement EF kg CO2/kg")
    scalars["EF_COMPOST_disp"]   = sc(m, "EF_COMPOST_disp",   -0.3,   "Compost displacement EF kg CO2/kg")
    scalars["EF_ELEC_disp"]      = sc(m, "EF_ELEC_disp",      0.386,  "Electricity displacement EF kg CO2/kWh")
    scalars["EF_AQ_disp"]        = sc(m, "EF_AQ_disp",        0.015,  "Aqueous phase disposal EF kg CO2/kg")
    scalars["EF_CHAR_disp"]      = sc(m, "EF_CHAR_disp",      0.005,  "Char disposal EF kg CO2/kg")
    scalars["EF_BIOSOLIDS_disp"] = sc(m, "EF_BIOSOLIDS_disp", 0.05,   "Biosolids displacement EF kg CO2/kg")
 
    return scalars
 
 
# ============================================================
# SECTION D — PARETO SCALARS
# ============================================================
def build_pareto_scalars(m: Container) -> dict:
    """Build Pareto optimization scalars."""
    scalars = {}
 
    scalars["w1"]           = sc(m, "w1",      1.0,  "NAC weight in objective")
    scalars["w2"]           = sc(m, "w2",      0.0,  "GHG weight in objective")
    scalars["NAC_min_sc"]   = sc(m, "NAC_min", 0.0,  "NAC minimum anchor")
    scalars["NAC_max_sc"]   = sc(m, "NAC_max", 1.0,  "NAC maximum anchor")
    scalars["GHG_min_sc"]   = sc(m, "GHG_min", 0.0,  "GHG minimum anchor")
    scalars["GHG_max_sc"]   = sc(m, "GHG_max", 1.0,  "GHG maximum anchor")
    scalars["eps_GHG"]      = sc(m, "eps_GHG", 1e8,  "GHG epsilon bound")
    scalars["SLF_min_area"] = sc(m, "SLF_min_area", 1.0, "Min landfill area acres")
    scalars["delta"]        = sc(m, "delta",   1e-6, "Augmented objective small penalty")
 
    return scalars
 
 
# ============================================================
# SECTION E — INDEXED PARAMETERS
# ============================================================
def build_indexed_parameters(m: Container, sets: dict,
                              composition: dict,
                              user_inputs: dict) -> dict:
    """
    Build all indexed Parameters.
 
    Parameters
    ----------
    m          : Container
    sets       : dict from build_sets()
    composition: dict from food_waste_database
    user_inputs: dict from app
 
    Returns
    -------
    dict of indexed Parameters
    """
    i    = sets["i"]
    k    = sets["k"]
    kp   = sets["kp"]
    p    = sets["p"]
    iConv   = sets["iConv"]
    i_mech  = sets["i_mech"]
    iHTLrec = sets["iHTLrec"]
    iGasUpg = sets["iGasUpg"]
 
    params = {}
 
    # ── Feed composition (wet basis) ───────────────────────────────
    Frac = Parameter(m, name="Frac", domain=k,
                     description="Feed composition wet basis fractions")
    Frac.setRecords([
        ("WATER",        composition.get("WATER",        0.75952)),
        ("CBH",          composition.get("CBH",          0.016745)),
        ("PRT",          composition.get("PRT",          0.108027)),
        ("FAT",          composition.get("FAT",          0.046492)),
        ("OTH",          composition.get("OTH",          0.020929)),
        ("ASH",          composition.get("ASH",          0.012427)),
        ("FIXED_CARBON", composition.get("FIXED_CARBON", 0.035360)),
    ])
    params["Frac"] = Frac
 
    # ── Equipment reference purchase cost ($) ──────────────────────
    C0 = Parameter(m, name="C0", domain=i,
                   description="Reference equipment purchase cost $")
    C0.setRecords([
        ("SHR",   111000), ("MCR",   111000), ("AER",   882000),
        ("ENZ",   882000), ("WWT",   882000), ("INC",  4700000),
        ("HTL",   645000), ("CMP",   786000), ("AND",   594000),
        ("SLF",   450000), ("CEN",    66000), ("FLT",    39000),
        ("ABS",    30000), ("PSA",    80000), ("STB",    45000),
    ])
    params["C0"] = C0
 
    # ── Reference capacity ─────────────────────────────────────────
    Q0 = Parameter(m, name="Q0", domain=i,
                   description="Reference capacity per technology")
    Q0.setRecords([
        ("SHR", 10000),  # kg/hr
        ("MCR", 60000),  # kg/hr
        ("AER", 15000),  # m3 vessel
        ("ENZ", 15000),  # m3 vessel
        ("WWT", 15000),  # m3 vessel
        ("INC",  8000),  # kg/hr
        ("HTL",    40),  # m3 vessel
        ("CMP",   350),  # m3 vessel
        ("AND",  1000),  # m3 vessel
        ("SLF",  0.15),  # acres
        ("CEN",  0.01),  # m3/hr sigma-factor
        ("FLT",    80),  # m3/hr filter proxy
        ("ABS",    32),  # m3/hr gas at STP
        ("PSA",    50),  # m3/hr gas at STP
        ("STB", 30000),  # kW
    ])
    params["Q0"] = Q0
 
    # ── Specific power (kW per unit capacity) ──────────────────────
    Wsp = Parameter(m, name="Wsp", domain=i,
                    description="Specific power kW per unit capacity")
    Wsp.setRecords([
        ("SHR", 0.05), ("MCR", 0.10), ("AER", 0.04), ("ENZ", 0.04),
        ("WWT", 0.04), ("INC", 0.05), ("HTL", 2.0),  ("CMP", 0.02),
        ("AND", 0.005),("SLF", 0.5),  ("CEN", 0.1),  ("FLT", 0.1),
        ("ABS", 0.1),  ("PSA", 0.4),  ("STB", 0.02),
    ])
    params["Wsp"] = Wsp
 
    # ── Labor scaling factor ───────────────────────────────────────
    Nlbr = Parameter(m, name="Nlbr", domain=i,
                     description="Labor scaling factor")
    Nlbr.setRecords([
        ("SHR", 0.1),  ("MCR", 0.1),  ("AER", 0.5),  ("ENZ", 0.5),
        ("WWT", 0.5),  ("INC", 1.0),  ("HTL", 2.0),  ("CMP", 0.5),
        ("AND", 0.02), ("SLF", 1.0),  ("CEN", 1.0),  ("FLT", 0.5),
        ("ABS", 0.01), ("PSA", 0.01), ("STB", 0.05),
    ])
    params["Nlbr"] = Nlbr
 
    # ── HTL product yield fractions ────────────────────────────────
    yHTL_p = Parameter(m, name="yHTL_p", domain=k,
                       description="HTL product yield fractions kg/kg organic")
    yHTL_p.setRecords([
        ("BIOCRUDE",      0.35),
        ("CHAR",          0.10),
        ("AQUEOUS_PHASE", 0.40),
        ("GAS_PRODUCT",   0.15),
    ])
    params["yHTL_p"] = yHTL_p
 
    # ── Biogas composition ─────────────────────────────────────────
    xBG = Parameter(m, name="xBG", domain=k,
                    description="Biogas composition mass fractions")
    xBG.setRecords([("CH4", 0.60), ("CO2", 0.40)])
    params["xBG"] = xBG
 
    # ── WWT removal fractions ──────────────────────────────────────
    rWW = Parameter(m, name="rWW", domain=k,
                    description="WWT component removal fractions")
    rWW.setRecords([
        ("CBH",          0.30),
        ("PRT",          0.30),
        ("FAT",          0.30),
        ("OTH",          0.30),
        ("WATER",        0.02),
        ("ASH",          1.00),
        ("FIXED_CARBON", 1.00),
    ])
    params["rWW"] = rWW
 
    # ── Filtration retention factor ────────────────────────────────
    RFLT = Parameter(m, name="RFLT", domain=k,
                     description="Filtration retention factors")
    RFLT.setRecords([
        ("BIOCRUDE",      0.05),
        ("CHAR",          0.98),
        ("AQUEOUS_PHASE", 0.10),
    ])
    params["RFLT"] = RFLT
 
    # ── Aerobic degradation fractions ──────────────────────────────
    fdegAER = Parameter(m, name="fdegAER", domain=k,
                        description="AER degradation fractions per component")
    fdegAER.setRecords([
        ("CBH", 0.40),
        ("PRT", 0.30),
        ("FAT", 0.15),
        ("OTH", 0.20),
    ])
    params["fdegAER"] = fdegAER
 
    # ── HTL product densities ──────────────────────────────────────
    Den = Parameter(m, name="Den", domain=k,
                    description="HTL product densities kg/m3")
    Den.setRecords([
        ("BIOCRUDE",      1200),
        ("CHAR",          1500),
        ("AQUEOUS_PHASE", 1000),
    ])
    params["Den"] = Den
 
    # ── Filter area factor ─────────────────────────────────────────
    Zeta = Parameter(m, name="Zeta", domain=i,
                     description="Filter area factor")
    Zeta.setRecords([("FLT", 0.2)])
    params["Zeta"] = Zeta
 
    # ── Product selling prices ─────────────────────────────────────
    Price_prod = Parameter(m, name="Price_prod", domain=kp,
                           description="Product selling prices $/kg or $/kWh")
    Price_prod.setRecords([
        ("CH4",         user_inputs.get("price_CH4",         0.185)),
        ("BIOCRUDE",    user_inputs.get("price_BIOCRUDE",    0.48)),
        ("COMPOST",     user_inputs.get("price_COMPOST",     0.068)),
        ("ELECTRICITY", user_inputs.get("price_ELECTRICITY", 0.10)),
        ("BIOSOLIDS",   user_inputs.get("price_BIOSOLIDS",   0.05)),
    ])
    params["Price_prod"] = Price_prod
 
    # ── Pareto result storage ──────────────────────────────────────
    GHG_eps_p    = Parameter(m, name="GHG_eps_p",   domain=p,
                             description="GHG epsilon bound per Pareto point")
    ParetoResult = Parameter(m, name="ParetoResult", domain=[p, "*"])
    ConvChoice   = Parameter(m, name="ConvChoice",   domain=[p, iConv])
    MechChoice   = Parameter(m, name="MechChoice",   domain=[p, i_mech])
    HTLRecChoice = Parameter(m, name="HTLRecChoice", domain=[p, iHTLrec])
    GasUpgChoice = Parameter(m, name="GasUpgChoice", domain=[p, iGasUpg])
 
    params["GHG_eps_p"]    = GHG_eps_p
    params["ParetoResult"] = ParetoResult
    params["ConvChoice"]   = ConvChoice
    params["MechChoice"]   = MechChoice
    params["HTLRecChoice"] = HTLRecChoice
    params["GasUpgChoice"] = GasUpgChoice
 
    return params
 
 
# ============================================================
# MAIN BUILDER — called by solver.py
# ============================================================
def build_all_parameters(m: Container, sets: dict,
                          user_inputs: dict) -> dict:
    """
    Build ALL scalars and indexed parameters.
    Returns merged dict of everything.
    """
    composition = user_inputs.get("composition", {
        "WATER": 0.75952, "CBH": 0.016745, "PRT": 0.108027,
        "FAT": 0.046492,  "OTH": 0.020929, "ASH": 0.012427,
        "FIXED_CARBON": 0.035360,
    })
 
    all_params = {}
    all_params.update(build_user_scalars(m, user_inputs))
    all_params.update(build_process_scalars(m))
    all_params.update(build_ghg_scalars(m))
    all_params.update(build_pareto_scalars(m))
    all_params.update(build_indexed_parameters(m, sets, composition, user_inputs))
 
    return all_params