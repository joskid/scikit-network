#!/usr/bin/env python3
# coding: utf-8
"""
Created on Jun 2020
@author: Victor Manach <victor.manach@telecom-paris.fr>
@author: Rémi Jaylet <remi.jaylet@telecom-paris.fr>
"""
from typing import Optional, Union

import numpy as np
from scipy import sparse

from sknetwork.embedding.base import BaseEmbedding
from sknetwork.utils import directed2undirected
from sknetwork.utils.check import check_format, is_symmetric, check_square


class ForceAtlas2(BaseEmbedding):

    def __init__(self, n_iter: int = 50, lin_log: bool = False, k_gravity: float = 0.01, strong_gravity: bool = False,
                 k_repulsive: int = 0.01, exponent: int = 0, no_hubs: bool = False, tolerance: float = 0.1,
                 k_speed: float = 0.01):
        super(ForceAtlas2, self).__init__()
        self.n_iter = n_iter
        self.lin_log = lin_log
        self.k_gravity = k_gravity
        self.strong_gravity = strong_gravity
        self.k_repulsive = k_repulsive
        self.exponent = exponent
        self.no_hubs = no_hubs
        self.tolerance = tolerance
        self.k_speed = k_speed

    def fit(self, adjacency: Union[sparse.csr_matrix, np.ndarray], n_iter: Optional[int] = None,
            lin_log: Optional[bool] = None, k_gravity: Optional[float] = None, strong_gravity: Optional[bool] = None,
            k_repulsive: Optional[int] = None, exponent: Optional[int] = None, no_hubs: Optional[bool] = None,
            tolerance: Optional[float] = None, k_speed: Optional[float] = None) -> 'ForceAtlas2':
        """Compute layout.

        Parameters
        ----------
        adjacency :
            Adjacency matrix of the graph, treated as undirected.
        n_iter : int
            Number of iterations to update positions.
            If ``None``, use the value of self.n_iter.
        lin_log :
            If True, activate an alternative formula for the attractive force
        k_gravity :
            Gravity force scaling constant
        strong_gravity :
            If True, activate an alternative formula for the gravity force
        k_repulsive :
            Repulsive force scaling constant
        exponent :
            If different to 0, modify attraction force, the weights are raised to the power of 'exponent'
        no_hubs :
            If True, change the value of the attraction force
        tolerance :
            Tolerance defined in the swinging constant
        k_speed :
            Speed constant


        Returns
        -------
        self: :class:`ForceAtlas2`
        """
        adjacency = check_format(adjacency)
        check_square(adjacency)
        if not is_symmetric(adjacency):
            adjacency = directed2undirected(adjacency)
        n = adjacency.shape[0]

        # setting of the tolerance according to the size of the graph
        if n < 5000:
            tolerance = 0.1
        elif 5000 <= n < 50000:
            tolerance = 1
        else:
            tolerance = 10

        # initial position of the nodes of the graph
        position = np.random.randn(n, 2)

        if n_iter is None:
            n_iter = self.n_iter
        if lin_log is None:
            lin_log = self.lin_log
        if k_gravity is None:
            k_gravity = self.k_gravity
        if strong_gravity is None:
            strong_gravity = self.strong_gravity
        if k_repulsive is None:
            k_repulsive = self.k_repulsive
        if exponent is None:
            exponent = self.exponent
        if no_hubs is None:
            no_hubs = self.no_hubs
        if tolerance is None:
            tolerance = self.tolerance
        if k_speed is None:
            k_speed = self.k_speed
        deg = adjacency.dot(np.ones(adjacency.shape[1])) + 1

        # definition of the step
        delta_x: float = position[:, 0].max() - position[:, 0].min()  # max variation /x
        delta_y: float = position[:, 1].max() - position[:, 1].min()  # max variation /y
        step_max: float = max(delta_x, delta_y)
        step: float = step_max / (n_iter + 1)

        delta = np.zeros((n, 2))  # initialization of variation of position of nodes
        forces_for_each_node = np.zeros(n)
        swing_vector = np.zeros(n)
        global_speed = 1
        attraction = np.zeros(n)

        for iteration in range(n_iter):
            delta *= 0
            global_swing = 0
            global_traction = 0
            for i in range(n):
                attraction *= 0
                indices = adjacency.indices[adjacency.indptr[i]:adjacency.indptr[i + 1]]

                grad: np.ndarray = (position[i] - position)  # shape (n, 2)
                distance: np.ndarray = np.linalg.norm(grad, axis=1)  # shape (n,)
                distance = np.where(distance < 0.01, 0.01, distance)

                attraction[indices] = 10 * distance[indices]  # change attraction of connected nodes
                # The lin_log mode calculates the attraction force
                if lin_log:
                    attraction = np.log(1 + attraction)

                if exponent != 0:
                    data = adjacency.data[adjacency.indptr[i]:adjacency.indptr[i + 1]]
                    attraction = (data**exponent)*attraction

                if no_hubs:
                    attraction = attraction / (deg[i] + 1)

                repulsion = k_repulsive * (deg[i] + 1) * deg / distance
                gravity = k_gravity * (deg + 1)
                if strong_gravity:
                    gravity = gravity * distance

                force = repulsion.sum() - attraction.sum() - gravity.sum()  # forces resultant applied on node i

                swing_node = np.abs(force - forces_for_each_node[i])  # force variation applied on node i
                swing_vector[i] = swing_node
                traction = np.abs(force + forces_for_each_node[i]) / 2  # traction force applied on node i

                global_swing += (deg[i] + 1) * swing_node
                global_traction += (deg[i] + 1) * traction

                node_speed = k_speed * global_speed / (1 + global_speed * np.sqrt(swing_node))

                forces_for_each_node[i] = force  # force resultant update

                # delta[i]: np.ndarray = node_speed * force
                delta[i]: np.ndarray = (grad * node_speed * (repulsion - attraction - gravity)[:, np.newaxis]).sum(
                    axis=0)  # shape (2,)

            global_speed = tolerance * global_traction / global_swing  # computation of global variables
            length = np.linalg.norm(delta, axis=0)
            length = np.where(length < 0.01, 0.1, length)
            delta = delta * step_max / length  # normalisation of distance between nodes
            position += delta  # calculating displacement and final position of points after iteration
            step_max -= step
            if (swing_vector < 0.01).all():
                break  # If the swing of all nodes is zero, then convergence is reached and we break.

        self.embedding_ = position
        return self
