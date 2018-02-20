import json


offers = [
    'HKG33', 'EUR/SEK', 'CAD/CHF', 'AUS200', 'USD/NOK', 'EUSTX50', 'USD/CAD', 'CHF/JPY', 'EUR/AUD',
    'GBP/CAD', 'EUR/USD', 'GBP/CHF', 'USOil', 'NZD/CAD', 'USDOLLAR', 'EUR/NZD',
    'US30', 'Copper', 'Bund', 'GBP/USD', 'ESP35', 'EUR/CHF', 'USD/ZAR', 'USD/SEK', 'EUR/NOK',
    'GBP/JPY', 'GER30', 'SPX500', 'NZD/USD', 'XAU/USD', 'AUD/CAD', 'USD/HKD', 'UKOil', 'TRY/JPY',
    'USD/CNH', 'GBP/AUD', 'USD/CHF', 'CAD/JPY', 'XAG/USD', 'AUD/JPY', 'AUD/CHF', 'EUR/JPY',
    'UK100', 'USD/TRY', 'EUR/TRY', 'NZD/CHF', 'EUR/CAD', 'AUD/USD', 'NAS100', 'FRA40', 'GBP/NZD',
    'USD/MXN', 'EUR/GBP', 'ZAR/JPY', 'AUD/NZD', 'NZD/JPY', 'JPN225', 'USD/JPY', 'NGAS'
]

def print_json_files(offers):
    all_string = ""
    for i in enumerate(offers, 1):
        no, offer = i
        file_loc = "/home/nonroot/fxcollect/json_files/{}.json".format(offer.replace('/',''))
        try:
            with open(file_loc) as f:
                result = json.load(f)
            time_frames = result[offer]['time_frames']
            market_status = result[offer]['market_status']
            if market_status == 'O':
                ms = 'Open'
            else:
                ms = 'Closed'
            base = result[offer]['base']
            last_update = result[offer]['last_update']
            ask = result[offer]['ask']
            bid = result[offer]['bid']
            header = "\n{0: <{width}} : {1}\n".format(
                offer, no, width=9)
            contract = "{0: <{width}} : {1}\n".format("Base", base, width=9)    
            s = "{0: <{width}} : {1}\n".format("Status", ms, width=9)
            update = "{0: <{width}} : {1}\n".format("Time", last_update, width=9)
            b = "{0: <{width}} : {1} \n".format(
                "Bid", bid, width=9)
            a = "{0: <{width}} : {1} \n".format(
                "Ask", ask, width=9)
            time_frame_values = header + contract + update + s + b+ a
            for tf, v in time_frames.items():
                s = '{0: <{width}}: {1} {2}\n'.format(tf,v['db_min'], v['db_max'], width=10)
                time_frame_values+=s
        except FileNotFoundError:
            pass
        all_string+=time_frame_values
    print(all_string)

print_json_files(offers)
