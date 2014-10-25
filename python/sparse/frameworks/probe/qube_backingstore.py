#! /usr/bin/env python
# Alex Braun 04.13.2014

# ------------------------------------------------------------------------------
# The MIT License (MIT)

# Copyright (c) 2014 Alex Braun

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# ------------------------------------------------------------------------------

'''
.. module:: qube_backingstore
	:date: 04.13.2014
	:platform: Unix
	:synopsis: Qube BackingStore for interfacing with Probe API

.. moduleauthor:: Alex Braun <ABraunCCS@gmail.com>
'''
# ------------------------------------------------------------------------------

import warnings
import re
import json
import time
from copy import copy
from datetime import datetime
import numpy
import pandas
from pandas import DataFrame, Series

from sparse.core.sparse_dataframe import SparseDataFrame
from sparse.core.sparse_series import SparseSeries
from sparse.frameworks.probe.backingstore import BackingStore
from sparse.frameworks.probe.renderlog_backingstore import RenderLogBackingStore
from sparse.utilities.qube_utils import *
from sparse.utilities.utils import *
from sparse.utilities.errors import *
from sparse.frameworks.tune.tuner import Tuner
TUNER = Tuner()
qb = TUNER['qb']
# ------------------------------------------------------------------------------

class QubeBackingStore(BackingStore):
	def __init__(self, 
						jobinfo=False,
						hostinfo=False,
						supervisor=None,
						agenda=False,
						callbacks=False,
						fields=[],
						filters={},
						id=None,
						name=None,
						status=None,
						subjobs=False,
						embed_graphs=False):

		super(QubeBackingStore, self).__init__(name=name)
		self._cls = 'QubeBackingStore'

		self._jobinfo = jobinfo
		self._hostinfo = hostinfo
		self._supervisor = supervisor
		self._agenda = agenda
		self._callbacks = callbacks
		self._fields = fields
		self._filters = filters
		self._id = id
		self._name = name
		self._status = status
		self._subjobs = subjobs
		self._embed_graphs = embed_graphs
		self._database = qb
		self._data = None
		self._results = None

		self._database.setsupervisor(self._supervisor)
	# --------------------------------------------------------------------------

	def _get_agenda_stats(self, data):
		sdata = SparseDataFrame(data)
		sdata.merge_columns(['agenda', 'id'], 
			func=lambda x: get_agenda_stats(x[x.index[0]], x[x.index[1]], self._embed_graphs),
			new_column='agenda', inplace=True)
		sdata.flatten(columns=['agenda'], inplace=True)
		data = sdata.data
		return data

	def _get_log_data(self, data):
		mask = data['agenda_subids'].dropna()
		data.loc[mask.index, 'stdout_subids'] = data['id'].apply(lambda x: str(x))

		sdata = SparseDataFrame(data)
		sdata.merge_columns(['stdout_subids', 'agenda_subids'], 
			func=lambda x: create_complete_subids( x[x.index[0]], x[x.index[1]] ),
			new_column='stdout_subids', iterables=True, inplace=True)

		sdata.data['stdout'] = sdata.data['stdout_subids'].apply(lambda x: self._get_stdout_data(x))
		mask = sdata.data['stdout'].dropna()
		sdata.data['stdout'] = sdata.data['stdout'].apply(lambda x: self._get_stdout_stats(x))
		sdata.flatten(columns=['stdout'], inplace=True)
		data = sdata.data
		return data

	def _get_callbacks(self, data):
		sdata = SparseDataFrame(data)
		data = sdata.merge_columns(['pgrp', 'callbacks'], 
			func=lambda x: [ x[x.index[0]], x[x.index[1]] ], new_column='dependency')

		def _get_dependency(item):
			if item:
				pgrp = item[0]
				jobs = self._database.jobinfo(filters={'pgrp':pgrp})
				labels = {}
				for job in jobs:
					labels[job['label']] = job['id']
				output = []

				deps = json.loads(item[1])
				deps = deps['triggers'].split('and')
				if deps[0] not in [u'', '', None]:
					deps = [x.split('-')[2].strip(' ') for x in deps]
					for dep in deps:
						new_item = dep
						if dep in labels:
							new_item = labels[dep]
						output.append(new_item)
				else:
					output.append(pgrp)
				return output

			return numpy.nan
			
		data['dependency'] = data['dependency'].apply(lambda x: _get_dependency(x))
		return data

	def _get_stdout_data(self, item):
		temp = []
		if len(item) > 1:
			temp = self._database.stdout(item[0], *item[1:])
		else:
			temp = self._database.stdout(item[0])

		text = ''
		for t in temp:
			text += t['data']
		
		if text:
			return text
		else:
			return numpy.nan

	def _get_stdout_stats(self, item):
		output = {'progress': numpy.nan, 'warning': numpy.nan, 'error': numpy.nan}
		if item.__class__.__name__ == 'str':
			output = {}
			rbs = RenderLogBackingStore(text=item)
			rbs.update()
			data = rbs.data.data
			output['progress'] = ' '.join(data['progress'].unique().tolist())
			output['warning'] = ' '.join(data['warning'].unique().tolist())
			output['error'] = ' '.join(data['error'].unique().tolist())
		return output
	# --------------------------------------------------------------------------

	def _job_update(self):
		data = pandas.read_json(self._job_data, orient='records')
		data = data.applymap(lambda x: {} if x is None else x)

		sdata = SparseDataFrame(data)
		sdata.flatten(columns=['todotally'], inplace=True)
		data = sdata.data
		data = data.applymap(lambda x: str_to_nan(x))

		# Add custom fields
		data['procs'] = data['reservations'].apply(lambda x: get_procs(x))
		data['procs+'] = data['reservations'].apply(lambda x: get_plus_procs(x))
		data['ram'] = data['reservations'].apply(lambda x: get_ram(x))
		data['ram+'] = data['reservations'].apply(lambda x: get_plus_ram(x))
		data['failed_frame_total'] = data['todotally_failed']
		data['percent_done'] = data['todotally_complete'] / data['todo']
		data['percent_done'] = data['percent_done'].apply(lambda x: round_to(x, 3) * 100)
		data['percent_utilized'] = data['todotally_running'] / (data['todo'] - data['todotally_complete'])
		data['percent_utilized'] = data['percent_utilized'].apply(lambda x: round_to(x, 3) * 100)
		
		data['jobtype'] = data['name'].apply(lambda x: get_jobtype(x))

		# mask = data['status'].apply(lambda x: x in ['failed', 'running'])
		data['stdout_subids'] = numpy.nan
		# data['stdout_subids'][mask] = data['id'].apply(lambda x: str(x))

		data['stdout_subids'] = data['id'].apply(lambda x: str(x))

		if self._agenda:
			data = self._get_agenda_stats(data)
			data = self._get_log_data(data)

		if self._callbacks:
			data = self._get_callbacks(data)	

		data.fillna('', inplace=True)	
		data['probe_id'] = data.index
		data.reset_index(drop=True, inplace=True)

		sdata = SparseDataFrame(data)
		sdata.data.columns = TUNER.tune(sdata.data.columns, 'qube_backingstore')
		self._data = sdata

	@property
	def _job_data(self):
		jobs = self._database.jobinfo(fields=self._fields,
									  filters=self._filters,
									  id=self._id,
									  status=self._status,
									  agenda=self._agenda,
									  subjobs=self._subjobs,
								      callbacks=self._callbacks)
		jobs = json.dumps([dict(job) for job in jobs])
		return jobs
	# --------------------------------------------------------------------------

	def _host_update(self):
		data = json.loads(self._host_data)

		fields = []
		if self._subjobs:
			fields.append('subjobs')
		if fields:
			data = fix_missing_fields(data, fields)
			data = flatten_qube_field(data, fields)

		data = DataFrame(data)
		data = data.applymap(lambda x: numpy.nan if x is {} else x)
		data['slots'] = data['resources'].apply(lambda x: get_slots(x))
		data['subjobs'] = data['subjobs'].apply(lambda x: x[0])

		sdata = SparseDataFrame(data)
		data = sdata.flatten()

		slot_pct = data['slots_used'] / data['slots_total']
		slot_pct = slot_pct.apply(lambda x: 0 if x == float('inf') else x)
		data['slots_percent'] = slot_pct.apply(lambda x: round_to(x, 3) * 100.0)

		mask = data[data['state'] == 'active']
		
		lmask = mask[mask['slots_total'] == 0]
		data.loc[lmask.index, 'state'] = 'locked'
		
		imask = mask['subjobs_pid'].apply(lambda x: x in [0, None])
		imask  = mask[imask].dropna()
		data.loc[imask.index, 'state'] = 'idle'

		data.reset_index(drop=True, inplace=True)
		data['probe_id'] = data.index
		data.columns = TUNER.tune(data.columns, 'qube_backingstore')
		sdata.data = data

		self._data = sdata

	@property
	def _host_data(self):
		hosts = self._database.hostinfo(fields=self._fields,
										filters=self._filters,
										name=self._name,
										state=['active', 'down'],
										subjobs=True)
		hosts = json.dumps([dict(host) for host in hosts])
		return hosts

	@property
	def supervisor(self):
		return self._supervisor
	# --------------------------------------------------------------------------

	@property
	def source_data(self):
		if self._jobinfo:
			return self._job_data
		elif self._hostinfo:
			return self._host_data
		else:
			raise NotFound('Database not specified')

	def update(self):
		if self._jobinfo:
			self._job_update()
		elif self._hostinfo:
			self._host_update()
		else:
			raise NotFound('Database not specified')
	# --------------------------------------------------------------------------

	def set_priority(self, priority): 
		job_ids = self._results.data['id'].tolist()
		self._database.set_priority(job_ids, priority)
# ------------------------------------------------------------------------------

def main():
	'''
	Run help if called directly
	'''

	import __main__
	help(__main__)

__all__ = ['QubeBackingStore']

if __name__ == '__main__':
	main()