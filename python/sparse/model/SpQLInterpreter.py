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
.. module:: SpQLInterpreter
	:date: 04.13.2014
	:platform: Unix
	:synopsis: Sparse Query Langauge interpreter
	
.. moduleauthor:: Alex Braun <ABraunCCS@gmail.com>
'''
# ------------------------------------------------------------------------------

from pyparsing import printables
from pyparsing import Word, Keyword, Or, Group
from pyparsing import delimitedList, oneOf, OneOrMore, Suppress
from sparse.model.SpQLParser import SpQLParser
# ------------------------------------------------------------------------------

class SpQLInterpreter(SpQLParser):
	
	def __init__(self, name=None):
		super(SpQLInterpreter, self).__init__(name=name)
		self._cls = 'SpQLInterpreter'

	def _gen_mongo_query(self, fields, operator, values):
		ops = {'==': '$in', '!=': '$ne', '>': '$gt', '<': '$lt', 're': '$regex',
		'nre': '$regex', 're.IGNORECASE': '$regex', 'nre.IGNORECASE': '$regex'}

		op = ops[operator]
		subquiries = []
		for field in fields:
			for value in values:
				subquery = {}
				subquery[field] = {op: value}
				if 'IGNORECASE' in operator:
					subquery[field]['$options'] = 'i'
				subquiries.append(subquery)

		mod_op = '$or'
		if 'nre' in operator:
			mod_op = '$not'

		return {'$match': {mod_op: subquiries}}

	@property
	def mongo_query(self):
		return [self._gen_mongo_query(q['fields'], q['operator'], q['values']) for q in self._last_query]
	# --------------------------------------------------------------------------

	def _gen_dataframe_query(self, dataframe, fields=['all'], operator='==', values=[''], field_operator='=='):
		if fields == ['all']:
			mask = dataframe.applymap(lambda x: bool_test(x, operator, values))
			mask[mask == False] = numpy.nan
			mask.dropna(how='any', inplace=True)
			return dataframe.ix[mask.index]

		columns = dataframe.columns.to_series()
		mask = columns.apply(lambda x: bool_test(x, field_operator, fields))
		columns = columns[mask].toList()

		mask = dataframe[columns].applymap(lambda x: bool_test(x, operator, values))
		mas[mask == False] = numpy.nan
		mask.dropna(how='any', inplace=True)
		dataframe = dataframe.ix[mask.index]
		dataframe = dataframe.dropna(how='all', axis=1)
		return dataframe

	@property
	def dataframe_query(self, dataframe, field_operator='=='):
		for q in self._last_query:
			dataframe = self._gen_dataframe_query(dataframe, q['fields'], q['operator'], q['values'], field_operator=field_operator)
		return dataframe
# ------------------------------------------------------------------------------

def main():
	'''
	Run help if called directly
	'''
	
	import __main__
	help(__main__)

__all__ = ['SpQLInterpreter']

if __name__ == '__main__':
	main()