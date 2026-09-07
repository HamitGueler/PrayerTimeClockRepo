# Offline Quran data: attribution and terms

The two JSON files contain unabridged source text. No AI-generated translation,
paraphrase, spelling correction or verse truncation is used. Sura/aya keys join
Arabic and German; each source contains 6,236 verses in 114 suras. The app's
selection is an editorial list of references, not a religious ranking.

## Arabic

`quran-arabic.json`: Quran JSON by Risan Bagja Pradana, release family 3.1.2.
The project credits QuranEnc.com for its Uthmani Arabic Quran text.

- Dataset: https://github.com/risan/quran-json
- Original source: https://quranenc.com/en/home
- Attribution: Risan Bagja Pradana (https://risanb.com)
- Dataset license: CC BY-SA 4.0; full text in `QURAN-JSON-LICENSE.txt`.
- The Arabic Quran itself is a public-domain religious text.

## German meanings

`quran-de-bubenheim.json`: A. S. F. Bubenheim and N. Elyas, from the Tanzil
translation repository; obtained through the `deu-asfbubenheimand` edition in
fawazahmed0/quran-api. This is the Tanzil edition, **not** a claim to contain
the latest QuranEnc German revision. The direct QuranEnc export could not be
retrieved in the development environment.

- Source: https://tanzil.net/trans/de.bubenheim
- Terms: https://tanzil.net/trans/
- Mirror: https://github.com/fawazahmed0/quran-api

Tanzil's translation terms permit non-commercial use. Commercial use requires
permission from the translator or publisher. The mirror's software license
does not replace the translation's terms. This data is included for this
non-commercial prayer-clock project.

## Reproducibility

`quran-sources.json` records retrieval date, source links and SHA-256 checksums
of the packaged files. `scripts/import_quran.py` is an explicit developer
refresh command. It checks both complete datasets before replacing any file.
Review changed text, terms and attribution before publishing a refreshed copy.
No runtime request, API account, new Python library or network connection is
needed to display the packaged verses.

## Font

Amiri Quran by The Amiri Quran Project Authors (2010–2022),
https://github.com/aliftype/amiri. Obtained from Google Fonts
`ofl/amiriquran/AmiriQuran-Regular.ttf`, Git blob
`2a4de2c4fd3e6fd23656586151935a98723acaff`. SIL Open Font License 1.1,
full text in `../Fonts/AMIRI-OFL.txt`. No font modifications.

### Display encoding

The QuranEnc Arabic export uses legacy font slots U+0656/U+0657/U+065E for
open tanwin. For rendering in Amiri Quran only, these are mapped to their
Unicode open-tanwin counterparts U+08F2/U+08F0/U+08F1. The source JSON is not
changed. These mappings are documented for the Quran Complex text in
https://github.com/fawazahmed0/quran-api/blob/1/editions.json
(`ara-quranuthmanihaf`). All displayed Arabic codepoints are tested against
the bundled font; translations are displayed exactly as stored.
