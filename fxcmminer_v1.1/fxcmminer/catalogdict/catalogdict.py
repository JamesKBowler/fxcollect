from dateutil import tz
import pytz
from datetime import datetime, timedelta

class InstrumentDictCatalog(object):
    """
    """
    def date_extract(self, offer, time_frame, catalog):
        """
        Reads the xmloffers and returns a start date.
        """
        for k, v in catalog[offer]['time-frames'].iteritems():
            if k[:1] == time_frame[:1]:
                cat_date = v['start-date']
                break
        if 'cat_date' not in locals():
            cat_date = catalog[offer]['attribs']['start-date']
        if 'cat_date' in locals():
            return self._correct_xml_date(cat_date, time_frame)
        else:
            print(
                "[:(] %s for %s cannot be found in the catalogue, "
                "you may need to add the first one manually" % (
                    offer, time_frame))
            return None

    def _correct_xml_date(self, cat_date, time_frame):
        """
        Corrects time zone and starting point.
        """
        # Time Zones
        from_zone = tz.gettz('America/New_York')
        to_zone = tz.gettz('UTC')
        # Convert EST datetime to UTC
        cat_date = datetime.strptime(cat_date, '%d.%m.%Y %H:%M:%S')
        est = cat_date.replace(tzinfo=from_zone)
        utc = est.astimezone(to_zone)
        cat_date = utc.replace(tzinfo=None)
        # Correct starting point
        if time_frame == "M1":
            # Make end of month 22:00
            cat_date = cat_date.replace(day=1, hour=22, minute=0)
            cat_date = cat_date - timedelta(days=1)
        elif time_frame == "W1":
            # Make a Saturday 22:00
            cat_date = cat_date - timedelta(
                7+((cat_date.weekday() + 1) % 7)-(5+1))
            cat_date = cat_date.replace(hour=22, minute=0)
        else:
            # Make a Sunday 22:00
            cat_date = cat_date - timedelta(
                7+((cat_date.weekday() + 1) % 7)-(6+1))
            cat_date = cat_date.replace(hour=22, minute=0)
        return cat_date
