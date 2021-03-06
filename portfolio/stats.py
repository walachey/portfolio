import pandas
import numpy as np

def get_global_state(transaction_df, merged_df, as_html=True):
	current_df = merged_df[merged_df.date == merged_df.date.max()][["symbol", "name", "total", "gain", "pcs"]]

	synced_symbols = set(current_df.symbol.unique())
	additional_rows = []
	for symbol in transaction_df.symbol_isin.unique():
		if symbol in synced_symbols:
			continue
		sub_df = transaction_df[transaction_df.symbol_isin == symbol]
		amount = sub_df.total.sum()
		pieces = sub_df.pcs.sum()
		if np.isclose(pieces, 0.0):
			continue
		additional_rows.append(dict(
			symbol=symbol, name=sub_df.name.iloc[0],
			total=amount,
			gain=np.nan, pcs=pieces))
	if len(additional_rows) > 0:
		current_df = pandas.concat((current_df, pandas.DataFrame(additional_rows)), axis=0)

	current_state = dict()

	current_state["Total investment amount"] = transaction_df.total.sum()
	fees_idx = transaction_df.transaction_cost.values > 0.0
	current_state["Total fees"] = transaction_df.transaction_cost.values[fees_idx].sum()
	current_state["Total payouts"] = -transaction_df.transaction_cost.values[~fees_idx].sum()
	current_state["Total money spent"] = current_state["Total investment amount"] + current_state["Total fees"]
	current_state["Total fees (%)"] = "{:0.2%}".format(current_state["Total fees"] / current_state["Total investment amount"])

	current_state["Portfolio value"] = current_df.total.sum()
	current_state["Portfolio gain (netto)"] = current_state["Portfolio value"] - current_state["Total investment amount"] + current_state["Total payouts"]
	current_state["Portfolio gain (brutto)"] = current_state["Portfolio gain (netto)"] - current_state["Total fees"]

	current_state = pandas.Series(current_state).to_frame()
	current_state.columns = ["value"]

	portfolio_state = current_df.pivot_table(index=["symbol", "name"], values=["gain", "total", "pcs"], aggfunc=np.sum)
	portfolio_state["fraction"] = portfolio_state.total / portfolio_state.total.sum()
	portfolio_state = portfolio_state.sort_values("fraction", ascending=False)
	portfolio_state["fraction"] = portfolio_state.fraction.apply(lambda d: "{:0.1%}".format(d))
	
	def format_money(f):
		if pandas.isnull(f):
			return "n/a"
		return "{:3.2f}".format(f)
		return f
	for col in ("gain", "pcs", "total"):
		portfolio_state[col] = portfolio_state[col].apply(format_money)

	if as_html:
		current_state = current_state.to_html(classes="table text-right")
		portfolio_state = portfolio_state.to_html(classes="table text-right")
	
	return current_state, portfolio_state
		
