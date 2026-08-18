"""
model/solver.py
===============
Solver and Pareto optimization for the food waste model.

Sections:
    A. Helper functions
    B. Model builder — assembles all sections
    C. Diagnostic solver — tests all technology combinations
    D. Pareto solver — epsilon constraint method
    E. run_optimization() — main entry point for the app
"""

from gamspy import (Container, Model, Sense, Options,
                    Equation, Parameter)
import pandas as pd
import numpy as np

from model.sets       import build_sets
from model.parameters import build_all_parameters
from model.variables  import build_variables
from model.equations  import build_equations
from model.costing    import build_costing
from model.ghg        import build_ghg


# ============================================================
# SECTION A — HELPER FUNCTIONS
# ============================================================

def get_value(var):
    """Safely extract scalar value from a GAMSPy variable."""
    try:
        return var.toValue()
    except:
        return float(var.records["level"].iloc[0])


def get_binary(var, key):
    """Safely extract binary variable value by key."""
    try:
        df = var.records
        if df is None:
            return 0
        row = df[df.iloc[:, 0] == key]
        return float(row["level"].values[0]) if len(row) > 0 else 0
    except:
        return 0


def get_config_labels(vars):
    """Return selected technology configuration as strings."""
    yConv    = vars["yConv"]
    yBio     = vars["yBio"]
    yBYP_bio = vars["yBYP_bio"]
    yS1      = vars["yS1"]
    yBYP1    = vars["yBYP1"]
    yBYP2    = vars["yBYP2"]
    yHTLrec  = vars["yHTLrec"]
    yGasUpg  = vars["yGasUpg"]
    ySTB     = vars["ySTB"]

    conv   = next((t for t in ["HTL", "AND", "SLF", "CMP", "WWT", "INC"]
                   if get_binary(yConv, t) > 0.5), "?")
    bio    = ("AER"     if get_binary(yBio, "AER") > 0.5 else
              "ENZ"     if get_binary(yBio, "ENZ") > 0.5 else
              "BYP_bio" if get_value(yBYP_bio)     > 0.5 else "(none)")
    mech   = ("SHR"  if get_binary(yS1, "SHR") > 0.5 else
              "MCR"  if get_binary(yS1, "MCR") > 0.5 else
              "BYP1" if get_value(yBYP1)        > 0.5 else
              "BYP2" if get_value(yBYP2)        > 0.5 else "?")
    htlrec = ("CEN" if get_binary(yHTLrec, "CEN") > 0.5 else
              "FLT" if get_binary(yHTLrec, "FLT") > 0.5 else "-")
    gasupg = ("ABS" if get_binary(yGasUpg, "ABS") > 0.5 else
              "PSA" if get_binary(yGasUpg, "PSA") > 0.5 else "-")
    stb    = "STB" if get_value(ySTB) > 0.5 else "-"
    return conv, bio, mech, htlrec, gasupg, stb


def unfix_all(vars):
    """Release all binary variable bounds."""
    yConv    = vars["yConv"]
    yBio     = vars["yBio"]
    yBYP_bio = vars["yBYP_bio"]
    yS1      = vars["yS1"]
    yBYP1    = vars["yBYP1"]
    yBYP2    = vars["yBYP2"]
    yHTLrec  = vars["yHTLrec"]
    yGasUpg  = vars["yGasUpg"]
    ySTB     = vars["ySTB"]

    for t in ["HTL", "AND", "SLF", "CMP", "WWT", "INC"]:
        yConv.lo[t] = 0;    yConv.up[t] = 1
    for b in ["AER", "ENZ"]:
        yBio.lo[b] = 0;     yBio.up[b] = 1
    yBYP_bio.lo = 0;        yBYP_bio.up = 1
    yS1.lo["SHR"] = 0;      yS1.up["SHR"] = 1
    yS1.lo["MCR"] = 0;      yS1.up["MCR"] = 1
    yBYP1.lo = 0;           yBYP1.up = 1
    yBYP2.lo = 0;           yBYP2.up = 1
    yHTLrec.lo["CEN"] = 0;  yHTLrec.up["CEN"] = 1
    yHTLrec.lo["FLT"] = 0;  yHTLrec.up["FLT"] = 1
    yGasUpg.lo["ABS"] = 0;  yGasUpg.up["ABS"] = 1
    yGasUpg.lo["PSA"] = 0;  yGasUpg.up["PSA"] = 1
    ySTB.lo = 0;            ySTB.up = 1


