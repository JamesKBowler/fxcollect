from event import CleanedDataEvent

class DataCleaner(object):
    """
    The DataCleaner class is the process of correcting
    (or removing) corrupt or inaccurate records from a record set
    and refers to identifying incomplete, incorrect, inaccurate
    or irrelevant parts of the data and then replacing,
    modifying, or deleting the dirty or coarse data.
    Most of the above is not implemented in the code below.
    """
    def __init__(self, events_queue):
        """ Initialize varables """
        self.events_queue = events_queue

    def _remove_duplicates(self, data):
        """ Drop any duplicates in the Datetime Index """
        return data.reset_index().drop_duplicates(
            subset='date', keep='last').set_index('date')

    def _remove_not_a_number(self, data):
        """ Drop any rows that contain NaN values """
        return data.dropna()

    def _remove_incorrect_values(
        self, data, ao='askopen',ah='askhigh', al='asklow',
        ac='askclose', bo='bidopen',bh='bidhigh', bl='bidlow',
        bc='bidclose', v='volume'
    ):
        """ Removes errors from the open high low close values """
        data = data.loc[data[ac] <= data[ah]]
        data = data.loc[data[ac] >= data[al]]
        data = data.loc[data[ao] <= data[ah]]
        data = data.loc[data[ao] >= data[al]]
        data = data.loc[data[ah] >= data[al]]
        data = data.loc[data[bc] <= data[bh]]
        data = data.loc[data[bc] >= data[bl]]
        data = data.loc[data[bo] <= data[bh]]
        data = data.loc[data[bo] >= data[bl]]
        data = data.loc[data[bh] >= data[bl]]
        data = data.loc[data[v] >= 0]
        return data

    def clean_data(self, event):
        """ Encapsulates the above cleaning processes """
        data = self._remove_not_a_number(event.data)
        data = self._remove_incorrect_values(data)
        data = self._remove_duplicates(data)
        self.events_queue.put(CleanedDataEvent(
                    data, event.instrument, event.time_frame))
