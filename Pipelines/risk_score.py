SPECIES_RISK_FACTORS = {
    "alnus rubra": {"root_risk": 0.9,
                     "wood_risk": 0.8, 
                    "growth_risk": 0.7},

    "alnus incana": {"root_risk": 0.85, 
                     "wood_risk": 0.75, 
                     "growth_risk": 0.7},

    "alnus glutinosa": {"root_risk": 0.85, 
                        "wood_risk": 0.7, 
                        "growth_risk": 0.65},

    "alnus viridis": {"root_risk": 0.8, 
                      "wood_risk": 0.7, 
                      "growth_risk": 0.7},

    "alnus serrulata": {"root_risk": 0.8, 
                        "wood_risk": 0.65, 
                        "growth_risk": 0.7},

    "salix babylonica": {"root_risk": 0.95, 
                         "wood_risk": 0.75, 
                         "growth_risk": 0.85},

    "salix lucida": {"root_risk": 0.9, 
                     "wood_risk": 0.7, 
                     "growth_risk": 0.8},

    "salix nigra": {"root_risk": 0.95, 
                    "wood_risk": 0.7, 
                    "growth_risk": 0.85},

    "salix alba": {"root_risk": 0.9, 
                   "wood_risk": 0.7, 
                   "growth_risk": 0.8},

    "salix fragilis": {"root_risk": 0.9, 
                       "wood_risk": 0.8, 
                       "growth_risk": 0.8},

    "salix exigua": {"root_risk": 0.85, 
                     "wood_risk": 0.65, 
                     "growth_risk": 0.75},

    "salix scouleriana": {"root_risk": 0.85, 
                          "wood_risk": 0.65, 
                          "growth_risk": 0.75},

    "populus trichocarpa": {"root_risk": 0.95, 
                            "wood_risk": 0.85, 
                            "growth_risk": 0.9},

    "populus deltoides": {"root_risk": 0.95, 
                          "wood_risk": 0.8, 
                          "growth_risk": 0.9},

    "populus tremuloides": {"root_risk": 0.8, 
                            "wood_risk": 0.6, 
                            "growth_risk": 0.75},

    "populus nigra": {"root_risk": 0.9, 
                      "wood_risk": 0.75, 
                      "growth_risk": 0.8},

    "acer saccharinum": {"root_risk": 0.85, 
                         "wood_risk": 0.8, 
                         "growth_risk": 0.7},

    "acer macrophyllum": {"root_risk": 0.7, 
                          "wood_risk": 0.65, 
                          "growth_risk": 0.7},

    "acer negundo": {"root_risk": 0.8, 
                     "wood_risk": 0.75, 
                     "growth_risk": 0.8},

    "betula papyrifera": {"root_risk": 0.7, 
                          "wood_risk": 0.6, 
                          "growth_risk": 0.6},

    "betula pendula": {"root_risk": 0.75, 
                       "wood_risk": 0.6, 
                       "growth_risk": 0.65},

    "picea sitchensis": {"root_risk": 0.9, 
                         "wood_risk": 0.5, 
                         "growth_risk": 0.6},

    "picea glauca": {"root_risk": 0.85, 
                     "wood_risk": 0.55, 
                     "growth_risk": 0.6},

    "pseudotsuga menziesii": {"root_risk": 0.7, 
                              "wood_risk": 0.4, 
                              "growth_risk": 0.5},

    "pyrus calleryana": {"root_risk": 0.6, 
                         "wood_risk": 0.95, 
                         "growth_risk": 0.7},

    "fraxinus latifolia": {"root_risk": 0.7, 
                           "wood_risk": 0.55, 
                           "growth_risk": 0.6},

    "ulmus americana": {"root_risk": 0.7, 
                        "wood_risk": 0.6, 
                        "growth_risk": 0.7},

    "liquidambar styraciflua": {"root_risk": 0.75, 
                                "wood_risk": 0.6, 
                                "growth_risk": 0.7},

    "ailanthus altissima": {"root_risk": 0.8, 
                            "wood_risk": 0.55, 
                            "growth_risk": 0.9},

    "eucalyptus globulus": {"root_risk": 0.85, 
                            "wood_risk": 0.7, 
                            "growth_risk": 0.9},
}


