import argparse
from strategy.trendlinestrategy import TrendlineStrategy
from broker.zerodha.zerodha_live_trading import ZerodhaServiceOnline
from broker.zerodha.zeroda_intraday_backtester import ZerodhaServiceIntraDay
from db import storage
from tradingsystem.tradingsystem import TradingSystem
from db.storage import StorageHandler
from db.tradebook import TradeBook
from trading_options import TradingOptions
import time
from broker.indan_stock import is_holiday, get_datetime
import datetime

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
import logging

logging.basicConfig(filename='./automatedtrader.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def play_casino():
    api_key = 'f6jdkd2t30tny1x8'
    api_secret = 'eiuq7ln5pp8ae6uc6cjulhap3zc3bsdo'

    sh = StorageHandler()

    top_n = 50
    # "INDIGO".split(" ") #

    # stocks = ["JINDALSTEL"]

    # option1- uncomment
    stocks = "RELIANCE TCS HINDUNILVR HDFCBANK HDFC INFY KOTAKBANK BHARTIARTL ITC ICICIBANK SBIN ASIANPAINT DMART BAJFINANCE MARUTI HCLTECH LT WIPRO AXISBANK ULTRACEMCO HDFCLIFE COALINDIA ONGC SUNPHARMA NTPC POWERGRID TITAN DABUR IOC BAJAJFINSV PIDILITIND BPCL HINDZINC BRITANNIA SBILIFE SHREECEM BAJAJ-AUTO SBICARD TECHM GODREJCP DIVISLAB DRREDDY ICICIPRULI ADANIPORTS ICICIGI BERGEPAINT HDFCAMC GSKCONS INDIGO SIEMENS EICHERMOT MARICO M&M JSWSTEEL MCDOWELL-N GAIL CIPLA COLPAL DLF TORNTPHARM PGHH BANDHANBNK BIOCON HEROMOTOCO GRASIM AMBUJACEM TATASTEEL HAVELLS PETRONET INFRATEL HINDPETRO YESBANK ALKEM BOSCHLTD CADILAHC IGL LUPIN UPL NAUKRI LTI BANKBARODA MRF MUTHOOTFIN NMDC INDUSINDBK UBL PFC AUROPHARMA VEDL ADANIGREEN WHIRLPOOL HONAUT TATAMOTORS PNB HINDALCO GLAXO 3MINDIA PEL KANSAINER ADANITRANS CONCOR NHPC IDBI BAJAJHLDNG ABB JUBLFOOD MOTHERSUMI PAGEIND TATACONSUM NIACL GICRE PFIZER ACC BEL GILLETTE IPCALAB RECLTD HAL OFSS TRENT RAJESHEXPO PIIND SRF COROMANDEL GUJGASLTD APOLLOHOSP BATAINDIA VOLTAS IRCTC BALKRISIND VBL NAM-INDIA GODREJPROP ADANIENT SRTRANSFIN RELAXO AUBANK SANOFI TVSMOTOR ASTRAL MINDTREE TORNTPOWER SUNDARMFIN AARTIIND AIAENG CROMPTON ASHOKLEY MPHASIS LTTS RAMCOCEM OBEROIRLTY CHOLAFIN AJANTPHARM ZEEL LICHSGFIN ATUL ABFRL LALPATHLAB WABCOINDIA SCHAEFFLER SUNTV EXIDEIND POLYCAB SUPREMEIND BHARATFORG ADANIPOWER BANKINDIA MFSL L&TFH IDFCFIRSTB AKZOINDIA APLLTD GMRINFRA CASTROLIND UNIONBANK ABCAPITAL GSPL SYNGENE GODREJIND FORTIS SAIL ADANIGAS CUB DALBHARAT CANBK AAVAS SUMICHEM NATCOPHARM M&MFIN CRISIL CUMMINSIND OIL IDEA ISEC INDHOTEL TATAPOWER IOB THERMAX IIFLWAM PHOENIXLTD ENDURANCE JINDALSTEL HATSUN SOLARINDS FEDERALBNK AMARAJABAT SJVN ESCORTS MGL MANAPPURAM VINATIORGA UCOBANK EMAMILTD ZYDUSWELL MOTILALOFS SKFINDIA BHEL JKCEMENT NIITTECH GODREJAGRO JSWENERGY CENTRALBK RBLBANK HEXAWARE TTKPRESTIG PRESTIGE TATACOMM VGUARD METROPOLIS SIS MINDAIND SFL RITES SUNDRMFAST NLCINDIA PVR NAVINFLUOR PGHL ASTRAZEN KAJARIACER FINEORG JCHAC GLENMARK TIMKEN TATACHEM IBVENTURES ITI INDIAMART SYMPHONY JMFINANCIL CHOLAHLDNG NATIONALUM CESC DEEPAKNTR BLUEDART MAHABANK TIINDIA BBTC ERIS NH GRINDWELL SHRIRAMCIT ESSELPACK GODFRYPHLP FINPIPE BASF CREDITACC ASTERDM KEC AEGISCHEM UJJIVANSFB APOLLOTYRE CHAMBLFERT BLUESTARCO VSTIND RATNAMANI PERSISTENT CHALET CARBORUNIV GALAXYSURF ORIENTELEC DIXON LINDEINDIA IBULHSGFIN JBCHEPHARM MRPL AVANTIFEED HUDCO JUBILANT FRETAIL TATAELXSI AMBER IEX ASAHIINDIA ENGINERSIN SPANDANA EIHOTEL CANFINHOME KIOCL GMMPFAUDLR GRANULES VTL EDELWEISS IRCON RADICO COCHINSHIP LAURUSLABS NESCO RALLIS VIPIND BDL JYOTHYLAB DCMSHRIRAM TATAINVEST MIDHANI FDC CENTURYTEX INDIACEM HEIDELBERG CEATLTD BIRLACORPN GEPIL POWERINDIA KRBL QUESS FLUOROCHEM FINCABLES APLAPOLLO SUNTECK BAJAJELEC GESHIP SUNCLAYLTD CERA CGCL DCBBANK NBCC GPPL DBL STAR MASFIN KALPATPOWR STARCEMENT OMAXE TEAMLEASE KNRCON PNBHOUSING INOXLEISUR TV18BRDCST REDINGTON RVNL BRIGADE INDIANB THYROCARE TECHNOE MAHINDCIE VMART GULFOILLUB SUDARSCHEM STRTECH AFFLE SUVENPHAR SPARC CYIENT GRAPHITE VAIBHAVGBL CENTURYPLY SWANENERGY EIDPARRY LAXMIMACH ALKYLAMINE MOIL PNCINFRA KEI LUXIND HATHWAY FLFL IIFL IDFC CCL GARFIBRES MAHSCOOTER KPRMILL JKLAKSHMI TASTYBITE INDOSTAR BALRAMCHIN INFIBEAM CDSL BHARATRAS WELSPUNIND RESPONIND TRIDENT KSCL CAPLIPOINT VAKRANGEE TCIEXP ICRA POLYMED CSBBANK TCNSBRANDS SHILPAMED ZENSARTECH HINDCOPPER BAJAJCON INGERRAND INDOCO NETWORK18 SEQUENT WOCKPHARMA JUSTDIAL FSL TRITURBINE BEML RAIN IRB HEG MHRIL IBREALEST MMTC GET&D UJJIVAN TATASTLBSL FMGOETZE GNFC ELGIEQUIP DELTACORP SCI LEMONTREE SONATSOFTW VARROC BSOFT SHOPERSTOP ESABINDIA VESUVIUS MAXINDIA GUJALKALI LAOPALA MAHLOG WELCORP FAIRCHEM KARURVYSYA GREAVESCOT JSWHL ADVENZYMES SUPRAJIT SCHNEIDER GRSE RCF DHANUKA PRSMJOHNSN NILKAMAL KSB NAVNETEDUL PAPERPROD JINDALSAW EQUITAS GSFC DEN TCI RAYMOND ALLCARGO ORIENTREF FCONSUMER VRLLOG DBCORP BALMLAWRIE ECLERX JAGRAN BSE JKPAPER MINDACORP KTKBANK MAHSEAMLES ACCELYA SOBHA KIRLOSENG SUPPETRO SWSOLAR HSCL GAEL GREENLAM VENKEYS JSL AARTIDRUGS PSPPROJECT DIAMONDYD NIITLTD HFCL ASHOKA SOLARA ARVINDFASN AHLUCONT PTC HGINFRA PRINCEPIPE NCC FACT TIDEWATER ITDC APARINDS".split(
        " ")[0:50]
    stock_input = dict((s, {"from": "2020-09-01", "to": "2020-09-30"}) for s in stocks)

    # option2- uncomment
    # stocks = "RELIANCE TCS HINDUNILVR HDFCBANK HDFC INFY KOTAKBANK BHARTIARTL ITC ICICIBANK SBIN ASIANPAINT DMART BAJFINANCE MARUTI HCLTECH LT WIPRO AXISBANK ULTRACEMCO HDFCLIFE COALINDIA ONGC SUNPHARMA NTPC POWERGRID TITAN DABUR IOC BAJAJFINSV PIDILITIND BPCL HINDZINC BRITANNIA SBILIFE SHREECEM BAJAJ-AUTO SBICARD TECHM GODREJCP DIVISLAB DRREDDY ICICIPRULI ADANIPORTS ICICIGI BERGEPAINT HDFCAMC GSKCONS INDIGO SIEMENS EICHERMOT MARICO M&M JSWSTEEL MCDOWELL-N GAIL CIPLA COLPAL DLF TORNTPHARM PGHH BANDHANBNK BIOCON HEROMOTOCO GRASIM AMBUJACEM TATASTEEL HAVELLS PETRONET INFRATEL HINDPETRO YESBANK ALKEM BOSCHLTD CADILAHC IGL LUPIN UPL NAUKRI LTI BANKBARODA MRF MUTHOOTFIN NMDC INDUSINDBK UBL PFC AUROPHARMA VEDL ADANIGREEN WHIRLPOOL HONAUT TATAMOTORS PNB HINDALCO GLAXO 3MINDIA PEL KANSAINER ADANITRANS CONCOR NHPC IDBI BAJAJHLDNG ABB JUBLFOOD MOTHERSUMI PAGEIND TATACONSUM NIACL GICRE PFIZER ACC BEL GILLETTE IPCALAB RECLTD HAL OFSS TRENT RAJESHEXPO PIIND SRF COROMANDEL GUJGASLTD APOLLOHOSP BATAINDIA VOLTAS IRCTC BALKRISIND VBL NAM-INDIA GODREJPROP ADANIENT SRTRANSFIN RELAXO AUBANK SANOFI TVSMOTOR ASTRAL MINDTREE TORNTPOWER SUNDARMFIN AARTIIND AIAENG CROMPTON ASHOKLEY MPHASIS LTTS RAMCOCEM OBEROIRLTY CHOLAFIN AJANTPHARM ZEEL LICHSGFIN ATUL ABFRL LALPATHLAB WABCOINDIA SCHAEFFLER SUNTV EXIDEIND POLYCAB SUPREMEIND BHARATFORG ADANIPOWER BANKINDIA MFSL L&TFH IDFCFIRSTB AKZOINDIA APLLTD GMRINFRA CASTROLIND UNIONBANK ABCAPITAL GSPL SYNGENE GODREJIND FORTIS SAIL ADANIGAS CUB DALBHARAT CANBK AAVAS SUMICHEM NATCOPHARM M&MFIN CRISIL CUMMINSIND OIL IDEA ISEC INDHOTEL TATAPOWER IOB THERMAX IIFLWAM PHOENIXLTD ENDURANCE JINDALSTEL HATSUN SOLARINDS FEDERALBNK AMARAJABAT SJVN ESCORTS MGL MANAPPURAM VINATIORGA UCOBANK EMAMILTD ZYDUSWELL MOTILALOFS SKFINDIA BHEL JKCEMENT NIITTECH GODREJAGRO JSWENERGY CENTRALBK RBLBANK HEXAWARE TTKPRESTIG PRESTIGE TATACOMM VGUARD METROPOLIS SIS MINDAIND SFL RITES SUNDRMFAST NLCINDIA PVR NAVINFLUOR PGHL ASTRAZEN KAJARIACER FINEORG JCHAC GLENMARK TIMKEN TATACHEM IBVENTURES ITI INDIAMART SYMPHONY JMFINANCIL CHOLAHLDNG NATIONALUM CESC DEEPAKNTR BLUEDART MAHABANK TIINDIA BBTC ERIS NH GRINDWELL SHRIRAMCIT ESSELPACK GODFRYPHLP FINPIPE BASF CREDITACC ASTERDM KEC AEGISCHEM UJJIVANSFB APOLLOTYRE CHAMBLFERT BLUESTARCO VSTIND RATNAMANI PERSISTENT CHALET CARBORUNIV GALAXYSURF ORIENTELEC DIXON LINDEINDIA IBULHSGFIN JBCHEPHARM MRPL AVANTIFEED HUDCO JUBILANT FRETAIL TATAELXSI AMBER IEX ASAHIINDIA ENGINERSIN SPANDANA EIHOTEL CANFINHOME KIOCL GMMPFAUDLR GRANULES VTL EDELWEISS IRCON RADICO COCHINSHIP LAURUSLABS NESCO RALLIS VIPIND BDL JYOTHYLAB DCMSHRIRAM TATAINVEST MIDHANI FDC CENTURYTEX INDIACEM HEIDELBERG CEATLTD BIRLACORPN GEPIL POWERINDIA KRBL QUESS FLUOROCHEM FINCABLES APLAPOLLO SUNTECK BAJAJELEC GESHIP SUNCLAYLTD CERA CGCL DCBBANK NBCC GPPL DBL STAR MASFIN KALPATPOWR STARCEMENT OMAXE TEAMLEASE KNRCON PNBHOUSING INOXLEISUR TV18BRDCST REDINGTON RVNL BRIGADE INDIANB THYROCARE TECHNOE MAHINDCIE VMART GULFOILLUB SUDARSCHEM STRTECH AFFLE SUVENPHAR SPARC CYIENT GRAPHITE VAIBHAVGBL CENTURYPLY SWANENERGY EIDPARRY LAXMIMACH ALKYLAMINE MOIL PNCINFRA KEI LUXIND HATHWAY FLFL IIFL IDFC CCL GARFIBRES MAHSCOOTER KPRMILL JKLAKSHMI TASTYBITE INDOSTAR BALRAMCHIN INFIBEAM CDSL BHARATRAS WELSPUNIND RESPONIND TRIDENT KSCL CAPLIPOINT VAKRANGEE TCIEXP ICRA POLYMED CSBBANK TCNSBRANDS SHILPAMED ZENSARTECH HINDCOPPER BAJAJCON INGERRAND INDOCO NETWORK18 SEQUENT WOCKPHARMA JUSTDIAL FSL TRITURBINE BEML RAIN IRB HEG MHRIL IBREALEST MMTC GET&D UJJIVAN TATASTLBSL FMGOETZE GNFC ELGIEQUIP DELTACORP SCI LEMONTREE SONATSOFTW VARROC BSOFT SHOPERSTOP ESABINDIA VESUVIUS MAXINDIA GUJALKALI LAOPALA MAHLOG WELCORP FAIRCHEM KARURVYSYA GREAVESCOT JSWHL ADVENZYMES SUPRAJIT SCHNEIDER GRSE RCF DHANUKA PRSMJOHNSN NILKAMAL KSB NAVNETEDUL PAPERPROD JINDALSAW EQUITAS GSFC DEN TCI RAYMOND ALLCARGO ORIENTREF FCONSUMER VRLLOG DBCORP BALMLAWRIE ECLERX JAGRAN BSE JKPAPER MINDACORP KTKBANK MAHSEAMLES ACCELYA SOBHA KIRLOSENG SUPPETRO SWSOLAR HSCL GAEL GREENLAM VENKEYS JSL AARTIDRUGS PSPPROJECT DIAMONDYD NIITLTD HFCL ASHOKA SOLARA ARVINDFASN AHLUCONT PTC HGINFRA PRINCEPIPE NCC FACT TIDEWATER ITDC APARINDS".split(
    #     " ")[1:50]
    # stock_input = dict((s, {"from": "2020-08-01", "to": "2020-08-31"}) for s in stocks)

    tradingSystem = TradingSystem({"api_key": api_key, "api_secret": api_secret}, {
        "back_testing_config": {"stocks_config": stock_input}},
                                  ZerodhaServiceIntraDay, [TrendlineStrategy()])  #
    # tradingSystem = TradingSystem({"api_key": api_key, "api_secret": api_secret}, {
    #     "back_testing_config": {"stocks_config": {"ZEEL": {"from": "2020-08-18", "to": "2020-09-04"}}}},
    #                               ZerodhaServiceIntraDay, [TrendlineStrategy()]) #
    tradingSystem.run()
    # tradingSystem.summery()

    from db.tradebook import TradeBook
    tradeBook = TradeBook()
    tradeBook.summary()


def play_casino_live():
    api_key = 'f6jdkd2t30tny1x8'
    api_secret = 'eiuq7ln5pp8ae6uc6cjulhap3zc3bsdo'

    sh = StorageHandler()

    top_n = 50
    # "INDIGO".split(" ") #

    # stocks = ["JINDALSTEL"]
    stocks = \
        "RELIANCE TCS HINDUNILVR HDFCBANK HDFC INFY KOTAKBANK BHARTIARTL ITC ICICIBANK SBIN ASIANPAINT DMART BAJFINANCE MARUTI HCLTECH LT WIPRO AXISBANK ULTRACEMCO HDFCLIFE COALINDIA ONGC SUNPHARMA NTPC POWERGRID TITAN DABUR IOC BAJAJFINSV PIDILITIND BPCL HINDZINC BRITANNIA SBILIFE SHREECEM BAJAJ-AUTO SBICARD TECHM GODREJCP DIVISLAB DRREDDY ICICIPRULI ADANIPORTS ICICIGI BERGEPAINT HDFCAMC GSKCONS INDIGO SIEMENS EICHERMOT MARICO M&M JSWSTEEL MCDOWELL-N GAIL CIPLA COLPAL DLF TORNTPHARM PGHH BANDHANBNK BIOCON HEROMOTOCO GRASIM AMBUJACEM TATASTEEL HAVELLS PETRONET INFRATEL HINDPETRO YESBANK ALKEM BOSCHLTD CADILAHC IGL LUPIN UPL NAUKRI LTI BANKBARODA MRF MUTHOOTFIN NMDC INDUSINDBK UBL PFC AUROPHARMA VEDL ADANIGREEN WHIRLPOOL HONAUT TATAMOTORS PNB HINDALCO GLAXO 3MINDIA PEL KANSAINER ADANITRANS CONCOR NHPC IDBI BAJAJHLDNG ABB JUBLFOOD MOTHERSUMI PAGEIND TATACONSUM NIACL GICRE PFIZER ACC BEL GILLETTE IPCALAB RECLTD HAL OFSS TRENT RAJESHEXPO PIIND SRF COROMANDEL GUJGASLTD APOLLOHOSP BATAINDIA VOLTAS IRCTC BALKRISIND VBL NAM-INDIA GODREJPROP ADANIENT SRTRANSFIN RELAXO AUBANK SANOFI TVSMOTOR ASTRAL MINDTREE TORNTPOWER SUNDARMFIN AARTIIND AIAENG CROMPTON ASHOKLEY MPHASIS LTTS RAMCOCEM OBEROIRLTY CHOLAFIN AJANTPHARM ZEEL LICHSGFIN ATUL ABFRL LALPATHLAB WABCOINDIA SCHAEFFLER SUNTV EXIDEIND POLYCAB SUPREMEIND BHARATFORG ADANIPOWER BANKINDIA MFSL L&TFH IDFCFIRSTB AKZOINDIA APLLTD GMRINFRA CASTROLIND UNIONBANK ABCAPITAL GSPL SYNGENE GODREJIND FORTIS SAIL ADANIGAS CUB DALBHARAT CANBK AAVAS SUMICHEM NATCOPHARM M&MFIN CRISIL CUMMINSIND OIL IDEA ISEC INDHOTEL TATAPOWER IOB THERMAX IIFLWAM PHOENIXLTD ENDURANCE JINDALSTEL HATSUN SOLARINDS FEDERALBNK AMARAJABAT SJVN ESCORTS MGL MANAPPURAM VINATIORGA UCOBANK EMAMILTD ZYDUSWELL MOTILALOFS SKFINDIA BHEL JKCEMENT NIITTECH GODREJAGRO JSWENERGY CENTRALBK RBLBANK HEXAWARE TTKPRESTIG PRESTIGE TATACOMM VGUARD METROPOLIS SIS MINDAIND SFL RITES SUNDRMFAST NLCINDIA PVR NAVINFLUOR PGHL ASTRAZEN KAJARIACER FINEORG JCHAC GLENMARK TIMKEN TATACHEM IBVENTURES ITI INDIAMART SYMPHONY JMFINANCIL CHOLAHLDNG NATIONALUM CESC DEEPAKNTR BLUEDART MAHABANK TIINDIA BBTC ERIS NH GRINDWELL SHRIRAMCIT ESSELPACK GODFRYPHLP FINPIPE BASF CREDITACC ASTERDM KEC AEGISCHEM UJJIVANSFB APOLLOTYRE CHAMBLFERT BLUESTARCO VSTIND RATNAMANI PERSISTENT CHALET CARBORUNIV GALAXYSURF ORIENTELEC DIXON LINDEINDIA IBULHSGFIN JBCHEPHARM MRPL AVANTIFEED HUDCO JUBILANT FRETAIL TATAELXSI AMBER IEX ASAHIINDIA ENGINERSIN SPANDANA EIHOTEL CANFINHOME KIOCL GMMPFAUDLR GRANULES VTL EDELWEISS IRCON RADICO COCHINSHIP LAURUSLABS NESCO RALLIS VIPIND BDL JYOTHYLAB DCMSHRIRAM TATAINVEST MIDHANI FDC CENTURYTEX INDIACEM HEIDELBERG CEATLTD BIRLACORPN GEPIL POWERINDIA KRBL QUESS FLUOROCHEM FINCABLES APLAPOLLO SUNTECK BAJAJELEC GESHIP SUNCLAYLTD CERA CGCL DCBBANK NBCC GPPL DBL STAR MASFIN KALPATPOWR STARCEMENT OMAXE TEAMLEASE KNRCON PNBHOUSING INOXLEISUR TV18BRDCST REDINGTON RVNL BRIGADE INDIANB THYROCARE TECHNOE MAHINDCIE VMART GULFOILLUB SUDARSCHEM STRTECH AFFLE SUVENPHAR SPARC CYIENT GRAPHITE VAIBHAVGBL CENTURYPLY SWANENERGY EIDPARRY LAXMIMACH ALKYLAMINE MOIL PNCINFRA KEI LUXIND HATHWAY FLFL IIFL IDFC CCL GARFIBRES MAHSCOOTER KPRMILL JKLAKSHMI TASTYBITE INDOSTAR BALRAMCHIN INFIBEAM CDSL BHARATRAS WELSPUNIND RESPONIND TRIDENT KSCL CAPLIPOINT VAKRANGEE TCIEXP ICRA POLYMED CSBBANK TCNSBRANDS SHILPAMED ZENSARTECH HINDCOPPER BAJAJCON INGERRAND INDOCO NETWORK18 SEQUENT WOCKPHARMA JUSTDIAL FSL TRITURBINE BEML RAIN IRB HEG MHRIL IBREALEST MMTC GET&D UJJIVAN TATASTLBSL FMGOETZE GNFC ELGIEQUIP DELTACORP SCI LEMONTREE SONATSOFTW VARROC BSOFT SHOPERSTOP ESABINDIA VESUVIUS MAXINDIA GUJALKALI LAOPALA MAHLOG WELCORP FAIRCHEM KARURVYSYA GREAVESCOT JSWHL ADVENZYMES SUPRAJIT SCHNEIDER GRSE RCF DHANUKA PRSMJOHNSN NILKAMAL KSB NAVNETEDUL PAPERPROD JINDALSAW EQUITAS GSFC DEN TCI RAYMOND ALLCARGO ORIENTREF FCONSUMER VRLLOG DBCORP BALMLAWRIE ECLERX JAGRAN BSE JKPAPER MINDACORP KTKBANK MAHSEAMLES ACCELYA SOBHA KIRLOSENG SUPPETRO SWSOLAR HSCL GAEL GREENLAM VENKEYS JSL AARTIDRUGS PSPPROJECT DIAMONDYD NIITLTD HFCL ASHOKA SOLARA ARVINDFASN AHLUCONT PTC HGINFRA PRINCEPIPE NCC FACT TIDEWATER ITDC APARINDS" \
            .split(" ")[:300]
    tradingSystem = TradingSystem({"api_key": api_key, "api_secret": api_secret},
                                  {"stocks_to_subscribe": stocks, "stocks_in_fullmode": []}, ZerodhaServiceOnline,
                                  [TrendlineStrategy()])  #
    from db.tradebook import TradeBook

    tradeBook = TradeBook()
    from db.shadow_trading_service import ShadowTradingService
    tradeBook.register_trading_service(ShadowTradingService())

    tradingSystem.run()
    tradeBook.summary()


# Uncomment to profile the code
# import yappi
# yappi.set_clock_type("cpu") # Use set_clock_type("wall") for wall time
# yappi.start()
# play_casino()
# play_casino()
# yappi.get_func_stats().print_all()
# yappi.get_thread_stats().print_all()

# Command line Running argument
# -l "RELIANCE" -s "2020-09-01" -e "2020-09-30"  live/audit

def run():
    options = TradingOptions()
    sh = StorageHandler()
    tradeRunner = ZerodhaServiceOnline if options.args.mode == 'live' else ZerodhaServiceIntraDay
    credentials = {"api_key": "f6jdkd2t30tny1x8", "api_secret": "eiuq7ln5pp8ae6uc6cjulhap3zc3bsdo"}
    configuration = None
    if options.args.mode == 'live':
        if is_holiday(datetime.datetime.now()):
            logging.info("Not Running the Live strategy today as date:{} is holiday".format(datetime.datetime.now()))
        configuration = {"stocks_to_subscribe": options.getStocks(), "stocks_in_fullmode": []}
    else:
        stock_input = dict((s, {"from": options.args.start, "to": options.args.end}) for s in options.getStocks())
        configuration = {"back_testing_config": {"stocks_config": stock_input}}
    # run trading system
    tradingSystem = TradingSystem(credentials, configuration, tradeRunner, [TrendlineStrategy()])
    tradingSystem.run()
    # Use tradebook and get summary
    tradeBook = TradeBook()
    if options.args.mode == 'live':
        # from db.shadow_trading_service import ShadowTradingService
        # tradeBook.register_trading_service(ShadowTradingService())
        from db.zeroda_live_trading_service import ZerodhaLiveTradingService
        tradeBook.register_trading_service(ZerodhaLiveTradingService(credentials))

    tradeBook.summary()
    if options.args.mode == 'live':
        print("Waiting till ", str(get_datetime(16, 00)))
        time.sleep((get_datetime(16, 00) - datetime.datetime.now()).total_seconds())
        tradingSystem.shutdown()


# Execute the command
run()
