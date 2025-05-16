
import datetime

HOLIDAYS = {
    "aprilfools": {"month": 4, "day": 1},
    "halloween":  {"month": (10, 11), "day": (29, 1)},
    "christmas":  {"month": 12, "day": (24, 31)},
}

def get_holiday():
    today_utc = datetime.datetime.now(datetime.timezone.utc).date()
    check_dates = {
        today_utc - datetime.timedelta(days=1),
        today_utc,
        today_utc + datetime.timedelta(days=1),
    }
    for name, info in HOLIDAYS.items():
        if isinstance(info["month"], int):
            start_month = end_month = info["month"]
        else:
            start_month, end_month = info["month"]
        if isinstance(info["day"], int):
            start_day = end_day = info["day"]
        else:
            start_day, end_day = info["day"]
        # check dates
        for date in check_dates:
            month, day = date.month, date.day
            if (start_month, start_day) <= (month, day) <= (end_month, end_day):
                return name
    return None
