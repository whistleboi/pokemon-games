p = 'build.py'
s = open(p, encoding='utf-8').read()
def R(old, new):
    global s
    assert old in s, old[:70]; s = s.replace(old, new, 1)
R('''def cap_band(f):''', '''def cap_band(f):
    """Gone (Jordan 11-24): wild Pokemon always come at their place's own level now (levels.wild_level)."""
    return None


def _old_cap_band(f):''')
R('''                f'highest level, and never below Lv {REMATCH_FLOOR}. Wild Pokémon rise to your team\'s level (its average, '
                'your lowest Pokémon left out) wherever that\'s above the place\'s own. Legendary Pokémon stay at Lv 70, and '
                'trainers keep their own levels.</div>')''', '''                f'highest level, and never below Lv {REMATCH_FLOOR}. Wild Pokémon stay at their places\' own levels, '
                'legendary Pokémon are Lv 70 unless the guide says otherwise, and trainers keep their own levels.</div>')''')
R('''            f'and Rare Candies stop working. The next Leader\'s best Pokémon is Lv {ace}. Once your lead Pokémon reaches '
            f'Lv {ace}, wild Pokémon in places below that level come at Lv {ace - LIFT_BELOW}\u2013{ace + LIFT_ABOVE}: '
            'the "At the cap" column in the tables. Trainers keep their own levels.</div>')''', '''            f'and Rare Candies stop working. The next Leader\'s best Pokémon is Lv {ace}.</div>')''')
R('''        rows.append(f"<tr><td>{n}</td><td><b>Lv {ace + CAP_OVER}</b></td><td>{esc(nxt)}</td><td>Lv {ace}</td>"
                    f"<td>Lv {ace - LIFT_BELOW}\u2013{ace + LIFT_ABOVE}</td></tr>")
    rows.append(f"<tr><td>Champion</td><td><b>Your team</b></td><td>the post-game</td><td>\u2014</td><td>your team's level</td></tr>")''',
'''        rows.append(f"<tr><td>{n}</td><td><b>Lv {ace + CAP_OVER}</b></td><td>{esc(nxt)}</td><td>Lv {ace}</td></tr>")
    rows.append(f"<tr><td>Champion</td><td><b>Your team</b></td><td>the post-game</td><td>\u2014</td></tr>")''')
R('''            '<th>Next (usual order)</th><th>Their best</th><th>Wild at the cap</th></tr></thead>\'''', '''            '<th>Next (usual order)</th><th>Their best</th></tr></thead>\'''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
