import os
from datetime import timedelta


HIJRI_MONTHS = (
    "Muḥarram", "Ṣafar", "Rabīʿ al-Awwal", "Rabīʿ ath-Thānī",
    "Dschumādā al-Ūlā", "Dschumādā ath-Thāniya", "Radschab",
    "Schaʿbān", "Ramaḍān", "Schawwāl", "Dhū l-Qaʿda", "Dhū l-Ḥiddscha",
)

SACRED_MONTHS = {1, 7, 11, 12}

# A small, reviewed offline selection. One verse is selected deterministically
# per day, so no network outage can leave the kiosk with an empty panel.
DAILY_VERSES = (
    (
        "إِنَّ مَعَ الْعُسْرِ يُسْرًا",
        "Gewiss, mit der Erschwernis ist Erleichterung.",
        "Asch-Scharḥ · 94:6",
    ),
    (
        "فَاذْكُرُونِي أَذْكُرْكُمْ",
        "Gedenkt Meiner, so gedenke Ich eurer.",
        "Al-Baqarah · 2:152",
    ),
    (
        "إِنَّ اللَّهَ مَعَ الصَّابِرِينَ",
        "Gewiss, Allah ist mit den Standhaften.",
        "Al-Baqarah · 2:153",
    ),
    (
        "وَقُل رَّبِّ زِدْنِي عِلْمًا",
        "Und sag: Mein Herr, lasse mich an Wissen zunehmen.",
        "Ṭā-Hā · 20:114",
    ),
    (
        "أَلَا بِذِكْرِ اللَّهِ تَطْمَئِنُّ الْقُلُوبُ",
        "Sicherlich, im Gedenken Allahs finden die Herzen Ruhe.",
        "Ar-Raʿd · 13:28",
    ),
)


def get_hijri_info(value, adjustment=None):
    """Return adjusted Hijri date and display metadata.

    HIJRI_DATE_ADJUSTMENT may be -1, 0, or 1 and lets a mosque align the
    calculated Umm al-Qura date with its locally adopted calendar.
    """
    from hijridate import Gregorian

    if adjustment is None:
        try:
            # The Berlin mosque calendar used by this clock is one day behind
            # Umm al-Qura by default. The settings page can override this.
            adjustment = int(os.getenv("HIJRI_DATE_ADJUSTMENT", "-1"))
        except ValueError:
            adjustment = -1
    adjustment = max(-2, min(2, adjustment))
    adjusted = value + timedelta(days=adjustment)
    hijri = Gregorian(adjusted.year, adjusted.month, adjusted.day).to_hijri()
    month_name = HIJRI_MONTHS[hijri.month - 1]
    return {
        "date": f"{hijri.day}. {month_name} {hijri.year} AH",
        "day": hijri.day,
        "month": hijri.month,
        "month_name": month_name,
        "year": hijri.year,
        "event": special_day_status(hijri.day, hijri.month),
        "sacred_month": hijri.month in SACRED_MONTHS,
    }


def daily_verse(value):
    return DAILY_VERSES[value.toordinal() % len(DAILY_VERSES)]


def _deduplicate_fasting_recommendation(tags):
    """Keep every reason, but show the fasting recommendation only once."""
    fasting_recommended = False
    deduplicated = []
    for tag in tags:
        for suffix in (" · FASTEN EMPFOHLEN", " · FASTEN EINPLANEN"):
            if tag.endswith(suffix):
                tag = tag.removesuffix(suffix)
                fasting_recommended = True
                break
        if tag and tag not in deduplicated:
            deduplicated.append(tag)
    if fasting_recommended:
        deduplicated.append("FASTEN EMPFOHLEN")
    return deduplicated


def _voluntary_fasting_indicator_allowed(day, month):
    """Avoid voluntary-fasting prompts during Ramadan, Eid and Tashriq."""
    return month != 9 and (month, day) not in {(10, 1), (12, 10), (12, 11), (12, 12), (12, 13)}


