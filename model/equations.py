"""
model/equations.py
==================
All mass balance and process equations for the food waste
optimization model.

Stages:
    Stage 1 — Feed, Splitter 1, Mechanical Pretreatment (SHR, MCR)
              Biological Pretreatment (AER, ENZ)
    Stage 2 — Conversion Technologies (HTL, AND, SLF, CMP, WWT, INC)
    Stage 3 — Recovery (CEN, FLT), Gas Upgrading (ABS, PSA), STB

Stream Map:
    1  = Food waste feed
    2  = BYP_1 (left bypass)
    3  = SHR feed
    4  = SHR output
    5  = SHR reject
    6  = MCR feed
    7  = MCR water addition
    8  = MCR output
    9  = Mixer 1 output
    10 = AER feed
    11 = AER offgas
    12 = AER output
    13 = AER water addition
    14 = ENZ feed
    15 = ENZ enzyme addition
    16 = ENZ offgas (zero)
    17 = ENZ output
    18 = Mixer 2 output
    19 = HTL feed
    20 = HTL gas product
    21 = HTL water addition
    22 = HTL products (biocrude, char, aqueous)
    23 = AND feed
    24 = AND water addition
    25 = AND uncaptured offgas
    26 = AND digestate
    27 = AND biogas
    28 = SLF feed
    29 = SLF uncaptured offgas
    30 = SLF captured LFG
    31 = CMP feed
    32 = CMP gas
    33 = CMP air
    34 = CMP compost
    35 = WWT feed
    36 = WWT offgas
    37 = WWT biosolids
    38 = INC feed
    39 = INC fugitive emissions
    40 = INC flue gas
    41 = CEN feed (from HTL)
    42 = CEN cake (char)
    43 = CEN liquid (biocrude)
    44 = FLT feed (from HTL)
    45 = FLT retentate
    46 = FLT permeate
    47 = Mixer 4 output (biocrude product)
    48 = Mixer 3 output (biogas from AND + SLF)
    49 = ABS feed
    50 = ABS water effluent
    51 = ABS offgas
    52 = ABS CH4 product
    53 = PSA feed
    54 = PSA offgas
    55 = PSA CH4 product
    56 = Mixer 5 output (biomethane)
    57 = STB electricity output
    58 = BYP_2 (right bypass)
    59 = STB boiler feedwater
    60 = STB steam
    61 = BYP_bio (biological bypass)
"""

from gamspy import Container, Equation, Sum


