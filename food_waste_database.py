"""
Food Waste Composition Database
================================
Maps food waste types to model variables:
  WATER, CBH (carbohydrates), PRT (protein), FAT (lipid),
  OTH (other organics), ASH, FIXED_CARBON

All values are on a WET BASIS (fraction, not %)
All fractions sum to 1.0

Sources:
  - Ho & Chu (2018) - Characterization of food waste from different sources
  - Moonsamy et al. (2024) - Food waste: analysis of complex composition
  - Tennessee State University dining hall study (2024)
  - Garcia et al. (2005) - Characterization of meat, fish, fruit, vegetable waste
  - CCNY Food Waste Energy Analysis (2016) - Proximate analysis by food group
  - Rios-Fuentes et al. (2022) - Restaurant food waste characterization
  - FAO Food Composition Data

NOTE: OTH = other organics (fiber, lignin, other volatiles not captured
      by CBH, PRT, FAT). Calculated by difference to ensure sum = 1.0
      FIXED_CARBON estimated from proximate thermogravimetric analysis.
"""

FOOD_WASTE_DATABASE = {

    # ----------------------------------------------------------------
    # 1. MIXED RESTAURANT / CAFETERIA WASTE

    # Source: Ho & Chu (2018), validated against your model parameters
    # ----------------------------------------------------------------
    "Mixed Restaurant / Cafeteria Waste": {
        "description": (
            "Post-consumer mixed waste from restaurants and cafeterias. "
            "High protein content from meat dishes. Represents the base "
            "case in the optimization model. "
            "Source: Ho & Chu (2018)"
        ),
        "composition": {
            "WATER":        0.75952,
            "CBH":          0.016745,
            "PRT":          0.108027,
            "FAT":          0.046492,
            "OTH":          0.020929,
            "ASH":          0.012427,
            "FIXED_CARBON": 0.035360,
        },
        "HHV_MJ_per_kg": 15.67,
        "references": ["Ho & Chu (2018)", "Your base model"],
    },

    # ----------------------------------------------------------------
    # 2. FRUIT & VEGETABLE WASTE
    # Very high moisture, low protein and fat, high carbohydrates
    # Source: Moonsamy et al. (2024), Proximate analysis Nairobi study (2018)
    # ----------------------------------------------------------------
    "Fruit & Vegetable Waste": {
        "description": (
            "Mixed fruit and vegetable scraps from markets, households, "
            "or processing facilities. Very high moisture content (80-90%). "
            "Rich in carbohydrates, low in protein and fat. "
            "Source: Moonsamy et al. (2024)"
        ),
        "composition": {
            "WATER":        0.8400,
            "CBH":          0.0800,
            "PRT":          0.0200,
            "FAT":          0.0080,
            "OTH":          0.0270,
            "ASH":          0.0150,
            "FIXED_CARBON": 0.0100,
        },
        "HHV_MJ_per_kg": 12.83,
        "references": ["Moonsamy et al. (2024)", "CCNY Food Waste Energy Analysis (2016)"],
    },

    # ----------------------------------------------------------------
    # 3. MEAT & FISH WASTE
    # Lower moisture, high protein and fat, moderate ash
    # Source: Garcia et al. (2005), Moonsamy et al. (2024)
    # ----------------------------------------------------------------
    "Meat & Fish Waste": {
        "description": (
            "Waste from meat processing, fish markets, or butcher shops. "
            "Lower moisture than plant-based waste. High protein and fat "
            "content. Higher energy value. "
            "Source: Garcia et al. (2005), Moonsamy et al. (2024)"
        ),
        "composition": {
            "WATER":        0.6500,
            "CBH":          0.0150,
            "PRT":          0.1900,
            "FAT":          0.1000,
            "OTH":          0.0130,
            "ASH":          0.0220,  # bone ash included
            "FIXED_CARBON": 0.0100,
        },
        "HHV_MJ_per_kg": 18.50,
        "references": ["Garcia et al. (2005)", "Moonsamy et al. (2024)"],
    },

    # ----------------------------------------------------------------
    # 4. BREAD & BAKERY WASTE
    # Low moisture, very high carbohydrates, moderate protein
    # Source: Rios-Fuentes et al. (2022), CCNY study (2016)
    # ----------------------------------------------------------------
    "Bread & Bakery Waste": {
        "description": (
            "Unsold or expired bread, pastries, and baked goods. "
            "Significantly lower moisture than other food wastes. "
            "Dominated by carbohydrates (starch). "
            "Source: Rios-Fuentes et al. (2022)"
        ),
        "composition": {
            "WATER":        0.3500,
            "CBH":          0.3800,
            "PRT":          0.0900,
            "FAT":          0.0600,
            "OTH":          0.0500,
            "ASH":          0.0300,
            "FIXED_CARBON": 0.0400,
        },
        "HHV_MJ_per_kg": 12.63,
        "references": ["Rios-Fuentes et al. (2022)", "CCNY Food Waste Energy Analysis (2016)"],
    },

    # ----------------------------------------------------------------
    # 5. DAIRY WASTE
    # High moisture, high fat, moderate protein, low carbohydrates
    # Source: Ho & Chu (2018), literature averages
    # ----------------------------------------------------------------
    "Dairy Waste": {
        "description": (
            "Expired milk, yogurt, cheese trimmings, and other dairy products. "
            "High moisture and fat content. Moderate protein. "
            "Source: Ho & Chu (2018)"
        ),
        "composition": {
            "WATER":        0.7800,
            "CBH":          0.0350,
            "PRT":          0.0650,
            "FAT":          0.0900,
            "OTH":          0.0150,
            "ASH":          0.0100,
            "FIXED_CARBON": 0.0050,
        },
        "HHV_MJ_per_kg": 11.20,
        "references": ["Ho & Chu (2018)", "Literature averages"],
    },

    # ----------------------------------------------------------------
    # 6. CAMPUS DINING HALL WASTE
    # Mixed post-consumer, moderate moisture, balanced macronutrients
    # Source: Tennessee State University study (2024)
    # Dry basis: fat 19.7%, protein 18.7%, ash 4.8%, starch 27.1%,
    # soluble sugars 20.9%, fiber 3.4%, moisture 34.7%
    # ----------------------------------------------------------------
    "Campus Dining Hall Waste": {
        "description": (
            "Mixed post-consumer waste from university dining halls. "
            "Balanced macronutrient profile. Lower moisture than "
            "restaurant waste due to mix of dry foods (cereals, bread). "
            "Source: Tennessee State University (2024)"
        ),
        "composition": {
            "WATER":        0.3470,
            "CBH":          0.3140,   # starch + soluble sugars on wet basis
            "PRT":          0.1220,
            "FAT":          0.1286,
            "OTH":          0.0222,   # fiber
            "ASH":          0.0313,
            "FIXED_CARBON": 0.0349,
        },
        "HHV_MJ_per_kg": 14.50,
        "references": ["Tennessee State University (2024)"],
    },

    # ----------------------------------------------------------------
    # 7. HOUSEHOLD KITCHEN WASTE
    # High moisture, mixed composition, lower protein than restaurant
    # Source: Moonsamy et al. (2024), Ho & Chu (2018)
    # ----------------------------------------------------------------
    "Household Kitchen Waste": {
        "description": (
            "Domestic food scraps from household kitchens. Mix of "
            "fruit/vegetable peels, cooked food leftovers, and small "
            "amounts of meat. High moisture, variable composition. "
            "Source: Moonsamy et al. (2024)"
        ),
        "composition": {
            "WATER":        0.7800,
            "CBH":          0.0700,
            "PRT":          0.0500,
            "FAT":          0.0350,
            "OTH":          0.0350,
            "ASH":          0.0180,
            "FIXED_CARBON": 0.0120,
        },
        "HHV_MJ_per_kg": 13.10,
        "references": ["Moonsamy et al. (2024)", "Ho & Chu (2018)"],
    },

    # ----------------------------------------------------------------
    # 8. MUNICIPAL SOLID FOOD WASTE (OFMSW)
    # Organic fraction of municipal solid waste — broad mix
    # Source: Multiple literature sources averaged
    # ----------------------------------------------------------------
    "Municipal Solid Waste (Organic Fraction)": {
        "description": (
            "Organic fraction of municipal solid waste (OFMSW). "
            "Broad mix of household, restaurant, and market waste. "
            "Representative of large-scale urban food waste streams. "
            "Source: Multiple literature averages"
        ),
        "composition": {
            "WATER":        0.7200,
            "CBH":          0.0900,
            "PRT":          0.0650,
            "FAT":          0.0400,
            "OTH":          0.0450,
            "ASH":          0.0200,
            "FIXED_CARBON": 0.0200,
        },
        "HHV_MJ_per_kg": 13.50,
        "references": ["Moonsamy et al. (2024)", "Ho & Chu (2018)", "FAO Food Composition Data"],
    },

    # ----------------------------------------------------------------
    # 9. CUSTOM (user enters their own experimental data)
    # ----------------------------------------------------------------
    "Custom (Enter Your Own Data)": {
        "description": (
            "Enter your own experimentally measured composition. "
            "All values must be on a wet basis and sum to 1.0."
        ),
        "composition": {
            "WATER":        0.0,
            "CBH":          0.0,
            "PRT":          0.0,
            "FAT":          0.0,
            "OTH":          0.0,
            "ASH":          0.0,
            "FIXED_CARBON": 0.0,
        },
        "HHV_MJ_per_kg": 0.0,
        "references": ["User-provided experimental data"],
    },
}


