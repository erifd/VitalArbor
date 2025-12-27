
SPECIES_RISK_FACTORS = {

    # Alders (Alnus spp.)

    "alnus rubra": {  # Red alder
        "root_risk": 0.9,
        "wood_risk": 0.8,
        "growth_risk": 0.7,
    },

    "alnus incana": {  # Gray alder
        "root_risk": 0.85,
        "wood_risk": 0.75,
        "growth_risk": 0.7,
    },

    "alnus glutinosa": {  # Black alder
        "root_risk": 0.85,
        "wood_risk": 0.7,
        "growth_risk": 0.65,
    },

    "alnus viridis": {  # Green alder
        "root_risk": 0.8,
        "wood_risk": 0.7,
        "growth_risk": 0.7,
    },

    "alnus serrulata": {  # Hazel alder
        "root_risk": 0.8,
        "wood_risk": 0.65,
        "growth_risk": 0.7,
    },

    # Willows (Salix spp.)

    "salix babylonica": {  # Weeping willow
        "root_risk": 0.95,
        "wood_risk": 0.75,
        "growth_risk": 0.85,
    },

    "salix lucida": {  # Shining willow
        "root_risk": 0.9,
        "wood_risk": 0.7,
        "growth_risk": 0.8,
    },

    "salix nigra": {  # Black willow
        "root_risk": 0.95,
        "wood_risk": 0.7,
        "growth_risk": 0.85,
    },

    "salix alba": {  # White willow
        "root_risk": 0.9,
        "wood_risk": 0.7,
        "growth_risk": 0.8,
    },

    "salix fragilis": {  # Crack willow
        "root_risk": 0.9,
        "wood_risk": 0.8,
        "growth_risk": 0.8,
    },

    "salix exigua": {  # Coyote willow
        "root_risk": 0.85,
        "wood_risk": 0.65,
        "growth_risk": 0.75,
    },

    "salix scouleriana": {  # Scouler's willow (PNW)
        "root_risk": 0.85,
        "wood_risk": 0.65,
        "growth_risk": 0.75,
    },

    # Poplars and Cottonwoods

    "populus trichocarpa": {  # Black cottonwood
        "root_risk": 0.95,
        "wood_risk": 0.85,
        "growth_risk": 0.9,
    },

    "populus deltoides": {  # Eastern cottonwood
        "root_risk": 0.95,
        "wood_risk": 0.8,
        "growth_risk": 0.9,
    },

    "populus tremuloides": {  # Quaking aspen
        "root_risk": 0.8,
        "wood_risk": 0.6,
        "growth_risk": 0.75,
    },

    "populus nigra": {  # Black poplar
        "root_risk": 0.9,
        "wood_risk": 0.75,
        "growth_risk": 0.8,
    },

    # Maples

    "acer saccharinum": {  # Silver maple
        "root_risk": 0.85,
        "wood_risk": 0.8,
        "growth_risk": 0.7,
    },

    "acer macrophyllum": {  # Bigleaf maple (PNW)
        "root_risk": 0.7,
        "wood_risk": 0.65,
        "growth_risk": 0.7,
    },

    "acer negundo": {  # Boxelder
        "root_risk": 0.8,
        "wood_risk": 0.75,
        "growth_risk": 0.8,
    },

    # Birches

    "betula papyrifera": {  # Paper birch
        "root_risk": 0.7,
        "wood_risk": 0.6,
        "growth_risk": 0.6,
    },

    "betula pendula": {  # Silver birch
        "root_risk": 0.75,
        "wood_risk": 0.6,
        "growth_risk": 0.65,
    },

    # Spruce and Fir

    "picea sitchensis": {  # Sitka spruce
        "root_risk": 0.9,
        "wood_risk": 0.5,
        "growth_risk": 0.6,
    },

    "picea glauca": {  # White spruce
        "root_risk": 0.85,
        "wood_risk": 0.55,
        "growth_risk": 0.6,
    },

    "pseudotsuga menziesii": {  # Douglas-fir
        "root_risk": 0.7,
        "wood_risk": 0.4,
        "growth_risk": 0.5,
    },

    # Other Species High Risk

    "pyrus calleryana": {  # Bradford pear
        "root_risk": 0.6,
        "wood_risk": 0.95,
        "growth_risk": 0.7,
    },

    "fraxinus latifolia": {  # Oregon ash
        "root_risk": 0.7,
        "wood_risk": 0.55,
        "growth_risk": 0.6,
    },

    "ulmus americana": {  # American elm (weak in old age)
        "root_risk": 0.7,
        "wood_risk": 0.6,
        "growth_risk": 0.7,
    },

    "liquidambar styraciflua": {  # Sweetgum
        "root_risk": 0.75,
        "wood_risk": 0.6,
        "growth_risk": 0.7,
    },

    "ailanthus altissima": {  # Tree-of-heaven (weak wood, invasive)
        "root_risk": 0.8,
        "wood_risk": 0.55,
        "growth_risk": 0.9,
    },

    "eucalyptus globulus": {  # Blue gum eucalyptus
        "root_risk": 0.85,
        "wood_risk": 0.7,
        "growth_risk": 0.9,
    },

}


