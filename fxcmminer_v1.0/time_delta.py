class TimeDelta(object):
    """
    This object will ensure nomore than X bars of data are called
    from the API.
    """
    @staticmethod    
    def get_delta(time_frame):
        tf = time_frame
        delta = 300
        if tf == 'm1':
            td = delta
        elif tf == 'm5':
            td = 5*delta
        elif tf == 'm15':
            td = 15*delta
        elif tf == 'm30':
            td = 30*delta
        elif tf == 'H1':
            td = 60*delta
        elif tf == 'H2':
            td = 120*delta
        elif tf == 'H4':
            td = 240*delta
        elif tf == 'H8':
            td = 580*delta
        elif tf == 'H12':
            td = 720*delta
        elif tf == 'D1':
            td = 1440*delta
        elif tf == 'D3':
            td = 4320*delta
        elif tf == 'W1':
            td = 10080*delta
        elif tf == 'M1':
            td = 44640*delta

        return td
