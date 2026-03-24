# [REF-0004: Type Chart System]
class TypeAdvantage:
    def __init__(self, chart=None):
        self.type_chart = chart if chart else {}

    def get_multiplier(self, attacker_type, defender_types):
        if not attacker_type or not defender_types:
            return 1.0

        multiplier = 1.0
        for defender_type in defender_types:
            multiplier *= self.type_chart.get(attacker_type,
                                              {}).get(defender_type, 1.0)
        return multiplier
