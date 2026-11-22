#!/usr/bin/env python3
"""Generate the SEO landing pages (one folder per page with an index.html) and sitemap.xml.

Run from the repo root:  python3 build_landing.py
Each page has its own title, description, intro, FAQ and a Play button that opens the game
preset to that mode (/?gens=N, /?hint=1, /#daily, /#multi).
"""
import json, html, os, datetime

SITE = 'https://nameemall.com/'
GA = 'G-1NZMHCPJ9C'
TODAY = datetime.date.today().isoformat()
LANGS = ['ja', 'zh-Hant', 'zh-Hans', 'ko', 'fr', 'de', 'es', 'it', 'he']

data = json.load(open('pokemon.json'))
by_id = {p['id']: p for p in data}

GENS = [
    # gen, region, games, year, starter ids, legendary highlight
    (1, 'Kanto', 'Pokémon Red, Blue and Yellow', 1996, (1, 4, 7), 'Mewtwo and Mew'),
    (2, 'Johto', 'Pokémon Gold, Silver and Crystal', 1999, (152, 155, 158), 'Lugia, Ho-Oh and Celebi'),
    (3, 'Hoenn', 'Pokémon Ruby, Sapphire and Emerald', 2002, (252, 255, 258), 'Groudon, Kyogre and Rayquaza'),
    (4, 'Sinnoh', 'Pokémon Diamond, Pearl and Platinum', 2006, (387, 390, 393), 'Dialga, Palkia and Arceus'),
    (5, 'Unova', 'Pokémon Black and White', 2010, (495, 498, 501), 'Reshiram, Zekrom and Kyurem'),
    (6, 'Kalos', 'Pokémon X and Y', 2013, (650, 653, 656), 'Xerneas, Yveltal and Zygarde'),
    (7, 'Alola', 'Pokémon Sun and Moon', 2016, (722, 725, 728), 'Solgaleo, Lunala and Necrozma'),
    (8, 'Galar', 'Pokémon Sword and Shield', 2019, (810, 813, 816), 'Zacian, Zamazenta and Eternatus'),
    (9, 'Paldea', 'Pokémon Scarlet and Violet', 2022, (906, 909, 912), 'Koraidon, Miraidon and Terapagos'),
]

def gen_list(region):
    return [p for p in data if p['g'] == region]

def names(ids):
    n = [by_id[i]['n'] for i in ids]
    return ', '.join(n[:-1]) + ' and ' + n[-1]

PAGES = []

for gen, region, games, year, starters, legends in GENS:
    mons = gen_list(region)
    count, first, last = len(mons), mons[0], mons[-1]
    slug = f'gen-{gen}-pokemon-quiz'
    PAGES.append({
        'slug': slug,
        'title': f'Gen {gen} Pokémon Quiz: Can You Name All {count} {region} Pokémon?',
        'description': f'Free Gen {gen} Pokémon quiz. Name all {count} {region} Pokémon from {first["n"]} to {last["n"]} as fast as you can. No sign-up, works on phone and desktop.',
        'h1': f'Gen {gen} Pokémon Quiz: Name All {count} {region} Pokémon',
        'play': f'/?gens={gen}',
        'play_label': f'▶ Start the Gen {gen} quiz',
        'sprites': starters,
        'intro': [
            f'Generation {gen} brought {count} new Pokémon to the {region} region in {games} ({year}). How many of them can you name from memory?',
            f'Type any {region} Pokémon name and its card fills in. The quiz covers every Pokémon from #{first["id"]} {first["n"]} to #{last["id"]} {last["n"]}, including the starters {names(starters)} and legendaries like {legends}.',
        ],
        'how': [
            'Start typing: there is no Enter key, a correct name is accepted the moment it is complete.',
            'Names are forgiving: accents, capital letters and spaces don\'t matter.',
            'Stuck? Turn on 💡 Hint to show silhouettes (your score is marked as played with hints).',
            'Your progress is saved in your browser, so you can come back and finish later.',
        ],
        'faq': [
            (f'How many Gen {gen} Pokémon are there?',
             f'There are {count} Pokémon in Generation {gen} ({region}), numbered #{first["id"]} to #{last["id"]} in the National Pokédex.'),
            (f'Who are the Gen {gen} starters?',
             f'The {region} starter Pokémon are {names(starters)}.'),
            (f'What is a good score on the Gen {gen} quiz?',
             f'Naming half of the {count} Pokémon is a solid start. Fans who grew up with {games.replace("Pokémon ", "")} often get 90% or more, and the best players finish all {count} in a few minutes.'),
        ],
        'list': (f'Show all {count} Gen {gen} Pokémon (spoilers!)', mons),
        'kind': 'gen',
    })

