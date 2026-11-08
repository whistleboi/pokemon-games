"""Kanto's walkable maps for dev/builders/build_town_maps.py (see its docstring for the characters), in story
order. The bigger ones are laid out with rectangles (town_maps/draw.py)."""
from town_maps.draw import Grid

G = '"'  # (tall grass)


ROUTE_22_ROWS = [  # (from Pokemon Journeys' map, tile by tile: its colours, read against its picture)
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccccccccccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccc........cccccc',
    'ccccccccccccGGGGGGGGGccccccccccccccccccccccccc.ccccccccc',
    'cccccccccckkGGGGDGGGGkkk========================..cccccc',
    'cccccccccckTTTT===TTTTk=========================..cccccc',
    'cccccccccckTTTT===TTTTk=========================TT......',
    'cccccccccck===========k.............cccccc......TT.====>',
    'cccccccccck===========k######.cccccccccccccc..ccTT.====>',
    'cccccccccck#######..##k"""""""c~~~~ccccccc""""""TT.====>',
    'cccccccccck...........k"""""""c~~~~ccccccc""""""TT.===cc',
    'cccccccccck...........k"""""""cccccccccccc""""""TT.===cc',
    'cccccccccckkk..!kkkkkkk"""""""......cccccc""""""TT.===cc',
    'cccccccccccc..........."""""""......cccccc""""""TT.===cc',
    'cccccccccccc........................cccccc............cc',
    'cccccccccccc###################################..#####cc',
    'cccccccccccc""""""""""""""""""""""""""""""""""""""""""cc',
    'cccccccccccc""""""""""""""""""""""""""""""""""""""""""cc',
    'cccccccccccc""""""""""""""""""""""""""""""""""""""""""cc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
]

def route_22():
    """Route 22, tile for tile after Pokemon Journeys' map (Map055, 56 x 40; Jordan, 11-07: exact): the
    Pokemon League's front gate (Route 23) in its fenced yard, the yard's sand and its ledge, in through the gap
    in the bottom fence beside the sign; the sand path east, its ledge, the tall grass, the pond in the rocks,
    the rock outcrop, the trees; east to Viridian City; the long strip of tall grass below the last ledge."""
    return list(ROUTE_22_ROWS)


VIRIDIAN_FOREST_ROWS = [  # (from Pokemon Journeys' map, tile by tile: its colours, read against its picture)
    'TTTTTGGGGGGGGGGG.TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTGGGGGGGGGGG"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTGGGGGGGGGGG"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTGGGGGGGGGGG"TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTGGGGGGGGGGG".T..T.TT..T.TTT.T..T..T..T..T..T..T..T.TTTTTTTT',
    'TTTTTGGGGGGGGGGG.......X.....TTT.............X..........TTTTTTTT',
    'TTTTTGGGGGGGGGGG.T=========T.TTT........................TTTTTTTT',
    'TTTTTGGGGGGGGGGG.===========.TTT........................TTTTTTTT',
    'TTTTTGGGGGGGGGGG.===========.TTT.....TTTTTTTTTTTTTTT....TTTTTTTT',
    'TTTTTGGGGGDGGGGG.===.....===.TTT.....TTTTTTTTTTTTTTT....TTTTTTTT',
    'TTTTTTTT#===#TTT.T=T.....T=T.TTT.....TTTTTTTTTTTTTTT....TTTTTTTT',
    'TTTTTTTT#===#TTT.....TTT.....TTT.....TTTTTTTTTTTTTTT....TTTTTTTT',
    'TTTTTTTT...!"TTT"""""TTT"""""TTT"""""TTTTTTTTTTTTTTT....TTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT"""""TTT"""""TTTTTTTTTTTTTTT....TTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT"""""TTT""""""T""T".T..T..T.....TTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT"""""TTT""""""""""".............TTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT"""""TTT"""""""""""..T=T........TTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT"""""TTT"""""""""""..===........TTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT"""""TTT"""""""""""..===..TTTTTTTTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT"""""TTT"""""""T""...===..TTTTTTTTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT"""""TTT""""""TTTTTT.===..TTTTTTTTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT"""""TTT..."""TTTTTT.===..TTTTTTTTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT....."T"......TTTTTT.===..TTTTTTTTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTT..T=========T.TTTTTT.===..TTTTTTTTTTTTTT',
    'TTTTTTTT"""""TTT"""""TTTTT===========.TTTTTT.===..TT..T.TTTTTTTT',
    'TTTTTTTT"""""TTT""""""TTTTT=========T.TTTTTT.===..X.....TTTTTTTT',
    'TTTTTTTT""""".T."""""""TTTTTTTTTTTTTTTTTTTTT.===!.......TTTTTTTT',
    'TTTTTTTT"""""..."""""""TTTTTTTTTTTTTTTTTTTTT.====T......TTTTTTTT',
    'TTTTTTTT...............TTTTTTTTTTTTTTTTTTTTT.T===T......TTTTTTTT',
    'TTTTTTTT.T=T..!...T=T..TTTTTTTTTTTTTTTTTTTTT""""........TTTTTTTT',
    'TTTTTTTT.============...T..T.TTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTT.============........TTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTT.T==========T........TTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTT.....................TTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTT......TTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTT......TTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTT"T""T""T""T""T"TTTTTTTTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTT"""""""""""""""TTTTTTTTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTT"""""""""""""""TTTTTTTTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTT"""""""""""""""TTTTTTTTTTTTTTTTTTTTT"""""TTT....TTTTTTTT',
    'TTTTTTTT""""""""""""""""T""T""T""T""T"TTTTTT""""".T.....TTTTTTTT',
    'TTTTTTTT"T""T""T""""""""""""""""".""""TTTTTT""""........TTTTTTTT',
    'TTTTTTTTTTTTTTTTT""""""""""""""""...""TTTTTT"""...X.....TTTTTTTT',
    'TTTTTTTTTTTTTTTTT""""""T""T""T"""...""TTTTTT""".........TTTTTTTT',
    'TTTTTTTTTTTTTTTTT.."""TTTTTTTTT""...""TTTTTT"""...TTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTT.."""TTTTTTTTT""...""TTTTTT"""...TTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTT.."""TTTTTTTTT""...""TTTTTT"""...TTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTT.."""TTTTTTTTT""...""TTTTTT"""...TTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTT.."""TTTTTTTTT""...""TTTTTT"""...TTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTT.."""TTTTTTTTT""...""TTTTTT"""...TTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTT.."""TTTTTTTTT""...""TTTTTT"""...TTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTT.."""TTTTTTTTT""...""TTTTTT"""...TTTTTTTTTTTTTT',
    'TTTTTTTT"T""T""T"..""""T""T""T"""..."".T..T."""..."T""T"TTTTTTTT',
    'TTTTTTTT"""""""""..""""""""""""""TTT""......"""...""""""TTTTTTTT',
    'TTTTTTTT"""""""""..""""""""""""""TTT"""""""""""...""""""TTTTTTTT',
    'TTTTTTTT"""""""""...""""""""""""..T.."""""""""..."""""""TTTTTTTT',
    'TTTTTTTT"""""""""....""""""""""......."""""""...."""""""TTTTTTTT',
    'TTTTTTTT""""""""....T==========T............!...."""""""TTTTTTTT',
    'TTTTTTTT""""""""....============X...!...........""""""""TTTTTTTT',
    'TTTTTTTT"T""T""T....T==========T."T"............T""T""T"TTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.vvv..TTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTBBBBBBBBBBBTTTTTTTTTTTTTTTTTTTTTTTT',
]

def viridian_forest():
    """Viridian Forest, tile for tile after Pokemon Journeys' map (Map326, 64 x 69; Jordan, 11-07: exact): in
    from Viridian City at the gate at the bottom, out through the gate at the top left to Route 2; the maze of
    tree blocks (only a tree's trunk tile in the way under its crown), the tall grass, the sand patches, the
    lawn paths; five trainers on their own spots, the signs where the original has them."""
    return list(VIRIDIAN_FOREST_ROWS)


ROUTE_2_ROWS = [  # (from Pokemon Journeys' map, x 13-38, rows 0-29: tile_classify.py, then by hand)
    'TTTTTTTTT.^^^TTTTTTTTTTTTT',
    'TTT.......===..........TTT',
    'TTT"""""""===##########TTT',
    'TTT"""""""===#.........TTT',
    'TTT"""""""===#.........TTT',
    'TTT"""""""===#.........TTT',
    'TTT"""""""===#QQQQQQQQ.TTT',
    'TTT"""""""===#QQQQQQQQ.TTT',
    'TTT"""""""===#QQQQQQQQ.TTT',
    'TTT..========#QQQQQQQQ.TTT',
    'TTT..========#QQQQQQQQ.TTT',
    'TTT..========#QQQQDQQQ.TTT',
    'TTT..====....#.!dddddd.TTT',
    'TTT##vvvv###.#.ddddddddTTT',
    'TTTGGGGGGGG#...ddddddddTTT',
    'TTTGGGGGGGG....ddddddddTTT',
    'TTTGGGGGGGGTTTT.dddddd.TTT',
    'TTTGGGGGGGGTTTT""".....TTT',
    'TTTGGGGGGGGTTTT"""""...TTT',
    'TTTGGGGGGGGTTTT"""""...TTT',
    'TTTTTTTTTTTTTTTAAAAA...TTT',
    'TTTTTTTTTTTTTTTAAAAAdddTTT',
    'TTTTTTTTTTTTTTTAAADAdddTTT',
    'TTTTTTTTTTTTTTT..ddddddTTT',
    'TTTTTTTTTTTTTTTTTddddddTTT',
    'TTTTTTTTTTTTTTTTTddddddTTT',
    'TTTTTTTTTTTTTTTTT##.###TTT',
    'TTTTTTTTTTTTTTTTT""."""TTT',
    'TTTTTTTTTTTTTTTTT""."""TTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTT',
]

def route_2():
    """Route 2's north stretch, tile for tile after Pokemon Journeys' map (Map035, its x 13-38, rows 0-29;
    Jordan, 11-07: exact): in from Viridian Forest's north gate (its way in is on top), the sand path north to
    Pewter City; the Cut tree into the east side is an open gap; Diglett's Cave in its fenced yard, its sign; Oak's aide's house; the tall grass and the pale
    grass paths. (Viridian City leads straight into the Forest, so the route's south stretch isn't walked.)"""
    return list(ROUTE_2_ROWS)


def pewter_city():
    """Pewter City, tile for tile after assets/backgrounds/kanto/pewter_city.png (57 x 47, 16 px tiles, grid
    phase 7,2; Jordan, 11-07: exact): cliffs round it; the Museum (and its wing) up on the lawn with the hedges,
    down its steps to the gray roads; the Gym on its raised lawn in its ring of trees (its own steps, the statue
    by them, the white posts along the west walk); the house up the east steps; the Mart and its little raised
    lawn; the Pokemon Center's plaza; the house below the walled garden (a gap: its ledge was a hop down); the
    fenced flower garden on its raised block (steps, a gate, the white posts); lamp posts; east past the lamps
    to Route 3, south between the fences down the sand path to Route 2."""
    g = Grid(57, 47, "c")
    # the north lawn, its trees and the Museum
    g.rect(3, 5, 47, 8, ".").rect(3, 7, 1, 13, ".").rect(4, 19, 4, 1, ".")
    g.rect(3, 3, 14, 2, "T").rect(3, 5, 6, 2, "T").rect(10, 6, 6, 4, "T").rect(4, 8, 12, 3, "T")
    g.rect(4, 11, 4, 8, "T").rect(8, 8, 1, 3, "T")
    g.rect(32, 3, 18, 2, "T").rect(42, 5, 8, 2, "T").rect(30, 8, 4, 3, "T").rect(34, 8, 6, 4, "T")
    g.building(17, 2, 11, 7, "U", door_x=5)   # the Museum
    g.rect(28, 3, 4, 4, "W")                  # its wing
    g.rect(21, 9, 3, 2, "p")
    g.rect(16, 10, 4, 1, "T").rect(25, 10, 5, 1, "T")   # the hedges
    g.rect(40, 9, 4, 1, "#").put(43, 8, "#")  # a little ledge
    for x, y in ((3, 8), (3, 16), (38, 6), (44, 8), (40, 11), (41, 11)):
        g.put(x, y, "f")
    g.rect(8, 11, 12, 1, "#").rect(25, 11, 9, 1, "#").put(33, 12, "#").rect(33, 13, 8, 1, "#")   # ledges
    g.rect(8, 12, 1, 8, "#")
    g.rect(20, 11, 5, 1, "=").rect(46, 13, 3, 1, "=")   # steps
    # the roads and the walks
    g.rect(9, 12, 11, 1, "p").rect(26, 12, 7, 1, "p").rect(9, 13, 2, 11, "p").rect(10, 24, 1, 15, "p")
    g.rect(20, 12, 5, 1, "a").rect(11, 13, 21, 2, "a").rect(11, 13, 2, 13, "a").rect(11, 24, 13, 2, "a")
    g.rect(28, 15, 2, 24, "p").rect(30, 13, 2, 26, "a").rect(47, 14, 2, 25, "a").rect(49, 14, 1, 14, "p")
    g.rect(49, 32, 1, 7, "p").rect(49, 28, 1, 4, "a")
    g.rect(32, 19, 15, 2, "a").rect(32, 26, 15, 2, "a").rect(10, 37, 39, 2, "a")
    g.rect(9, 24, 1, 15, ".").put(9, 27, "r")
    # the Gym on its raised lawn
    g.rect(13, 15, 2, 9, "p").rect(15, 15, 13, 7, ".")
    g.rect(15, 15, 1, 8, "#").rect(27, 15, 1, 8, "#").rect(15, 22, 5, 1, "#").rect(23, 22, 4, 1, "#")
    g.rect(20, 22, 3, 1, "=")
    g.rect(16, 15, 2, 6, "T").rect(25, 15, 2, 6, "T")
    g.building(18, 15, 7, 6, "G", door_x=3)
    g.rect(13, 23, 13, 1, "p").rect(24, 24, 2, 2, "p").rect(26, 23, 2, 3, "T").rect(10, 26, 18, 2, "T")
    for y in (16, 17, 19, 20, 22, 23):
        g.put(13, y, "j")                     # the white posts
    # the east house, its walk and trees
    g.rect(32, 14, 15, 5, "p").put(32, 13, "p").rect(33, 15, 8, 2, "T").rect(33, 17, 8, 1, ".")
    g.building(41, 13, 5, 5, "H", door_x=1)
    # the Mart and its little raised lawn
    g.rect(32, 21, 15, 5, "p")
    g.building(33, 21, 4, 4, "M", door_x=2)
    g.rect(38, 22, 2, 3, "T").put(39, 21, "#")
    g.rect(40, 21, 5, 3, ".").rect(45, 21, 1, 4, "#").rect(40, 24, 5, 1, "#").rect(42, 24, 2, 2, "=")
    g.put(42, 21, "f").put(40, 22, "f")
    # the Pokemon Center's plaza, the house below the walled garden
    g.rect(17, 28, 12, 6, "p")
    g.building(20, 28, 5, 5, "C", door_x=2)
    g.rect(9, 28, 1, 4, "#").rect(10, 28, 6, 3, ".").rect(16, 28, 1, 4, "#").rect(10, 31, 6, 1, "#")
    g.put(16, 29, ".")                        # (a gap: its ledge was a hop down)
    g.put(12, 29, "f").put(10, 30, "f")
    g.rect(10, 32, 10, 5, "p")
    g.building(10, 32, 4, 4, "J", door_x=1)
    g.rect(14, 34, 4, 3, "T")
    g.rect(20, 34, 12, 1, "a").rect(20, 34, 2, 4, "a").rect(22, 35, 7, 2, "p")
    # the flower garden on its raised block
    g.rect(32, 28, 15, 2, "p").rect(46, 28, 1, 10, "p")
    for x in range(32, 45, 2):
        g.put(x, 29, "j")
    g.rect(32, 30, 1, 7, "#").rect(45, 30, 1, 7, "#").rect(33, 36, 12, 1, "#").rect(38, 36, 2, 1, "=")
    g.rect(33, 30, 12, 6, "k").rect(34, 31, 10, 4, "f").rect(38, 31, 2, 5, ".")
    # lamp posts
    for x, y in ((9, 13), (9, 18), (9, 22), (28, 18), (28, 22), (28, 27), (28, 32), (49, 13), (49, 38),
                 (50, 28), (50, 32), (13, 40), (18, 40)):
        g.put(x, y, "l")
    # east to Route 3
    g.rect(50, 29, 7, 3, ".").rect(51, 28, 6, 5, ".").rect(53, 29, 4, 2, "=").rect(56, 28, 1, 5, ">")
    g.put(52, 30, "N")                        # the boy (till you've beaten Brock)
    # south to Route 2
    g.rect(0, 39, 57, 8, "T").rect(50, 39, 7, 8, "c").rect(9, 38, 1, 1, ".")
    g.rect(12, 39, 8, 2, ".").rect(14, 41, 4, 6, ".").rect(15, 42, 2, 5, "=")
    g.rect(12, 41, 2, 1, "k").rect(18, 41, 2, 1, "k").rect(13, 42, 1, 5, "k").rect(18, 42, 1, 5, "k")
    g.rect(14, 46, 4, 1, "v")
    # signs
    g.put(25, 12, "!").put(19, 23, "!").put(38, 30, "!").put(19, 36, "!")
    return g.rows()


ROUTE_3_ROWS = [  # (from Pokemon Journeys' map, x 0-81, rows 0-19: colour shares, then by hand)
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccCCCCQQQQccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccCCCCQQQQccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccCCDCQQDQccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc========ccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc========ccccc',
    'ccccccccccccc======================cccccccccccccccccccccccccccccccccc========ccccc',
    'ccccccccccc==============X===========cccccccccccccccccccccccccccccccc.....cccccccc',
    'ccccccccccc======.......=============cccccc================cccccccccc.....cccccccc',
    'ccccccccccc..X......ccc.......cc..===ccccc===================cccccccc.....cccccccc',
    'ccccccccccc###..####ccc.######cc###..ccccc====...........====cccccccc.....cccccccc',
    'ccccccc.............ccc.......cc.....ccccc####..ccccccc#####.cccccccc###..cccccccc',
    '<...................ccc.......cc................ccccccc......cccccccc.....cccccccc',
    '<.................X.ccc.......ccc...............ccccccc......cccccc.......""""cccc',
    '<........ccc........ccc.......ccc""""""X........ccccccc................##!""""""cc',
    '..cccccccccc####..##ccc#######ccc""""""""""""""cccccccc.................""""""""cc',
    'cccccccccccc""""""""ccc"""""""ccc""""""""""""""cccccccc.................""""""""cc',
    'cccccccccccc"""""""""""""""""cccccc""""""""""""ccccccccf.f............."""""""""cc',
    'cccccccccccccc"""""""""""""""cccccc""""""""""""cccccccccc.f............"""""""""cc',
    'ccccccccccccccccccccccccccccccccccccccc""""""""ccccccccccf.f.f.........""""""ccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
]

def route_3():
    """Route 3, tile for tile after Pokemon Journeys' map (Map036, its x 0-81, rows 0-19; Jordan, 11-07: exact):
    east from Pewter between the cliffs, the sand path up top with its ledges (their own gaps), the tall grass
    below, the flowers, the sign by the fence posts; north up the sand clearing, where Route 4 would start, to
    the Pokemon Center beside Mt. Moon's mouth (Jordan, 11-07: keep the Center on Route 3)."""
    return list(ROUTE_3_ROWS)


MT_MOON_FLOORS = [  # (from Pokemon Journeys' Mt. Moon, Map332, tile by tile: 1F its x 0-47, rows 0-39;
    # B1F its x 75-121, rows 0-37 (its four rooms where they lie); B2F its x 10-58, rows 70-109. Ladders pair
    # in reading order exactly as its warps do: 1F's three down to B1F's rooms A, B, D; B1F's C, B, A, D
    # down to B2F's NW, NE, middle, south. Out to Route 4 from room C, as in the original.)
    [  # 1F
        'cccccccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccccccc',
        'ccssssssss.rrcccccccsssssssssssssssssssssssssscc',
        'ccssssss....rccccccssssssssssss......ssssssssscc',
        'ccssss.......cccccssssssssss.............ssssscc',
        'ccsss........ccccr.ssssssss...............sssscc',
        'ccsss+.......cccc...ssss...................ssscc',
        'ccss........scccr........................r..sscc',
        'ccss........sccc........................rrrrsscc',
        'ccss........sccc.........................rr.sscc',
        'ccss.......ssccc....ccccccccccccccc.........sscc',
        'ccs........ssccc....ccccccccccccccc..........scc',
        'ccs........ssccc....ccccccccccccccc..........scc',
        'ccs........ssccc....cccrr.....rrrr..ss.......scc',
        'ccs........ssccc...+cccr............ss.ccc...scc',
        'ccs........ssccc....cccr...........sss.ccc...scc',
        'ccs........ssccc....ccc........+..ssss.ccc....cc',
        'cc.........sssss....ccc....ccc..ssssss.ccc....cc',
        'cc..........sss.....ccc....ccc.sssssss.ccc....cc',
        'ccccccccccc.........ccc....ccc.sssssss.ccc....cc',
        'ccccccccccc.........ccc....ccc.sssssss.ccc....cc',
        'ccccccccccc.........ccc....ccc.sssssss.ccc....cc',
        'cc....rrccccccccccccccc....ccc.sssssss.ccc....cc',
        'cc.....rccccccccccccccc....ccc..ssssss.ccc....cc',
        'cc......ccccccccccccccc....ccc..sssss..ccc....cc',
        'cc......ccc................ccc...ssss..ccc....cc',
        'cc......ccc........!.......ccc.........ccc....cc',
        'cc......ccc................ccc.........ccc....cc',
        'cc.........................ccc.........ccc....cc',
        'cc..................cccccccccc...ccc...ccc...scc',
        'cc..................cccccccccc...ccc...ccc...scc',
        'cc............rr....cccccccccc...ccc...ccc...scc',
        'cc...........cccc...ccccr........ccc.........scc',
        'cc...........cccc...ccccrr.......ccc........sscc',
        'cc...........cccc...ccccrr.......ccc........sscc',
        'cc...........cccc...ccccr..................ssscc',
        'cc...........cccc...cccc..................sssscc',
        'cc...........cccc...cccc..............sssssssscc',
        'ccccccccccccccccccvccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccccccc',
    ],
    [  # B1F
        'ccccccccccccccccccccccccccccccccccccccccccccccc',
        'ccccccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccrr........rcccccccccrrrrr.....rc',
        'c.-...cccccccccr.........rcccccccccrr........rc',
        'c.....ccccccccc.........-.cccccccccr..+.......c',
        'c.....ccccccccc.+.........ccccccccc...........c',
        'c.....cccccccccccccccccccccccccccccccccccccvccc',
        'c.....ccccccccccccccccccccccccccccccccccccccccc',
        'c.....ccccccccccccccccccccccccccccccccccccccccc',
        'c....rccccccccccccccccccccccccccccccccccccccccc',
        'c.....ccccccccccccccccccccccccccccccccccccccccc',
        'c...r.ccccccccccccccccccccccccccccccccccccccccc',
        'c....rccccccccccccccccccccccccccccccccccccccccc',
        'c.....ccccccccccccccccccccccccccccccccccccccccc',
        'c.....ccccccccccccccccccccccccccccccccccccccccc',
        'c.....ccccccccccccccccccccccccccccccccccccccccc',
        'c......................cccccccccccccccccccccccc',
        'c......................cccccccccccccccccccccccc',
        'c....................+.cccccccccccccccccccccccc',
        'ccccccccccccccccccccccccccccccccccccccccccccccc',
        'ccccccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccc..-.ccc',
        'cccccccccccccccccccccccccccccccccccccccc....ccc',
        'cccccccccccccccccccccccccccccccccccccccc....ccc',
        'cccccccccccccccccccccccccccccccccccccccc....ccc',
        'cccccccccccccccccccccccccccccccccccccccc....ccc',
        'cccccccccccccccccccccccccccccccccccccccc....ccc',
        'cccccccccccccccccccccccccccccccccccccccc....ccc',
        'cccccccccccccccccccccccccccccccccccccccc....ccc',
        'cccccccccccccccccccccccccccccccccccccccc....ccc',
        'cccccccccccccccccccccccccccccccccccccccc....ccc',
        'ccccccccccccccccccccccccccccccccccccccccr...ccc',
        'ccccccccccccccccccccccccccccccccccccccccr...ccc',
        'ccccccccccccccccccccccccccccccccccccccccr...ccc',
        'cccccccccccccccccccccccrr...........rrrr....ccc',
        'cccccccccccccccccccccccr....................ccc',
        'ccccccccccccccccccccccc.+...................ccc',
        'ccccccccccccccccccccccccccccccccccccccccccccccc',
    ],
    [  # B2F
        'ccccccccccccccccccccccccccccccccccccccccccccccccc',
        'ccccccccccccccccccccccccccccccccccccccccccccccccc',
        'ccccccccccccccccccccccccccccccccccccccccccccccccc',
        'ccc.................ccccccccccccccccccccccccccccc',
        'ccc.................ccccccccccccccccccccccccccccc',
        'ccc.................ccc....cccccc....cccccccccccc',
        'ccc.................ccc....c....c....c....ccccccc',
        'ccc==cccccccc..cccccccc....c....cc==cc....ccccccc',
        'cc..................ccc....c..........N...ccccccc',
        'cc...r..c...........ccc....c..............ccccccc',
        'cc...-r.c...........ccc....c..rr.....NN...ccccccc',
        'cc......c...........ccc....c..r-.......r..ccccccc',
        'cc.....rccccc==ccc..ccc....c..............ccccccc',
        'ccccccccr........c..ccc....c..............ccccccc',
        'cccccccc.........c..ccc............cc...........c',
        'cccccccc.........cccccc............cc..........cc',
        'cccccccc............rcc............cc..........cc',
        'cccccccccccc...cccccccc............cc..........cc',
        'cccccccccccc...cccccccc......cc==ccccc==cc.....cc',
        'cccccccccccc...cccccccc......c...........c.....cc',
        'cccccccccccc...cccccccc..r...c...........c.....cc',
        'cccccccc.............cc..-.r.c...........c.....cc',
        'c~~~~~cc.............cc...r..c...........c.....cc',
        '~~~~~~~c.....cccccccccccccccccccccccccccccc....cc',
        '~~~~~~~c.....cccccccccccccccccccccccccccccc....cc',
        '~~~~~~~c.....cccccccccccccccccccccccccccccc....cc',
        '~~~~~~~c.....ccccccccccccccc....ccccccccccc....cc',
        '~~~~~~~c.....cc............c....c..cc..........cc',
        '~~~~~~~c.....ccr...........cc==cc..cc..........cc',
        '~~~~~~~c.....cc....................cc.....ccccccc',
        '~~~~~~~c.....cc..r.................cc.....cc~~~cc',
        '~~~~~~~c.....cc.r-.................cc.....c~~~~~c',
        '~~~~~~~c.....ccrr..................cc.....c~~~~~c',
        '~~~~~~~c.....cccccccccccccccccccccccc.....c~~~~~c',
        '~~~~~~~c.....cccccccccccccccccccccccc.....c~~~~~c',
        '~~~~~~~c.....cccccccccccccccccccccccc.....c~~~~~c',
        '~~~~~~~c.....cccccccccccccccccccccccc.....c~~~~~c',
        '~~~~~~~c..................................c~~~~~c',
        '~~~~~~~c..................................c~~~~~c',
        '~~~~~~~cccccccccccccccccccccccccccccccccccc~~~~~c',
    ],
]

def mt_moon_1f():
    """Mt. Moon 1F, tile for tile after Pokemon Journeys' map (Jordan, 11-07: exact): in from Route 3 at the
    bottom; the rock ridges and pillars, the sandy edges, the rocks; three ladders down; the sign."""
    return list(MT_MOON_FLOORS[0])


def mt_moon_b1f():
    """Mt. Moon B1F: the four little rooms between the floors, each where the original has it (they don't
    join: "parts"); room C's way out to Route 4."""
    return list(MT_MOON_FLOORS[1])


def mt_moon_b2f():
    """Mt. Moon B2F: the rock walls with their wooden steps, the water down both sides, the four ladders up (the
    south room, its steps and nook, only by its own ladder from B1F's room D, as in the original: "parts");
    the Super Nerd and the two fossils in the north-east room (Team Rocket about)."""
    return list(MT_MOON_FLOORS[2])


ROUTE_4_ROWS = [  # (from Pokemon Journeys' map, x 30-111, rows 11-29: colour shares, then by hand)
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccc""#......#"ccccccccc.#.....#ccccccccccccccc....=======ccccccccccc',
    'cccccQQQccccccccc""#......#""#.f.f.#..#.""".#f.f................=================>',
    'cccccQQQccccccccc""#......#""#f.f.f#..#.""".#.f.fX..............=================>',
    'cccccQDQccccccc""""###..###""#.....#..#.""".#.########################kkkkkkkkkkkk',
    'ccccc=========...............#.""".#..#...............................kk~~~~~~~~~~',
    'ccccc==!======...............#.."..#..##..############################kk~~~~~~~~~~',
    'cccc.........................#.....#..................................kk~~~~~~~~~~',
    'cccc###########...############.===.###......................TTTT######kkkkkkkkkkkk',
    'cccc"""""""""".................===...######..TTTT.##########TTTT..===============>',
    'cccc""""""""""..........====================.TTTT"""""""""""TTTT..===============>',
    'ccccccccccccccc.........====X===============.TTTT"""""""""""""TT..===============>',
    'cccccccccccccccccccTTTT.====================.TTTT"""""""""""""TT..===.kkkkkkkkkkkk',
    'ccccccccccccccccccc""""......................TTTT"""""""""""""TT##===#kTTTTTTTTTTT',
    'ccccccccccccccccccccccc##..#########..#####TTTTTT"""""""""""""TT..===.kTTTTTTTTTTT',
    'ccccccccccccccccccccccc.f.f................TTTTTT"""""""""""".""..===.kTTTTTTTTTTT',
    'cccccccccccccccccccccccf.f.f.f............XTT"""""""""""""""..........kTTTTTTTTTTT',
    'cccccccccccccccccccccccccccccc.............""ccccccccccccccc.........ccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
]

