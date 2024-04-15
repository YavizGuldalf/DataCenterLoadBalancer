from dijkstar import Graph, find_path
from typing import Callable

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
            nodes = [self.tiers[tier_no-1].get_node(i) for tier_no in tiers
                     for i in range(len(self.tiers[tier_no-1].nodes))]
        return nodes

    def get_node(self, tier_no, index):
        return self.tiers[tier_no-1].get_node(index)

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
            tier = Tier(str(tier_no + 1), [])
            tiers.append(tier)
            for _ in range(num_nodes_per_tier[tier_no]):
                tier.add(Node(str(node_num), tier))
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
                    connections.append(Connection(f"{node1.id}-{node2.id}", node1, node2, cap))

        return cls(name, tiers, connections)


class Tier:
    def __init__(self, tier_id: str, nodes: list['Node']):
        self.nodes = nodes
        self.id = tier_id

    def add(self, node):
        self.nodes.append(node)

    def remove(self, node):
        self.nodes.remove(node)

    def get_node(self, index):
        return self.nodes[index]


class Node:
    def __init__(self, node_id: str, tier: Tier):
        self.id = node_id
        self.tier = Tier

    def __repr__(self):
        return self.id


class Connection:
    def __init__(self, connection_id, node1, node2, capacity, flows: list['Flow'] = None):
        self.n1 = node1
        self.n2 = node2
        self.id = connection_id
        self.cap = capacity
        self.flows = flows
        self.length = 1/capacity

    def __repr__(self):
        return f"{self.n1.id}<-{self.cap}->{self.n2.id}"

    def get_total_flow(self):
        return sum([f.size for f in self.flows])

    def get_exp_time(self):
        tf = self.get_total_flow()
        if tf < self.cap:
            return 1 / (self.cap - tf)
        else:
            return INF


class Flow:
    def __init__(self, source: Node, dest: Node, size, priority=1):
        self.source = source
        self.dest = dest
        self.priority = priority
        self.size = size
        self.path = []

    def assign_path(self, path: list['Connection']):
        self.path = path

    def get_e2e_delay(self):
        return sum(c.get_exp_time for c in self.path)


NT = Network.generate('NT', 3, [2, 3, 6], [200, 100],
                      [2, 2], {('7', '2'): 10})

print(NT.connections)
print(NT.graph)
print(NT.get_shortest_path(NT.get_node(3, 2), NT.get_node(3, 0),
                           lambda u, v, e, pe: 1/e.cap))