PAGES += [
    {
        'slug': 'pokemon-silhouette-quiz',
        'title': 'Pokémon Silhouette Quiz: Guess All 1025 Pokémon by Their Shadow',
        'description': 'Free Pokémon silhouette quiz. Every Pokémon is shown as a shadow: type the right name to reveal it. All 1025 Pokémon, or pick your favourite generations.',
        'h1': 'Pokémon Silhouette Quiz',
        'play': '/?hint=1',
        'play_label': '▶ Start the silhouette quiz',
        'sprites': (25, 133, 94),
        'intro': [
            'Every Pokémon starts as a dark silhouette. Recognise the shape, type the name, and the full-color Pokémon pops out.',
            'It\'s the classic "guess the shadow" game, but with all 1025 Pokémon on one board. Play every generation at once, or open ⚙️ Settings and pick only the generations you know best.',
        ],
        'how': [
            'Silhouettes are on from the start; you can switch them off any time with the 💡 Hint button.',
            'Type a name and it is accepted as soon as it is correct, no Enter key needed.',
            'Games played with silhouettes are marked with 💡 on your scoreboard, so you can tell them apart from your no-hint runs.',
            'Ready for more? Turn hints off and try to name them all from memory.',
        ],
        'faq': [
            ('Is the Pokémon silhouette quiz free?', 'Yes. NameEmAll is free, runs in the browser and needs no account.'),
            ('Can I play the silhouette quiz for just one generation?', 'Yes. Open ⚙️ Settings in the game and choose the generations you want, or start from one of the generation quizzes below.'),
            ('Does it work on mobile?', 'Yes, the quiz works on phones, tablets and desktop browsers.'),
        ],
        'kind': 'mode',
    },
    {
        'slug': 'daily-pokemon-game',
        'title': 'Daily Pokémon Game: A New Pokémon Quiz Every Day',
        'description': 'A free daily Pokémon game. Every day there is a new set of Pokémon to name: Mini (5) and Midi (30). Keep your streak and see how you rank against other players.',
        'h1': 'The Daily Pokémon Game',
        'play': '/#daily',
        'play_label': '▶ Play today\'s Daily',
        'sprites': (143, 39, 54),
        'intro': [
            'Every day NameEmAll picks a fresh set of Pokémon, the same for every player in the world. Name them all to keep your streak alive.',
            'Choose Mini, a quick 5-Pokémon warm-up, or Midi with 30 Pokémon for a real challenge. When you finish, see how many players you beat and share your result with friends.',
        ],
        'how': [
            'Mini: 5 Pokémon. Midi: 30 Pokémon. A new Daily starts at midnight in your time zone.',
            'Each mode has its own 🔥 streak, and only perfect runs count.',
            'Compare your score with everyone who played today, and challenge a friend with a link.',
            'Missed a day? Play previous dailies from the archive.',
        ],
        'faq': [
            ('When does the daily Pokémon game reset?', 'A new Daily is available every day at midnight, in your own time zone.'),
            ('How does the streak work?', 'Mini and Midi have separate streaks. Naming every Pokémon in the Daily extends your streak; giving up resets it.'),
            ('Can I play old dailies?', 'Yes. Open "Play previous dailies" in the Daily tab and pick any past number.'),
        ],
        'kind': 'mode',
    },
    {
        'slug': 'pokemon-quiz-for-kids',
        'title': 'Pokémon Quiz for Kids: Easy Gen 1 Game with Silhouette Hints',
        'description': 'An easy Pokémon quiz for kids: the original 151 Pokémon with silhouette hints. Free, no sign-up and no ads in the game. Great for practising reading and spelling.',
        'h1': 'Pokémon Quiz for Kids',
        'play': '/?gens=1&hint=1',
        'play_label': '▶ Start the kids\' quiz',
        'sprites': (25, 1, 4),
        'intro': [
            'A friendly way for young Pokémon fans to test what they know. This quiz starts with the original 151 Pokémon from Kanto, with silhouette hints switched on so every Pokémon\'s shape is visible.',
            'Kids type the names themselves, which makes it great practice for reading and spelling. Small mistakes like capital letters, accents and spaces are forgiven.',
        ],
        'how': [
            'Silhouettes show the shape of each Pokémon to help kids guess.',
            'No timer pressure: the game can be paused, and progress is saved to come back to later.',
            'No account, no chat and no personal details needed.',
            'Ready for more? Pick more generations in ⚙️ Settings, or try the Daily Mini with just 5 Pokémon.',
        ],
        'faq': [
            ('What age is this Pokémon quiz for?', 'It suits kids who can read and type, usually around 6 and up. Younger kids can play together with a parent.'),
            ('Is it safe for kids?', 'Yes. There is no sign-up, no chat with strangers, and no personal information is collected.'),
            ('Can kids play in other languages?', 'Yes. The quiz is available in English, Japanese, Chinese, Korean, French, German, Spanish and Italian.'),
        ],
        'kind': 'mode',
    },
    {
        'slug': 'pokemon-quiz-with-friends',
        'title': 'Multiplayer Pokémon Quiz: Duel or Team Up with Friends',
        'description': 'Play a Pokémon quiz with friends online. Race a friend in a real-time Duel, or team up in Co-Op to name all 1025 Pokémon together. Free, just share a link.',
        'h1': 'Pokémon Quiz with Friends',
        'play': '/#multi',
        'play_label': '▶ Play with friends',
        'sprites': (6, 9, 3),
        'intro': [
            'Who knows more Pokémon, you or your friends? Create a room, share the link, and play together in real time. No accounts and no downloads.',
            'In ⚔️ Duel you race to name Pokémon before your opponent does. In 🤝 Co-Op you work as a team to fill the whole Pokédex together.',
        ],
        'how': [
            'Create a Duel or Co-Op room and send the link to a friend.',
            'Pick which generations to play before you start.',
            'Every name you type shows up on both screens instantly.',
            'For a solo competition, send a Daily challenge link and compare scores.',
        ],
        'faq': [
            ('How do I play the Pokémon quiz with a friend?', 'Open the Multiplayer tab, choose Duel or Co-Op, and share the room link. Your friend joins straight from the browser.'),
            ('Do we need to be on the same network?', 'No. You can play with friends anywhere; the link connects you directly.'),
            ('How many players can join?', 'Duel and Co-Op are designed for two players. For bigger groups, everyone can play the same Daily and compare results.'),
        ],
        'kind': 'mode',
    },
    {
        'slug': 'pokemon-quiz-for-streamers',
        'title': 'Pokémon Quiz for Streamers and YouTubers: Creator Mode',
        'description': 'A free Pokémon naming game built for streams and videos. Let your Twitch chat play along, and use a big, clean layout with a 9:16 frame for TikTok and Shorts.',
        'h1': 'Pokémon Quiz for Streamers and Creators',
        'play': '/?creator=setup',
        'play_label': '▶ Set up Creator Mode',
        'sprites': (25, 150, 448),
        'intro': [
            'Naming every Pokémon from memory makes great content: chat shouts suggestions, the counter keeps climbing, and the last few always feel impossible. Creator Mode turns NameEmAll into a layout that looks good on stream and is easy to edit.',
            'Pick horizontal for YouTube and Twitch, or vertical for TikTok, Shorts and Reels. The game then uses one steady top bar, a big input box your viewers can read, and a spotlight on the last Pokémon you named.',
        ],
        'how': [
            'Horizontal (16:9) or vertical (9:16): in vertical mode the game stays inside a fixed 9:16 frame, so cropping in OBS or your editor takes seconds.',
            'Big, readable score, timer and input box, with no tabs or footer to crop around.',
            'Twitch Chat Plays: enter your channel and your viewers name Pokémon by typing in chat. Play together, or go Chat vs You, with a live leaderboard of your top chatters.',
            'Milestone celebrations at 10, 25, 50, 75 and every 100 Pokémon, combo streaks, region completions and a finale with confetti.',
            "Challenge your audience: play today's Daily on stream and let viewers compare their scores, or race a viewer in a real-time Duel.",
        ],
        'faq': [
            ('How do I turn on Creator Mode?', 'Open ⚙️ Settings in the Full Pokédex and choose 🎥 Creator Mode, or use the button on this page. Your choice is remembered until you press Exit.'),
            ('Can I use NameEmAll on stream or in videos?', 'Yes. NameEmAll is free to play on stream and in videos. A link to nameemall.com in your description is appreciated.'),
            ('Does it work with OBS?', 'Yes. Capture the browser window in OBS, Streamlabs or any recorder. In vertical mode, crop the capture to the 9:16 game frame.'),
            ('Can my Twitch chat play along?', 'Yes. Type your channel name in the Creator Mode setup. Chat messages count as guesses, with no login or Twitch app needed. Choose Together to fill the Pokédex as a team, or Chat vs You to race your viewers.'),
            ('Is there a NameEmAll community?', 'Yes. Join the NameEmAll Discord at discord.gg/WJj2VYVxnz to share clips, find opponents for a Duel and suggest features for your stream.'),
        ],
        'kind': 'mode',
    },
]

