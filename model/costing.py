"""
model/costing.py
================
All costing equations and feasibility constraints for the
food waste optimization model.

Sections:
    A. Capital costs (purchase, annualized, working capital, insurance)
    B. Operating costs (labor, utilities, overhead, raw materials, disposal)
    C. Revenue (products + tipping fee)
    D. Total and net annual cost
    E. Feasibility constraints (infeasible technology paths blocked)
"""

from gamspy import Container, Equation, Sum


def build_costing(m: Container, sets: dict,
                  params: dict, vars: dict) -> dict:
    """
    Build all costing equations and feasibility constraints.

    Parameters
    ----------
    m      : Container
    sets   : dict from build_sets()
    params : dict from build_all_parameters()
    vars   : dict from build_variables()

    Returns
    -------
    dict of all Equation objects
    """

    # ── Unpack sets ──────────────────────────────────────────────────
    i     = sets["i"]
    k     = sets["k"]
    kp    = sets["kp"]
    iConv = sets["iConv"]
    i_mech = sets["i_mech"]
    i_bio  = sets["i_bio"]

    # ── Unpack parameters ────────────────────────────────────────────
    C0         = params["C0"]
    Q0         = params["Q0"]
    Nlbr       = params["Nlbr"]
    Price_prod = params["Price_prod"]
    Qf         = params["Qf"]
    CRF        = params["CRF"]
    BMC_mult   = params["BMC_mult"]
    nc         = params["nc"]
    r_wc       = params["r_wc"]
    r_ins      = params["r_ins"]
    C_lbr      = params["C_lbr"]
    Tann       = params["Tann"]
    C_elec     = params["C_elec"]
    C_stm      = params["C_stm"]
    C_pwt      = params["C_pwt"]
    C_water    = params["C_water"]
    C_enzyme   = params["C_enzyme"]
    C_amine    = params["C_amine"]
    amine_loss = params["amine_loss"]
    C_tip      = params["C_tip"]
    C_disp_reject    = params["C_disp_reject"]
    C_disp_char      = params["C_disp_char"]
    C_disp_aq        = params["C_disp_aq"]
    C_disp_digestate = params["C_disp_digestate"]
    C_disp_land      = params["C_disp_land"]

    # ── Unpack variables ─────────────────────────────────────────────
    M_var        = vars["M_var"]
    Qc           = vars["Qc"]
    PW           = vars["PW"]
    Mstm         = vars["Mstm"]
    Mcw          = vars["Mcw"]
    Mprod        = vars["Mprod"]
    PurchaseCost = vars["PurchaseCost"]
    Nlabr_new    = vars["Nlabr_new"]
    Px           = vars["Px"]
    m_wasteleft_SLF = vars["m_wasteleft_SLF"]
    m_wasteleft_WWT = vars["m_wasteleft_WWT"]
    m_ash_INC    = vars["m_ash_INC"]
    CCAC         = vars["CCAC"]
    CCWC         = vars["CCWC"]
    CCINS        = vars["CCINS"]
    CCLB         = vars["CCLB"]
    CCUC         = vars["CCUC"]
    CCOC         = vars["CCOC"]
    CCRM         = vars["CCRM"]
    CDISP        = vars["CDISP"]
    CTIP         = vars["CTIP"]
    CCTC         = vars["CCTC"]
    REV          = vars["REV"]
    NAC          = vars["NAC"]
    yS1          = vars["yS1"]
    yConv        = vars["yConv"]
    yBio         = vars["yBio"]
    yBYP1        = vars["yBYP1"]
    yBYP2        = vars["yBYP2"]
    yBYP_bio     = vars["yBYP_bio"]

    eqs = {}

    # ================================================================
    # SECTION A — CAPITAL COSTS
    # ================================================================

    # ── Equipment purchase cost (6/10ths scaling rule) ──────────────
    eqs["Capital_eq"] = Equation(m, name="Capital_eq", domain=i)
    eqs["Capital_eq"][i] = PurchaseCost[i] == C0[i] * (Qc[i] / Q0[i]) ** nc

    # ── Annualized capital cost ──────────────────────────────────────
    eqs["ACC_eq"] = Equation(m, name="ACC_eq")
    eqs["ACC_eq"][...] = CCAC == (1.66 * CRF * BMC_mult * Sum(i, PurchaseCost[i])) / 1e6

    # ── Working capital (annualized via CRF) ─────────────────────────
    eqs["WC_eq"] = Equation(m, name="WC_eq")
    eqs["WC_eq"][...] = CCWC == (r_wc * CRF * BMC_mult * Sum(i, PurchaseCost[i])) / 1e6

    # ── Insurance + property tax ─────────────────────────────────────
    eqs["INS_eq"] = Equation(m, name="INS_eq")
    eqs["INS_eq"][...] = CCINS == (r_ins * BMC_mult * Sum(i, PurchaseCost[i])) / 1e6

    # ================================================================
    # SECTION B — OPERATING COSTS
    # ================================================================

    # ── Labor cost ───────────────────────────────────────────────────
    eqs["Labor_units_eq"] = Equation(m, name="Labor_units_eq", domain=i)
    eqs["Labor_units_eq"][i] = Nlabr_new[i] * Q0[i] == Nlbr[i] * Qc[i]

    eqs["Labor_eq"] = Equation(m, name="Labor_eq")
    eqs["Labor_eq"][...] = CCLB == (Sum(i, Nlabr_new[i]) * C_lbr * Tann) / 1e6

    # ── Utility cost (electricity + steam + cooling water) ───────────
    eqs["Utility_eq"] = Equation(m, name="Utility_eq")
    eqs["Utility_eq"][...] = CCUC == (Tann / 1e6) * (
          Sum(i, PW[i])   * C_elec
        + Sum(i, Mstm[i]) * C_stm
        + Sum(i, Mcw[i])  * C_pwt)

    # ── Overhead cost (tied to labor) ─────────────────────────────────
    eqs["Overhead_eq"] = Equation(m, name="Overhead_eq")
    eqs["Overhead_eq"][...] = CCOC == 2.78 * CCLB

    # ── Raw material cost ─────────────────────────────────────────────
    # Water: AER (stream 13), HTL (stream 21), AND (stream 24), STB (stream 59)
    # Enzyme: ENZ (stream 15)
    # Amine: ABS scrubbing solution (1% daily makeup of stream 50)
    eqs["CCRM_eq"] = Equation(m, name="CCRM_eq")
    eqs["CCRM_eq"][...] = CCRM == (Tann / 1e6) * (
          C_water  * (M_var["13", "WATER"] +
                      M_var["21", "WATER"] +
                      M_var["24", "WATER"] +
                      M_var["59", "WATER"])
        + C_enzyme * M_var["15", "ENZYME"]
        + C_amine  * amine_loss * M_var["50", "WATER"])

    # ── Disposal cost ─────────────────────────────────────────────────
    # Stream 5  = SHR reject
    # Stream 42 = CEN cake (CHAR)
    # Stream 45 = FLT retentate (CHAR + AQUEOUS)
    # Stream 26 = AND digestate
    # m_wasteleft_SLF = landfill waste remaining
    # m_wasteleft_WWT = WWT effluent
    # m_ash_INC = INC ash residue
    # Stream 50 = ABS effluent water
    eqs["Disposal_eq"] = Equation(m, name="Disposal_eq")
    eqs["Disposal_eq"][...] = CDISP == (Tann / 1e6) * (
          C_disp_reject    * Sum(k, M_var["5", k])
        + C_disp_char      * (M_var["42", "CHAR"] + M_var["45", "CHAR"])
        + C_disp_aq        * (M_var["42", "AQUEOUS_PHASE"] + M_var["45", "AQUEOUS_PHASE"])
        + C_disp_digestate * Sum(k, M_var["26", k])
        + C_disp_land      * m_wasteleft_SLF
        + C_disp_land      * m_wasteleft_WWT
        + C_disp_land      * m_ash_INC
        + C_disp_aq        * M_var["50", "WATER"])

    # ── Tipping fee ───────────────────────────────────────────────────
    eqs["Tipping_eq"] = Equation(m, name="Tipping_eq")
    eqs["Tipping_eq"][...] = CTIP == (C_tip * Qf * Tann) / 1e6

    # ================================================================
    # SECTION C — REVENUE
    # ================================================================

    # Products: CH4 (stream 56), biocrude (stream 47), compost (CMP),
    #           biosolids (WWT), electricity (STB stream 57)
    # Plus tipping fee
    eqs["Revenue_eq"] = Equation(m, name="Revenue_eq")
    eqs["Revenue_eq"][...] = REV == (Tann / 1e6) * (
          Price_prod["CH4"]         * M_var["56", "CH4"]
        + Price_prod["BIOCRUDE"]    * M_var["47", "BIOCRUDE"]
        + Price_prod["COMPOST"]     * Mprod["CMP", "COMPOST"]
        + Price_prod["BIOSOLIDS"]   * Px
        + Price_prod["ELECTRICITY"] * Qc["STB"]
    ) + CTIP

    # ================================================================
    # SECTION D — TOTAL AND NET ANNUAL COST
    # ================================================================

    # ── Total annual cost ─────────────────────────────────────────────
    eqs["Total_eq"] = Equation(m, name="Total_eq")
    eqs["Total_eq"][...] = CCTC == (CCAC + CCWC + CCINS +
                                     CCUC + CCLB + CCOC +
                                     CCRM + CDISP)

    # ── Net annual cost (objective 1) ─────────────────────────────────
    eqs["NetCost_eq"] = Equation(m, name="NetCost_eq")
    eqs["NetCost_eq"][...] = NAC == CCTC - REV

    # ================================================================
    # SECTION E — FEASIBILITY CONSTRAINTS
    # Technology path restrictions based on process compatibility
    # ================================================================

    # ── HTL: must skip bio pretreatment, must have mechanical ────────
    eqs["HTL_skip_bio"] = Equation(m, name="HTL_skip_bio")
    eqs["HTL_skip_bio"][...] = yConv["HTL"] <= yBYP_bio + yBYP2

    eqs["HTL_needs_mech"] = Equation(m, name="HTL_needs_mech")
    eqs["HTL_needs_mech"][...] = yConv["HTL"] <= yS1["SHR"] + yS1["MCR"]

    # ── AND: no AER, must have mechanical pretreatment ────────────────
    eqs["AND_no_AER"] = Equation(m, name="AND_no_AER")
    eqs["AND_no_AER"][...] = yConv["AND"] + yBio["AER"] <= 1

    eqs["AND_needs_mech"] = Equation(m, name="AND_needs_mech")
    eqs["AND_needs_mech"][...] = yConv["AND"] <= yS1["SHR"] + yS1["MCR"]

    # ── CMP: SHR + BYP_bio only (no MCR, no AER, no ENZ) ─────────────
    eqs["CMP_skip_bio"] = Equation(m, name="CMP_skip_bio")
    eqs["CMP_skip_bio"][...] = yConv["CMP"] <= yBYP_bio

    eqs["CMP_no_AER"] = Equation(m, name="CMP_no_AER")
    eqs["CMP_no_AER"][...] = yConv["CMP"] + yBio["AER"] <= 1

    eqs["CMP_no_ENZ"] = Equation(m, name="CMP_no_ENZ")
    eqs["CMP_no_ENZ"][...] = yConv["CMP"] + yBio["ENZ"] <= 1

    eqs["CMP_no_MCR"] = Equation(m, name="CMP_no_MCR")
    eqs["CMP_no_MCR"][...] = yConv["CMP"] + yS1["MCR"] <= 1

    # ── SLF: BYP2 only — no pretreatment ─────────────────────────────
    eqs["SLF_only_BYP2"] = Equation(m, name="SLF_only_BYP2")
    eqs["SLF_only_BYP2"][...] = yConv["SLF"] <= yBYP2

    # ── INC: BYP2 only — no pretreatment ─────────────────────────────
    eqs["INC_only_BYP2"] = Equation(m, name="INC_only_BYP2")
    eqs["INC_only_BYP2"][...] = yConv["INC"] <= yBYP2

    # ── WWT: must pass through AER (not BYP2) ────────────────────────
    eqs["WWT_no_BYP2"] = Equation(m, name="WWT_no_BYP2")
    eqs["WWT_no_BYP2"][...] = yConv["WWT"] + yBYP2 <= 1

    return eqs
