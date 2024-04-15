from dijkstar import Graph, find_path
from typing import Callable
from copy import copy

INF = 9999999999


class Network:
    def __init__(self, name, tiers: list['Tier'], connections: list['Connection']):
        self.name = name
        self.tiers = tiers
        self.connections = connections
        self.graph = Graph(undirected=True)
        for connection in self.connections:
            self.graph.add_edge(connection.n1, connection.n2, connection)

    def get_nodes(self, tiers: int | list[int] = None):
        if isinstance(tiers, int):
            tiers = [tiers]
        if tiers is None:
            nodes = [self.tiers[tier_no].get_node(i) for tier_no in range(len(self.tiers))
                     for i in range(len(self.tiers[tier_no].nodes))]
        else:
            nodes = [self.tiers[tier_no - 1].get_node(i) for tier_no in tiers
                     for i in range(len(self.tiers[tier_no - 1].nodes))]
        return nodes

    def get_node(self, tier_no, index):
        return self.tiers[tier_no - 1].get_node(index)

    def get_shortest_path(self, source: 'Node', destination: 'Node',
                          cost_func: Callable[['Node', 'Node', 'Connection', 'Connection'], float | int]):
        return find_path(self.graph, source, destination, cost_func=cost_func)

    @classmethod
    def generate(cls, name, num_tiers: int, num_nodes_per_tier: list[int], default_connection_cap: list[float],
                 default_connectivity: list[int], asymmetries: dict[tuple[str]: float] = None):
        if asymmetries is None:
            asymmetries = dict()
        if len(num_nodes_per_tier) != num_tiers:
            raise ValueError("The number of nodes per tier does not match the number of tiers.")
        if len(default_connection_cap) != num_tiers - 1:
            raise ValueError("The default connection cap count specified does not match the number of tiers.")
        if len(default_connectivity) != num_tiers - 1:
            raise ValueError("The default connectivity count specified does not match the number of tiers.")
        tiers = list()
        node_num = 0
        for tier_no in range(num_tiers):
            tier = Tier(tier_no + 1, [])
            tiers.append(tier)
            for _ in range(num_nodes_per_tier[tier_no]):
                tier.add(Node(node_num, tier))
                node_num += 1

        connections = list()
        for tier_no in range(1, num_tiers):
            for i in range(len(tiers[tier_no].nodes)):
                node1 = tiers[tier_no].get_node(i)
                for c_num in range(default_connectivity[tier_no - 1]):
                    node2 = tiers[tier_no - 1].get_node((i + c_num) % len(tiers[tier_no - 1].nodes))
                    if asymmetries.get((node1.id, node2.id)) is not None:
                        cap = asymmetries.get((node1.id, node2.id))
                    else:
                        cap = default_connection_cap[tier_no - 1]
                    connections.append(Connection(node1, node2, cap))

        return cls(name, tiers, connections)


class Tier:
    def __init__(self, tier_id: int, nodes: list['Node']):
        self.nodes = nodes
        self.id = tier_id

    def add(self, node):
        self.nodes.append(node)

    def remove(self, node):
        self.nodes.remove(node)

    def get_node(self, index):
        return self.nodes[index]


class Node:
    index = dict()

    @staticmethod
    def get(node_id):
        return Node.index[node_id]

    def __init__(self, node_id: int, tier: Tier):
        self.id = node_id
        self.tier = tier
        Node.index[node_id] = self

    def __repr__(self):
        return str(self.id)