# ── Themed quizzes (/?theme=<slug>, lists from themes.json via build_themes.py) ──
THEMES = json.load(open('themes.json'))
THEME_PAGES = {
    # theme slug: (page slug, short label, intro line, FAQ answer about who is included)
    'starters': ('starter-pokemon-quiz', 'Starter Pokémon',
        'Every region begins with a choice of three. Can you name all {count} starter Pokémon, from Bulbasaur, Charmander and Squirtle to Browt, Pombon and Gecqua, the Gen 10 starters revealed for Pokémon Winds and Waves?',
        'The first-stage Grass, Fire and Water starters of every generation, including the three Gen 10 starters revealed so far (Browt, Pombon and Gecqua).'),
    'legendary': ('legendary-pokemon-quiz', 'Legendary Pokémon',
        'From the Kanto birds to Koraidon, Miraidon and Terapagos: how many of the {count} Legendary Pokémon can you name from memory?',
        'Every Pokémon officially classed as Legendary, including sub-legendaries like the Tapus, the Treasures of Ruin and the Loyal Three. Mythical Pokémon have their own quiz.'),
    'mythical': ('mythical-pokemon-quiz', 'Mythical Pokémon',
        'Mew, Celebi, Jirachi, Arceus, Pecharunt and the rest: name all {count} Mythical Pokémon, the rare ones usually only given out at events.',
        'All {count} Mythical Pokémon, from Mew (#151) to Pecharunt (#1025).'),
    'pseudo-legendary': ('pseudo-legendary-pokemon-quiz', 'Pseudo-legendary Pokémon',
        'Dragonite, Tyranitar, Garchomp, Dragapult and friends: name all {count} pseudo-legendary Pokémon, including every pre-evolution.',
        'The full three-stage lines of the ten pseudo-legendaries (a base stat total of 600), from Dratini to Baxcalibur.'),
    'eeveelutions': ('eeveelution-quiz', 'Eeveelutions',
        'Eevee can evolve in more ways than any other Pokémon. Can you name Eevee and all its evolutions?',
        'Eevee plus Vaporeon, Jolteon, Flareon, Espeon, Umbreon, Leafeon, Glaceon and Sylveon.'),
    'fossils': ('fossil-pokemon-quiz', 'Fossil Pokémon',
        'Revived from fossils across six generations: how many of the {count} Fossil Pokémon can you name?',
        'Every Pokémon revived from a fossil and its evolutions, from Omanyte and Kabuto to the Galar fossil Pokémon.'),
    'ultra-beasts': ('ultra-beast-quiz', 'Ultra Beasts',
        'Nihilego, Buzzwole, Pheromosa and the rest came through Ultra Wormholes. Can you name all {count} Ultra Beasts?',
        'All {count} Ultra Beasts from Pokémon Sun, Moon, Ultra Sun and Ultra Moon.'),
    'paradox': ('paradox-pokemon-quiz', 'Paradox Pokémon',
        'Ancient and future forms of familiar Pokémon: name all {count} Paradox Pokémon from Pokémon Scarlet and Violet and their DLC.',
        'The ancient Paradox Pokémon (like Great Tusk and Roaring Moon) and the future ones (like Iron Valiant and Iron Crown).'),
}

