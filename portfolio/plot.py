import datetime, pytz
import pygal
import matplotlib.pyplot as plt
import scipy.cluster.hierarchy
import seaborn as sns
import pandas
import numpy as np
import itertools

DPI = 100
FIGSCALE = 0.5

def plot_history(etf_df, transaction_df, save_path=None):
    max_date = etf_df.date.max()
    etf_df = etf_df.pivot_table(index="date", values="price", columns="symbol")
    etf_translations = {isin: name for isin, name in transaction_df[["symbol_isin", "name"]].itertuples(index=False)}
    etf_df.columns = [etf_translations[c] for c in etf_df.columns]
    

    from_date = max_date - datetime.timedelta(days=30)
    etf_df = etf_df[etf_df.index > from_date]
    for symbol in etf_df.columns:
        offset = etf_df[symbol].iloc[0]
        etf_df[symbol] /= offset
        etf_df[symbol] -= 1.0
        etf_df[symbol] *= 100
    col_order = np.argsort(etf_df.iloc[-1, :].values)
    columns = [etf_df.columns[i] for i in col_order[::-1]]
    etf_df = etf_df[columns]

    chart = pygal.Line(fill=False, show_dots=False, width=20 * FIGSCALE * DPI, height=10 * FIGSCALE * DPI)
    chart.title = "%% change over last month"
    for col in etf_df.columns:
        def fixna(v):
            if pandas.isnull(v):
                return None
            return v
        vals = [fixna(v) for v in etf_df[col]]
        if np.all(pandas.isnull(vals)):
            continue
        chart.add(col, vals)
    chart.x_labels = list(etf_df.index)

    if save_path is None:
        return chart.render(is_unicode=True)
    else:
        chart.render_to_file(save_path)
    return

def plot_cci(etf_df, transaction_df, save_path=None):
    max_date = etf_df.date.max()
    cci_df = etf_df.pivot_table(index="date", values="price", columns="symbol")
    etf_translations = {isin: name for isin, name in transaction_df[["symbol_isin", "name"]].itertuples(index=False)}

    for col in cci_df.columns:
        n_days = 10
        TP = cci_df[col]
        cci_df[col] = pandas.Series((TP - TP.rolling(n_days).mean()) / (0.015 * TP.rolling(n_days).std()))
    cci_df.columns = [etf_translations[c] for c in cci_df.columns]
    

    from_date = max_date - datetime.timedelta(days=60)
    cci_df = cci_df[cci_df.index > from_date]
    cci_df = cci_df.rolling(7, center=False).mean()
    cci_df = cci_df.iloc[7:]
    col_order = np.argsort(cci_df.iloc[-1, :].values)
    columns = [cci_df.columns[i] for i in col_order[::-1]]
    cci_df = cci_df[columns]

    chart = pygal.Line(fill=False, show_dots=False, width=20 * FIGSCALE * DPI, height=10 * FIGSCALE * DPI,
                        range=(-110, 110))
    chart.title = "Commodity Channel Index"
    for col in cci_df.columns:
        def fixna(v):
            if pandas.isnull(v):
                return None
            return v
        vals = [fixna(v) for v in cci_df[col]]
        if np.all(pandas.isnull(vals)):
            continue
        chart.add(col, vals)
    chart.x_labels = list(cci_df.index)

    if save_path is None:
        return chart.render(is_unicode=True)
    else:
        chart.render_to_file(save_path)
    return

