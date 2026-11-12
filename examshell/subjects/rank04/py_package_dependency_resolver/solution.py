def package_dependency_resolver(packages: dict[str, list[str]]) -> list[str]:
    # dependencies that exist in the input; missing ones are ignored
    remaining = {
        name: {d for d in deps if d in packages}
        for name, deps in packages.items()
    }
    if any(name in deps for name, deps in remaining.items()):
        return []  # self-dependency
    order = []
    # Kahn's algorithm, one wave at a time: every package whose dependencies
    # are all installed goes in, alphabetically
    while remaining:
        ready = sorted(name for name, deps in remaining.items() if not deps)
        if not ready:
            return []  # circular dependency
        for name in ready:
            del remaining[name]
        for deps in remaining.values():
            deps.difference_update(ready)
        order.extend(ready)
    return order
