
import csv
import datetime
import io
import numpy as np
import pandas
import pytz
import re
import requests
import time


def load_transactions_from_google_sheets(google_sheets_url):
    raw_transaction_data = requests.get(google_sheets_url)
    raw_transaction_data = raw_transaction_data.content.decode("utf-8")

    raw_transaction_data = raw_transaction_data.replace('","', '"\t"')
    raw_transaction_data = raw_transaction_data.replace(" €", "")
    raw_transaction_data = re.sub(r"-[ ]*", "-", raw_transaction_data)
    raw_transaction_data = re.sub(r"-\t", "-0.0\t", raw_transaction_data)
    csv_data = io.StringIO(raw_transaction_data)

    def parse_nr(nr):
        nr = nr.replace("€", "")
        if "," in nr:
            nr = nr.replace(".", "")
            nr = nr.replace(",", ".")
        if not nr:
            return np.nan
        if nr == "-":
            return 0.0
        nr = float(nr)
        return nr

    transaction_df = pandas.read_csv(csv_data, sep="\t",quoting = csv.QUOTE_ALL,
                                     parse_dates=["date"], quotechar='"', decimal=",", thousands=".",
                                          #dtype=dict(pcs=np.float64, pp=np.float64,
                                          #           total=np.float64, transaction_cost=np.float64),
                                         converters=dict(pcs=parse_nr, pp=parse_nr, total=parse_nr,
                                                         transaction_cost=parse_nr)

                                          )
    transaction_df = transaction_df[["date", "symbol_wkn", "symbol_isin", "name", "pcs", "pp", "total", "transaction_cost"]]
    transaction_df["date"] = transaction_df.date.apply(lambda d: d.to_pydatetime().date())
    for col in ("symbol_isin", "symbol_wkn"):
        transaction_df[col] = transaction_df[col].apply(lambda s: s.strip())

    def clean_name(name):
        for cut in ("UCITS", "PLC"):
            if cut in name:
                name = name[:name.find(cut)]
        for cut in ("MSCI", ):
            if cut in name:
                name = name[(name.find(cut)):]
        return name
    transaction_df["name"] = transaction_df.name.apply(clean_name)

    return transaction_df

def fetch_etf_data_q(isin, since_when, data_source, isin_to_wkn_map, yesterday):
    try:
        wkn = isin_to_wkn_map[isin]
        assert wkn is not None
    except:
        print("\t ISIN {} not mapped to WKN".format(isin))
        return None
    def parse_date(d):
        return datetime.date(*list(map(int, d.split(".")))[::-1])
    def parse_value(v):
        if v == "-":
            return np.nan
        v = v.replace(".", "")
        v = v.replace(",", ".")
        v = float(v)
        return v
        
    df = None
    for subpage in ("fonds", "aktien"):
        try:
            df = pandas.read_html(data_source.format(subpage, wkn),
                        decimal="~", thousands="#", parse_dates=False,
                        converters=dict(Datum=parse_date, Schluss=parse_value))
            break
        except Exception as e:
            if subpage == "aktien":
                print("\tError: " + str(e))
            continue
    if df is None:
        return None

    assert len(df) == 1

    df = df[0]
    df = df[["Datum", "Schluss"]]
    df.columns = ["date", "price"]
    #df["date"] = df.date.apply(lambda d: datetime.date(list(map(int, d.split("."))[::-1])))


    df = df[~np.isnan(df.price)]
    #df["date"] = df.date.apply(lambda d: d.to_pydatetime().date())
    df = df[df.date >= since_when]
    df = df[df.date <= yesterday]
    df["symbol"] = isin
    return df.reset_index(drop=True)

