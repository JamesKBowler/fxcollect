from event import CleanedDataEvent

class DataCleaner(object):
    """
    Basic data cleaning
    """
    def __init__(self, events_queue):
        """
        """
        self.events_queue = events_queue
        
    def _remove_duplicates(self, data):
        """
        Drop any duplicates in the Datetime Index
        """
        return data.reset_index().drop_duplicates(
            subset='date', keep='last').set_index('date')

    def _remove_not_a_number(self, data):
        """
        Drop any rows that contain NaN values.
        """
        return data.dropna()

    def _remove_incorrect_values(
        self, data, ao='askopen',ah='askhigh', al='asklow',
        ac='askclose', bo='bidopen',bh='bidhigh', bl='bidlow',
        bc='bidclose', v='volume'
    ):
        """
        Removes errors from the open high low close values.
        """
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
        data = self._remove_not_a_number(event.data)
        data = self._remove_incorrect_values(data)
        data = self._remove_duplicates(data)
        self.events_queue.put(CleanedDataEvent(
                    data, event.instrument, event.time_frame))
