"""The Sinnoh Battle Frontier's gate and facility rooms on Platinum's own rooms (written by kanto_handoff/
sinnoh_map_tools/s_s8_frontier_rooms.py from the game file, 11-25): walk grid, doors, attendant and townsfolk."""
ROOMS = {
 "sgate": {
  "zone": "D32R0101",
  "art": [
   "ccccccccccccccc",
   "ccccccccccccccc",
   "ccccccvvvcccccc",
   "c.c........Nc.c",
   "c..N..........c",
   "c.............c",
   "c...N......N..c",
   "c.............c",
   "cccc.......cccc",
   "cccc.c...c.cccc",
   "cccc.......cccc",
   "cccc.......cccc",
   "ccccccc.ccccccc",
   "cccc.Nm.ccccccc",
   "ccccc.c.ccccccc",
   "ccccccc.ccccccc",
   "ccccccc.ccccccc",
   "ccccccc.ccccccc",
   "ccccccc.ccccccc",
   "cccc.......cccc",
   "cccc..nnn..cccc",
   "ccccccccccccccc"
  ],
  "people": [
   {
    "text": "Hopeful trainer",
    "action": "EVENT",
    "event": {
     "lines": [
      "My dream is to battle Palmer in the Tower. I'm not strong enough yet!"
     ]
    }
   },
   {
    "text": "Excited explorer",
    "action": "EVENT",
    "event": {
     "lines": [
      "The Battle Frontier's just ahead! What kind of Trainers will I meet?"
     ]
    }
   },
   {
    "text": "Recorder fan",
    "action": "EVENT",
    "event": {
     "lines": [
      "The Vs. Recorder is so handy! It shows how many Battle Points you have."
     ]
    }
   },
   {
    "text": "Acronym man",
    "action": "EVENT",
    "event": {
     "lines": [
      "Tower, Hall, Castle, Factory, Arcade... How do you make a word out of that?"
     ]
    }
   },
   "Gate attendant"
  ]
 },
 "sfactory": {
  "zone": "D32R0301",
  "art": [
   "ccccccccccccccccccccccccccc",
   "ccccccccccccccccccccccccccc",
   "ccccccccccccccccccccccccccc",
   "c..............cc..c.....cc",
   "c..................c.....cc",
   "c...............N..c.....cc",
   "cv.cc..cc..cc......ccNc.ccc",
   "cv........................c",
   "cv.cc..cc..cc.............c",
   "c.................N......Nc",
   "c.........................c",
   "cN....................N...c",
   "cN.............N..........c",
   "ccccccccccccccccccccccccccc"
  ],
  "people": [
   {
    "text": "Factory boy",
    "action": "EVENT",
    "event": {
     "lines": [
      "I always pick Pokemon I've never raised before. You learn so much that way."
     ]
    }
   },
   "Factory attendant",
   {
    "text": "Factory clown",
    "action": "EVENT",
    "event": {
     "lines": [
      "Do you raise every kind of Pokemon? No? Here you get to try them all!"
     ]
    }
   },
   {
    "text": "Factory officer",
    "action": "EVENT",
    "event": {
     "lines": [
      "I hated battling some Pokemon. Then I got them on my side and they won me over!"
     ]
    }
   },
   {
    "text": "Helpful woman",
    "action": "EVENT",
    "event": {
     "lines": [
      "The staff here tell you about the next Trainer you'll face. So helpful!"
     ]
    }
   },
   {
    "text": "Torn lady",
    "action": "EVENT",
    "event": {
     "lines": [
      "The Pokemon I rented became my favourites! But I already have six favourites!"
     ]
    }
   },
   {
    "text": "Factory sailor",
    "action": "EVENT",
    "event": {
     "lines": [
      "My trick? Look at the other side's team, then choose. Simple!"
     ]
    }
   },
   {
    "text": "Factory woman",
    "action": "EVENT",
    "event": {
     "lines": [
      "Remember what moves your opponent used. Then you know what to trade for."
     ]
    }
   }
  ]
 },
 "shall": {
  "zone": "D32R0401",
  "art": [
   "ccccccccccccccccccccccccccc",
   "ccccccccccccccccccccccccccc",
   "ccccccccccccccccccccccccccc",
   "c...cc.cccN...ccc..ccc....c",
   "c...................N....Nc",
   "c.N............N..........c",
   "c.....N........N..........c",
   "c..N......................c",
   "cccccccc.................vc",
   "c.....N..................vc",
   "c........................vc",
   "c.....c................N..c",
   "c.....c...................c",
   "ccccccccccccccccccccccccccc"
  ],
  "people": [
   {
    "text": "Record keeper",
    "action": "EVENT",
    "event": {
     "lines": [
      "Try the Hall with lots of different Pokemon. It all adds to your record."
     ]
    }
   },
   {
    "text": "Stage girl",
    "action": "EVENT",
    "event": {
     "lines": [
      "Any Pokemon can stand on that stage. Even your one favourite!"
     ]
    }
   },
   {
    "text": "Streak racer",
    "action": "EVENT",
    "event": {
     "lines": [
      "My friend and I race to see who gets the longest streak. Same rules for both!"
     ]
    }
   },
   {
    "text": "Mysterious maid",
    "action": "EVENT",
    "event": {
     "lines": [
      "Ohoho! I'm the mysterious maid! My advice: a type matchup can change everything here!"
     ]
    }
   },
   {
    "text": "Pachirisu girl",
    "action": "EVENT",
    "event": {
     "lines": [
      "My Pachirisu has even battled the Brain here! The Brain matches your level."
     ]
    }
   },
   {
    "text": "Hall idol",
    "action": "EVENT",
    "event": {
     "lines": [
      "You can bring the same kind of Pokemon if it's a different one. Mix up its moves!"
     ]
    }
   },
   {
    "text": "Hall Pachirisu",
    "action": "EVENT",
    "event": {
     "lines": [
      "PACHIRISU: Pachi pachi!"
     ]
    }
   },
   {
    "text": "Type thinker",
    "action": "EVENT",
    "event": {
     "lines": [
      "Croagunk is Poison and Fighting, so it can come up as either kind."
     ]
    }
   },
   "Hall attendant",
   {
    "text": "Hall hiker",
    "action": "EVENT",
    "event": {
     "lines": [
      "I start with the types my Pokemon dislikes. Get the tough ones out of the way!"
     ]
    }
   }
  ]
 },
 "scastle": {
  "zone": "D32R0501",
  "art": [
   "ccccccccccccccccccccccc",
   "ccccccccccccccccccccccc",
   "ccccccccccccccccccccccc",
   "cccccccc.cc..cc.......c",
   "cccccccc....Nc........c",
   "cccccccc.....cNc....N.c",
   "cccccccc.....cccc.....c",
   "cccccccc.N............c",
   "cccccccc.............vc",
   "ccc..N...............vc",
   "c....................vc",
   "cccccc................c",
   "c.......N....cccc.....c",
   "c............cNc......c",
   "c.N.c....c...c........c",
   "c............cc.......c",
   "ccccccccccccccccccccccc"
  ],
  "people": [
   {
    "text": "Scout",
    "action": "EVENT",
    "event": {
     "lines": [
      "Always check the other side's team before a battle. Don't be stingy with your points!"
     ]
    }
   },
   {
    "text": "Castle lady",
    "action": "EVENT",
    "event": {
     "lines": [
      "Stronger opponents give more points. If you win, of course."
     ]
    }
   },
   {
    "text": "Castle artist",
    "action": "EVENT",
    "event": {
     "lines": [
      "Win without taking a hit and you earn more points."
     ]
    }
   },
   {
    "text": "Dreamy waitress",
    "action": "EVENT",
    "event": {
     "lines": [
      "The castle's master... so elegant... Sigh..."
     ]
    }
   },
   "Castle attendant",
   {
    "text": "Serious gentleman",
    "action": "EVENT",
    "event": {
     "lines": [
      "Listen closely: lose, and your Castle Points are gone. All of them."
     ]
    }
   },
   {
    "text": "Point saver",
    "action": "EVENT",
    "event": {
     "lines": [
      "At first Castle Points only heal. Rank up, and you can restore PP too."
     ]
    }
   },
   {
    "text": "Castle dreamer",
    "action": "EVENT",
    "event": {
     "lines": [
      "Every man dreams of living in a castle! Right?"
     ]
    }
   }
  ]
 },
 "sarcade": {
  "zone": "D32R0601",
  "art": [
   "ccccccccccccccccccccccc",
   "ccccccccccccccccccccccc",
   "ccccccccccccccc.ccccccc",
   "c...........Nc...c.cc.c",
   "c............c..cc....c",
   "cv...........cN.cc....c",
   "cv.................N..c",
   "cv....................c",
   "c............N.......cc",
   "c............N....cN.cc",
   "ccccccccccccccc.......c",
   "cc.....N..........c..cc",
   "c.Nc..................c",
   "c.......ccccccccccccccc",
   "c.NcN................Nc",
   "cc....................c",
   "ccccccccccccccccccccccc"
  ],
  "people": [
   {
    "text": "Board worker",
    "action": "EVENT",
    "event": {
     "lines": [
      "Whoever rules the game board rules the Arcade. Sounds deep, but it's obvious!"
     ]
    }
   },
   "Arcade attendant",
   {
    "text": "Unlucky lady",
    "action": "EVENT",
    "event": {
     "lines": [
      "It all came down to luck... and my Pokemon got frozen."
     ]
    }
   },
   {
    "text": "Clever hiker",
    "action": "EVENT",
    "event": {
     "lines": [
      "A Pokemon whose type or ability blocks a status can shrug off that square."
     ]
    }
   },
   {
    "text": "Ground hiker",
    "action": "EVENT",
    "event": {
     "lines": [
      "If the board picks paralysis, Ground types don't mind one bit."
     ]
    }
   },
   {
    "text": "Luck believer",
    "action": "EVENT",
    "event": {
     "lines": [
      "You can't do anything about luck. It's there or it isn't."
     ]
    }
   },
   {
    "text": "Board timer",
    "action": "EVENT",
    "event": {
     "lines": [
      "If you don't stop the board in time, it stops by itself."
     ]
    }
   },
   {
    "text": "Arcade waitress",
    "action": "EVENT",
    "event": {
     "lines": [
      "The Brain here has quite a style. A little bump, a wiggle... please don't stare."
     ]
    }
   },
   {
    "text": "Worried camper",
    "action": "EVENT",
    "event": {
     "lines": [
      "A battle can start with Trick Room already up? Speed won't save you then!"
     ]
    }
   },
   {
    "text": "Thrill seeker",
    "action": "EVENT",
    "event": {
     "lines": [
      "Leave it to fate! That's how you enjoy the Arcade!"
     ]
    }
   },
   {
    "text": "Sporting girl",
    "action": "EVENT",
    "event": {
     "lines": [
      "Don't blame the board when you lose. Win more, and it gives you better picks."
     ]
    }
   }
  ]
 }
}
FIGURES = {"Hall Pachirisu": {"pokemon": 417}}