def build_equations(m: Container, sets: dict,
                    params: dict, vars: dict) -> dict:
    """
    Build all process equations.

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
    i       = sets["i"]
    k       = sets["k"]
    kp      = sets["kp"]
    i_mech  = sets["i_mech"]
    i_bio   = sets["i_bio"]
    iConv   = sets["iConv"]
    iHTLrec = sets["iHTLrec"]
    iGasUpg = sets["iGasUpg"]

    # ── Unpack parameters ────────────────────────────────────────────
    Qf         = params["Qf"]
    Frac       = params["Frac"]
    MM         = params["MM"]
    MM_ST      = params["MM_ST"]
    Den_FW     = params["Den_FW"]
    fdegAER    = params["fdegAER"]
    yHTL_p     = params["yHTL_p"]
    RFLT       = params["RFLT"]
    Den        = params["Den"]
    Zeta       = params["Zeta"]
    Eff_CNT    = params["Eff_CNT"]
    xBG        = params["xBG"]
    rWW        = params["rWW"]

    # Scalars
    eta_SHR    = params["eta_SHR"]
    Rw_MCR     = params["Rw_MCR"]
    Rw_AER     = params["Rw_AER"]
    theta_AER  = params["theta_AER"]
    eps_AER    = params["eps_AER"]
    yCO2_AER   = params["yCO2_AER"]
    yH2O_AER   = params["yH2O_AER"]
    r_enz      = params["r_enz"]
    eta_ENZ    = params["eta_ENZ"]
    HRT_ENZ    = params["HRT_ENZ"]
    rDry_HTL   = params["rDry_HTL"]
    rho_HTL    = params["rho_HTL"]
    T_HTL      = params["T_HTL"]
    T_amb      = params["T_amb"]
    etaHX_HTL  = params["etaHX_HTL"]
    Cp_eff     = params["Cp_eff"]
    dh_steam   = params["dh_steam"]
    theta_HTL  = params["theta_HTL"]
    eps_HTL    = params["eps_HTL"]
    HHV_HTLgas = params["HHV_HTLgas"]
    Rw_AND     = params["Rw_AND"]
    theta_AND  = params["theta_AND"]
    epsilon_AND= params["epsilon_AND"]
    eta_OTH_AND= params["eta_OTH_AND"]
    eta_cap_AND= params["eta_cap_AND"]
    eta_AND    = params["eta_AND"]
    BMP_scen   = params["BMP_scen"]
    rhoCH4     = params["rhoCH4"]
    MW_CH4     = params["MW_CH4"]
    MW_CO2_AND = params["MW_CO2_AND"]
    DOC_value  = params["DOC_value"]
    DOC_f_value= params["DOC_f_value"]
    MCF_value  = params["MCF_value"]
    F_value    = params["F_value"]
    density_CH4= params["density_CH4"]
    ratio_CH4_to_C = params["ratio_CH4_to_C"]
    Depth_SLF  = params["Depth_SLF"]
    ACRE       = params["ACRE"]
    OX         = params["OX"]
    CAP_SLF    = params["CAP_SLF"]
    MW1_CH4    = params["MW1_CH4"]
    MW1_CO2    = params["MW1_CO2"]
    Tann       = params["Tann"]
    fdeg_CMP   = params["fdeg_CMP"]
    yCO2_CMP   = params["yCO2_CMP"]
    yH2O_CMP   = params["yH2O_CMP"]
    yNH3_CMP   = params["yNH3_CMP"]
    EF_CH4_CMP_wet = params["EF_CH4_CMP_wet"]
    EF_N2O_CMP_wet = params["EF_N2O_CMP_wet"]
    theta_CMP  = params["theta_CMP"]
    epsilon_CMP= params["epsilon_CMP"]
    eta_OTH_CMP= params["eta_OTH_CMP"]
    yO2_air    = params["yO2_air"]
    yN2_air    = params["yN2_air"]
    EAR_CMP    = params["EAR_CMP"]
    alpha_O2_CMP = params["alpha_O2_CMP"]
    rho_ww     = params["rho_ww"]
    fBOD       = params["fBOD"]
    FM_day     = params["FM_day"]
    X_MLSS     = params["X_MLSS"]
    n_wwtp     = params["n_wwtp"]
    b_wwtp     = params["b_wwtp"]
    SRT_day    = params["SRT_day"]
    yCO2_WWT   = params["yCO2_WWT"]
    yH2O_WWT   = params["yH2O_WWT"]
    EF_CH4_WWT = params["EF_CH4_WWT"]
    EF_N2O_WWT = params["EF_N2O_WWT"]
    lambda_inc = params["lambda_inc"]
    EF_CH4_INC_wet = params["EF_CH4_INC_wet"]
    EF_N2O_INC_wet = params["EF_N2O_INC_wet"]
    C_frac     = params["C_frac"]
    H_frac     = params["H_frac"]
    O_frac     = params["O_frac"]
    N_frac     = params["N_frac"]
    S_frac     = params["S_frac"]
    CP_g       = params["CP_g"]
    T_g_in     = params["T_g_in"]
    T_g_out    = params["T_g_out"]
    H2_steam   = params["H2_steam"]
    H1_water   = params["H1_water"]
    h1_value   = params["h1_value"]
    h2_value   = params["h2_value"]
    eta_turbine   = params["eta_turbine"]
    eta_generator = params["eta_generator"]
    Vm_STP     = params["Vm_STP"]
    slipCH4_ABS  = params["slipCH4_ABS"]
    etaCO2_ABS   = params["etaCO2_ABS"]
    e_el_ABS     = params["e_el_ABS"]
    slipCH4_PSA  = params["slipCH4_PSA"]
    etaCO2_PSA   = params["etaCO2_PSA"]
    e_el_PSA     = params["e_el_PSA"]
    Pur_CH4      = params["Pur_CH4"]
    r_water_ABS  = params["r_water_ABS"]
    Cp_water     = params["Cp_water"]
    Tcw_out      = params["Tcw_out"]
    Tcw_in       = params["Tcw_in"]

    # ── Unpack variables ─────────────────────────────────────────────
    M_var        = vars["M_var"]
    Qc           = vars["Qc"]
    PW           = vars["PW"]
    Mstm         = vars["Mstm"]
    Mcw          = vars["Mcw"]
    Mprod        = vars["Mprod"]
    W_total      = vars["W_total"]
    yS1          = vars["yS1"]
    yConv        = vars["yConv"]
    yHTLrec      = vars["yHTLrec"]
    yGasUpg      = vars["yGasUpg"]
    ySTB         = vars["ySTB"]
    yBio         = vars["yBio"]
    yBYP1        = vars["yBYP1"]
    yBYP2        = vars["yBYP2"]
    yBYP_bio     = vars["yBYP_bio"]
    VS_AER_deg   = vars["VS_AER_deg"]
    V_w_AER      = vars["V_w_AER"]
    V_vessel_AER = vars["V_vessel_AER"]
    V_ENZ        = vars["V_ENZ"]
    ENZ_DS_in    = vars["ENZ_DS_in"]
    Morg_HTL     = vars["Morg_HTL"]
    Mslurry17    = vars["Mslurry17"]
    Mslurry22    = vars["Mslurry22"]
    mHTL_heated  = vars["mHTL_heated"]
    Qnet_HTL     = vars["Qnet_HTL"]
    Qgas_HTL     = vars["Qgas_HTL"]
    V_w_HTL      = vars["V_w_HTL"]
    V_vessel_HTL = vars["V_vessel_HTL"]
    VSANDin      = vars["VSANDin"]
    CH4gen       = vars["CH4gen"]
    CO2gen       = vars["CO2gen"]
    V_w_AND      = vars["V_w_AND"]
    V_vessel_AND = vars["V_vessel_AND"]
    CH4_mass_SLF    = vars["CH4_mass_SLF"]
    CO2_mass_SLF    = vars["CO2_mass_SLF"]
    CH4_volume_SLF  = vars["CH4_volume_SLF"]
    m_wasteleft_SLF = vars["m_wasteleft_SLF"]
    vol_FW_SLF      = vars["vol_FW_SLF"]
    CH4_ox_SLF      = vars["CH4_ox_SLF"]
    VSCMP_in     = vars["VSCMP_in"]
    VSCMP_deg    = vars["VSCMP_deg"]
    O2req_CMP    = vars["O2req_CMP"]
    AirCMP       = vars["AirCMP"]
    V_work_CMP   = vars["V_work_CMP"]
    V_vessel_CMP = vars["V_vessel_CMP"]
    Qww_m3ph     = vars["Qww_m3ph"]
    mVS_in       = vars["mVS_in"]
    mVS_deg_WWT  = vars["mVS_deg_WWT"]
    Px           = vars["Px"]
    m_wasteleft_WWT = vars["m_wasteleft_WWT"]
    mdry_inc     = vars["mdry_inc"]
    mdaf_inc     = vars["mdaf_inc"]
    nC_inc       = vars["nC_inc"]
    nH_inc       = vars["nH_inc"]
    nO_inc       = vars["nO_inc"]
    nN_inc       = vars["nN_inc"]
    nS_inc       = vars["nS_inc"]
    nO2_sto      = vars["nO2_sto"]
    nO2_in       = vars["nO2_in"]
    nN2_air      = vars["nN2_air"]
    nCO2_inc     = vars["nCO2_inc"]
    nH2O_inc     = vars["nH2O_inc"]
    nSO2_inc     = vars["nSO2_inc"]
    nO2_out      = vars["nO2_out"]
    nN2_out      = vars["nN2_out"]
    mflue_inc    = vars["mflue_inc"]
    m_ash_INC    = vars["m_ash_INC"]
    P_turbine    = vars["P_turbine"]
    CF           = vars["CF"]
    U            = vars["U"]

    eqs = {}

    # ================================================================
    # STAGE 1 — FEED + SPLITTER 1
    # ================================================================

    eqs["eq_feed"] = Equation(m, name="eq_feed", domain=k)
    eqs["eq_feed"][k] = M_var["1", k] == Qf * Frac[k]

    eqs["Spl1_bal"] = Equation(m, name="Spl1_bal", domain=k)
    eqs["Spl1_bal"][k] = M_var["1", k] == (M_var["2", k] + M_var["3", k]
                                           + M_var["6", k] + M_var["58", k])

    eqs["Spl1_byp1_cap"] = Equation(m, name="Spl1_byp1_cap", domain=k)
    eqs["Spl1_byp1_cap"][k] = M_var["2", k] <= Qf * Frac[k] * yBYP1

    eqs["Spl1_SHR_cap"] = Equation(m, name="Spl1_SHR_cap", domain=k)
    eqs["Spl1_SHR_cap"][k] = M_var["3", k] <= Qf * Frac[k] * yS1["SHR"]

    eqs["Spl1_MCR_cap"] = Equation(m, name="Spl1_MCR_cap", domain=k)
    eqs["Spl1_MCR_cap"][k] = M_var["6", k] <= Qf * Frac[k] * yS1["MCR"]

    eqs["Spl1_byp2_cap"] = Equation(m, name="Spl1_byp2_cap", domain=k)
    eqs["Spl1_byp2_cap"][k] = M_var["58", k] <= Qf * Frac[k] * yBYP2

    eqs["Mech_choose"] = Equation(m, name="Mech_choose")
    eqs["Mech_choose"][...] = yS1["SHR"] + yS1["MCR"] + yBYP1 + yBYP2 == 1

    # ── SHR ────────────────────────────────────────────────────────
    eqs["eq_SHR_out"] = Equation(m, name="eq_SHR_out", domain=k)
    eqs["eq_SHR_out"][k] = M_var["4", k] == eta_SHR * M_var["3", k]

    eqs["eq_SHR_rej"] = Equation(m, name="eq_SHR_rej", domain=k)
    eqs["eq_SHR_rej"][k] = M_var["5", k] == (1 - eta_SHR) * M_var["3", k]

    eqs["eq_SHR_Qc"] = Equation(m, name="eq_SHR_Qc")
    eqs["eq_SHR_Qc"][...] = Qc["SHR"] == Sum(k, M_var["3", k])

    eqs["eq_SHR_PW"] = Equation(m, name="eq_SHR_PW")
    eqs["eq_SHR_PW"][...] = PW["SHR"] == params["Wsp"]["SHR"] * Qc["SHR"]

    eqs["Mstm_SHR_zero"] = Equation(m, name="Mstm_SHR_zero")
    eqs["Mstm_SHR_zero"][...] = Mstm["SHR"] == 0

    eqs["Mcw_SHR_zero"] = Equation(m, name="Mcw_SHR_zero")
    eqs["Mcw_SHR_zero"][...] = Mcw["SHR"] == 0

    eqs["Mprod_SHR_zero"] = Equation(m, name="Mprod_SHR_zero", domain=kp)
    eqs["Mprod_SHR_zero"][kp] = Mprod["SHR", kp] == 0

    # ── MCR ────────────────────────────────────────────────────────
    eqs["eq_MCR_water"] = Equation(m, name="eq_MCR_water")
    eqs["eq_MCR_water"][...] = (M_var["7", "WATER"] ==
                                Rw_MCR * Sum(k.where[~k.sameAs("WATER")], M_var["6", k]))

    eqs["eq_MCR_water_zero"] = Equation(m, name="eq_MCR_water_zero", domain=k)
    eqs["eq_MCR_water_zero"][k].where[~k.sameAs("WATER")] = M_var["7", k] == 0

    eqs["eq_MCR_out"] = Equation(m, name="eq_MCR_out", domain=k)
    eqs["eq_MCR_out"][k] = M_var["8", k] == M_var["6", k] + M_var["7", k]

    eqs["eq_MCR_Qc"] = Equation(m, name="eq_MCR_Qc")
    eqs["eq_MCR_Qc"][...] = Qc["MCR"] == Sum(k, M_var["6", k])

    eqs["eq_MCR_PW"] = Equation(m, name="eq_MCR_PW")
    eqs["eq_MCR_PW"][...] = PW["MCR"] == params["Wsp"]["MCR"] * Qc["MCR"]

    eqs["Mstm_MCR_zero"] = Equation(m, name="Mstm_MCR_zero")
    eqs["Mstm_MCR_zero"][...] = Mstm["MCR"] == 0

    eqs["Mcw_MCR_zero"] = Equation(m, name="Mcw_MCR_zero")
    eqs["Mcw_MCR_zero"][...] = Mcw["MCR"] == 0

    eqs["Mprod_MCR_zero"] = Equation(m, name="Mprod_MCR_zero", domain=kp)
    eqs["Mprod_MCR_zero"][kp] = Mprod["MCR", kp] == 0

    # ── Mixer 1 ────────────────────────────────────────────────────
    eqs["Mxr1_bal"] = Equation(m, name="Mxr1_bal", domain=k)
    eqs["Mxr1_bal"][k] = M_var["9", k] == M_var["4", k] + M_var["8", k]

    # ── Splitter 2 ─────────────────────────────────────────────────
    eqs["Spl2_bal"] = Equation(m, name="Spl2_bal", domain=k)
    eqs["Spl2_bal"][k] = (M_var["9", k] + M_var["2", k] ==
                          M_var["10", k] + M_var["14", k] + M_var["61", k])

    eqs["Spl2_AER_cap"] = Equation(m, name="Spl2_AER_cap", domain=k)
    eqs["Spl2_AER_cap"][k] = M_var["10", k] <= MM * yBio["AER"]

    eqs["Spl2_ENZ_cap"] = Equation(m, name="Spl2_ENZ_cap", domain=k)
    eqs["Spl2_ENZ_cap"][k] = M_var["14", k] <= MM * yBio["ENZ"]

    eqs["Spl2_BYPbio_cap"] = Equation(m, name="Spl2_BYPbio_cap", domain=k)
    eqs["Spl2_BYPbio_cap"][k] = M_var["61", k] <= MM * yBYP_bio

    eqs["Bio_choose"] = Equation(m, name="Bio_choose")
    eqs["Bio_choose"][...] = yBio["AER"] + yBio["ENZ"] + yBYP_bio == 1 - yBYP2

    # ── AER ────────────────────────────────────────────────────────
    eqs["AER_addW"] = Equation(m, name="AER_addW")
    eqs["AER_addW"][...] = (M_var["13", "WATER"] ==
                            Rw_AER * Sum(k.where[~k.sameAs("WATER")], M_var["10", k]))

    eqs["AER_addW_zero"] = Equation(m, name="AER_addW_zero", domain=k)
    eqs["AER_addW_zero"][k].where[~k.sameAs("WATER")] = M_var["13", k] == 0

    eqs["AER_VSdeg_eq"] = Equation(m, name="AER_VSdeg_eq")
    eqs["AER_VSdeg_eq"][...] = VS_AER_deg == (fdegAER["CBH"] * M_var["10", "CBH"] +
                                               fdegAER["PRT"] * M_var["10", "PRT"] +
                                               fdegAER["FAT"] * M_var["10", "FAT"] +
                                               fdegAER["OTH"] * M_var["10", "OTH"])

    eqs["AER_gas_CO2"] = Equation(m, name="AER_gas_CO2")
    eqs["AER_gas_CO2"][...] = M_var["11", "CO2"] == yCO2_AER * VS_AER_deg

    eqs["AER_gas_H2O"] = Equation(m, name="AER_gas_H2O")
    eqs["AER_gas_H2O"][...] = M_var["11", "WATER"] == yH2O_AER * VS_AER_deg

    eqs["AER_gas_zero"] = Equation(m, name="AER_gas_zero", domain=k)
    eqs["AER_gas_zero"][k].where[~k.sameAs("CO2") & ~k.sameAs("WATER")] = M_var["11", k] == 0

    eqs["AER_out_CBH"] = Equation(m, name="AER_out_CBH")
    eqs["AER_out_CBH"][...] = M_var["12", "CBH"] == (1 - fdegAER["CBH"]) * M_var["10", "CBH"]

    eqs["AER_out_PRT"] = Equation(m, name="AER_out_PRT")
    eqs["AER_out_PRT"][...] = M_var["12", "PRT"] == (1 - fdegAER["PRT"]) * M_var["10", "PRT"]

    eqs["AER_out_FAT"] = Equation(m, name="AER_out_FAT")
    eqs["AER_out_FAT"][...] = M_var["12", "FAT"] == (1 - fdegAER["FAT"]) * M_var["10", "FAT"]

    eqs["AER_out_OTH"] = Equation(m, name="AER_out_OTH")
    eqs["AER_out_OTH"][...] = M_var["12", "OTH"] == (1 - fdegAER["OTH"]) * M_var["10", "OTH"]

    eqs["AER_out_ASH"] = Equation(m, name="AER_out_ASH")
    eqs["AER_out_ASH"][...] = M_var["12", "ASH"] == M_var["10", "ASH"]

    eqs["AER_out_FC"] = Equation(m, name="AER_out_FC")
    eqs["AER_out_FC"][...] = M_var["12", "FIXED_CARBON"] == M_var["10", "FIXED_CARBON"]

    eqs["AER_out_WAT"] = Equation(m, name="AER_out_WAT")
    eqs["AER_out_WAT"][...] = (M_var["12", "WATER"] ==
                               M_var["10", "WATER"] + M_var["13", "WATER"] - M_var["11", "WATER"])

    eqs["AER_out_zero"] = Equation(m, name="AER_out_zero", domain=k)
    eqs["AER_out_zero"][k].where[
        ~k.sameAs("CBH") & ~k.sameAs("PRT") & ~k.sameAs("FAT") & ~k.sameAs("OTH") &
        ~k.sameAs("ASH") & ~k.sameAs("FIXED_CARBON") & ~k.sameAs("WATER")
    ] = M_var["12", k] == 0

    eqs["AER_working_vol"] = Equation(m, name="AER_working_vol")
    eqs["AER_working_vol"][...] = (Den_FW * V_w_AER ==
                                   theta_AER * (Sum(k, M_var["10", k]) + Sum(k, M_var["13", k])))

    eqs["AER_vessel_vol"] = Equation(m, name="AER_vessel_vol")
    eqs["AER_vessel_vol"][...] = eps_AER * V_vessel_AER == V_w_AER

    eqs["AER_capacity"] = Equation(m, name="AER_capacity")
    eqs["AER_capacity"][...] = Qc["AER"] == V_vessel_AER

    eqs["AER_power"] = Equation(m, name="AER_power")
    eqs["AER_power"][...] = PW["AER"] == params["Wsp"]["AER"] * Qc["AER"]

    eqs["Mstm_AER_zero"] = Equation(m, name="Mstm_AER_zero")
    eqs["Mstm_AER_zero"][...] = Mstm["AER"] == 0

    eqs["Mcw_AER_zero"] = Equation(m, name="Mcw_AER_zero")
    eqs["Mcw_AER_zero"][...] = Mcw["AER"] == 0

    eqs["Mprod_AER_zero"] = Equation(m, name="Mprod_AER_zero", domain=kp)
    eqs["Mprod_AER_zero"][kp] = Mprod["AER", kp] == 0

    # ── ENZ ────────────────────────────────────────────────────────
    eqs["ENZ_DSin_eq"] = Equation(m, name="ENZ_DSin_eq")
    eqs["ENZ_DSin_eq"][...] = ENZ_DS_in == (M_var["14", "CBH"] + M_var["14", "PRT"] +
                                             M_var["14", "FAT"] + M_var["14", "OTH"] +
                                             M_var["14", "ASH"] + M_var["14", "FIXED_CARBON"])

    eqs["ENZ_Ez"] = Equation(m, name="ENZ_Ez")
    eqs["ENZ_Ez"][...] = M_var["15", "ENZYME"] == r_enz * ENZ_DS_in

    eqs["ENZ_Ez_zero"] = Equation(m, name="ENZ_Ez_zero", domain=k)
    eqs["ENZ_Ez_zero"][k].where[~k.sameAs("ENZYME")] = M_var["15", k] == 0

    eqs["ENZ_offgas_zero"] = Equation(m, name="ENZ_offgas_zero", domain=k)
    eqs["ENZ_offgas_zero"][k] = M_var["16", k] == 0

    eqs["ENZ_out_CBH"] = Equation(m, name="ENZ_out_CBH")
    eqs["ENZ_out_CBH"][...] = M_var["17", "CBH"] == (1 - eta_ENZ) * M_var["14", "CBH"]

    eqs["ENZ_out_OTH"] = Equation(m, name="ENZ_out_OTH")
    eqs["ENZ_out_OTH"][...] = (M_var["17", "OTH"] ==
                               M_var["14", "OTH"] + eta_ENZ * M_var["14", "CBH"] +
                               M_var["15", "ENZYME"])

    eqs["ENZ_out_rest"] = Equation(m, name="ENZ_out_rest", domain=k)
    eqs["ENZ_out_rest"][k].where[
        ~k.sameAs("CBH") & ~k.sameAs("OTH") & ~k.sameAs("ENZYME")
    ] = M_var["17", k] == M_var["14", k]

    eqs["ENZ_out_enz_zero"] = Equation(m, name="ENZ_out_enz_zero")
    eqs["ENZ_out_enz_zero"][...] = M_var["17", "ENZYME"] == 0

    eqs["ENZ_V"] = Equation(m, name="ENZ_V")
    eqs["ENZ_V"][...] = (Den_FW * V_ENZ ==
                         HRT_ENZ * (Sum(k, M_var["14", k]) + Sum(k, M_var["15", k])))

    eqs["ENZ_capacity"] = Equation(m, name="ENZ_capacity")
    eqs["ENZ_capacity"][...] = Qc["ENZ"] == V_ENZ

    eqs["ENZ_power"] = Equation(m, name="ENZ_power")
    eqs["ENZ_power"][...] = PW["ENZ"] == params["Wsp"]["ENZ"] * Qc["ENZ"]

    eqs["Mstm_ENZ_zero"] = Equation(m, name="Mstm_ENZ_zero")
    eqs["Mstm_ENZ_zero"][...] = Mstm["ENZ"] == 0

    eqs["Mcw_ENZ_zero"] = Equation(m, name="Mcw_ENZ_zero")
    eqs["Mcw_ENZ_zero"][...] = Mcw["ENZ"] == 0

    eqs["Mprod_ENZ_zero"] = Equation(m, name="Mprod_ENZ_zero", domain=kp)
    eqs["Mprod_ENZ_zero"][kp] = Mprod["ENZ", kp] == 0

    # ── Mixer 2 ────────────────────────────────────────────────────
    eqs["Mxr2_bal"] = Equation(m, name="Mxr2_bal", domain=k)
    eqs["Mxr2_bal"][k] = (M_var["18", k] ==
                          M_var["12", k] + M_var["17", k] + M_var["61", k])

    eqs["eq_Wtotal"] = Equation(m, name="eq_Wtotal")
    eqs["eq_Wtotal"][...] = W_total == Sum(i, PW[i])

    # ================================================================
    # SPLITTER 3 — TO CONVERSION TECHNOLOGIES
    # ================================================================

    eqs["Spl3_bal"] = Equation(m, name="Spl3_bal", domain=k)
    eqs["Spl3_bal"][k] = (M_var["18", k] + M_var["58", k] ==
                          M_var["19", k] + M_var["23", k] + M_var["28", k] +
                          M_var["31", k] + M_var["35", k] + M_var["38", k])

    eqs["Spl3_HTL_cap"] = Equation(m, name="Spl3_HTL_cap", domain=k)
    eqs["Spl3_HTL_cap"][k] = M_var["19", k] <= MM * yConv["HTL"]

    eqs["Spl3_AND_cap"] = Equation(m, name="Spl3_AND_cap", domain=k)
    eqs["Spl3_AND_cap"][k] = M_var["23", k] <= MM * yConv["AND"]

    eqs["Spl3_SLF_cap"] = Equation(m, name="Spl3_SLF_cap", domain=k)
    eqs["Spl3_SLF_cap"][k] = M_var["28", k] <= MM * yConv["SLF"]

    eqs["Spl3_CMP_cap"] = Equation(m, name="Spl3_CMP_cap", domain=k)
    eqs["Spl3_CMP_cap"][k] = M_var["31", k] <= MM * yConv["CMP"]

    eqs["Spl3_WWT_cap"] = Equation(m, name="Spl3_WWT_cap", domain=k)
    eqs["Spl3_WWT_cap"][k] = M_var["35", k] <= MM * yConv["WWT"]

    eqs["Spl3_INC_cap"] = Equation(m, name="Spl3_INC_cap", domain=k)
    eqs["Spl3_INC_cap"][k] = M_var["38", k] <= MM * yConv["INC"]

    eqs["Conv_choose"] = Equation(m, name="Conv_choose")
    eqs["Conv_choose"][...] = Sum(iConv, yConv[iConv]) == 1

    # ================================================================
    # STAGE 2 — CONVERSION TECHNOLOGIES
    # ================================================================

    # ── HTL ────────────────────────────────────────────────────────
    eqs["HTL_org_def"] = Equation(m, name="HTL_org_def")
    eqs["HTL_org_def"][...] = Morg_HTL == (M_var["19", "CBH"] + M_var["19", "PRT"] +
                                            M_var["19", "FAT"] + M_var["19", "OTH"])

    eqs["HTL_addW_def_new"] = Equation(m, name="HTL_addW_def_new")
    eqs["HTL_addW_def_new"][...] = (M_var["19", "WATER"] + M_var["21", "WATER"] >=
                                    rDry_HTL * Sum(k.where[~k.sameAs("WATER")], M_var["19", k]))

    eqs["HTL_water_zero"] = Equation(m, name="HTL_water_zero", domain=k)
    eqs["HTL_water_zero"][k].where[~k.sameAs("WATER")] = M_var["21", k] == 0

    eqs["HTL_gas"] = Equation(m, name="HTL_gas")
    eqs["HTL_gas"][...] = M_var["20", "GAS_PRODUCT"] == yHTL_p["GAS_PRODUCT"] * Morg_HTL

    eqs["HTL_gas_zero"] = Equation(m, name="HTL_gas_zero", domain=k)
    eqs["HTL_gas_zero"][k].where[~k.sameAs("GAS_PRODUCT")] = M_var["20", k] == 0

    eqs["HTL_biocrude"] = Equation(m, name="HTL_biocrude")
    eqs["HTL_biocrude"][...] = M_var["22", "BIOCRUDE"] == yHTL_p["BIOCRUDE"] * Morg_HTL

    eqs["HTL_char"] = Equation(m, name="HTL_char")
    eqs["HTL_char"][...] = (M_var["22", "CHAR"] ==
                            yHTL_p["CHAR"] * Morg_HTL +
                            M_var["19", "FIXED_CARBON"] + M_var["19", "ASH"])

    eqs["HTL_aq"] = Equation(m, name="HTL_aq")
    eqs["HTL_aq"][...] = (M_var["22", "AQUEOUS_PHASE"] ==
                          yHTL_p["AQUEOUS_PHASE"] * Morg_HTL +
                          M_var["19", "WATER"] + M_var["21", "WATER"])

    eqs["HTL_22_zero"] = Equation(m, name="HTL_22_zero", domain=k)
    eqs["HTL_22_zero"][k].where[
        ~k.sameAs("BIOCRUDE") & ~k.sameAs("CHAR") & ~k.sameAs("AQUEOUS_PHASE")
    ] = M_var["22", k] == 0

    eqs["Slurry22_def"] = Equation(m, name="Slurry22_def")
    eqs["Slurry22_def"][...] = Mslurry22 == (M_var["22", "BIOCRUDE"] +
                                              M_var["22", "CHAR"] +
                                              M_var["22", "AQUEOUS_PHASE"])

    eqs["HTL_mheated_def"] = Equation(m, name="HTL_mheated_def")
    eqs["HTL_mheated_def"][...] = mHTL_heated == Sum(k, M_var["19", k]) + M_var["21", "WATER"]

    eqs["HTL_working_vol"] = Equation(m, name="HTL_working_vol")
    eqs["HTL_working_vol"][...] = rho_HTL * V_w_HTL == theta_HTL * mHTL_heated

    eqs["HTL_vessel_vol"] = Equation(m, name="HTL_vessel_vol")
    eqs["HTL_vessel_vol"][...] = eps_HTL * V_vessel_HTL == V_w_HTL

    eqs["HTL_capacity"] = Equation(m, name="HTL_capacity")
    eqs["HTL_capacity"][...] = Qc["HTL"] == V_vessel_HTL

    eqs["HTL_power"] = Equation(m, name="HTL_power")
    eqs["HTL_power"][...] = PW["HTL"] == params["Wsp"]["HTL"] * Qc["HTL"]

    eqs["HTL_heat_gross"] = Equation(m, name="HTL_heat_gross")
    eqs["HTL_heat_gross"][...] = (Qnet_HTL ==
                                  (1 - etaHX_HTL) * mHTL_heated * Cp_eff * (T_HTL - T_amb))

    eqs["HTL_gas_heat"] = Equation(m, name="HTL_gas_heat")
    eqs["HTL_gas_heat"][...] = Qgas_HTL == HHV_HTLgas * M_var["20", "GAS_PRODUCT"] * 1000

    eqs["HTL_steam_req"] = Equation(m, name="HTL_steam_req")
    eqs["HTL_steam_req"][...] = dh_steam * Mstm["HTL"] >= Qnet_HTL - Qgas_HTL

    eqs["HTL_Mcw_zero"] = Equation(m, name="HTL_Mcw_zero")
    eqs["HTL_Mcw_zero"][...] = Mcw["HTL"] == 0

    eqs["HTL_nonprod_zero"] = Equation(m, name="HTL_nonprod_zero", domain=kp)
    eqs["HTL_nonprod_zero"][kp].where[~kp.sameAs("BIOCRUDE")] = Mprod["HTL", kp] == 0

    # ── AND ────────────────────────────────────────────────────────
    eqs["AND_addW_new"] = Equation(m, name="AND_addW_new")
    eqs["AND_addW_new"][...] = (M_var["23", "WATER"] + M_var["24", "WATER"] >=
                                (1 + Rw_AND) * Sum(k.where[~k.sameAs("WATER")], M_var["23", k]))

    eqs["AND_addW_zero"] = Equation(m, name="AND_addW_zero", domain=k)
    eqs["AND_addW_zero"][k].where[~k.sameAs("WATER")] = M_var["24", k] == 0

    eqs["AND_VS"] = Equation(m, name="AND_VS")
    eqs["AND_VS"][...] = VSANDin == (M_var["23", "CBH"] + M_var["23", "PRT"] +
                                     M_var["23", "FAT"] + eta_OTH_AND * M_var["23", "OTH"])

    eqs["AND_CH4gen"] = Equation(m, name="AND_CH4gen")
    eqs["AND_CH4gen"][...] = CH4gen == eta_AND * BMP_scen * rhoCH4 * VSANDin

    eqs["AND_CO2gen"] = Equation(m, name="AND_CO2gen")
    eqs["AND_CO2gen"][...] = CO2gen == CH4gen * (MW_CO2_AND / MW_CH4) * (xBG["CO2"] / xBG["CH4"])

    eqs["AND_biogasCH4"] = Equation(m, name="AND_biogasCH4")
    eqs["AND_biogasCH4"][...] = M_var["27", "CH4"] == eta_cap_AND * CH4gen

    eqs["AND_biogasCO2"] = Equation(m, name="AND_biogasCO2")
    eqs["AND_biogasCO2"][...] = M_var["27", "CO2"] == eta_cap_AND * CO2gen

    eqs["AND_biogas_zero"] = Equation(m, name="AND_biogas_zero", domain=k)
    eqs["AND_biogas_zero"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["27", k] == 0

    eqs["AND_offgasCH4"] = Equation(m, name="AND_offgasCH4")
    eqs["AND_offgasCH4"][...] = M_var["25", "CH4"] == (1 - eta_cap_AND) * CH4gen

    eqs["AND_offgasCO2"] = Equation(m, name="AND_offgasCO2")
    eqs["AND_offgasCO2"][...] = M_var["25", "CO2"] == (1 - eta_cap_AND) * CO2gen

    eqs["AND_offgas_zero"] = Equation(m, name="AND_offgas_zero", domain=k)
    eqs["AND_offgas_zero"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["25", k] == 0

    eqs["AND_dig_CBH"] = Equation(m, name="AND_dig_CBH")
    eqs["AND_dig_CBH"][...] = M_var["26", "CBH"] == (1 - eta_AND) * M_var["23", "CBH"]

    eqs["AND_dig_PRT"] = Equation(m, name="AND_dig_PRT")
    eqs["AND_dig_PRT"][...] = M_var["26", "PRT"] == (1 - eta_AND) * M_var["23", "PRT"]

    eqs["AND_dig_FAT"] = Equation(m, name="AND_dig_FAT")
    eqs["AND_dig_FAT"][...] = M_var["26", "FAT"] == (1 - eta_AND) * M_var["23", "FAT"]

    eqs["AND_dig_OTH"] = Equation(m, name="AND_dig_OTH")
    eqs["AND_dig_OTH"][...] = (M_var["26", "OTH"] ==
                               M_var["23", "OTH"] - eta_OTH_AND * eta_AND * M_var["23", "OTH"])

    eqs["AND_dig_ASH"] = Equation(m, name="AND_dig_ASH")
    eqs["AND_dig_ASH"][...] = M_var["26", "ASH"] == M_var["23", "ASH"]

    eqs["AND_dig_FC"] = Equation(m, name="AND_dig_FC")
    eqs["AND_dig_FC"][...] = M_var["26", "FIXED_CARBON"] == M_var["23", "FIXED_CARBON"]

    eqs["AND_dig_WAT"] = Equation(m, name="AND_dig_WAT")
    eqs["AND_dig_WAT"][...] = (M_var["26", "WATER"] ==
                               M_var["23", "WATER"] + M_var["24", "WATER"])

    eqs["AND_dig_zero"] = Equation(m, name="AND_dig_zero", domain=k)
    eqs["AND_dig_zero"][k].where[
        ~k.sameAs("CBH") & ~k.sameAs("PRT") & ~k.sameAs("FAT") & ~k.sameAs("OTH") &
        ~k.sameAs("ASH") & ~k.sameAs("FIXED_CARBON") & ~k.sameAs("WATER")
    ] = M_var["26", k] == 0

    eqs["AND_working_vol"] = Equation(m, name="AND_working_vol")
    eqs["AND_working_vol"][...] = (Den_FW * V_w_AND ==
                                   theta_AND * (Sum(k, M_var["23", k]) + Sum(k, M_var["24", k])))

    eqs["AND_vessel_vol"] = Equation(m, name="AND_vessel_vol")
    eqs["AND_vessel_vol"][...] = epsilon_AND * V_vessel_AND == V_w_AND

    eqs["AND_capacity"] = Equation(m, name="AND_capacity")
    eqs["AND_capacity"][...] = Qc["AND"] == V_vessel_AND

    eqs["AND_power"] = Equation(m, name="AND_power")
    eqs["AND_power"][...] = PW["AND"] == params["Wsp"]["AND"] * Qc["AND"]

    eqs["Mstm_AND_zero"] = Equation(m, name="Mstm_AND_zero")
    eqs["Mstm_AND_zero"][...] = Mstm["AND"] == 0

    eqs["Mcw_AND_zero"] = Equation(m, name="Mcw_AND_zero")
    eqs["Mcw_AND_zero"][...] = Mcw["AND"] == 0

    eqs["Mprod_AND_zero"] = Equation(m, name="Mprod_AND_zero", domain=kp)
    eqs["Mprod_AND_zero"][kp] = Mprod["AND", kp] == 0

    # ── SLF ────────────────────────────────────────────────────────
    eqs["SLF_CH4gen"] = Equation(m, name="SLF_CH4gen")
    eqs["SLF_CH4gen"][...] = (CH4_mass_SLF ==
                              Sum(k.where[~k.sameAs("WATER") & ~k.sameAs("ASH")], M_var["28", k])
                              * DOC_value * DOC_f_value * MCF_value * F_value * ratio_CH4_to_C)

    eqs["SLF_CO2gen"] = Equation(m, name="SLF_CO2gen")
    eqs["SLF_CO2gen"][...] = (CO2_mass_SLF ==
                              CH4_mass_SLF * ((1 - F_value) / F_value) * (MW1_CO2 / MW1_CH4))

    eqs["SLF_oxidation"] = Equation(m, name="SLF_oxidation")
    eqs["SLF_oxidation"][...] = CH4_ox_SLF == (1 - CAP_SLF) * OX * CH4_mass_SLF

    eqs["SLF_CH4_vol"] = Equation(m, name="SLF_CH4_vol")
    eqs["SLF_CH4_vol"][...] = CH4_volume_SLF == CH4_mass_SLF / density_CH4

    eqs["SLF_cap_CH4"] = Equation(m, name="SLF_cap_CH4")
    eqs["SLF_cap_CH4"][...] = M_var["30", "CH4"] == CAP_SLF * CH4_mass_SLF

    eqs["SLF_cap_CO2"] = Equation(m, name="SLF_cap_CO2")
    eqs["SLF_cap_CO2"][...] = M_var["30", "CO2"] == CAP_SLF * CO2_mass_SLF

    eqs["SLF_cap_zero"] = Equation(m, name="SLF_cap_zero", domain=k)
    eqs["SLF_cap_zero"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["30", k] == 0

    eqs["SLF_off_CH4"] = Equation(m, name="SLF_off_CH4")
    eqs["SLF_off_CH4"][...] = (M_var["29", "CH4"] ==
                               (1 - CAP_SLF) * (1 - OX) * CH4_mass_SLF)

    eqs["SLF_off_CO2"] = Equation(m, name="SLF_off_CO2")
    eqs["SLF_off_CO2"][...] = (M_var["29", "CO2"] ==
                               (1 - CAP_SLF) * CO2_mass_SLF +
                               (MW1_CO2 / MW1_CH4) * CH4_ox_SLF)

    eqs["SLF_off_zero"] = Equation(m, name="SLF_off_zero", domain=k)
    eqs["SLF_off_zero"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["29", k] == 0

    eqs["SLF_wasteleft"] = Equation(m, name="SLF_wasteleft")
    eqs["SLF_wasteleft"][...] = (m_wasteleft_SLF ==
                                 Sum(k, M_var["28", k]) -
                                 M_var["30", "CH4"] - M_var["30", "CO2"] -
                                 M_var["29", "CH4"] - M_var["29", "CO2"])

    eqs["SLF_vol"] = Equation(m, name="SLF_vol")
    eqs["SLF_vol"][...] = vol_FW_SLF == (Sum(k, M_var["28", k]) / Den_FW) * Tann

    eqs["SLF_capacity"] = Equation(m, name="SLF_capacity")
    eqs["SLF_capacity"][...] = Qc["SLF"] == vol_FW_SLF / (Depth_SLF * ACRE)

    eqs["SLF_power"] = Equation(m, name="SLF_power")
    eqs["SLF_power"][...] = PW["SLF"] == params["Wsp"]["SLF"] * Qc["SLF"]

    eqs["Mstm_SLF_zero"] = Equation(m, name="Mstm_SLF_zero")
    eqs["Mstm_SLF_zero"][...] = Mstm["SLF"] == 0

    eqs["Mcw_SLF_zero"] = Equation(m, name="Mcw_SLF_zero")
    eqs["Mcw_SLF_zero"][...] = Mcw["SLF"] == 0

    eqs["Mprod_SLF_zero"] = Equation(m, name="Mprod_SLF_zero", domain=kp)
    eqs["Mprod_SLF_zero"][kp] = Mprod["SLF", kp] == 0

    # ── CMP ────────────────────────────────────────────────────────
    eqs["CMP_VS_in"] = Equation(m, name="CMP_VS_in")
    eqs["CMP_VS_in"][...] = VSCMP_in == (M_var["31", "CBH"] + M_var["31", "PRT"] +
                                          M_var["31", "FAT"] + eta_OTH_CMP * M_var["31", "OTH"])

    eqs["CMP_VS_deg"] = Equation(m, name="CMP_VS_deg")
    eqs["CMP_VS_deg"][...] = VSCMP_deg == fdeg_CMP * VSCMP_in

    eqs["CMP_O2_demand"] = Equation(m, name="CMP_O2_demand")
    eqs["CMP_O2_demand"][...] = O2req_CMP == alpha_O2_CMP * VSCMP_deg

    eqs["CMP_air_req"] = Equation(m, name="CMP_air_req")
    eqs["CMP_air_req"][...] = AirCMP >= EAR_CMP * O2req_CMP / yO2_air

    eqs["CMP_air_O2"] = Equation(m, name="CMP_air_O2")
    eqs["CMP_air_O2"][...] = M_var["33", "O2"] == yO2_air * AirCMP

    eqs["CMP_air_N2"] = Equation(m, name="CMP_air_N2")
    eqs["CMP_air_N2"][...] = M_var["33", "N2"] == yN2_air * AirCMP

    eqs["CMP_air_zero"] = Equation(m, name="CMP_air_zero", domain=k)
    eqs["CMP_air_zero"][k].where[~k.sameAs("O2") & ~k.sameAs("N2")] = M_var["33", k] == 0

    eqs["CMP_gas_CO2"] = Equation(m, name="CMP_gas_CO2")
    eqs["CMP_gas_CO2"][...] = M_var["32", "CO2"] == yCO2_CMP * VSCMP_deg

    eqs["CMP_gas_H2O"] = Equation(m, name="CMP_gas_H2O")
    eqs["CMP_gas_H2O"][...] = M_var["32", "WATER"] == yH2O_CMP * VSCMP_deg

    eqs["CMP_gas_NH3"] = Equation(m, name="CMP_gas_NH3")
    eqs["CMP_gas_NH3"][...] = M_var["32", "NH3"] == yNH3_CMP * VSCMP_deg

    eqs["CMP_gas_CH4"] = Equation(m, name="CMP_gas_CH4")
    eqs["CMP_gas_CH4"][...] = M_var["32", "CH4"] == EF_CH4_CMP_wet * VSCMP_in

    eqs["CMP_gas_N2O"] = Equation(m, name="CMP_gas_N2O")
    eqs["CMP_gas_N2O"][...] = M_var["32", "N2O"] == EF_N2O_CMP_wet * VSCMP_in

    eqs["CMP_gas_O2"] = Equation(m, name="CMP_gas_O2")
    eqs["CMP_gas_O2"][...] = M_var["32", "O2"] == M_var["33", "O2"] - O2req_CMP

    eqs["CMP_gas_N2"] = Equation(m, name="CMP_gas_N2")
    eqs["CMP_gas_N2"][...] = M_var["32", "N2"] == M_var["33", "N2"]

    eqs["CMP_gas_zero"] = Equation(m, name="CMP_gas_zero", domain=k)
    eqs["CMP_gas_zero"][k].where[
        ~k.sameAs("CO2") & ~k.sameAs("WATER") & ~k.sameAs("NH3") &
        ~k.sameAs("CH4") & ~k.sameAs("N2O") & ~k.sameAs("O2") & ~k.sameAs("N2")
    ] = M_var["32", k] == 0

    eqs["CMP_comp_CBH"] = Equation(m, name="CMP_comp_CBH")
    eqs["CMP_comp_CBH"][...] = (M_var["34", "CBH"] ==
                                M_var["31", "CBH"] - fdeg_CMP * M_var["31", "CBH"])

    eqs["CMP_comp_PRT"] = Equation(m, name="CMP_comp_PRT")
    eqs["CMP_comp_PRT"][...] = (M_var["34", "PRT"] ==
                                M_var["31", "PRT"] - fdeg_CMP * M_var["31", "PRT"])

    eqs["CMP_comp_FAT"] = Equation(m, name="CMP_comp_FAT")
    eqs["CMP_comp_FAT"][...] = (M_var["34", "FAT"] ==
                                M_var["31", "FAT"] - fdeg_CMP * M_var["31", "FAT"])

    eqs["CMP_comp_OTH"] = Equation(m, name="CMP_comp_OTH")
    eqs["CMP_comp_OTH"][...] = (M_var["34", "OTH"] ==
                                M_var["31", "OTH"] - fdeg_CMP * eta_OTH_CMP * M_var["31", "OTH"])

    eqs["CMP_comp_WAT"] = Equation(m, name="CMP_comp_WAT")
    eqs["CMP_comp_WAT"][...] = M_var["34", "WATER"] == M_var["31", "WATER"]

    eqs["CMP_comp_ASH"] = Equation(m, name="CMP_comp_ASH")
    eqs["CMP_comp_ASH"][...] = M_var["34", "ASH"] == M_var["31", "ASH"]

    eqs["CMP_comp_FC"] = Equation(m, name="CMP_comp_FC")
    eqs["CMP_comp_FC"][...] = M_var["34", "FIXED_CARBON"] == M_var["31", "FIXED_CARBON"]

    eqs["CMP_comp_zero"] = Equation(m, name="CMP_comp_zero", domain=k)
    eqs["CMP_comp_zero"][k].where[
        ~k.sameAs("CBH") & ~k.sameAs("PRT") & ~k.sameAs("FAT") & ~k.sameAs("OTH") &
        ~k.sameAs("WATER") & ~k.sameAs("ASH") & ~k.sameAs("FIXED_CARBON")
    ] = M_var["34", k] == 0

    eqs["CMP_wvol"] = Equation(m, name="CMP_wvol")
    eqs["CMP_wvol"][...] = V_work_CMP == theta_CMP * (Sum(k, M_var["31", k]) / Den_FW)

    eqs["CMP_vvol"] = Equation(m, name="CMP_vvol")
    eqs["CMP_vvol"][...] = V_vessel_CMP == V_work_CMP / epsilon_CMP

    eqs["CMP_capacity"] = Equation(m, name="CMP_capacity")
    eqs["CMP_capacity"][...] = Qc["CMP"] == V_vessel_CMP

    eqs["CMP_power"] = Equation(m, name="CMP_power")
    eqs["CMP_power"][...] = PW["CMP"] == params["Wsp"]["CMP"] * Qc["CMP"]

    eqs["Mstm_CMP_zero"] = Equation(m, name="Mstm_CMP_zero")
    eqs["Mstm_CMP_zero"][...] = Mstm["CMP"] == 0

    eqs["Mcw_CMP_zero"] = Equation(m, name="Mcw_CMP_zero")
    eqs["Mcw_CMP_zero"][...] = Mcw["CMP"] == 0

    eqs["CMP_prod_compost_new"] = Equation(m, name="CMP_prod_compost_new")
    eqs["CMP_prod_compost_new"][...] = (Mprod["CMP", "COMPOST"] ==
                                        M_var["34", "CBH"] + M_var["34", "PRT"] +
                                        M_var["34", "FAT"] + M_var["34", "OTH"] +
                                        M_var["34", "ASH"] + M_var["34", "FIXED_CARBON"])

    eqs["CMP_nonprod_zero"] = Equation(m, name="CMP_nonprod_zero", domain=kp)
    eqs["CMP_nonprod_zero"][kp].where[~kp.sameAs("COMPOST")] = Mprod["CMP", kp] == 0

    # ── WWT ────────────────────────────────────────────────────────
    eqs["WWT_AER_link"] = Equation(m, name="WWT_AER_link")
    eqs["WWT_AER_link"][...] = yConv["WWT"] <= yBio["AER"]

    eqs["WWT_Q_def"] = Equation(m, name="WWT_Q_def")
    eqs["WWT_Q_def"][...] = Qww_m3ph == Sum(k, M_var["35", k]) / rho_ww

    eqs["WWT_mVS_def"] = Equation(m, name="WWT_mVS_def")
    eqs["WWT_mVS_def"][...] = mVS_in == (M_var["35", "CBH"] + M_var["35", "PRT"] +
                                          M_var["35", "FAT"] + M_var["35", "OTH"])

    eqs["WWT_VSdeg"] = Equation(m, name="WWT_VSdeg")
    eqs["WWT_VSdeg"][...] = (mVS_deg_WWT ==
                             fBOD * mVS_in - (n_wwtp * fBOD * mVS_in) / (1 + b_wwtp * SRT_day))

    eqs["WWT_split_bio"] = Equation(m, name="WWT_split_bio", domain=k)
    eqs["WWT_split_bio"][k] = M_var["37", k] == rWW[k] * M_var["35", k]

    eqs["WWT_biosolids_prod"] = Equation(m, name="WWT_biosolids_prod")
    eqs["WWT_biosolids_prod"][...] = (Px ==
                                      (n_wwtp * fBOD * mVS_in) / (1 + b_wwtp * SRT_day) +
                                      M_var["37", "ASH"] + M_var["37", "FIXED_CARBON"])

    eqs["WWT_off_CO2"] = Equation(m, name="WWT_off_CO2")
    eqs["WWT_off_CO2"][...] = M_var["36", "CO2"] == yCO2_WWT * mVS_deg_WWT

    eqs["WWT_off_H2O"] = Equation(m, name="WWT_off_H2O")
    eqs["WWT_off_H2O"][...] = M_var["36", "WATER"] == yH2O_WWT * mVS_deg_WWT

    eqs["WWT_off_CH4"] = Equation(m, name="WWT_off_CH4")
    eqs["WWT_off_CH4"][...] = M_var["36", "CH4"] == EF_CH4_WWT * mVS_in

    eqs["WWT_off_N2O"] = Equation(m, name="WWT_off_N2O")
    eqs["WWT_off_N2O"][...] = M_var["36", "N2O"] == EF_N2O_WWT * mVS_in

    eqs["WWT_off_zero"] = Equation(m, name="WWT_off_zero", domain=k)
    eqs["WWT_off_zero"][k].where[
        ~k.sameAs("CO2") & ~k.sameAs("WATER") &
        ~k.sameAs("CH4") & ~k.sameAs("N2O")
    ] = M_var["36", k] == 0

    eqs["WWT_wasteleft"] = Equation(m, name="WWT_wasteleft")
    eqs["WWT_wasteleft"][...] = (m_wasteleft_WWT ==
                                 Sum(k, M_var["35", k]) -
                                 Sum(k, M_var["37", k]) - Sum(k, M_var["36", k]))

    eqs["WWT_capacity"] = Equation(m, name="WWT_capacity")
    eqs["WWT_capacity"][...] = Qc["WWT"] == (fBOD * mVS_in * 24) / (FM_day * X_MLSS)

    eqs["WWT_power"] = Equation(m, name="WWT_power")
    eqs["WWT_power"][...] = PW["WWT"] == params["Wsp"]["WWT"] * Qc["WWT"]

    eqs["Mstm_WWT_zero"] = Equation(m, name="Mstm_WWT_zero")
    eqs["Mstm_WWT_zero"][...] = Mstm["WWT"] == 0

    eqs["Mcw_WWT_zero"] = Equation(m, name="Mcw_WWT_zero")
    eqs["Mcw_WWT_zero"][...] = Mcw["WWT"] == 0

    eqs["WWT_biosolids_sale"] = Equation(m, name="WWT_biosolids_sale")
    eqs["WWT_biosolids_sale"][...] = Mprod["WWT", "BIOSOLIDS"] == Px

    eqs["WWT_nonprod_zero"] = Equation(m, name="WWT_nonprod_zero", domain=kp)
    eqs["WWT_nonprod_zero"][kp].where[~kp.sameAs("BIOSOLIDS")] = Mprod["WWT", kp] == 0

    # ── INC ────────────────────────────────────────────────────────
    eqs["INC_dryfeed"] = Equation(m, name="INC_dryfeed")
    eqs["INC_dryfeed"][...] = mdry_inc == Sum(k, M_var["38", k]) - M_var["38", "WATER"]

    eqs["INC_ash"] = Equation(m, name="INC_ash")
    eqs["INC_ash"][...] = m_ash_INC == M_var["38", "ASH"] + M_var["38", "FIXED_CARBON"]

    eqs["INC_daf"] = Equation(m, name="INC_daf")
    eqs["INC_daf"][...] = mdaf_inc == mdry_inc - M_var["38", "ASH"] - M_var["38", "FIXED_CARBON"]

    eqs["INC_elem_C"] = Equation(m, name="INC_elem_C")
    eqs["INC_elem_C"][...] = nC_inc == (mdaf_inc * C_frac) / 12.011

    eqs["INC_elem_H"] = Equation(m, name="INC_elem_H")
    eqs["INC_elem_H"][...] = nH_inc == (mdaf_inc * H_frac) / 1.008

    eqs["INC_elem_O"] = Equation(m, name="INC_elem_O")
    eqs["INC_elem_O"][...] = nO_inc == (mdaf_inc * O_frac) / 15.999

    eqs["INC_elem_N"] = Equation(m, name="INC_elem_N")
    eqs["INC_elem_N"][...] = nN_inc == (mdaf_inc * N_frac) / 14.007

    eqs["INC_elem_S"] = Equation(m, name="INC_elem_S")
    eqs["INC_elem_S"][...] = nS_inc == (mdaf_inc * S_frac) / 32.065

    eqs["INC_stoO2"] = Equation(m, name="INC_stoO2")
    eqs["INC_stoO2"][...] = nO2_sto == nC_inc + 0.25 * nH_inc + nS_inc - 0.5 * nO_inc

    eqs["INC_airO2"] = Equation(m, name="INC_airO2")
    eqs["INC_airO2"][...] = nO2_in == lambda_inc * nO2_sto

    eqs["INC_airN2"] = Equation(m, name="INC_airN2")
    eqs["INC_airN2"][...] = nN2_air == (0.79 / 0.21) * nO2_in

    eqs["INC_prod_CO2"] = Equation(m, name="INC_prod_CO2")
    eqs["INC_prod_CO2"][...] = nCO2_inc == nC_inc

    eqs["INC_prod_H2O"] = Equation(m, name="INC_prod_H2O")
    eqs["INC_prod_H2O"][...] = nH2O_inc == 0.5 * nH_inc

    eqs["INC_prod_SO2"] = Equation(m, name="INC_prod_SO2")
    eqs["INC_prod_SO2"][...] = nSO2_inc == nS_inc

    eqs["INC_prod_O2"] = Equation(m, name="INC_prod_O2")
    eqs["INC_prod_O2"][...] = nO2_out == nO2_in - nO2_sto

    eqs["INC_prod_N2"] = Equation(m, name="INC_prod_N2")
    eqs["INC_prod_N2"][...] = nN2_out == nN2_air + 0.5 * nN_inc

    eqs["INC_fug_CH4"] = Equation(m, name="INC_fug_CH4")
    eqs["INC_fug_CH4"][...] = M_var["39", "CH4"] == EF_CH4_INC_wet * Sum(k, M_var["38", k])

    eqs["INC_fug_N2O"] = Equation(m, name="INC_fug_N2O")
    eqs["INC_fug_N2O"][...] = M_var["39", "N2O"] == EF_N2O_INC_wet * Sum(k, M_var["38", k])

    eqs["INC_fug_zero"] = Equation(m, name="INC_fug_zero", domain=k)
    eqs["INC_fug_zero"][k].where[~k.sameAs("CH4") & ~k.sameAs("N2O")] = M_var["39", k] == 0

    eqs["INC_flue_CO2"] = Equation(m, name="INC_flue_CO2")
    eqs["INC_flue_CO2"][...] = M_var["40", "CO2"] == 44.01 * nCO2_inc

    eqs["INC_flue_H2O"] = Equation(m, name="INC_flue_H2O")
    eqs["INC_flue_H2O"][...] = M_var["40", "WATER"] == M_var["38", "WATER"] + 18.015 * nH2O_inc

    eqs["INC_flue_SO2"] = Equation(m, name="INC_flue_SO2")
    eqs["INC_flue_SO2"][...] = M_var["40", "SO2"] == 64.06 * nSO2_inc

    eqs["INC_flue_O2"] = Equation(m, name="INC_flue_O2")
    eqs["INC_flue_O2"][...] = M_var["40", "O2"] == 32.00 * nO2_out

    eqs["INC_flue_N2"] = Equation(m, name="INC_flue_N2")
    eqs["INC_flue_N2"][...] = M_var["40", "N2"] == 28.0134 * nN2_out

    eqs["INC_flue_zero"] = Equation(m, name="INC_flue_zero", domain=k)
    eqs["INC_flue_zero"][k].where[
        ~k.sameAs("CO2") & ~k.sameAs("WATER") & ~k.sameAs("SO2") &
        ~k.sameAs("O2") & ~k.sameAs("N2")
    ] = M_var["40", k] == 0

    eqs["INC_mflue"] = Equation(m, name="INC_mflue")
    eqs["INC_mflue"][...] = mflue_inc == (M_var["40", "CO2"] + M_var["40", "WATER"] +
                                           M_var["40", "SO2"] + M_var["40", "O2"] +
                                           M_var["40", "N2"])

    eqs["INC_capacity"] = Equation(m, name="INC_capacity")
    eqs["INC_capacity"][...] = Qc["INC"] == Sum(k, M_var["38", k])

    eqs["INC_power"] = Equation(m, name="INC_power")
    eqs["INC_power"][...] = PW["INC"] == params["Wsp"]["INC"] * Qc["INC"]

    eqs["Mstm_INC_zero"] = Equation(m, name="Mstm_INC_zero")
    eqs["Mstm_INC_zero"][...] = Mstm["INC"] == 0

    eqs["Mcw_INC_zero"] = Equation(m, name="Mcw_INC_zero")
    eqs["Mcw_INC_zero"][...] = Mcw["INC"] == 0

    eqs["Mprod_INC_zero"] = Equation(m, name="Mprod_INC_zero", domain=kp)
    eqs["Mprod_INC_zero"][kp] = Mprod["INC", kp] == 0

    # ================================================================
    # STAGE 3 — RECOVERY + GAS UPGRADING + STB
    # ================================================================

    # ── Mixer 3: AND + SLF biogas → stream 48 ──────────────────────
    eqs["Mxr3_bal"] = Equation(m, name="Mxr3_bal", domain=k)
    eqs["Mxr3_bal"][k] = M_var["48", k] == M_var["27", k] + M_var["30", k]

    # ── Splitter 4: HTL products → CEN or FLT ──────────────────────
    eqs["Spl4_bal"] = Equation(m, name="Spl4_bal", domain=k)
    eqs["Spl4_bal"][k] = M_var["22", k] == M_var["41", k] + M_var["44", k]

    eqs["Spl4_CEN_cap"] = Equation(m, name="Spl4_CEN_cap", domain=k)
    eqs["Spl4_CEN_cap"][k] = M_var["41", k] <= MM * yHTLrec["CEN"]

    eqs["Spl4_FLT_cap"] = Equation(m, name="Spl4_FLT_cap", domain=k)
    eqs["Spl4_FLT_cap"][k] = M_var["44", k] <= MM * yHTLrec["FLT"]

    eqs["HTLrec_choose"] = Equation(m, name="HTLrec_choose")
    eqs["HTLrec_choose"][...] = Sum(iHTLrec, yHTLrec[iHTLrec]) == yConv["HTL"]

    # ── CEN ────────────────────────────────────────────────────────
    eqs["CEN_bal"] = Equation(m, name="CEN_bal", domain=k)
    eqs["CEN_bal"][k] = M_var["41", k] == M_var["42", k] + M_var["43", k]

    eqs["CEN_liq_BIOCRUDE"] = Equation(m, name="CEN_liq_BIOCRUDE")
    eqs["CEN_liq_BIOCRUDE"][...] = M_var["43", "BIOCRUDE"] == Eff_CNT * M_var["41", "BIOCRUDE"]

    eqs["CEN_liq_AQUEOUS"] = Equation(m, name="CEN_liq_AQUEOUS")
    eqs["CEN_liq_AQUEOUS"][...] = M_var["43", "AQUEOUS_PHASE"] == Eff_CNT * M_var["41", "AQUEOUS_PHASE"]

    eqs["CEN_liq_CHAR_zero"] = Equation(m, name="CEN_liq_CHAR_zero")
    eqs["CEN_liq_CHAR_zero"][...] = M_var["43", "CHAR"] == 0

    eqs["CEN_cake_CHAR"] = Equation(m, name="CEN_cake_CHAR")
    eqs["CEN_cake_CHAR"][...] = M_var["42", "CHAR"] == Eff_CNT * M_var["41", "CHAR"]

    eqs["CEN_cake_BIOCRUDE_zero"] = Equation(m, name="CEN_cake_BIOCRUDE_zero")
    eqs["CEN_cake_BIOCRUDE_zero"][...] = M_var["42", "BIOCRUDE"] == 0

    eqs["CEN_cake_AQUEOUS_zero"] = Equation(m, name="CEN_cake_AQUEOUS_zero")
    eqs["CEN_cake_AQUEOUS_zero"][...] = M_var["42", "AQUEOUS_PHASE"] == 0

    eqs["CEN_41_zero"] = Equation(m, name="CEN_41_zero", domain=k)
    eqs["CEN_41_zero"][k].where[
        ~k.sameAs("BIOCRUDE") & ~k.sameAs("CHAR") & ~k.sameAs("AQUEOUS_PHASE")
    ] = M_var["41", k] == 0

    eqs["CEN_42_zero"] = Equation(m, name="CEN_42_zero", domain=k)
    eqs["CEN_42_zero"][k].where[
        ~k.sameAs("BIOCRUDE") & ~k.sameAs("CHAR") & ~k.sameAs("AQUEOUS_PHASE")
    ] = M_var["42", k] == 0

    eqs["CEN_43_zero"] = Equation(m, name="CEN_43_zero", domain=k)
    eqs["CEN_43_zero"][k].where[
        ~k.sameAs("BIOCRUDE") & ~k.sameAs("CHAR") & ~k.sameAs("AQUEOUS_PHASE")
    ] = M_var["43", k] == 0

    eqs["CEN_CF_eq"] = Equation(m, name="CEN_CF_eq")
    eqs["CEN_CF_eq"][...] = (CF["CEN"] * (M_var["42", "CHAR"] / Den["CHAR"]) ==
                             M_var["41", "BIOCRUDE"] / Den["BIOCRUDE"] +
                             M_var["41", "CHAR"]     / Den["CHAR"] +
                             M_var["41", "AQUEOUS_PHASE"] / Den["AQUEOUS_PHASE"])

    eqs["CEN_sigma"] = Equation(m, name="CEN_sigma")
    eqs["CEN_sigma"][...] = (Qc["CEN"] * U["CEN"] ==
                             M_var["41", "BIOCRUDE"] / Den["BIOCRUDE"] +
                             M_var["41", "CHAR"]     / Den["CHAR"] +
                             M_var["41", "AQUEOUS_PHASE"] / Den["AQUEOUS_PHASE"])

    eqs["CEN_power"] = Equation(m, name="CEN_power")
    eqs["CEN_power"][...] = (PW["CEN"] ==
                             params["Wsp"]["CEN"] * (M_var["41", "BIOCRUDE"] / Den["BIOCRUDE"] +
                                                     M_var["41", "CHAR"]     / Den["CHAR"] +
                                                     M_var["41", "AQUEOUS_PHASE"] / Den["AQUEOUS_PHASE"]))

    eqs["CEN_cw"] = Equation(m, name="CEN_cw")
    eqs["CEN_cw"][...] = Mcw["CEN"] * Cp_water * (Tcw_out - Tcw_in) == 0.4 * PW["CEN"] * 3600

    eqs["Mstm_CEN_zero"] = Equation(m, name="Mstm_CEN_zero")
    eqs["Mstm_CEN_zero"][...] = Mstm["CEN"] == 0

    eqs["Mprod_CEN_zero"] = Equation(m, name="Mprod_CEN_zero", domain=kp)
    eqs["Mprod_CEN_zero"][kp] = Mprod["CEN", kp] == 0

    # ── FLT ────────────────────────────────────────────────────────
    eqs["FLT_44_zero"] = Equation(m, name="FLT_44_zero", domain=k)
    eqs["FLT_44_zero"][k].where[
        ~k.sameAs("BIOCRUDE") & ~k.sameAs("CHAR") & ~k.sameAs("AQUEOUS_PHASE")
    ] = M_var["44", k] == 0

    eqs["FLT_ret_BIOCRUDE"] = Equation(m, name="FLT_ret_BIOCRUDE")
    eqs["FLT_ret_BIOCRUDE"][...] = M_var["45", "BIOCRUDE"] == RFLT["BIOCRUDE"] * M_var["44", "BIOCRUDE"]

    eqs["FLT_ret_CHAR"] = Equation(m, name="FLT_ret_CHAR")
    eqs["FLT_ret_CHAR"][...] = M_var["45", "CHAR"] == RFLT["CHAR"] * M_var["44", "CHAR"]

    eqs["FLT_ret_AQUEOUS"] = Equation(m, name="FLT_ret_AQUEOUS")
    eqs["FLT_ret_AQUEOUS"][...] = (M_var["45", "AQUEOUS_PHASE"] ==
                                   RFLT["AQUEOUS_PHASE"] * M_var["44", "AQUEOUS_PHASE"])

    eqs["FLT_45_zero"] = Equation(m, name="FLT_45_zero", domain=k)
    eqs["FLT_45_zero"][k].where[
        ~k.sameAs("BIOCRUDE") & ~k.sameAs("CHAR") & ~k.sameAs("AQUEOUS_PHASE")
    ] = M_var["45", k] == 0

    eqs["FLT_perm_BIOCRUDE"] = Equation(m, name="FLT_perm_BIOCRUDE")
    eqs["FLT_perm_BIOCRUDE"][...] = (M_var["46", "BIOCRUDE"] ==
                                     (1 - RFLT["BIOCRUDE"]) * M_var["44", "BIOCRUDE"])

    eqs["FLT_perm_CHAR"] = Equation(m, name="FLT_perm_CHAR")
    eqs["FLT_perm_CHAR"][...] = M_var["46", "CHAR"] == (1 - RFLT["CHAR"]) * M_var["44", "CHAR"]

    eqs["FLT_perm_AQUEOUS"] = Equation(m, name="FLT_perm_AQUEOUS")
    eqs["FLT_perm_AQUEOUS"][...] = (M_var["46", "AQUEOUS_PHASE"] ==
                                    (1 - RFLT["AQUEOUS_PHASE"]) * M_var["44", "AQUEOUS_PHASE"])

    eqs["FLT_46_zero"] = Equation(m, name="FLT_46_zero", domain=k)
    eqs["FLT_46_zero"][k].where[
        ~k.sameAs("BIOCRUDE") & ~k.sameAs("CHAR") & ~k.sameAs("AQUEOUS_PHASE")
    ] = M_var["46", k] == 0

    eqs["FLT_bal"] = Equation(m, name="FLT_bal", domain=k)
    eqs["FLT_bal"][k] = M_var["44", k] == M_var["45", k] + M_var["46", k]

    eqs["FLT_CF_eq"] = Equation(m, name="FLT_CF_eq")
    eqs["FLT_CF_eq"][...] = (CF["FLT"] * (M_var["45", "BIOCRUDE"] / Den["BIOCRUDE"] +
                                           M_var["45", "CHAR"]     / Den["CHAR"] +
                                           M_var["45", "AQUEOUS_PHASE"] / Den["AQUEOUS_PHASE"]) ==
                             M_var["44", "BIOCRUDE"] / Den["BIOCRUDE"] +
                             M_var["44", "CHAR"]     / Den["CHAR"] +
                             M_var["44", "AQUEOUS_PHASE"] / Den["AQUEOUS_PHASE"])

    eqs["FLT_flux"] = Equation(m, name="FLT_flux")
    eqs["FLT_flux"][...] = (Zeta["FLT"] * Qc["FLT"] ==
                            (M_var["44", "BIOCRUDE"] / Den["BIOCRUDE"] +
                             M_var["44", "CHAR"]     / Den["CHAR"] +
                             M_var["44", "AQUEOUS_PHASE"] / Den["AQUEOUS_PHASE"]) *
                            (1 - 1 / CF["FLT"]))

    eqs["FLT_power"] = Equation(m, name="FLT_power")
    eqs["FLT_power"][...] = PW["FLT"] == params["Wsp"]["FLT"] * Qc["FLT"]

    eqs["Mstm_FLT_zero"] = Equation(m, name="Mstm_FLT_zero")
    eqs["Mstm_FLT_zero"][...] = Mstm["FLT"] == 0

    eqs["Mcw_FLT_zero"] = Equation(m, name="Mcw_FLT_zero")
    eqs["Mcw_FLT_zero"][...] = Mcw["FLT"] == 0

    eqs["Mprod_FLT_zero"] = Equation(m, name="Mprod_FLT_zero", domain=kp)
    eqs["Mprod_FLT_zero"][kp] = Mprod["FLT", kp] == 0

    # ── Mixer 4: CEN + FLT → biocrude product (stream 47) ──────────
    eqs["Mxr4_bal"] = Equation(m, name="Mxr4_bal", domain=k)
    eqs["Mxr4_bal"][k] = M_var["47", k] == M_var["43", k] + M_var["46", k]

    eqs["HTL_biocrude_prod"] = Equation(m, name="HTL_biocrude_prod")
    eqs["HTL_biocrude_prod"][...] = Mprod["HTL", "BIOCRUDE"] == M_var["47", "BIOCRUDE"]

    # ── Splitter 5: biogas → ABS or PSA ────────────────────────────
    eqs["Spl5_bal"] = Equation(m, name="Spl5_bal", domain=k)
    eqs["Spl5_bal"][k] = M_var["48", k] == M_var["49", k] + M_var["53", k]

    eqs["Spl5_ABS_cap"] = Equation(m, name="Spl5_ABS_cap", domain=k)
    eqs["Spl5_ABS_cap"][k] = M_var["49", k] <= MM * yGasUpg["ABS"]

    eqs["Spl5_PSA_cap"] = Equation(m, name="Spl5_PSA_cap", domain=k)
    eqs["Spl5_PSA_cap"][k] = M_var["53", k] <= MM * yGasUpg["PSA"]

    eqs["GasUpg_choose"] = Equation(m, name="GasUpg_choose")
    eqs["GasUpg_choose"][...] = Sum(iGasUpg, yGasUpg[iGasUpg]) == yConv["AND"] + yConv["SLF"]

    # ── ABS ────────────────────────────────────────────────────────
    eqs["ABS_zero_49"] = Equation(m, name="ABS_zero_49", domain=k)
    eqs["ABS_zero_49"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["49", k] == 0

    eqs["ABS_CH4_prod"] = Equation(m, name="ABS_CH4_prod")
    eqs["ABS_CH4_prod"][...] = M_var["52", "CH4"] == (1 - slipCH4_ABS) * M_var["49", "CH4"]

    eqs["ABS_CO2_prod"] = Equation(m, name="ABS_CO2_prod")
    eqs["ABS_CO2_prod"][...] = M_var["52", "CO2"] == (1 - etaCO2_ABS) * M_var["49", "CO2"]

    eqs["ABS_zero_52"] = Equation(m, name="ABS_zero_52", domain=k)
    eqs["ABS_zero_52"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["52", k] == 0

    eqs["ABS_CH4_off"] = Equation(m, name="ABS_CH4_off")
    eqs["ABS_CH4_off"][...] = M_var["51", "CH4"] == slipCH4_ABS * M_var["49", "CH4"]

    eqs["ABS_CO2_off"] = Equation(m, name="ABS_CO2_off")
    eqs["ABS_CO2_off"][...] = M_var["51", "CO2"] == etaCO2_ABS * M_var["49", "CO2"]

    eqs["ABS_zero_51"] = Equation(m, name="ABS_zero_51", domain=k)
    eqs["ABS_zero_51"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["51", k] == 0

    eqs["ABS_water_50"] = Equation(m, name="ABS_water_50")
    eqs["ABS_water_50"][...] = (M_var["50", "WATER"] ==
                                r_water_ABS * etaCO2_ABS * M_var["49", "CO2"])

    eqs["ABS_zero_50"] = Equation(m, name="ABS_zero_50", domain=k)
    eqs["ABS_zero_50"][k].where[~k.sameAs("WATER")] = M_var["50", k] == 0

    eqs["ABS_cap"] = Equation(m, name="ABS_cap")
    eqs["ABS_cap"][...] = (Qc["ABS"] ==
                           Vm_STP * (M_var["49", "CH4"] / MW_CH4 +
                                     M_var["49", "CO2"] / MW_CO2_AND))

    eqs["ABS_power"] = Equation(m, name="ABS_power")
    eqs["ABS_power"][...] = PW["ABS"] == e_el_ABS * Qc["ABS"]

    eqs["ABS_purity"] = Equation(m, name="ABS_purity")
    eqs["ABS_purity"][...] = ((1 - Pur_CH4) * (M_var["52", "CH4"] / MW_CH4) >=
                              Pur_CH4 * (M_var["52", "CO2"] / MW_CO2_AND))

    eqs["Mstm_ABS_zero"] = Equation(m, name="Mstm_ABS_zero")
    eqs["Mstm_ABS_zero"][...] = Mstm["ABS"] == 0

    eqs["Mcw_ABS_zero"] = Equation(m, name="Mcw_ABS_zero")
    eqs["Mcw_ABS_zero"][...] = Mcw["ABS"] == 0

    eqs["ABS_CH4_mprod"] = Equation(m, name="ABS_CH4_mprod")
    eqs["ABS_CH4_mprod"][...] = Mprod["ABS", "CH4"] == M_var["52", "CH4"]

    eqs["ABS_nonprod_zero"] = Equation(m, name="ABS_nonprod_zero", domain=kp)
    eqs["ABS_nonprod_zero"][kp].where[~kp.sameAs("CH4")] = Mprod["ABS", kp] == 0

    # ── PSA ────────────────────────────────────────────────────────
    eqs["PSA_zero_53"] = Equation(m, name="PSA_zero_53", domain=k)
    eqs["PSA_zero_53"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["53", k] == 0

    eqs["PSA_CH4_prod"] = Equation(m, name="PSA_CH4_prod")
    eqs["PSA_CH4_prod"][...] = M_var["55", "CH4"] == (1 - slipCH4_PSA) * M_var["53", "CH4"]

    eqs["PSA_CO2_prod"] = Equation(m, name="PSA_CO2_prod")
    eqs["PSA_CO2_prod"][...] = M_var["55", "CO2"] == (1 - etaCO2_PSA) * M_var["53", "CO2"]

    eqs["PSA_zero_55"] = Equation(m, name="PSA_zero_55", domain=k)
    eqs["PSA_zero_55"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["55", k] == 0

    eqs["PSA_CH4_off"] = Equation(m, name="PSA_CH4_off")
    eqs["PSA_CH4_off"][...] = M_var["54", "CH4"] == slipCH4_PSA * M_var["53", "CH4"]

    eqs["PSA_CO2_off"] = Equation(m, name="PSA_CO2_off")
    eqs["PSA_CO2_off"][...] = M_var["54", "CO2"] == etaCO2_PSA * M_var["53", "CO2"]

    eqs["PSA_zero_54"] = Equation(m, name="PSA_zero_54", domain=k)
    eqs["PSA_zero_54"][k].where[~k.sameAs("CH4") & ~k.sameAs("CO2")] = M_var["54", k] == 0

    eqs["PSA_cap"] = Equation(m, name="PSA_cap")
    eqs["PSA_cap"][...] = (Qc["PSA"] ==
                           Vm_STP * (M_var["53", "CH4"] / MW_CH4 +
                                     M_var["53", "CO2"] / MW_CO2_AND))

    eqs["PSA_power"] = Equation(m, name="PSA_power")
    eqs["PSA_power"][...] = PW["PSA"] == e_el_PSA * Qc["PSA"]

    eqs["Mstm_PSA_zero"] = Equation(m, name="Mstm_PSA_zero")
    eqs["Mstm_PSA_zero"][...] = Mstm["PSA"] == 0

    eqs["Mcw_PSA_zero"] = Equation(m, name="Mcw_PSA_zero")
    eqs["Mcw_PSA_zero"][...] = Mcw["PSA"] == 0

    eqs["PSA_CH4_mprod"] = Equation(m, name="PSA_CH4_mprod")
    eqs["PSA_CH4_mprod"][...] = Mprod["PSA", "CH4"] == M_var["55", "CH4"]

    eqs["PSA_nonprod_zero"] = Equation(m, name="PSA_nonprod_zero", domain=kp)
    eqs["PSA_nonprod_zero"][kp].where[~kp.sameAs("CH4")] = Mprod["PSA", kp] == 0

    # ── Mixer 5: ABS + PSA → biomethane (stream 56) ────────────────
    eqs["Mxr5_bal"] = Equation(m, name="Mxr5_bal", domain=k)
    eqs["Mxr5_bal"][k] = M_var["56", k] == M_var["52", k] + M_var["55", k]

    eqs["CH4_prod_eq"] = Equation(m, name="CH4_prod_eq")
    eqs["CH4_prod_eq"][...] = Mprod["ABS", "CH4"] + Mprod["PSA", "CH4"] == M_var["56", "CH4"]

    # ── STB ────────────────────────────────────────────────────────
    eqs["STB_link"] = Equation(m, name="STB_link")
    eqs["STB_link"][...] = ySTB == yConv["INC"]

    eqs["STB_HE_balance_ge"] = Equation(m, name="STB_HE_balance_ge")
    eqs["STB_HE_balance_ge"][...] = (mflue_inc * CP_g * (T_g_in - T_g_out) +
                                     MM_ST * (1 - ySTB) >=
                                     M_var["59", "WATER"] * (H2_steam - H1_water))

    eqs["STB_HE_balance_le"] = Equation(m, name="STB_HE_balance_le")
    eqs["STB_HE_balance_le"][...] = (mflue_inc * CP_g * (T_g_in - T_g_out) <=
                                     M_var["59", "WATER"] * (H2_steam - H1_water) +
                                     MM_ST * (1 - ySTB))

    eqs["STB_BFW_zero"] = Equation(m, name="STB_BFW_zero", domain=k)
    eqs["STB_BFW_zero"][k].where[~k.sameAs("WATER")] = M_var["59", k] == 0

    eqs["STB_BFW_cap"] = Equation(m, name="STB_BFW_cap")
    eqs["STB_BFW_cap"][...] = M_var["59", "WATER"] <= MM_ST * ySTB

    eqs["STB_steam_bal"] = Equation(m, name="STB_steam_bal")
    eqs["STB_steam_bal"][...] = M_var["60", "WATER"] == M_var["59", "WATER"]

    eqs["STB_steam_zero"] = Equation(m, name="STB_steam_zero", domain=k)
    eqs["STB_steam_zero"][k].where[~k.sameAs("WATER")] = M_var["60", k] == 0

    eqs["STB_turb_power"] = Equation(m, name="STB_turb_power")
    eqs["STB_turb_power"][...] = P_turbine == M_var["60", "WATER"] * (h1_value - h2_value)

    eqs["STB_P_cap"] = Equation(m, name="STB_P_cap")
    eqs["STB_P_cap"][...] = P_turbine <= MM_ST * ySTB

    eqs["STB_elec_cap"] = Equation(m, name="STB_elec_cap")
    eqs["STB_elec_cap"][...] = Qc["STB"] == eta_turbine * eta_generator * P_turbine / 3600

    eqs["STB_Qc_cap"] = Equation(m, name="STB_Qc_cap")
    eqs["STB_Qc_cap"][...] = Qc["STB"] <= MM_ST * ySTB

    eqs["STB_power"] = Equation(m, name="STB_power")
    eqs["STB_power"][...] = PW["STB"] == params["Wsp"]["STB"] * Qc["STB"]

    eqs["STB_elec_stream"] = Equation(m, name="STB_elec_stream")
    eqs["STB_elec_stream"][...] = M_var["57", "ELECTRICITY"] == Qc["STB"]

    eqs["STB_zero_57"] = Equation(m, name="STB_zero_57", domain=k)
    eqs["STB_zero_57"][k].where[~k.sameAs("ELECTRICITY")] = M_var["57", k] == 0

    return eqs
