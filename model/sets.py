"""
model/sets.py
=============
Defines all GAMSPy sets used in the food waste optimization model.

Sets:
    i       - Technology set (15 technologies)
    j       - Stream set (61 streams)
    k       - Component set (29 components)
    p       - Pareto points (10 points)

Sub-sets:
    i_mech  - Mechanical pretreatment technologies
    i_bio   - Biological pretreatment technologies
    iConv   - Conversion technologies
    iHTLrec - HTL recovery technologies
    iGasUpg - Gas upgrading technologies
    kp      - Product components
    kgas    - Gas components
    kADdig  - Anaerobic digestion components
    kADgas  - Anaerobic digestion gas components
    kHTL    - HTL product components
    kCPgas  - Composting gas components
    kCPcomp - Composting components
    kINCgas - Incineration gas components
    kINCflue- Incineration flue gas components
"""

from gamspy import Container, Set


def build_sets(m: Container) -> dict:
    """
    Build and return all sets for the optimization model.

    Parameters
    ----------
    m : Container
        GAMSPy model container

    Returns
    -------
    dict of all sets and subsets
    """

    # ── Main sets ──────────────────────────────────────────────────

    i = Set(
        m, name="i",
        description="Technology set",
        records=[
            "SHR",  # Shredder
            "MCR",  # Macerator
            "AER",  # Aerobic biodigester
            "ENZ",  # Enzymatic hydrolysis
            "HTL",  # Hydrothermal liquefaction
            "AND",  # Anaerobic digestion
            "SLF",  # Sanitary landfill
            "CMP",  # Composting
            "WWT",  # Wastewater treatment
            "INC",  # Incineration
            "CEN",  # Centrifuge
            "FLT",  # Filtration
            "ABS",  # Absorption (amine scrubbing)
            "PSA",  # Pressure swing adsorption
            "STB",  # Steam turbine
        ]
    )

    j = Set(
        m, name="j",
        description="Stream set (61 process streams)",
        records=[str(x) for x in range(1, 62)]
    )

    k = Set(
        m, name="k",
        description="Component set",
        records=[
            # Organic macronutrients
            "CBH",           # Carbohydrates
            "PRT",           # Protein
            "FAT",           # Fat / Lipid
            "OTH",           # Other organics
            # Inorganic
            "WATER",         # Water / Moisture
            "FIXED_CARBON",  # Fixed carbon
            "ASH",           # Ash (inorganic residue)
            # HTL products
            "BIOCRUDE",      # Biocrude oil
            "CHAR",          # Hydrochar
            "AQUEOUS_PHASE", # Aqueous phase
            "GAS_PRODUCT",   # HTL gas product
            # Biological products
            "COMPOST",       # Compost
            "ELECTRICITY",   # Electricity (kWh)
            # Reagents
            "AMINE",         # Amine scrubbing solution
            # Gases
            "CO2",           # Carbon dioxide
            "CH4",           # Methane / Biomethane
            "N2O",           # Nitrous oxide
            "SO2",           # Sulfur dioxide
            "N2",            # Nitrogen
            "O2",            # Oxygen
            "NH3",           # Ammonia
            # Elemental analysis
            "C",             # Carbon
            "H",             # Hydrogen
            "N",             # Nitrogen (elemental)
            "O",             # Oxygen (elemental)
            "S",             # Sulfur
            # Other products
            "BIOSOLIDS",     # Biosolids from WWT
            "ENZYME",        # Enzyme (ENZ process)
            "PH_CHEM",       # pH chemicals
        ]
    )

    p = Set(
        m, name="p",
        description="Pareto front points",
        records=[f"p{x}" for x in range(1, 11)]
    )

    # ── Technology sub-sets ─────────────────────────────────────────

    i_mech = Set(
        m, name="i_mech",
        domain=i,
        description="Mechanical pretreatment technologies",
        records=["SHR", "MCR"]
    )

    i_bio = Set(
        m, name="i_bio",
        domain=i,
        description="Biological pretreatment technologies",
        records=["AER", "ENZ"]
    )

    iConv = Set(
        m, name="iConv",
        domain=i,
        description="Conversion technologies",
        records=["HTL", "AND", "SLF", "CMP", "WWT", "INC"]
    )

    iHTLrec = Set(
        m, name="iHTLrec",
        domain=i,
        description="HTL product recovery technologies",
        records=["CEN", "FLT"]
    )

    iGasUpg = Set(
        m, name="iGasUpg",
        domain=i,
        description="Biogas upgrading technologies",
        records=["ABS", "PSA"]
    )

    # ── Component sub-sets ──────────────────────────────────────────

    kp = Set(
        m, name="kp",
        domain=k,
        description="Saleable product components",
        records=["CH4", "BIOCRUDE", "COMPOST", "ELECTRICITY", "BIOSOLIDS"]
    )

    kgas = Set(
        m, name="kgas",
        domain=k,
        description="Gas phase components",
        records=["CH4", "CO2", "N2O", "SO2", "N2", "O2", "NH3"]
    )

    kADdig = Set(
        m, name="kADdig",
        domain=k,
        description="Anaerobic digestion feed components",
        records=["CBH", "PRT", "FAT", "OTH", "WATER", "ASH", "FIXED_CARBON"]
    )

    kADgas = Set(
        m, name="kADgas",
        domain=k,
        description="Anaerobic digestion biogas components",
        records=["CH4", "CO2"]
    )

    kHTL = Set(
        m, name="kHTL",
        domain=k,
        description="HTL product components",
        records=["BIOCRUDE", "CHAR", "AQUEOUS_PHASE", "GAS_PRODUCT"]
    )

    kCPgas = Set(
        m, name="kCPgas",
        domain=k,
        description="Composting gas components",
        records=["WATER", "NH3", "CO2", "CH4", "N2O", "O2", "N2"]
    )

    kCPcomp = Set(
        m, name="kCPcomp",
        domain=k,
        description="Composting solid components",
        records=["CBH", "PRT", "FAT", "OTH", "WATER", "ASH", "FIXED_CARBON"]
    )

    kCPair = Set(
        m, name="kCPair",
        domain=k,
        description="Composting air components",
        records=["O2", "N2"]
    )

    kINCgas = Set(
        m, name="kINCgas",
        domain=k,
        description="Incineration gas components",
        records=["CO2", "SO2", "O2", "N2", "WATER", "CH4", "N2O"]
    )

    kINCflue = Set(
        m, name="kINCflue",
        domain=k,
        description="Incineration flue gas components",
        records=["CO2", "SO2", "O2", "N2", "WATER"]
    )

    return {
        # Main sets
        "i": i, "j": j, "k": k, "p": p,
        # Technology subsets
        "i_mech": i_mech, "i_bio": i_bio,
        "iConv": iConv, "iHTLrec": iHTLrec, "iGasUpg": iGasUpg,
        # Component subsets
        "kp": kp, "kgas": kgas, "kADdig": kADdig, "kADgas": kADgas,
        "kHTL": kHTL, "kCPgas": kCPgas, "kCPcomp": kCPcomp,
        "kCPair": kCPair, "kINCgas": kINCgas, "kINCflue": kINCflue,
    }
