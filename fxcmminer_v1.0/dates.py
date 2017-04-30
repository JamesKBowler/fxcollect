import datetime

class DateRange(object):
    """
    DateRange has been desinged to never return a date range during
    non-trading hours. FXCM Trading Hours : Sunday 17:00 - Friday 16:59

    If the date range falls within the exculded range, the date is moved.

    The revised date range will never exceed the MAXBARS of 300.

    This also provides more control if the API returns and empty frame.
    """
    @staticmethod
    def get_date_block(time_delta, fm_date, to_date):
        """
        This is ugly, but need to prevent the API making calls to FXCM for
        the weekend when there is no data to be collected. Also the holidays
        are mixed up and not consistant
        """
        # Setup fm_date
        if to_date != None:
            fm_date = to_date + datetime.timedelta(minutes=1)  # After

        else:
            fm_date = fm_date + datetime.timedelta(minutes=1)
            #if fm_date.year < 1970:
            #    fm_date = fm_date.replace(year=1990)  # First

        d = fm_date
        if d.weekday() == 4 and d.time() == datetime.time(16,59):  # If date is Friday 16:59
            fm_date = d  # New Date
            to_date = fm_date

        else:
            if d.weekday() == 4 and d.time() >= datetime.time(17,00):  # If date is Friday >= 17:00
                d = d + datetime.timedelta(days=2)
                fm_date = d  # New Date

            elif d.weekday() == 5: # If date is Saturday
                d = d + datetime.timedelta(days=1)
                d = d.replace(hour=17, minute=00)                    
                fm_date = d  # New Date

            elif d.weekday() == 6 and d.time() <= datetime.time(16,59):  # If date is Sunday < 16:59
                d = d.replace(hour=17, minute=00)                    
                fm_date = d  # New Date

            to_date = fm_date + datetime.timedelta(minutes=time_delta) - \
                      datetime.timedelta(minutes=1)

        # Setup to_date
            d = to_date
            if d.weekday() == 4 and d.time() > datetime.time(16,59):
                d = d.replace(hour=16, minute=59)
                to_date = d
            elif d.weekday() == 5:
                d = d - datetime.timedelta(days=1)
                d = d.replace(hour=16, minute=59)
                to_date = d
            elif d.weekday() == 6 and d.time() < datetime.time(17,00):
                d = d - datetime.timedelta(days=2)
                d = d.replace(hour=16, minute=59)
                to_date = d

        return fm_date, to_date
