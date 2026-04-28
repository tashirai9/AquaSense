"""Rule-based conservation tips."""


def get_tips(amount_litres, season):
    """Return water-saving tips; inputs: amount in litres and season; output: list of tip dicts."""
    season = (season or "general").lower()
    seasonal_tip = {
        "summer": "Water outdoor plants early morning to reduce evaporation.",
        "winter": "Check geyser and hot-water pipe leaks weekly.",
        "spring": "Inspect garden hoses and sprinkler heads before frequent use.",
        "autumn": "Reuse rinse water for cleaning outdoor areas.",
    }.get(season, "Track daily usage to spot unusual spikes early.")

    if amount_litres < 100:
        return [{"urgency": "green", "tip": "Keep maintaining low-flow habits."}, {"urgency": "green", "tip": seasonal_tip}]
    if amount_litres <= 180:
        return [{"urgency": "yellow", "tip": "Shorten showers and run full laundry loads."}, {"urgency": "yellow", "tip": seasonal_tip}]
    return [{"urgency": "red", "tip": "Check for leaks and avoid non-essential water use today."}, {"urgency": "red", "tip": seasonal_tip}]
