from sparse.frameworks.probe.qube_backingstore import QubeBackingStore

CONFIG = {
'probe_cli': {
	'target_path': 'sparse/python/sparse/views/probe_cli.py',
	'line_width': 500,
	  'max_rows': 1000},
'probe': {
	'target_path': 'sparse/bin/probe',
	'prompt': 'SpQL[ ]>',
	'backingstores': {
		'qube': QubeBackingStore}
	}
}