def theme_title(th):
    return th['title']

def list_ids(ids):
    return [by_id[i] for i in ids if i in by_id]

for th in THEMES:
    count = len(th['ids'])
    mons = list_ids(th['ids'])
    if th.get('type'):
        tname = th['type'].capitalize()
        slug = f"{th['type']}-type-pokemon-quiz"
        label = f'{tname}-type Pokémon'
        intro0 = f'There are {count} Pokémon with the {tname} type. How many can you name from memory, from {mons[0]["n"]} to {mons[-1]["n"]}?'
        who = f'Every Pokémon whose main form has the {tname} type, as one of its one or two types. Regional forms are not counted separately.'
    else:
        slug, label, intro0, who = THEME_PAGES[th['slug']]
        intro0, who = intro0.format(count=count), who.format(count=count)
    PAGES.append({
        'slug': slug,
        'title': f'{label} Quiz: Can You Name All {count}?',
        'description': f'Free {label} quiz. Name all {count} {label} as fast as you can. No sign-up, works on phone and desktop, in 10 languages.',
        'h1': f'{label} Quiz: Name All {count}',
        'play': f'/?theme={th["slug"]}',
        'play_label': f'▶ Start the {label} quiz',
        'sprites': tuple(m['id'] for m in mons[:3] if m['id'] <= 1025),
        'intro': [
            intro0,
            'Type a name and its card fills in. Names are forgiving: accents, capital letters and spaces don\'t matter, and you can switch to Japanese, Chinese, Korean, French, German, Spanish or Italian names.',
        ],
        'how': [
            'Start typing: there is no Enter key, a correct name is accepted the moment it is complete.',
            'Type a Pokémon that isn\'t part of this quiz and the game tells you, so you can move on.',
            'Stuck? Turn on 💡 Hint to show silhouettes (your score is marked as played with hints).',
            'Your progress is saved in your browser, so you can come back and finish later.',
        ],
        'faq': [
            (f'How many {label} are there?', f'This quiz has {count}. ' + who),
            ('Is the quiz free?', 'Yes. NameEmAll is free, runs in the browser and needs no account.'),
            ('Can I play other themes?', 'Yes. Open ⚙️ Settings in the game and pick another theme from Themed quizzes, or choose one below.'),
        ],
        'list': (f'Show all {count} (spoilers!)', mons),
        'kind': 'theme',
        'card': (label, f'{count} Pokémon'),
    })

