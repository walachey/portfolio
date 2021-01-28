import calendar
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
    chart.title = "% change over last month"
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

def plot_portfolio_category_distribution(merged_df, category_df, save_path=None):

    current_state = merged_df[merged_df.date == merged_df.date.max()]
    current_state = current_state.pivot_table(index="symbol", values="total", aggfunc=np.sum)
    current_state = current_state.reset_index()
    current_state = current_state.sort_values("total", ascending=False)

    n_categories = len(category_df.category.unique())
    columns = 5
    rows = 1 + n_categories // columns

    fig, axes = plt.subplots(rows, columns, figsize=(3 * columns * FIGSCALE, 3 * rows * FIGSCALE), dpi=DPI)
    axes = list(itertools.chain(*axes))
    for ax in axes:
        ax.set_axis_off()

    category_order = []
    for (category, df) in category_df.groupby("category"):
        df = current_state[current_state.symbol.isin(df.symbol.unique())]
        category_order.append((df.total.sum(), category))
    category_order = sorted(category_order)[::-1]

    for ax, (_, category) in zip(axes, category_order):
        df = category_df[category_df.category == category]
        symbols = list(df.symbol.unique())
        idx = current_state.symbol.isin(symbols)
        hit_df = current_state[idx]
        miss_df = current_state[~idx]
        labels = [category, "other"]
        ax.pie(x=[hit_df.total.sum(), miss_df.total.sum()],
               colors=["#dddd00", "#aaaabb"],
               autopct='%1.1f%%', startangle=90, pctdistance=0.85)
        ax.axis("equal")
        ax.add_artist(plt.Circle((0.0, 0.0), 0.70, fc='white'))
        legend = ax.legend(labels[0:1], loc="center", handlelength=0, handletextpad=0)
        legend.set_zorder(10)

    plt.tight_layout()

    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()

def plot_volatility(etf_df, transaction_df, merged_df, save_path=None, timedelta="month"):
    # Name map.
    etf_translations = {isin: name for isin, name in transaction_df[["symbol_isin", "name"]].itertuples(index=False)}
    
    min_number_of_days = dict(month=23, year=300)[timedelta]
    
    data = []
    begin_date = transaction_df.date.min().replace(day=1)
    end_date = merged_df.date.max()
    
    while begin_date < end_date:
        if timedelta == "month":
            end_of_period = begin_date.replace(day=calendar.monthrange(begin_date.year, begin_date.month)[1])
        elif timedelta == "year":
            end_of_period = begin_date.replace(year=begin_date.year + 1) - datetime.timedelta(days=1)
        month_df_all = merged_df[(merged_df.date >= begin_date) & (merged_df.date <= end_of_period)]
        month_df = month_df_all.pivot_table(index="date", columns="symbol", values="price")
        
        for symbol in month_df.columns:
            df = month_df_all[month_df_all.symbol == symbol]
            if df.pcs.sum() <= 0:
                continue
            values = month_df[symbol]
            values = values[~pandas.isnull(values)]
            min_date, max_date = values.index.min(), values.index.max()
            if (max_date - min_date).days < min_number_of_days:
                continue
            gain = (values[-1] - values[0]) / values[0]
            data.append(dict(
                symbol=etf_translations[symbol],
                gain=gain * 100.0))
        
        if timedelta == "month":
            month = begin_date.month + 1
            year = begin_date.year
            if month > 12:
                month = 1
                year += 1
            begin_date = datetime.date(year, month, 1)
        elif timedelta == "year":
            begin_date = begin_date.replace(year=begin_date.year + 1)
            
    data = pandas.DataFrame(data)
    
    data.symbol = [ "{} (N={:1d})".format(i[:30], (data.symbol == i).sum()) for i in data.symbol]
    data_means = data.pivot_table(index="symbol", values="gain", aggfunc="std")
    if data_means.shape[0] > 0:
        data_means = data_means.sort_values("gain", ascending=False)
        order = data_means.index
    else:
        order = None
    fig, ax = plt.subplots(figsize=(20 * FIGSCALE, 5 * FIGSCALE), dpi=DPI)
    sns.barplot(y="symbol", x="gain", data=data, ax=ax, order=order, ci=66.6)
    plt.title("Bootstrap 66.6% CI of the mean gain per {}".format(timedelta))
    plt.xlabel("% gain")
    plt.ylabel(None)
            
    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path, bbox_inches='tight')
        plt.close()