def analyze_sweep_quality(sweep_metrics):
    """
    Advanced sweep quality analysis based on arboricultural research.
    
    Research-based criteria:
    1. Progressive outward lean = CRITICAL (active root failure)
    2. Sharp curves = HIGH RISK (stress concentrations)
    3. Gradual correcting curves = LOW RISK (reaction wood working)
    4. Lean out → straight up = MODERATE (partial compensation)
    5. Lean out → curve back = GOOD (full compensation)
    
    Returns: (sweep_quality, tilt_weight_adjustment, quality_description)
    """
    
    if not sweep_metrics or not sweep_metrics.get('has_data', False):
        return 'neutral', 1.0, "Insufficient sweep data - using standard tilt assessment"
    
    # Extract all relevant metrics
    sweep_type = sweep_metrics.get('sweep_type', 'neutral')
    sweep_quality_raw = sweep_metrics.get('sweep_quality', 'moderate')
    
    # New curvature metrics
    sharpness = sweep_metrics.get('sharpness_score', 0.0)
    smoothness = sweep_metrics.get('smoothness_score', 1.0)
    
    # New movement pattern metrics
    movement_pattern = sweep_metrics.get('movement_pattern', 'neutral')
    movement_risk = sweep_metrics.get('movement_risk_level', 'moderate')
    pattern_score = sweep_metrics.get('pattern_score', 0.0)
    
    # Traditional metrics
    curve_recovery = sweep_metrics.get('curve_recovery', 0.0)
    consistency_score = sweep_metrics.get('consistency_score', 0.5)
    overall_tilt = sweep_metrics.get('overall_tilt_angle', 0.0)
    
    print(f"\n{'='*60}")
    print(f"ADVANCED SWEEP QUALITY ANALYSIS")
    print(f"{'='*60}")
    print(f"Sweep Type: {sweep_type}")
    print(f"Movement Pattern: {movement_pattern}")
    print(f"Movement Risk: {movement_risk}")
    print(f"Pattern Score: {pattern_score:.3f} (-1=worst, +1=best)")
    print(f"Curve Sharpness: {sharpness:.3f} (0=gradual, 1=sharp)")
    print(f"Curve Smoothness: {smoothness:.3f} (0=erratic, 1=smooth)")
    print(f"Curve Recovery: {curve_recovery:.3f} (-1=worse, +1=better)")
    print(f"Consistency: {consistency_score:.3f} (high=straight)")
    print(f"Overall Tilt: {overall_tilt:.2f}°")
    
    # === CRITICAL CASE: Progressive Outward Lean ===
    # Research: This indicates active root failure - highest priority
    if movement_pattern == 'progressive_out' or sweep_type == 'progressive_failure':
        sweep_quality = 'critical'
        tilt_weight = 2.0  # DOUBLE the tilt concern
        description = ("⚠️ CRITICAL - PROGRESSIVE OUTWARD LEAN: Tree is actively leaning more "
                      "away from vertical. This indicates ongoing root failure or soil movement. "
                      "IMMEDIATE professional arborist assessment required. This is the most "
                      "dangerous lean pattern.")
        print(f"\n🚨 CRITICAL: Progressive failure detected!")
    
    # === HIGH RISK CASE: Sharp Curve ===
    # Research: Sharp curves create stress concentration points - can fail suddenly
    elif sharpness > 0.6 and smoothness < 0.4:
        sweep_quality = 'poor'
        tilt_weight = 1.6  # Significantly increase concern
        description = ("⚠️ HIGH RISK - SHARP CURVE: Tree has abrupt directional changes creating "
                      "stress concentration points in the wood fibers. Sharp curves are more prone "
                      "to sudden failure than gradual curves. The erratic curvature pattern suggests "
                      "inadequate reaction wood formation. Professional inspection recommended.")
        print(f"\n⚠️  Sharp curve stress pattern detected")
    
    # === EXCELLENT CASE: Gradual Correcting Curve ===
    # Research: This shows reaction wood successfully compensating - very safe
    elif (movement_pattern == 'correcting_inward' and 
          sharpness < 0.4 and 
          smoothness > 0.6 and 
          curve_recovery > 0.3):
        sweep_quality = 'excellent'
        tilt_weight = 0.25  # Greatly reduce tilt concern (75% reduction)
        description = ("✓ EXCELLENT - GRADUAL CORRECTION: Tree shows smooth, gradual curve back "
                      "toward vertical. This indicates successful reaction wood formation - the tree "
                      "is actively compensating for the lean through natural growth processes. "
                      "This is the safest sweep pattern. The measured tilt angle primarily represents "
                      "historical growth, not current structural instability.")
        print(f"\n✓ Excellent: Natural compensation working perfectly")
    
    # === GOOD CASE: Natural Recovery Sweep ===
    # Research: Direction reversal with gradual curve = healthy compensation
    elif (movement_pattern == 'correcting_inward' and 
          sharpness < 0.5 and 
          curve_recovery > 0.2):
        sweep_quality = 'good'
        tilt_weight = 0.4  # Significantly reduce concern (60% reduction)
        description = ("✓ GOOD - NATURAL RECOVERY: Tree demonstrates recovery toward vertical "
                      "with relatively gradual curvature. Reaction wood is forming to compensate "
                      "for the lean. While not perfect, this pattern indicates the tree is managing "
                      "the structural load through natural adaptive growth.")
        print(f"\n✓ Good: Healthy recovery pattern")
    
    # === MODERATE CASE: Stable Lean (Lean then Straight) ===
    # Research: Tree has adapted but isn't actively correcting - monitor
    elif (movement_pattern == 'stable_lean' and 
          overall_tilt < 15 and 
          sharpness < 0.6):
        sweep_quality = 'moderate'
        tilt_weight = 0.9  # Slight reduction (10% reduction)
        description = ("MODERATE - STABLE LEAN: Tree leans at base but grows relatively straight "
                      "upward. Some adaptation has occurred but full correction is not evident. "
                      "This pattern is common and generally stable if the lean developed gradually. "
                      "Monitor for any increase in lean angle over time.")
        print(f"\nℹ️  Moderate: Partial adaptation evident")
    
    # === POOR CASE: Straight Consistent Tilt ===
    # Research: No compensation occurring - concerning
    elif (consistency_score > 0.75 and 
          overall_tilt > 10 and 
          movement_pattern != 'correcting_inward'):
        sweep_quality = 'poor'
        tilt_weight = 1.3  # Increase concern (30% increase)
        description = ("⚠️ POOR - CONSISTENT TILT: Entire trunk shows uniform tilt without "
                      "corrective curvature. No evidence of reaction wood formation or natural "
                      "compensation. This pattern suggests either recent lean development or "
                      "insufficient tree vigor to produce corrective growth. Requires monitoring "
                      "and may need intervention.")
        print(f"\n⚠️  Poor: No compensation detected")
    
    # === CRITICAL CASE: Severe Tilt ===
    # Research: Extreme angles regardless of pattern
    elif overall_tilt > 25:
        sweep_quality = 'critical'
        tilt_weight = 1.8  # Major increase (80% increase)
        description = ("⚠️ CRITICAL - SEVERE TILT: Tilt angle exceeds 25° which is approaching "
                      "the threshold (45°) where failure likelihood becomes very high. Regardless "
                      "of sweep pattern, extreme lean angles create significant structural stress. "
                      "IMMEDIATE professional assessment strongly recommended.")
        print(f"\n🚨 CRITICAL: Severe tilt angle")
    
    # === EXCELLENT CASE: Minimal Tilt ===
    # Nearly vertical tree
    elif overall_tilt < 5:
        sweep_quality = 'excellent'
        tilt_weight = 0.5  # Moderate reduction (50% reduction)
        description = ("✓ EXCELLENT - MINIMAL TILT: Tree maintains near-vertical orientation "
                      "with less than 5° deviation. This is within normal growth variation and "
                      "indicates excellent structural stability.")
        print(f"\n✓ Excellent: Nearly vertical growth")
    
    # === MODERATE CASE: Sharp but Small Tilt ===
    elif sharpness > 0.5 and overall_tilt < 10:
        sweep_quality = 'moderate'
        tilt_weight = 1.1  # Slight increase (10% increase)
        description = ("MODERATE - SMALL SHARP CURVE: Tree shows somewhat abrupt directional "
                      "changes but overall tilt is modest. While the curve sharpness is concerning, "
                      "the limited lean angle reduces overall risk. Monitor curve areas for signs "
                      "of stress (cracks, bark irregularities).")
        print(f"\nℹ️  Moderate: Sharp but limited")
    
    # === DEFAULT: Neutral Assessment ===
    else:
        sweep_quality = 'neutral'
        tilt_weight = 1.0  # No adjustment
        description = ("NEUTRAL - MIXED CHARACTERISTICS: Sweep pattern shows mixed features "
                      "without strongly positive or negative indicators. Standard tilt-based "
                      "risk assessment applies. Consider routine monitoring.")
        print(f"\nℹ️  Neutral: Standard assessment")
    
    # Additional risk factor: Severe sharpness regardless of other factors
    if sharpness > 0.8:
        print(f"\n⚠️  WARNING: Very sharp curve detected - adds stress risk")
        tilt_weight = min(2.0, tilt_weight * 1.2)  # Add 20% penalty, cap at 2.0
    
    # Additional safety factor: Excellent smoothness helps
    if smoothness > 0.8 and sweep_quality not in ['critical', 'poor']:
        print(f"\n✓ Smooth gradient detected - reduces stress")
        tilt_weight = max(0.25, tilt_weight * 0.9)  # Remove 10%, floor at 0.25
    
    print(f"\n{'='*60}")
    print(f"FINAL SWEEP ASSESSMENT:")
    print(f"Quality: {sweep_quality.upper()}")
    print(f"Tilt Weight Multiplier: {tilt_weight:.2f}x")
    print(f"{description}")
    print(f"{'='*60}\n")
    
    return sweep_quality, tilt_weight, description


