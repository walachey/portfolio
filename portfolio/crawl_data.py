
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
    transaction_df = transaction_df[["date", "symbol_isin", "name", "pcs", "pp", "total", "transaction_cost"]]
    transaction_df["date"] = transaction_df.date.apply(lambda d: d.to_pydatetime().date())
    
    return transaction_df

def parse_dt_value_tuple(text):
    if text[0] == "[":
        text = text[1:]
    if text[-1] == "]":
        text = text[:-1]
    text = text[len("Date.UTC("):]
    date_end = text.find(")")
    date_string = text[:date_end]
    try:
        year, mon, day = list(map(int, date_string.split(",")))
    except:
        print(date_string)
        raise
    value_part = text[date_end+2:]
    value_part = float(value_part)
    
    
    
    mon += 1
        
    try:
        return_values = pytz.UTC.localize(datetime.datetime(year, mon, day)), value_part
    except Exception as e:
        print(str(e), year, mon, day, value_part)
        if mon == 0:
            print(text)
            raise
        if mon == 2 and day >= 29:
            return (None, None)
        else:
            return (None, None)
    
    return return_values

def parse_all_dt_tuples(text, symbol):
    if text[0] == "[":
        text = text[1:-1]
    data = map(parse_dt_value_tuple, text.split("],["))
    data = [(d[0], d[1], symbol) for d in data]
    return pandas.DataFrame(data, columns=["date", "price", "symbol"])

def request_price_chart_raw_data(isin):
    
    url = "https://www.justetf.com/en/etf-profile.html"

    """initial_querystring = {
      "0-1.0-chartPanel": "",
      #"groupField":"index",
      #"from":"search",
      "isin": isin,
      #"query": isin
      "_": "1591698467608"
    }
    querystring = {
      #"0-1.0-chartPanel-chart-content-dates-ptl_max":"",
      #"3-1.0-chartPanel-chart-content-dates-ptl_max": "", 
      "0-1.0-chartPanel-chart-content-dates-ptl_max": "", 
      #"groupField":"index",
      #"from":"search",
      "isin": isin,
      #"query": isin,
      "_": "1591698467608"
    }
    querystring2 = {
      "0": "", 
      "isin": isin
    }
    querystring_abs = {
      #"0-1.0-tabs-panel-chart-optionsPanel-selectContainer-valueType": "",
      "3-1.0-chartPanel-chart-content-optionsPanel-selectContainer-valueType": "",
      #"groupField":"index",
      #"sortField":"ter",
      #"sortOrder":"asc",
      #"from":"search",
      #"query": isin,
      "isin": isin,
      #"tab":"chart",
      "_": "1591698467608"
    }
    data = {
      "tabs:panel:chart:optionsPanel:selectContainer:valueType": "market_value",
      #"currencies": "0"
        
    }

    # Not all of these headers may be necessary
    headers_abs = {
        'authority': "www.justetf.com",
        'accept': "application/xml, text/xml, */*; q=0.01",
        'x-requested-with': "XMLHttpRequest",
        #"Wicket-Ajax-BaseURL": "en/etf-profile.html?query={}&amp;groupField=index&amp;from=search&amp;isin={}&amp;tab=chart".format(isin, isin),
        "Wicket-Ajax-BaseURL": "en/etf-profile.html?isin={}".format(isin),
        'Wicket-Ajax': "true",
        'Connection': "keep-alive",
        "Origin": "https://www.justetf.com",
        "Wicket-FocusedElementId": "id2f4",
        #"Referer": "https://www.justetf.com/en/etf-profile.html?query={}&groupField=index&from=search&isin={}&tab=chart".format(isin, isin)
        "Referer": "https://www.justetf.com/en/etf-profile.html?isin={}".format(isin)
    }

    session = requests.Session()
    
    #response = session.get(url, params=initial_querystring)
    response = session.get(url, params=querystring)
    response = session.get(url, params=querystring, headers=headers_abs)
    response = session.get(url, params=querystring2, headers=headers_abs)"""
    
    #response = session.get( url, params=querystring, headers=headers_abs)
    #print(response.text)
    #response = session.post( url, params=querystring_abs, headers=headers_abs, data=data)
    
    # The first request won't return what we want but it sets the cookies
    #response = session.get( url, params=querystring)
    
    
    querystring = {
    # Modify this string to get the timeline you want
    # Currently it is set to "max" as you can see
    "0-1.0-chartPanel-chart-content-dates-ptl_max":"",
    "isin": isin,
    "_":"1591884177573"}

    # Not all of these headers may be necessary
    headers = {
        'authority': "www.justetf.com",
        'accept': "application/xml, text/xml, */*; q=0.01",
        'x-requested-with': "XMLHttpRequest",
        'wicket-ajax-baseurl': "en/etf-profile.html?isin={}".format(isin),
        'wicket-ajax': "true",
        'wicket-focusedelementid': "id27",
        'Connection': "keep-alive",
    }

    session = requests.Session()
    cookie_obj = requests.cookies.create_cookie(name='CookieConsent',
        value="{stamp:'io5uexgwEE6Wf6IlTg5R2CDchKIF6yvLj7PI3sC0Rc9AdW9f2tsClA==',necessary:true,preferences:true,statistics:true,marketing:true,ver:1,utc:1591885306054,region:'de'}")
    session.cookies.set_cookie(cookie_obj)
    cookie_obj = requests.cookies.create_cookie(name='JSESSIONID',
        value="6CC1C6C2B0F80D809CAAB5174AA2CCB3")
    session.cookies.set_cookie(cookie_obj)
    # The first request won't return what we want but it sets the cookies
    response = session.get( url, params=querystring, allow_redirects=True)

    # Cookies have been set now we can make the 2nd request and get the data we want
    response = session.get( url, headers=headers, params=querystring, allow_redirects=True)
    

    # Cookies have been set now we can make the 2nd request and get the data we want
    #response = session.get( url, headers=headers_abs, params=querystring)
    return response.text

def request_price_chart(isin):
    contents = request_price_chart_raw_data(isin)
    sub_script = contents
    data_position = sub_script.find("data: [[")
    if data_position == -1:
        print(contents)
        raise ValueError("Invalid response.")
    
    sub_script = sub_script[(data_position + 6):]
    sub_script = sub_script[:(sub_script.find("]]")+2)]
    df = parse_all_dt_tuples(sub_script, isin)
    return df

def crawl_and_save_etf_data(root_path, isins):

    today = datetime.date.today()
    for isin in isins:
        chart = request_price_chart(isin)
        chart.to_pickle(root_path + isin + "_" + today.isoformat() + ".pickle")
        time.sleep(5)