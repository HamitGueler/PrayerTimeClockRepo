"""Complete offline source texts, joined strictly by sura and aya identifiers."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'Data'
# Familiar passages about prayer, gratitude, mercy, patience, conduct and dua.
# Identifiers only: Arabic and translation are always the complete source verse.
SELECTED_REFERENCES = tuple('''
1:1 1:2 1:5 1:6 2:45 2:83 2:110 2:152 2:153 2:155 2:156 2:157
2:172 2:177 2:183 2:186 2:201 2:208 2:214 2:216 2:255 2:256 2:261 2:263 2:271 2:277 2:285 2:286
3:8 3:9 3:26 3:27 3:31 3:92 3:102 3:103 3:104 3:133 3:134 3:135 3:139 3:159 3:160 3:173 3:185 3:190 3:191 3:200
4:29 4:36 4:40 4:58 4:86 4:110 4:135 5:2 5:8 5:32 5:48 5:90
6:59 6:151 6:152 6:160 6:162 7:23 7:31 7:55 7:56 7:156 7:199 7:204 7:205
8:2 8:46 9:40 9:51 9:71 9:119 9:128 9:129 10:57 10:58 10:62 10:63
11:6 11:88 11:90 11:114 11:115 11:123 12:18 12:64 12:86 12:87 12:90 12:92
13:11 13:22 13:28 14:7 14:24 14:40 14:41 15:49 15:98 15:99
16:18 16:90 16:97 16:125 16:127 16:128 17:23 17:24 17:26 17:27 17:32 17:36 17:37 17:53 17:78 17:79 17:80 17:82
18:10 18:23 18:24 18:28 18:46 18:110 19:96 20:14 20:25 20:26 20:46 20:114 20:130 20:132
21:35 21:83 21:87 21:89 21:107 22:32 22:77 22:78 23:1 23:2 23:3 23:4 23:8 23:9 23:97 23:98 23:118
24:22 24:30 24:31 24:35 24:37 24:38 24:52 25:58 25:63 25:64 25:65 25:67 25:70 25:71 25:74
26:78 26:79 26:80 26:81 26:82 26:83 26:84 26:87 27:19 28:24 28:77 29:2 29:45 29:57 29:60 29:69
30:21 30:22 30:30 31:14 31:17 31:18 31:19 31:34 32:16 32:17 33:21 33:35 33:41 33:42 33:56 33:70 33:71
34:39 35:3 35:15 35:29 35:30 36:58 36:82 37:180 37:181 37:182 38:29 39:9 39:10 39:36 39:53 39:54
40:44 40:60 41:30 41:33 41:34 41:35 42:11 42:19 42:25 42:30 42:36 42:38 42:40 42:43
43:13 43:14 44:3 45:13 46:15 47:7 48:4 49:10 49:11 49:12 49:13 50:16 51:50 51:55 51:56 51:58
52:48 53:39 53:40 53:41 53:42 53:43 54:17 55:13 55:26 55:27 55:60 56:74 57:4 57:16 57:20 57:21 57:23 57:28
58:11 59:18 59:19 59:22 59:23 59:24 60:4 60:8 61:2 61:3 62:9 62:10 63:9 63:10 64:11 64:13 64:16
65:2 65:3 65:7 66:8 66:11 67:1 67:2 67:15 67:23 68:4 69:40 70:5 71:10 71:11 71:12 71:28 72:18
73:8 73:9 74:3 74:4 74:5 74:6 74:7 75:22 75:23 76:8 76:9 76:24 76:25 76:26 78:31 79:40 79:41
80:24 81:27 81:28 82:10 82:11 82:12 83:18 83:19 83:20 84:6 85:14 85:15 85:16 86:4 87:1 87:14 87:15 87:16 87:17
88:21 88:22 89:27 89:28 89:29 89:30 90:12 90:13 90:14 90:15 90:16 90:17 91:9 91:10 92:18 92:19 92:20 92:21
93:3 93:4 93:5 93:9 93:10 93:11 94:5 94:6 94:7 94:8 95:4 96:1 96:2 96:3 96:4 96:5 96:19 97:3 97:5
98:7 98:8 99:7 99:8 100:6 100:7 100:8 101:6 101:7 102:8 103:1 103:2 103:3 104:1 106:3 106:4 107:1 107:2 107:3
108:1 108:2 109:6 110:3 112:1 112:2 112:3 112:4 113:1 114:1 114:2 114:3
'''.split())


@lru_cache(maxsize=1)
def corpus():
    chapters = json.loads((DATA / 'quran-arabic.json').read_text(encoding='utf-8'))
    translations = json.loads((DATA / 'quran-de-bubenheim.json').read_text(encoding='utf-8'))['quran']
    german = {(v['chapter'], v['verse']): v['text'] for v in translations}
    result = {}
    for chapter in chapters:
        for verse in chapter['verses']:
            key = (chapter['id'], verse['id'])
            result[f'{key[0]}:{key[1]}'] = (
                verse['text'], german[key], f"{chapter['transliteration']} · {key[0]}:{key[1]}",
            )
    if len(chapters) != 114 or len(result) != 6236 or len(german) != 6236:
        raise ValueError('Incomplete Quran corpus')
    if any(not a or not g for a, g, _ in result.values()):
        raise ValueError('Empty verse')
    return result


@lru_cache(maxsize=2)
def reference_order(collection='selected'):
    references = tuple(corpus()) if collection == 'all' else SELECTED_REFERENCES
    if len(set(references)) != len(references) or any(ref not in corpus() for ref in references):
        raise ValueError('Invalid verse selection')
    # Stable shuffle across suras, with no repetition until the entire cycle ends.
    return tuple(sorted(references, key=lambda ref: hashlib.sha256(f'prayerclock-v1:{ref}'.encode()).digest()))


def verse_for_day(day, collection='selected'):
    order = reference_order(collection)
    return corpus()[order[day.toordinal() % len(order)]]