def species_structural_risk(species_name, multiplier):
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
        (0.5 * traits["root_risk"] +
        0.3 * traits["wood_risk"] +
        0.2 * traits["growth_risk"]) * multiplier
    )


def give_risk_score(tilt_angle, trunk_lines_count=None, sweep_metrics=None):
    """
    Calculate tree fall risk score with advanced sweep-based adjustment.
    
    Now includes research-based curve analysis:
    - Progressive outward lean: 2.0x multiplier (CRITICAL)
    - Sharp curves: 1.6x multiplier (stress concentration)
    - Gradual correction: 0.25x multiplier (natural compensation)
    - Straight tilt: 1.3x multiplier (no compensation)
    
    Parameters:
    - tilt_angle: angle in degrees from vertical (0 = perfectly vertical)
    - trunk_lines_count: number of detected trunk lines (optional)
    - sweep_metrics: dict containing advanced sweep analysis data
    
    Returns:
    - risk_score: 1-40 score (1=lowest risk, 40=highest risk)
    """
    
    # Analyze sweep quality if metrics provided
    tilt_weight = 1.0  # Default weight
    sweep_quality = 'neutral'
    sweep_description = "No sweep analysis available"
    
    if sweep_metrics:
        sweep_quality, tilt_weight, sweep_description = analyze_sweep_quality(sweep_metrics)
    
    # Apply sweep-based adjustment to the tilt angle
    raw_tilt = abs(tilt_angle)
    effective_tilt = raw_tilt * tilt_weight
    
    print(f"\n{'='*60}")
    print(f"TILT RISK CALCULATION")
    print(f"{'='*60}")
    print(f"Raw tilt angle: {raw_tilt:.2f}°")
    print(f"Sweep quality: {sweep_quality}")
    print(f"Tilt weight multiplier: {tilt_weight:.2f}x")
    print(f"Effective tilt: {effective_tilt:.2f}°")
    
    # Risk thresholds based on effective tilt
    # 0-10°: Low risk (score 1-10)
    # 10-20°: Moderate risk (score 11-20)
    # 20-30°: High risk (score 21-30)
    # 30+°: Critical risk (score 31-40)
    
    if effective_tilt <= 10:
        risk_score = 1 + (effective_tilt / 10.0) * 9
    elif effective_tilt <= 20:
        risk_score = 11 + ((effective_tilt - 10) / 10.0) * 9
    elif effective_tilt <= 30:
        risk_score = 21 + ((effective_tilt - 20) / 10.0) * 9
    else:
        risk_score = 31 + min((effective_tilt - 30) / 10.0, 1.0) * 9
        risk_score = min(risk_score, 40)
    
    # Confidence adjustment
    if trunk_lines_count is not None and trunk_lines_count < 5:
        print(f"Low detection confidence (+2 penalty): {trunk_lines_count} trunk lines")
        risk_score = min(risk_score + 2, 40)
    
    # Quality-based bounds
    if sweep_quality == 'excellent':
        # Cap excellent sweeps at moderate-low risk
        if risk_score > 12:
            print(f"Excellent sweep cap: limiting score to 12")
            risk_score = min(risk_score, 12)
    
    elif sweep_quality == 'critical':
        # Add penalty for critical sweeps
        print(f"Critical sweep penalty: +5 to score")
        risk_score = min(risk_score + 5, 40)
        
        # For progressive failure, ensure minimum HIGH risk
        if sweep_metrics and sweep_metrics.get('movement_pattern') == 'progressive_out':
            print(f"Progressive failure: ensuring minimum score of 25")
            risk_score = max(risk_score, 25)
    
    print(f"\nFinal risk score: {risk_score:.1f} / 40")
    print(f"{'='*60}\n")
    
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


