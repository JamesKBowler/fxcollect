# The MIT License (MIT)
#
# Copyright (c) 2017 James K Bowler, Data Centauri Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from datetime import datetime, timedelta
import pytz

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

def new_york_offset(dt):
    """
    Adjusts the time based on the US/Eastern timezone,
    for New York opening.
    """
    offset = 0
    newyork = pytz.timezone('US/Eastern')
    nydt = newyork.localize(dt, is_dst=None)
    assert nydt.tzinfo is not None
    assert nydt.tzinfo.utcoffset(nydt) is not None
    isdst = bool(nydt.dst())
    if isdst:
        offset = 1
    return dt - timedelta(hours=offset)

def end_of_next_month(dt):
    """
    Return the end of the next month
    """
    month = dt.month + 2
    year = dt.year
    if month > 12:
        next_month = month - 12
        year+=1
    else:
        next_month = month
    return (
        dt.replace(
            year=year, month=next_month, day=1
        ) - timedelta(days=1)
    )

def end_of_month(dt):
    """
    Return the end of the current month
    """
    month = dt.month + 1
    year = dt.year
    if month > 12:
        month = 1
        year+=1
    return (
        dt.replace(
            year=year, month=month, day=1
        ) - timedelta(days=1)
    )

def end_of_last_month(dt):
    """
    Return the end of last month.
    """
    return dt.replace(day=1) - timedelta(days=1)
