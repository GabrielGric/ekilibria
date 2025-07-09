from datetime import datetime, timedelta

def get_last_closed_week_range(today=None):
    if today is None:
        today = datetime.today()
    days_since_last_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_last_sunday)
    last_monday = last_sunday - timedelta(days=6)
    return last_monday.date(), last_sunday.date()

def get_week_ranges_until(start_date, end_date):
    """
    Genera tuplas (fecha_desde, fecha_hasta) de semanas cerradas (lunes a domingo)
    desde end_date hacia atrás hasta cubrir start_date (inclusive).
    """
    ranges = []
    current_end = end_date
    while current_end >= start_date:
        current_start = current_end - timedelta(days=6)
        ranges.append((current_start, current_end))
        current_end = current_start - timedelta(days=1)
    return list(reversed(ranges))

def get_last_n_weeks_range(n=4):
    """
    Devuelve los rangos de las últimas N semanas cerradas (por defecto 4 semanas ~1 mes).
    """
    _, last_sunday = get_last_closed_week_range()
    end_date = last_sunday
    start_date = end_date - timedelta(weeks=n) + timedelta(days=1)
    return get_week_ranges_until(start_date, end_date)