def species_structural_risk(species_name):
    """
    Returns a 0.0–1.0 structural risk multiplier based on species traits.
    If species is unknown, returns a neutral multiplier of 0.5.
    """

    if not species_name:
        return 0.5

    species = species_name.lower().strip()

    if species not in SPECIES_RISK_FACTORS:
        return 0.5

    traits = SPECIES_RISK_FACTORS[species]

    return (
        0.5 * traits["root_risk"] +
        0.3 * traits["wood_risk"] +
        0.2 * traits["growth_risk"]
    )


def give_risk_score(tilt_angle, trunk_lines_count=None):
    """
    Calculate tree fall risk score based on tilt angle and other factors.
    
    Parameters:
    - tilt_angle: angle in degrees from vertical (0 = perfectly vertical)
    - trunk_lines_count: number of detected trunk lines (optional, for confidence)
    
    Returns:
    - risk_score: 1-40 score (1=lowest risk, 40=highest risk)
    """
    
    # Base risk calculation from tilt angle
    abs_tilt = abs(tilt_angle)
    
    # More relaxed risk thresholds:
    # 0-10°: Low risk (score 1-10)
    # 10-20°: Moderate risk (score 11-20)
    # 20-30°: High risk (score 21-30)
    # 30+°: Critical risk (score 31-40)
    
    if abs_tilt <= 10:
        # Low risk: linear scale from 1 to 10
        risk_score = 1 + (abs_tilt / 10.0) * 9

    elif abs_tilt <= 20:
        # Moderate risk: linear scale from 11 to 20
        risk_score = 11 + ((abs_tilt - 10) / 10.0) * 9

    elif abs_tilt <= 30:
        # High risk: linear scale from 21 to 30
        risk_score = 21 + ((abs_tilt - 20) / 10.0) * 9

    else:
        # Critical risk: linear scale from 31 to 40, capped at 40
        risk_score = 31 + min((abs_tilt - 30) / 10.0, 1.0) * 9
        risk_score = min(risk_score, 40)
    
    # Confidence adjustment (optional)
    if trunk_lines_count is not None and trunk_lines_count < 5:
        # Low confidence - add uncertainty penalty
        risk_score = min(risk_score + 2, 40)
    
    return round(risk_score, 1)



def get_risk_category(risk_score):
    """Get risk category and color based on score."""
    if risk_score <= 10:
        return "LOW RISK", "green"
    elif risk_score <= 20:
        return "MODERATE RISK", "yellow"
    elif risk_score <= 30:
        return "HIGH RISK", "orange"
    else:
        return "CRITICAL RISK", "red"


