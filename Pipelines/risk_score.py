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


def display_risk_gradient(risk_score, tilt_angle):
    """
    Display a colorful gradient bar in the terminal showing risk level.
    """
    
    # Terminal color codes
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
    
    # Create gradient bar
    bar_length = 40
    marker_position = int((risk_score - 1) / 39 * (bar_length - 1))
    
    print("\n" + "="*60)
    print(f"{COLORS['bold']}TREE FALL RISK ASSESSMENT{COLORS['reset']}")
    print("="*60)
    
    # Display tilt angle
    print(f"\n{COLORS['cyan']}Tilt Angle:{COLORS['reset']} {abs(tilt_angle):.2f}° from vertical")
    direction = "RIGHT" if tilt_angle > 0 else "LEFT"
    if abs(tilt_angle) > 0.5:
        print(f"{COLORS['cyan']}Direction:{COLORS['reset']} Leaning {direction}")
    
    # Display risk score
    category, _ = get_risk_category(risk_score)
    print(f"\n{COLORS['cyan']}Risk Score:{COLORS['reset']} {risk_score:.1f} / 40")
    print(f"{COLORS['cyan']}Category:{COLORS['reset']} {category}")
    
    # Build the gradient bar
    print(f"\n{COLORS['bold']}Risk Level:{COLORS['reset']}")
    print("└─ 1" + " " * (bar_length - 6) + "40 ─┘")
    
    bar = ""
    for i in range(bar_length):
        # Determine color for this segment
        segment_score = 1 + (i / (bar_length - 1)) * 39
        
        if segment_score <= 10:
            color = COLORS['green']
            char = "█"
        elif segment_score <= 20:
            color = COLORS['yellow']
            char = "█"
        elif segment_score <= 30:
            color = COLORS['orange']
            char = "█"
        else:
            color = COLORS['red']
            char = "█"
        
        # Add marker at risk score position
        if i == marker_position:
            bar += f"{COLORS['blue']}{COLORS['bold']}▼{COLORS['reset']}"
        else:
            bar += f"{color}{char}{COLORS['reset']}"
    
    print("   " + bar)
    
    # Add legend
    print("\n" + " " * (marker_position + 3) + f"{COLORS['blue']}│{COLORS['reset']}")
    print(" " * (marker_position + 2) + f"{COLORS['blue']}{risk_score:.1f}{COLORS['reset']}")
    
    print("\n" + f"{COLORS['green']}■{COLORS['reset']} Low (1-10)   " +
          f"{COLORS['yellow']}■{COLORS['reset']} Moderate (11-20)   " +
          f"{COLORS['orange']}■{COLORS['reset']} High (21-30)   " +
          f"{COLORS['red']}■{COLORS['reset']} Critical (31-40)")
    
    # Risk interpretation
    print("\n" + "-"*60)
    print(f"{COLORS['bold']}INTERPRETATION:{COLORS['reset']}")
    
    if risk_score <= 10:
        print(f"{COLORS['green']}✓{COLORS['reset']} Tree appears stable with minimal lean.")
        print("  No immediate action required. Monitor during annual inspections.")
    elif risk_score <= 20:
        print(f"{COLORS['yellow']}⚠{COLORS['reset']} Tree has noticeable lean.")
        print("  Recommend inspection by arborist within 1 year.")
    elif risk_score <= 30:
        print(f"{COLORS['orange']}⚠{COLORS['reset']} Tree has significant lean - potential concern.")
        print("  Recommend professional assessment within 6 months.")
        print("  May need monitoring or support if near structures.")
    else:
        print(f"{COLORS['red']}✗{COLORS['reset']} Tree has severe lean - elevated fall risk.")
        print("  Consult certified arborist within 1-3 months.")
        print("  Consider remediation options or removal if necessary.")
    
    print("="*60 + "\n")