def get_waste_types():
    """Return list of all food waste type names."""
    return list(FOOD_WASTE_DATABASE.keys())


def get_composition(waste_type):
    """
    Return composition dict for a given waste type.
    Keys: WATER, CBH, PRT, FAT, OTH, ASH, FIXED_CARBON
    Values: fractions on wet basis (sum to 1.0)
    """
    if waste_type not in FOOD_WASTE_DATABASE:
        raise ValueError(f"Unknown waste type: {waste_type}")
    return FOOD_WASTE_DATABASE[waste_type]["composition"].copy()


def get_description(waste_type):
    """Return description string for a given waste type."""
    return FOOD_WASTE_DATABASE[waste_type]["description"]


def get_references(waste_type):
    """Return list of references for a given waste type."""
    return FOOD_WASTE_DATABASE[waste_type]["references"]


def get_HHV(waste_type):
    """Return higher heating value (MJ/kg wet basis) for a given waste type."""
    return FOOD_WASTE_DATABASE[waste_type]["HHV_MJ_per_kg"]


def validate_composition(composition):
    """
    Check that composition fractions sum to ~1.0.
    Returns (is_valid, error_message).
    """
    total = sum(composition.values())
    if abs(total - 1.0) > 0.01:
        return False, f"Fractions sum to {total:.4f}, must sum to 1.0"
    for key, val in composition.items():
        if val < 0:
            return False, f"{key} cannot be negative"
    return True, "OK"


