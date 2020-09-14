import datetime

from strategy.trendlinestrategy import TrendlineStrategy
from zerodha.zeroda_intraday_backtester import ZerodhaServiceIntraDay
from db import storage

"""
Trading System to Automate the Strategy execution in DB
1. It can listen to the tick data for a list of stock from the CSV File
2. It can insert the tick data into DB
3. It can execute the configured Strategy For specific stock
4. It can execute a default trading strategy

5. Risk management
6. Ordering Management - Can Resume the system from where it stopped.
7. Support the multiple trading platform

"""

class TradingAPI(object):
    def __init__(self, credential, configuration, tradeRunner):
        # self.credential = credential
        self.tradeRunner = self._get_trading_service(credential, configuration, tradeRunner)

    def _get_trading_service(self, credential, configuration, tradeRunner):
        return tradeRunner(credential, configuration)

    def on_tick_update(self, callback_function):
        self.tradeRunner.on_tick_update(callback_function)

    def on_day_closure(self, callback_function):
        self.tradeRunner.on_day_closure(callback_function)

    def place_order(self, order_details):
        pass

    def run(self):
        self.tradeRunner.init_listening()
        pass


class RiskManagement:
    def __init__(self):
        pass


#             self.balance = balance
#         def deduct(self):


class TradingSystem(object):

    def __init__(self, credential, configuration, tradeRunner, stratagies):
        self.stratagies = stratagies
        self.tradingAPI = TradingAPI(credential, configuration, tradeRunner)
        self.tradingAPI.on_tick_update(self.record_in_db)
        self.tradingAPI.on_tick_update(self.strategy_runner)
        self.tradingAPI.on_day_closure(self.day_closure)
        self.riskmanagement = RiskManagement()

    def run(self):
        self.tradingAPI.run()

    def __get_ohlc(self, ohlc1, ohlc2):
        ohlc_new = {}
        ohlc_new['low'] = min(ohlc1['low'], ohlc2['low'])
        ohlc_new['high'] = max(ohlc1['high'], ohlc2['high'])
        ohlc_new['open'] = ohlc1['open']
        ohlc_new['close'] = ohlc2['close']

        # ohlc_new['volume'] = ohlc1['volume'] + ohlc2['volume']
        return ohlc_new

    def day_closure(self, date, instrument_token):
        for strategy in self.stratagies:
            strategy.close_day(date, instrument_token)

    def summery(self):
        for strategy in self.stratagies:
            strategy.summary()

    def record_in_db(self, td, timestamp):
        # Recording data in DB[{'tradable': True, 'mode': 'quote', 'instrument_token': 5633, 'last_price': 1357.85, 'last_quantity': 25, 'average_price': 1346.6, 'volume': 713412, 'buy_quantity': 226, 'sell_quantity': 0, 'ohlc': {'open': 1333.0, 'high': 1361.8, 'low': 1326.65, 'close': 1338.65}, 'change': 1.4342808052888967}]
        tick_data = td[0]
        it = tick_data['instrument_token']
        ohlc = tick_data['ohlc']
        current_time = timestamp.replace(second=0, microsecond=0)
        storage.get_db().setdefault(it, {"1minute": {}, "5minute": {}})

        for agg_type in [1, 5]:
            agg_key = str(agg_type) + "minute"
            agg_data = storage.get_db()[it][agg_key]
            last_agg_minute = (int(timestamp.minute / agg_type)) * agg_type
            agg_datetime = timestamp.replace(minute=last_agg_minute, second=0, microsecond=0)

            if agg_datetime in agg_data:
                updated_agg = self.__get_ohlc(agg_data[agg_datetime], ohlc)
                agg_data[agg_datetime] = updated_agg
                updated_agg['date'] = agg_datetime
            else:
                agg_data[current_time] = ohlc

        # print("Recording data in DB" + str(tick_data))

    def strategy_runner(self, tick_data, timestamp):
        for strategy in self.stratagies:
            order_details = strategy.run(tick_data, self.riskmanagement, timestamp)
            if order_details != None:
                break
        pass


