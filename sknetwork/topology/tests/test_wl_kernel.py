#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Weisfeiler-Lehman kernels"""
import unittest

import numpy as np

from sknetwork.data import house, bow_tie, linear_graph
from sknetwork.topology import wl_isomorphism_test


class TestWLKernel(unittest.TestCase):

    def test_isomorphism(self):
        ref = house()
        n = ref.shape[0]

        adjacency = house()
        reorder = list(range(n))
        np.random.shuffle(reorder)
        adjacency = adjacency[reorder][:, reorder]
        self.assertTrue(wl_isomorphism_test(ref, adjacency))

        adjacency = bow_tie()
        self.assertFalse(wl_isomorphism_test(ref, adjacency))

        adjacency = linear_graph(n)
        self.assertFalse(wl_isomorphism_test(ref, adjacency))

        adjacency = linear_graph(n + 1)
        self.assertFalse(wl_isomorphism_test(ref, adjacency))
