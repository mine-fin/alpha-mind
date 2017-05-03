# -*- coding: utf-8 -*-
"""
Created on 2017-5-3

@author: cheng.li
"""

import math
import numpy as np
import numba as nb


def groupby(groups):
    a = np.arange(groups.shape[0])
    order_group_idx = groups.argsort()
    counts = np.bincount(groups)
    ret = np.split(a[order_group_idx], np.cumsum(counts)[:-1])
    return ret


@nb.njit(nogil=True, cache=True)
def simple_sum(x, axis=0):
    length, width = x.shape

    if axis == 0:
        res = np.zeros(width)
        for i in range(length):
            for j in range(width):
                res[j] += x[i, j]

    elif axis == 1:
        res = np.zeros(length)
        for i in range(length):
            for j in range(width):
                res[i] += x[i, j]
    return res


@nb.njit(nogil=True, cache=True)
def simple_mean(x, axis=0):
    length, width = x.shape

    if axis == 0:
        res = np.zeros(width)
        for j in range(width):
            for i in range(length):
                res[j] += x[i, j]
            res[j] /= length

    elif axis == 1:
        res = np.zeros(length)
        for i in range(length):
            for j in range(width):
                res[i] += x[i, j]
            res[i] /= width
    return res


@nb.njit(nogil=True, cache=True)
def simple_std(x, axis=0, ddof=1):
    length, width = x.shape

    if axis == 0:
        res = np.zeros(width)
        sum_mat = np.zeros(width)
        for j in range(width):
            for i in range(length):
                res[j] += x[i, j] * x[i, j]
                sum_mat[j] += x[i, j]
            res[j] = math.sqrt((res[j] - sum_mat[j] * sum_mat[j] / length) / (length - ddof))
    elif axis == 1:
        res = np.zeros(length)
        sum_mat = np.zeros(width)
        for i in range(length):
            for j in range(width):
                res[i] += x[i, j] * x[i, j]
                sum_mat[i] += x[i, j]
            res[i] = math.sqrt((res[i] - sum_mat[i] * sum_mat[i] / width) / (width - ddof))
    return res


@nb.njit(nogil=True, cache=True)
def agg_sum(groups, x):
    max_g = groups.max()
    length, width = x.shape
    res = np.zeros((max_g+1, width), dtype=np.float64)

    for i in range(length):
        for j in range(width):
            res[groups[i], j] += x[i, j]
    return res


@nb.njit(nogil=True, cache=True)
def agg_abssum(groups, x):
    max_g = groups.max()
    length, width = x.shape
    res = np.zeros((max_g+1, width), dtype=np.float64)

    for i in range(length):
        for j in range(width):
            res[groups[i], j] += abs(x[i, j])
    return res


@nb.njit(nogil=True, cache=True)
def agg_mean(groups, x):
    max_g = groups.max()
    length, width = x.shape
    res = np.zeros((max_g+1, width), dtype=np.float64)
    bin_count = np.zeros(max_g+1, dtype=np.int32)

    for i in range(length):
        for j in range(width):
            res[groups[i], j] += x[i, j]
        bin_count[groups[i]] += 1

    for i in range(max_g+1):
        curr = bin_count[i]
        for j in range(width):
            res[i, j] /= curr
    return res


@nb.njit(nogil=True, cache=True)
def agg_std(groups, x, ddof=1):
    max_g = groups.max()
    length, width = x.shape
    res = np.zeros((max_g+1, width), dtype=np.float64)
    sumsq = np.zeros((max_g + 1, width), dtype=np.float64)
    bin_count = np.zeros(max_g+1, dtype=np.int32)

    for i in range(length):
        for j in range(width):
            res[groups[i], j] += x[i, j]
            sumsq[groups[i], j] += x[i, j] * x[i, j]
        bin_count[groups[i]] += 1

    for i in range(max_g+1):
        curr = bin_count[i]
        for j in range(width):
            res[i, j] = math.sqrt((sumsq[i, j] - res[i, j] * res[i, j] / curr) / (curr - ddof))
    return res


@nb.njit(nogil=True, cache=True)
def copy_value(groups, source):
    length = groups.shape[0]
    width = source.shape[1]
    destination = np.zeros((length, width))
    for i in range(length):
        k = groups[i]
        for j in range(width):
            destination[i, j] = source[k, j]
    return destination


def transform(groups, x, func, ddof=1):

    if func == 'mean':
        value_data = agg_mean(groups, x)
    elif func == 'std':
        value_data = agg_std(groups, x, ddof=ddof)
    elif func == 'sum':
        value_data = agg_sum(groups, x)
    elif func =='abssum':
        value_data = agg_abssum(groups, x)
    else:
        raise ValueError('({0}) is not recognized as valid functor'.format(func))

    return copy_value(groups, value_data)


def aggregate(groups, x, func, ddof=1):
    if func == 'mean':
        value_data = agg_mean(groups, x)
    elif func == 'std':
        value_data = agg_std(groups, x, ddof=ddof)
    elif func == 'sum':
        value_data = agg_sum(groups, x)
    elif func =='abssum':
        value_data = agg_abssum(groups, x)
    else:
        raise ValueError('({0}) is not recognized as valid functor'.format(func))

    return value_data


if __name__ == '__main__':
    n_samples = 6000
    n_features = 10
    n_groups = 30
    groups = np.random.randint(n_groups, size=n_samples)
    max_g = n_groups - 1
    x = np.random.randn(n_samples, n_features)

    import datetime as dt
    start = dt.datetime.now()
    for i in range(1000):
        res = aggregate(groups, x, 'mean')
    print(dt.datetime.now() - start)

    #transform = nb.jit(transform)

    start = dt.datetime.now()

    for i in range(1000):
        res = aggregate(groups, x, 'mean')
    print(dt.datetime.now() - start)