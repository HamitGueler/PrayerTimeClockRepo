def is_critical_stale(last_successful_update_at, now, prayer_times_are_current, threshold):
    return (
        last_successful_update_at is not None
        and now - last_successful_update_at >= threshold
        and not prayer_times_are_current
    )


def fallback_days_remaining(last_available_date, today):
    if last_available_date is None:
        return None
    return max(0, (last_available_date - today).days)


def fallback_horizon_text(last_available_date, today):
    days = fallback_days_remaining(last_available_date, today)
    if days is None:
        return "Kein Fallback verfügbar"
    if days == 0:
        return "Fallback endet heute"
    if days == 1:
        return "Fallback noch 1 Tag verfügbar"
    return f"Fallback noch {days} Tage verfügbar"


def fallback_horizon_after_request(request_succeeded, last_available_date, today):
    """Return fallback reach only for a failed refresh attempt."""
    if request_succeeded:
        return ""
    return fallback_horizon_text(last_available_date, today)