def plot_development(transaction_df, merged_df, save_path=None, show_gains=False, show_net_gain=False):
    # Name map.
    etf_translations = {isin: name for isin, name in transaction_df[["symbol_isin", "name"]].itertuples(index=False)}
    
    # Transaction costs over time.
    transaction_costs_df = transaction_df.pivot_table(index="date", columns="symbol_isin",
                                                        values="transaction_cost", aggfunc=np.sum)
    transaction_costs_df.index = pandas.to_datetime(transaction_costs_df.index)
    transaction_costs_df = transaction_costs_df.resample("1D").sum()
    transaction_costs_df = transaction_costs_df.cumsum(axis=0)

    # Stackable data.
    df_cols = merged_df.pivot_table(index="date", columns="symbol", values=["total", "initial_value"], aggfunc=np.sum)
    if show_gains:
        df_cols = df_cols["total"] - df_cols["initial_value"]
    else:
        df_cols = df_cols["total"]

    df_cols.fillna(0.0, inplace=True)

    if show_net_gain: # Subtract transaction costs.
        # Fill missing dates.
        transaction_costs_df.index = [i.date() for i in transaction_costs_df.index]
        last_row = transaction_costs_df.iloc[-1]
        for date in df_cols.index:
            if date not in transaction_costs_df.index:
                transaction_costs_df.loc[date] = last_row
        for col in df_cols.columns:
            df_cols[col] -= transaction_costs_df[col] # Same index.
    
    df_cols.clip(0.0, None, inplace=True)
    col_order = np.argsort(df_cols.iloc[-1, :])
    columns = [df_cols.columns[i] for i in col_order]
    df_cols = df_cols[columns]
    df_cols.rename(etf_translations, axis=1, inplace=True)
    
    chart = pygal.StackedBar(fill=True, show_dots=False, width=20 * FIGSCALE * DPI, height=10 * FIGSCALE * DPI)
    chart.title = "Gains over time" if show_gains else "Portfolio value over time"
    if show_net_gain:
        chart.title += " (net, minus transaction costs)"
    else:
        chart.title += " (gross)"
    for col in df_cols.columns:
        vals = df_cols[col]
        chart.add(col, vals)
    chart.x_labels = list(df_cols.index)

    if save_path is None:
        return chart.render(is_unicode=True)
    else:
        chart.render_to_file(save_path)
    
    return
   
def plot_clustermap(transaction_df, merged_df, save_path=None):
    df_series = merged_df.pivot_table(index="date", columns="name", values="price", aggfunc=np.sum)

    N = len(df_series.columns)
    correlations = np.ones(shape=(N, N), dtype=np.float32)

    for c1, c2 in itertools.combinations(range(N), 2):
        series = df_series[df_series.columns[c1]].values, df_series[df_series.columns[c2]].values
        valid = ~pandas.isnull(series[0]) & ~pandas.isnull(series[1])
        if valid.sum() < 2:
            c = 0.0
        else:
            series = series[0][valid], series[1][valid]
            c, p = scipy.stats.spearmanr(*series)
        correlations[c1, c2] = c
        correlations[c2, c1] = c

    distance_matrix = np.abs(np.max(correlations) - correlations)
    distance_matrix = scipy.spatial.distance.squareform(distance_matrix) # Inverse square form.
    linkage = scipy.cluster.hierarchy.linkage(distance_matrix, method="ward")
    sns.clustermap(correlations, vmin=-1.0, vmax=1.0, cmap="seismic",
                row_linkage=linkage, col_linkage=linkage,
                xticklabels=df_series.columns, yticklabels=df_series.columns, figsize=(15 * FIGSCALE, 15 * FIGSCALE))

    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()

def plot_portfolio_distribution(merged_df, save_path=None):

    current_state = merged_df[merged_df.date == merged_df.date.max()]
    current_state = current_state.pivot_table(index="name", values="total", aggfunc=np.sum)
    current_state = current_state.reset_index()
    current_state = current_state.sort_values("total", ascending=False)

    def clean_label(l):
        cut = l.find(" ", 15)
        if cut != -1:
            l = l[:cut] + "\n" + l[(cut+1):]
        return l
    labels = [clean_label(str(l)) for l in current_state.name]

    fig, ax = plt.subplots(figsize=(15 * FIGSCALE, 15 * FIGSCALE), dpi=DPI)
    plt.pie(x=current_state.total, labels=labels)
    
    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()