def extract_row(vars, label, eps, status):
    """Extract all cost/config values from current solver solution."""
    conv, bio, mech, htlrec, gasupg, stb = get_config_labels(vars)
    return {
        "Pareto_pt": label,
        "eps_GHG":   round(eps, 1),
        "Conv":      conv,  "Bio": bio, "Mech": mech,
        "HTLrec":    htlrec, "GasUpg": gasupg, "STB": stb,
        "NAC":       round(get_value(vars["NAC"]),           4),
        "GHG":       round(get_value(vars["GHG_total_tpy"]), 1),
        "CCAC":      round(get_value(vars["CCAC"]),  4),
        "CCWC":      round(get_value(vars["CCWC"]),  4),
        "CCINS":     round(get_value(vars["CCINS"]), 4),
        "CCUC":      round(get_value(vars["CCUC"]),  4),
        "CCLB":      round(get_value(vars["CCLB"]),  4),
        "CCOC":      round(get_value(vars["CCOC"]),  4),
        "CCRM":      round(get_value(vars["CCRM"]),  4),
        "CDISP":     round(get_value(vars["CDISP"]), 4),
        "CTIP":      round(get_value(vars["CTIP"]),  4),
        "REV":       round(get_value(vars["REV"]),   4),
        "CCTC":      round(get_value(vars["CCTC"]),  4),
        "GHG_IND":   round(get_value(vars["GHG_ind_tpy"]),   1),
        "GHG_DIR":   round(get_value(vars["GHG_dir_total"]), 1),
        "GHG_AQ":    round(get_value(vars["GHG_aq"]),        1),
        "GHG_DISP":  round(get_value(vars["GHG_disp"]),      1),
        "Status":    status,
    }


# ============================================================
# SECTION B — MODEL BUILDER
# ============================================================

def build_model(user_inputs: dict) -> tuple:
    m = Container()
    sets   = build_sets(m)
    params = build_all_parameters(m, sets, user_inputs)
    vars   = build_variables(m, sets, params)
    eqs    = {}
    eqs.update(build_equations(m, sets, params, vars))
    eqs.update(build_costing(m, sets, params, vars))
    eqs.update(build_ghg(m, sets, params, vars))

    delta = Parameter(m, name="delta", records=1e-6)
    aug_obj_eq = Equation(m, name="aug_obj_eq")
    aug_obj_eq[...] = vars["obj"] == vars["NAC"] + delta * vars["GHG_total_tpy"]
    eqs["aug_obj_eq"] = aug_obj_eq

    return m, sets, params, vars, eqs


# ============================================================
# SECTION C — DIAGNOSTIC SOLVER
# ============================================================

