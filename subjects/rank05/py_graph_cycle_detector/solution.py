def py_graph_cycle_detector(graph: dict[int, list[int]]) -> bool:
    WHITE, GREY, BLACK = 0, 1, 2
    color = {}
    for start in graph:
        if color.get(start, WHITE) != WHITE:
            continue
        # iterative DFS: (node, iterator over its neighbours)
        color[start] = GREY
        stack = [(start, iter(graph.get(start, [])))]
        while stack:
            node, neighbours = stack[-1]
            for nxt in neighbours:
                state = color.get(nxt, WHITE)
                if state == GREY:
                    return True  # back edge
                if state == WHITE:
                    color[nxt] = GREY
                    stack.append((nxt, iter(graph.get(nxt, []))))
                    break
            else:
                color[node] = BLACK
                stack.pop()
    return False