def route_4():
    """Route 4, tile for tile after Pokemon Journeys' map (Map037, its x 30-111, rows 11-29; Jordan, 11-07:
    exact): out of Mt. Moon's east mouth by the sign, the ledges (fences, their own gaps), the tall grass, the
    sand paths, the pine trees, the flowers (gaps at the west ends of the ledge below the north sand path and the one above the big tall grass: in
    the original you only hop down it); the fenced pond and the fenced trees; east to Cerulean City. (Its
    west end, the Pokemon Center and Mt. Moon's way in, is on Route 3 in our game: Jordan, 11-07.)"""
    return list(ROUTE_4_ROWS)


CERULEAN_CITY_ROWS = [  # (from assets/backgrounds/kanto/cerulean_city.png: its tiles x 1-64, rows 1-52 at
    # 16 px, grid phase 5,4: tile_classify.py, then by hand from zoomed crops)
    'cccccccccccccccccccccccccccccccccccoooooi^^^^i~~Tk^^^^^r^^cccccc',
    'cccccccccccccccccccccccccccccccccccoooooi====i~~Tk.====...cccccc',
    'cccccccccccccccccccccccccccccccccccoooooi====i~~Tk.====...cccccc',
    'cccccccccccccccccccccccccccccccccccooooci====iTTTT....=TTTcccccc',
    'cccccccccccccccccccccccccccccccccccooooc......TTTT....TTTTcccccc',
    'ccccccccccccccccccoooooooooooooooooooooc......TTTT....TTTTcccccc',
    'ccccccccccccccccccoooooooooooooooooooooc..aa..TTTT....TTTTcccccc',
    'ccccccccccoooooooooooooooooooooooooooooc.!aaal.....###TTTTcccccc',
    'ccccccQQccooooooooooooc...f.f..........c..aaa..T.T....TTTTcccccc',
    'ccccccDQccooooccooooooc.f...#.f....f...c..aaa.TTTT....TTTTcccccc',
    'cccf..==..oooocc..f.........=..........=..aaa.TTTT....TTTTcccccc',
    'cccf..==..oooocc..f.HHHHIIII=.....f....=..aaa.TTTT....TTTTcccccc',
    'ccc.......oooocc....HHHHIIII#..........c..aaal........TTTTcccccc',
    'oooooooooooooocckkkkHHHHIIIIkkkkkkkkkkkkk.aaa.........TTTTcccccc',
    'oooooooooooooocckfffHHHHIIII..aaaaaaaaaaaaaaa.TTTTTTTTTTTTcccccc',
    'oooooooooooooocckfffHDHHIDII..aaaaaaaaaaaaaaa.TTTTTTTTTTTTcccccc',
    'kkkkkkkkkkkkkkkkk.............aaa.....TT.aaaa..KKKKTTTTTTTcccccc',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa..JJJJT..aaal.KKKKTTTTTTTcccccc',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa..JJJJT..aaa..KKKKTTTTTTTcccccc',
    '.....l.aaaalTTTTTTl....lTTTTlaaaa..JJJJT..aaa..KDKKTTTTTTTcccccc',
    'kkkkkkk.aaa...................aaa.!JDJJT..aaaT....TTTTTTTTcccccc',
    'TTTTTTk.aaa...................aaa.....TT..aaaT....TTTTTTTTcccccc',
    'TTTTTTk.aaa.yy..yy............aaa.....TT..aaaT....TTTTTTTTcccccc',
    'TTTTTTk.aaa........LLLLCCCCCC.aaaaaaaaTT..aaaT.....T.T.T.Tcccccc',
    'TTTTTTk.aaa........LLLLCCCCCC.aGGGGGGGTT..aaaT............cccccc',
    'TTTTTTk.aaa....~...LLLLCCCCCC..GGGGGGGTT..aaal....kkkkkkkkkkkkkk',
    'TTTTTTk.aaa........LLLLCCCCCC..GGGGGGGTT..aaaaaaaaaaaaaaaaa....>',
    'TTTTTTk.aaal......lLDLLCCDCCC..GGGGGGGTT..aaaaaaaaaaaaaaaaa....>',
    'TTTTTTk.aaa....................GGGGGGGTT..aaaaaaaaaaaaaaaaa....>',
    'TTTTTTk.aaaaaaaaaaaaaaaaaaaaaa.GGGGDGG...####l....kkkkkkkkkkkk..',
    'TTTTTTk.aaaaaaaaaaaaaaaaaaaaaa.......!....aa.T....TTTTTTTTcccck.',
    'TTTTTTk.aaa........aaa...!.aaaaaaaaaaaaaaaaaaT....TTTTTTTTcccck.',
    'TTTTTTk.aaa........aaa.....aaaaaaaaaaaaaaaaaaT....TTTTTTTTcccck.',
    'TTTTTTk.aaa.BBBBB..aaa.MMMMMOOOO..........aaaT....TTTTTTTTcccck.',
    'TTTTTTk.aaa.BBBBB..aaa.MMMMMOOOO.fffffff..aaaT....TTTTTTTTcccck.',
    'TTTTTTk.aaa.BBBBB..aaa.MMMMMOOOO.fffffff..aaaT....TTTTTTTTcccck.',
    'TTTTTTk.aaa!BBDBB..aaa.MMDMMODOO.fffffff..aaaT....TTTTTTTTcccck.',
    'TTTTTTk.aaa........aaa...........fffffff..aaal....TTTTTTTTcccck.',
    'TTTTTTk.aaa.......aaaa...................aaaa.....TTTTTTTTcccck.',
    'TTTTTTk.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.....TTTTTTTTcccccc',
    'TTTTTTk.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa......TTTTTTTTcccccc',
    'TTTTTTkTTTTTl......lTTTTTTTTTTTT.lTTTTTTTTTTTl....TTTTTTTTcccccc',
    'TTTTTTk...........................................TTTTTTTTcccccc',
    'TTTTTTk...........................................TTTTTTTTcccccc',
    'TTTTTTk....TT......TT.....kkkkkkkkkkkkkkkkkkkkkkkkTTTTTTTTcccccc',
    'TTTTTTk....TT......TT.....kTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTcccccc',
    'TTTTTTk....TT......TT.....kTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTcccccc',
    'TTTTTTk....TT......TT.....kTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTcccccc',
    'TTTTTTk....TT#####.TTT....kTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTcccccc',
    'TTTTTT.#.##TT""""""TT###.#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTcccccc',
    'TTTTTT..===TT""""""TTT===.TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTcccccc',
    'TTTTTT..vvvTTvvvvvvTTTvvv.TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTcccccc',
]

def cerulean_city():
    """Cerulean City, tile for tile after assets/backgrounds/kanto/cerulean_city.png (64 x 52; Jordan, 11-07:
    exact): the cliffs and the river across the top, Cerulean Cave on its island (by Surf, after the title);
    the Nugget Bridge north to Route 24, and the path down from Route 24 beside it (north-east: the way to the
    cave by Surf; Jordan, 11-08; a gap in its ledge); the lawn above the fence with its little wooden steps; the houses,
    the Pokemon Center, the Gym, the Mart, the Bike Shop; the gray streets, the hedges and lamp posts, the
    benches and the fountain, the flower bed; east past the fence to Route 9; south down three ways (the
    rails and the ledge, each with a gap) to Route 5."""
    return list(CERULEAN_CITY_ROWS)


def route_24():
    """Route 24, tile for tile after Pokemon Journeys' map (Map057, its x 18-39, rows 3-41; Jordan, 11-07:
    exact): the Nugget Bridge north from Cerulean over the river (five trainers on it, left and right, the
    Rocket at its north end), the tall grass by the water, the sand path up to the cliffs, its ledges (a gap
    into the north-east lawn), the flowers, the hedge; east to Route 25."""
    g = Grid(22, 39, "c")
    P = lambda x, y: (x - 18, y - 3)          # (the original's tiles)
    def rect(x, y, w, h, ch):
        g.rect(*P(x, y), w, h, ch)
    rect(20, 5, 10, 4, "="); rect(31, 5, 3, 4, "="); rect(35, 5, 5, 3, ".")
    rect(25, 8, 5, 1, "#"); rect(34, 5, 1, 4, "c"); rect(34, 8, 6, 1, "#"); rect(35, 8, 1, 1, ".")
    rect(19, 9, 21, 3, "=")
    rect(19, 12, 10, 9, "."); rect(26, 12, 3, 7, "=")
    for x, y in ((19, 12), (21, 12), (20, 13), (19, 14), (20, 15), (19, 16)):
        g.put(*P(x, y), "f")
    rect(29, 12, 11, 1, "T"); rect(29, 12, 1, 7, "T")     # the hedge
    rect(30, 13, 10, 1, "."); rect(30, 14, 3, 28, ".")
    rect(33, 28, 1, 14, "k"); rect(34, 29, 6, 13, "~")
    rect(19, 21, 3, 13, '"'); rect(22, 18, 3, 24, "~"); rect(20, 34, 2, 8, "~")
    rect(25, 18, 1, 24, "i"); rect(29, 19, 1, 23, "i"); rect(26, 19, 3, 23, "=")   # the bridge
    rect(29, 19, 1, 1, ".")                   # (the lawn east of the bridge: in by its north end)
    rect(26, 41, 3, 1, "v"); rect(39, 9, 1, 3, ">")
    rect(30, 41, 3, 1, "v")                   # (the lawn east of the bridge: down to Cerulean's north-east)
    for x, y in ((27, 20), (26, 25), (28, 28), (26, 31), (28, 34), (26, 37)):
        g.put(*P(x, y), "X")                  # the Rocket; the five on the bridge
    g.put(*P(22, 15), "X")                    # Camper Shane
    g.put(*P(30, 39), "!")
    return g.rows()


def route_25():
    """Route 25, tile for tile after Pokemon Journeys' map (Map058, its x 0-62, rows 5-18; Jordan, 11-07:
    exact): in from Route 24 along the sand path under the ledge; the round shrubs and the tall grass, the
    flowers, the long hedge; Bill's Sea Cottage in its fenced yard at the cape, between the pines, its sand
    paths and flower patches, the mailbox; the sea beyond the fence. (Journeys has no trainers here: ours
    stand about the shrubs.)"""
    g = Grid(63, 14, "c")
    P = lambda x, y: (x - 0, y - 5)           # (the original's tiles)
    def rect(x, y, w, h, ch):
        g.rect(*P(x, y), w, h, ch)
    def put(x, y, ch):
        g.put(*P(x, y), ch)
    rect(0, 6, 62, 9, "."); rect(0, 15, 40, 1, "."); rect(40, 15, 21, 2, ".")
    rect(1, 7, 8, 2, G)                       # the tall grass
    rect(0, 10, 10, 1, "#"); rect(0, 11, 13, 3, "=")   # the ledge over the sand path
    for x, y in ((15, 6), (19, 6), (25, 6), (31, 6), (15, 7), (19, 7), (25, 7), (31, 7), (25, 8), (26, 8), (27, 8),
                 (29, 8), (16, 9), (18, 9), (20, 9), (25, 9), (29, 9), (34, 9), (10, 10), (11, 10), (14, 10),
                 (15, 10), (20, 10), (22, 10), (23, 10), (25, 10), (34, 10), (16, 11), (20, 11), (25, 11), (31, 11),
                 (32, 11), (13, 12), (16, 12), (17, 12), (20, 12), (31, 12), (13, 13), (20, 13), (22, 13), (31, 13)):
        put(x, y, "T")                        # the round shrubs
    for x, y in ((35, 6), (37, 6), (39, 6), (41, 6), (37, 9), (39, 9), (36, 10), (38, 10), (33, 13), (35, 13),
                 (37, 13)):
        put(x, y, "f")
    rect(0, 14, 40, 1, "T")                   # the hedge
    # Bill's Sea Cottage and its yard
    rect(42, 6, 1, 3, "k"); rect(42, 8, 7, 1, "k"); rect(54, 8, 8, 1, "k"); rect(61, 8, 1, 10, "k")
    rect(40, 14, 3, 1, "k"); rect(41, 17, 21, 1, "k")
    rect(43, 6, 6, 2, "T"); rect(54, 6, 8, 2, "T")
    g.building(*P(49, 5), 5, 4, "B", door_x=2)
    put(48, 8, "!")                           # the mailbox
    rect(50, 9, 3, 1, "="); rect(47, 10, 9, 2, "="); rect(49, 13, 5, 2, "=")
    rect(43, 13, 6, 3, "f"); rect(54, 13, 6, 3, "f")
    rect(40, 18, 23, 1, "~"); rect(62, 6, 1, 12, "~")
    rect(0, 11, 1, 3, "<")
    for x, y in ((17, 7), (24, 7), (12, 8), (33, 8), (28, 10), (36, 11), (22, 12), (39, 12), (30, 13)):
        put(x, y, "X")
    return g.rows()


def bills_house():
    """Bill's Sea Cottage inside, tile for tile after assets/backgrounds/kanto/bills_city.png (15 x 10, 16 px
    tiles; Jordan, 11-07: walkable): the back wall with its two machines and the poster; the Cell Separator's
    two pods joined by the green pipe; the boxes, monitors and cabinets round the walls; Bill by his computer
    desk; the potted plants in the front corners; the mat out (south) to Route 25."""
    g = Grid(15, 11, "c")
    g.rect(0, 2, 15, 8, ".")
    g.rect(5, 2, 4, 1, "c").put(13, 2, "c")      # (behind the boxes: the wall)
    g.put(0, 2, "m").put(1, 1, "m").put(1, 2, "m").put(12, 1, "m").put(12, 2, "m")   # a box; the two machines
    g.rect(2, 1, 3, 3, "m").rect(9, 1, 3, 3, "m").rect(5, 1, 4, 1, "m")   # the pods and their pipe
    g.put(0, 3, "m").put(1, 3, "m").rect(5, 3, 4, 1, "m").put(13, 3, "m")   # monitors and boxes
    g.rect(14, 2, 1, 6, "m").put(0, 7, "m").rect(0, 8, 1, 2, "m")           # the cabinets down the sides
    g.rect(4, 5, 2, 2, "m")                      # the computer desk
    g.put(3, 6, "N")                             # Bill
    g.put(1, 9, "z").put(2, 9, "z").put(12, 9, "z").put(13, 9, "z")   # the plants
    g.put(7, 10, "v")                            # out to Route 25
    return g.rows()


def route_5():
    """Route 5, tile for tile after Pokemon Journeys' map (Map038, its x 12-35, rows 0-39; Jordan, 11-08:
    exact): south from Cerulean down three lanes between the fences: the sand paths either side, the middle
    one stepping down its ledges past the tall grass to the Day Care; the Underground Path's little house
    (bottom right); the sand path to the gatehouse to Saffron, in at its top (a thirsty guard turns you back
    till you bring him a drink: Celadon's Tea)."""
    g = Grid(24, 40, "T")
    P = lambda x, y: (x - 12, y)              # (the original's tiles)
    def rect(x, y, w, h, ch):
        g.rect(*P(x, y), w, h, ch)
    def put(x, y, ch):
        g.put(*P(x, y), ch)
    rect(14, 0, 20, 34, ".")
    rect(15, 0, 4, 27, "="); rect(29, 0, 4, 27, "=")          # the sand paths
    rect(14, 0, 1, 34, "k"); rect(33, 0, 1, 28, "k"); rect(19, 0, 1, 27, "k"); rect(28, 0, 1, 27, "k")
    for y in (4, 9, 14, 19):
        rect(20, y, 8, 1, "#")                # the middle lane's ledges
    rect(19, 27, 10, 1, "#")
    for y in (4, 9, 14, 19, 27):
        put(20, y, ".")                       # (a gap at each ledge's west end: they were hops down)
    for y in (5, 10, 15):
        rect(20, y, 8, 2, G)
    g.building(*P(21, 21), 5, 5, "Y", door_x=2)   # the Day Care
    g.building(*P(30, 28), 4, 4, "U", door_x=1)   # the Underground Path
    put(32, 32, "!")
    rect(23, 29, 4, 3, "=")                   # the path to the gate
    rect(14, 34, 8, 1, "k"); rect(28, 34, 6, 1, "k"); rect(14, 35, 8, 5, "T"); rect(28, 35, 6, 5, "T")
    rect(22, 33, 6, 7, "G"); rect(24, 32, 2, 1, "v")   # the gatehouse to Saffron (in at its top)
    put(26, 31, "N")                          # the guard
    rect(15, 0, 18, 1, "^"); rect(19, 0, 1, 1, "k"); rect(28, 0, 1, 1, "k")
    return g.rows()


def underground_path():
    """The Underground Path, tile for tile after Pokemon Journeys' (Map369; Jordan, 11-08: exact): its two
    tunnels, side by side here as in the original they don't meet ("parts"): north-south (left: its x 4-11,
    rows 18-80), stairs up to Route 5 at the top and Route 6 at the bottom; east-west (right: its x 80-159,
    rows 45-51), stairs up to Route 7 (west) and Route 8 (east, open once you've been to Lavender)."""
    g = Grid(90, 63, "c")
    g.rect(1, 2, 6, 60, ".")                  # north-south
    g.rect(5, 2, 2, 2, "^").rect(1, 59, 2, 2, "v")
    g.put(4, 30, "N")                         # the Fossil Maniac
    g.put(1, 5, "!")
    g.rect(10, 29, 78, 4, ".")                # east-west
    g.rect(10, 29, 2, 3, "<").rect(86, 29, 2, 3, ">")
    g.put(13, 32, "!")
    return g.rows()


ROUTE_6_ROWS = [  # (from Pokemon Journeys' map, x 14-37, rows 0-40: colour shares, then by hand)
    'TTTTTTTTTTGGGGGGTTTTTTTT',
    'TTTTTTTTTTGGGGGGTTTTTTTT',
    'TTTTTTTTTTGGGGGGTTTTTTTT',
    'TTTTTTTTTTGGGGGGTTTTTTTT',
    'TTkkkkkkkkGGGGGGkkkkkkTT',
    'TT........kk^^kk......TT',
    'TT.......k.N===.k.....TT',
    'TT###.####.====.###.##TT',
    'TT.........====.......TT',
    'TT.....X..............TT',
    'TT................UUUUTT',
    'TT#######.########UUUUTT',
    'TT================UUUUTT',
    'TT================UDUUTT',
    'TT=!==================TT',
    'TT""""===""""""=======TT',
    'TT""""==="""""""""""""TT',
    'TT""""==="""""""""""""TT',
    'TT""""==="""""""""""""TT',
    'TT""""==============""TT',
    'TT""""==============""TT',
    'TT""""==============""TT',
    'TT"""""""""""""""===""TT',
    'TT~~~~~~~~~~~~~""===""TT',
    'TT~~~~~~~~~~~~~""=X=""TT',
    'TT~~~~~~~~~~~~~""===""TT',
    'TT~~~~~~~~~~~~~""===""TT',
    'TT........==========""TT',
    'TT..X.....==========""TT',
    'TT........==========""TT',
    'TTkkkkk...===""""kkkkkTT',
    'TTTTTTk...===""""kTTTTTT',
    'TTTTTTk...===""""kTTTTTT',
    'TTTTTTk...===""""kTTTTTT',
    'TTTTTTkkkk===kkkkkTTTTTT',
    'TTTTTTTTTk===kTTTTTTTTTT',
    'TTTTTTTTTk===kTTTTTTTTTT',
    'TTTTTTTTTk===kTTTTTTTTTT',
    'TTTTTTTTTk===kTTTTTTTTTT',
    'TTTTTTTTTk===kTTTTTTTTTT',
    'TTTTTTTTTkvvvkTTTTTTTTTT',
]

def route_6():
    """Route 6, tile for tile after Pokemon Journeys' map (Map039, its x 14-37, rows 0-40; Jordan, 11-08:
    exact): south out of the gatehouse below Saffron (the thirsty guard again), the ledges (their own gaps),
    the sand path winding down between the tall grass and past the pond; the Underground Path's little house
    (top right); between the fences and down the sand lane to Vermilion. (Journeys has no trainers here.)"""
    return list(ROUTE_6_ROWS)


def vermilion_city():
    """Vermilion City, tile for tile after assets/backgrounds/kanto/vermillion_city.png (65 x 51: its tiles x 1-65,
    rows 1-51 at 16 px, grid phase 2,2; Jordan, 11-08: exact): down the steps from Route 6 into the brick plaza:
    the Pokemon Center between two houses, a house right of the stone avenue; the stone road along the water
    channel, the round plaza and its sign; the Fan Club and a house; the Mart, the lawn and the fenced
    construction lot with its rocks and Machop (in by a gap on its west side); the Gym and its posted yard (a
    gap at its top left: the original's way in isn't drawn), the Fishing Guru's house; east along the posted
    road to Route 11 (the lawn below it, down its steps to the water, is reached by Surf); the piers with their lamps, sand and
    boats, out to the harbour at the end (in from the pier, on its north side); the sea
    rocks round the bay."""
    g = Grid(67, 53, "o")
    def rect(x, y, w, h, ch):
        g.rect(x, y, w, h, ch)
    def put(x, y, ch):
        g.put(x, y, ch)
    # the north edge: trees, the hedge and its fence, the sand path and its steps down
    rect(0, 0, 25, 4, "T"); rect(10, 3, 15, 1, "k"); rect(28, 0, 39, 4, "T"); rect(34, 4, 33, 3, "T"); rect(48, 7, 19, 7, "T")
    rect(25, 0, 3, 4, "="); rect(25, 1, 3, 1, "^")
    rect(0, 4, 25, 1, "c"); rect(28, 4, 6, 1, "c"); rect(25, 4, 3, 1, "=")
    # the brick plaza, the stone avenue and road
    rect(10, 5, 24, 9, "p"); rect(10, 5, 1, 9, "a")
    rect(25, 5, 3, 22, "a"); rect(11, 10, 22, 3, "a"); rect(23, 10, 7, 6, "a")
    rect(24, 5, 1, 4, "k"); rect(28, 5, 1, 4, "k")
    g.building(11, 5, 4, 4, "A", door_x=1)
    g.building(15, 5, 5, 5, "C", door_x=2)
    g.building(20, 5, 4, 4, "B", door_x=1)
    g.building(29, 5, 4, 4, "E", door_x=1)
    put(24, 12, "!")
    rect(10, 14, 12, 3, "o")                 # the water channel
    rect(29, 13, 5, 4, "."); rect(22, 13, 1, 4, "p")
    # the lawn and the construction lot
    rect(34, 7, 14, 12, "."); rect(48, 7, 2, 12, "T")
    rect(35, 8, 13, 11, "k"); rect(36, 9, 11, 9, "."); put(35, 13, ".")
    for x, y in ((45, 9), (46, 9), (43, 10), (44, 10), (46, 10), (39, 12), (45, 12), (41, 13), (45, 13), (46, 13),
                 (36, 16), (37, 16), (44, 16), (45, 16), (39, 17), (40, 17), (42, 17), (43, 17), (45, 17), (46, 17), (44, 17)):
        put(x, y, "r")
    put(40, 14, "N")                         # Machop
    rect(34, 19, 17, 1, "#"); rect(51, 19, 3, 1, "=")
    rect(34, 20, 17, 2, "p"); put(44, 21, "!")
    # the middle blocks: the Fan Club, a house, the Mart
    rect(10, 17, 13, 5, "p"); rect(23, 17, 2, 5, "p"); rect(28, 17, 6, 5, "p"); rect(28, 13, 1, 4, "a")
    g.building(12, 17, 4, 4, "F", door_x=1); put(16, 20, "!")
    g.building(20, 17, 4, 4, "I", door_x=1)
    g.building(29, 17, 5, 4, "M", door_x=2)
    rect(10, 22, 44, 2, "a")                 # the long stone road
    # the Gym and its yard; the Fishing Guru's house
    rect(10, 24, 1, 4, "a"); rect(11, 24, 15, 4, "p"); rect(19, 24, 3, 4, "a")
    g.building(12, 24, 7, 5, "V", door_x=3)
    rect(10, 28, 2, 4, "k"); rect(20, 28, 2, 4, "k"); rect(11, 29, 9, 2, "."); rect(10, 31, 12, 1, "k")
    put(19, 28, "!"); put(11, 28, "."); rect(14, 31, 3, 1, "s"); rect(10, 32, 12, 1, "c")
    rect(26, 24, 8, 8, "p"); rect(26, 27, 6, 4, "a"); rect(33, 24, 1, 8, "k"); rect(26, 31, 7, 1, "c")
    g.building(29, 24, 4, 4, "W", door_x=1)
    rect(22, 28, 4, 4, "o")
    # the east road to Route 11, and the lawn below it
    rect(48, 14, 2, 5, "T"); rect(50, 14, 1, 5, "k"); rect(51, 14, 11, 1, "k")
    rect(51, 15, 12, 2, "a"); rect(51, 17, 3, 2, "a"); rect(54, 17, 8, 1, "k"); rect(51, 20, 3, 2, "a")
    rect(62, 13, 5, 5, "."); rect(65, 14, 1, 3, ">")
    rect(54, 18, 13, 5, "T"); rect(54, 23, 7, 4, "T"); rect(61, 23, 6, 4, ".")
    put(62, 24, "f"); put(64, 25, "f")
    rect(54, 27, 13, 14, "T"); rect(62, 27, 2, 1, "="); rect(62, 28, 2, 6, "."); rect(55, 33, 8, 2, "."); rect(54, 28, 1, 13, ".")
    rect(55, 41, 9, 1, "."); rect(64, 41, 3, 12, "T")
    # the piers
    rect(44, 24, 3, 15, "e"); rect(44, 27, 3, 2, "=")
    rect(27, 36, 20, 4, "e"); rect(35, 33, 7, 3, "s"); rect(28, 40, 3, 4, "e")
    rect(32, 40, 7, 3, "s"); rect(32, 43, 7, 1, "e")
    for x, y in ((10, 13), (24, 17), (28, 17), (10, 23), (41, 21), (47, 30), (47, 34), (47, 39), (34, 36), (40, 36),
                 (28, 36), (31, 42)):
        put(x, y, "l")
    rect(47, 28, 1, 12, "o"); put(47, 30, "l"); put(47, 34, "l"); put(47, 39, "l")
    # the harbour (walk round its west side to its door)
    g.rect(27, 44, 7, 8, "P").put(29, 44, "D")   # (its way in faces the pier; the picture's door is its south exit)
    # boats and sea rocks
    for x, y in ((21, 37), (21, 40), (21, 43), (37, 27), (37, 30)):
        rect(x, y, 4, 2, "q")
    for x, y in ((9, 9), (9, 10), (9, 12), (7, 12), (7, 14), (7, 15), (7, 17), (5, 17), (5, 18), (5, 20), (6, 21),
                 (6, 23), (6, 25), (7, 26), (6, 28), (7, 29), (7, 31), (5, 32), (7, 32), (5, 34), (6, 35), (6, 37),
                 (6, 38), (7, 40), (7, 41), (6, 43), (6, 44), (8, 44), (10, 45), (12, 45), (12, 47), (14, 47),
                 (16, 47), (18, 47), (20, 46), (22, 46), (24, 46), (35, 46), (37, 46), (39, 47), (41, 47), (43, 47),
                 (45, 46), (47, 46), (49, 46), (51, 46), (53, 46), (54, 45), (54, 43), (55, 41)):
        put(x, y, "q")
    return [r[1:66] for r in g.rows()[1:52]]


def ss_anne(floor):
    """The S.S. Anne, after Pokemon Journeys' ship (Map345's cabin decks, Map349's top deck; Jordan, 11-08: six
    cabins, one way through, the captain on the top deck). 1F (its x 68-103, rows 115-131): up the stairs from
    the gangway (bottom left) into the long hall, six cabin doors along its north wall (each: a trainer), the
    stairs up at the end of its east arm. 2F (its x 70-103, rows 42-65): in at the end of its east arm, along
    the hall with your rival, up the short passage north to the deck. The top deck (Map349, 24 x 15): the bow,
    its chairs, tables and barrels, the deckhouse with the captain's door on its west side."""
    if floor == 0:
        g = Grid(36, 17, "c")
        P = lambda x, y: (x - 68, y - 115)
        def rect(x, y, w, h, ch):
            g.rect(*P(x, y), w, h, ch)
        rect(70, 116, 4, 14, "."); rect(98, 116, 4, 14, "."); rect(97, 122, 1, 2, "."); rect(70, 126, 32, 4, ".")
        for k, d in enumerate((75, 79, 83, 87, 91, 95)):   # the cabins
            g.building(*P(d - 1, 124), 3, 2, "ABCEFG"[k])
        rect(100, 117, 2, 1, "+")             # up to 2F
        rect(70, 127, 2, 1, "v")              # down the gangway to Vermilion
        g.put(*P(78, 127), "!")
        return g.rows()
    if floor == 1:
        g = Grid(34, 24, "c")
        P = lambda x, y: (x - 70, y - 42)
        def rect(x, y, w, h, ch):
            g.rect(*P(x, y), w, h, ch)
        rect(71, 52, 31, 3, "."); rect(71, 55, 4, 10, "."); rect(97, 55, 5, 10, "."); rect(89, 45, 3, 7, ".")
        rect(97, 63, 2, 1, "-")               # down to 1F
        g.put(*P(90, 45), "+")                # up to the deck
        g.put(*P(92, 53), "X")                # your rival
        return g.rows()
    g = Grid(24, 15, "~")
    for y, x0, x1 in ((5, 9, 15), (6, 7, 15), (7, 5, 15), (8, 3, 15), (9, 1, 15), (10, 3, 15), (11, 5, 15), (12, 7, 15),
                      (13, 9, 15)):
        g.rect(x0, y, x1 - x0 + 1, 1, ".")
    g.rect(16, 13, 8, 1, "c")
    g.rect(16, 10, 8, 3, "L")                 # the deckhouse
    g.building(16, 5, 8, 5, "K", door_x=0)    # (the captain's door: its west side)
    g.rect(9, 6, 1, 2, "y").rect(9, 11, 1, 2, "y").put(8, 7, "m").put(12, 7, "m").put(10, 12, "m")   # chairs, tables
    for x, y in ((14, 5), (15, 5), (15, 6), (15, 12), (14, 13), (15, 13)):
        g.put(x, y, "m")                      # barrels
    g.put(11, 5, "-")                         # down to 2F
    return g.rows()


