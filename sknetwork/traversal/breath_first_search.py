from sknetwork.model.graph import Graph
from collections import deque
from sknetwork.traversal.algo_traversal import AlgoTraversal


class BreathFirstSearchAlgo(AlgoTraversal):

    def __init__(self, graph):
        super().__init__()
        self._graph = graph
        self._discovered = {}

    def clear(self):
        self.parent = {}
        self._discovered = {}

    def iterator(self, source, process_vertex_early=False, process_edge=False, process_vertex_late=False):
        """
		BFS algorithm from source s
		inspired from http://www3.cs.stonybrook.edu/~skiena/algorist/book/

		Example
		-------
		>>>graph = { 0 : [1,4,5],
	          1 : [0,2,4],
	          2 : [1,3],
	          3 : [2,4],
	          4 : [0,1,3],
	          5 : [0]
	        }
		>>>g = Graph(graph)
		>>>bfs = BreathFirstSearchAlgo(g)
		>>>for i in bfs.iterator(1, process_vertex_early = True, process_edge = True):
			print(i)
		1
		(1, 0)
		(1, 2)
		(1, 4)
		0
		(0, 4)
		(0, 5)
		2
		(2, 3)
		4
		(4, 3)
		5
		3
		"""
        fifo_queue = deque([source])
        self._discovered = {source}
        processed = set()
        while fifo_queue:
            vertex = fifo_queue[0]
            if process_vertex_early:
                yield vertex
            processed.add(vertex)
            for neighbor in self._graph.graph_dict[vertex]:
                if (neighbor not in processed) or self._graph.directed:
                    if process_edge:
                        yield vertex, neighbor
                if (neighbor not in self._discovered):
                    fifo_queue.append(neighbor)
                    self._discovered.add(neighbor)
            fifo_queue.popleft()
            if process_vertex_late:
                yield vertex

    def tree(self, source, target=set()):
        """
		constructs the BFS tree from source and stops as soon as all elements in target have been found
		if target == set() then the full BFS tree is computed

		"""
        early_stopping = False
        if target:
            early_stopping = True

        self.parent = {i: -2 for i in self._graph.graph_dict.keys()}
        self.parent[source] = -1
        for (vertex, neighbor) in self.iterator(source, process_edge=True):
            if neighbor not in self._discovered:
                self.parent[neighbor] = int(vertex)
                if early_stopping:
                    target = target.difference({neighbor})
                    if target == set():
                        break

    def find_path_BFS(self, a, b):
        """
        find the shortest unweighted path between node a to node b
        :param a:
        :param b:
        :return:
        """
        self.tree(a, {b})
        self.find_path(a, b)

    def connected_components(self):
        """
		print the connected components
		TODO put the label of the component to each vertex and remove print.
		move to algo_traversal? can be used with dfs...ABC class
		https://www.python-course.eu/python3_abstract_classes.php
		:return: number of components, one seed per component
		"""
        self.clear()
        number_components = 0
        seeds = []
        for node in self._graph.graph_dict.keys():
            if node not in self._discovered:
                number_components += 1
                seeds.append(node)
                print('Component {}:'.format(number_components))
                for vertex in self.iterator(node, process_vertex_early=True):
                    print('{}|'.format(vertex), end='')
                print()
        return number_components, seeds