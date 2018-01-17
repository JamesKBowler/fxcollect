from dateutil import tz
import pytz
from datetime import datetime, timedelta

class InstrumentDictCatalog(object):
    """
    The InstrumentDictCatalog provides an interface for extracing
    instrument attributes from a python dictionary created by
    the XMLCatalogue class.
    """
    def date_extract(self, offer, time_frame, catalog):
        """
        Each instrument at FXCM has a documented starting point,
        this method will extract a starting date for the historical
        data collection process.
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
        The dates within the xml catalogue are EST and in order
        provide the data collection process with a correct starting
        point, the times are converted to UTC and the day according
        to the time frame. For instance, weekly data is collected
        every Saturday, Monthly on the last day of each month
        and all other time frames start on Sunday.
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