def print_database_summary():
    """Print a summary table of all waste types and their compositions."""
    print("\n" + "=" * 100)
    print("FOOD WASTE COMPOSITION DATABASE — WET BASIS FRACTIONS")
    print("=" * 100)
    header = f"{'Waste Type':<42} {'WATER':>7} {'CBH':>7} {'PRT':>7} {'FAT':>7} {'OTH':>7} {'ASH':>7} {'FC':>7} {'HHV':>8}"
    print(header)
    print("-" * 100)
    for name, data in FOOD_WASTE_DATABASE.items():
        if name == "Custom (Enter Your Own Data)":
            continue
        c = data["composition"]
        print(
            f"{name:<42} "
            f"{c['WATER']:>7.4f} "
            f"{c['CBH']:>7.4f} "
            f"{c['PRT']:>7.4f} "
            f"{c['FAT']:>7.4f} "
            f"{c['OTH']:>7.4f} "
            f"{c['ASH']:>7.4f} "
            f"{c['FIXED_CARBON']:>7.4f} "
            f"{data['HHV_MJ_per_kg']:>7.2f}"
        )
    print("=" * 100)
    print("CBH=Carbohydrates, PRT=Protein, FAT=Lipid, OTH=Other organics,")
    print("ASH=Inorganic ash, FC=Fixed carbon, HHV=Higher heating value (MJ/kg wet)")
    print()


if __name__ == "__main__":
    print_database_summary()

    # Example: get composition for fruit & vegetable waste
    comp = get_composition("Fruit & Vegetable Waste")
    print("\nExample — Fruit & Vegetable Waste composition:")
    for k, v in comp.items():
        print(f"  {k}: {v:.4f} ({v*100:.2f}%)")

    # Validate
    valid, msg = validate_composition(comp)
    print(f"\nValidation: {msg}")