def combined_tree_risk(multiplier, tilt_angle, species_name, trunk_lines_count=None, sweep_metrics=None):
    """
    Combines tilt-based risk with species structural risk.
    Now includes advanced sweep analysis for accurate assessment.
    Returns a final 1–40 score.
    """
    tilt_risk = give_risk_score(tilt_angle, trunk_lines_count, sweep_metrics)
    species_risk = species_structural_risk(species_name, multiplier)

    # Apply species multiplier: 0.8× to 1.2× depending on species weakness
    adjusted_risk = tilt_risk * (0.8 + species_risk * 0.4)
    adjusted_risk = max(1, min(40, adjusted_risk))
    
    print(f"{'='*60}")
    print(f"COMBINED RISK CALCULATION")
    print(f"{'='*60}")
    print(f"Tilt-based risk: {tilt_risk:.1f}")
    print(f"Species: {species_name if species_name else 'Unknown'}")
    print(f"Species risk factor: {species_risk:.3f}")
    print(f"Final adjusted risk: {adjusted_risk:.1f} / 40")
    print(f"{'='*60}\n")
    
    return round(adjusted_risk, 1)


def display_risk_gradient(risk_score, tilt_angle, diagnosis, fixes, sweep_metrics=None):
    """
    Display a colorful gradient bar showing risk level with sweep analysis.
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
        'magenta': '\033[95m',
    }
    
    bar_length = 40
    marker_position = int((risk_score - 1) / 39 * (bar_length - 1))
    
    print("\n" + "="*70)
    print(f"{COLORS['bold']}TREE FALL RISK ASSESSMENT{COLORS['reset']}")
    print("="*70)
    
    print(f"\n{COLORS['cyan']}Tilt Angle:{COLORS['reset']} {abs(tilt_angle):.2f}° from vertical")
    direction = "RIGHT" if tilt_angle > 0 else "LEFT"
    if abs(tilt_angle) > 0.5:
        print(f"{COLORS['cyan']}Direction:{COLORS['reset']} Leaning {direction}")
    
    # Display advanced sweep information
    if sweep_metrics and sweep_metrics.get('has_data', False):
        print(f"\n{COLORS['bold']}═══ SWEEP ANALYSIS ═══{COLORS['reset']}")
        
        sweep_quality, tilt_weight, sweep_desc = analyze_sweep_quality(sweep_metrics)
        
        # Color code based on quality
        quality_colors = {
            'excellent': COLORS['green'],
            'good': COLORS['green'],
            'neutral': COLORS['yellow'],
            'moderate': COLORS['yellow'],
            'poor': COLORS['orange'],
            'critical': COLORS['red']
        }
        quality_color = quality_colors.get(sweep_quality, COLORS['yellow'])
        
        # Movement pattern
        movement_pattern = sweep_metrics.get('movement_pattern', 'unknown')
        pattern_display = movement_pattern.replace('_', ' ').title()
        
        print(f"{COLORS['cyan']}Movement Pattern:{COLORS['reset']} {pattern_display}")
        
        # Show critical warning for progressive failure
        if movement_pattern == 'progressive_out':
            print(f"{COLORS['red']}{COLORS['bold']}⚠️  PROGRESSIVE OUTWARD LEAN - CRITICAL{COLORS['reset']}")
        
        print(f"{COLORS['cyan']}Sweep Quality:{COLORS['reset']} {quality_color}{sweep_quality.upper()}{COLORS['reset']}")
        
        # Curve characteristics
        sharpness = sweep_metrics.get('sharpness_score', 0)
        smoothness = sweep_metrics.get('smoothness_score', 0)
        pattern_score = sweep_metrics.get('pattern_score', 0)
        
        print(f"{COLORS['cyan']}Curve Sharpness:{COLORS['reset']} {sharpness:.2f} ", end="")
        if sharpness > 0.6:
            print(f"{COLORS['red']}(Sharp - Stress Risk){COLORS['reset']}")
        elif sharpness < 0.4:
            print(f"{COLORS['green']}(Gradual - Good){COLORS['reset']}")
        else:
            print(f"{COLORS['yellow']}(Moderate){COLORS['reset']}")
        
        print(f"{COLORS['cyan']}Curve Smoothness:{COLORS['reset']} {smoothness:.2f} ", end="")
        if smoothness > 0.6:
            print(f"{COLORS['green']}(Smooth - Good){COLORS['reset']}")
        else:
            print(f"{COLORS['orange']}(Erratic){COLORS['reset']}")
        
        print(f"{COLORS['cyan']}Pattern Score:{COLORS['reset']} {pattern_score:.2f} ", end="")
        if pattern_score > 0.5:
            print(f"{COLORS['green']}(Correcting){COLORS['reset']}")
        elif pattern_score < -0.5:
            print(f"{COLORS['red']}(Worsening){COLORS['reset']}")
        else:
            print(f"{COLORS['yellow']}(Stable){COLORS['reset']}")
        
        print(f"{COLORS['cyan']}Tilt Weight Multiplier:{COLORS['reset']} {tilt_weight:.2f}x")
        
        # Interpretation
        if sweep_quality in ['excellent', 'good']:
            print(f"{COLORS['green']}✓{COLORS['reset']} Natural compensation detected - reduced risk")
        elif sweep_quality in ['poor', 'critical']:
            print(f"{COLORS['red']}⚠{COLORS['reset']} Concerning pattern - increased risk")
    
    category, _ = get_risk_category(risk_score)
    print(f"\n{COLORS['cyan']}Risk Score:{COLORS['reset']} {COLORS['bold']}{risk_score:.1f} / 40{COLORS['reset']}")
    print(f"{COLORS['cyan']}Category:{COLORS['reset']} {COLORS['bold']}{category}{COLORS['reset']}")
    
    print(f"\n{COLORS['bold']}Risk Level Scale:{COLORS['reset']}")
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
    print(" " * (marker_position + 2) + f"{COLORS['blue']}{COLORS['bold']}{risk_score:.1f}{COLORS['reset']}")
    
    print("\n" + f"{COLORS['green']}■{COLORS['reset']} Low (1-10)   " +
          f"{COLORS['yellow']}■{COLORS['reset']} Moderate (11-20)   " +
          f"{COLORS['orange']}■{COLORS['reset']} High (21-30)   " +
          f"{COLORS['red']}■{COLORS['reset']} Critical (31-40)")
    
    print("\n" + "-"*70)
    print(f"{COLORS['bold']}INTERPRETATION:{COLORS['reset']}")
    
    if risk_score <= 10:
        print(f"{COLORS['green']}✓{COLORS['reset']} Tree appears stable with minimal lean.")
        if sweep_metrics and sweep_metrics.get('movement_pattern') in ['correcting_inward', 'straight']:
            print(f"{COLORS['green']}✓{COLORS['reset']} Sweep pattern indicates healthy growth.")
        print(f"\n{COLORS['cyan']}Diagnosis:{COLORS['reset']} {diagnosis}")
        print(f"{COLORS['cyan']}Recommendations:{COLORS['reset']} {fixes}")
        
    elif risk_score <= 20:
        print(f"{COLORS['yellow']}⚠{COLORS['reset']} Tree has noticeable lean - monitoring recommended.")
        if sweep_metrics:
            if sweep_metrics.get('sweep_quality') in ['excellent', 'good']:
                print(f"{COLORS['green']}✓{COLORS['reset']} Natural sweep pattern suggests stable growth.")
            elif sweep_metrics.get('sharpness_score', 0) > 0.6:
                print(f"{COLORS['orange']}⚠{COLORS['reset']} Sharp curve areas should be monitored for stress.")
        print(f"\n{COLORS['cyan']}Diagnosis:{COLORS['reset']} {diagnosis}")
        print(f"{COLORS['cyan']}Recommendations:{COLORS['reset']} {fixes}")
        
    elif risk_score <= 30:
        print(f"{COLORS['orange']}⚠{COLORS['reset']} Tree has significant lean - professional assessment recommended.")
        if sweep_metrics:
            if sweep_metrics.get('movement_pattern') == 'progressive_out':
                print(f"{COLORS['red']}⚠{COLORS['reset']} ALERT: Progressive lean detected - URGENT assessment needed.")
            elif sweep_metrics.get('sharpness_score', 0) > 0.6:
                print(f"{COLORS['orange']}⚠{COLORS['reset']} Sharp curves create stress points - increased failure risk.")
        print(f"\n{COLORS['cyan']}Diagnosis:{COLORS['reset']} {diagnosis}")
        print(f"{COLORS['cyan']}Recommendations:{COLORS['reset']} {fixes}")
        
    else:
        print(f"{COLORS['red']}✗{COLORS['reset']} Tree has severe lean - IMMEDIATE professional assessment required.")
        if sweep_metrics:
            if sweep_metrics.get('movement_pattern') == 'progressive_out':
                print(f"{COLORS['red']}{COLORS['bold']}✗ CRITICAL: Active progressive failure - DO NOT DELAY{COLORS['reset']}")
            elif sweep_metrics.get('sweep_quality') == 'critical':
                print(f"{COLORS['red']}✗{COLORS['reset']} Critical structural concerns identified.")
        print(f"\n{COLORS['cyan']}Diagnosis:{COLORS['reset']} {diagnosis}")
        print(f"{COLORS['cyan']}Recommendations:{COLORS['reset']} {fixes}")
    
    print("="*70 + "\n")