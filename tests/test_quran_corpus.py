import hashlib
import json
from datetime import date, timedelta
from HelperClasses.QuranCorpus import DATA, corpus, reference_order, verse_for_day


def test_complete_original_corpus_and_exact_arabic_german_pairing():
    verses = corpus()
    assert len(verses) == 6236
    assert len({ref.split(':')[0] for ref in verses}) == 114
    assert 'Erschwernis' in verses['94:6'][1]
    assert 'Wissen' in verses['20:114'][1]
    originals = json.loads((DATA / 'quran-de-bubenheim.json').read_text())['quran']
    assert all(verses[f"{v['chapter']}:{v['verse']}"][1] == v['text'] for v in originals)


def test_daily_selection_is_stable_and_does_not_repeat_within_cycle():
    day = date(2026, 9, 7)
    for mode in ('selected', 'all'):
        order = reference_order(mode)
        assert len(order) >= 100
        seen = [verse_for_day(day + timedelta(days=i), mode)[2] for i in range(len(order))]
        assert len(set(seen)) == len(order)
        assert verse_for_day(day, mode) == verse_for_day(day + timedelta(days=len(order)), mode)


def test_snapshot_checksums_match_packaged_files():
    manifest = json.loads((DATA / 'quran-sources.json').read_text())
    for name, entry in manifest['files'].items():
        assert hashlib.sha256((DATA / name).read_bytes()).hexdigest() == entry['sha256']


def test_longest_verse_stays_complete_in_scrollable_panel(qapp):
    from PyViews.QuranQuotePanel import QuranQuotePanel, arabic_display_text
    panel = QuranQuotePanel()
    panel.setFixedSize(1000, 132)
    original = corpus()['2:282']
    panel.set_verse(*original)
    panel.show()
    qapp.processEvents()
    assert panel.arabic.text() == arabic_display_text(original[0])
    assert panel.translation.text() == original[1]
    assert panel.scroll.verticalScrollBar().maximum() > 0
    assert panel.reference.isVisible()
    assert panel.height() == 132
    panel.close()
    panel.deleteLater()


def test_bundled_font_covers_every_displayed_quran_character(qapp):
    from PySide6.QtGui import QRawFont
    from PyViews.QuranQuotePanel import arabic_display_text
    font = QRawFont(str(DATA.parent / 'Fonts' / 'AmiriQuran-Regular.ttf'), 36)
    characters = {c for arabic, _, _ in corpus().values() for c in arabic_display_text(arabic) if not c.isspace()}
    assert font.isValid()
    assert all(font.supportsCharacter(ord(c)) for c in characters)
