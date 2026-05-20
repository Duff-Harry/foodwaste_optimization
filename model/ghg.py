"""
model/ghg.py
============
All GHG (greenhouse gas) emission equations for the
food waste optimization model.
 
Sections:
    A. Indirect GHG — electricity consumption
    B. Direct GHG — per technology emissions
    C. Displacement credits — products offsetting fossil fuels
    D. Aqueous, char and digestate disposal GHG
    E. Total GHG equation
"""
 
from gamspy import Container, Equation, Sum
 
 
def build_ghg(m: Container, sets: dict,
              params: dict, vars: dict) -> dict:
    """
    Build all GHG equations.
 
    Parameters
    ----------
    m      : Container
    sets   : dict from build_sets()
    params : dict from build_all_parameters()
    vars   : dict from build_variables()
 
    Returns
    -------
    dict of all GHG Equation objects
    """
 
    # ── Unpack sets ──────────────────────────────────────────────────
    i  = sets["i"]
    k  = sets["k"]
 
    # ── Unpack parameters ────────────────────────────────────────────
    Tann             = params["Tann"]
    EF_elec          = params["EF_elec"]
    GWP_CH4          = params["GWP_CH4"]
    GWP_N2O          = params["GWP_N2O"]
    EF_HTLgas        = params["EF_HTLgas"]
    EF_CH4_disp      = params["EF_CH4_disp"]
    EF_BIOCRUDE_disp = params["EF_BIOCRUDE_disp"]
    EF_COMPOST_disp  = params["EF_COMPOST_disp"]
    EF_BIOSOLIDS_disp= params["EF_BIOSOLIDS_disp"]
    EF_ELEC_disp     = params["EF_ELEC_disp"]
    EF_AQ_disp       = params["EF_AQ_disp"]
    EF_CHAR_disp     = params["EF_CHAR_disp"]
 
    # ── Unpack variables ─────────────────────────────────────────────
    M_var         = vars["M_var"]
    PW            = vars["PW"]
    Qc            = vars["Qc"]
    Mprod         = vars["Mprod"]
    Px            = vars["Px"]
    GHG_ind_kgph  = vars["GHG_ind_kgph"]
    GHG_ind_kgyr  = vars["GHG_ind_kgyr"]
    GHG_ind_tpy   = vars["GHG_ind_tpy"]
    GHG_dir       = vars["GHG_dir"]
    GHG_dir_total = vars["GHG_dir_total"]
    GHG_disp      = vars["GHG_disp"]
    GHG_aq        = vars["GHG_aq"]
    GHG_total_tpy = vars["GHG_total_tpy"]
 
    eqs = {}
 
    # ================================================================
    # SECTION A — INDIRECT GHG (electricity consumption)
    # ================================================================
 
    eqs["GHG_ind_ph_eq"] = Equation(m, name="GHG_ind_ph_eq")
    eqs["GHG_ind_ph_eq"][...] = GHG_ind_kgph == EF_elec * Sum(i, PW[i])
 
    eqs["GHG_ind_yr_eq"] = Equation(m, name="GHG_ind_yr_eq")
    eqs["GHG_ind_yr_eq"][...] = GHG_ind_kgyr == Tann * GHG_ind_kgph
 
    eqs["GHG_ind_tpy_eq"] = Equation(m, name="GHG_ind_tpy_eq")
    eqs["GHG_ind_tpy_eq"][...] = GHG_ind_tpy == GHG_ind_kgyr / 1000
 
    # ================================================================
    # SECTION B — DIRECT GHG PER TECHNOLOGY
    # ================================================================
 
    # ── AER — biogenic CO2 only → carbon neutral → zero ──────────────
    eqs["GHG_AER_eq"] = Equation(m, name="GHG_AER_eq")
    eqs["GHG_AER_eq"][...] = GHG_dir["AER"] == 0
 
    # ── ENZ — no emissions ────────────────────────────────────────────
    eqs["GHG_ENZ_eq"] = Equation(m, name="GHG_ENZ_eq")
    eqs["GHG_ENZ_eq"][...] = GHG_dir["ENZ"] == 0
 
    # ── HTL — gas product combusted (stream 20) ───────────────────────
    eqs["GHG_HTL_eq"] = Equation(m, name="GHG_HTL_eq")
    eqs["GHG_HTL_eq"][...] = (GHG_dir["HTL"] ==
                              (Tann / 1000) * EF_HTLgas * M_var["20", "GAS_PRODUCT"])
 
    # ── AND — uncaptured CH4 offgas (stream 25) ───────────────────────
    # CO2 is biogenic → excluded
    eqs["GHG_AND_eq"] = Equation(m, name="GHG_AND_eq")
    eqs["GHG_AND_eq"][...] = (GHG_dir["AND"] ==
                              (Tann / 1000) * GWP_CH4 * M_var["25", "CH4"])
 
    # ── SLF — uncaptured LFG CH4 (stream 29) ─────────────────────────
    # CO2 is biogenic → excluded
    eqs["GHG_SLF_eq"] = Equation(m, name="GHG_SLF_eq")
    eqs["GHG_SLF_eq"][...] = (GHG_dir["SLF"] ==
                              (Tann / 1000) * GWP_CH4 * M_var["29", "CH4"])
 
    # ── CMP — process CH4 and N2O (stream 32) ────────────────────────
    # CO2 is biogenic → excluded
    eqs["GHG_CMP_eq"] = Equation(m, name="GHG_CMP_eq")
    eqs["GHG_CMP_eq"][...] = (GHG_dir["CMP"] ==
                              (Tann / 1000) * (
                                  GWP_CH4 * M_var["32", "CH4"] +
                                  GWP_N2O * M_var["32", "N2O"]))
 
    # ── WWT — process CH4 and N2O (stream 36) ────────────────────────
    # CO2 is biogenic → excluded
    eqs["GHG_WWT_eq"] = Equation(m, name="GHG_WWT_eq")
    eqs["GHG_WWT_eq"][...] = (GHG_dir["WWT"] ==
                              (Tann / 1000) * (
                                  GWP_CH4 * M_var["36", "CH4"] +
                                  GWP_N2O * M_var["36", "N2O"]))
 
    # ── INC — fugitive CH4 and N2O (stream 39) ───────────────────────
    # Flue CO2 is biogenic → excluded
    eqs["GHG_INC_eq"] = Equation(m, name="GHG_INC_eq")
    eqs["GHG_INC_eq"][...] = (GHG_dir["INC"] ==
                              (Tann / 1000) * (
                                  GWP_CH4 * M_var["39", "CH4"] +
                                  GWP_N2O * M_var["39", "N2O"]))
 
    # ── Zero out GHG for non-emitting technologies ────────────────────
    eqs["GHG_dir_zero"] = Equation(m, name="GHG_dir_zero", domain=i)
    eqs["GHG_dir_zero"][i].where[
        ~i.sameAs("AER") & ~i.sameAs("ENZ") &
        ~i.sameAs("HTL") & ~i.sameAs("AND") &
        ~i.sameAs("SLF") & ~i.sameAs("CMP") &
        ~i.sameAs("WWT") & ~i.sameAs("INC")
    ] = GHG_dir[i] == 0
 
    # ── Total direct GHG ──────────────────────────────────────────────
    eqs["GHG_dir_total_eq"] = Equation(m, name="GHG_dir_total_eq")
    eqs["GHG_dir_total_eq"][...] = GHG_dir_total == Sum(i, GHG_dir[i])
 
    # ================================================================
    # SECTION C — DISPLACEMENT CREDITS
    # Products offsetting fossil fuel equivalents
    # ================================================================
 
    # CH4 displaces natural gas
    # Biocrude displaces petroleum
    # Compost displaces synthetic fertilizer (negative credit)
    # Biosolids displaces synthetic fertilizer
    # Electricity displaces grid power
    eqs["GHG_disp_eq"] = Equation(m, name="GHG_disp_eq")
    eqs["GHG_disp_eq"][...] = GHG_disp == (Tann / 1000) * (
          EF_CH4_disp       * M_var["56", "CH4"]
        + EF_BIOCRUDE_disp  * M_var["47", "BIOCRUDE"]
        + EF_COMPOST_disp   * Mprod["CMP", "COMPOST"]
        + EF_BIOSOLIDS_disp * Px
        + EF_ELEC_disp      * Qc["STB"])
 
    # ================================================================
    # SECTION D — AQUEOUS, CHAR AND DIGESTATE DISPOSAL GHG
    # ================================================================
 
    eqs["GHG_aq_eq"] = Equation(m, name="GHG_aq_eq")
    eqs["GHG_aq_eq"][...] = GHG_aq == (Tann / 1000) * (
          EF_AQ_disp        * (M_var["42", "AQUEOUS_PHASE"] +
                               M_var["45", "AQUEOUS_PHASE"])
        + EF_CHAR_disp      * (M_var["42", "CHAR"] +
                               M_var["45", "CHAR"])
        + EF_BIOSOLIDS_disp * Sum(k, M_var["26", k]))
 
    # ================================================================
    # SECTION E — TOTAL GHG (objective 2)
    # ================================================================
 
    eqs["GHG_total_tpy_eq"] = Equation(m, name="GHG_total_tpy_eq")
    eqs["GHG_total_tpy_eq"][...] = GHG_total_tpy == (
          GHG_ind_tpy
        + GHG_dir_total
        + GHG_aq
        - GHG_disp)
 
    return eqs
 