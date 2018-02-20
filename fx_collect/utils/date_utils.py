from datetime import datetime, timedelta

def ole_zero():
    return datetime(1899,12,30)

def to_ole(pydate):
    if isinstance(pydate, datetime):
        delta = pydate - ole_zero()
        return float(delta.days) + (float(delta.seconds) / 86400)
    else:
        return pydate

def fm_ole(oletime):
    if isinstance(oletime, float):
        return ole_zero() + timedelta(days=float(oletime))
    else:
        return oletime
    
def fm_string(dt_string, millisecond=False):
    """
    Input a date string and returns a datetime object.
    """
    if millisecond:
        return datetime.strptime(
            dt_string, '%Y/%m/%d %H:%M:%S.%f')
    else:
        return datetime.strptime(
            dt_string, '%Y/%m/%d %H:%M:%S')

def switch_day(
    dt, day=6, hour=22, minute=0,
    second=0, microsecond=0,
    add_week=False, sub_week=False
):
    """
    Move date to next specified day at 22:00UTC
    """
    day_num = dt.weekday()
    days_until = (7 - day_num + day) % 7
    if add_week:
        days_until+=7
    if sub_week:
        days_until-=7
    _sunday = dt + timedelta(days=days_until)
    return _sunday.replace(
        hour=hour, minute=minute,
        second=second, microsecond=microsecond)