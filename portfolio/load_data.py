import pandas
import numpy as np

def read_current_etf_information(root_path):
    import os
    import pandas
    from collections import defaultdict

    available_files = os.listdir(root_path)
    files_per_etf = defaultdict(list)
    for f in available_files:
        if not os.path.isfile(root_path + f):
            continue
        if "_" in f:
            isin = f.split("_")[0]
        else:
            isin = f.split(".")[0]
        files_per_etf[isin].append(f)
    for k, v in files_per_etf.items():
        files_per_etf[k] = list(sorted(v))[-1]
    
    etf_df = []
    for f in files_per_etf.values():
        df = pandas.read_pickle(root_path + f)
        try:
            df["date"] = df.date.apply(lambda d: d.to_pydatetime().date())
        except:
            pass
        etf_df.append(df)
    etf_df = pandas.concat(etf_df)

    return etf_df

def merge_transaction_and_etf_data(transaction_df, etf_df):
    df = []
    for row_tuple in transaction_df.itertuples(index=False):
        sub_df = etf_df[
            (etf_df.symbol == row_tuple.symbol_isin) & (etf_df.date >= row_tuple.date)
                ][["symbol", "date", "price"]].copy().reset_index()
        assert sub_df.shape[0] == len(sub_df.date.unique())
        if sub_df.shape[0] == 0:
            continue
        try:
            initial_value = sub_df[sub_df.date == row_tuple.date].price.values[0]
        except:
            print("No direct match for {}, taking {} at {}".format(str(row_tuple), sub_df.date.iloc[0], sub_df.price.iloc[0]))
            initial_value = sub_df.price.iloc[0]
        sub_df["transaction_date"] = row_tuple.date
        sub_df["name"] = row_tuple.name
        sub_df["pcs"] = row_tuple.pcs
        sub_df["initial_price"] = initial_value
        sub_df["initial_value_actual"] = row_tuple.total
        df.append(sub_df)
    df = pandas.concat(df)

    df["total"] = df.pcs * df.price
    df["initial_value"] = df.pcs * df.initial_price
    df["gain"] = df.total - df.initial_value
    df["positive_gain"] = np.clip(df.gain, 0, np.inf)

    return df