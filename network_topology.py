class NetworkTopology:
    def __init__(self, name, nodes: list[list[str]] = None, connections: dict[tuple[str]: float] = None):
        if nodes is None:
            nodes = list()
        if connections is None:
            connections = list()
        self.name = name
        self.nodes = nodes
        self.connections = connections

    def get_nodes(self, tiers: int | list[int] = None):
        if isinstance(tiers, int):
            tiers = [tiers]
        if tiers is None:
            nodes = [self.nodes[tier][i] for tier in range(len(self.nodes)) for i in range(len(self.nodes[tier]))]
        else:
            nodes = [self.nodes[tier][i] for tier in tiers for i in range(len(self.nodes[tier]))]
        return nodes

    @classmethod
    def generate(cls, name, num_tiers: int, num_nodes_per_tier: list[int], default_connection_cap: list[float],
                 default_connectivity: list[int], asymmetries: dict[tuple[str]: float]):
        if len(num_nodes_per_tier) != num_tiers:
            raise ValueError("The number of nodes per tier does not match the number of tiers.")
        if len(default_connection_cap) != num_tiers - 1:
            raise ValueError("The default connection cap count specified does not match the number of tiers.")
        if len(default_connectivity) != num_tiers - 1:
            raise ValueError("The default connectivity count specified does not match the number of tiers.")
        nodes = list()
        for tier in range(num_tiers):
            nodes.append(list())
            for node_num in range(num_nodes_per_tier[tier]):
                nodes[-1].append(f'T{tier}_N{node_num}')

        connections = dict()
        for tier in range(0, num_tiers - 1):
            for i in range(len(nodes[tier])):
                node1 = nodes[tier][i]
                for c_num in range(default_connectivity[tier]):
                    node2 = nodes[tier + 1][(i + c_num) % len(nodes[tier + 1])]
                    if asymmetries.get((node1, node2)) is not None:
                        cap = asymmetries.get((node1, node2))
                    else:
                        cap = default_connection_cap[tier]
                    connections[(node1, node2)] = cap

        return cls(name, nodes, connections)


NT = NetworkTopology.generate('NT', 3, [5, 3, 2], [100, 200],
                              [2, 2], {('T0_N0', 'T1_N1'): 50})

print(NT.get_nodes(2))
print(NT.connections)

