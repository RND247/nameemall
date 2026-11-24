#!/usr/bin/env python3
"""Generate themes.json: the Pokémon ID lists behind the themed quizzes (/?theme=<slug>).

Run from the repo root:  python3 build_themes.py
Type themes come from pokemon_details.json (each Pokémon's default form); the others are
hand-made lists. Gen 10 Pokémon are left out of type themes until their games release.
"""
import json

details = json.load(open('pokemon_details.json'))
names = {p['id']: p['n'] for p in json.load(open('pokemon.json'))}

def rng(a, b): return list(range(a, b + 1))

TYPES = ['normal', 'fire', 'water', 'grass', 'electric', 'ice', 'fighting', 'poison', 'ground',
         'flying', 'psychic', 'bug', 'rock', 'ghost', 'dragon', 'dark', 'steel', 'fairy']
TYPE_ICONS = {'normal': '⚪', 'fire': '🔥', 'water': '💧', 'grass': '🌿', 'electric': '⚡', 'ice': '❄️',
              'fighting': '🥊', 'poison': '☠️', 'ground': '⛰️', 'flying': '🪽', 'psychic': '🔮', 'bug': '🐛',
              'rock': '🪨', 'ghost': '👻', 'dragon': '🐉', 'dark': '🌑', 'steel': '⚙️', 'fairy': '✨'}

SPECIAL = [
    ('starters', '🌱', 'Starter Pokémon',
     [1, 4, 7, 152, 155, 158, 252, 255, 258, 387, 390, 393, 495, 498, 501, 650, 653, 656,
      722, 725, 728, 810, 813, 816, 906, 909, 912, 1026, 1027, 1028]),
    ('legendary', '👑', 'Legendary Pokémon',
     [144, 145, 146, 150, 243, 244, 245, 249, 250] + rng(377, 384) + rng(480, 488) + rng(638, 646) +
     [716, 717, 718, 772, 773] + rng(785, 792) + [800] + rng(888, 892) + rng(894, 898) + [905] +
     rng(1001, 1004) + [1007, 1008] + rng(1014, 1017) + [1024]),
    ('mythical', '🌟', 'Mythical Pokémon',
     [151, 251, 385, 386, 489, 490, 491, 492, 493, 494, 647, 648, 649, 719, 720, 721,
      801, 802, 807, 808, 809, 893, 1025]),
    ('pseudo-legendary', '🐲', 'Pseudo-Legendary Pokémon',
     rng(147, 149) + rng(246, 248) + rng(371, 376) + rng(443, 445) + rng(633, 635) +
     rng(704, 706) + rng(782, 784) + rng(885, 887) + rng(996, 998)),
    ('eeveelutions', '🦊', 'Eevee and Eeveelutions', [133, 134, 135, 136, 196, 197, 470, 471, 700]),
    ('fossils', '🦴', 'Fossil Pokémon',
     [138, 139, 140, 141, 142, 345, 346, 347, 348, 408, 409, 410, 411, 564, 565, 566, 567,
      696, 697, 698, 699, 880, 881, 882, 883]),
    ('ultra-beasts', '🌀', 'Ultra Beasts', rng(793, 799) + rng(803, 806)),
    ('paradox', '⏳', 'Paradox Pokémon', rng(984, 995) + [1005, 1006, 1009, 1010] + rng(1020, 1023)),
]

themes = []
for slug, icon, title, ids in SPECIAL:
    assert len(ids) == len(set(ids)), slug
    assert all(i in names for i in ids), slug
    themes.append({'slug': slug, 'icon': icon, 'title': title, 'ids': sorted(ids)})
for t in TYPES:
    ids = [int(k) for k, d in details.items() if int(k) <= 1025 and t in d['t']]
    themes.append({'slug': t + '-type', 'icon': TYPE_ICONS[t], 'title': t.capitalize() + '-type Pokémon',
                   'type': t, 'ids': sorted(ids)})

json.dump(themes, open('themes.json', 'w'), ensure_ascii=False, separators=(',', ':'))
for th in themes:
    print(f"{th['slug']:18} {len(th['ids']):4}  {', '.join(names[i] for i in th['ids'][:4])} … {names[th['ids'][-1]]}")