def play_casino():
    api_key = 'f6jdkd2t30tny1x8'
    api_secret = 'eiuq7ln5pp8ae6uc6cjulhap3zc3bsdo'
    storage.init()
    top_n = 50
    # "INDIGO".split(" ") #
    stocks = "RELIANCE TCS HINDUNILVR HDFCBANK HDFC INFY KOTAKBANK BHARTIARTL ITC ICICIBANK SBIN ASIANPAINT DMART BAJFINANCE MARUTI HCLTECH LT WIPRO AXISBANK ULTRACEMCO HDFCLIFE COALINDIA ONGC SUNPHARMA NTPC POWERGRID TITAN DABUR IOC BAJAJFINSV PIDILITIND BPCL HINDZINC BRITANNIA SBILIFE SHREECEM BAJAJ-AUTO SBICARD TECHM GODREJCP DIVISLAB DRREDDY ICICIPRULI ADANIPORTS ICICIGI BERGEPAINT HDFCAMC GSKCONS INDIGO SIEMENS EICHERMOT MARICO M&M JSWSTEEL MCDOWELL-N GAIL CIPLA COLPAL DLF TORNTPHARM PGHH BANDHANBNK BIOCON HEROMOTOCO GRASIM AMBUJACEM TATASTEEL HAVELLS PETRONET INFRATEL HINDPETRO YESBANK ALKEM BOSCHLTD CADILAHC IGL LUPIN UPL NAUKRI LTI BANKBARODA MRF MUTHOOTFIN NMDC INDUSINDBK UBL PFC AUROPHARMA VEDL ADANIGREEN WHIRLPOOL HONAUT TATAMOTORS PNB HINDALCO GLAXO 3MINDIA PEL KANSAINER ADANITRANS CONCOR NHPC IDBI BAJAJHLDNG ABB JUBLFOOD MOTHERSUMI PAGEIND TATACONSUM NIACL GICRE PFIZER ACC BEL GILLETTE IPCALAB RECLTD HAL OFSS TRENT RAJESHEXPO PIIND SRF COROMANDEL GUJGASLTD APOLLOHOSP BATAINDIA VOLTAS IRCTC BALKRISIND VBL NAM-INDIA GODREJPROP ADANIENT SRTRANSFIN RELAXO AUBANK SANOFI TVSMOTOR ASTRAL MINDTREE TORNTPOWER SUNDARMFIN AARTIIND AIAENG CROMPTON ASHOKLEY MPHASIS LTTS RAMCOCEM OBEROIRLTY CHOLAFIN AJANTPHARM ZEEL LICHSGFIN ATUL ABFRL LALPATHLAB WABCOINDIA SCHAEFFLER SUNTV EXIDEIND POLYCAB SUPREMEIND BHARATFORG ADANIPOWER BANKINDIA MFSL L&TFH IDFCFIRSTB AKZOINDIA APLLTD GMRINFRA CASTROLIND UNIONBANK ABCAPITAL GSPL SYNGENE GODREJIND FORTIS SAIL ADANIGAS CUB DALBHARAT CANBK AAVAS SUMICHEM NATCOPHARM M&MFIN CRISIL CUMMINSIND OIL IDEA ISEC INDHOTEL TATAPOWER IOB THERMAX IIFLWAM PHOENIXLTD ENDURANCE JINDALSTEL HATSUN SOLARINDS FEDERALBNK AMARAJABAT SJVN ESCORTS MGL MANAPPURAM VINATIORGA UCOBANK EMAMILTD ZYDUSWELL MOTILALOFS SKFINDIA BHEL JKCEMENT NIITTECH GODREJAGRO JSWENERGY CENTRALBK RBLBANK HEXAWARE TTKPRESTIG PRESTIGE TATACOMM VGUARD METROPOLIS SIS MINDAIND SFL RITES SUNDRMFAST NLCINDIA PVR NAVINFLUOR PGHL ASTRAZEN KAJARIACER FINEORG JCHAC GLENMARK TIMKEN TATACHEM IBVENTURES ITI INDIAMART SYMPHONY JMFINANCIL CHOLAHLDNG NATIONALUM CESC DEEPAKNTR BLUEDART MAHABANK TIINDIA BBTC ERIS NH GRINDWELL SHRIRAMCIT ESSELPACK GODFRYPHLP FINPIPE BASF CREDITACC ASTERDM KEC AEGISCHEM UJJIVANSFB APOLLOTYRE CHAMBLFERT BLUESTARCO VSTIND RATNAMANI PERSISTENT CHALET CARBORUNIV GALAXYSURF ORIENTELEC DIXON LINDEINDIA IBULHSGFIN JBCHEPHARM MRPL AVANTIFEED HUDCO JUBILANT FRETAIL TATAELXSI AMBER IEX ASAHIINDIA ENGINERSIN SPANDANA EIHOTEL CANFINHOME KIOCL GMMPFAUDLR GRANULES VTL EDELWEISS IRCON RADICO COCHINSHIP LAURUSLABS NESCO RALLIS VIPIND BDL JYOTHYLAB DCMSHRIRAM TATAINVEST MIDHANI FDC CENTURYTEX INDIACEM HEIDELBERG CEATLTD BIRLACORPN GEPIL POWERINDIA KRBL QUESS FLUOROCHEM FINCABLES APLAPOLLO SUNTECK BAJAJELEC GESHIP SUNCLAYLTD CERA CGCL DCBBANK NBCC GPPL DBL STAR MASFIN KALPATPOWR STARCEMENT OMAXE TEAMLEASE KNRCON PNBHOUSING INOXLEISUR TV18BRDCST REDINGTON RVNL BRIGADE INDIANB THYROCARE TECHNOE MAHINDCIE VMART GULFOILLUB SUDARSCHEM STRTECH AFFLE SUVENPHAR SPARC CYIENT GRAPHITE VAIBHAVGBL CENTURYPLY SWANENERGY EIDPARRY LAXMIMACH ALKYLAMINE MOIL PNCINFRA KEI LUXIND HATHWAY FLFL IIFL IDFC CCL GARFIBRES MAHSCOOTER KPRMILL JKLAKSHMI TASTYBITE INDOSTAR BALRAMCHIN INFIBEAM CDSL BHARATRAS WELSPUNIND RESPONIND TRIDENT KSCL CAPLIPOINT VAKRANGEE TCIEXP ICRA POLYMED CSBBANK TCNSBRANDS SHILPAMED ZENSARTECH HINDCOPPER BAJAJCON INGERRAND INDOCO NETWORK18 SEQUENT WOCKPHARMA JUSTDIAL FSL TRITURBINE BEML RAIN IRB HEG MHRIL IBREALEST MMTC GET&D UJJIVAN TATASTLBSL FMGOETZE GNFC ELGIEQUIP DELTACORP SCI LEMONTREE SONATSOFTW VARROC BSOFT SHOPERSTOP ESABINDIA VESUVIUS MAXINDIA GUJALKALI LAOPALA MAHLOG WELCORP FAIRCHEM KARURVYSYA GREAVESCOT JSWHL ADVENZYMES SUPRAJIT SCHNEIDER GRSE RCF DHANUKA PRSMJOHNSN NILKAMAL KSB NAVNETEDUL PAPERPROD JINDALSAW EQUITAS GSFC DEN TCI RAYMOND ALLCARGO ORIENTREF FCONSUMER VRLLOG DBCORP BALMLAWRIE ECLERX JAGRAN BSE JKPAPER MINDACORP KTKBANK MAHSEAMLES ACCELYA SOBHA KIRLOSENG SUPPETRO SWSOLAR HSCL GAEL GREENLAM VENKEYS JSL AARTIDRUGS PSPPROJECT DIAMONDYD NIITLTD HFCL ASHOKA SOLARA ARVINDFASN AHLUCONT PTC HGINFRA PRINCEPIPE NCC FACT TIDEWATER ITDC APARINDS".split(
        " ")[200:250]
    stock_input = dict((s, {"from": "2019-12-01", "to": "2019-12-31"}) for s in stocks)
    tradingSystem = TradingSystem({"api_key": api_key, "api_secret": api_secret}, {
        "back_testing_config": {"stocks_config": stock_input}},
                                  ZerodhaServiceIntraDay, [TrendlineStrategy()])  #
    # tradingSystem = TradingSystem({"api_key": api_key, "api_secret": api_secret}, {
    #     "back_testing_config": {"stocks_config": {"ZEEL": {"from": "2020-08-18", "to": "2020-09-04"}}}},
    #                               ZerodhaServiceIntraDay, [TrendlineStrategy()]) #
    tradingSystem.run()
    tradingSystem.summery()

#Uncomment to profile the code 
# import yappi
# yappi.set_clock_type("cpu") # Use set_clock_type("wall") for wall time
# yappi.start()
play_casino()
# yappi.get_func_stats().print_all()
# yappi.get_thread_stats().print_all()