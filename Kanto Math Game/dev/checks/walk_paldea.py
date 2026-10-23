
# ---- areas expansion (areas_03_paldea.patch): Paldea is open world, so this walk only covers the added areas
story.badges = {"PALDEA": []}
story.inventory = {}
story.story_flags = {"visited_CABO_POCO": True}
story.defeated_trainers = {}
story.starting_region = "PALDEA"
R, S = "PALDEA", "CABO_POCO"
BASES = ["SEGIN_SQUAD_BASE", "SCHEDAR_SQUAD_BASE", "NAVI_SQUAD_BASE", "RUCHBAH_SQUAD_BASE", "CAPH_SQUAD_BASE"]
gate_check("team star bases", BASES, S, "met_team_star")
story.story_flags.update({"met_team_star": True, "has_paldea_starter": True})
PALDEA_NEW = BASES + ["SOCARRAT_TRAIL", "DALIZAPA_PASSAGE", "SOUTH_PROVINCE_AREA_4", "SOUTH_PROVINCE_AREA_6", "ALFORNADA_CAVERN",
              "INLET_GROTTO", "PORTO_MARINADA", "SOUTH_PALDEAN_SEA", "WEST_PALDEAN_SEA", "EAST_PALDEAN_SEA", "NORTH_PALDEAN_SEA"]
expansion_check("paldea expansion", PALDEA_NEW, S)
gate_check("great crater", ["GREAT_CRATER_OF_PALDEA"], S, "beat_paldea_champion")
story.story_flags.update({"beat_paldea_champion": True, "path_of_legends_complete": True, "starfall_street_complete": True})
expansion_check("paldea post-game expansion", ["GREAT_CRATER_OF_PALDEA"], S)