ROUTE_11_ROWS = [  # (from Pokemon Journeys' map, x 0-71, rows 9-29: colour shares, then by hand)
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTT...==================""""===============""".....TTTTTTTTTTTT',
    'TTTTQQQQQQTT...=====X============""""===============""".....TTTTTTTTTTTT',
    'TTTTQQQQQQTT...==================""""===============""".....TTTTTTTTTTTT',
    'TTTTQQQQQQTT...===""""""""""""===""""==="""""""""==="""...r.TTTTTTTTTTTT',
    'TTTTQQQQQQTT...===""""""""""""===""""===""""""""""""""".....TTTTTTTTTTTT',
    'kkk!QQDQQQTT...===""""===========""""==========="""""""kkkGGGGGGGTTTTTTT',
    '<.........========""""===========""""==========="""""""...GGGGGGG......>',
    '<.........========""""===========""""===X=======""""====.=GGGGGGG======>',
    '<.........==============="""""===""""==="""""===""""====.=GDGGGGG======>',
    '..~~~~~~~~~~~..=========="""""=========="""""===""""====.==============>',
    '~~~~~~~~~~~~~..=========="""""=========="""""===""""===.kkkkkkkkkkkkkkkk',
    'qq~~~~~~~~~~~.."""""""""""""""=========="""""===""""===.............TTTT',
    '~~TTTTTTTTTTkk.""""""""""""""""""""""===========""""===.....TTTTTTTTTTTT',
    '~~TTTTTTTTTT...""""""""""""""""""""""===========""""===.....TTTTTTTTTTTT',
    '~~TTTTTTTTTTTT.====""""""""""""""""""===========""""X==.....TTTTTTTTTTTT',
    '~~TTTTTTTTTTTT.========================="""""==========.....TTTTTTTTTTTT',
    '~~TTTTTTTTTTTT.========================="""""==========.....TTTTTTTTTTTT',
    '~~TTTTTTTTTTTT.========================="""""==========.....TTTTTTTTTTTT',
    '~~TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    '~~TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
]

def route_11():
    """Route 11, tile for tile after Pokemon Journeys' map (Map044, its x 0-71, rows 9-29; Jordan, 11-08:
    exact): east from Vermilion past Diglett's Cave's mound and its sign, the pond; the sand paths winding
    through the tall grass; the gatehouse to Route 12 at the east end (in by its west door, or round it on the
    sand). (Journeys has no trainers here.)"""
    return list(ROUTE_11_ROWS)


DIGLETTS_CAVE_ROWS = [  # (from Pokemon Journeys' Diglett's Cave, Map329: its x 52-134, rows 22-93; the tunnel's
    # brown floor by its colour)
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'c.<cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'c..cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'c..cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'c..cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'c.....ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'c......cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'c.......ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'c.......ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'ccccc......cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccc......ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccc......ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccc....ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccc...ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccc..ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccc..ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccc..........ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccc............ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccc............ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccc..c.c............cccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccc............ccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccc...........ccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccc.c.......ccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccc.........ccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccc..........ccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccc.........cccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccc.......ccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccc.......cccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccc.....cccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccc....cccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccc....cccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccc....cccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccc....cccccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccc......cccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccc......cccccccccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccc..........cccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccc............ccccccccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccccc...........ccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccc..........ccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccc...........c.cccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccc..........ccccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccc..........cccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccc..........cccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccc........cccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccc.c......ccccccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccc.....ccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccc.......cccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccc......cccccccccccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccc..............cccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccc..............cccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccc.c............ccccccccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc............cccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc.cc.......ccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc......ccccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc......cccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc......cccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc......cccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc......cccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc.....cccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc.....cccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc.....cccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc....cccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc....cccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc....cccccccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc......cccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc.......cccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc........ccccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc........cccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc.......cccc',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc......>c',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc......c',
    'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
]

def digletts_cave():
    """Diglett's Cave, tile for tile after Pokemon Journeys' (Map329, its x 52-134, rows 22-93; Jordan, 11-08:
    exact): the one long tunnel winding down from the ladder up to Route 2 (top left) to the ladder up to
    Route 11 (bottom right)."""
    return list(DIGLETTS_CAVE_ROWS)


ROUTE_9_ROWS = [  # (from Pokemon Journeys' map, x 0-71, rows 3-24: colour shares, then by hand)
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'TTTTTTk"""""""""""............cccccc""""""cccccc...........======ccccccc',
    'TTTTTTk"""""""""""............cccccc""""""cccccc...........======ccccccc',
    'TTTTTTk"""X"""""""ccccc.......cccccc......cccccc..........ccccc==ccccccc',
    'TTTTTTk"""""""""""ccccc#####..cccccc##..##cccccc##..######ccccc==ccccccc',
    'TTTTTTk"""""""""""ccccc=======cccccc======cccccc==========ccccc==ccccccc',
    '<.................ccccc=======cccccc======================ccccc==ccccccc',
    'kkkkkkk#########..ccccc======!ccccccccccc=================ccccc==ccccccc',
    '<......========cccccccc=============ccccc====ccccc===cccccccccc==ccccccc',
    '<......========cccccccc=============ccccc====ccccc===ccccc=============>',
    'kkkkkcccccc====cccccccc###########==ccccc====ccccc===ccccc=============>',
    'TTTTTcccccc.###cccccccc===========..ccccc####ccccc##.ccccc===ccccc===ccc',
    'TTTTTcccccc====cccccccc===========..ccccc....ccccc...ccccc.##ccccc.##ccc',
    'TTTTTcccccc===================X==....................ccccc===ccccc===ccc',
    'TTTTTcccccc===============cccccc=....................ccccc...ccccc===ccc',
    'TTTTTcccccc#########==####cccccc##..#################ccccc###ccccc###ccc',
    'TTTTTcccccc===============cccccc.......................X.............ccc',
    'TTTTTcccccc===============cccccc.....................................ccc',
    'TTcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'TTcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
]

def route_9():
    """Route 9, tile for tile after Pokemon Journeys' map (Map042, its x 0-71, rows 3-24; Jordan, 11-08:
    exact): east from Cerulean between the fences, the tall grass, the rock; the sand paths among the rock
    pillars and their ledges (their own gaps), the sign; east to Route 10. (Journeys has no trainers here.)"""
    return list(ROUTE_9_ROWS)


ROUTE_10_ROWS = [  # (from Pokemon Journeys' map, x 0-22, rows 5-55)
    'ccccccccccccccccccccccc',
    'ccooooooooooooooooooooc',
    'ccooooooooooooooooooooc',
    'ccooooooooooooooooooooc',
    'cc.................oooc',
    'cckk..kkkkkkkkkkkkkoooc',
    'cc....""""""""""".koooc',
    'cc....""""""""""".koooc',
    'cc....""X"""""""".koooc',
    '<.....""""""""""".koooc',
    '<.....""""""""""".koooc',
    'cc................koooc',
    'cc#############..kkoooc',
    'cc...X............koooc',
    'cc................koooc',
    'ccccccccccc.......koooc',
    'ccccccccccc.......koooc',
    'cccccccccccCCCCC..koooc',
    'cccccccQQQcCCCCC..koooc',
    'cccccccQDQcCCCCC..koooc',
    'cc.......TTCCDCC..koooc',
    'cc..kkk!kTT=====..koooc',
    'cc........T=====..koooc',
    'cc........T=====..koooc',
    'cc........T.......koooc',
    'cc........T.......koooc',
    'cc........T...X...koooc',
    'cc........T.......koooc',
    'cc................koooc',
    'cc................koooc',
    'cckkkkkkkkkkkkkkkkkoooc',
    'ccccccccccccccccc..oooc',
    'ccccccccccccccccc..oooc',
    'ccccccccccccccccc..oooc',
    'ccccccccccccccccc..oooc',
    'cccPPPPPPPPPccccc..oooc',
    'c.mPPPPPPPPPmcccc..oooc',
    'c.mPPPPPPPPPmcccc..oooc',
    'c.mPPPPPPPPPmcccc..oooc',
    'c.mPPPPPPPPPmcccc..oooc',
    'c..PPPPPPPPPmcccc..oooc',
    'c.#PPPPDPPPP.ccc...oooc',
    'c............ccc...oooc',
    'cc....!......ccc...oooc',
    'cc.................oooc',
    'cc.................oooc',
    'cc................~oooc',
    'ccooooooooooooooooooooc',
    'ccooooooooooooooooooooc',
    'ccooooooooooooooooooooc',
    'ccccccccccccccccccccccc',
]

def route_10():
    """Route 10's north half, tile for tile after Pokemon Journeys' map (Map043, its x 0-22, rows 5-55;
    Jordan, 11-08: exact): in from Route 9 (west); the tall grass in its fence, the ledge; Rock Tunnel's mouth
    in the cliff beside the Pokemon Center, the sign, the little trees; the river round it all (Surf it down to
    the Power Plant, in its own walled yard, and its sign)."""
    return list(ROUTE_10_ROWS)


ROUTE_10_SOUTH_ROWS = [  # (from Pokemon Journeys' map, x 0-22, rows 58-84)
    'ccccccccccccccccccccccc',
    'ccccccccccccccccccccccc',
    'ccccccccccccccccccccccc',
    'cccccccQQQccccccc=....c',
    'cccccccQDQccccccc=....c',
    'ccc===============....c',
    'ccc============!==....c',
    'ccc==============.....c',
    'ccc=========ccccc.....c',
    'cc==========ccccc#.###c',
    'cc===cccccccccccc.....c',
    'cc===cccccccccccc.....c',
    'cc###cccccccccccc.....c',
    'cc===cccccccccccc####.c',
    'cc===cccccccccccc.....c',
    'cc=..""...............c',
    'cc."""""".............c',
    'cc."""""".............c',
    'ccccccccccc...........c',
    'ccccccccccc...........c',
    'ccccccccccc.....LLLLL.c',
    'ccccccccccc...ccLLLLLcc',
    'ccccccccccc...ccLLLLLcc',
    'ccccccccccc...ccLLLLLcc',
    'ccccccccccc...ccLLLLLcc',
    'ccccccccccc..cccLLLLLcc',
    'cccccccccccvvcccLLLLLcc',
]

def route_10_south():
    """Route 10's south half, tile for tile after Pokemon Journeys' map (its x 0-22, rows 58-84): out of
    Rock Tunnel's south mouth, its sign, down the sand paths and ledges (their own gaps) past the tall grass
    to Lavender Town (its tower ahead)."""
    return list(ROUTE_10_SOUTH_ROWS)


ROCK_TUNNEL_FLOORS = [  # (from Pokemon Journeys' Rock Tunnel, Map338: 1F its x 0-47, B1F its x 62-109, rows 0-39;
    # by colour: its floor, its rock walls, the boulders. The ladders pair as its warps say: "ladders" below)
    [  # 1F
        'cccccccccccccccccccccccccccccccccccccccccccccccc',
        'ccc...rrccccccccc^ccccccccccccccccccccccccrr..cc',
        'ccc.+..rcccccccc.....ccccccccccccccccccccc...+cc',
        'ccc.....cccccccc..!..ccccccccccccccccccccc....cc',
        'ccc.....cccccccc.......................ccc....cc',
        'ccc.....cccccccc.......................ccc....cc',
        'c...........rccc.......................ccc....cc',
        'c...........rccc.......................ccc....cc',
        'c...........rccc.......................ccc....cc',
        'c...........rccccccccccc....cccccccccccccc....cc',
        'c.....ccc...rccccccccccc....cccccccccccccc....cc',
        'c.....ccc....ccccccccccc....cccccccccccccc....cc',
        'c.....ccc....cccrr...ccc......................cc',
        'c.....cccr...ccc....+ccc......................cc',
        'c....rccc....ccc.....cccrr...................rcc',
        'c.....cccr...ccc.....cccrr.r..............rrrrcc',
        'c....rccc............ccccccccccccccccccccccccccc',
        'c.....ccc............ccccccccccccccccccccccccccc',
        'c.....ccc............ccccccccccccccccccccccccccc',
        'c....rccc................cccrr...r..cccrr...rrcc',
        'c.....ccc................cccr.......cccr......cc',
        'c........................ccc........ccc......+cc',
        'c........................ccc........ccc.......cc',
        'c.......................rccc........ccc.......cc',
        'c..................rrrrrrccc........ccc.......cc',
        'cccccccccccccccccccccccccccc........ccc.......cc',
        'cccccccccccccccccccccccccccc........ccc.......cc',
        'cccccccccccccccccccccccccccc........ccc......rcc',
        'c...................................ccc.......cc',
        'c...................................ccc.......cc',
        'c...................................ccc.......cc',
        'c...................................ccc.....r.cc',
        'cccccccccccc...........cccccccc............rrrcc',
        'cccccccccccc...........cccccccc............rr.cc',
        'cccccccccccc.......r...ccccccccrr.............cc',
        'cccccccccccc...........ccccccccrrrr...........cc',
        'cccccccccccc.r...!..r..ccccccccccccccccccccccccc',
        'cccccccccccc...r.....r.ccccccccccccccccccccccccc',
        'ccccccccccccrrccccvcccrccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccccccc',
    ],
    [  # B1F
        'cccccccccccccccccccccccccccccccccccccccccccccccc',
        'crr..ccc....cccr.....rr.r..rcccrrr.......r.rrrcc',
        'c.c..ccc....cccrr.....r....rcccr.c..........rrcc',
        'c.-..ccc....cccr............ccc..-...........rcc',
        'c....ccc....ccc.............ccc..............rcc',
        'c....ccc....ccc.............ccc........r.....rcc',
        'c....cccr...ccc.....ccc.....ccc.....cccccc....cc',
        'c....ccc...rccc.....ccc.....ccc....rcccccc....cc',
        'c....ccc...rccc.....ccccccccccc....rccccccr...cc',
        'c....ccc....ccc.....ccccccccccc....rccccccr...cc',
        'c....ccc...rccc.....ccccccccccc.....ccccccr...cc',
        'c...........ccc............cccc.......rrrr....cc',
        'c...........ccc............-cccr..............cc',
        'c...........ccc.............cccrr.............cc',
        'c...........ccc.............cccrr.............cc',
        'c...........ccc.............cccrrrrr..........cc',
        'c....ccc............cccccccccccccccccc........cc',
        'c....ccc............cccccccccccccccccc........cc',
        'c....ccc............cccccccccccccccccc.......rcc',
        'c....ccc............ccc.......................cc',
        'c....ccc....ccc.....ccc.....................rrcc',
        'c....ccc....ccc.....ccc...................r.rrcc',
        'c....cccr...ccc.....ccc.......cccccccccccccccccc',
        'cr...cccrr..ccc.....ccc.......cccccccccccccccccc',
        'crrrrccc....ccc.....ccc.......cccccccccccccccccc',
        'cccccccc....ccccccccccc.......cccrr.....r.rrrrcc',
        'cccccccc....ccccccccccc.......cccr...r......rrcc',
        'cccccccc....ccccccccccc.......ccc.....c.....rrcc',
        'c...........cccrr.............ccc.....-......rcc',
        'c...........cccrr.............ccc............rcc',
        'c...........ccc...............ccc.............cc',
        'c.........rrccc...............ccc.............cc',
        'ccccccccccccccc....rccccccccccccc............rcc',
        'ccccccccccccccc...rrccccccccccccc.............cc',
        'ccccccccccccccc...rrccccccccccccc.............cc',
        'c......rr.r.........r....rrrr..rr...........r.cc',
        'c.............................................cc',
        'c.............................................cc',
        'c..............................rr.............cc',
        'cccccccccccccccccccccccccccccccccccccccccccccccc',
    ],
]

def rock_tunnel(part):
    """Rock Tunnel, tile for tile after Pokemon Journeys' (Map338; Jordan, 11-08: exact; dark till Flash lights
    it): 1F, in from Route 10's north half by the ladder up top, out to its south half at the bottom, its four
    holes down; B1F, its four ladders back up, each to the hole it pairs with in the original (A to its 2nd,
    B to its 4th, C to its 3rd, D to its 1st, in reading order). The rock walls, the boulders, the signs."""
    return list(ROCK_TUNNEL_FLOORS[part])


def lavender_town():
    """Lavender Town, after assets/backgrounds/kanto/lavender_city.png (its tiles x 15-43, rows 0-31; grid phase
    1,7) with FireRed / LeafGreen's (Downloads/Lavender_Town_FRLG.png; Jordan, 11-08: both tall towers, one in each
    north corner): down from Route 10 across the lawn (a gap in its ledge) onto the stone streets; the tall Pokemon
    Tower north-west, the tall Radio Tower north-east (open once the Power Plant's generator is fixed), the Pokemon
    Center between them under the cliff; a house and its mailbox, a house, Mr. Fuji's (the purple and gold one);
    the Mart in the flower garden; the long planter of flowers; west to Route 8, south to Route 12."""
    g = Grid(44, 32, "c")
    g.rect(19, 0, 23, 2, ".").rect(28, 2, 5, 6, ".").rect(28, 7, 5, 1, "#").put(28, 7, ".")
    g.rect(28, 0, 4, 1, "^")
    g.rect(27, 8, 6, 8, "a").rect(16, 15, 12, 2, "a").rect(15, 16, 28, 5, "a").rect(16, 21, 17, 9, "a")
    g.rect(15, 17, 1, 4, "<")
    g.building(16, 1, 7, 14, "P", door_x=3)   # the Pokemon Tower
    g.building(23, 11, 5, 5, "C", door_x=2)
    g.put(28, 15, "!").put(21, 16, "!")
    g.building(32, 1, 7, 14, "R", door_x=3)
    g.rect(33, 15, 7, 1, "a").put(36, 16, "!")
    g.building(24, 18, 4, 4, "A", door_x=1).put(23, 21, "!")
    g.building(19, 23, 4, 4, "B", door_x=1)
    g.building(23, 23, 5, 4, "F", door_x=2)
    g.rect(33, 21, 10, 9, ".")
    g.building(35, 20, 5, 5, "M", door_x=2)
    g.rect(32, 22, 3, 1, "k").rect(41, 22, 2, 1, "k").rect(42, 22, 1, 4, "k")
    g.rect(33, 22, 2, 3, "f").rect(40, 22, 2, 3, "f").put(32, 24, "!")
    g.rect(32, 28, 11, 3, "f")
    g.rect(28, 30, 5, 2, ".").rect(28, 31, 5, 1, "v")
    return [r[15:44] for r in g.rows()]


ROUTE_8_ROWS = [  # (from Pokemon Journeys' map, x 0-71, rows 5-24: colour shares, then by hand)
    'TTTTcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'TTTTccccccccUUUUcccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
    'TTTTccccccccUUUUf========k..............................TTTTTTTTTTTTcccc',
    'TTTTccccccccUUUU.========k..............................TTTTTTTTTTTTcccc',
    'TTTTccccccccUDUUf========k..=========================...TTTTTTTTTTTTcccc',
    'TTTTcccc.f.f.======.#####k..=========================...TTTTTTTTTTTTcccc',
    'TTTTccccf....======k=====k..============X============...TTTTTTf.f.f.cccc',
    'TGGGGGGkkk...======k=====k..===...................===...TTTTTT.f.f.fcccc',
    'TGGGGGG...!..======k=====k..===...kkkkkkkkkkkkk...===...TTTTTT......cccc',
    'TGGGGGG=========...k.####k..===..kkf""."".""..kk..===...TTTTTT...======>',
    'TGGGGGG=N=======...k=====k..===..kf..""""".""f.k..==X...TTTTTT...======>',
    'TGGGGGD=========...k=====...===..k.f""."."".".fk..===...TTTTTT...======>',
    'kkkkkkkk.....===...k=====...===..k..""""""""""....===...TTTTTT...===kkkk',
    'TTTTcccccccc.===...kkkkkkk..===..kf".".".".""".k..===...TTTTTT...===cccc',
    'TTTTcccccccc.===............===..k."""""""".".fk..===............===cccc',
    'TTTTcccccccc.===............===....."."."".".".k..===............===cccc',
    'TTTTcccccccc.=========X========..k.".""".""""".k..==================cccc',
    'TTTTcccccccc.==================..kf.f.".""f.".fk..==================cccc',
    'TTTTcccccccc.==================..k.f.f.".f.f.f.k..==================cccc',
    'TTTTcccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
]

def route_8():
    """Route 8, tile for tile after Pokemon Journeys' map (Map041, its x 0-71, rows 5-24; Jordan, 11-08:
    exact): west from Lavender along the sand paths, past the trees and flowers, the tall grass in its fence
    (gaps where the original has them), the ledges between the fences; the Underground Path's little house
    (on to Route 7 under Saffron), and the gatehouse to Saffron with its thirsty guard. (Journeys has no
    trainers here.)"""
    return list(ROUTE_8_ROWS)


ROUTE_7_ROWS = [  # (from Pokemon Journeys' map, x 0-23, rows 14-30: colour shares, then by hand)
    'TTTTTTTTTTTTTTTTTTTTTTTT',
    '<.........#""""""""kTTTT',
    '<.........#""""""""kTTTT',
    '<....X....#""""""""kTTTT',
    '<.........#""""""f.kTTTT',
    'TTTT......#"""""".fkTTTT',
    'TTTT......#fXf.GGGGGGGTT',
    'TTTT##..###.f..GGGGGGGTT',
    'TTTT...........GGGGGGGTT',
    'TTTT..........NGGGGGGGTT',
    'TTTT...........DGGGGGGTT',
    'TTTT..UUUU.........kkkkk',
    'TTTT##UUUU.........kTTTT',
    'TTTT..UUUU......X..kTTTT',
    'TTTT.!UDUU.........kTTTT',
    'TTTT...............kTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTT',
]

def route_7():
    """Route 7, tile for tile after Pokemon Journeys' map (Map040, its x 0-23, rows 14-30; Jordan, 11-08:
    exact): east from Celadon, the tall grass behind its ledge and fence, the flowers; the Underground Path's
    little house and its sign (on to Route 8 under Saffron); the gatehouse to Saffron with its thirsty guard.
    (Journeys has no trainers here.)"""
    return list(ROUTE_7_ROWS)


def celadon_city():
    """Celadon City, tile for tile after assets/backgrounds/kanto/celadon_city.png (64 x 45, 16 px tiles, grid
    phase 0,4; Jordan, 11-08: exact): the row along the top: houses, the Dept. Store, the Mansion, the
    Condominiums, the Pokemon Center; the pale stone streets; the park with its fountain; the flower shop, the
    Game Corner and its signs; the pond and its bridge; the Gym and its neighbours on their brick terrace (reached from behind:
    down the gap south of the Hotel's road, where the Cut tree is in the games, along the lawn behind the trees and
    up through the ledges); the Hotel's row of houses; west to Route 16, east up the steps to Route 7."""
    g = Grid(64, 46, "T")
    def rect(x, y, w, h, ch):
        g.rect(x, y, w, h, ch)
    def put(x, y, ch):
        g.put(x, y, ch)
    # the lawns behind and round it
    rect(11, 5, 39, 1, "."); rect(32, 6, 1, 3, "."); rect(40, 6, 2, 3, "."); rect(11, 9, 38, 1, ".")
    rect(11, 9, 1, 19, "."); rect(48, 9, 1, 6, "."); rect(51, 5, 2, 8, "."); rect(49, 13, 13, 2, ".")
    # the row along the top, on its brick terrace
    rect(12, 10, 36, 5, "p")
    g.building(12, 10, 3, 4, "H", door_x=1)
    g.building(15, 8, 6, 6, "S", door_x=3)
    g.building(22, 10, 3, 4, "I", door_x=1)
    g.building(25, 8, 5, 6, "Y", door_x=2)
    g.building(30, 8, 5, 6, "J", door_x=3)
    g.building(36, 10, 3, 4, "K", door_x=1)
    g.building(40, 10, 3, 4, "L", door_x=1)
    g.building(43, 10, 5, 4, "C", door_x=2)
    put(35, 13, "!"); put(19, 14, "!")
    # the streets
    rect(12, 15, 47, 3, "e"); rect(12, 18, 12, 12, "e"); rect(3, 28, 9, 2, "e"); rect(12, 27, 14, 3, "e")
    rect(30, 26, 4, 8, "e"); rect(31, 25, 18, 2, "e"); rect(33, 32, 16, 2, "e")
    rect(0, 26, 3, 4, "."); rect(3, 26, 8, 2, "."); rect(0, 27, 1, 3, "<")
    # the east way out
    rect(59, 15, 3, 3, "."); rect(61, 16, 2, 2, "="); rect(63, 16, 1, 2, ">"); rect(62, 15, 1, 3, ".")
    # the park
    rect(14, 19, 9, 8, "."); put(20, 19, "!"); rect(17, 21, 3, 2, "~")
    put(14, 22, "l"); put(21, 22, "l"); put(20, 22, "f")
    # the flower shop, the Game Corner, the fences
    rect(24, 18, 7, 9, "."); rect(25, 18, 1, 9, "k"); rect(30, 18, 1, 9, "k"); put(25, 24, ".")   # (a gate: its way in)
    g.building(26, 18, 4, 5, "B", door_x=1)
    rect(31, 18, 18, 7, ".")
    g.building(30, 18, 7, 5, "Q", door_x=3)
    g.building(37, 19, 4, 4, "P", door_x=1)
    g.building(42, 18, 3, 5, "U", door_x=1)
    g.building(46, 18, 3, 5, "V", door_x=1)
    rect(31, 24, 9, 1, "k"); rect(42, 24, 7, 1, "k"); put(34, 24, "!"); put(43, 24, "!")
    # the pond and its bridge
    rect(26, 25, 4, 9, "~"); rect(26, 27, 4, 3, "e"); rect(25, 30, 1, 4, "k"); rect(30, 30, 1, 4, "k")
    # the Gym's terrace
    rect(12, 30, 13, 7, "p"); rect(12, 37, 41, 1, "."); rect(51, 24, 2, 13, "."); rect(41, 34, 1, 3, ".")
    g.building(12, 30, 3, 5, "M", door_x=1)
    g.building(15, 30, 6, 4, "Z", door_x=3)
    g.building(21, 30, 4, 4, "O", door_x=2)
    put(20, 35, "!")
    rect(12, 36, 7, 1, "#"); rect(21, 36, 4, 1, "#")
    # the Hotel's row
    rect(35, 26, 14, 6, ".")
    rect(33, 27, 2, 5, ".")
    g.building(35, 26, 3, 5, "A", door_x=1)
    g.building(38, 26, 4, 5, "R", door_x=1)
    g.building(42, 26, 3, 5, "W", door_x=1)
    g.building(46, 26, 3, 5, "E", door_x=1)
    # the corridors east of town
    rect(49, 13, 3, 1, ".")
    for x, y in ((50, 14), (50, 31), (50, 33)):  # (lamps)
        put(x, y, "l")
    return [r for r in g.rows()[:45]]


