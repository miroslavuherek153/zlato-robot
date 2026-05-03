def calculate_position_size(risk_amount, vstup, sl):
    risk_per_unit = abs(vstup - sl)
    if risk_per_unit <= 0:
        return 0
    return int(risk_amount / risk_per_unit)
