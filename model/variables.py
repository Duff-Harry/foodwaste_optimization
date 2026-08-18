"""
model/variables.py
==================
Defines ALL GAMSPy variables and bounds for the food waste
optimization model.
 
Sections:
    A. Binary selection variables
    B. Mass flow variables
    C. Equipment sizing variables
    D. Technology intermediate variables (AER, ENZ, HTL, AND, SLF, CMP, WWT, INC, STB)
    E. Cost variables
    F. GHG variables
    G. Free / objective variables
    H. Bounds
"""
 
from gamspy import Container, Variable
 
 
# ============================================================
# MAIN BUILDER
# ============================================================
def build_variables(m: Container, sets: dict, params: dict) -> dict:
    """
    Build and return all variables for the optimization model.
 
    Parameters
    ----------
    m      : Container
    sets   : dict from build_sets()
    params : dict from build_all_parameters()
 
    Returns
    -------
    dict of all Variable objects
    """
 
    # Unpack sets needed for domains
    i       = sets["i"]
    j       = sets["j"]
    k       = sets["k"]
    kp      = sets["kp"]
    kgas    = sets["kgas"]
    kHTL    = sets["kHTL"]
    i_mech  = sets["i_mech"]
    i_bio   = sets["i_bio"]
    iConv   = sets["iConv"]
    iHTLrec = sets["iHTLrec"]
    iGasUpg = sets["iGasUpg"]
 
    vars = {}
 
    # ============================================================
    # SECTION A — BINARY SELECTION VARIABLES
    # ============================================================
 
    vars["yS1"] = Variable(
        m, name="yS1", domain=i_mech, type="binary",
    )  # Mechanical pretreatment selection (SHR or MCR)
 
    vars["yConv"] = Variable(
        m, name="yConv", domain=iConv, type="binary",
    )  # Conversion technology selection
 
    vars["yHTLrec"] = Variable(
        m, name="yHTLrec", domain=iHTLrec, type="binary",
    )  # HTL recovery technology selection (CEN or FLT)
 
    vars["yGasUpg"] = Variable(
        m, name="yGasUpg", domain=iGasUpg, type="binary",
    )  # Gas upgrading technology selection (ABS or PSA)
 
    vars["ySTB"] = Variable(
        m, name="ySTB", type="binary",
    )  # Steam turbine selection (active when INC selected)
 
    vars["yBio"] = Variable(
        m, name="yBio", domain=i_bio, type="binary",
    )  # Biological pretreatment selection (AER or ENZ)
 
    vars["yBYP1"] = Variable(
        m, name="yBYP1", type="binary",
    )  # Left bypass — skips mechanical + biological pretreatment
 
    vars["yBYP2"] = Variable(
        m, name="yBYP2", type="binary",
    )  # Right bypass — skips ALL pretreatment (direct to conversion)
 
    vars["yBYP_bio"] = Variable(
        m, name="yBYP_bio", type="binary",
    )  # Bypass biological stage (Splitter 2 → Mixer 2 direct)
 
    # ============================================================
    # SECTION B — MASS FLOW VARIABLES
    # ============================================================
 
    vars["M_var"] = Variable(
        m, name="M_var", domain=[j, k], type="positive",
    )  # Mass flow of component k in stream j (kg/hr)
 
    vars["F2"] = Variable(
        m, name="F2", domain=[iConv, k], type="positive",
    )  # Feed to conversion technology (kg/hr)
 
    vars["F_HTLrec"] = Variable(
        m, name="F_HTLrec", domain=[iHTLrec, kHTL], type="positive",
    )  # HTL product recovery flows (kg/hr)
 
    vars["F_GasUpg"] = Variable(
        m, name="F_GasUpg", domain=[iGasUpg, kgas], type="positive",
    )  # Gas upgrading flows (kg/hr)
 
    # ============================================================
    # SECTION C — EQUIPMENT SIZING VARIABLES
    # ============================================================
 
    vars["W_total"] = Variable(
        m, name="W_total", type="positive",
    )  # Total electricity consumption (kW)
 
    vars["Qc"] = Variable(
        m, name="Qc", domain=i, type="positive",
    )  # Equipment capacity (units depend on technology)
 
    vars["PurchaseCost"] = Variable(
        m, name="PurchaseCost", domain=i, type="positive",
    )  # Equipment purchase cost ($)
 
    vars["Nlabr_new"] = Variable(
        m, name="Nlabr_new", domain=i, type="positive",
    )  # Number of labor units per technology
 
    vars["PW"] = Variable(
        m, name="PW", domain=i, type="positive",
    )  # Power consumption per technology (kW)
 
    vars["Mstm"] = Variable(
        m, name="Mstm", domain=i, type="positive",
    )  # Steam consumption per technology (kg/hr)
 
    vars["Mcw"] = Variable(
        m, name="Mcw", domain=i, type="positive",
    )  # Cooling water consumption per technology (kg/hr)
 
    vars["Mprod"] = Variable(
        m, name="Mprod", domain=[i, kp], type="positive",
    )  # Product output per technology (kg/hr or kWh/hr)
 
    vars["CF"] = Variable(
        m, name="CF", domain=i, type="positive",
    )  # Concentration factor (CEN, FLT)
 
    vars["U"] = Variable(
        m, name="U", domain=i, type="positive",
    )  # Sigma factor for centrifuge sizing
 
    # ============================================================
    # SECTION D — TECHNOLOGY INTERMEDIATE VARIABLES
    # ============================================================
 
    # ── AER (Aerobic biodigester) ──────────────────────────────────
    vars["VS_AER_deg"]   = Variable(m, name="VS_AER_deg",   type="positive")  # VS degraded in AER (kg/hr)
    vars["V_w_AER"]      = Variable(m, name="V_w_AER",      type="positive")  # Working volume AER (m3)
    vars["V_vessel_AER"] = Variable(m, name="V_vessel_AER", type="positive")  # Vessel volume AER (m3)
 
    # ── ENZ (Enzymatic hydrolysis) ─────────────────────────────────
    vars["V_ENZ"]     = Variable(m, name="V_ENZ",     type="positive")  # ENZ vessel volume (m3)
    vars["ENZ_DS_in"] = Variable(m, name="ENZ_DS_in", type="positive")  # Dry solids entering ENZ (kg/hr)
 
    # ── HTL (Hydrothermal liquefaction) ────────────────────────────
    vars["Morg_HTL"]     = Variable(m, name="Morg_HTL",     type="positive")  # Organic feed HTL (kg/hr)
    vars["Mslurry17"]    = Variable(m, name="Mslurry17",    type="positive")  # HTL slurry stream 17 (kg/hr)
    vars["Mslurry22"]    = Variable(m, name="Mslurry22",    type="positive")  # HTL product slurry stream 22 (kg/hr)
    vars["mHTL_heated"]  = Variable(m, name="mHTL_heated",  type="positive")  # Mass heated in HTL (kg/hr)
    vars["Qnet_HTL"]     = Variable(m, name="Qnet_HTL",     type="positive")  # Net heat duty HTL (kJ/hr)
    vars["Qgas_HTL"]     = Variable(m, name="Qgas_HTL",     type="positive")  # Heat from HTL gas combustion (kJ/hr)
    vars["V_w_HTL"]      = Variable(m, name="V_w_HTL",      type="positive")  # Working volume HTL (m3)
    vars["V_vessel_HTL"] = Variable(m, name="V_vessel_HTL", type="positive")  # Vessel volume HTL (m3)
 
    # ── AND (Anaerobic digestion) ───────────────────────────────────
    vars["VSANDin"]      = Variable(m, name="VSANDin",      type="positive")  # VS entering AND (kg/hr)
    vars["CH4gen"]       = Variable(m, name="CH4gen",       type="positive")  # CH4 generated AND (kg/hr)
    vars["CO2gen"]       = Variable(m, name="CO2gen",       type="positive")  # CO2 generated AND (kg/hr)
    vars["V_w_AND"]      = Variable(m, name="V_w_AND",      type="positive")  # Working volume AND (m3)
    vars["V_vessel_AND"] = Variable(m, name="V_vessel_AND", type="positive")  # Vessel volume AND (m3)
 
    # ── SLF (Sanitary landfill) ────────────────────────────────────
    vars["CH4_mass_SLF"]    = Variable(m, name="CH4_mass_SLF",    type="positive")  # CH4 generated SLF (kg/hr)
    vars["CO2_mass_SLF"]    = Variable(m, name="CO2_mass_SLF",    type="positive")  # CO2 generated SLF (kg/hr)
    vars["CH4_volume_SLF"]  = Variable(m, name="CH4_volume_SLF",  type="positive")  # CH4 volume SLF (m3/hr)
    vars["m_wasteleft_SLF"] = Variable(m, name="m_wasteleft_SLF", type="positive")  # Waste remaining SLF (kg/hr)
    vars["vol_FW_SLF"]      = Variable(m, name="vol_FW_SLF",      type="positive")  # Volume of waste SLF (m3)
    vars["CH4_ox_SLF"]      = Variable(m, name="CH4_ox_SLF",      type="positive")  # CH4 oxidized SLF (kg/hr)
 
    # ── CMP (Composting) ───────────────────────────────────────────
    vars["VSCMP_in"]     = Variable(m, name="VSCMP_in",     type="positive")  # VS entering CMP (kg/hr)
    vars["VSCMP_deg"]    = Variable(m, name="VSCMP_deg",    type="positive")  # VS degraded CMP (kg/hr)
    vars["O2req_CMP"]    = Variable(m, name="O2req_CMP",    type="positive")  # O2 demand CMP (kg/hr)
    vars["AirCMP"]       = Variable(m, name="AirCMP",       type="positive")  # Air supply CMP (kg/hr)
    vars["V_work_CMP"]   = Variable(m, name="V_work_CMP",   type="positive")  # Working volume CMP (m3)
    vars["V_vessel_CMP"] = Variable(m, name="V_vessel_CMP", type="positive")  # Vessel volume CMP (m3)
 
    # ── WWT (Wastewater treatment) ─────────────────────────────────
    vars["Qww_m3ph"]        = Variable(m, name="Qww_m3ph",        type="positive")  # Volumetric flow WWT (m3/hr)
    vars["mVS_in"]          = Variable(m, name="mVS_in",          type="positive")  # VS entering WWT (kg/hr)
    vars["mVS_deg_WWT"]     = Variable(m, name="mVS_deg_WWT",     type="positive")  # VS degraded WWT (kg/hr)
    vars["Px"]              = Variable(m, name="Px",              type="positive")  # Net biosolids yield WWT (kg/hr)
    vars["m_wasteleft_WWT"] = Variable(m, name="m_wasteleft_WWT", type="positive")  # WWT effluent (kg/hr)
 
    # ── INC (Incineration) ─────────────────────────────────────────
    vars["mdry_inc"]  = Variable(m, name="mdry_inc",  type="positive")  # Dry feed INC (kg/hr)
    vars["mdaf_inc"]  = Variable(m, name="mdaf_inc",  type="positive")  # Ash-free dry feed INC (kg/hr)
    vars["nC_inc"]    = Variable(m, name="nC_inc",    type="positive")  # C molar flow INC (kmol/hr)
    vars["nH_inc"]    = Variable(m, name="nH_inc",    type="positive")  # H molar flow INC (kmol/hr)
    vars["nO_inc"]    = Variable(m, name="nO_inc",    type="positive")  # O molar flow INC (kmol/hr)
    vars["nN_inc"]    = Variable(m, name="nN_inc",    type="positive")  # N molar flow INC (kmol/hr)
    vars["nS_inc"]    = Variable(m, name="nS_inc",    type="positive")  # S molar flow INC (kmol/hr)
    vars["nO2_sto"]   = Variable(m, name="nO2_sto",   type="positive")  # Stoichiometric O2 INC (kmol/hr)
    vars["nO2_in"]    = Variable(m, name="nO2_in",    type="positive")  # Actual O2 input INC (kmol/hr)
    vars["nN2_air"]   = Variable(m, name="nN2_air",   type="positive")  # N2 from air INC (kmol/hr)
    vars["nCO2_inc"]  = Variable(m, name="nCO2_inc",  type="positive")  # CO2 produced INC (kmol/hr)
    vars["nH2O_inc"]  = Variable(m, name="nH2O_inc",  type="positive")  # H2O produced INC (kmol/hr)
    vars["nSO2_inc"]  = Variable(m, name="nSO2_inc",  type="positive")  # SO2 produced INC (kmol/hr)
    vars["nO2_out"]   = Variable(m, name="nO2_out",   type="positive")  # Excess O2 INC (kmol/hr)
    vars["nN2_out"]   = Variable(m, name="nN2_out",   type="positive")  # N2 out INC (kmol/hr)
    vars["mflue_inc"] = Variable(m, name="mflue_inc", type="positive")  # Total flue gas INC (kg/hr)
    vars["m_ash_INC"] = Variable(m, name="m_ash_INC", type="positive")  # Ash from INC (kg/hr)
 
    # ── STB (Steam turbine) ────────────────────────────────────────
    vars["P_turbine"] = Variable(m, name="P_turbine", type="positive")  # Turbine power output (kW)
 
    # ============================================================
    # SECTION E — COST VARIABLES
    # ============================================================
 
    vars["CCAC"]  = Variable(m, name="CCAC",  type="positive")  # Annualized capital cost (M$/yr)
    vars["CCWC"]  = Variable(m, name="CCWC",  type="positive")  # Working capital cost (M$/yr)
    vars["CCINS"] = Variable(m, name="CCINS", type="positive")  # Insurance cost (M$/yr)
    vars["CCLB"]  = Variable(m, name="CCLB",  type="positive")  # Labor cost (M$/yr)
    vars["CCUC"]  = Variable(m, name="CCUC",  type="positive")  # Utility cost (M$/yr)
    vars["CCOC"]  = Variable(m, name="CCOC",  type="positive")  # Overhead cost (M$/yr)
    vars["CCRM"]  = Variable(m, name="CCRM",  type="positive")  # Raw material cost (M$/yr)
    vars["CDISP"] = Variable(m, name="CDISP", type="positive")  # Disposal cost (M$/yr)
    vars["CTIP"]  = Variable(m, name="CTIP",  type="positive")  # Tipping fee revenue (M$/yr)
    vars["CCTC"]  = Variable(m, name="CCTC",  type="positive")  # Total annual cost (M$/yr)
    vars["REV"]   = Variable(m, name="REV",   type="positive")  # Total revenue (M$/yr)
 
    # ============================================================
    # SECTION F — GHG VARIABLES
    # ============================================================
 
    vars["GHG_ind_kgph"]  = Variable(m, name="GHG_ind_kgph",  type="positive")  # Indirect GHG kg/hr
    vars["GHG_ind_kgyr"]  = Variable(m, name="GHG_ind_kgyr",  type="positive")  # Indirect GHG kg/yr
    vars["GHG_ind_tpy"]   = Variable(m, name="GHG_ind_tpy",   type="positive")  # Indirect GHG t/yr
    vars["GHG_dir"]       = Variable(m, name="GHG_dir",        domain=i, type="positive")  # Direct GHG per technology t/yr
    vars["GHG_dir_total"] = Variable(m, name="GHG_dir_total",  type="positive")  # Total direct GHG t/yr
    vars["GHG_disp"]      = Variable(m, name="GHG_disp",       type="free")      # Displacement credits t/yr
    vars["GHG_aq"]        = Variable(m, name="GHG_aq",         type="free")      # Aqueous/char disposal GHG t/yr
 
    # ============================================================
    # SECTION G — FREE / OBJECTIVE VARIABLES
    # ============================================================
 
    vars["NAC"]           = Variable(m, name="NAC",           type="free")  # Net annual cost (M$/yr)
    vars["GHG_total_tpy"] = Variable(m, name="GHG_total_tpy", type="free")  # Total GHG (t CO2-eq/yr)
    vars["ZCOST"]         = Variable(m, name="ZCOST",         type="free")  # Cost objective
    vars["ZGHG"]          = Variable(m, name="ZGHG",          type="free")  # GHG objective
    vars["obj"]           = Variable(m, name="obj",           type="free")  # Augmented objective
 
    # ============================================================
    # SECTION H — BOUNDS
    # ============================================================
    _set_bounds(vars, params)
 
    return vars
 
 
def _set_bounds(vars: dict, params: dict):
    """Set all variable bounds."""
 
    Qf   = params["Qf"]
    Tann = params["Tann"]
 
    # Concentration factor bounds
    vars["CF"].lo["FLT"] = 2.0
    vars["CF"].up["FLT"] = 30.0
    vars["CF"].lo["CEN"] = 1.001
    vars["CF"].up["CEN"] = 100.0
 
    # Vessel volume bounds
    vars["V_vessel_AER"].up = 2000.0
    vars["V_ENZ"].up        = 500.0
    vars["Qc"].up["AER"]    = 2000.0
    vars["Qc"].up["ENZ"]    = 500.0
 
    # Biosolids upper bound
    vars["Px"].up = Qf.toValue() * Tann.toValue()
 
    # NAC bounds
    vars["NAC"].lo = -10.0
    vars["NAC"].up = 100.0
 
    # GHG bounds
    vars["GHG_total_tpy"].lo = -50000.0
    vars["GHG_total_tpy"].up = 100000.0
 
    # Steam lower bound (prevent negative steam)
    vars["Mstm"].lo["HTL"] = 0.0