ROUTE_12_ROWS = [  # (from Pokemon Journeys' map, x 0-26, rows 0-115: colour shares, then by hand)
    'ccccccccccc^^cccccccccccccc',
    'cccccccq~~~==~~~~qq~~~~~~~~',
    'ccccccc~~~~==~~~~qq~~~~~~~~',
    'ccccccc~~~~==~~~qq~~~~~~~~~',
    'ccccccc~~~~==~~~qq~~~~~~~~~',
    'ccccccc~~~~==~~~~qqqq~~~~~~',
    'ccccccc=========~qqqqqq~~~~',
    'ccccccc=========~~~~~qq~~~~',
    'ccccccc==~~~~===~~~~~qq~~~~',
    'ccccccc==~~~~====!==~qq~~~~',
    'ccccccc==~~~~=======~qq~~~~',
    'ccccccc==~~~~===~~~~~qq~~~~',
    'ccccccc==~~~GG=JJ~~~~qq~~~~',
    'ccccccc==~qqGG=JJqq~~qq~~~~',
    'ccccccc~~~qqGG=JJqq~qq~~~~~',
    'cccccccqqqq~GG=JJ~qqqq~~~~~',
    'cccccccqqqq~GG=JJ~qqqq~~~~~',
    'cccccccq~~~~GG=JJ~~~qq~~~~~',
    'ccccccccc~~~~===~~~~~qq~~~~',
    'ccccccccc~~~~===~~~~~qq~~~~',
    'ccccccccc~~~~=X=~~~~~qq~~~~',
    'ccccccccc~~~~===~~~~~qq~~~~',
    'ccccccccc===========~~qq~~~',
    'ccccccccc===========~~qq~~~',
    'ccccccccc~~~~~~~~~==~qq~~~~',
    'ccccccccq~~~~~~~~~==~qq~~~~',
    'cccccccc~~~~~~~~~~==~qq~~~~',
    'cccccccc==~~~=======~qq~~~~',
    'cccccccc==~~~=======~qq~~~~',
    'cccccccc==~~~==~~~~~~qq~~~~',
    'cccccccc==~~~==~~~~~~~qq~~~',
    'cccccccc==~~~==~~~TT~~qq~~~',
    'cccccccc=======~~~TT~~qq~~~',
    'cccccccc=======~~~TT~~qq~~~',
    'cccccccc==~~~~~~~~TT~qq~~~~',
    'cccccccc==~~~~~~~~TT~qq~~~~',
    'cccccccc==~~~~~~~~~~~~qq~~~',
    'cccccccc==~~~~~~~~~~~~qq~~~',
    'TTTTTTTT=============~qq~~~',
    'TTTTTTTT=============~qq~~~',
    'TTTTTTTT==~~==~~~~~~~~qq~~~',
    'TTTTTTTT==~~==~~~~~~~~qq~~~',
    'TTTTTTTT==~~==~~~~~~~qq~~~~',
    'TTTTTTTT~~~~======~~~qq~~~~',
    'TTTTTTTT~~~~======~~~qq~~~~',
    'TTTTTTTT~~~~~~~~====~qq~~~~',
    'TTTTTTTT~~~~~~~~==X=~qq~~~~',
    'TTTTTTTT~~~~~~~~==~~~qq~~~~',
    'TTTTTTTT~~~~~~~~==~~qq~~~~~',
    'TTTTTTTT======~~==~~qq~~~~~',
    'TTTTTTTT======~~==~~~qq~~~~',
    'TTTTTTTT==~~==~~....~qq~~~~',
    'TTTTTTTT==~~==~~."".~~qq~~~',
    'TTTTTTTT==~~==~~."".~~qq~~~',
    'TTTTTTTT==~~====."".~~qq~~~',
    'TTTTTTTT==~~====....~~qq~~~',
    'TTTTTTTT==~~~~~~~~~~~qq~~~~',
    'TTTTTTTT==~~~~~~~~~~~qq~~~~',
    'TTTTTTTT==~~~~~~~~~~~qq~~~~',
    'TTTTTTTT============~qq~~~~',
    'TTTTTTTT============~qq~~~~',
    'TTTTTTTT~~~~~~==~~~~~qq~~~~',
    'TTTTTTTT~~~~~~==~~~~~~qq~~~',
    'TTTTTTTT~~~~~~==~~~~~~qq~~~',
    'kkkkkkkkq~~~~~==~~~~qq~~~~~',
    '<......kkkkkkk=!~~~~qq~~~~~',
    '<"""""".......==~~~qq~~~~~~',
    '<......kkkkkkk==~~~qq~~~~~~',
    'kkkkkkkTq~~~~~==~~~qq~~~~~~',
    'TTTTTTTT~~~~~~==~~~qq~~~~~~',
    'TTTTTTTT~~~~~~==~~~~qq~~~~~',
    'TTTTTTTT~~~~~~=X~~~~qq~~~~~',
    'TTTTTTTT~~~~~~==~~~~~qq~~~~',
    'TTTTTTTT~~~~~~==~~~~~qq~~~~',
    'TTTTTTTT~~~~~~==~~~~~~qq~~~',
    'TTTTTTTT~~~~~~======~~qq~~~',
    'TTTTTTTT~~~~~~======~~qq~~~',
    'TTTTTTTT~~~~~~~~~~==~~qq~~~',
    'TTTTTTTT~~~~~~~~~~==~qq~~~~',
    'TTTTTTTT~~~~~~~~~~==~qq~~~~',
    'TTTTTTTT=="HHHHH....~qq~~~~',
    'TTTTTTTT=="HHHHHf.f.~qq~~~~',
    'TTTTTTTT=="HHHDH.f..~~qq~~~',
    'TTTTTTTT==..........~~qq~~~',
    'TTTTTTTT==..........~~qq~~~',
    'TTTTTTTT==~~~~~~~~~~~~qq~~~',
    'TTTTTTTT==~~~~~~~~~~~qq~~~~',
    'TTTTTTTT==~~~~~~~~~~~qq~~~~',
    'TTTTTTTT==========~~qq~~~~~',
    'TTTTTTTT==========~~qq~~~~~',
    'TTTTTTTT~~~~~~==~~~~qq~~~~~',
    'TTTTTTTT~~~~~~==~~~~qq~~~~~',
    'TTTTTTTT~~~~~~==~~~qq~~~~~~',
    'TTTTTTTTq~~~~~==~~~qq~~~~~~',
    'TTTTTTTTTTTT~~==~~~~qq~~~~~',
    'TTTTTTTT"""T~~==~~~~qq~~~~~',
    'TTTTTTTT""".====~~~~qq~~~~~',
    'TTTTTTTT""T.====~~~~qq~~~~~',
    'TTTTTTTTTT..~~======~~qq~~~',
    'TTTTTTTT....~~======~~qq~~~',
    'TTTTTTTT========~~~~~~qq~~~',
    'TTTTTTTT========~~~~~~qq~~~',
    'TTTTTTTT~~~~~~======~~qq~~~',
    'TTTTTTTT~~~~~~======~~qq~~~',
    'TTTTTTTT~~~~~~~~~~==~~qq~~~',
    'TTTTTTTTq~~~~~~~~~==~~qq~~~',
    'TTTTTTTTkkkkkk======~~qq~~~',
    'TTTTTTTT......======~~qq~~~',
    'TTTTTTTT....kk~~==~~~~qq~~~',
    'TTTTTTTT""""TT~~==~~~~qq~~~',
    'TTTTTTTT""""TT~~==~~~qq~~~~',
    'TTTTTTTT""""TT~~==~~~qq~~~~',
    'TTTTTTTT""""TT====~~~qq~~~~',
    'TTTTTTTT""""TT====~~~qq~~~~',
    'TTTTTTTT""""TT==~~~~qq~~~~~',
    'TTTTTTTTTTTTTTvv~~~~qq~~~~~',
]

def route_12():
    """Route 12, tile for tile after Pokemon Journeys' map (Map045, its x 0-26, rows 0-115; Jordan, 11-08:
    exact): the long wooden piers south from Lavender over the water, through the gatehouse; the sea rocks; the
    lane west to Route 11; the house on its island; south to Route 13 (Snorlax in the way). (Journeys has no
    trainers here.)"""
    return list(ROUTE_12_ROWS)


ROUTE_13_ROWS = [  # (from Pokemon Journeys' map, x 0-75, rows 5-19: colour shares, then by hand)
    '<...f.f.f.f.......ddd............fk.............."""""""""""TT^^~~~qq~~~~~~~',
    'kkkkkkkkkkkkkkkk..ddd.kkkkkkkkk.f.k..!kkkkkk....."""""""""""TT==~~~qq~~~~~~~',
    '<...........X.d.......k.....................TTTT."""""""""""TT==~~~qq~~~~~~~',
    'kkkkkkkkkkkkkdddkkkkkkk..kkkkkkkkkkkkkkkkk..TTTT."""""""""""TT==~~~~qq~~~~~~',
    '<f..f.........d.k.f...........X.....k.......TTTTTTTTTTTTTTTTTT==~~~~qq~~~~~~',
    'kkkkkk..kkkkkkkkkf.kkkkkkkkkkkkkk...k..kkk..TTTTTTTTTTTTTTTTTT==~~~~qq~~~~~~',
    '<.......k..................d..k.........X.....==================~~~~qq~~~~~~',
    'kkkkkkkkk..kkkkkkkkkkkkkkkddd.k..kkkkkkkkkkk..==================~~~qq~~~~~~~',
    'k.....................k....dd.................~~~~~~~~~~~~~~~~~~~~~qq~~~~~~~',
    'k.kkkkkk..kkkkkkkkkkk!k.kkkkkkkkkkkkkkkkkkkkkk~~~~~~~~~~~~~~~~~~~~~qq~~~~~~~',
    'TTTTTTTTTTTTTTTTTTTTTTTTq~~~~~~~~~~~~~~~~~qq~~~~~~~~~~~~~~~~~~qq~~~qq~~~~~~~',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~qq~~~~~~qqqq~~~~~~qqqqqqqq~~~~~~~~',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~qqqqqqqqqqqq~~qqqq~~qqqq~~~~~~~~',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~qqqqqq~~~~qqqqqq~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~qq~~~~~~~~~~~~~~~~~~',
]

def route_13():
    """Route 13, tile for tile after Pokemon Journeys' map (Map046, its x 0-75, rows 5-19; Jordan, 11-08:
    exact): off the end of Route 12's pier (north-east) and west through the maze of fences, its signs, the
    tall grass and pines, the long hedge, the sea rocks. (Journeys has no trainers here.)"""
    return list(ROUTE_13_ROWS)


ROUTE_14_ROWS = [  # (from Pokemon Journeys' map, x 0-23, rows 4-57: colour shares, then by hand)
    'TTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTk....f.f.f.......>',
    'TTTTTT...kkkkkkkkkkkkkkk',
    'TTTTTT..X..............>',
    'TTTTTT.kkkkkkkkkkk..kkkk',
    'TTTTTT.................>',
    'TTTTTT.kk..kkkkkkkkkkkkk',
    'TTTTTT.................>',
    'TTTTTT.kkkkkkk...!kkkkkk',
    'TTTTTT..f.f...===......>',
    'TTTTTT.f.f....===kkkkkkk',
    'TTTTTT..f.....===.TTTTTT',
    'TTTTTT........===.TTTTTT',
    'TTTTTT.TTTTTT.===.TTTTTT',
    'TTTTTT.TTTTTT.===.TTTTTT',
    'TTTTTT."""""TT===.TTTTTT',
    'TTTTTT."""""TT=X=.TTTTTT',
    'TTTTTT."""""TT===.TTTTTT',
    'TTTTTT."""""TT===.TTTTTT',
    'TTTTTT."""""TT===..~~~~~',
    'TTTTTT."""""TT===.~~~~~~',
    'TTTTTT......TT===.~~~~~~',
    'TTTTTT..####TT===.~~~~~~',
    'TTTTTT...===TT===.~~~~~~',
    'TTTTTT...===TT===.~~~~~~',
    'TTTTTT...===TT===..~~~~~',
    'TTTTTT...===TT===.....~~',
    'TTTTTT...===TT===kkkkk~~',
    'TTTTTT...===TT===.....~~',
    'TTTTTT...===TT===.....~~',
    'TTTTTT...===TT===.....~~',
    'TTTTTT...=X=..===.....~~',
    'TTTTTT...===TT===.....~~',
    'TTTTTT...===TT===.....~~',
    'TTTTTT...===TT===.....~~',
    'TTTTTT...===TT===.....~~',
    'TTTTTT...===TT===..f..~~',
    'TTTTTT...===TT===.f...~~',
    'TTTTTT...===TT===..f..~~',
    'TTTTTT...===TT===.f...~~',
    'TTTTTTk..===TT===..f..~~',
    'TT==========TT===.f...~~',
    'TT==========..===..f..~~',
    '..==========..===.....~~',
    '.#............===.....~~',
    '##..f.f.f.f...===.....~~',
    '.....f.f.f....===.....~~',
    '..............===.....~~',
    '<================.....~~',
    '<================.....~~',
    '<================.....~~',
    'kkkkkkkkkkkkkkkkkkkkkk~~',
    'TTTTTTTTTTTTTTTTTTTTTT~~',
    'TTTTTTTTTTTTTTTTTTTTTT~~',
]

def route_14():
    """Route 14, tile for tile after Pokemon Journeys' map (Map047, its x 0-23, rows 4-57; Jordan, 11-08:
    exact): in from Route 13 (east) through the fences, the flowers, the tall grass behind its trees, the
    long sand paths south and its ledge; the water east; west to Route 15. (Journeys has no trainers here.)"""
    return list(ROUTE_14_ROWS)


ROUTE_15_ROWS = [  # (from Pokemon Journeys' map, x 0-71, rows 14-26: colour shares, then by hand)
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTk====================================================>',
    'TTTTTTTTTTTTTTTTTT.===========X=============================X==========>',
    'TTTTTT.............====================================================>',
    'TTTTTTkkkkkkYYYYYYk.....................................................',
    'TTTTTT......YYYYYY.###########.#########################################',
    '<===========YYYYYY====""""""f.f.f."""""".........f.f.""""f.f."""""""f.f.',
    '<====================="""""".f.f.f""""""...!......f.f"""".f.f""""""".f.f',
    '<===========VVVVVV=====================================================>',
    'kkkkkkkkkkkkkkkkkkk==========================X=========================>',
    'TTTTTTTTTTTTTTTTTTT====================================================>',
    'TTTTTTTTTTTTTTTTTTkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkkk',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
]

def route_15():
    """Route 15, tile for tile after Pokemon Journeys' map (Map048, its x 0-71, rows 14-26; Jordan, 11-08:
    exact): west from Route 14 along the sand paths either side of the flowers and tall grass (a gap in the
    long ledge), through the gatehouse, on to Fuchsia City. (Journeys has no trainers here.)"""
    return list(ROUTE_15_ROWS)


ROUTE_16_ROWS = [  # (from Pokemon Journeys' map, x 0-71, rows 13-29: colour shares, then by hand)
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTFFFFFTTTTTTTGGGGGGTTTTTTTTTTTTTTTTTT',
    'TTTTTT"""""""""""""""TTTTTTTTTkkkkkkFFFFFkkkkkkkGGGGGGkkkkkkkkkkkkkkkTTT',
    'TTTTTT===============TTTTTTTTT======FFFDF=======GGGGGG======"""""""""TTT',
    'TTTTTT======X========TTTTTTTTT==================GGGGGG======"""""""""TTT',
    'TTTTTT===============TTTTTTTTT==================GGGGGG======"""""""""TTT',
    '........f.....................==============....GGGGGG.f.============TTT',
    '................f...........f..................f======..f=====X======TTT',
    'cccccccccccccccccccccccccccc.kkkkkkkkkkkkkkk.kkkHHHHHHkkk============TTT',
    'cccccccccccccccccccccccccccck...................HHHHHH..kkkk!kkkkkkk.TTT',
    'cccccccccccccccccccccccccccck.===""""===========HHHHHH===TTT.f....f....>',
    '~~~~~~~~~~~~~~~~~~~~~~~~~ccck.===""""===========HHHHHH===..............>',
    '~~~~~~~~~~~~~~~~~~~~~~~~~ccck.==="X""===========HHHHHH===TTT.f....f....>',
    '~~~~~~~~~~~~~~~~~~~~~~~~~ccck.===""""=====kkkkkkkkkkkkkkkkkkkkkkkkkkkkkk',
    '~~~~~~~~~~~~~~~~~~~~~~~~~ccck.===""""=====kTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    '~~~~~~~~~~~~~~~~~~~~~~~~~ccck.===!========kTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    '~~~~~~~~~~~~~~~~~~~~~~~~~ccck.============kTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    '~~~~~~~~~~~~~~~~~~~~~~~~~ccck.vvvvvvvvvvvvkTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
]

def route_16():
    """Route 16, tile for tile after Pokemon Journeys' map (Map049, its x 0-71, rows 13-29; Jordan, 11-08:
    exact): west from Celadon past the flowers and tall grass, through the big gatehouse; the sand paths, the
    bamboo, the quiet house where you're given Fly; the cliff and the water; south to the top of Cycling Road
    (a gap in the fence). (Journeys has no trainers here.)"""
    return list(ROUTE_16_ROWS)


ROUTE_17_ROWS = [  # (from Pokemon Journeys' map, 34 x 160: colour shares, then by hand)
    '~~~ccc..^^^....^^^...TTTTTTTTTTTTc',
    '~~~ccc..===....===...TTTTTTTTTTTTc',
    '~~~ccc..===....===....cccccccccccc',
    '~~~ccc..===....===....cccccccccccc',
    '~~~ccc..===....===....cccccccccccc',
    '~~~ccc..aaa....aaa....cccccccccq~~',
    '~~~cccaaaaaaaaaaaaa...ccccccccc~~~',
    '~~~cccaaaaaaaaaaaaa...ccccccccc~~~',
    '~~~cccaaaaaaaaaaaaa.........ccc~~~',
    '~~~cccaaaaaaaaaaaaa.kkkkkkkkccc~~~',
    '~~~cccaaaaaaaaaaaaa.........ccc~~~',
    '~~~ccaaaaaaaaaaaaaaaccccccccccc~~~',
    '~~~ccaaaaaaaaaaaaaaaccccccccccc~~~',
    '~~~ccaaaaaaaaaaaaaaaccccccccccc~~~',
    '~~~~~aaaaaaaaaaaaaaa~~~~~~~~~~~~~~',
    '~~~~~aaaaaa~a~~aaaaa~~~~~~~~~~~~~~',
    '~~~~~aaaaaa~~~~aaaaa~~~~~~~~~~~~~~',
    '~~~~~aaaaaa~~~~aaaaa~~~~~~~~~~~~~~',
    '~~~~~~aaaaa~~~~aaaa~~~~~~~~~~~~~~~',
    '~~~~~~aaaaa~~~~aaaa~~~~~~~~~~~~~~~',
    '~~~~~~aaaaa~~~~aaaa~~~~~~~~~~~~~~~',
    '~~~~~~aaaaa~~~~aaaa~~~~~~~~~~~~~~~',
    '~~~~~~aaaaa~~~~aaaaaaaaaaaaa~~~~~~',
    '~~~~~aaaaaaa~~~aaaaaaaaaaaaa~~~~~~',
    '~~~~~aaaaaaa~~~aaaaaaaaaaaaa~~~~~~',
    '~~~~~aaaaaaa~~~aaaaaaaaaaaaaa~~~~~',
    '~~~~~~aaaaa~~~~aaaaaaaaaaaaaa~~~~~',
    '~~~~~~aaaaa~~~~aaaaaaaaaaaaaa~~~~~',
    '~~~~~~aaaaa~~~~aaa~~a~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaXaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaX~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~~aaaaaa~~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~~aaaaaa~~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaa~~aaaaa~~aaaXaaaa~~~~~',
    '~~~~~aaaaaaa~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaa~~~~aaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaaaaaaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaaaaaaaa~~aaaaaaaa~~~~~',
    '~~~~~~aaaaaaaaaaaaa~~aaaaaaaa~~~~~',
    '~~~~~~aaaaaaaaaaaaa~~aaaaaaaa~~~~~',
    '~~~~~~aaaaaaaaaaaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaaaaaaa~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~a~~~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~~aaaaaaa~~~~~~~~~aaaaaa~~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~~~aaaaaaaaa~~~~~~~aaaaaaaa~~~~~',
    '~~~cccaaaaaaacccccccccaaaaaaccc~~~',
    '~~~cccccaaacccccccccccccaaccccc~~~',
    '~~~ccck......."""."""......kccc~~~',
    '~~~ccc.......""""#""""......ccc~~~',
    '~~~ccc.......q~~~~~~~q......ccc~~~',
    '~~~ccc.......~~~~~~~~~......ccc~~~',
    '~~~ccc.......~~~~~~~~~......ccc~~~',
    '~~~ccc.......~~~~~~~~~......ccc~~~',
    '~~~ccc.......~~~~~~~~~......ccc~~~',
    '~~~ccc.......~~~~~~~~~......ccc~~~',
    '~~~ccc.......q~~~~~~~q......ccc~~~',
    '~~~ccc........""""""".......ccc~~~',
    '~~~ccc........""""""".......ccc~~~',
    '~~~ccc........""""""".......ccc~~~',
    '~~~ccc........""""""".......ccc~~~',
    '~~~ccckkkkkkk...kkk...kkkkkkccc~~~',
    '~~~ccccccccc.===...===.cccccccc~~~',
    '~~~ccccccccc.===.".===.cccccccc~~~',
    '~~~ccccccccc.===.".===.cccccccc~~~',
    '~~~~~~~~qccck===.".===kccc~~~~~~~~',
    '~~~~~~~~qcccc===ccc===cccc~~~~~~~~',
    '~~~~~~~~qcc..===.".===..cc~~~~~~~~',
    '~~~~~~~~qcccc===ccc===cccc~~~~~~~~',
    '~~~~~~~~qcccc===ccc===ccccqq~~~~~~',
    '~~~~~~~qq~~~k===.".===k~~~qq~~~~~~',
    '~~~~~~~qq~~~.===.".===.~~~qq~~~~~~',
    '~~~~~~qq~~~~.===.".===.~~~qq~~~~~~',
    '~~~~~~qq~~~~.===.".===.~~qq~~~~~~~',
    '~~~~~~qq~~~~.===.".===.~~qq~~~~~~~',
    '~~~~~~qq~~~~.===.".===.~~~qq~~~~~~',
    '~~~~~~~qq~~~.===.".===.~qqqq~~~~~~',
    '~~~~~~~qq~~~.===.".===.~qq~~~~~~~~',
    '~~~~~~~qq~~~.===.".===.~~qq~~~~~~~',
    '~~~~~~~qq~~~.===.".===.~~qq~~~~~~~',
    '~~~~~~~~qq~~.===...===.~~qq~~~~~~~',
    '~~~~~~~~qq~~.===!..===.~~qq~~~~~~~',
    '~~~~~~~~~qq~.####.####.~qq~~~~~~~~',
    '~~~~~~~~~qq~vvvvvvvvvvv~qq~~~~~~~~',
]

def route_17():
    """Route 17, Cycling Road, tile for tile after Pokemon Journeys' map (Map050, 34 x 160; Jordan, 11-08:
    exact): the long raised roads south over the water from Route 16, the lawns, the pond and tall grass at the
    foot, the last ledges and lanes down to Route 18. (Journeys has no trainers here.)"""
    return list(ROUTE_17_ROWS)


ROUTE_18_ROWS = [  # (from Pokemon Journeys' map, x 0-58, rows 0-18: colour shares, then by hand)
    '~~~~~~~~~qqk^^^^^^^^^kqq~~~~~~~~~~~~kTTTTTTTTTTTTTTTTTTTTTT',
    '~~~~~~~~~qqk.f.....f.kqqqq~~~~~~~~~~kTTTTTTTTTTTTTTTTTTTTTT',
    '~~~~~~~qq~~kf.......fk~~qq~~~~~~~~~~kTTTTTTTTTTTTTTTTTTTTTT',
    '~~~~~~~qq~~k.f.....f.k~~~~qqqq~~qqqqkTTTTTTTTTTTTTTTTTTTTTT',
    '~~~~~~qq~~~kf.......fk~~~~qqqqqqqqqqkTTTTTTTTTTTTTTTTTTTTTT',
    '~~~~~~qq~~~k.f.....f.k~~~~~~~~qq~~~~kTTTTTTTTTTTTTTTTTTTTTT',
    '~~~~~qq~~~~kf.......fkq~~~~~~~~~~~~qkTTTTTTTTTGGGGGGTTTTTkT',
    '~~~~~qq~~~~k.=======................kkkkkkkkk.GGGGGG...!.kk',
    '~~~~~~qq~~~k===X==============================GGGGGG======>',
    '~~~~~~qq~~~k=======================X======================>',
    '~~~~~~qq~~~k==================================HHHHHH======>',
    '~~~~~~qq~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~q##########..kkkkk',
    '~~~~~~qq~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~qq~#...........TTTTT',
    '~~~~~~qq~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~qq~#.""""""....TTTTT',
    '~~~~~~~~qq~~~~~qqqq~~~~~~~~~~~~~~~~~~~~~~~#."""""".#TTTTTTT',
    '~~~~~~~~qqqq~~~qqqq~~~~~~~~~qqqq~~qqqq~~qq#."""X"".#TTTTTTT',
    '~~~~~~~~~~qqqqqq~~~~~~qqqqqqqqqqqqqqqqqqqq#."""""".#TTTTTTT',
    '~~~~~~~~~~~~qqqqqqqqqqqqqqqq~~~~qq~~~~qq~~#........#TTTTTTT',
    '~~~~~~~~~~~~~~~~qqqqqq~~~~~~~~~~~~~~~~~qq~##########q~~~~qT',
]

def route_18():
    """Route 18, tile for tile after Pokemon Journeys' map (Map051, its x 0-58, rows 0-18; Jordan, 11-08:
    exact): off the foot of Cycling Road between the flowers, east along the sand path by the sea, the sea
    rocks, through the gatehouse to Fuchsia City; the fenced tall grass below. (Journeys has no trainers here.)"""
    return list(ROUTE_18_ROWS)