HUB = {
    'slug': 'pokemon-quizzes',
    'title': 'All Pokémon Quizzes: By Generation, Silhouettes, Daily and More',
    'description': 'Every NameEmAll Pokémon quiz in one place: name all 1025 Pokémon, quizzes for each generation from Kanto to Paldea, themed quizzes by type, Legendaries and starters, silhouettes, the Daily game and multiplayer.',
    'h1': 'All Pokémon Quizzes',
}

CSS = """
:root { --bg:#0f0f1a; --bg2:#161625; --card:#1c1c30; --accent:#e94560; --text:#e8e8f0; --dim:#9aa0ad; --border:#2a2a40; }
@media (prefers-color-scheme: light) { :root { --bg:#f0f2f5; --bg2:#fff; --card:#e4e7ec; --accent:#d63050; --text:#1a1a2e; --dim:#5b6270; --border:#c8cdd5; } }
* { box-sizing:border-box; margin:0; padding:0; }
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }
a { color:var(--accent); }
.top { background:var(--bg2); border-bottom:1px solid var(--border); padding:10px 16px; }
.top a { color:var(--text); text-decoration:none; font-weight:800; font-size:1.1rem; }
.top a span { color:var(--accent); }
.brand-note { max-width:760px; margin:0 auto; padding:14px 16px 0; }
.brand-note div { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:10px 14px; font-size:.88rem; }
.brand-note a { font-weight:700; }
main { max-width:760px; margin:0 auto; padding:28px 16px 40px; }
.crumbs { font-size:.8rem; color:var(--dim); margin-bottom:10px; }
.crumbs a { color:var(--dim); }
h1 { font-size:clamp(1.5rem,5vw,2.1rem); line-height:1.25; margin-bottom:14px; }
h2 { font-size:1.15rem; margin:28px 0 10px; }
p { margin-bottom:12px; }
.sprites { display:flex; gap:8px; margin:6px 0 14px; }
.sprites img { width:84px; height:84px; image-rendering:pixelated; background:var(--card); border:1px solid var(--border); border-radius:12px; }
.play { display:inline-block; background:var(--accent); color:#fff; text-decoration:none; font-weight:800; font-size:1.1rem; padding:13px 26px; border-radius:10px; margin:8px 0 6px; }
.play:hover { filter:brightness(1.1); }
.note { font-size:.82rem; color:var(--dim); }
ul.how { padding-left:20px; } ul.how li { margin-bottom:6px; }
.faq h3 { font-size:1rem; margin:14px 0 4px; }
details.list { background:var(--card); border:1px solid var(--border); border-radius:10px; padding:10px 14px; margin-top:8px; }
details.list summary { cursor:pointer; font-weight:700; }
details.list ol { columns:3 140px; margin-top:10px; padding-left:0; list-style:none; font-size:.88rem; }
details.list li span { color:var(--dim); font-variant-numeric:tabular-nums; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(210px,1fr)); gap:10px; }
.grid a { display:block; background:var(--card); border:1px solid var(--border); border-radius:10px; padding:12px 14px; text-decoration:none; color:var(--text); }
.grid a:hover { border-color:var(--accent); }
.grid b { display:block; color:var(--accent); }
.grid small { color:var(--dim); }
footer { max-width:760px; margin:0 auto; padding:20px 16px 36px; border-top:1px solid var(--border); font-size:.78rem; color:var(--dim); }
footer a { color:var(--dim); }
"""