def fetch_etf_data_bf(isin, since_when, yesterday, data_source, state):
    
    import time
    import selenium
    import selenium.common.exceptions
    from selenium.webdriver.common.keys import Keys
    
    if "driver" in state:
        driver = state["driver"]
    else:
        import os
        os.environ['MOZ_HEADLESS'] = "0"
        driver = selenium.webdriver.Firefox()
        driver.implicitly_wait(2)
        state["driver"] = driver
        
    driver.get(data_source)
    elem = driver.find_element_by_id("mat-input-0")
    elem.send_keys(isin)
    time.sleep(3.0)
    elem.send_keys(Keys.ENTER)
    
    time.sleep(2.0)
    driver.get(driver.current_url + "/kurshistorie/historische-kurse-und-umsaetze")

    try:
        elem = driver.find_element_by_xpath('//th[text()="Datum"]')
    except selenium.common.exceptions.NoSuchElementException as e:
        print("\tTable could not be loaded. ({})".format(str(e)))
        return None
    table = elem.find_element_by_xpath("..").find_element_by_xpath("..").find_element_by_xpath("..")
    
    table_html = table.get_attribute("outerHTML")
    
    table = pandas.read_html(table_html,
                             thousands=None, decimal=",",
                             parse_dates=False)
    if not table:
        print("\tNo table could be parsed.")
        return None
    df = table[0]
    
    date_parser = lambda x: datetime.datetime.strptime(str(x), "%d.%m.%y").date()
    df["Datum"] = df.Datum.apply(date_parser)
    df = df[["Datum", "Schluss"]].copy()
    df.columns = ["date", "price"]
    df["symbol"] = isin
    
    df = df[~np.isnan(df.price)]
    df = df[df.date >= since_when]
    df = df[df.date <= yesterday]
    
    return df

def update_and_store_etf_data(transaction_df, etf_df, data_source, data_source_bf, save_folder_path=None):
    
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    selenium_state = dict()

    all_etfs = set(transaction_df.symbol_isin.unique())

    isin_to_wkn_map = dict()
    for isin, wkn in transaction_df[["symbol_isin", "symbol_wkn"]].itertuples(index=False):
        if isin and wkn:
            isin_to_wkn_map[isin] = wkn
    
    to_update = dict()
    for etf, df in etf_df.groupby("symbol"):
        max_date = df.date.max()
        if max_date == yesterday:
            continue
        max_date = max_date + datetime.timedelta(days=1)
        to_update[etf] = max_date
        
    for etf in all_etfs:
        if (etf not in to_update) and (etf not in etf_df.symbol.unique()):
            to_update[etf] = datetime.date(2020, 1, 1)
    
    additional_data = []
    for etf, update_begin in to_update.items():
        print("Updating {}...\t[last state {}]".format(etf, update_begin.isoformat()))
        kwargs = dict(isin=etf, since_when=update_begin, data_source=data_source_bf,
                      yesterday=yesterday)
        try:
            new_data = fetch_etf_data_bf(state=selenium_state, **kwargs)
        except Exception as e:
            print("\tFailed with exception {}.".format(str(e)))
            continue
        
        if new_data is None or new_data.shape[0] == 0:
            print("\tTrying secondary data source..")
            kwargs["data_source"] = data_source
            kwargs["isin_to_wkn_map"] = isin_to_wkn_map
            new_data = fetch_etf_data_q(**kwargs)

        if new_data is not None and new_data.shape[0] > 0:
            print("\tOK ({} new data points, max date: {}).".format(new_data.shape[0], new_data.date.max()))
            additional_data.append(new_data)
        else:
            print("\tFailed.")
        
    if "driver" in selenium_state:
        try:
            selenium_state["driver"].close()
        except:
            pass

    if len(additional_data) > 0:
        additional_data = pandas.concat(additional_data)
        min_date = min(additional_data.groupby("symbol").date.max())
        print("Limiting data to before {}".format(min_date.isoformat()))
        additional_data = additional_data[additional_data.date <= min_date]
        etf_df = pandas.concat((etf_df, additional_data)).sort_values("date")
        
        if save_folder_path is not None:
            for symbol, df in etf_df.groupby("symbol"):
                if additional_data[additional_data.symbol == symbol].shape[0] == 0:
                    continue
                date = df.date.max().isoformat()
                filename = save_folder_path + "/{}_{}.pickle".format(symbol, date)
                print("\tSaving {}...".format(filename))
                df.to_pickle(filename)

    return etf_df