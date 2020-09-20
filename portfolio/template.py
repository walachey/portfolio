def get_template():
	import jinja2

	return jinja2.Template(
		"""
<html>
<head>
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
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
	<div class="col-md-7"><img src="gains_development.png" class="img-responsive"></img></div>
	<div class="col-md-5"><img src="distribution.png" class="img-responsive"></img></div>
	</div>
</div>
<h2>More</h2>
<div class="">
	<div class="row">
	<div class="col-md-5"><img src="clustermap.png" class="img-responsive"></img></div>
	<div class="col-md-7"><img src="cci.png" class="img-responsive"></img></div>
	</div>
</div>
<h2>Log</h2>
{{ log }}
</body>
</html>
"""
		)