def esc(s):
    return html.escape(s, quote=True)

def card_label(p):
    if p.get('card'):
        return p['card']
    if p.get('kind') == 'gen':
        g = p['slug'].split('-')[1]
        region = GENS[int(g) - 1][1]
        return f'Gen {g}: {region}', f'{len(gen_list(region))} Pokémon'
    return {
        'pokemon-silhouette-quiz': ('Silhouette quiz', 'Guess every Pokémon by its shadow'),
        'daily-pokemon-game': ('Daily Pokémon game', 'Mini (5) and Midi (30), every day'),
        'pokemon-quiz-for-kids': ('Quiz for kids', 'Gen 1 with silhouette hints'),
        'pokemon-quiz-with-friends': ('Play with friends', 'Real-time Duel and Co-Op'),
        'pokemon-quiz-for-streamers': ('For streamers', 'Creator Mode for videos and streams'),
    }[p['slug']]

def grid(exclude=None):
    cards = [('/', 'All 1025 Pokémon', 'The full National Pokédex')]
    for p in PAGES:
        if p['slug'] == exclude:
            continue
        a, b = card_label(p)
        cards.append((f'/{p["slug"]}/', a, b))
    return '<div class="grid">' + ''.join(
        f'<a href="{h}"><b>{esc(a)}</b><small>{esc(b)}</small></a>' for h, a, b in cards) + '</div>'

BRAND_NOTE = '<div class="brand-note"><div>This quiz is part of <a href="/">NameEmAll</a>, the free game where you name all 1025 Pokémon. <a href="/">Play the full Pokédex quiz →</a></div></div>'

def page(p, body, jsonld):
    url = SITE + p['slug'] + '/'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','{GA}');</script>
