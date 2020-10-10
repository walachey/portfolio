def get_template():
	import jinja2

	return jinja2.Template(
		"""
<html>
<head>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">
<script src="https://code.jquery.com/jquery-3.5.1.min.js" integrity="sha256-9/aliU8dGd2tb6OSsuzixeV4y/faTqgFtohetphbbj0=" crossorigin="anonymous"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
<script type="text/javascript" src="http://kozea.github.com/pygal.js/latest/pygal-tooltips.min.js"></script>
</head>
<body>
<h1>Portfolio - {{ today }}</h1>
<h2>Overview</h2>
<div class="">
	<div class="row">
	<div class="col-md-4">{{ global_state }}</div>
	<div class="col-md-8">{{ symbol_state }}</div>
	</div>
</div>
<h2>Development</h2>
<div class="">
	<div class="row">
	<div class="col-md-7">
		<button class="switch-development btn btn-secondary">Toggle gains/total</button>
		<button class="switch-net-gross btn btn-secondary">Toggle net/gross</button>
		<div class="net_gross">
			<figure class="gains_total"><embed type="image/svg+xml" src="net_gains_development.svg" /></figure>
			<figure class="gains_total hidden"><embed type="image/svg+xml" src="net_absolute_development.svg" /></figure>
		</div>
		<div class="net_gross hidden">
			<figure class="gains_total"><embed type="image/svg+xml" src="gross_gains_development.svg" /></figure>
			<figure class="gains_total hidden"><embed type="image/svg+xml" src="gross_absolute_development.svg" /></figure>
		</div>
	</div>
	<div class="col-md-5"><img src="distribution.png" class="img-responsive" /></div>
	</div>
</div>
<h2>More</h2>
<div class="">
	<div class="row">
	<div class="col-md-5"><img src="clustermap.png" class="img-responsive" /></div>
	<div class="col-md-7"><figure><embed type="image/svg+xml" src="cci.svg" /></figure></div>
	</div>
</div>
<h2>Log</h2>
{{ log }}

<script>
$(document).ready(function() {
	$('.switch-development').on('click', function() {
		$('.switch-development').toggleClass('active');
		$('.gains_total').toggleClass('hidden');
		});
	$('.switch-net-gross').on('click', function() {
		$('.switch-net-gross').toggleClass('active');
		$('.net_gross').toggleClass('hidden');
		});
});
</script>
</body>
</html>
"""
		)