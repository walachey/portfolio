import datetime, pytz
import matplotlib.pyplot as plt
import scipy.cluster.hierarchy
import seaborn as sns
import pandas
import numpy as np
import itertools

def plot_cci(etf_df, transaction_df, save_path=None):
    cci_df = etf_df.pivot_table(index="date", values="price", columns="symbol")
    etf_translations = {isin: name for isin, name in transaction_df[["symbol_isin", "name"]].itertuples(index=False)}

    for col in cci_df.columns:
        n_days = 10
        TP = cci_df[col]
        cci_df[col] = pandas.Series((TP - TP.rolling(n_days).mean()) / (0.015 * TP.rolling(n_days).std()))
    cci_df.columns = [etf_translations[c] for c in cci_df.columns]

    from_date = transaction_df.date.max() - datetime.timedelta(days=60)
    cci_df = cci_df[cci_df.index > from_date]
    cci_df = cci_df.rolling(7, center=True).mean()
    #cci_df = cci_df.reset_index()

    fig, ax = plt.subplots(figsize=(20, 10))
    cci_df.plot(ax=ax)
    ax.axhline(100, linestyle="--", c="k")
    ax.axhline(-100, linestyle="--", c="k")
    ax.legend(loc='center', bbox_to_anchor=(0.5, -0.25), mode="expand", ncol=2)
    plt.title("Commodity Channel Index")
    plt.tight_layout()
    if save_path is not None:
        plt.savefig(save_path)
        plt.close()
    else:
        plt.show()

def plot_gain_development(transaction_df, merged_df, save_path=None):
    df_cols = merged_df.pivot_table(index="date", columns="name", values="positive_gain", aggfunc=np.sum)
    df_cols.fillna(0.0, inplace=True)
    
    df_sum = merged_df.pivot_table(index="date", values=["total", "gain"], aggfunc=np.sum)
    df_sum.reset_index(inplace=True)

    fig, ax = plt.subplots(figsize=(20, 10))
    df_cols.plot.area(ax=ax)

    fig.canvas.draw()

    locs, labels = ax.get_yticks(), ax.get_yticklabels()

    sns.lineplot(x="date", y="gain", color="k", linewidth=2.0, data=df_sum, ax=ax)

    transaction_costs_df = transaction_df.pivot_table(index="date", values="transaction_cost", aggfunc=np.sum)
    transaction_costs_df.index = pandas.to_datetime(transaction_costs_df.index)
    transaction_costs_df = transaction_costs_df.resample("1D").sum()
    transaction_costs_df.transaction_cost = np.cumsum(transaction_costs_df.transaction_cost)

    transaction_costs_df.reset_index(inplace=True)
    transaction_costs_df.date = transaction_costs_df.date.apply(lambda d: d.to_pydatetime().date())

    sns.lineplot(x="date", y="transaction_cost", color="r", linewidth=1.0, data=transaction_costs_df, ax=ax)

    transaction_costs = transaction_df.transaction_cost.sum()
    ax.axhline(transaction_costs, linestyle=":", color="r")
    ylim = list(ax.get_ylim())
    ylim[1] = max(ylim[1],transaction_costs + 10)
    ax.set_ylim(*ylim)
    plt.ylabel("Gain development")
    ax.legend(loc='center', bbox_to_anchor=(0.5, -0.25), ncol=2)

    plt.tight_layout()

    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path)
        plt.close()


def plot_clustermap(transaction_df, merged_df, save_path=None):
    df_series = merged_df.pivot_table(index="date", columns="name", values="price", aggfunc=np.sum)

    N = len(df_series.columns)
    correlations = np.zeros(shape=(N, N), dtype=np.float32)

    for c1, c2 in itertools.combinations(range(N), 2):
        series = df_series[df_series.columns[c1]].values, df_series[df_series.columns[c2]].values
        valid = ~pandas.isnull(series[0]) & ~pandas.isnull(series[1])
        if valid.sum() < 2:
            continue
        series = series[0][valid], series[1][valid]
        c, p = scipy.stats.spearmanr(*series)
        correlations[c1, c2] = c
        correlations[c2, c1] = c

    linkage = scipy.cluster.hierarchy.linkage(1.0 - np.abs(correlations), method="ward")
    sns.clustermap(correlations, vmin=-1.0, vmax=1.0, cmap="seismic",
                row_linkage=linkage, col_linkage=linkage,
                xticklabels=df_series.columns, yticklabels=df_series.columns, figsize=(15, 15))
                
    if save_path is None:
        plt.show()
    else:
        plt.savefig(save_path)
        plt.close()