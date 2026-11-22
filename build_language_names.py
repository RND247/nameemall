#!/usr/bin/env python3
"""Generate names/<lang>.js for every supported UI language.

Usage:
    python3 build_language_names.py path/to/pokeapi_csv_dir [lang ...]

The directory must contain PokeAPI's data/v2/csv files:
    pokemon_species_names.csv, region_names.csv, type_names.csv
(https://github.com/PokeAPI/pokeapi)

Each output file sets window.NEA_NAMES = {
    pokemon: { "<id>": [displayName, ...acceptedAnswers] },
    regions: { "Kanto": "...", ... },   # keyed by English name
    types:   { "grass": "...", ... },   # keyed by lowercase English name
}
Accepted answers are raw spellings; index.html normalizes them (and the typed
input) with normalizeAnswer(), so accents, case, kana and full-width forms
don't matter. The script also checks that no answer collides with, or is a
prefix of, a different Pokémon's English answer.
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "names"

# code -> (main PokeAPI language id, extra ids whose names are also accepted)
LANGS = {
    "ja": (1, [11]),        # katakana; also the kanji-capable "ja" list
    "zh-Hant": (4, [12]),   # Traditional; also accept Simplified spellings
    "zh-Hans": (12, [4]),   # Simplified; also accept Traditional spellings
    "ko": (3, []),
    "fr": (5, []),
    "de": (6, []),
    "es": (7, []),
    "it": (8, []),
}
EN = 9
REGIONS = ["Kanto", "Johto", "Hoenn", "Sinnoh", "Unova", "Kalos", "Alola", "Galar", "Paldea"]
REGION_FALLBACK = {"es": {"Unova": "Teselia"}}  # PokeAPI has no Spanish region names
# Pokémon newer than PokeAPI's data (Gen 10 starters). Languages not listed here keep the
# names already in their names/<lang>.js file.
MANUAL = {"zh-Hans": {1026: "叶眉鸟", 1027: "博姆耿", 1028: "妙澪儿"}}
# "Gen 10" has no region yet, so it gets a generation label
GEN10 = {"ja": "第10世代", "zh-Hant": "第10世代", "zh-Hans": "第10世代", "ko": "10세대", "fr": "Gén. 10",
         "de": "Gen. 10", "es": "Gen. 10", "it": "Gen. 10"}


def existing_names(code: str) -> dict:
    f = OUT / f"{code}.js"
    if not f.exists():
        return {}
    txt = f.read_text(encoding="utf-8")
    return {int(k): v[0] for k, v in json.loads(txt[txt.index("{"):txt.rindex("}") + 1])["pokemon"].items()}


HE_FINALS = str.maketrans("ךםןףץ", "כמנפצ")


def normalize(s: str) -> str:
    """Python twin of normalizeAnswer() in index.html (used for the checks only)."""
    s = unicodedata.normalize("NFKC", s).lower().strip()
    s = "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in s)
    s = "".join(c for c in unicodedata.normalize("NFD", s) if not "̀" <= c <= "ͯ")
    s = unicodedata.normalize("NFC", s)
    # Hebrew: drop vowel points, geresh/apostrophes after a letter, and final-letter forms
    s = re.sub(r"[\u0591-\u05c7]", "", s)
    s = re.sub(r"(?<=[\u05d0-\u05ea])['׳’`״\"]", "", s)
    return s.translate(HE_FINALS)


def variants(name: str, lang: str) -> list:
    out = [name, re.sub(r"[\s\-.:'’・：׳]", "", name)]
    for sym, word in (("♀", "メス"), ("♂", "オス")):
        if sym in name:
            out += [name.replace(sym, "").strip()]
            if lang == "ja":
                out += [name.replace(sym, word)]
    if lang == "de":
        out += [n.replace("ß", "ss").replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
                 .replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue") for n in list(out)]
    if lang == "fr":
        out += [n.replace("œ", "oe").replace("Œ", "Oe") for n in list(out)]
    return [v for v in dict.fromkeys(out) if v]


def load(csv_dir: Path, fname: str, id_col: str):
    data = {}
    with open(csv_dir / fname, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            data.setdefault(int(row["local_language_id"]), {})[int(row[id_col])] = row["name"]
    return data


def main(csv_dir: str, only=None) -> None:
    csv_dir = Path(csv_dir)
    species = load(csv_dir, "pokemon_species_names.csv", "pokemon_species_id")
    regions = load(csv_dir, "region_names.csv", "region_id")
    types = load(csv_dir, "type_names.csv", "type_id")
    pokemon = json.loads((ROOT / "pokemon.json").read_text(encoding="utf-8"))

    en_regions = {v: k for k, v in regions[EN].items()}
    en_types = {k: v.lower() for k, v in types[EN].items() if k < 10000}

    # English answers, normalized, for collision / prefix checks
    en_keys = {}
    for p in pokemon:
        for k in p["k"]:
            en_keys.setdefault(normalize(k), set()).add(p["id"])

    OUT.mkdir(exist_ok=True)
    problems = 0
    for code, (main_id, extra_ids) in LANGS.items():
        if only and code not in only:
            continue
        names = {}
        fallback = {**existing_names(code), **MANUAL.get(code, {})}
        for p in pokemon:
            pid = p["id"]
            display = species[main_id].get(pid) or fallback.get(pid)
            if not display:
                sys.exit(f"{code}: missing name for #{pid}")
            accepted = variants(display, code)
            for eid in extra_ids:
                extra = species.get(eid, {}).get(pid)
                if extra:
                    accepted += [v for v in variants(extra, code) if v not in accepted]
            names[str(pid)] = [display] + accepted

        # Checks: no answer may point at a different Pokémon than English does,
        # and no answer may be a prefix of a different Pokémon's answer (instant matching would stop early).
        lang_keys = {}
        for pid, vals in names.items():
            for v in vals[1:]:
                lang_keys.setdefault(normalize(v), set()).add(int(pid))
        clashes = [(k, ids, en_keys[k]) for k, ids in lang_keys.items() if k in en_keys and not ids <= en_keys[k]]
        # Cross-language prefixes: a full answer in one language that starts a different
        # Pokémon's answer in the other language (e.g. French "Abo" vs English "Abomasnow").
        # The game delays these by a moment (see ambiguousKeys in index.html); listed for info.
        langs_of = {}
        for k in en_keys:
            langs_of.setdefault(k, set()).add("en")
        for k in lang_keys:
            langs_of.setdefault(k, set()).add(code)
        species_of = {k: en_keys.get(k, set()) | lang_keys.get(k, set()) for k in langs_of}
        ordered = sorted(langs_of)
        prefix = []
        for i, k in enumerate(ordered):
            for k2 in ordered[i + 1:]:
                if not k2.startswith(k):
                    break
                if not (species_of[k] & species_of[k2]) and not (langs_of[k] & langs_of[k2]):
                    prefix.append((k, k2))
        if clashes:
            problems += 1
            print(f"{code}: {len(clashes)} CLASHES {clashes[:5]}")
        if prefix:
            print(f"{code}: {len(prefix)} cross-language prefixes (delayed in game): {prefix}")

        reg = {en: regions.get(main_id, {}).get(en_regions[en]) or REGION_FALLBACK.get(code, {}).get(en, en)
               for en in REGIONS}
        if code in GEN10:
            reg["Gen 10"] = GEN10[code]
        typ = {en_types[tid]: types[main_id][tid] for tid in en_types if tid in types.get(main_id, {})}

        payload = {"pokemon": names, "regions": reg, "types": typ}
        (OUT / f"{code}.js").write_text(
            "// Generated by build_language_names.py from PokeAPI data. Do not edit by hand.\n"
            "window.NEA_NAMES = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
            encoding="utf-8",
        )
        size = (OUT / f"{code}.js").stat().st_size // 1024
        print(f"{code}: {len(names)} Pokémon, {len(typ)} types, regions {list(reg.values())[4]}… -> names/{code}.js ({size} KB)")
    if not only or "he" in only:
        problems += build_hebrew(pokemon, en_keys)
    if problems:
        print(f"\n{problems} language(s) need attention (see above)")


# Hebrew has no official Pokémon names: the hand-written Hebrew spellings in names_src/he.txt
# (one line per Pokédex number, alternatives split by |; the first is the one shown) are accepted
# as answers alongside English. Types and regions are translated here.
HE_TYPES = {"normal": "נורמלי", "fire": "אש", "water": "מים", "grass": "דשא", "electric": "חשמל",
            "ice": "קרח", "fighting": "לחימה", "poison": "רעל", "ground": "אדמה", "flying": "מעופף",
            "psychic": "על-חושי", "bug": "חרק", "rock": "סלע", "ghost": "רוח רפאים", "dragon": "דרקון",
            "dark": "אופל", "steel": "פלדה", "fairy": "פיה", "stellar": "כוכבי"}
HE_REGIONS = {"Kanto": "קאנטו", "Johto": "ג'וטו", "Hoenn": "הואן", "Sinnoh": "סינו", "Unova": "יונובה",
              "Kalos": "קאלוס", "Alola": "אלולה", "Galar": "גאלאר", "Paldea": "פאלדאה", "Gen 10": "דור 10"}


def build_hebrew(pokemon, en_keys) -> int:
    lines = (ROOT / "names_src" / "he.txt").read_text(encoding="utf-8").splitlines()
    if len(lines) != len(pokemon):
        sys.exit(f"he: names_src/he.txt has {len(lines)} lines, expected {len(pokemon)}")
    names, he_keys = {}, {}
    for p, line in zip(pokemon, lines):
        accepted = []
        for sp in line.split("|"):
            accepted += [v for v in variants(sp.strip(), "he") if v not in accepted]
        names[str(p["id"])] = [accepted[0]] + accepted  # shown in Hebrew: the first spelling
        for v in accepted:
            he_keys.setdefault(normalize(v), set()).add(p["id"])
    problems = 0
    dupes = {k: ids for k, ids in he_keys.items() if len(ids) > 1}
    if dupes:
        problems += 1
        print(f"he: {len(dupes)} spellings shared by different Pokémon: {dupes}")
    # A Hebrew answer that starts a different Pokémon's Hebrew answer: the game waits a moment
    # before matching it (ambiguousKeys in index.html), so the longer name can still be typed.
    en_pairs = {(min(a), min(b)) for k, a in en_keys.items() for k2, b in en_keys.items()
                if k2 != k and k2.startswith(k) and not (a & b)}
    ordered = sorted(he_keys)
    odd = []
    for i, k in enumerate(ordered):
        for k2 in ordered[i + 1:]:
            if not k2.startswith(k):
                break
            a, b = he_keys[k], he_keys[k2]
            if not (a & b) and (min(a), min(b)) not in en_pairs:
                odd.append((k, sorted(a), k2, sorted(b)))
    if odd:
        print(f"he: {len(odd)} Hebrew prefix pairs (delayed in game)")
    payload = {"pokemon": names, "regions": HE_REGIONS, "types": HE_TYPES}
    (OUT / "he.js").write_text(
        "// Generated by build_language_names.py from names_src/he.txt. Do not edit by hand.\n"
        "window.NEA_NAMES = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"he: {len(names)} Pokémon -> names/he.js ({(OUT / 'he.js').stat().st_size // 1024} KB)")
    return problems


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1], set(sys.argv[2:]) or None)
