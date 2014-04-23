#! /usr/bin/env python
# Alex Braun 04.23.2014

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
.. module:: SparseDataFrame
	:date: 04.13.2014
	:platform: Unix
	:synopsis: Special subclass of pandas DataFrame for sparse data aggregation
	
.. moduleauthor:: Alex Braun <ABraunCCS@gmail.com>
'''
# ------------------------------------------------------------------------------

from __future__ import with_statement
import re
import pandas
from pandas import DataFrame, Series
import numpy
from sparse.utilities.Utils import *
from sparse.model.SpQLParser import SpQLParser
# ------------------------------------------------------------------------------

class SparseDataFrame(DataFrame, Base):
	def __init__(self, data=None, index=None, columns=None, dtype=None, copy=False, name=None):
		super(SparseDataFrame, self).__init__(data=None, index=None, columns=None, dtype=None, copy=False)
		self._cls = 'SparseDataFrame'
	# --------------------------------------------------------------------------

	def to_type(self, dtype, inplace=False):
		data = self.applymap(lambda x: to_type(x, dtype))

		if inplace:
			self = data
		return data

	def is_iterable(self, inplace=False):
		data = self.applymap(lambda x: is_iterable(x))

		if inplace:
			self = data
		return data

	def make_iterable(self, inplace=False):
		data = self.applymap(lambda x: make_iterable(x))

		if inplace:
			self = data
		return data	
	# --------------------------------------------------------------------------
	
	def regex_match(self, pattern, group=0, ignore_case=False, inplace=False):
		data = self.applymap(lambda x: regex_match(pattern, x, group, ignore_case=ignore_case))

		if inplace:
			self = data
		return data

	def regex_search(self, pattern, group=0, ignore_case=False, inplace=False):
		data = self.applymap(lambda x: regex_search(pattern, x, group, ignore_case=ignore_case))

		if inplace:
			self = data
		return data

	def regex_sub(self, pattern, repl, group=0, count=0, ignore_case=False, inplace=False):
		data = self.applymap(lambda x: regex_sub(pattern, repl, x, group, ignore_case=ignore_case))

		if inplace:
			self = data
		return data

	def regex_split(self, pattern, ignore_case=False, inplace=False):
		data = self.applymap(lambda x: regex_split(pattern, x, ignore_case=ignore_case))

		if inplace:
			self = data
		return data
	# --------------------------------------------------------------------------

	def flatten(self, dtype=dict, prefix=True, inplace=False):
		mask = self.applymap(lambda x: bool_test(type(x), '==', dtype))
		iterables = self[mask]
		iterables = iterables.dropna(how='all', axis=1)

		new_data = self.drop(iterables.columns, axis=1)
		frames = [new_data]
		for col in iterables.columns:
			frame = DataFrame(self[col].tolist())
			if prefix:
				columns = {}
				for k in frame.columns:
					columns[k] = str(col) + '_' + str(k)
				frame.rename(columns=columns)
			frames.append(frame)
		data = pandas.concat(frames, axis=1)
		
		if inplace:
			self = data
		return data

	def drop_by_mask(self, mask, how='all', axis=0, inplace=False):
		mask = self[mask]
		mask = mask.dropna(how=how, axis=axis)
		data = None
		if axis = 0:
			data = self.ix[mask.index]
		if axis = 1:
			data = self[mask.columns]
		data.reset_index(drop=True, inplace=True)

		if inplace:
			self = data
		return data
	# --------------------------------------------------------------------------

	def spql_search(self, string, field_operator='re', inplace=False):
		spql = SpQLInterpreter()
		spql.search(string)
		data = spql.dataframe_query(self, field_operator=field_operator)
		
		if inplace:
			self = data
		return data
# ------------------------------------------------------------------------------

def main():
	'''
	Run help if called directly
	'''
	
	import __main__
	help(__main__)

__all__ = ['SparseDataFrame']

if __name__ == '__main__':
	main()