def special_day_statuses(day, month, weekday=None):
    """Return all matching current-day tag texts, ordered by importance."""
    statuses = []
    if weekday == 4:
        statuses.append("JUMUʿAH")
    if month == 1 and day == 9:
        statuses.append("TĀSŪʿĀʾ · FASTEN EMPFOHLEN")
    if month == 1 and day == 10:
        statuses.append("ʿĀSCHŪRĀʾ · FASTEN EMPFOHLEN")
    if month == 9 and day == 1:
        statuses.append("ERSTER TAG RAMAḌĀN")
    if month == 9 and day in (21, 23, 25, 27, 29):
        statuses.append(f"{day}. NACHT · LAYLAT AL-QADR SUCHEN")
    if month == 9 and 21 <= day <= 30:
        statuses.append("LETZTE ZEHN NÄCHTE RAMAḌĀN")
    if month == 10 and day == 1:
        statuses.append("ʿĪD AL-FIṬR")
    if month == 12 and day == 9:
        statuses.append("ʿARAFAH · FASTEN EMPFOHLEN")
    if month == 12 and day == 10:
        statuses.append("ʿĪD AL-AḌḤĀ")
    if month == 12 and 1 <= day <= 10:
        statuses.insert(0, f"{day}. TAG VON DHŪ L-ḤIDDSCHA")
    if day in (13, 14, 15) and _voluntary_fasting_indicator_allowed(day, month):
        statuses.append(f"{day}. WEISSER TAG · FASTEN EMPFOHLEN")
    return _deduplicate_fasting_recommendation(statuses)


def uses_celebration_palette(day, month):
    """Return whether the day should use the rare gold-and-white visual state."""
    return (
        (month, day) in {(1, 10), (9, 1), (10, 1), (12, 9), (12, 10)}
        or (month == 9 and day in (21, 23, 25, 27, 29))
        or (month == 12 and 1 <= day <= 10)
    )


def special_day_status(day, month, weekday=None):
    """Return one shared heading followed by every matching current-day tag."""
    statuses = special_day_statuses(day, month, weekday)
    return f"HEUTE · | {' | | '.join(statuses)} |" if statuses else ""


def special_day_tomorrow_notices(day, month, weekday=None):
    """Return all matching preparation tag texts, ordered by importance."""
    notices = []
    voluntary_fasting_allowed = _voluntary_fasting_indicator_allowed(day, month)
    if weekday == 0 and voluntary_fasting_allowed:
        notices.append("MONTAG · FASTEN EMPFOHLEN")
    elif weekday == 3 and voluntary_fasting_allowed:
        notices.append("DONNERSTAG · FASTEN EMPFOHLEN")
    elif weekday == 4:
        notices.append("JUMUʿAH")
    if month == 1 and day == 9:
        notices.append("TĀSŪʿĀʾ · FASTEN EINPLANEN")
    if month == 1 and day == 10:
        notices.append("ʿĀSCHŪRĀʾ · FASTEN EINPLANEN")
    if month == 9 and day == 1:
        notices.append("RAMAḌĀN BEGINNT")
    if month == 9 and day == 21:
        notices.append("LETZTE 10 NÄCHTE BEGINNEN")
    if month == 9 and day in (23, 25, 27, 29):
        notices.append(f"{day}. NACHT · LAYLAT AL-QADR SUCHEN")
    if month == 9 and 21 <= day <= 30:
        notices.append("LETZTE ZEHN NÄCHTE RAMAḌĀN")
    if month == 10 and day == 1:
        notices.append("ʿĪD AL-FIṬR")
    if month == 12 and day == 1:
        notices.append("DIE BESTEN 10 TAGE BEGINNEN")
    if month == 12 and day == 9:
        notices.append("ʿARAFAH · FASTEN EINPLANEN")
    if month == 12 and day == 10:
        notices.append("ʿĪD AL-AḌḤĀ")
    if month == 12 and 1 <= day <= 10:
        notices.insert(0, f"{day}. TAG VON DHŪ L-ḤIDDSCHA")
    if day in (13, 14, 15) and voluntary_fasting_allowed:
        notices.append(f"{day}. WEISSER TAG · FASTEN EINPLANEN")
    return _deduplicate_fasting_recommendation(notices)


def special_day_tomorrow_notice(day, month, weekday=None):
    """Return all preparation tags; MORGEN is already the panel heading."""
    notices = special_day_tomorrow_notices(day, month, weekday)
    return f"| {' | | '.join(notices)} |" if notices else ""


def tomorrow_notice(value):
    """Return all preparation notices for tomorrow."""
    tomorrow = value + timedelta(days=1)
    info = get_hijri_info(tomorrow)
    return special_day_tomorrow_notice(info["day"], info["month"], tomorrow.weekday())