class Connection:
    index = dict()

    @staticmethod
    def get(n1_id, n2_id):
        return Connection.index[(n1_id, n2_id)]

    def __init__(self, node1, node2, capacity):
        self.n1 = node1
        self.n2 = node2
        self.cap = capacity
        self.flows = set()
        self.total_flow = 0
        self.avg_priority = 0
        Connection.index[(self.n1.id, self.n2.id)] = self

    def add_flow(self, flow: 'Flow'):
        self.flows.add(flow)
        self.avg_priority = ((self.avg_priority * self.total_flow + flow.priority * flow.size)
                             / (self.total_flow + flow.size))
        self.total_flow += flow.size

    def rm_flow(self, flow: 'Flow'):
        self.flows.remove(flow)
        self.avg_priority = 0 if self.total_flow == flow.size else (
                (self.avg_priority * self.total_flow - flow.priority * flow.size) / (self.total_flow - flow.size))
        self.total_flow -= flow.size

    def __repr__(self):
        return f"{self.n1.id}<-{self.cap}->{self.n2.id}"

    def get_exp_time(self):
        if self.total_flow < self.cap:
            return 1 / (self.cap - self.total_flow)
        else:
            return INF


class Flow:
    def __init__(self, source: Node, dest: Node, size: float, priority=1):
        self.source = source
        self.dest = dest
        self.priority = priority
        self.size = size
        self.path = []

    def assign_path(self, path: list['Connection']):
        for connection in self.path:
            connection.rm_flow(self)
        self.path = path
        for connection in self.path:
            connection.add_flow(self)

    def get_e2e_delay(self):
        return sum(c.get_exp_time() for c in self.path)

    def get_node_path(self):
        node_path = [self.source]
        for conn in self.path:
            node_path.append(conn.n2 if conn.n2 != node_path[-1] else conn.n1)
        return node_path

    def __repr__(self):
        return (f"Flow from node {self.source} to node {self.dest}, through the path {self.get_node_path()} "
                f"with e2e delay {self.get_e2e_delay()}")


class Solution:
    def __init__(self, network: 'Network', flows: list['Flow'], max_delay: float, priority_scale=1):
        self.net = network
        self.flows = flows
        self.max_delay = max_delay
        self.priority_scale = priority_scale

        for flow in self.flows:
            flow.priority = 1 + (flow.priority - 1) * priority_scale
            flow.assign_path(self.net.get_shortest_path(flow.source, flow.dest, cf_inverse_cap).edges)

        self.bestPaths = dict()
        self.bestAvgDelay = INF

    def is_feasible(self):
        for flow in self.flows:
            if flow.get_e2e_delay() > self.max_delay:
                return False
        return True

    def make_feasible(self):
        max_iter = 10
        iteration = 0
        while not self.is_feasible() and iteration < max_iter:
            iteration += 1
            for flow in self.flows:
                if flow.get_e2e_delay() > self.max_delay:
                    flow.assign_path(self.net.get_shortest_path(flow.source, flow.dest, cf_gen_flow_delay(flow)).edges)
        iteration = 0
        while not self.is_feasible() and iteration < max_iter:
            iteration += 1
            for flow in self.flows:
                if flow.get_e2e_delay() > self.max_delay:
                    buddies = set()  # The set of flows with which this flow shares at least one route
                    for conn in flow.path:
                        buddies.update(conn.flows)
                    buddies.remove(flow)

                    buddies = sorted(buddies, key=lambda b: b.size)  # Start from the smallest buddies

                    for buddy in buddies:
                        buddy.assign_path(self.net.get_shortest_path(
                            buddy.source, buddy.dest, cf_derivative).edges)
                        if flow.get_e2e_delay() <= self.max_delay:  # Stop when the desired delay is reached
                            break
        iteration = 0
        while not self.is_feasible() and iteration < max_iter:
            iteration += 1
            for flow in self.flows:
                if flow.get_e2e_delay() > self.max_delay:
                    flow.assign_path(self.net.get_shortest_path(flow.source, flow.dest, cf_gen_flow_delay(flow)).edges)

        if self.is_feasible():
            return True
        else:
            return False

    def get_avg_delay(self):
        weighted_delay = 0
        for conn in self.net.connections:
            weighted_delay += conn.total_flow * conn.get_exp_time() * conn.avg_priority

        traffic = 0
        for flow in self.flows:
            traffic += flow.size
        return weighted_delay/traffic

    def minimize_avg_delay(self):
        # Make sure to call this function after a feasible solution is reached
        for flow in self.flows:
            self.bestPaths[f"{flow.source}-{flow.dest}"] = copy(flow.path)
        self.bestAvgDelay = self.get_avg_delay()

        sim_ann_offshoot = 0.15
        sim_ann_cooling_factor = 0.8
        sim_ann_continue = True

        while sim_ann_continue:
            sim_ann_continue = False

            for flow in self.flows:  # TODO: Introduce randomness/prioritization here
                old_path = flow.path
                flow.assign_path(self.net.get_shortest_path(flow.source, flow.dest, cf_priority_derivative).edges)
                new_avg_delay = self.get_avg_delay()
                if new_avg_delay > self.bestAvgDelay * (1 + sim_ann_offshoot) or not self.is_feasible():
                    flow.assign_path(old_path)
                elif new_avg_delay < self.bestAvgDelay:
                    sim_ann_continue = True
                    for f in self.flows:
                        self.bestPaths[f"{f.source}-{f.dest}"] = copy(f.path)
                    self.bestAvgDelay = new_avg_delay

            sim_ann_offshoot *= sim_ann_cooling_factor

        for flow in self.flows:
            flow.assign_path(self.bestPaths[f"{flow.source}-{flow.dest}"])

    def __repr__(self):
        rep = ''
        for flow in S.flows:
            rep += str(flow) + '\n'
        return rep


