def bridge_finder(graph: dict[int, list[int]]) -> list[tuple[int, int]]:
    # Tarjan: an edge u-v is a bridge when nothing below v reaches above it
    disc, low = {}, {}
    bridges = []
    timer = 0
    for root in graph:
        if root in disc:
            continue
        disc[root] = low[root] = timer
        timer += 1
        stack = [(root, None, iter(graph.get(root, [])))]
        while stack:
            node, parent, neighbours = stack[-1]
            advanced = False
            for nxt in neighbours:
                if nxt == parent:
                    continue
                if nxt in disc:
                    low[node] = min(low[node], disc[nxt])
                else:
                    disc[nxt] = low[nxt] = timer
                    timer += 1
                    stack.append((nxt, node, iter(graph.get(nxt, []))))
                    advanced = True
                    break
            if advanced:
                continue
            stack.pop()
            if parent is not None:
                low[parent] = min(low[parent], low[node])
                if low[node] > disc[parent]:
                    bridges.append((min(parent, node), max(parent, node)))
    return sorted(bridges)
