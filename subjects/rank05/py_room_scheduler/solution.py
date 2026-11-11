from typing import Any


def py_room_scheduler(meetings: list[list[int]]) -> dict[str, Any]:
    rooms = []  # each room: its meetings, in order
    for start, end in sorted(meetings, key=lambda m: m[0]):
        for room in rooms:
            if room[-1][1] <= start:  # free again: its last meeting has ended
                room.append([start, end])
                break
        else:
            rooms.append([[start, end]])
    return {"total_rooms": len(rooms), "schedule": rooms}