def run_diagnostic(user_inputs: dict,
                   time_limit: int = 120,
                   gap: float = 0.05) -> pd.DataFrame:
    m, sets, params, vars, eqs = build_model(user_inputs)
    solver_opts = Options(time_limit=time_limit, relative_optimality_gap=gap)

    NAC           = vars["NAC"]
    GHG_total_tpy = vars["GHG_total_tpy"]
    yConv         = vars["yConv"]
    yBio          = vars["yBio"]
    yBYP_bio      = vars["yBYP_bio"]
    yS1           = vars["yS1"]
    yBYP1         = vars["yBYP1"]
    yBYP2         = vars["yBYP2"]
    yHTLrec       = vars["yHTLrec"]
    yGasUpg       = vars["yGasUpg"]
    ySTB          = vars["ySTB"]

    conv_techs = ["HTL", "AND", "SLF", "CMP", "WWT", "INC"]
    bio_list   = ["AER", "ENZ", "BYP_bio"]
    mech_list  = ["SHR", "MCR", "BYP1", "BYP2"]
    results    = []

    for conv in conv_techs:
        for bio in bio_list:
            for mech in mech_list:
                if conv in ["HTL", "AND"] and mech in ["BYP1", "BYP2"]:
                    continue
                if conv == "CMP" and (mech != "SHR" or bio != "BYP_bio"):
                    continue
                if conv == "SLF" and mech != "BYP2":
                    continue
                if conv == "INC" and mech != "BYP2":
                    continue
                if conv == "WWT" and (bio != "AER" or mech == "BYP2"):
                    continue
                if mech == "BYP2" and bio != bio_list[0]:
                    continue

                unfix_all(vars)
                for t in conv_techs:
                    yConv.fx[t] = 1 if t == conv else 0
                if mech == "BYP2":
                    yBio.fx["AER"] = 0; yBio.fx["ENZ"] = 0; yBYP_bio.fx = 0
                else:
                    yBio.fx["AER"]  = 1 if bio == "AER"     else 0
                    yBio.fx["ENZ"]  = 1 if bio == "ENZ"     else 0
                    yBYP_bio.fx     = 1 if bio == "BYP_bio" else 0
                yS1.fx["SHR"] = 1 if mech == "SHR"  else 0
                yS1.fx["MCR"] = 1 if mech == "MCR"  else 0
                yBYP1.fx      = 1 if mech == "BYP1" else 0
                yBYP2.fx      = 1 if mech == "BYP2" else 0
                if conv == "HTL":
                    yHTLrec.lo["CEN"] = 0; yHTLrec.up["CEN"] = 1
                    yHTLrec.lo["FLT"] = 0; yHTLrec.up["FLT"] = 1
                else:
                    yHTLrec.lo["CEN"] = 0; yHTLrec.up["CEN"] = 0
                    yHTLrec.lo["FLT"] = 0; yHTLrec.up["FLT"] = 0
                if conv in ["AND", "SLF"]:
                    yGasUpg.lo["ABS"] = 0; yGasUpg.up["ABS"] = 1
                    yGasUpg.lo["PSA"] = 0; yGasUpg.up["PSA"] = 1
                else:
                    yGasUpg.lo["ABS"] = 0; yGasUpg.up["ABS"] = 0
                    yGasUpg.lo["PSA"] = 0; yGasUpg.up["PSA"] = 0
                ySTB.fx = 1 if conv == "INC" else 0

                bio_label = "(none)" if mech == "BYP2" else bio
                diag = Model(m, name=f"d_{conv}_{bio}_{mech}",
                             equations=m.getEquations(),
                             problem="MINLP", sense=Sense.MIN, objective=NAC)
                try:
                    diag.solve(solver="SBB", options=solver_opts)
                    stat = str(diag.status)
                except Exception as e:
                    stat = f"ERROR: {type(e).__name__}"

                if "Infeasible" not in stat and "ERROR" not in stat:
                    htlrec = ("CEN" if get_binary(yHTLrec, "CEN") > 0.5 else
                              "FLT" if get_binary(yHTLrec, "FLT") > 0.5 else "-")
                    gasupg = ("ABS" if get_binary(yGasUpg, "ABS") > 0.5 else
                              "PSA" if get_binary(yGasUpg, "PSA") > 0.5 else "-")
                    stb    = "STB" if get_value(ySTB) > 0.5 else "-"
                    results.append({
                        "Conv": conv, "Bio": bio_label, "Mech": mech,
                        "HTLrec": htlrec, "GasUpg": gasupg, "STB": stb,
                        "NAC": round(get_value(NAC), 4),
                        "GHG": round(get_value(GHG_total_tpy), 1),
                        "Status": stat
                    })
                else:
                    results.append({
                        "Conv": conv, "Bio": bio_label, "Mech": mech,
                        "HTLrec": "-", "GasUpg": "-", "STB": "-",
                        "NAC": None, "GHG": None, "Status": "Infeasible"
                    })

    unfix_all(vars)
    return pd.DataFrame(results)


# ============================================================
# SECTION D — PARETO SOLVER (epsilon constraint method)
# ============================================================

