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
.. module:: utils
	:date: 04.13.2014
	:platform: Unix
	:synopsis: General Python utilities

.. moduleauthor:: Alex Braun <ABraunCCS@gmail.com>
'''
# ------------------------------------------------------------------------------

import warnings
import re
from decimal import Decimal
import numpy
import pandas
from pandas import DataFrame
from collections import OrderedDict, namedtuple
# ------------------------------------------------------------------------------

class Base(object):
	'''
	Generic base class
	'''
	def __init__(self, name=None):
		'''
		:kwarg name: name of instance
		:returns: Base instance
		:rtype: Base
		'''
		self._cls = 'Base'
		self._name = name

	@property
	def cls(self):
		'''
		class of instance
		'''
		return self._cls

	@property
	def name(self):
		'''
		name of instance
		'''
		return self._name

	def _printPublic(self):
		nonPublicRE = re.compile('^_')
		for item in dir(self):
			found = nonPublicRE.match(item)
			if not found:
				print item

	def _printSemiPrivate(self):
		semiPrivateRE = re.compile('^_[^_]+')
		for item in dir(self):
			found = semiPrivateRE.match(item)
			if found:
				print item

	def _printPrivate(self):
		privateRE = re.compile('^__')
		for item in dir(self):
			found = privateRE.match(item)
			if found:
				print item
# ------------------------------------------------------------------------------

def to_type(item, dtype):
	try:
		return dtype(item)
	except ValueError:
		return item

def is_iterable(item):
	try:
		result = iter(item)
		return True
	except TypeError:
		return False

def make_iterable(item):
	if is_iterable(item):
		return item
	else:
		return [item]

def iprint(iterable):
	for item in iterable:
		print item

def keep_type(item, func):
	return item.dtypes.type(func(item))

def set_decimal_expansion(item, expansion):
	return int(item * 10 ** expansion) / float(10 ** expansion)

def try_(item, func):
	try:
		return func(item)
	except:
		return item

def round_to(item, order):
	return round(Decimal(item), order)

def eval_(item):
	try:
		return eval(item)
	except:
		return item
# ------------------------------------------------------------------------------

def _eq(item, value):
	return item == value

def _ne(item, value):
	return item != value

def _lt(item, value):
	return item < value

def _lte(item, value):
	return item <= value

def _gt(item, value):
	return item > value

def _gte(item, value):
	return item >= value

def _re(item, value):
	found = re.search(str(value), str(item))
	if found:
		return True
	else:
		return False

def _reig(item, value):
	found = re.search(str(value), str(item), re.IGNORECASE)
	if found:
		return True
	else:
		return False

def _nre(item, value):
	found = re.search(str(value), str(item))
	if not found:
		return True
	else:
		return False

def _nreig(item, value):
	found = re.search(str(value), str(item), re.IGNORECASE)
	if not found:
		return True
	else:
		return False

OPERATORS = {'==': _eq, '!=': _ne, '<': _lt, '<=': _lte, '>': _gt, '>=': _gte, 
			're': _re, 're.IGNORECASE': _reig, 'nre': _nre, 'nre.IGNORECASE': _nreig}

def bool_test(item, operator, values):
	op = OPERATORS[operator]
	values = make_iterable(values)
	for value in values:
		if op(item, value):
			return True
	return False
# ------------------------------------------------------------------------------

def regex_match(pattern, string, group=0, ignore_case=False):
	if ignore_case:
		regex = re.compile(pattern, re.IGNORECASE)
	else:
		regex = re.compile(pattern)
	found = regex.match(string)
	if found:
		return found.group(group)
	else:
		return string

def regex_search(pattern, string, group=0, ignore_case=False):
	if ignore_case:
		regex = re.compile(pattern, re.IGNORECASE)
	else:
		regex = re.compile(pattern)
	found = regex.search(string)
	if found:
		return found.group(group)
	else:
		return string

def regex_sub(pattern, repl, string, count=0, ignore_case=False):
	if ignore_case:
		return re.sub(pattern, repl, string, count, re.IGNORECASE)
	else:
		return re.sub(pattern, repl, string, count)

def regex_split(pattern, string, ignore_case=False):
	if ignore_case:
		regex = re.compile(pattern, re.IGNORECASE)
	else:
		regex = re.compile(pattern)
	found = regex.search(string)
	if found:
		return list(found.groups())
	else:
		return string
# ------------------------------------------------------------------------------

def invert(iterable):
	patterns = sorted(list(set(iterable)))
	inversion_map = dict(zip(patterns, [x for x in reversed(patterns)]))
	return [inversion_map[x] for x in iterable]

def reduce_units(iterable, new_unit='-', min=0):
	old = sorted(set(iterable))
	new = range(0, len(old))
	new = [new_unit * (x + min) for x in new]
	lut = dict(zip(old, new))
	return [lut[x] for x in iterable]

def dict_to_namedtuple(name, dict):
    tup = namedtuple(name, dict.keys())
    return tup(*dict.values())

def flatten_nested_dict(item, separator='_', null='null'):
    temp = OrderedDict()
    def _flatten_nested_dict(item, name):
        for key, val in item.iteritems():
            if type(val) is dict and val != {}:
                temp[name + separator + str(key)] = null
                _flatten_nested_dict(val, name + separator + str(key))
            else:
                temp[name + separator + str(key)] = val
    _flatten_nested_dict(item, '__null__')
    output = OrderedDict()
    header = 8 + len(separator)
    for key, value in temp.iteritems():
    	output[key[header:]] = value
    return output

def nested_dict_to_index(item, name):
    index = flatten_nested_dict(item, name, separator='__null__')
    index = [x.split('__null__') for x in index.keys()]
    max_ = 0
    for item in index:
        if len(item) > max_:
            max_ = len(item)
    for item in index:
        while len(item) < max_:
            item.append('-->')
    index = DataFrame(index).transpose().values.tolist()
    return index

def interpret_nested_dict(item, predicate):
	def _interpret_nested_dict(item, cursor):
		for key, val in item.iteritems():
			if type(val) is dict and val != {}:
				cursor[key] = _interpret_nested_dict(val, val)
			else:
				cursor[key] = predicate(val)
		return cursor
	return _interpret_nested_dict(item, {})
# ------------------------------------------------------------------------------

def irregular_concat(items, axis=0, ignore_index=True):
	max_len = 0
	for item in items:
		if len(item) > max_len:
			max_len = len(item)
	
	for item in items:
		bufr = item.head(1)
		bufr = bufr.apply(lambda x: numpy.nan)
		buf_len = max_len - len(item)
		for i in range(buf_len):
			if ignore_index:
				item.append(bufr, ignore_index=True)
			else:
				item.append(bufr)
	
	data = pandas.concat(items, axis=axis)
	return data
# ------------------------------------------------------------------------------

def double_lut_transform(items, input_lut, output_lut):
	# Check luts and issue warnings/errors if necessary
    if input_lut.keys() != output_lut.keys():
        raise KeyError('input lut keys do not match output lut keys')
    if len(set(input_lut.values() )) != len(input_lut.values()):
        warnings.warn('input lut has non-unique values', Warning)
    if len(set(output_lut.values() )) != len(output_lut.values()):
        warnings.warn('output lut has non-unique values', Warning)
        
    reverse_lut = dict(zip(input_lut.values(), input_lut.keys() ))       
    output = []
    for item in items:
        new_item = item
        if item in reverse_lut.keys():
            new_item = output_lut[reverse_lut[item]]
        output.append(new_item)
    return output
# ------------------------------------------------------------------------------

def main():
	'''
	Run help if called directly
	'''

	import __main__
	help(__main__)

__all__ = ['Base', 'to_type', 'is_iterable', 'make_iterable', 'iprint',
			'keep_type', 'set_decimal_expansion', 'try_', 'round_to', 'eval_',
			'bool_test', 'regex_match', 'regex_search', 'regex_sub', 
			'dict_to_namedtuple', 'flatten_nested_dict', 'nested_dict_to_index',
			'interpret_nested_dict', 'irregular_concat', 'double_lut_transform']

if __name__ == '__main__':
	main()