def cf_inverse_cap(u: 'Node', v: 'Node', e: 'Connection', pe: 'Connection'):
    return 1 / e.cap


def cf_gen_flow_delay(flow):
    def cost_func(u: 'Node', v: 'Node', e: 'Connection', pe: 'Connection'):
        if flow in e.flows:
            return 1 / (e.cap - e.total_flow) if e.cap - e.total_flow > 0 else INF
        else:
            return 1 / (e.cap - e.total_flow - flow.size) if e.cap - e.total_flow - flow.size > 0 else INF
    return cost_func


def cf_derivative(u: 'Node', v: 'Node', e: 'Connection', pe: 'Connection'):
    return e.cap / (e.cap - e.total_flow)**2 if e.cap - e.total_flow > 0 else INF


def cf_priority_derivative(u: 'Node', v: 'Node', e: 'Connection', pe: 'Connection'):
    return e.cap * e.avg_priority / (e.cap - e.total_flow)**2 if e.cap - e.total_flow > 0 else INF


NT = Network.generate('NT', 3, [2, 3, 6], [200, 100],
                      [2, 2], {('8', '3'): 50, ('10', '4'): 50, ('6', '3'): 50})


f = [Flow(Node.get(5), Node.get(6), 10),
     Flow(Node.get(5), Node.get(8), 30, 2),
     Flow(Node.get(5), Node.get(10), 15, 2),
     Flow(Node.get(10), Node.get(5), 20, 3),
     Flow(Node.get(8), Node.get(6), 30),
     Flow(Node.get(0), Node.get(9), 50),
     Flow(Node.get(1), Node.get(9), 50),
     Flow(Node.get(0), Node.get(5), 15),
     Flow(Node.get(1), Node.get(8), 10, 3),
     Flow(Node.get(6), Node.get(9), 10, 2),
     Flow(Node.get(7), Node.get(8), 10),
     Flow(Node.get(7), Node.get(10), 15),
     Flow(Node.get(7), Node.get(5), 10),
     Flow(Node.get(0), Node.get(7), 20),
     Flow(Node.get(0), Node.get(10), 30),
     Flow(Node.get(9), Node.get(6), 10, 5)]

S = Solution(NT, f, 0.6)
print(S.get_avg_delay())
print(f"Solution is feasible = {S.make_feasible()}")
print(S)
print(S.get_avg_delay())
S.minimize_avg_delay()
print(S)
print(S.get_avg_delay())