def combined_tree_risk(multiplier, tilt_angle, species_name, trunk_lines_count=None):
    """
    Combines tilt-based risk with species structural risk.
    Returns a final 1–40 score.
    """

    tilt_risk = give_risk_score(tilt_angle, trunk_lines_count)
    species_risk = species_structural_risk(species_name)

    # Apply multiplier: 0.8× to 1.2× depending on species weakness
    adjusted_risk = tilt_risk * (0.8 + species_risk * 0.4) * multiplier

    adjusted_risk = max(1, min(40, adjusted_risk))
    return round(adjusted_risk, 1)


def display_risk_gradient(risk_score, tilt_angle, diagnosis, fixes):
    """
    Display a colorful gradient bar in the terminal showing risk level.
    """
    
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'orange': '\033[38;5;208m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
    }
    
    bar_length = 40
    marker_position = int((risk_score - 1) / 39 * (bar_length - 1))
    
    print("\n" + "="*60)
    print(f"{COLORS['bold']}TREE FALL RISK ASSESSMENT{COLORS['reset']}")
    print("="*60)
    
    print(f"\n{COLORS['cyan']}Tilt Angle:{COLORS['reset']} {abs(tilt_angle):.2f}° from vertical")
    direction = "RIGHT" if tilt_angle > 0 else "LEFT"
    if abs(tilt_angle) > 0.5:
        print(f"{COLORS['cyan']}Direction:{COLORS['reset']} Leaning {direction}")
    
    category, _ = get_risk_category(risk_score)
    print(f"\n{COLORS['cyan']}Risk Score:{COLORS['reset']} {risk_score:.1f} / 40")
    print(f"{COLORS['cyan']}Category:{COLORS['reset']} {category}")
    
    print(f"\n{COLORS['bold']}Risk Level:{COLORS['reset']}")
    print("└─ 1" + " " * (bar_length - 6) + "40 ─┘")
    
    bar = ""
    for i in range(bar_length):
        segment_score = 1 + (i / (bar_length - 1)) * 39
        
        if segment_score <= 10:
            color = COLORS['green']
        elif segment_score <= 20:
            color = COLORS['yellow']
        elif segment_score <= 30:
            color = COLORS['orange']
        else:
            color = COLORS['red']
        
        if i == marker_position:
            bar += f"{COLORS['blue']}{COLORS['bold']}▼{COLORS['reset']}"
        else:
            bar += f"{color}█{COLORS['reset']}"
    
    print("   " + bar)
    
    print("\n" + " " * (marker_position + 3) + f"{COLORS['blue']}│{COLORS['reset']}")
    print(" " * (marker_position + 2) + f"{COLORS['blue']}{risk_score:.1f}{COLORS['reset']}")
    
    print("\n" + f"{COLORS['green']}■{COLORS['reset']} Low (1-10)   " +
          f"{COLORS['yellow']}■{COLORS['reset']} Moderate (11-20)   " +
          f"{COLORS['orange']}■{COLORS['reset']} High (21-30)   " +
          f"{COLORS['red']}■{COLORS['reset']} Critical (31-40)")
    
    print("\n" + "-"*60)
    print(f"{COLORS['bold']}INTERPRETATION:{COLORS['reset']}")
    
    if risk_score <= 10:
        print(f"{COLORS['green']}✓{COLORS['reset']} Tree appears stable with minimal lean.")
        print("Diagnosis of tree:", diagnosis)
        print("Fixes/reccomendations:", fixes)
    elif risk_score <= 20:
        print(f"{COLORS['yellow']}⚠{COLORS['reset']} Tree has noticeable lean.")
        print("Diagnosis of tree:", diagnosis)
        print("Fixes/reccomendations:", fixes)
    elif risk_score <= 30:
        print(f"{COLORS['orange']}⚠{COLORS['reset']} Tree has significant lean - potential concern.")
        print("Diagnosis of tree:", diagnosis)
        print("Fixes/reccomendations:", fixes)
    else:
        print(f"{COLORS['red']}✗{COLORS['reset']} Tree has severe lean - elevated fall risk.")
        print("Diagnosis of tree:", diagnosis)
        print("Fixes/reccomendations:", fixes)
    
    print("="*60 + "\n")