def run_pareto(user_inputs: dict,
               n_pts: int = 10,
               time_limit: int = 300,
               gap: float = 0.02,
               objective: str = "Lowest Cost & Emissions Pathway") -> dict:
    try:
        m, sets, params, vars, eqs = build_model(user_inputs)
        solver_opts = Options(time_limit=time_limit,
                              relative_optimality_gap=gap)

        NAC           = vars["NAC"]
        GHG_total_tpy = vars["GHG_total_tpy"]
        obj           = vars["obj"]

        # ── Lowest Cost only — minimise NAC and return ────────
        if objective == "Lowest Cost Pathway":
            print("=" * 60)
            print("ANCHOR A — minimise NAC")
            print("=" * 60)
            unfix_all(vars)

            mdl_A = Model(m, name="anchor_NAC",
                          equations=m.getEquations(),
                          problem="MINLP", sense=Sense.MIN, objective=NAC)
            mdl_A.solve(solver="SBB", options=solver_opts)

            NAC_min  = get_value(NAC)
            GHG_at_A = get_value(GHG_total_tpy)
            print(f"  Status: {mdl_A.status}  NAC={NAC_min:.4f}  GHG={GHG_at_A:.1f}")

            row = extract_row(vars, "p1", GHG_at_A, str(mdl_A.status))
            df  = pd.DataFrame([row])
            df.to_csv("pareto_results.csv", index=False)
            return {
                "status":    "success",
                "message":   "Lowest Cost Pathway optimized",
                "pareto_df": df,
                "NAC_min":   NAC_min,
                "GHG_min":   GHG_at_A,
            }

        # ── Lowest Emissions only — minimise GHG and return ───
        if objective == "Lowest Emissions Pathway":
            print("=" * 60)
            print("ANCHOR B — minimise GHG")
            print("=" * 60)
            unfix_all(vars)

            mdl_B = Model(m, name="anchor_GHG",
                          equations=m.getEquations(),
                          problem="MINLP", sense=Sense.MIN,
                          objective=GHG_total_tpy)
            mdl_B.solve(solver="SBB", options=solver_opts)

            GHG_min  = get_value(GHG_total_tpy)
            NAC_at_B = get_value(NAC)
            print(f"  Status: {mdl_B.status}  GHG={GHG_min:.1f}  NAC={NAC_at_B:.4f}")

            row = extract_row(vars, "p1", GHG_min, str(mdl_B.status))
            df  = pd.DataFrame([row])
            df.to_csv("pareto_results.csv", index=False)
            return {
                "status":    "success",
                "message":   "Lowest Emissions Pathway optimized",
                "pareto_df": df,
                "NAC_min":   NAC_at_B,
                "GHG_min":   GHG_min,
            }

        # ── Balanced — need both anchors for the eps-grid bounds ──
        print("=" * 60)
        print("ANCHOR A — minimise NAC")
        print("=" * 60)
        unfix_all(vars)

        mdl_A = Model(m, name="anchor_NAC",
                      equations=m.getEquations(),
                      problem="MINLP", sense=Sense.MIN, objective=NAC)
        mdl_A.solve(solver="SBB", options=solver_opts)

        NAC_min  = get_value(NAC)
        GHG_at_A = get_value(GHG_total_tpy)
        print(f"  Status: {mdl_A.status}  NAC={NAC_min:.4f}  GHG={GHG_at_A:.1f}")

        print("=" * 60)
        print("ANCHOR B — minimise GHG")
        print("=" * 60)
        unfix_all(vars)

        mdl_B = Model(m, name="anchor_GHG",
                      equations=m.getEquations(),
                      problem="MINLP", sense=Sense.MIN,
                      objective=GHG_total_tpy)
        mdl_B.solve(solver="SBB", options=solver_opts)

        GHG_min  = get_value(GHG_total_tpy)
        NAC_at_B = get_value(NAC)
        print(f"  Status: {mdl_B.status}  GHG={GHG_min:.1f}  NAC={NAC_at_B:.4f}")

        # ── Full Pareto — epsilon constraint sweep ────────────
        GHG_max_val = GHG_at_A + abs(GHG_at_A) * 0.001
        GHG_min_val = GHG_min  - abs(GHG_min)  * 0.001

        eps_grid = [
            GHG_max_val - (GHG_max_val - GHG_min_val) * i / (n_pts - 1)
            for i in range(n_pts)
        ]

        print("=" * 60)
        print(f"EPSILON SWEEP ({n_pts} points)")
        print("=" * 60)

        eps_con = Equation(m, name="eps_ghg_con",
                           description="GHG epsilon upper bound")
        pareto_rows = []

        for idx, eps_ghg in enumerate(eps_grid):
            pt_label = f"p{idx + 1}"
            unfix_all(vars)
            eps_con[...] = GHG_total_tpy <= eps_ghg

            mdl_pt = Model(m, name=f"pareto_{pt_label}",
                           equations=m.getEquations(),
                           problem="MINLP", sense=Sense.MIN, objective=obj)
            mdl_pt.solve(solver="SBB", options=solver_opts)

            status = str(mdl_pt.status)

            if "Infeasible" in status or "Error" in status:
                print(f"  {pt_label}  eps={eps_ghg:9.1f}  -> INFEASIBLE")
                pareto_rows.append({
                    "Pareto_pt": pt_label, "eps_GHG": round(eps_ghg, 1),
                    "Conv": None, "Bio": None, "Mech": None,
                    "HTLrec": None, "GasUpg": None, "STB": None,
                    "NAC": None, "GHG": None,
                    "CCAC": None, "CCWC": None, "CCINS": None,
                    "CCUC": None, "CCLB": None, "CCOC": None,
                    "CCRM": None, "CDISP": None, "CTIP": None,
                    "REV": None, "CCTC": None,
                    "GHG_IND": None, "GHG_DIR": None,
                    "GHG_AQ": None, "GHG_DISP": None,
                    "Status": status,
                })
                continue

            row = extract_row(vars, pt_label, eps_ghg, status)
            print(f"  {pt_label}  eps={eps_ghg:9.1f}  NAC={row['NAC']:7.3f}  GHG={row['GHG']:8.1f}  [{row['Conv']}+{row['Bio']}+{row['Mech']}]")
            pareto_rows.append(row)

        unfix_all(vars)

        df_pareto   = pd.DataFrame(pareto_rows)
        feasible_df = df_pareto[df_pareto["NAC"].notna()].copy()

        print("\n" + "=" * 60)
        print("PARETO FRONT — SUMMARY")
        print("=" * 60)
        print(feasible_df[["Pareto_pt","Conv","Bio","Mech","NAC","GHG","Status"]].to_string(index=False))

        df_pareto.to_csv("pareto_results.csv", index=False)
        print("\nSaved -> pareto_results.csv")

        return {
            "status":    "success",
            "message":   f"Pareto front computed: {len(feasible_df)} feasible points",
            "pareto_df": df_pareto,
            "NAC_min":   NAC_min,
            "GHG_min":   GHG_min,
        }

    except Exception as e:
        return {
            "status":    "error",
            "message":   str(e),
            "pareto_df": None,
            "NAC_min":   None,
            "GHG_min":   None,
        }


# ============================================================
# SECTION E — MAIN ENTRY POINT FOR APP
# ============================================================

def run_optimization(user_inputs: dict) -> dict:
    objective = user_inputs.get("objective", "Lowest Cost & Emissions Pathway")
    return run_pareto(
        user_inputs=user_inputs,
        n_pts=user_inputs.get("n_pareto_pts", 10),
        time_limit=user_inputs.get("time_limit", 300),
        gap=user_inputs.get("gap", 0.02),
        objective=objective,
    )


# ============================================================
# QUICK TEST
# ============================================================
if __name__ == "__main__":
    result = run_optimization({
        "Qf": 1000, "Tann": 7920,
        "composition": {
            "WATER": 0.75952, "CBH": 0.016745, "PRT": 0.108027,
            "FAT": 0.046492, "OTH": 0.020929, "ASH": 0.012427,
            "FIXED_CARBON": 0.035360,
        },
        "C_elec": 0.1, "C_tip": 0.08, "C_lbr": 30, "CRF": 0.11,
        "n_pareto_pts": 10, "time_limit": 300, "gap": 0.02,
        "objective": "Lowest Cost & Emissions Pathway",
    })
    print(result["message"])