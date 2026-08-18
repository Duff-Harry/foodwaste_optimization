"""
tests/test_sanity.py
=====================
Quick sanity check for the food waste optimization model.

Runs a single fast "Lowest Cost" solve and checks that the
cost and GHG sub-totals are internally consistent (i.e. the
component breakdown actually adds up to the reported totals).

This will NOT catch every possible modeling error, but it
catches the class of bug found during the model audit
(mismatched signs, double counting, components that don't
sum to the totals shown in the UI).

Run with:
    py -3.12 tests/test_sanity.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.solver import run_optimization

TOL = 1e-3


def check(name, lhs, rhs, tol=TOL):
    diff = abs(lhs - rhs)
    status = "PASS" if diff <= tol else "FAIL"
    print(f"  [{status}] {name}: {lhs:.6f} vs {rhs:.6f} (diff={diff:.6f})")
    return status == "PASS"


def main():
    user_inputs = {
        "Qf": 1000, "Tann": 7920,
        "composition": {
            "WATER": 0.75952, "CBH": 0.016745, "PRT": 0.108027,
            "FAT": 0.046492, "OTH": 0.020929, "ASH": 0.012427,
            "FIXED_CARBON": 0.035360,
        },
        "C_elec": 0.1, "C_tip": 0.08, "C_lbr": 30, "CRF": 0.11,
        "n_pareto_pts": 1, "time_limit": 120, "gap": 0.05,
        "objective": "Lowest Cost Pathway",
    }

    result = run_optimization(user_inputs)

    if result["status"] != "success":
        print(f"FAIL: optimization did not succeed: {result['message']}")
        sys.exit(1)

    row = result["pareto_df"].iloc[0]

    print(f"\nSolved pathway: {row['Conv']} + {row['Bio']} + {row['Mech']}  "
          f"(NAC={row['NAC']}, GHG={row['GHG']})\n")

    all_ok = True

    # Cost components must add up to CCTC
    cctc_sum = (row["CCAC"] + row["CCWC"] + row["CCINS"] + row["CCUC"] +
                row["CCLB"] + row["CCOC"] + row["CCRM"] + row["CDISP"])
    all_ok &= check("CCTC == sum(cost components)", row["CCTC"], cctc_sum)

    # NAC must equal CCTC - REV
    all_ok &= check("NAC == CCTC - REV", row["NAC"], row["CCTC"] - row["REV"])

    # GHG components must add up to GHG_total
    ghg_sum = row["GHG_IND"] + row["GHG_DIR"] + row["GHG_AQ"] - row["GHG_DISP"]
    all_ok &= check("GHG == GHG_IND + GHG_DIR + GHG_AQ - GHG_DISP", row["GHG"], ghg_sum, tol=0.5)

    print()
    if all_ok:
        print("ALL CHECKS PASSED")
    else:
        print("SOME CHECKS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
