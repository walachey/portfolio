import datetime
import pytz
import io
import sys
import numpy as np
import pandas
import seaborn as sns

from .import load_data, plot, stats, crawl_data
from .template import get_template


def analyze_portfolio(transaction_df, etf_df, plot_output_path):
	plot.plot_cci(etf_df, transaction_df, save_path=plot_output_path + "cci.svg")

	merged_df = load_data.merge_transaction_and_etf_data(transaction_df, etf_df)
	global_state, symbol_state = stats.get_global_state(transaction_df, merged_df)

	plot.plot_development(transaction_df, merged_df, save_path=plot_output_path + "gains_development.svg", show_gains=True)
	plot.plot_development(transaction_df, merged_df, save_path=plot_output_path + "absolute_development.svg", show_gains=False)
	plot.plot_clustermap(transaction_df, merged_df, save_path=plot_output_path + "clustermap.png")
	plot.plot_portfolio_distribution(merged_df, save_path=plot_output_path + "distribution.png")

	return global_state, symbol_state

def update_and_analyze_portfolio(google_sheets_url, etf_data_path, plot_output_path, data_source):

	sns.set_palette("Set2")
	
	sys.stdout = event_logger = io.StringIO()
	transaction_df = crawl_data.load_transactions_from_google_sheets(google_sheets_url)

	etf_df = load_data.read_current_etf_information(etf_data_path)

	today = datetime.date.today()

	if today.weekday() == 0: # Monday.
		save_folder_path = etf_data_path
	else:
		save_folder_path = None

	etf_df = crawl_data.update_and_store_etf_data(transaction_df, etf_df, data_source=data_source, save_folder_path=save_folder_path)

	try:
		global_state, symbol_state = analyze_portfolio(transaction_df, etf_df, plot_output_path)
	except Exception as e:
		print("Unhandled exception: {}".format(str(e)))
		global_state, symbol_state = None, None

	template = get_template().render(
		today=today.isoformat(),
		log=event_logger.getvalue().replace("\n", "<br/>"),
		global_state=global_state, symbol_state=symbol_state)

	with open(plot_output_path + "index.html", "w") as f:
		f.write(template)

	