<title>{esc(p['title'])}</title>
<meta name="description" content="{esc(p['description'])}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="NameEmAll">
<meta property="og:title" content="{esc(p['h1'])}">
<meta property="og:description" content="{esc(p['description'])}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}og-image.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(p['h1'])}">
<meta name="twitter:description" content="{esc(p['description'])}">
<meta name="twitter:image" content="{SITE}og-image.png">
<link rel="icon" type="image/png" sizes="48x48" href="/img/icons/favicon-48.png">
<link rel="icon" type="image/png" sizes="192x192" href="/img/icons/icon-192.png">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>
<body>
<div class="top"><a href="/">Name<span>'Em All</span></a></div>
{'' if p.get('no_brand_note') else BRAND_NOTE}
<main>
{body}
</main>
<footer>
NameEmAll is a free fan-made quiz. It is not affiliated with Nintendo, Game Freak, Creatures or The Pokémon Company. Pokémon names and sprites are trademarks of their respective owners.
Data: <a href="https://pokeapi.co">PokéAPI</a>.
<br><a href="/">Play NameEmAll</a> · <a href="/pokemon-quizzes/">All quizzes</a> · <a href="/press/">Press kit</a>
</footer>
</body>
</html>
"""

def webpage(p):
    return {"@type": "WebPage", "name": p['h1'], "url": SITE + p['slug'] + '/',
            "isPartOf": {"@type": "WebSite", "name": "NameEmAll", "url": SITE}}

def breadcrumb(p):
    return {"@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "NameEmAll", "item": SITE},
        {"@type": "ListItem", "position": 2, "name": p['h1'], "item": SITE + p['slug'] + '/'},
    ]}

def build(p):
    sprites = ''.join(f'<img src="{by_id[i]["s"]}" alt="{esc(by_id[i]["n"])}" width="84" height="84" loading="lazy">' for i in p['sprites'])
    parts = [f'<div class="crumbs"><a href="/">NameEmAll</a> › <a href="/pokemon-quizzes/">Quizzes</a></div>',
             f'<h1>{esc(p["h1"])}</h1>', f'<div class="sprites">{sprites}</div>']
    parts += [f'<p>{esc(t)}</p>' for t in p['intro']]
    parts.append(f'<a class="play" href="{esc(p["play"])}">{esc(p["play_label"])}</a>')
    parts.append('<p class="note">Free, no sign-up, works on phone and desktop. Also in 日本語, 繁體中文, 简体中文, 한국어, Français, Deutsch, Español, Italiano and עברית.</p>')
    parts.append('<h2>How it works</h2><ul class="how">' + ''.join(f'<li>{esc(t)}</li>' for t in p['how']) + '</ul>')
    if p.get('list'):
        label, mons = p['list']
        parts.append(f'<details class="list"><summary>{esc(label)}</summary><ol>' +
                     ''.join(f'<li><span>#{m["id"]}</span> {esc(m["n"])}</li>' for m in mons) + '</ol></details>')
    parts.append('<h2>FAQ</h2><div class="faq">' + ''.join(f'<h3>{esc(q)}</h3><p>{esc(a)}</p>' for q, a in p['faq']) + '</div>')
    parts.append('<h2>More Pokémon quizzes</h2>' + grid(exclude=p['slug']))
    jsonld = {"@context": "https://schema.org", "@graph": [
        webpage(p), breadcrumb(p),
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p['faq']]},
    ]}
    return page(p, '\n'.join(parts), jsonld)

PRESS = {
    'slug': 'press',
    'title': 'NameEmAll for Streamers and Creators: Press Kit',
    'description': 'Press kit for NameEmAll, the free Pokémon naming game with Twitch Chat Plays and Creator Mode. Screenshots, a demo GIF and how to set it up on stream.',
    'h1': 'Press Kit: NameEmAll for Streamers',
    'no_brand_note': True,
}

def build_press():
    p = PRESS
    steps = [
        'Open <a href="/?creator=setup">nameemall.com/?creator=setup</a> (or ⚙️ Settings → 🎥 Creator Mode).',
        'Choose horizontal (YouTube, Twitch) or vertical (TikTok, Shorts), and type your Twitch channel name.',
        'Pick 🤝 Together or ⚔️ Chat vs You, press Start, and capture the browser window in OBS.',
    ]
    feats = [
        ('💬 Twitch Chat Plays', 'Viewers name Pokémon by typing them in your chat. No login, no bot, read-only.'),
        ('⚔️ Chat vs You', 'Race your chat. Claimed Pokémon are outlined, with a live You vs Chat score.'),
        ('👑 Live leaderboard', 'Your top chatters in their Twitch colors, and the spotlight credits who named each Pokémon.'),
        ('🎥 Creator Mode', 'One steady layout, big text, a 9:16 frame for vertical video, and celebrations at every milestone.'),
        ('🌍 10 languages', 'English, 日本語, 繁體中文, 简体中文, 한국어, Français, Deutsch, Español, Italiano and עברית.'),
        ('🗓️ Daily challenge', 'A new set every day (5 or 30 Pokémon). Great for a quick segment with chat comparing scores.'),
    ]
    body = '\n'.join([
        '<div class="crumbs"><a href="/">NameEmAll</a></div>',
        f'<h1>{esc(p["h1"])}</h1>',
        '<p><b>NameEmAll</b> is a free browser game: name all 1025 Pokémon from memory. With <b>Twitch Chat Plays</b>, your viewers type Pokémon names in chat and fill the Pokédex with you, or against you.</p>',
        '<p><img src="/img/press/chat-plays.gif" alt="Twitch Chat Plays: chat names Pokémon and a live leaderboard fills up" style="width:100%;border-radius:12px;border:1px solid var(--border)" loading="lazy"></p>',
        '<a class="play" href="/?creator=setup">▶ Set up Creator Mode</a>',
        '<p class="note">Free to use on stream and in videos, no permission needed. A link to nameemall.com in your description is appreciated.</p>',
        '<h2>Set it up in 30 seconds</h2><ol class="how">' + ''.join(f'<li>{x}</li>' for x in steps) + '</ol>',
        '<h2>What your stream gets</h2><div class="grid">' + ''.join(f'<a href="/?creator=setup"><b>{esc(a)}</b><small>{esc(b)}</small></a>' for a, b in feats) + '</div>',
        '<h2>Assets</h2><ul class="how">'
        '<li><a href="/img/press/chat-plays.gif">Chat Plays demo (GIF)</a></li>'
        '<li><a href="/img/press/creator-mode.jpg">Creator Mode screenshot (JPG)</a></li>'
        '<li><a href="/og-image.png">Title card, 1200 × 630 (PNG)</a></li></ul>',
        '<h2>Contact</h2><p>Ideas, bugs or a feature you want for your stream: <a href="mailto:randayan10@gmail.com">randayan10@gmail.com</a>, or come say hi on the <a href="https://discord.gg/WJj2VYVxnz">NameEmAll Discord</a>.</p>',
    ])
    jsonld = {"@context": "https://schema.org", "@graph": [webpage(p), breadcrumb(p)]}
    return page(p, body, jsonld)

def build_hub():
    p = HUB
    body = '\n'.join([
        f'<div class="crumbs"><a href="/">NameEmAll</a></div>',
        f'<h1>{esc(p["h1"])}</h1>',
        '<p>Can you name every Pokémon? Start with the full 1025-Pokémon Pokédex, focus on a single generation, or try one of the special modes. Every quiz is free and runs right in your browser.</p>',
        grid(),
    ])
    jsonld = {"@context": "https://schema.org", "@graph": [webpage(p), breadcrumb(p), {
        "@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": SITE + q['slug'] + '/', "name": q['h1']} for i, q in enumerate(PAGES)]}]}
    return page(p, body, jsonld)

def write(slug, content):
    os.makedirs(slug, exist_ok=True)
    with open(os.path.join(slug, 'index.html'), 'w') as f:
        f.write(content)

for p in PAGES:
    write(p['slug'], build(p))
write(HUB['slug'], build_hub())
write(PRESS['slug'], build_press())

# ── sitemap.xml ──
alt = lambda: ''.join(f'\n    <xhtml:link rel="alternate" hreflang="{l}" href="{SITE}?lang={l}"/>' for l in LANGS) + \
    f'\n    <xhtml:link rel="alternate" hreflang="en" href="{SITE}"/>\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}"/>'
urls = [f'  <url>\n    <loc>{SITE}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>{alt()}\n  </url>']
for l in LANGS:
    urls.append(f'  <url>\n    <loc>{SITE}?lang={l}</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>0.8</priority>{alt()}\n  </url>')
for slug in [HUB['slug']] + [p['slug'] for p in PAGES] + [PRESS['slug']]:
    urls.append(f'  <url>\n    <loc>{SITE}{slug}/</loc>\n    <lastmod>{TODAY}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.7</priority>\n  </url>')
with open('sitemap.xml', 'w') as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + '\n'.join(urls) + '\n</urlset>\n')

print(f'Built {len(PAGES) + 1} pages and sitemap.xml ({len(urls)} URLs)')