def fuchsia_city():
    """Fuchsia City, tile for tile after assets/backgrounds/kanto/fuchsia_city.png (60 x 41, 16 px tiles, grid
    phase 5,10; Jordan, 11-08: exact): the Safari Zone's entrance at the top; the road down from it; the five
    hedged gardens (each with a gate), the ponds, the Mart; the fence and lamps along the roads; the long road
    west to Route 18 and east through the gatehouse to Route 15; the Fishing Guru's brother's two houses in
    their fenced yard, his pond; the Gym, the Warden's house, a house and the Pokemon Center under the cliff, and
    the way south to Route 19."""
    g = Grid(60, 41, "T")
    def rect(x, y, w, h, ch):
        g.rect(x, y, w, h, ch)
    def put(x, y, ch):
        g.put(x, y, ch)
    rect(10, 7, 41, 13, "."); rect(19, 19, 8, 4, ".")
    g.building(28, 0, 6, 7, "Z", door_x=2)    # the Safari Zone
    put(28, 8, "!")
    # the roads
    rect(29, 8, 3, 18, "a"); rect(17, 15, 12, 2, "a"); rect(11, 17, 7, 1, "a")
    rect(1, 24, 31, 2, "a"); rect(0, 24, 1, 2, "<"); rect(31, 21, 25, 2, "a")
    # the gardens
    rect(11, 8, 1, 5, "T"); rect(18, 8, 1, 5, "T"); rect(12, 8, 6, 1, "T"); rect(12, 9, 6, 1, "k"); rect(12, 10, 6, 3, "~")
    for x0, x1, y0 in ((20, 26, 8), (34, 39, 8), (42, 48, 8), (38, 44, 13)):
        rect(x0, y0, 1, 5 if y0 == 8 else 4, "T"); rect(x1, y0, 1, 5 if y0 == 8 else 4, "T"); rect(x0 + 1, y0, x1 - x0 - 1, 1, "T")
        ybot = y0 + (4 if y0 == 8 else 3)
        rect(x0 + 1, y0 + 1, x1 - x0 - 1, ybot - y0 - 1, "f")
        rect(x0 + 1, ybot, x1 - x0 - 1, 1, "k"); put((x0 + x1) // 2, ybot, ".")
    g.building(11, 13, 5, 4, "M", door_x=2)
    rect(19, 17, 8, 2, "T")
    # the second pond, the fence, the little trees
    rect(8, 18, 3, 4, "T"); rect(11, 19, 7, 1, "T"); rect(11, 20, 7, 1, "k"); rect(11, 21, 7, 2, "~"); rect(18, 19, 1, 4, "T")
    put(21, 20, "T"); rect(27, 18, 1, 6, "k"); rect(1, 23, 26, 1, "k"); put(23, 23, "!"); put(26, 23, ".")   # (the Cut tree: a gap)
    rect(33, 20, 23, 1, "k"); rect(32, 16, 19, 4, "."); rect(33, 17, 18, 2, "T")
    # east through the gatehouse
    rect(56, 18, 4, 3, "Y"); rect(56, 21, 4, 2, "="); rect(59, 21, 1, 2, ">"); rect(56, 23, 4, 1, "V")
    # the brother's yard, the pond, the south-east road
    rect(32, 23, 22, 13, "."); rect(30, 26, 2, 1, "."); rect(32, 24, 16, 1, "k"); rect(32, 24, 1, 7, "k"); rect(48, 24, 1, 4, "k"); put(32, 26, ".")   # (a gate into the yard)
    rect(32, 30, 4, 1, "k"); rect(44, 30, 4, 1, "k"); rect(38, 25, 9, 3, "~")
    g.building(36, 27, 5, 5, "B", door_x=1)
    g.building(41, 27, 4, 5, "P", door_x=1)
    put(35, 31, "!")
    rect(50, 26, 2, 8, "a"); rect(35, 33, 17, 2, "a")
    rect(32, 35, 4, 1, "k"); rect(39, 35, 9, 1, "k")
    # the Gym's row
    rect(4, 26, 26, 14, "."); rect(5, 27, 24, 5, "c")
    g.building(7, 30, 7, 5, "G", door_x=3)
    g.building(14, 31, 4, 4, "W", door_x=1)
    g.building(18, 31, 4, 4, "H", door_x=1)
    g.building(22, 30, 5, 5, "C", door_x=2)
    rect(7, 35, 20, 2, "a"); rect(10, 37, 3, 1, "a"); rect(17, 37, 5, 2, "a"); put(8, 35, "!")
    rect(5, 32, 1, 7, "#"); rect(5, 38, 3, 1, "#"); rect(23, 37, 6, 1, "#"); rect(28, 32, 1, 5, "#")
    rect(13, 37, 3, 2, "T"); rect(22, 39, 4, 2, "T"); rect(18, 39, 3, 1, "="); rect(18, 40, 3, 1, "v")
    rect(4, 40, 12, 1, "c"); rect(16, 39, 2, 2, "T"); rect(21, 39, 1, 2, "T")
    for x, y in ((10, 7), (26, 13), (33, 13), (50, 7), (27, 19), (32, 20), (38, 20), (44, 20), (50, 20), (4, 23), (3, 38), (28, 38)):
        put(x, y, "l")
    return g.rows()


SAFARI_ZONE_ROWS = [  # (from Pokemon Journeys' map, 165 x 90: colour shares, then by hand)
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT............................"""""......TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT..""..""...................""""""AAAAA.TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.""""""""................""""""".AAAAA.TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT."""""""".TTTTTTTTTTTTTTT""""""..ADAAA.TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT..""""""..TTT.======TTT..""""""....!===TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT..""""""..TTT.======TTT==.""""".....===TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT."""""""q~~q...===========""""""..=====TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT."""""""~~~~"""....========"""""".=====TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"..""~~~~""".TTT========.""""""=====TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT=====~~~~""""TTTTTTTTTTTTTTT"""====.TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT=====~~~~""""TTT=====......c=======cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.======.q~~q""".T=========....c=======cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT====q~~q..""""""T=========....c=======cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT====~~~~""""""".T=========....cc==cc==cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT====~~~~""""""..T=======.....======c==cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT====~~~~."".....T======.....=======c==cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT===.~~~~......c=========c==========c==cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT===.q~~q......c=========c==========c==cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT===..T..."""".c=========c========..c==cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT===..T."""""""c====cc==ccc============cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT==...T""""""""c====c"""""c============cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.....T""q~~q""c====c"""""c============cTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT....#T""~~~~""c==ccc"""""ccc==cccccccccTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.....#""~~~~"....T"""""""#.===========.TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.....#."~~~~.....T.""""""..===========.TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.....#."q~~q.....T.""""""""..=========.################TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.....#........!..T..."""""""..======...===============#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.....#...........#..#"""""""...........===============#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.....#...........#.....""".............#############==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTT#==#TTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTT#==#TTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTT""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTT#==#TTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTT""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTT#==#TTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTT""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTT#==#TTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTT""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTT#==#TTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTT""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#===#TTT####==#TTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTT""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#===#TT#======#TTTTTT#==#TTT"""""""""""""""""""""""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTT#======TTTTTTT#==#TTT"""""""""""""""""""""""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTT#==####TTTTTTT#==#TTT"""""""""""""""""""""""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTT#==#TTTTTTTTTT#==#TTT"""""""""""""""""""""""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTT#==#TTTTTTTTTT#==#TTT"""""""""""""""""""""""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTEEEEEETTTTTTTTTTTTT#==#TTT#==#TTTTTTTTTT#==#TTT"""""""""""""""""""""""T#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTEEEEEETTTTTTTTTTTTT#==#TTT#==#TTTTTTTTTT#==#TTT"""""""""""""""""""""""T#==#TTTTTTTTTTTTTTTTTTTTTTTTT...........""""""""""""""""...""""".TTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTEEEEEETTTTTTTTTTTTT#==#TTT#==#TTTTTTTTTT#==##########..........####"""T#==#TTTTTTTTTTTTTTTTTTTTTTTTT.........==""""""""""""""...."""""""TTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTEEEEEETTTTTTTTTTTTT....TTT....TTTTTTTTTT#=========================#"""T#==##########################TTTTTTTT#===="""""""""......""""""""TTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTEEDEEETTT.........====.TTT....TTTTTTTTTT#=========================#"""T#============================........=====c===========c""""""""""TTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTT.......TT.........=====TTT....TTTTTTTTTT########################==#TTTT#============================........=====c===========c""""""""""TTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTT====TTTT........#.====TTT....TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTT################################TTTTTTTTTTc===========c."""....."TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT..=======...............==TTT#...TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT..........cc==ccccc==cc""""BBBBB"TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT..=======.................TTT....TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT..."...."..............."".BBBBB.TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT..========.c=======c......TTT==..TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT..""....""..............===BDBBB.TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT.....=====.c=======c===...TTT====TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.""".""."""...q~~~~~~~~q=======!.TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT.....=====.c=======c====..TTT====TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#==#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT"...""""......~~~~~~~~~~=======..TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT...........TTTTcc==c======TTT====TTTTTTTTTTTTTTTTTT.............T....................TTTTTTTTTTTTTTTTTTTTT".."""""".....q~~~~~~~c=========cTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTq~~~~~~~~~qTTTTTc==c======TTT====TTTTTTTTTTTTTTTTTT.....""""....T........"""""....===TTTTTTTTTTTTTTTTTTTTT".."""""".....""""""~~c=========cTTTTTTTTTTTTTTT',
    'TTTTTTTTTTT~~~~~~~~~~~TTTTTc==c======TTT===.TTTTTTTTTTTTTTTTTT...""""""""..T....."""""""""".====TTTTTTTTTTTTTTTTTTTTT"...""""......""""""~~ccc==c==cccTTTTTTTTTTTTTTT',
    'TTTTTTTTTTT~~~~~~~~~~~TTTTTc==c=====.TTT==..TTTTTTTTTTTTTTTTTT.."""""""""..T....""""""""""""====TTTTTTTTTTTTTTTTTTTTT.""".""."""...q~~~~~~~~qc==c=====TTTTTTTTTTTTTTT',
    'TTTTTTTTTTTq~~~~~~~~~q====Tc==c=====.TTT....TTTTTTTTTTTTTTTTTT.."""""""""..T..."""""""""""""====TTTTTTTTTTTTTTTTTTTTT..""...."".==.q~~~~~~~~qc==c=====TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT.N.........=====c========cTTT....TTTTTTTTTTTTTTTTTT..""""""""...T...""""""""""""=====TTTTTTTTTTTTTTTTTTTTTTTTTTT.."====...........c==c=====TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT............====c========cTTT....TTTTTTTTTTTTTTTTTT...""""".....T....""""...""".=====TTTTTTTTTTTTTTTTTTTTTTTTTTT...====c=============c..===TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT................c========c==.....TTTTTTTTTTTTTTTTTT...""".."q~~~~~~~~~~~~~~q....=====TTTTTTTTTTTTTTTTTTTTTTTTTTT..=====c=============c"""==TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT....c==============ccc==cc==.....TTTTTTTTTTTTTTTTTT...."..""~~~~~~~~~~~~~~~~###########################TTTTTTTTTTT=====cccc==ccccc==cc"""".TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT..""c==============c========.....TTTTTTTTTTTTTTTTTT.......""~~~~TTTTTTTT~~~~.........==================..======..T====........T""""""""""".TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT."""c==============c========.....##################.====."""~~~~TTTTTTTT~~~~.........==================..=======!TTTTTTTTTTTTTT""""""""""".TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT."""ccccccc==ccccccc#======.!....==================.====="""~~~~~~~~~~~~~~~~"".......##################....=====..........."""""""""""""...TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT.""""""""""""""""""""#====.......==================..====.""q~~~~~~~~~~~~~~q"""".....TTTTTTTTTTTTTTTTTT....................."""""""""""....TTTTTTTTTTTTTTT',
    'TTTTTTTTTTT...""""""""""""""""""#====.......##################..=====..............TT..."""""...TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTT...."""""""""""""""..#...........TTTTTTTTTTTTTTTTTT..=====..TTTTTTTTTTTTTT.k.""""""".TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTT......"""""...."""...#...........TTTTTTTTTTTTTTTTTTTTTTTTTTT....===..........""""""".TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.............=====.........""""...TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.....""""""""=====.HHHHH..""""""".TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT....""""""""""====.HHHHH..""""""..TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT....""""""""""====.HDHHH."""""....TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT.....""""""""........!..."""".....TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT....."""""""""""!.......""""......TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT......."""""""........."""".......TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT...............====...............TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#========#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#========#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#========#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#========#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#========#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#========#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
    'TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT#vvvvvvvv#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT',
]

def safari_zone():
    """The Safari Zone, tile for tile after Pokemon Journeys' map (Map249, 165 x 90; Jordan, 11-08: exact): in
    at the bottom to the Center, with its pond and rest house; the sand corridors between their walls to East,
    North and West, each with its own Pokemon, ponds, plateaus and steps, tall grass and rest house. The Warden's
    Gold Teeth are in the West area."""
    return list(SAFARI_ZONE_ROWS)


ROUTE_19_ROWS = [  # (from Pokemon Journeys' map, x 0-35, rows 0-57: colour shares, then by hand)
    'ccccccc.######c^^cccccccTTTTTTTTTTTT',
    'ccccccc=======c==cccccccTTTTTTTTTTTT',
    'ccccccc.######c==cccccccTTTTTTTTTTTT',
    'ccccccc=======c==cccccccq~~~~~~~~~~~',
    'ccccccc.######c==ccccccc~~~~~~~~~~~~',
    'ccccccc==========ccccccc~~~~~~~~~~~~',
    '~~~~~qqo========oqq~~~~~~~~~~~~~~~~~',
    '~~~~~qqo========oqq~~~~~~~~~~~~~~~~~',
    '~~~~~qqo========oqq~~~~~~~~~~~~~~~~~',
    '~~~~~qqoo=======oqq~~~~~~~~~~~~~~~~~',
    '~~~~~qqooo=====!oqq~~~~~~~~~~~~~~~~~',
    '~~~~~qqooooooooooqqqq~~~~~~~~~~~~~~~',
    '~~~~qqoooooooooooooqq~~~~~~~~~~~~~~~',
    '~~~~qqoooooooooooooqq~~~~~~~~~~~~~~~',
    '~~~qqooooooooooooooqq~~~~~~~~~~~~~~~',
    '~~~qqqqoooooooooooqqqq~~~~~~~~~~~~~~',
    '~~~~~qqoooooooooooqqqq~~~~~~~~~~~~~~',
    '~~~qqooooooooooooooooqq~~~~~~~~~~~~~',
    '~~~qqooooooooooooooooqq~~~~~~~~~~~~~',
    '~qqooooooooooooooooooqq~~~~~~~~~~~~~',
    '~qqoqqooooooXooooooooqq~~~~~~~~~~~~~',
    '~qqoqqooooooooooooooooqq~~~~~~~~~~~~',
    '~qqoooooooooooooooooooqq~~~~~~~~~~~~',
    'qqoooooooooooooooooqqoqq~~~~~~~~~~~~',
    'qqooooooooooooooqqoqqoqq~~~~~~~~~~~~',
    '~qqoooooooooooooqqooooqq~~~~~~~~~~~~',
    '~qqoooooooooooooooooooqq~~~~~~~~~~~~',
    'qqoooooooooooooooooooqq~~~~~~~~~~~~~',
    'qqoooooooooooooooooooqq~~~~~~~~~~~~~',
    '~qqoooooqqooooooooooooqq~~~~~~~~~~~~',
    '~qqoooooqqooooooooooooqq~~~~~~~~~~~~',
    '~qqooooooooooooooooooqq~~~~~~~~~~~~~',
    '~qqoooooooooooooooqqoqq~~~~~~~~~~~~~',
    'qqoooqqoooooooooooqqqq~~~~~~~~~~~~~~',
    'qqoooqqoooooooooooooqq~~~~~~~~~~~~~~',
    'qqooooooooooooXooqqqq~~~~~~~~~~~~~~~',
    'qqoooooooooooooooqqqq~~~~~~~~~~~~~~~',
    'qqoqqoooooooooooooooqq~~~~~~~~~~~~~~',
    'qqoqqoooooooooooooooqq~~~~~~~~~~~~~~',
    'ooooooooooooooooooooooqq~~~~~~~~~~~~',
    'woooooooXoooooooooooooqq~~~~~~~~~~~~',
    'wooooooooooooooooooooqq~~~~~~~~~~~~~',
    'wooooooooooooooooooooqq~~~~~~~~~~~~~',
    'wooooooooooooooooooooqq~~~~~~~~~~~~~',
    'wooooooooooooooooooooqq~~~~~~~~~~~~~',
    'wooooooooooooooooooooqq~~~~~~~~~~~~~',
    'wooooooooooooooooooooqq~~~~~~~~~~~~~',
    'woooooooooooooooooooqq~~~~~~~~~~~~~~',
    'woooooooooooooooooqqqq~~~~~~~~~~~~~~',
    'ooooooooooooooooooqqoqq~~~~~~~~~~~~~',
    'oooqqooooooooooooooooqq~~~~~~~~~~~~~',
    'oooqqooooooooqqooooqq~~~~~~~~~~~~~~~',
    'ooooooooqqoooqqooqqqq~~~~~~~~~~~~~~~',
    'ooooooooqqoooooooqq~~~~~~~~~~~~~~~~~',
    'ooqqqqqq~~qqqqooqq~~~~~~~~~~~~~~~~~~',
    'qqqqqqqqqqqqqqqqqq~~~~~~~~~~~~~~~~~~',
    'qq~~~~~~qq~~~~qq~~~~~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
]

def route_19():
    """Route 19, tile for tile after Pokemon Journeys' map (Map052, its x 0-35, rows 0-57; Jordan, 11-08: exact):
    the beach under Fuchsia's south gate between the two cliffs, its ledges and sign; then the sea (Surf) inside
    its ring of rocks, round to the west and Route 20. (Journeys has no trainers here: ours are out swimming.)"""
    return list(ROUTE_19_ROWS)


ROUTE_20_ROWS = [  # (from Pokemon Journeys' map, x 0-119, rows 33-56: colour shares, then by hand)
    'oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo',
    'oooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo',
    'ooooooooooooooooooooooqqooooooooooooooooooqqqqooooooooooooocccooqqooooqqqqoooooooooooooooooooooooooooooooooooooooooooooo',
    'ooooooooooooqqooooqqqqqqqqooooooqqooooooqqqqqqqqqqoooooooocccccoqqqqqqqqqqqqqqooooooooooooooooooqqooooooooooooooooqqqqqq',
    'ooooooooooqqqqqqqqqqqqooqqqqqqqqqqqqqqqqqqooooqqqqqqoooooccccccc~~qqqqooooqqqqqqqqooqqooooooqqqqqqqqooooqqqqooooqqqqqqqq',
    'uqqoooooooqqooqqqqooooooooqqqqqqooqqqqqqooooqqooooqqqqocccccccccccoq========q~qqqqqqqqqqqqqqqqqq~~qqqqqqqqqqqqqqqqooooow',
    'uqqooooooqqoooooooqqooooooooooooooooooooooooqqooqqooqqoccccccccccc===========qooooqqooqqqqqqooooqqooqqqqooooqqqqoooqqoow',
    'uooqqqqqqqqoqqooooqqoo===oooooooooqqooooooooooooqqoqqqqccccccccccc============ooooooooooooooooooqqoooooooooooooooooqqoow',
    'uooqqqqqqoooqqooooooo======oooooooqqoooooooooooooooqqqqccccccccccc====ccccc===ooooooooooooooooooooooooooooooooooooooooow',
    'uoooooooooooooooooooo======ooooooooooooo=====oooooqqooo=cccQQQccc====ccccccc==ooooooooooooooooooooooooooooooooooooooooow',
    'uoooooooooooooooooooo=====oooooooooooooo=====ooooooooqq==ccQDQccc===ccccccccc=ooooooooooooooooooooooooooooooooooooooooow',
    'uoooooooooooooooooooooooooooooXooooooooo=====oooooXqoqq============cccccccccccoooooooooooooooooXooooooooooooooooooooooow',
    'uooooooooooooooooooooooooooooooooooooooooo===oooooqqoooq===========cccccccccccqqooooooooooooooooooooooooooooooooooooooow',
    'uooooooooooooooooooooooooooooooooooooooooooooooooooqqooo=======qooqcccccccccccqqooqqooooooooooooooooooooooooooooooooooow',
    'uoooooooooooooooooooooooooooooo==ooooooooooooooooooqqooooooooooooqqcccccccccccoqqoqqooqqooooooooooooooooooooooooooooooow',
    'uooooooooooooooo===oooooooooooo==ooooooooooooooooooooqqooooooooqqqqccccPPPcccqoqqoooooqqooooooooooooooooooooooooooooooow',
    'uoqqooooooooqqoo===ooooooooooooooooooooooooooooooooooqqqqqqqqqqqqooq!ccPDPccqoooqqooqqooooooooooooooooooooooooooooooooow',
    'ooqqooooooooqqooooooooooooooooooooooooooooooooqqoooooooqqqqqqqqooooo=======qooooqqqqqqooqqoooooooqqooooooooooooqqooooooo',
    'ooooooqqqqooooooooooooooooqqooooooooqqooooooooqqooooooooooooooooooooooq====oooooqqqq~~qqqqoooooooqqoooqqqqoooooqqooooooo',
    'ooooqqqqqqqqooqqqqqqooooqqqqqqooooqqqqqqooqqqq~~qqooooooooooooooooooooooooooooqqqq~~~~qqooooqqqqooooqqqqqqqqqqooooqqqqoo',
    'qqqqqq~~~~qqqqqqqqqqqqqqqq~~qqqqqqqq~~qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq~~~~~~~~qqqqqqqqqqqqqq~~~~qqqqqqqqqqqqqq',
    'qqqq~~~~~~~~qq~~~~~~qqqq~~~~~~qqqq~~~~~~qq~~~~qq~~qqqqqqqqqqqqqqqqqqqqqqqqqqqq~~~~~~~~~~qqqq~~~~qqqq~~~~~~~~~~qqqq~~~~qq',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
    '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
]

def route_20():
    """Route 20, tile for tile after Pokemon Journeys' map (Map053, its x 0-119, rows 33-56; Jordan, 11-08: exact): the long sea route (Surf) between its lines of rocks, the sandbars, and the Seafoam Islands' two mounds with their cave mouths; east to Route 19, west to Cinnabar. (Journeys has no trainers here: ours are out swimming.)"""
    return list(ROUTE_20_ROWS)


ROUTE_21_ROWS = [  # (from Pokemon Journeys' map, 34 x 100: colour shares, then by hand)
    'TTTTTTTTTTTkwwwwkkkkkkkTTTTTTTTTTT',
    'TTTTTTTTTTT.oooo.......TTTTTTTTTTT',
    'TTTTTTTTTTT.oooo.......TTTTTTTTTTT',
    'TTTTTTTTTTT.oooo..!....TTTTTTTTTTT',
    'TTTTTTTTTTT.oooo.......TTTTTTTTTTT',
    'TTTTTTTTTTT.oooo"""""".TTTTTTTTTTT',
    'TTTTTTTTTTT.oooo"""""".TTTTTTTTTTT',
    'TTTTTTTTTTT.oooo"""""".TTTTTTTTTTT',
    'TTTTTTTTTTT.oooo"""""".TTTTTTTTTTT',
    'TTTTTTTTTTT.oooo"""""".TTTTTTTTTTT',
    'TTTTTTTTTTT.oooo""""""kkkkkkkkkkkk',
    'TTTTTTTTTTT.ooooooooooqq~~~~~~~~~~',
    'TTTTTTTTTTT.ooooooooooqq~~~~~~~~~~',
    'TTTTTTTTTTT.oooooooooqq~~~~~~~~~~~',
    'kkkkkkkkkkkkoooooooooqq~~~~~~~~~~~',
    '~~~~~~~~~~qqooooooooooqq~~~~~~~~~~',
    '~~~~~~~~~~qqqqooooooooqq~~~~~~~~~~',
    '~~~~~~~~qq~~qqooooooooooqq~~~~~~~~',
    '~~~~~~~~qq~qqoooooooooooqq~~~~~~~~',
    '~~~~~~~~~~~qqooooooooooooqq~~~~~~~',
    '~~~~~~~~qqqqooooooooooqqoqq~~~~~~~',
    '~~~~~~~~qqqqooooooooooqqooqq~~~~~~',
    '~~~~~~~qqoooooooooooooooooqq~~~~~~',
    '~~~~~~~qqoqqoooooooooooooooqq~~~~~',
    '~~~~~~qqooqqooooooooo===oooqq~~~~~',
    '~~~~~~qqoooooooooooo====oooqq~~~~~',
    '~~~~~qqooooooooooooo===ooooqq~~~~~',
    '~~~~~qqoooooooooooooooooooqq~~~~~~',
    '~~~~~qqoooo===ooooooooooooqq~~~~~~',
    '~~~~~qqooo======oooooooooooqq~~~~~',
    '~~~~~~qqoo=====Xoooooooooooqq~~~~~',
    '~~~~~~qqoo======ooooooooooqq~~~~~~',
    '~~~~~~qqooooo==oooooooooooqq~~~~~~',
    '~~~~~~qqoooooooooooooooooqq~~~~~~~',
    '~~~~~qqooqqooooooooooooooqq~~~~~~~',
    '~~~~~qqooqqooooooooooooooooqq~~~~~',
    '~~~~~~qqoooooqqooooooooooqqqq~~~~~',
    '~~~~~~qqoooooqqooooooooooqq~~~~~~~',
    '~~~~~~~qqoooooooooooooooooqq~~~~~~',
    '~~~~~~~qqooqqoooooooooooooqq~~~~~~',
    '~~~~~~~qqooqqoooooooo==oooqq~~~~~~',
    '~~~~~~~qqooooooooooo====ooqq~~~~~~',
    '~~~~~~qqoooooooooooo====ooqq~~~~~~',
    '~~~~~~qqoooooooooooo===oooqq~~~~~~',
    '~~~~~~~~qqoooooooooooooooooqq~~~~~',
    '~~~~~~~~qqoooooooooooooooooqq~~~~~',
    '~~~~~~qqooooooooooooooooooqq~~~~~~',
    '~~~~~~qqooooooooooooooooooqq~~~~~~',
    '~~~~~qqooooooooooooooooooooqq~~~~~',
    '~~~~~qqooooooooooooooooooooqq~~~~~',
    '~~~~~qqooqqooooooooooooqqooqq~~~~~',
    '~~~~~qqooqqooooooooooooqqooqq~~~~~',
    '~~~~~~qqooooooooooooooooooqq~~~~~~',
    '~~~~~~qqqqooooooooooooooooqq~~~~~~',
    '~~~~~~~~qqooqqoooooooooooqq~~~~~~~',
    '~~~~~~~qqoooqqoooooooooooqq~~~~~~~',
    '~~~~~~~qqooooooooooooooooqq~~~~~~~',
    '~~~~~~~qqooo==oooooooooooqq~~~~~~~',
    '~~~~~~~qqooo====ooooooooooqq~~~~~~',
    '~~~~~~~~~qqoo===ooooooooooqq~~~~~~',
    '~~~~~~~qqqqoooXoooooooooqqqq~~~~~~',
    '~~~~~~~qqoooooooooooooooqqqq~~~~~~',
    '~~~~~~qqooooooooooooooooooqq~~~~~~',
    '~~~~~~qqoqqooooooooo====ooqq~~~~~~',
    '~~~~~~qqoqqoooooooo=====ooqq~~~~~~',
    '~~~~~~qqooooooooooo=====ooqq~~~~~~',
    '~~~~~~~qqooooooooooo===oooqq~~~~~~',
    '~~~~~~~qqoooooooooooooooooqq~~~~~~',
    '~~~~~~~qqooooooooooooooooqq~~~~~~~',
    '~~~~~~~qqooooooooooooooooqq~~~~~~~',
    '~~~~~~qqoooooooooooooooooqq~~~~~~~',
    '~~~~~~qqoo=====ooooooooooqq~~~~~~~',
    '~~~~~~qqoo======ooooooooooqq~~~~~~',
    '~~~~~~qqooo=====ooooooooooqq~~~~~~',
    '~~~~~~~qqooo====ooooooooqq~qq~~~~~',
    '~~~~~qqqqoooooooooooooooqq~qq~~~~~',
    '~~~~~qqqqoooooooooooooooooqq~~~~~~',
    '~~~~~~~qqoooooooooooooooooqq~~~~~~',
    '~~~~~~qqooooooooooooooooooqq~~~~~~',
    '~~~~~~qqooooooooooooooooooqq~~~~~~',
    '~~~~~qqooooooooooXoooooooooqq~~~~~',
    '~~~~~qqoooooooooooooooooqqoqq~~~~~',
    '~~~~~~qqoqqoooooooooooooqqqq~~~~~~',
    '~~~~~~qqoqqqqoooooooooooooqq~~~~~~',
    '~~~~~~qqoooqqoooooooooooooqq~~~~~~',
    '~~~~~~qqoooooooooooooooqqoqq~~~~~~',
    '~~~~~~qqooooo====ooooooqqoqq~~~~~~',
    '~~~~~~qqooo======ooooqqoooqq~~~~~~',
    '~~~~~~qqooo====ooooooqqooqq~~~~~~~',
    '~~~~~~qqoooooooooooooooqqqq~~~~~~~',
    '~~~~~~~qqooooooooooooooqq~~~~~~~~~',
    '~~~~~~~qqoooooooooooooqq~~~~~~~~~~',
    '~~~~~~~qqoqqooooooooooqq~~~~~~~~~~',
    '~~~~~~~qqoqqoooooooooqq~~~~~~~~~~~',
    '~~~~~~qqoooqqooooooooqq~~~~~~~~~~~',
    '~~~~~~qqqqoqqooooooooqq~~~~~~~~~~~',
    '~~~~~~qqqqooooo=====oqq~~~~~~~~~~~',
    '~~~~~~qqooooooo======oqq~~~~~~~~~~',
    '~~~~~qqoooooooo======oqq~~~~~~~~~~',
    '~~~~~qqooouuuuuoo====oqq~~~~~~~~~~',
]

def route_21():
    """Route 21, tile for tile after Pokemon Journeys' map (Map054, 34 x 100; Jordan, 11-08: exact): from Pallet Town's channel between the trees, the fenced tall grass, then the long open sea (Surf) inside its rocks, its sandbars, on to Cinnabar Island. (Journeys has no trainers here: ours are out swimming.)"""
    return list(ROUTE_21_ROWS)


SEAFOAM_FLOORS = [  # (from Pokemon Journeys' Map340: its five floors side by side, x 0-35, 40-83, 88-131, 140-183,
    # 192-235; by colour. Ladders line up floor to floor in the original; B2F's need an order: "ladders")
    [  # 1F
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccc.....c',
        'cccc.!.....................ccc.+...c',
        'cccc....s..................c.c.....c',
        'cccc...sss+........cc........c.....c',
        'cccc.cssss....ccccccccccc==ccc.....c',
        'cccc.csssss...c......c..c...c.c....c',
        'cccc..sssss...c.........cc......s..c',
        'ccccc.ssss...cc.....s...cc.sssssss.c',
        'ccccc..sss....c....sss..ccsssssss..c',
        'cccc....s.....c....sss..cc.sssss...c',
        'cccc.......c..c...ssss..cc..sss....c',
        'cccccccc==ccccc..ssssss.cccccbcccccc',
        'ccc.............ssssss..cc.........c',
        'ccc...........sssssss...cc.........c',
        'ccc...........ssssss....cc.........c',
        'ccc............sss......cc.........c',
        'ccc.....................cc..+......c',
        'ccccc...ccccccccccccccccccccccc...cc',
        'ccccc<<<ccccccccccccccccccccccc>>>cc',
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccc',
    ],
    [  # B1F
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'ccccccccccccccccccc..........ccccccccccccccc',
        'ccccccc....+......c..........c.....c...ccccc',
        'ccccccc...........c..........c.....-...ccccc',
        'ccccccc..cccccccccc.....cc==cc.........ccccc',
        'ccccccc..c.....-ccc.....c.....c........ccccc',
        'ccccccc..c.......cc.....c.....c........ccccc',
        'ccccccc..c....ccccc.....c..c..c.c......ccccc',
        'ccccccc..c....ccccc..+..c.....c........ccccc',
        'ccccccc..c....cc........c.....c........ccccc',
        'ccccccc..cc==ccc........c.....cccccccccccccc',
        'ccccccc........c........cccccc.........ccccc',
        'ccccccc........c.............c.........ccccc',
        'ccccccc........c.............c......+..ccccc',
        'ccccccc........c.............c.........ccccc',
        'ccccccc........cc==ccccccccccc.........ccccc',
        'ccccccc..............c........c........ccccc',
        'ccccccc..............c........c.c......ccccc',
        'ccccccc..............c.......+c.-......ccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
    ],
    [  # B2F
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'ccccccc....c...................ccccccccccccc',
        'ccccccc....-...................c....+.cccccc',
        'ccccccc........................c......cccccc',
        'ccccccc..........cccccccc......c......cccccc',
        'ccccccc........ssc...c..c......cccc==ccccccc',
        'ccccccc....ssssssc...cc.c...cccc.......ccccc',
        'ccccccc..ssssssssc...-..c....cc........ccccc',
        'cccccccccccccccccc......cccccccc.......ccccc',
        'cccccccc.......................c.......ccccc',
        'cccccccc.......................c.......ccccc',
        'cccccccc.......................ccccccccccccc',
        'cccccccccccc==cccccccccc.......cc...-.cccccc',
        'ccccccc.........sssssssc.......cc.....cccccc',
        'ccccccc............ssssccc==ccccc.....cccccc',
        'ccccccc....+.........ssss.......c..+..cccccc',
        'ccccccc......................c..c.....cccccc',
        'ccccccc................cc....-..cccccccccccc',
        'ccccccccccccccccccccccccc.cccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
    ],
    [  # B3F
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'ccccccc.........ccccccccccccc.....-c.ccccccc',
        'ccccccc.........cccoooooooocc...+....ccccccc',
        'ccccccc.........ccooooooooooc........ccccccc',
        'ccccccc.........ccccccccccoocccccccccccccccc',
        'ccccccc.....c==ccc.......coocccccccccccccccc',
        'ccccccc.....c..+.c.......cooc........ccccccc',
        'ccccccc.....c....c...cc==cooc........ccccccc',
        'ccccccc.....cccccc...ccooooocc==c....ccccccc',
        'ccccccc.c............cooooooooocc....ccccccc',
        'ccccccc.cc....cccc...cooooooooooc....ccccccc',
        'ccccccc.......c..c....ccccccooccc....ccccccc',
        'ccccccccccccccc..c.........cooc...c..ccccccc',
        'cccccc........c..c.........cooc...-..ccccccc',
        'cccccc....c......cccccccccccoocccccccccccccc',
        'cccccc...-c.c...c........cccoocccccccccccccc',
        'cccccc....c..............cccoocccccccccccccc',
        'ccccccccccccccccccccccccccccoocccccccccccccc',
        'ccccccccccccccccccccccccccccoocccccccccccccc',
        'ccccccccccccccccccccccccccccoocccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
    ],
    [  # B4F
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccooooooccccccccccccccccccccccccc',
        'cccccoocccccooooooooc..........!cccccccccccc',
        'cccccoocccccooooooooc............ccccccccccc',
        'cccccoocc==cooooooooc............-cccccccccc',
        'cccccoooooooooccccccc...ccccc==ccccccccccccc',
        'cccccoooooooocc.cc......ccoooooooooccccccccc',
        'cccccooooooooc...-......cooooooooooocccccccc',
        'cccccooooooooc.........ccooooooooooocccccccc',
        'cccccoooooooocc......ccccooooooooooocccccccc',
        'cccccoooooooocc==ccc.ccooooooooooooocccccccc',
        'cccccooooooooooooocc.coooooooooooooccccccccc',
        'cccccooooooooooooooc.coooooooooooooccccccccc',
        'cccccooooooooooooooc.coooooooooooooccccccccc',
        'cccccooooooooooooooc.coooooooooooooccccccccc',
        'ccccccccccccoooccccc.cccoooooooooooccccccccc',
        'ccccccccccccoooc.......cccoooooooooccccccccc',
        'ccccccccccccoooc.!.......coocccccccccccccccc',
        'ccccccccccccoooc....N....coocccccccccccccccc',
        'ccccccccccccooocc.......ccoocccccccccccccccc',
        'ccccccccccccooocccccccccccoocccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccccccccccc',
    ],
]

def seafoam(floor):
    """The Seafoam Islands, tile for tile after Pokemon Journeys' five floors (Map340; Jordan, 11-08: exact), icy:
    the ice walls, boulders, sandy patches and wooden steps; the ladders pair floor to floor where they line up;
    a boulder between its two halves on 1F needs Strength and the slide puzzle; B3F and B4F's water needs Surf; Articuno on B4F."""
    return list(SEAFOAM_FLOORS[floor])


def cinnabar_island():
    """Cinnabar Island, tile for tile after FireRed / LeafGreen's (Downloads/Cinnabar_Island_FRLG.png, 24 x 20;
    Jordan, 11-08: exact): the Pokemon Mansion top left, the volcano's mouth at the top, the Gym top right; the Pokemon
    Lab; the Pokemon Center and the Mart side by side; the harbor on the south beach (in from its north side); the
    sand and lawn; the sea rocks; north by Surf to Route 21, east by Surf to Route 20."""
    g = Grid(24, 20, "~")
    def rect(x, y, w, h, ch):
        g.rect(x, y, w, h, ch)
    rect(5, 0, 18, 12, "s"); rect(8, 12, 15, 3, "s")
    rect(12, 2, 11, 6, "."); rect(14, 0, 8, 2, "."); rect(7, 10, 5, 1, "."); rect(12, 12, 9, 1, "."); rect(21, 5, 2, 3, ".")
    rect(13, 5, 7, 2, "s")
    rect(12, 0, 2, 1, "w")
    g.building(5, 0, 7, 5, "Y", door_x=3)
    g.building(14, 0, 3, 2, "V", door_x=1)
    g.building(17, 0, 6, 5, "G", door_x=3)
    g.building(5, 6, 7, 4, "L", door_x=3)
    g.building(12, 8, 5, 4, "C", door_x=2)
    g.building(17, 8, 4, 4, "M", door_x=2)
    rect(14, 13, 4, 2, "H"); g.put(15, 13, "D")    # (the harbor: in from the north)
    g.put(12, 3, "!").put(22, 5, "!").put(9, 10, "!")
    rect(23, 6, 1, 7, "u")
    for x, y in ((0, 0), (0, 2), (2, 4), (2, 6), (0, 8), (0, 10), (2, 12), (2, 14), (3, 16), (5, 17), (7, 17), (9, 18), (11, 18),
                 (13, 18), (15, 17), (17, 17), (19, 17), (21, 18), (23, 18), (23, 5)):
        g.put(x, y, "q")
    return g.rows()


def saffron_city():
    """Saffron City, tile for tile after assets/backgrounds/kanto/saffron_city.png (Jordan, 11-07: exact, one
    of our tiles to each of the picture's 16 px tiles): gray streets and brick sidewalks; blue railings along
    the edges; lamps and hydrants; Silph Co.'s tower in the middle with its plaza; the Magnet Train station
    top left; the Fighting Dojo and the Gym top right behind their railing; Copycat's purple-roofed house; the
    Mart; the Pokemon Center; rows of apartments (closed); a gatehouse on each side (Routes 5 north, 6 south,
    7 west, 8 east)."""
    g = Grid(69, 53, "T")
    g.rect(8, 8, 54, 41, "p")                  # the city: sidewalks, then the streets
    g.rect(8, 8, 54, 1, "i").rect(8, 8, 1, 41, "i").rect(61, 8, 1, 41, "i").rect(8, 48, 54, 1, "i")   # railings
    g.rect(24, 8, 6, 2, "p")                   # (the way in from the north gate)
    # the streets (from the picture's road colour, tile by tile)
    g.rect(25, 10, 4, 7, "a")                  # the avenue from the north gate
    g.rect(10, 17, 50, 1, "a").rect(9, 18, 52, 1, "a")       # the main road
    g.rect(10, 19, 4, 25, "a").rect(57, 19, 4, 25, "a")      # down the west and east sides
    g.rect(10, 24, 18, 3, "a").rect(42, 24, 19, 3, "a")      # toward Silph Co.
    g.rect(30, 33, 10, 3, "a")                 # Silph Co.'s plaza
    g.rect(9, 36, 52, 1, "a")                  # the cross street
    g.rect(10, 43, 51, 1, "a")                 # the bottom road
    g.rect(25, 44, 4, 5, "a")                  # the avenue to the south gate
    g.rect(1, 38, 9, 3, "a").rect(56, 38, 12, 3, "a")        # out to the west and east gates
    g.rect(8, 37, 1, 5, "p").rect(61, 37, 1, 5, "p")         # (gaps in the railings there)
    g.rect(5, 36, 3, 6, ".").rect(62, 36, 2, 6, ".")         # the gates' lawns
    g.rect(1, 38, 1, 3, "a")
    # the gatehouses
    g.building(24, 0, 6, 8, "A", door_x=2)     # north: Route 5 (its door: the stairs down into the city)
    g.rect(25, 49, 5, 4, "B").put(26, 48, "vv")   # south: Route 6
    g.rect(0, 35, 6, 6, "E").put(6, 38, "<").put(6, 39, "<")   # west: Route 7
    g.rect(64, 35, 5, 6, "F").put(63, 38, ">").put(63, 39, ">")   # east: Route 8
    g.rect(6, 38, 1, 3, "<").rect(63, 38, 1, 3, ">")
    # along the top
    g.building(10, 7, 9, 8, "S", door_x=6)    # the Magnet Train station
    g.building(19, 9, 5, 6, "\u0391")         # apartments (closed)
    g.building(30, 9, 5, 6, "\u0392").building(35, 9, 5, 6, "\u0393")
    g.building(44, 7, 7, 5, "O", door_x=3)     # the Fighting Dojo
    g.building(51, 7, 7, 5, "G", door_x=3)     # the Gym
    g.rect(40, 14, 9, 1, "i").rect(50, 14, 3, 1, "i").rect(57, 14, 4, 1, "i")   # the railing in front of them
    g.put(49, 14, "!").put(56, 14, "!")        # their signs
    # the second row
    g.building(14, 19, 4, 4, "\u0394").building(18, 19, 4, 4, "\u0395")
    g.building(22, 19, 4, 4, "H")              # Copycat's house
    g.building(26, 19, 4, 4, "\u0396")
    g.building(30, 19, 10, 12, "Y")            # Silph Co.
    g.building(40, 19, 3, 4, "\u0397")
    g.building(43, 19, 4, 4, "M")              # the Mart
    g.building(48, 19, 4, 4, "\u0398").building(52, 19, 4, 4, "\u0399")
    # the third row
    g.building(14, 28, 5, 6, "\u039a").building(19, 28, 5, 6, "\u039b").building(24, 28, 5, 6, "\u039c")
    g.building(41, 28, 5, 6, "\u039d").building(46, 28, 5, 6, "\u039e").building(51, 28, 5, 6, "\u039f")
    # the fourth row
    g.building(14, 37, 4, 4, "\u03a0")
    g.building(18, 37, 5, 4, "C")              # the Pokemon Center
    g.building(23, 37, 4, 4, "\u03a1").building(27, 37, 4, 4, "\u03a3").building(31, 37, 4, 4, "\u03a4")
    g.building(35, 37, 4, 4, "\u03a5").building(39, 37, 4, 4, "\u03a6")
    g.building(48, 38, 4, 3, "\u03a7")        # Mr. Psychic's house (closed)
    g.building(52, 37, 4, 4, "\u03a8")
    g.rect(43, 41, 4, 1, "i")
    # along the bottom
    for k, x in enumerate((12, 16, 20, 30, 34, 38, 42, 46, 50, 54)):  # (their fronts face the railing: no door)
        g.rect(x, 44, 4, 4, "\u03a9\u0411\u0413\u0414\u0416\u0417\u0418\u041b\u041f\u0424"[k])
    # lamps, hydrants, signs
    for x, y in ((9, 17), (9, 26), (9, 46), (14, 26), (26, 26), (43, 26), (55, 26), (42, 11), (59, 11),
                 (45, 39), (60, 46), (9, 36)):
        g.put(x, y, "l")
    for x, y in ((9, 16), (23, 16), (14, 23), (55, 23), (22, 34), (49, 34), (14, 41), (30, 41), (40, 41), (55, 41)):
        g.put(x, y, "h")
    g.put(18, 16, "!").put(32, 34, "!").put(47, 40, "!")
    return g.rows()


def power_plant():
    """The Power Plant, tile for tile after assets/backgrounds/kanto/power_plant.png (21 x 18; Jordan, 11-07:
    exact): the control wall along the top with its desks and lockers; the orange machines down the west wall;
    the generator's two machines behind yellow railings, the manager's booth between them (open from the top,
    the manager behind her counter); the railing across the room with the stairs down through it; the lower
    hall's wall (glass cases, a sign, a bookshelf) and the way out to Route 10. Zapdos (not in the picture)
    waits in the top corridor."""
    g = Grid(21, 18, "c")
    g.rect(1, 2, 19, 11, ".")                  # the upper floor
    for x in (3, 4, 6, 7, 9, 10):              # the desks with their computers
        g.put(x, 2, "m")
    g.put(1, 2, "m").put(19, 2, "m")           # the lockers
    g.rect(1, 4, 1, 8, "m")                    # the orange machines
    g.rect(4, 5, 8, 1, "i").rect(4, 5, 1, 6, "i").rect(11, 5, 1, 2, "i")   # the generator's railings
    g.rect(14, 5, 4, 1, "i").rect(17, 5, 1, 6, "i").rect(14, 5, 1, 2, "i").rect(4, 10, 14, 1, "i")
    g.rect(5, 6, 6, 4, "m").rect(15, 6, 2, 4, "m").rect(11, 7, 4, 3, "m")   # its machines and pipes
    g.put(12, 6, "N").put(13, 6, "N")          # the manager (before and after the Machine Part)
    g.put(17, 3, "N")                          # Zapdos
    g.rect(0, 13, 13, 1, "i").rect(15, 13, 6, 1, "i")   # the railing across the room; the stairs at 13-14
    g.rect(13, 13, 2, 2, ".")
    g.rect(1, 15, 19, 2, ".")                  # the lower hall
    g.rect(1, 15, 4, 1, "m").put(19, 15, "m")  # the glass cases, the bookshelf
    g.put(11, 14, "!")
    g.rect(6, 17, 2, 1, "v")                   # out to Route 10
    return g.rows()


def route_23():
    """Route 23, tile for tile after Pokemon Journeys' map (Map056, 34 x 160; Jordan, 11-07: exact): Victory
    Road's steps at the top behind a stone plaza of white posts; the big rocky hill and its side path; the
    badge gates (stone walls with an arch to pass through, a guard by each); the lake to Surf, crossed by more
    walls; flowers and pavement; the gatehouse down to Route 22 at the bottom."""
    g = Grid(34, 160, "T")
    g.rect(7, 0, 20, 160, ".")
    # Victory Road's steps, the plaza and its posts
    g.rect(7, 0, 7, 2, "c").rect(19, 0, 8, 2, "c").rect(15, 0, 3, 1, "^").rect(15, 1, 3, 1, "=")
    g.put(14, 0, "r").put(14, 1, "r").put(18, 0, "r").put(18, 1, "r")
    g.rect(10, 2, 14, 16, "e")
    g.rect(7, 1, 4, 4, "T").rect(23, 1, 4, 4, "T")   # the trees in the top corners
    posts = {2: (11, 13, 22), 3: (11, 13, 14, 17, 19, 22), 4: (12, 14, 17, 19, 21, 22), 5: (11, 15, 18, 21, 22),
             6: (11, 15, 18, 22), 7: (13, 15, 17), 8: (13, 15, 17, 21), 9: (11, 14, 16, 18, 21),
             10: (11, 14, 16, 18, 21), 11: (12, 15, 18), 12: (11, 12, 13, 15, 18, 20), 13: (11, 13, 15, 18, 20),
             14: (11, 13, 15, 18, 20, 22), 15: (11, 13, 20, 22)}   # (found by their white, tile by tile)
    for y, xs in posts.items():
        for x in xs:
            g.put(x, y, "j")
    g.rect(7, 5, 4, 11, "g").rect(23, 5, 4, 11, "g")   # the plaza's gate walls
    g.put(7, 16, "r").put(10, 16, "r").put(23, 16, "r").put(26, 16, "r")
    # the rocky hill, its side path (statues, a sign) and the way round on the right
    g.rect(8, 20, 15, 9, "c").rect(8, 24, 18, 5, "c")   # the hill (a grass strip either side, x 7 and 26)
    g.rect(14, 29, 4, 12, "c").rect(16, 33, 10, 8, "c").rect(20, 29, 3, 3, "c")   # the rock below it
    g.rect(8, 29, 5, 14, "e")                  # the side path
    g.put(8, 29, "r").put(12, 29, "r").put(8, 35, "r").put(12, 35, "r").put(8, 40, "r").put(12, 40, "r")
    g.put(8, 31, "!")
    for x, y in ((7, 33), (13, 29), (13, 34), (13, 39), (7, 40)):
        g.put(x, y, "r")
    # rocks and grass below the hill
    g.rect(17, 41, 5, 2, G)
    for x, y in ((16, 42), (16, 43), (17, 44), (16, 45), (17, 45), (18, 45), (19, 45)):
        g.put(x, y, "r")
    g.rect(21, 44, 6, 4, "e").rect(13, 47, 7, 5, "e").put(22, 49, "f")
    # the first badge gates
    g.rect(7, 44, 7, 8, "g").put(7, 52, "r").put(10, 52, "r").put(13, 52, "r")
    g.rect(20, 52, 7, 9, "g").put(20, 61, "r").put(23, 61, "r")
    g.rect(7, 54, 9, 8, "g").rect(20, 54, 3, 8, "g")     # (the arch: x 16-19)
    g.rect(16, 54, 4, 8, "e")
    g.put(13, 62, "r").put(16, 62, "r")
    g.rect(7, 62, 6, 18, "g").rect(24, 61, 3, 13, "g").put(24, 74, "r").put(26, 74, "r")
    g.rect(13, 62, 5, 3, G).rect(18, 65, 6, 3, G).rect(13, 70, 4, 3, G).rect(23, 75, 4, 3, G)
    for x, y in ((13, 66), (13, 68), (13, 70), (13, 72), (13, 74), (14, 75), (17, 64), (18, 66), (17, 68),
                 (18, 70), (21, 69), (21, 71)):
        g.put(x, y, "r")
    # the lake (Surf), its walls and their arches
    g.rect(13, 77, 9, 1, "s").rect(8, 78, 18, 40, "o")
    g.rect(7, 78, 1, 41, "s").rect(26, 78, 1, 11, "s")
    g.rect(21, 78, 6, 5, "g").rect(7, 78, 6, 5, "g")
    g.rect(7, 89, 5, 4, "g").rect(16, 89, 11, 4, "g").put(11, 93, "r")   # (the arch: x 12-15)
    g.rect(7, 93, 3, 11, "g").rect(23, 93, 4, 26, "g")
    g.rect(14, 98, 5, 5, "s")                  # the island
    g.rect(7, 108, 10, 4, "g").rect(21, 108, 6, 4, "g").put(17, 112, "r")   # (the arch: x 17-20)
    g.rect(7, 118, 10, 4, "g").rect(20, 118, 7, 4, "g").put(16, 122, "r").put(20, 122, "r")   # (the arch: 17-19)
    g.rect(17, 118, 3, 4, "e")
    # pavement, the last badge gates, flowers
    g.rect(9, 123, 18, 3, "e")
    g.rect(10, 126, 4, 5, "g").rect(17, 126, 10, 5, "g").put(13, 131, "r").put(17, 131, "r")
    g.rect(14, 126, 3, 6, "e")
    for x, y in ((9, 132), (10, 133), (9, 134), (22, 132), (26, 132), (25, 134), (8, 141), (7, 140)):
        g.put(x, y, "f")
    g.rect(7, 135, 4, 4, "g").rect(15, 135, 12, 4, "g")   # (the arch: x 11-14)
    g.put(7, 139, "r").put(10, 139, "r").put(15, 139, "r").put(26, 139, "r")
    g.rect(11, 139, 4, 2, "e").rect(15, 141, 10, 3, "e").rect(7, 140, 2, 13, "T").rect(25, 140, 2, 13, "T")
    g.rect(11, 144, 6, 4, "g").rect(21, 144, 4, 4, "g")   # (the arch: x 17-20)
    g.put(11, 148, "r").put(16, 148, "r").put(21, 148, "r").put(24, 148, "r")
    g.rect(11, 149, 11, 4, "e")
    for x, y in ((8, 150), (22, 150), (23, 151), (24, 152)):
        g.put(x, y, "f")
    # down to Route 22's gatehouse
    g.rect(7, 153, 2, 7, "c").rect(19, 153, 8, 7, "c")
    g.rect(9, 154, 10, 6, "B")
    g.rect(13, 153, 2, 1, "v")
    # the guards (the Boulder Badge's at the bottom), the signs
    for (x, y) in ((24, 18), (12, 43), (24, 51), (16, 63), (11, 94), (18, 113), (14, 132), (16, 143)):
        g.put(x, y, "N")
    g.put(15, 150, "!").put(16, 2, "!")
    return g.rows()


VICTORY_ROAD_FLOORS = {  # (from Pokemon Journeys' map, tile by tile: dev/tools/map_grid.py's method, its colours)
    0: [
        "ccccccccccccccccccccccccc",
        "cccc+ccccccccc.cc..cccccc",
        "cccc..cccccccc.ccc..ccccc",
        "cccc..cccccc.........cccc",
        "cccc...ccccccc..c.....ccc",
        "ccc...ccccccccccccccc..cc",
        "ccc...c.............c..cc",
        "ccc...c.............c..cc",
        "cccc..c.............c..cc",
        "cccc..cccc.ccc..ccc.c..cc",
        "ccccc........c..cc.....cc",
        "cccc..cccccc.c..ccc...ccc",
        "cccc.cc....ccc..ccccccccc",
        "cccc..c....ccc..ccccccccc",
        "cccc..c....ccc..cc...cccc",
        "ccc...c.........c....cccc",
        "cc...cc.ccccccccc.c..cccc",
        "cc..cc..ccc.........ccccc",
        "ccc.....cc...cc.....ccccc",
        "cccc.........cc..cccccccc",
        "cccccccc.....cccccccccccc",
        "cccccccccccvccccccccccccc",
    ],
    1: [
        "ccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "cccccccccccccccccccccccc.sssssssssssssssssccccccccccc",
        "ccccc................ccc.....sssssssssssssccccccccccc",
        "cccc-..................c.......ssssssssss.ccccccccccc",
        "cccc...................c............ssss.+ccccccccccc",
        "cccc...................c..................ccccccccccc",
        "ccccccccc.ccccc...r....c.....cccccccc.....ccccccccccc",
        "ccc.......c...c...cc...c............c.....ccccccccccc",
        "cc............c........c...........cc.cccccc....ccccc",  # (a gap: the ledge you hop down to the way out)
        "cc.c..........c........c............c...c........cccc",
        "cc......ccccccccccccccccc...........c.............ccc",
        "ccc.....c...............cs..........c.............ccc",
        "ccc....scc.cccccc.......csss........c......ccccc...cc",
        "ccc...ssss....c.ccccc...cssss.......ccccccccccccc.>cc",
        "ccc...ssss....c.ssssc...csssssss...........cccccccccc",
        "cccc...sss....c..sssc...ccccccccccc........cccccccccc",
        "cccc..........c..sssc............cccccccc...ccccccccc",
        "ccc...........c...ssc...................c..sccccccccc",
        "ccc.c.....ccccc.....cccc.ccccccc.cccccccc.ssccccccccc",
        "cccb...ccccccccb..........................ssccccccccc",
        "cccccccccccccccccc.....................sssssccccccccc",
        "ccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    ],
    2: [
        "ccccccccccccccccccccccccccccccccccccccccccccc",
        "ccccccccccccccccccccccccccccccccccccccccccccc",
        "ccccc-.ccccc............cc...............cccc",
        "ccccc...cc...............................cccc",
        "ccccc........cccccccccccccccc.........c..cccc",
        "cccc...c.c...c..............c......cccc..cccc",
        "cccc.....c...c..............c......cccc..cccc",
        "cccc...bcc...c...cccccccc.ccc......ccc...cccc",
        "ccc...cccc...c...c.................cccccccccc",
        "cccccccccccc.c...c................-c.....cccc",
        "ccc........ccc...c........ccc......c.-...cccc",
        "ccc........ccc...c.........c.......c.....cccc",
        "ccccc.ccc..ccc...c.............ccccc.....cccc",
        "cccc....c........c.............c.....c...cccc",
        "cccc....cccccccccc.............c...c.....cccc",
        "cccc..............c.cccccccccccc...c.....cccc",
        "cccc..............c................c.....cccc",
        "cccc..............ccc..............c...-.cccc",
        "ccccc.............ccc.............rc.....cccc",
        "ccccc..............................c.....cccc",
        "ccccccccccccccccccccccccccccccccccccccccccccc",
        "ccccccccccccccccccccccccccccccccccccccccccccc",
    ],
}


def victory_road(floor):
    """Victory Road, tile for tile after Pokemon Journeys' map (Map335: three floors side by side, 1F, 2F, 3F;
    Jordan, 11-07: exact): rubble walls, ledges and their stairs, sand; in from Route 23 at the bottom of 1F, its
    ladder up at the top left; 2F's boulders and its way out east to Indigo Plateau; 3F (Jordan's picture) with
    its ladders and boulder. (Journeys' map has no warps: the ladders link the floors in order.)"""
    return list(VICTORY_ROAD_FLOORS[floor])


def indigo_plateau():
    """Indigo Plateau's lobby, tile for tile after assets/backgrounds/kanto/indigo_city.png (21 x 21; Jordan,
    11-07: exact): the red carpet up the middle from the way out (south, to Route 23) to the Elite Four's door;
    the waiting areas either side behind gold railings (a TV, plants, red sofas, a vending machine); the nurse's
    counter (left) and the Mart's (right) behind their railings; the stairs in the bottom corners (the right one:
    the ride to Johto, for Champions)."""
    g = Grid(21, 21, "c")
    g.rect(0, 3, 21, 17, ".")
    g.building(9, 0, 3, 3, "E")                # the Elite Four
    g.rect(9, 3, 3, 18, "=")                   # the red carpet
    for x in (1, 4, 7, 13, 16, 19):            # the plants along the back wall
        g.put(x, 3, "z")
    g.rect(0, 4, 9, 1, "i").rect(12, 4, 9, 1, "i").rect(8, 4, 1, 6, "i").rect(12, 4, 1, 6, "i")   # railings
    g.put(3, 6, "m").put(7, 6, "z").put(13, 6, "z").put(14, 6, "m").put(17, 6, "m")   # TVs, plants, vending
    g.rect(0, 8, 5, 2, "y").put(3, 8, "m").rect(16, 8, 5, 2, "y").put(17, 8, "m")       # sofas, their tables
    g.rect(2, 11, 7, 1, "i").rect(12, 11, 9, 1, "i").rect(8, 11, 1, 4, "i").rect(12, 11, 1, 4, "i")
    g.rect(3, 12, 5, 1, "m").rect(13, 12, 7, 1, "m")    # the healing machine; the shelves
    g.rect(3, 14, 2, 1, "m").rect(6, 14, 2, 1, "m").rect(13, 14, 2, 1, "m").rect(16, 14, 3, 1, "m")   # counters
    g.put(5, 14, "N").put(15, 14, "N")         # the nurse; the clerk
    g.rect(0, 14, 2, 4, "c")                   # the stairs down (bottom left)
    g.building(18, 16, 3, 3, "J")              # the stairs down to the ride to Johto
    g.rect(10, 20, 2, 1, "v")                  # out to Route 23
    return g.rows()


CERULEAN_CAVE_FLOORS = {  # (from Pokemon Journeys' map, tile by tile, by its colours; 1F's ladders from its events)
    0: [  # 2F
        "cccccccccccccccccccccccccccccccccccc",
        "cccccccccccccccccccccccccccccccccccc",
        "cccccccccccccccccccccrrrrrrrcccccccc",
        "c....cccc..rr.....r............ccccc",
        "crrr......+r..rrr.r.rrrrrrrrr.+ccccc",
        "c..rrrr.rrrr.rr.r.r.........rrrccccc",
        "c.+...r.........rrrrrrrrrrr....ccccc",
        "crrr.rrrrrrrrrrrr.........rrrr.ccccc",
        "c.r...............rrrrrrr....r.ccccc",
        "r.rrrrrrrrrrrrrrrrr..rr+rrr.rr.ccccc",
        "r.r....r............+r...r...r.rcccc",
        "r.r.rr.r.rrrrr.rrrrrrr.rrrrr.r.rcccc",
        "r.r..r.r.....r.......r.....r.r.rcccc",
        "r.r..r.rrrrr.rrrrrrr.rrrrr.r.r.rcccc",
        "r.r.+r.r.....r.....r.....r.r.r.rcccc",
        "r.rrrr.r.rrrrr.rrr.r.r.r.r.r.r.rcccc",
        "c.r....r.........r.r.r.r.r.r.r.ccccc",
        "c.r.rrrr.rrrrrrrrr.r.r.r.rrr.r.ccccc",
        "c.r....r.....r.....r.r.r.....r.ccccc",
        "c.rrrrrrrrrrrr.rrrrr.r.rrrrrrr.ccccc",
        "c..............r.....r.........ccccc",
        "ccccrrrrrrccccccccccccrrrrrrrccccccc",
        "cccccccccccccccccccccccccccccccccccc",
    ],
    1: [  # 1F
        "cccccccccccccccccccccccccccccccccccccc",
        "ccccccc...rr.ccccccccroooooooooc..rr..",
        "ccccccc...-..cccccccrroooooooooc..-...",
        "crrcccc..rr..coooooooooooooooooc......",
        "cr-cccc..rr..cooooooooooo...ooocc.cccc",
        "cr.c.........cooooooooooc...cooooooooo",
        "c..c....cc...coooo..........cooooooooo",
        "c+.c....cc...coooc..........cooooooooo",
        "c..c....cc...coooc.................ooo",
        "crbc....cc.crroooc...cccccc...r....coo",
        "cc......cooorroooc...cc.rccc..-....coo",
        "cc......cooorrooocc.ccc.-.cc.......coo",
        "cc......coooooooor....c...cc...cccccoo",
        "cc......coooooooor..r.cc.ccc...crr....",
        "cc..rr..coooooooor.........c...c......",
        "cc..r-..coooo....cr......rrc...c.....c",
        "cc......c...c....crrr...rrrc...c...rrc",
        "cc......c...c..................c...ccc",
        "ccccc.ccc...cc.c...............c...ccc",
        "ccccc..........c...............c...ccc",
        "ccccc..........c...............c...ccc",
        "ccccc..........ccccccccccccccccc...ccc",
        "cccccccccccccccccccccccccccccccccvcccc",
    ],
    2: [  # B1F
        "cccccccccccccccccccccccccccccccccccccccc",
        "cc..............cr.....ccccccccccrr....c",
        "cc..............c........ccccccc.......c",
        "cc..............c..cccc.....ccccccc....c",
        "cc......ccccc.ccc..cccc.....ccccccc....c",
        "cc......c..........cccccccc.ccccccc.r..c",
        "cc..r-..cr........rcccccccc............c",
        "cc..rr..crr......rrcccccccc............c",
        "cc......cooooorc................c...cccc",
        "cccccccccooooorc................c...cccc",
        "cooocccccccccccc................c...cccc",
        "cooocccccccccccccc.ccccccc.rcc..c...cccc",
        "coooc.r.r.ccccccrr.......c.rcc..c...cccc",
        "coooc.....cccccccr.......c...N..c...cccc",
        "coooc.....cccccccr.......c......c...cccc",
        "coooccc.cccooooc......c..c.ccr..c...cccc",
        "cooooooooooooooc......c..c.ccr..c...cccc",
        "cooooooooooooooc......c..c......c...cccc",
        "cooooooooooooooc......c..c......c...cccc",
        "cccccoooooooooocc.cc.cc..cccc.ccc...cccc",
        "ccccccoooooooooooor.......ccc.......cccc",
        "ccccccoooooooooooorr.....cccc.......cccc",
        "cccccccccccccccccccccccccccccccccccccccc",
    ],
}


def cerulean_cave(floor):
    """Cerulean Cave, tile for tile after Pokemon Journeys' map (Map194: 1F, 2F, B1F side by side; Jordan,
    11-07: exact): 1F's grassy ledges, its water (Surf) and stone pillar, its ladders, in from Cerulean City at
    the bottom; 2F's maze of boulders, in separate parts, each reached by its own ladder from 1F (ladders pair up
    in reading order); 1F's hole down to B1F's lake and rooms, Mewtwo in the east room. (Journeys' own warps are
    unfinished; this is how FireRed / LeafGreen joins them.)"""
    return list(CERULEAN_CAVE_FLOORS[floor])


POKEMON_TOWER_FLOORS = [  # (from Jordan's assets/backgrounds/kanto/pokemon_tower_1-4.png, 16 px tiles: the floor,
    # the walls, the graves by colour)
    [  # 1F
        'ccccccccccccccccccc',
        'ccccccccccccccccccc',
        'cccccccc....ccccccc',
        'cccccc........ccccc',
        'cccc............ccc',
        'ccc..............cc',
        'cc................c',
        'c.................c',
        'c................cc',
        '.................+c',
        '.................cc',
        '.............mmmmmm',
        '.............mmmmmm',
        'c............mccccc',
        'c...!........mccccc',
        'cc...........mccccc',
        'cccc.........mccccc',
        'ccccccc.....ccccccc',
        'cccccccc.v.cccccccc',
        'ccccccccccccccccccc',
    ],
    [  # 2F
        'ccccccccccccccccccc',
        'ccccccccccccccccccc',
        'cccccccc....ccccccc',
        'cccccrr.......ccccc',
        'cccrrrr.........ccc',
        'ccc..............cc',
        'cc..rrrrrrrrrrrrr.c',
        'c...r.............c',
        'c...r..........r.rr',
        'cc..r...rrr...r..rc',
        'c-..r...rrr...r..+c',
        'cc..r.........r..cc',
        'c...r.........r..rr',
        'c...r...rrrrrrr.rrc',
        'c.................c',
        'ccrrr..........rrcc',
        'ccccr..........cccc',
        'cccccccrrrrrccccccc',
    ],
    [  # 3F
        'ccccccccccccccccccc',
        'ccccccccccccccccccc',
        'cccccccc....ccccccc',
        'cccccc........ccccc',
        'ccccrrrrr..rrrrrccc',
        'ccc.rr.......rrr.cc',
        'cc................c',
        'c.....rrrrr.......c',
        'c..rrr.......rrr.cc',
        'cc.rrr...c...rrr.cc',
        'c-.rrr.......rrrNN+',
        'cc.r.......rr....cc',
        '...r....rrr........',
        'c..rr..........rrrc',
        'c..rr.........r...c',
        'cc..rrrr...rrr...cc',
        'cccc...........cccc',
        'ccccccc.....ccccccc',
    ],
    [  # 4F
        'ccccccccccccccccccc',
        'ccccccccccccccccccc',
        'cccccccrrrrrccccccc',
        'ccccccrc.N.crrccccc',
        'ccccrrrc...crrrrccc',
        'cccrrrr.....rrrrrcc',
        'ccrrrrr..X..rrrrrrc',
        'crrrrrr.....rrrrrrc',
        'crrrrrr.....rrrrrrr',
        'rrrrrrr.....rrrrrrr',
        'rrrrrrr.....rrrrrrr',
        'rrrrrrr.....rrrrrrr',
        'rrrrrrrr..Xrrrrrrrr',
        'crrrrrrr...rrrrrrrc',
        'crrrrrrr...rrrrrrrc',
        'ccrrrrrcc...rrrrrcc',
        'ccccrrrc-...rrrcccc',
        'ccccccccc...ccccccc',
    ],
]

def pokemon_tower(floor):
    """The Pokemon Tower, tile for tile after Jordan's four floors (assets/backgrounds/kanto/pokemon_tower_1-4.png,
    19 tiles across; Jordan, 11-08: exact; its fog, its moods and the Black Fog's ambush kept): 1F in from
    Lavender by the mat, the counter, the stairs up (right); 2F and 3F the graves, the stairs down (left) and
    up (right) (on 3F a ghost stands at the stairs up, reached by one tile only, till the Silph Scope shows
    it's Marowak's spirit); the top floor's graves, its two statues, Team Rocket holding Mr. Fuji."""
    return list(POKEMON_TOWER_FLOORS[floor])


ROCKET_HIDEOUT_FLOORS = [  # (from Pokemon Journeys' map: by colour; B1F, B2F, B3F, B4F)
    [  # B1F
        'cccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccc',
        'cccccccccc^c......+ccccccccc',
        'cccccccccc.c.......ccccccccc',
        'cccccccccc..........cccccccc',
        'cccccccccc..........cccccccc',
        'cccccccccc..........cccccccc',
        'cccccccccc..........cccccccc',
        'c..........................c',
        'c..........................c',
        'ccc..mmmmm.......mmmmm...ccc',
        'ccc..mmmmm.......mmmmm...ccc',
        'ccc..mmmmmm......mmmmm...ccc',
        'c......mmmm.....mmm........c',
        'c......mmmm......mm.mmmmmm.c',
        'c..mmm..mmm.....mmm.mmmmmm.c',
        'cc.ccc..mmm......mm.cccccccc',
        'cc.ccc..mmm.....mmm........c',
        'cccccccccccccccccccc..cccccc',
        'cccccccccccccccccccc..cccccc',
        'cccccccccccccccccccc..cccccc',
        'cccccccccccccccccccc..cccccc',
        'cccc..c.........cccc..cccccc',
        'c...............cccc..cccccc',
        'c...ccccccc...........cccccc',
        'c..ccccccc........cc..cccccc',
        'c...cccccc........cc.......c',
        'c............ccccccc.......c',
        'c............ccccccccccccccc',
        'c..cccccccc..ccccccccccccccc',
        'c...ccccccc.....cccccccccccc',
        'c...cccccc......cccccccccccc',
        'c.................cccccccccc',
        'c.................cccccccccc',
    ],
    [  # B2F
        'ccccccccccccccccccccccc',
        'ccccccccccccccccccccccc',
        'ccccccccccccccccccccccc',
        'ccc.cc.............-ccc',
        'c...................ccc',
        'ccccccccccc..mmmmmm..cc',
        'ccccccccccc..mmmmmm..cc',
        'ccccccccccc..mmmmmm..cc',
        'c............mmmm....cc',
        'ccccc..mmmmm.mm......cc',
        'c............mm..cccccc',
        'cc.m.mmm..mmmmm..cccccc',
        'c.........mmmmm..cccccc',
        'c.mm.m.m..mm.mm..ccc.cc',
        'c.mm.m.......mm......cc',
        'c..........cccccccccccc',
        'c.mm....mm.cccccccccccc',
        'c.......mm...cccccccccc',
        'c.......mm...cccccccccc',
        'cccc.mm.mm...+c..cccccc',
        'c....m..mm....c..cccccc',
        'c.......mm.......cccccc',
        'c.....mmmm.......cccccc',
        'cccc..mmmm.......cccccc',
        'cccc..mmmm.......cccccc',
        'cccc..mmmm.......cccccc',
        'c.c..............cccccc',
        'c................cccccc',
    ],
    [  # B3F
        'ccccccccccccccccccccccccccccccccc',
        'ccccccccccccccccccccccccccccccccc',
        'c.....c.........cccc...+cccc..-cc',
        'c.mmm.c.m.m.m.m..ccc....cccc...cc',
        'c.............cccccc.....ccc....c',
        'ccc..mmmmm.m...............c....c',
        'c.c........m....................c',
        'c.c.mm.m.m.m...mmm..............c',
        'c....m.m.m.m...m................c',
        'cccc........mmmm.cccccccccccccccc',
        'c...........mm...cccccccccccccccc',
        'c.mm.mmm.........cccccccccccccccc',
        'c....mmmmm.......cccc....cccccccc',
        'c.mmm...m........ccc.....cccccccc',
        'c.............mm.ccc.......cccccc',
        'c.mm.m.m.m.....m...........cccccc',
        'c.m....m.mmmmm.m...........cccccc',
        'c..m.m.m.......m..mm............c',
        'c..m.m.m.......m..mm............c',
        'c..m.m.m...mmmmm.cccccccccccccccc',
        'c......mmm.......cccccccccccccccc',
        'c...ccccccccccccccccccccccccccccc',
    ],
    [  # B4F
        'ccccccccccccccccccccccccc',
        'ccccccccccccccccccccccccc',
        'ccc..cccccccccccccc.cc.cc',
        'cc.....ccccccccc.......cc',
        'cccccc.cccccccccccc.cc.cc',
        'ccccc.........ccc.....ccc',
        'c.............ccc.mmmm.cc',
        'c......mm.....ccc.mmm..cc',
        'ccccccccc..............cc',
        'ccccccccc.....cc.......cc',
        'ccccccccc.....cc.......cc',
        'ccc..cccc.....ccc..cccccc',
        'c......cc.....ccc..cccccc',
        'c.mmmm.cc.....ccc..cccccc',
        'c.mmmmm.....-ccc.....cccc',
        'c..mmm.......ccc.....cccc',
        'c...........cccc.......cc',
        'cccccccccccccccc.......cc',
        'cccccccccccccccc..ccccccc',
        'cccccccccccccccc..ccccccc',
        'ccc.cccc..........ccccccc',
        'c.................ccccccc',
        'c....ccccccc......ccccccc',
        'c...ccccccc.......ccccccc',
        'c....cccccc.mm.........cc',
        'c......................cc',
    ],
]

SILPH_FLOORS = [  # (from Pokemon Journeys' map: by colour; 1F, 2F, 3F, 4F, 5F)
    [  # 1F
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccc',
        'ccccccccccccccccccccccccccccccccc+cc',
        'ccccccccccccccccccccccccccccccc...cc',
        'ccccccccccccccccccccccccccccccc.cccc',
        'c....cc.............................',
        'c....ccN............................',
        'c.....c.......................mm...m',
        'c.ccccc......mmm....mmm.......mm.m..',
        'c...........mmmmm..mmmmm......mm.m..',
        'c..........cccccccccccccc..........m',
        'c.........cccccccccccccccc....mm....',
        'ccc..mm...cccccccccccccccc....mm.m..',
        'ccc..mm....cccccccccccccc.....mm.m.m',
        'c...........ccccc..ccccc............',
        'ccc..mm......ccc....ccc.......mm....',
        'ccc..mm.......................mm.m.m',
        'c.............................mm.m..',
        'c...................................',
        'c..................................m',
        'c......................m..m..m..m...',
        'cccccccccvcccccccccccccccccccccccccc',
    ],
    [  # 2F
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccc+c....-ccc',
        'cccccccccccccccccccccccccc.c...c.ccc',
        'cccccccccccccccccccccccccc.....ccccc',
        'c.........Nccc......................',
        'c.m........ccc.m....................',
        'ccccc..cccccccccccccccccccccc..mmmmm',
        'cccccc.ccccccccccccccccccccccc.mmmmm',
        'cccccc.ccccccccccccccccccccccc.mmmmm',
        'cccccc.ccccccccccccccccccccccc.mmmmm',
        'c...................................',
        'c.........................cccccccccc',
        'c.........................cccccccccc',
        'ccccc..ccccccc............cccccccccc',
        'cccccc.cccccccc.mmm..mmm..cc......cc',
        'cccccc.cccccccc.mmmm.mmmm.cc........',
        'cccccc.cccccccc.....................',
        'c..........cccc.mmm..mmm..mm.mmmm..m',
        'c.mmmm.m...cccc.mmmm.mmmm.mm.mmm.m.m',
        'c.mmm......cccc...........mm.mmm...m',
        'c..........cccc...........mm.......m',
    ],
    [  # 3F
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccc-c...+cccc',
        'cccccccccccccccccccccccccc......cccc',
        'c................................c..',
        'c...m...............................',
        'cccccccccccccccccccccc....cccccccccc',
        'ccccccccccccccccccccccc...cccccccccc',
        'ccccccccccccccccccccccc...cccccccccc',
        'ccccccccccccccccccccccc...cccccccccc',
        'c....ccc.ccc...ccc..ccc...ccc.......',
        'c....ccc.ccc...ccc..ccc...ccc...mmm.',
        'c...cccc......cccc.............mmmm.',
        'c.m......ccc........ccc...cc.m..mmm.',
        'ccccccccccccccccccccccc...cccccccccc',
        'ccccccccccccccccccccccc...cccccccccc',
        'ccccccccccccccccccccccc...cccccccccc',
        'ccccccccccccccccccccccc...cccccccccc',
        'c...................................',
        'c..m............................m...',
        'c...................................',
    ],
    [  # 4F
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccccccccccccc',
        'cccccccccccccccccccccccccc+c...-cccc',
        'cccccccccccccccccccccccccc......cccc',
        'ccccc....cc..cccc..ccc..............',
        'cccccccc.cc..cccc..ccc..............',
        'cccccccc.cc.cccccc.ccc..............',
        'cccccccc.cc........ccc..mmmmm..mmmmm',
        'cccccccc.cc.m......ccc..mmmmmm.mmmmm',
        'cccccccc.ccccc..cccccc..mmmmmm.mmmmm',
        'ccc.cccc.cccccc.cccccc..mmmmmm.mmmmm',
        'ccc..ccc.cccccc.cccccc..mmm.........',
        'cc...cc..cccccc.cccccc..mmm..mmm....',
        'c........cc.......cccc..mmm.mmmmm..m',
        'ccc..ccccccccc..cccccc..mmm..mmm....',
        'cccc.cccccccccc.cccccc..mmm.........',
        'cccc.cccccccccc.cccccc..mmm..mmm...m',
        'cccc.cccccccccc.cccccc..mmm.mmmmm...',
        '........................mmm..mmm....',
        '..m.....................mmm........m',
        '........................mmm.........',
    ],
    [  # 5F
        'cccccccccccccccccccc',
        'cccccccccccccccccccc',
        'cccccccccccccccccccc',
        'cccccccc-...cccccccc',
        'cccccccc....cccccccc',
        'ccc.cccc.cccccccc..c',
        'ccc..ccc.ccccccccc.c',
        'ccc..ccc.ccccccccc.c',
        'ccc..ccc.ccccccccc.c',
        'ccc..ccc..ccc......c',
        'ccc..ccc.......ccc.c',
        'ccc..ccc.mmmmm.ccc.c',
        'ccc..ccc.mmmmm.ccc.c',
        'ccc..ccc.mmmmm.ccc.c',
        'ccc..ccc.N.....ccc.c',
        'ccc..ccc.ccccccccc.c',
        'ccc..ccc.ccccccccc.c',
        'ccc..ccc.ccccccccc.c',
        'ccc..ccc.ccccccccc.c',
        'ccc............ccc.c',
        'cccccccccccccccccccc',
    ],
]

def pallet_town():
    """Pallet Town, tile for tile after assets/backgrounds/kanto/pallet_city.png (16 px tiles, grid phase 4,13;
    two tiles of trees each side: 24 x 26, as FireRed / LeafGreen's; Jordan, 11-07: exact): the fence along the
    top, the tall grass up to Route 1 between the rows of trees; your house and your rival's with their
    mailboxes; the flower garden (its fence along the top) and its signs; Professor Oak's lab; the fence and
    sign below it; the pond (Surf south to Route 21) between the bottom fences and trees."""
    g = Grid(24, 26, "T")
    g.rect(2, 6, 20, 20, ".")
    paths = {4: "............dd..........", 5: "............dd..........", 6: "...dddddddddddddddddd...", 7: "..ddddddddddddddddddd...",
             8: "..ddd.....dddd.....dd...", 9: "..d........d........d...", 10: "..d........d........d...",
             11: "..d........d........d...", 12: "..ddd.d...dddd.d...dd...", 13: "..ddddddddddddddddddd...",
             14: "..ddddddddddd.......d...", 15: "..ddd.....dd........d...", 16: "..dd.......d........d...",
             17: "..dd.......d........d...", 18: "..dd.......dd...d...d...", 19: "..ddddddddddddddddddd...",
             20: "..ddddddddddd...d...d...", 21: "..ddddd....dddddddddd...", 22: "...........dddddddddd..."}
    for y, row in paths.items():  # the walking paths (the picture's pale grass), tile by tile
        for x, ch in enumerate(row):
            if ch == "d":
                g.put(x, y, "d")
    g.rect(2, 0, 10, 1, "k").rect(14, 0, 8, 1, "k")   # the top fence
    g.rect(12, 0, 2, 4, G).rect(12, 4, 2, 2, ".").put(12, 0, "^^")   # the tall grass up to Route 1
    g.put(12, 5, "N")                          # Professor Oak (before you have your first Pokemon)
    g.building(5, 8, 5, 4, "P", door_x=1)      # your house
    g.building(14, 8, 5, 4, "R", door_x=1)     # your rival's house
    g.put(4, 11, "!").put(13, 11, "!")         # their mailboxes
    g.rect(5, 15, 4, 1, "k").put(9, 15, "!")   # the garden: its fence, its sign
    g.rect(5, 16, 4, 2, "f").put(5, 18, "!")
    g.building(13, 14, 7, 4, "L", door_x=3)    # Professor Oak's lab
    g.rect(13, 20, 6, 1, "k").put(16, 20, "!")  # the fence below it, its sign
    g.rect(7, 21, 4, 1, "w").rect(7, 22, 4, 4, "~")   # the pond: Surf south to Route 21
    g.put(6, 24, "k").rect(11, 24, 7, 1, "k")  # the bottom fences
    g.rect(2, 23, 4, 3, "T").rect(18, 23, 4, 3, "T").put(6, 25, "T").rect(11, 25, 7, 1, "T")   # (the edge)
    return g.rows()


def route_1():
    """Route 1, tile for tile after Pokemon Journeys' map (Map034: the route is its x 10-29; two tiles of trees
    each side, 24 x 40; Jordan, 11-07: exact). The sand path winds from Viridian (north) down the east side,
    back west along the bottom and into the tall grass to Pallet Town; ledges are fences (their own gaps kept);
    the trees, tall grass and flowers where the original has them; the sign above the bottom grass."""
    g = Grid(24, 40, "T")
    g.rect(2, 2, 20, 35, ".")
    g.rect(2, 0, 8, 2, "T").rect(14, 0, 8, 2, "T")
    sand = [(10, 0, 4, 5), (14, 3, 8, 2), (18, 5, 4, 1), (13, 11, 9, 3), (13, 17, 3, 1), (5, 18, 11, 2),
            (5, 21, 17, 2), (18, 23, 4, 6), (2, 29, 20, 2), (11, 31, 4, 4)]
    for x, y, w, h in sand:  # the sand path
        g.rect(x, y, w, h, "=")
    g.rect(8, 3, 2, 9, "T")                    # the column of trees
    g.rect(10, 6, 12, 5, G).rect(16, 13, 6, 5, G).rect(12, 24, 6, 5, G)   # the tall grass
    g.rect(4, 32, 7, 2, G).rect(2, 34, 7, 2, G).rect(17, 32, 5, 2, G).rect(15, 34, 5, 2, G)
    g.rect(2, 14, 2, 3, "T").rect(10, 14, 6, 3, "T").rect(2, 24, 10, 3, "T")   # trees
    g.rect(2, 5, 5, 1, "#").rect(10, 5, 6, 1, "#").rect(2, 10, 6, 1, "#").rect(4, 15, 6, 1, "#")   # ledges (a gap: x 7)
    g.rect(2, 20, 2, 1, "#").rect(5, 20, 4, 1, "#").rect(11, 20, 11, 1, "#")
    g.rect(2, 31, 2, 1, "#").rect(8, 31, 3, 1, "#").rect(15, 31, 7, 1, "#")
    for x, y in ((3, 7), (6, 8), (4, 9), (3, 12), (6, 13), (4, 23), (4, 28), (9, 34), (10, 35), (20, 34), (21, 35)):
        g.put(x, y, "f")                       # flowers
    g.put(7, 31, "!")
    g.put(4, 2, "N")                           # the Poke Mart clerk
    g.rect(2, 36, 10, 1, "k").rect(14, 36, 8, 1, "k")   # the fence above Pallet
    g.rect(2, 37, 10, 3, "T").rect(14, 37, 8, 3, "T")
    g.rect(12, 34, 2, 6, G).put(12, 39, "vv")  # the tall grass down to Pallet Town
    g.put(10, 0, "^^^^")                       # north to Viridian City
    return g.rows()


def viridian_city():
    """Viridian City, tile for tile after assets/backgrounds/kanto/viridian_city.png (64 x 45, 16 px tiles, grid
    phase 8,3; Jordan, 11-07: exact): gray roads with tan curbs: north to Viridian Forest (the old man asleep
    across the sand path), west through the stairs and the cut in the cliffs to Route 22, a loop round the
    Pokemon Center's yard; the old man's house, a house, the Trainer School, the Gym, the Mart; the fenced tree
    blocks on the left, the pond and its ledge, the lamp posts; south between the lamps to the gate to Route 1."""
    g = Grid(64, 45, "T")
    g.rect(0, 2, 16, 43, "c")                  # the cliffs (west)
    g.rect(2, 26, 8, 3, "=").rect(2, 28, 3, 6, "=").rect(10, 26, 2, 2, "=")   # the sand cut, the stairs
    g.rect(0, 31, 2, 3, "=").rect(0, 31, 1, 3, "<")   # west to Route 22
    g.rect(16, 10, 40, 25, ".")                # the town's lawn
    g.rect(27, 0, 4, 10, ".").rect(27, 0, 4, 4, "T")
    g.rect(31, 0, 4, 6, "=").put(32, 0, "^^").rect(31, 0, 1, 1, "T").rect(34, 0, 1, 1, "T")   # north: sand path
    g.put(32, 2, "N").put(33, 2, "N")          # the old man, asleep across it
    g.rect(31, 5, 4, 20, "=").rect(32, 6, 2, 27, "a")   # the north road and its curbs
    g.rect(12, 25, 20, 4, "=").rect(12, 26, 20, 2, "a")   # the west road
    g.rect(34, 24, 19, 10, "=").rect(34, 25, 18, 2, "a").rect(50, 25, 2, 8, "a").rect(32, 31, 20, 2, "a")   # the loop
    g.rect(43, 27, 6, 3, "f")                  # the flower bed
    # trees and fences
    g.rect(16, 0, 11, 10, "T").rect(16, 10, 11, 1, "k").rect(27, 4, 1, 7, "k")
    g.rect(17, 11, 11, 14, "k").rect(18, 12, 9, 12, "T").put(26, 11, "T")
    g.rect(28, 4, 2, 6, "T").rect(28, 14, 2, 3, "T").rect(28, 19, 2, 5, "T")
    g.rect(35, 4, 2, 6, "T").rect(35, 14, 2, 3, "T").rect(35, 19, 2, 5, "T")
    g.rect(35, 0, 21, 8, "T").rect(56, 0, 8, 45, "T")
    g.rect(42, 15, 5, 2, "T").rect(42, 17, 14, 1, "#")   # trees; the ledge below the Gym's yard
    g.rect(53, 19, 3, 1, "f").rect(53, 20, 3, 14, "T")
    g.rect(16, 28, 8, 2, "T").rect(24, 29, 5, 4, "~").rect(22, 31, 2, 2, "~")   # the pond
    g.rect(16, 32, 6, 1, "#").rect(35, 33, 18, 1, "#")   # ledges
    g.rect(14, 33, 10, 12, "T").rect(24, 35, 16, 10, "T").rect(44, 35, 12, 10, "T")
    g.rect(24, 33, 24, 2, ".").rect(35, 33, 13, 1, "#")   # the lawn below the loop (its ledge east)
    g.rect(40, 35, 3, 6, ".")                  # the walkway south
    g.rect(40, 41, 4, 4, "B").rect(40, 40, 3, 1, "v")   # the gate to Route 1
    g.rect(57, 37, 7, 1, "c").rect(57, 37, 1, 8, "c")   # (a cliff edge in the trees)
    # buildings
    g.building(38, 9, 4, 3, "O", door_x=1)     # the old man's house
    g.building(38, 15, 4, 3, "H", door_x=2)    # a house
    g.building(38, 19, 7, 5, "S", door_x=3)    # the Trainer School
    g.building(46, 11, 6, 4, "G", door_x=2)    # the Gym
    g.building(45, 20, 4, 4, "M", door_x=1)    # the Mart
    g.building(35, 27, 5, 3, "C", door_x=2)    # the Pokemon Center
    for x, y in ((30, 11), (30, 17), (35, 11), (35, 17), (42, 9), (55, 9), (52, 18), (52, 25), (27, 24),
                 (27, 28), (15, 25), (39, 36), (43, 36)):
        g.put(x, y, "l")                       # lamp posts
    g.put(34, 8, "!").put(45, 13, "!").put(42, 24, "!").put(30, 25, "!")
    return g.rows()

MAPS = {
    # Pallet Town (Jordan, 11-07): your house top left, the rival's (Daisy) top right, Oak's Lab bottom right,
    # the fenced flower garden, readable signs, the pond at the bottom the Surf way to Route 21. Oak stands in
    # the gap north to Route 1 until you have a starter; the game opens in front of your house.
    "PALLET_TOWN": {
        "art": pallet_town(),
        "exits": {"^": "KANTO_ROUTE_1", "w": "KANTO_ROUTE_21"},
        "buildings": {"P": "home", "R": "rival", "L": "lab"},
        "roofs": {"P": [214, 72, 64]},
        "people": [{"text": "Professor Oak", "action": "NPC", "target": "professor_oak", "door": "outside",
                    "flag_condition": "not received_starter_kanto"}],
        "signs": [
            ["Your house. Mom says: don't forget to come home and rest!"],
            ["Your rival's house. Daisy is usually home."],
            ["PALLET TOWN", "Every big journey starts with one small step... and one math problem!"],
            ["Practice makes perfect! Two Pidgey plus two Pidgey make four. Keep counting!"],
            ["OAK POKEMON RESEARCH LAB", "Great trainers check their answers twice!"],
        ],
    },
    # Route 1: Pallet (south) to Viridian (north); tall grass, fences with gaps where the ledges were, Headbutt
    # trees, the Poke Mart clerk with a free Potion near Pallet, a sign at each end. No trainers.
    "KANTO_ROUTE_1": {
        "art": route_1(),
        "exits": {"^": "VIRIDIAN_CITY", "v": "PALLET_TOWN"},
        "buildings": {},
        "people": ["POKE MART CLERK"],
        "signs": [
            ["ROUTE 1: PALLET TOWN - VIRIDIAN CITY", "Wild Pokemon hide in the tall grass. Answer fast to catch them!"],
        ],
    },
    # Viridian City (from assets/backgrounds/kanto/viridian_city.png, compacted): the north road to Viridian Forest
    # (the sleeping old man lies across it till you wake him), the west road to Route 22, the south road to
    # Route 1 between lamp posts; the Gym top right (shut till 7 badges; Team Rocket's ambush), a locked
    # two-chimney house, the old man's house, the Trainer School, the Mart, the Center; the pond, the flower
    # paths, the white picket fence round the trees on the left.
    "VIRIDIAN_CITY": {
        "art": viridian_city(),
        "exits": {"^": "VIRIDIAN_FOREST", "<": "KANTO_ROUTE_22", "v": "KANTO_ROUTE_1"},  # (north: the Forest)
        "buildings": {"H": "house", "G": "gym", "O": "oldman", "S": "school", "M": "mart", "C": "center", "B": "gate"},
        "roofs": {"G": [196, 120, 70], "H": [84, 150, 90], "O": [84, 150, 90], "S": [84, 150, 90], "B": [70, 168, 170]},
        "people": ["Wake Sleeping Man", "Wake Sleeping Man"],
        "signs": [
            ["VIRIDIAN CITY", "The Eternally Green Paradise. Keep growing, one problem at a time!"],
            ["VIRIDIAN GYM", "The Gym Leader is away... or so they say."],
            ["TRAINER SCHOOL", "Learn the basics here. Practice makes perfect!"],
            ["ROUTE 22 is to the west.", "The road to the Pokemon League! Keep practicing, Champion-to-be!"],
        ],
    },
    "KANTO_ROUTE_22": {
        "art": route_22(),
        "exits": {">": "VIRIDIAN_CITY", "G": "KANTO_ROUTE_23"},
        "buildings": {"G": "gate"},
        "roofs": {"G": [150, 190, 140]},
        "signs": [["POKEMON LEAGUE - FRONT GATE", "Only trainers with all 8 badges may pass. Keep at it!"]],
    },
    "VIRIDIAN_FOREST": {
        "art": viridian_forest(),
        "exits": {"G": "KANTO_ROUTE_2", "v": "VIRIDIAN_CITY"},
        "buildings": {"G": "gate", "B": "gate"},
        "trainer_spots": ["Rick", "Ember", "Benjamin", "Doug", "Anthony"],
        "signs": [
            ["VIRIDIAN FOREST", "Pewter City is just through the gate. You made it!"],
            ["TRAINER TIPS", "Bug Pokemon fill this forest, and they're weak to Fire. Plan your moves!"],
            ["TRAINER TIPS", "Can't find the way out? Every forest has one. Keep exploring!"],
            ["TRAINER TIPS", "Tall grass hides wild Pokemon. Quick, right answers make catching easier!"],
            ["VIRIDIAN FOREST", "Bug Catchers love a battle here. Keep your math sharp!"],
        ],
    },
    "KANTO_ROUTE_2": {
        "art": route_2(),
        "exits": {"^": "PEWTER_CITY", "v": "VIRIDIAN_FOREST", "Q": "DIGGLETT_CAVE"},
        "buildings": {"Q": "cave", "A": "aide", "G": "gate"},
        "signs": [["DIGGLETT'S CAVE", "A long tunnel dug by Diglett. It comes out near Vermilion City!"]],
    },
    "PEWTER_CITY": {
        "art": pewter_city(),
        "exits": {"v": "KANTO_ROUTE_2", ">": "KANTO_ROUTE_3"},
        "buildings": {"U": "museum", "W": "museum", "G": "gym", "H": "house", "M": "mart", "C": "center", "J": "house"},
        "roofs": {"G": [170, 120, 80]},
        "people": [{"text": "Boy", "action": "EVENT", "door": "outside", "condition": "not:has_boulder_badge",
                    "event": {"lines": ["Boy: Hold it! You want to go east? Beat Brock at the Gym first!",
                                        "He's tough, but you can do it. Try Water or Grass moves!"]}}],
        "signs": [
            ["PEWTER MUSEUM OF SCIENCE", "Fossils, meteorites and more. Science is just math with rocks!"],
            ["PEWTER CITY GYM", "Leader: Brock, the rock-solid Pokemon Trainer!"],
            ["Pewter's flower garden. Count the petals... then count them again!"],
            ["PEWTER CITY", "A stone gray city. Solid work builds solid trainers!"],
        ],
    },
    "KANTO_ROUTE_3": {
        "art": route_3(),
        "exits": {"<": "PEWTER_CITY", "Q": "MT_MOON"},
        "buildings": {"C": "center", "Q": "cave"},
        "trainer_spots": ["Calivin", "Janice", "Sammy", "Otis"],
        "signs": [["ROUTE 3", "Mt. Moon is just north. Rest at the Pokemon Center before you go in!"]],
    },
    "MT_MOON": {
        "theme": "cave",
        "descend": True,
        "buildings": {},
        "figure_floors": {"SUPER NERD": 2, "TAKE DOME FOSSIL": 2, "TAKE HELIX FOSSIL": 2,
                          "Grunt": 2, "Jessie and James": 2},
        "floors": [
            {"art": mt_moon_1f(), "exits": {"v": "KANTO_ROUTE_3"},
             "signs": [["TEAM ROCKET is lurking deep in Mt. Moon. Stay sharp, and keep your math sharper!"]]},
            {"art": mt_moon_b1f(), "exits": {"v": "KANTO_ROUTE_4"}, "parts": True},
            {"art": mt_moon_b2f(), "exits": {}, "parts": True,
             "people": ["SUPER NERD", "TAKE DOME FOSSIL", "TAKE HELIX FOSSIL"]},
        ],
    },
    "KANTO_ROUTE_4": {
        "art": route_4(),
        "exits": {"Q": "MT_MOON", ">": "CERULEAN_CITY"},
        "buildings": {"Q": "cave"},
        "trainer_spots": ["Hope", "Crissy", "Hank"],
        "signs": [["ROUTE 4", "Mt. Moon - Cerulean City. You made it through the mountain!"]],
    },
    "CERULEAN_CITY": {
        "art": cerulean_city(),
        "exits": {"^": "KANTO_ROUTE_24", "<": "KANTO_ROUTE_4", ">": "KANTO_ROUTE_9", "v": "KANTO_ROUTE_5",
                  "Q": "CERULEAN_CAVE"},
        "buildings": {"Q": "cave", "H": "house", "I": "house", "J": "house", "K": "house", "L": "house",
                      "O": "house", "C": "center", "G": "gym", "M": "mart", "B": "bike"},
        "roofs": {"G": [176, 120, 76], "B": [232, 196, 70]},
        "signs": [
            ["NUGGET BRIDGE is just north. Five trainers in a row: are you up for it?"],
            ["A quiet house beside the Gym."],
            ["CERULEAN CITY GYM", "Leader: Misty, the Tomboyish Mermaid!"],
            ["CERULEAN CITY", "A mysterious, blue aura surrounds it. So does a lot of good math!"],
            ["BIKE SHOP", "Bikes for the speedy trainer!"],
        ],
    },
    "KANTO_ROUTE_24": {
        "art": route_24(),
        "exits": {"v": "CERULEAN_CITY", ">": "KANTO_ROUTE_25"},
        "buildings": {},
        # (by the X's in reading order, top down: Shane on the grass, the Rocket at the bridge's north end, then
        # the five on the bridge from the north: you meet Cale first, coming up from Cerulean)
        "trainer_spots": ["Camper Shane", "Team Rocket Grunt", "Camper Ethan", "Lass Reli", "Youngster Timmy",
                          "Lass Ali", "Bug Catcher Cale"],
        "signs": [["NUGGET BRIDGE", "Five trainers in a row! Beat them all for a prize. Count them as you go!"]],
    },
    "KANTO_ROUTE_25": {
        "art": route_25(),
        "exits": {"<": "KANTO_ROUTE_24", "B": "BILLS_HOUSE"},  # (its door: in to Bill's Sea Cottage)
        "buildings": {"B": "bill"},
        "trainer_spots": ["Hiker Franklin", "Hiker Wayne", "Youngster Joey", "Youngster Dan", "Picnicker Kelsey",
                          "Hiker Nob", "Camper Flint", "Youngster Chad", "Lass Haley"],
        "signs": [["SEA COTTAGE", "Bill lives here. He's a Pokemon maniac, and a computer whiz!"]],
    },
    "BILLS_HOUSE": {
        "theme": "ship",
        "art": bills_house(),
        "exits": {"v": "KANTO_ROUTE_25"},
        "buildings": {},
        "people": ["Talk to Bill"],
        "signs": [],
    },
    "KANTO_ROUTE_5": {
        "art": route_5(),
        "exits": {"^": "CERULEAN_CITY", "U": "UNDERGROUND_PATH", "v": "SAFFRON_CITY"},
        "buildings": {"Y": "daycare", "U": "tunnel", "G": "gate"},
        "people": ["GUARD"],
        "signs": [["UNDERGROUND PATH", "Cerulean City - Vermilion City, under Saffron. Down the stairs here!"]],
    },
    "UNDERGROUND_PATH": {
        "art": underground_path(),
        "theme": "tunnel",
        "exits": {"^": "KANTO_ROUTE_5", "v": "KANTO_ROUTE_6", "<": "KANTO_ROUTE_7", ">": "KANTO_ROUTE_8"},
        "buildings": {},
        "parts": True,
        "people": ["Talk to Fossil Maniac"],
        "signs": [
            ["UNDERGROUND PATH", "North: Route 5. South: Route 6. No need to count the steps... but you can!"],
            ["UNDERGROUND PATH", "West: Route 7. East: Route 8. A tunnel under Saffron City."],
        ],
    },
    "KANTO_ROUTE_6": {
        "art": route_6(),
        "exits": {"^": "SAFFRON_CITY", "U": "UNDERGROUND_PATH", "v": "VERMILLION_CITY"},
        "buildings": {"U": "tunnel", "G": "gate"},
        "people": ["GUARD"],
        "trainer_spots": ["Keigo", "Ricky", "Edward"],
        "signs": [["ROUTE 6", "South: Vermilion City, the Port of Exquisite Sunsets!"]],
    },
    "VERMILLION_CITY": {
        "art": vermilion_city(),
        "exits": {"^": "KANTO_ROUTE_6", ">": "KANTO_ROUTE_11"},
        "buildings": {"A": "house", "C": "center", "B": "house", "E": "house", "M": "mart", "F": "fanclub",
                      "I": "house", "V": "gym", "W": "guru", "P": "harbor"},
        "roofs": {"V": [176, 120, 76]},
        "people": [{"text": "Machop", "action": "EVENT", "door": "outside",
                    "event": {"lines": ["Machop: Maaa-chop! (It's stomping the ground flat for a new building.)"]}}],
        "signs": [
            ["VERMILION CITY", "The Port of Exquisite Sunsets. Every problem has an answer, like every port has a ship!"],
            ["POKEMON FAN CLUB", "All Pokemon fans welcome! Come in and share a story."],
            ["VERMILION HARBOR", "Ships to far-off places. Show your ticket at the door!"],
            ["VERMILION CITY GYM", "Leader: Lt. Surge, the Lightning American!"],
        ],
    },
    "KANTO_SS_ANNE": {
        "theme": "ship",
        "buildings": {"A": "cabin0", "B": "cabin1", "C": "cabin2", "E": "cabin3", "F": "cabin4", "G": "cabin5",
                      "K": "captain", "L": "captain"},
        "cabin_trainers": [0, 1, 2, 3, 4, 5],
        "floors": [
            {"art": ss_anne(0), "exits": {"v": "VERMILLION_CITY"},
             "signs": [["S.S. ANNE", "Welcome aboard! The captain's cabin is up on the top deck."]]},
            {"art": ss_anne(1), "exits": {}, "trainer_spots": ["{rival_name}"]},
            {"art": ss_anne(2), "exits": {}},
        ],
    },
    "KANTO_ROUTE_11": {
        "art": route_11(),
        "exits": {"<": "VERMILLION_CITY", "Q": "DIGGLETT_CAVE", "G": "KANTO_ROUTE_12", ">": "KANTO_ROUTE_12"},
        "buildings": {"Q": "cave", "G": "gate"},
        "trainer_spots": ["Hugo", "Dave", "Bernie"],
        "signs": [["DIGLETT'S CAVE", "A long tunnel dug by Diglett. It comes out on Route 2!"]],
    },
    "DIGGLETT_CAVE": {
        "art": digletts_cave(),
        "theme": "cave",
        "exits": {"<": "KANTO_ROUTE_2", ">": "KANTO_ROUTE_11"},
        "buildings": {},
    },
    "KANTO_ROUTE_9": {
        "art": route_9(),
        "exits": {"<": "CERULEAN_CITY", ">": "KANTO_ROUTE_10"},
        "buildings": {},
        "trainer_spots": ["Jeremy", "Conner", "Chris"],
        "signs": [["ROUTE 9", "East to Rock Tunnel. Bring Flash, or you'll be counting steps in the dark!"]],
    },
    "KANTO_ROUTE_10": {
        "art": route_10(),
        "exits": {"<": "KANTO_ROUTE_9", "Q": "ROCK_TUNNEL", "P": "POWER_PLANT"},
        "buildings": {"C": "center", "Q": "cave", "P": "plant"},
        "trainer_spots": ["Mark", "Clark", "Heidi"],
        "signs": [
            ["ROCK TUNNEL", "A dark cave! Flash lights the way. Rest at the Pokemon Center first."],
            ["POWER PLANT", "Kanto's power, made right here. Something's wrong with the generator..."],
        ],
    },
    "KANTO_ROUTE_10_SOUTH": {
        "art": route_10_south(),
        "exits": {"Q": "ROCK_TUNNEL", "v": "LAVENDER_TOWN"},
        "buildings": {"Q": "cave", "L": "house"},
        "signs": [["ROUTE 10", "Lavender Town is just south. You made it through the dark!"]],
    },
    "ROCK_TUNNEL": {
        "theme": "cave",
        "dark": True,
        "buildings": {},
        "floor_names": ["1F", "B1F"],
        "floors": [
            {"art": rock_tunnel(0), "exits": {"^": "KANTO_ROUTE_10", "v": "KANTO_ROUTE_10_SOUTH"}, "parts": True,
             "ladders": [1, 3, 2, 0],
             "signs": [["ROCK TUNNEL", "It's pitch black in here! Flash would light it up."],
                       ["Daylight ahead! Lavender Town is south on Route 10."]]},
            {"art": rock_tunnel(1), "exits": {}, "parts": True},
        ],
    },
    "LAVENDER_TOWN": {
        "art": lavender_town(),
        "exits": {"^": "KANTO_ROUTE_10_SOUTH", "<": "KANTO_ROUTE_8", "v": "KANTO_ROUTE_12"},
        "buildings": {"R": "radio", "P": "ptower", "A": "house", "B": "house", "F": "fuji", "M": "mart", "C": "center"},
        "locked": {"radio": "The Radio Tower is dark. The power's out!"},
        "roofs": {"R": [60, 110, 80], "P": [150, 170, 150], "A": [140, 90, 170], "B": [140, 90, 170], "F": [214, 170, 60]},
        "signs": [
            ["LAVENDER TOWN", "The Noble Purple Town. Even quiet places hold big answers!"],
            ["POKEMON TOWER", "A resting place for Pokemon. Please be respectful."],
            ["LAVENDER RADIO TOWER", "Off the air! The power's out..."],
            ["A quiet purple house. Lavender's homes are all this color."],
            ["Lavender's garden. Count the petals, then count them again!"],
        ],
    },
    "KANTO_POKEMON_TOWER": {
        "theme": "tower",
        "fog": True,
        "buildings": {},
        "floors": [
            {"art": pokemon_tower(0), "exits": {"v": "LAVENDER_TOWN"},
             "signs": [["POKEMON TOWER", "Here rest the Pokemon who have passed on. Please be quiet."]]},
            {"art": pokemon_tower(1), "exits": {}},
            {"art": pokemon_tower(2), "exits": {}, "people": ["GHOST", "CONFRONT GHOST"]},
            {"art": pokemon_tower(3), "exits": {}, "people": ["MR. FUJI"], "trainer_spots": ["Jessie and James", "Grunt"]},
        ],
    },
    "ROCKET_HIDEOUT": {
        "theme": "ship",
        "descend": True,
        "buildings": {},
        "floor_names": ["B1F", "B2F", "B3F", "B4F"],
        "figure_floors": {"GIOVANNI": 3, "SILPH SCOPE": 3},
        "floors": [
            {"art": ROCKET_HIDEOUT_FLOORS[0], "exits": {"^": "CELADON_CITY"}},
            {"art": ROCKET_HIDEOUT_FLOORS[1], "exits": {}},
            {"art": ROCKET_HIDEOUT_FLOORS[2], "exits": {}},
            {"art": ROCKET_HIDEOUT_FLOORS[3], "exits": {}},
        ],
    },
    "SILPH_CITY": {
        "theme": "ship",
        "buildings": {},
        "floor_names": ["1F", "2F", "3F", "4F", "5F"],
        "floors": [
            {"art": SILPH_FLOORS[0], "exits": {"v": "SAFFRON_CITY"}, "people": ["NURSE"]},
            {"art": SILPH_FLOORS[1], "exits": {}, "people": ["TALK TO EMPLOYEE"]},
            {"art": SILPH_FLOORS[2], "exits": {}},
            {"art": SILPH_FLOORS[3], "exits": {}},
            {"art": SILPH_FLOORS[4], "exits": {}, "people": ["VISIT THE PRESIDENT"]},
        ],
    },
    "KANTO_ROUTE_8": {
        "art": route_8(),
        "exits": {">": "LAVENDER_TOWN", "G": "SAFFRON_CITY", "U": "UNDERGROUND_PATH"},
        "buildings": {"U": "tunnel", "G": "gate"},
        "people": ["GUARD"],
        "trainer_spots": ["Richie", "Aidan", "Julia"],
        "signs": [["ROUTE 8", "West: the Underground Path goes under Saffron to Route 7 and Celadon City."]],
    },
    "KANTO_ROUTE_7": {
        "art": route_7(),
        "exits": {"<": "CELADON_CITY", "G": "SAFFRON_CITY", "U": "UNDERGROUND_PATH"},
        "buildings": {"U": "tunnel", "G": "gate"},
        "people": ["GUARD"],
        "trainer_spots": ["Alpesh", "Kelly", "Nancy"],
        "signs": [["UNDERGROUND PATH", "Celadon City - Lavender Town, under Saffron. Down the stairs here!"]],
    },
    "CELADON_CITY": {
        "art": celadon_city(),
        "exits": {">": "KANTO_ROUTE_7", "<": "KANTO_ROUTE_16"},
        "buildings": {"S": "dept", "H": "house", "Y": "mansion", "I": "house", "J": "house", "C": "center",
                      "K": "house", "Q": "game corner", "P": "game corner", "L": "house", "M": "house",
                      "Z": "gym", "O": "house", "R": "hotel", "U": "house", "V": "house", "A": "house", "B": "house",
                      "W": "house", "E": "house"},
        "roofs": {"S": [80, 150, 220], "Y": [214, 204, 180], "Q": [120, 70, 170], "P": [120, 70, 170],
                  "Z": [176, 120, 76], "R": [232, 130, 60]},
        "locked": {"hotel": "Celadon Hotel: Sorry, we're all booked up tonight!"},
        "signs": [
            ["CELADON CONDOMINIUMS", "Quiet homes, right in the city."],
            ["CELADON DEPT. STORE", "Everything a trainer needs, on every floor!"],
            ["CELADON CITY", "The City of Rainbow Dreams. Dream big, and count every step!"],
            ["GAME CORNER", "The playground for grown-ups... and math whizzes!"],
            ["CELADON HOTEL", "Just past the pond. Route 16 is west, Cycling Road that way too!"],
            ["CELADON CITY GYM", "Leader: Erika, the Nature-Loving Princess!"],
        ],
    },
    "KANTO_ROUTE_12": {
        "art": route_12(),
        "exits": {"^": "LAVENDER_TOWN", "<": "KANTO_ROUTE_11", "v": "KANTO_ROUTE_13"},
        "buildings": {"G": "gate", "J": "gate", "H": "house"},
        "trainer_spots": ["Ernest", "Grace", "Edwin"],
        "signs": [["ROUTE 12", "North: Lavender Town. The lane to Route 11 is further south."],
                  ["A huge Pokemon is sleeping on the road! A gentle tune might wake it..."]],
    },
    "KANTO_ROUTE_13": {
        "art": route_13(),
        "exits": {"^": "KANTO_ROUTE_12", "<": "KANTO_ROUTE_14"},
        "buildings": {},
        "trainer_spots": ["Sebastian", "Alma", "Jared"],
        "signs": [["ROUTE 13", "Trainers, watch your step... and your sums!"],
                  ["Look to the left: there's always another way through the fences."]],
    },
    "KANTO_ROUTE_14": {
        "art": route_14(),
        "exits": {">": "KANTO_ROUTE_13", "<": "KANTO_ROUTE_15"},
        "buildings": {},
        "trainer_spots": ["Mitch", "Malik", "Carter"],
        "signs": [["ROUTE 14", "South to Route 15, then west to Fuchsia City."]],
    },
    "KANTO_ROUTE_15": {
        "art": route_15(),
        "exits": {">": "KANTO_ROUTE_14", "<": "FUCHSIA_CITY"},
        "buildings": {"Y": "gate", "V": "gate"},
        "signs": [["ROUTE 15", "West: Fuchsia City, home of the Safari Zone!"]],
        "trainer_spots": ["Hideo", "Koji", "Luke"],
    },
    "KANTO_ROUTE_16": {
        "art": route_16(),
        "exits": {">": "CELADON_CITY", "v": "KANTO_ROUTE_17"},
        "buildings": {"G": "gate", "H": "gate", "F": "flyhouse"},
        "signs": [["CYCLING ROAD", "Bicycles only! It's a long, fast ride down to Route 18."], ["ROUTE 16", "East: Celadon City. West: a quiet house, for those who look."]],
        "trainer_spots": ["Wilton", "Charles", "Ramiro"],
    },
    "KANTO_ROUTE_17": {
        "art": route_17(),
        "exits": {"^": "KANTO_ROUTE_16", "v": "KANTO_ROUTE_18"},
        "buildings": {},
        "signs": [["CYCLING ROAD", "Keep your speed steady, like counting by fives: 5, 10, 15, 20!"]],
        "trainer_spots": ["Nikolas", "Zeek", "Jaxon"],
    },
    "KANTO_ROUTE_18": {
        "art": route_18(),
        "exits": {"^": "KANTO_ROUTE_17", ">": "FUCHSIA_CITY"},
        "buildings": {"G": "gate", "H": "gate"},
        "signs": [["ROUTE 18", "East: Fuchsia City. North: Cycling Road (bike riders only)."]],
        "trainer_spots": ["Luke", "Dana", "Arnie"],
    },
    "FUCHSIA_CITY": {
        "art": fuchsia_city(),
        "exits": {"Z": "SAFARI_ZONE", "<": "KANTO_ROUTE_18", ">": "KANTO_ROUTE_15", "v": "KANTO_ROUTE_19"},
        "buildings": {"Z": "safari", "M": "mart", "G": "gym", "W": "warden", "H": "house", "C": "center",
                      "B": "brother", "P": "brother", "Y": "gate", "V": "gate"},
        "roofs": {"Z": [232, 130, 50], "G": [176, 120, 76], "W": [200, 60, 50], "H": [226, 140, 160],
                  "B": [226, 214, 170], "P": [226, 140, 160]},
        "signs": [
            ["SAFARI ZONE", "Catch rare Pokemon in the wild! Gardens out front, adventure inside."],
            ["FUCHSIA CITY", "Behold! It's passion pink! Keep your sums just as bright."],
            ["Behind this house is a pond. The Fishing Guru's brother lives here!"],
            ["FUCHSIA CITY GYM", "Leader: Koga, the Poisonous Ninja Master!"],
        ],
    },
    "SAFARI_ZONE": {
        "art": safari_zone(),
        "exits": {"v": "FUCHSIA_CITY"},
        "buildings": {"A": "house", "B": "house", "E": "house", "H": "house"},
        "zone_rects": [[53, 50, 44, 40], [97, 35, 68, 45], [25, 0, 60, 42], [0, 42, 53, 40]],
        "people": ["GOLD TEETH"],
        "locked": {"house": "A rest house. Nobody's resting right now."},
        "signs": [["NORTH AREA", "Rest here if your feet are tired!"], ["This way: the North Area's far side."],
                  ["EAST AREA", "Watch for the steps up the plateaus."], ["WEST AREA", "Someone dropped something around here..."],
                  ["The path bends on. Keep counting your steps!"], ["CENTER AREA", "A rest house. Catch your breath."],
                  ["SAFARI ZONE", "Four areas: Center, East, North and West. Each has its own Pokemon!"]],
    },
    "KANTO_ROUTE_19": {
        "art": route_19(),
        "exits": {"^": "FUCHSIA_CITY", "w": "KANTO_ROUTE_20"},
        "buildings": {},
        "signs": [["ROUTE 19", "Sea route to Seafoam Islands and Cinnabar Island. Surf safely!"]],
        "trainer_spots": ["Jerome", "Ronald", "Lil"],
    },
    "KANTO_ROUTE_20": {
        "art": route_20(),
        "exits": {"w": "KANTO_ROUTE_19", "u": "CINNABAR_ISLAND", "Q": "SEAFOAM_ISLANDS", "P": "SEAFOAM_ISLANDS"},
        "buildings": {"Q": "cave", "P": "cave"},
        "signs": [["SEAFOAM ISLANDS", "Two islands, one icy cave. Something cold lives deep inside..."]],
        "trainer_spots": ["Richard", "Alice", "Connie"],
    },
    "KANTO_ROUTE_21": {
        "art": route_21(),
        "exits": {"w": "PALLET_TOWN", "u": "CINNABAR_ISLAND"},
        "buildings": {},
        "signs": [["ROUTE 21", "North: Pallet Town. South: Cinnabar Island. It's a long swim!"]],
        "trainer_spots": ["Tucker", "Lola", "Irene"],
    },
    "SEAFOAM_ISLANDS": {
        "theme": "ice",
        "descend": True,
        "buildings": {},
        "floors": [
            {"art": seafoam(0), "exits": {"<": "KANTO_ROUTE_20", ">": "KANTO_ROUTE_20"}, "parts": True,
             "signs": [["Boulders block the way down. Strength, and a sharp mind, can move them!"]]},
            {"art": seafoam(1), "exits": {}, "parts": True},
            {"art": seafoam(2), "exits": {}, "parts": True, "ladders": [0, 2, 1]},
            {"art": seafoam(3), "exits": {}, "parts": True},
            {"art": seafoam(4), "exits": {}, "parts": True, "people": ["CHALLENGE ARTICUNO"],
             "signs": [["The water runs fast here. Surf with care!"], ["Something very cold is close by..."]]},
        ],
    },
    "CINNABAR_ISLAND": {
        "art": cinnabar_island(),
        "exits": {"w": "KANTO_ROUTE_21", "u": "KANTO_ROUTE_20", "V": "CINNABAR_VOLCANO"},
        "buildings": {"Y": "mansion", "V": "cave", "G": "gym", "L": "fossil", "C": "center", "M": "mart", "H": "harbor"},
        "roofs": {"Y": [150, 92, 70], "G": [214, 176, 70], "L": [226, 220, 196]},
        "signs": [
            ["POKEMON MANSION", "An old mansion. Nobody has lived here for years..."],
            ["CINNABAR ISLAND GYM", "Leader: Blaine, the Hotheaded Quiz Master!"],
            ["POKEMON LAB", "Fossils brought back to life here!"],
        ],
    },
    "SAFFRON_CITY": {
        "art": saffron_city(),
        "exits": {"A": "KANTO_ROUTE_5", "v": "KANTO_ROUTE_6", "<": "KANTO_ROUTE_7", ">": "KANTO_ROUTE_8",
                  "Y": "SILPH_CITY"},
        "buildings": {"A": "gate", "B": "gate", "E": "gate", "F": "gate", "S": "station", "O": "dojo", "G": "gym",
                      "H": "copycat", "Y": "silph", "M": "mart", "C": "center", "\u0391": "house", "\u0392": "house", "\u0393": "house", "\u0394": "house", "\u0395": "house", "\u0396": "house", "\u0397": "house", "\u0398": "house", "\u0399": "house", "\u039a": "house", "\u039b": "house", "\u039c": "house", "\u039d": "house", "\u039e": "house", "\u039f": "house", "\u03a0": "house", "\u03a1": "house", "\u03a3": "house", "\u03a4": "house", "\u03a5": "house", "\u03a6": "house", "\u03a7": "house", "\u03a8": "house", "\u03a9": "house", "\u0411": "house", "\u0413": "house", "\u0414": "house", "\u0416": "house", "\u0417": "house", "\u0418": "house", "\u041b": "house", "\u041f": "house", "\u0424": "house"},
        "roofs": {"S": [170, 200, 210], "O": [176, 120, 76], "G": [150, 90, 190], "H": [190, 120, 200],
                  "Y": [120, 170, 210], "\u0391": [214, 204, 120], "\u0392": [214, 204, 120], "\u0393": [214, 204, 120], "\u0394": [96, 170, 96], "\u0395": [96, 170, 96], "\u0396": [96, 170, 96], "\u0397": [96, 170, 96], "\u0398": [96, 170, 96], "\u0399": [96, 170, 96], "\u039a": [214, 204, 120], "\u039b": [214, 204, 120], "\u039c": [214, 204, 120], "\u039d": [214, 204, 120], "\u039e": [214, 204, 120], "\u039f": [214, 204, 120], "\u03a0": [96, 170, 96], "\u03a1": [96, 170, 96], "\u03a3": [96, 170, 96], "\u03a4": [96, 170, 96], "\u03a5": [96, 170, 96], "\u03a6": [96, 170, 96], "\u03a7": [176, 120, 76], "\u03a8": [96, 170, 96], "\u03a9": [96, 170, 96], "\u0411": [96, 170, 96], "\u0413": [96, 170, 96], "\u0414": [96, 170, 96], "\u0416": [96, 170, 96], "\u0417": [96, 170, 96], "\u0418": [96, 170, 96], "\u041b": [96, 170, 96], "\u041f": [96, 170, 96], "\u0424": [96, 170, 96]},
        "signs": [
            ["FIGHTING DOJO", "Masters of fighting moves train here. Think fast, hit hard!"],
            ["SAFFRON CITY GYM", "Leader: Sabrina, the Master of Psychic Pokemon!"],
            ["MAGNET TRAIN STATION", "The fastest way to Goldenrod City in Johto!"],
            ["SILPH CO.", "Home of the Silph Scope, Poke Balls... and many good ideas!"],
            ["SAFFRON CITY", "Shining, golden land of commerce. Where every number counts!"],
        ],
    },
    "POWER_PLANT": {
        "theme": "tunnel",
        "art": power_plant(),
        "exits": {"v": "KANTO_ROUTE_10"},
        "buildings": {},
        "people": ["CHALLENGE ZAPDOS", "TALK TO THE MANAGER", "RETURN THE MACHINE PART"],
        "signs": [["POWER PLANT", "Danger! High voltage! Electric Pokemon have moved in."]],
    },
    "KANTO_ROUTE_23": {
        "art": route_23(),
        "exits": {"v": "KANTO_ROUTE_22", "^": "VICTORY_ROAD"},
        "buildings": {"B": "gate"},
        "people": ["EARTH BADGE GUARD", "VOLCANO BADGE GUARD", "MARSH BADGE GUARD", "SOUL BADGE GUARD",
                   "RAINBOW BADGE GUARD", "THUNDER BADGE GUARD", "CASCADE BADGE GUARD", "BOULDER BADGE GUARD"],
        "signs": [["VICTORY ROAD", "The last test before the Pokemon League."],
                  ["ROUTE 23", "The path beside the hill is quieter. Mind the rocks!"],
                  ["ROUTE 23", "Victory Road is ahead. Only trainers with all eight badges may pass!"]],
    },
    "VICTORY_ROAD": {
        "theme": "cave",
        "descend": True,
        "floor_names": ["1F", "2F", "3F"],
        "buildings": {},
        "floors": [
            {"art": victory_road(0), "exits": {"v": "KANTO_ROUTE_23"}},
            {"art": victory_road(1), "exits": {">": "INDIGO_PLATEAU"}},
            {"art": victory_road(2), "exits": {}},
        ],
    },
    "INDIGO_PLATEAU": {
        "theme": "ship",
        "art": indigo_plateau(),
        "exits": {"v": "KANTO_ROUTE_23"},
        "buildings": {"E": "league", "J": "johto"},
        "roofs": {"E": [200, 60, 60], "J": [200, 200, 210]},
        "people": ["Heal", "Shop"],
        "locked": {"johto": "The ride to Johto is for Champions only. Beat the Elite Four first!"},
        "signs": [],
    },
    "CERULEAN_CAVE": {
        "theme": "cave",
        "descend": True,
        "floor_names": ["2F", "1F", "B1F"],
        "buildings": {},
        "floors": [
            {"art": cerulean_cave(0), "exits": {}, "parts": True},   # (2F: separate parts, a ladder each)
            {"art": cerulean_cave(1), "exits": {"v": "CERULEAN_CITY"}},
            {"art": cerulean_cave(2), "exits": {}, "people": ["CHALLENGE MEWTWO"]},
        ],
    },
}
