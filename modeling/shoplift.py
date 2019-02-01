CLASSES = {
    0: "Face-or-head",
    1: "Left-hand",
    2: "Right-hand",
    3: "Body"
}
STATES = {
    0: "Lookout",
    1: "Talking-to-someone",
    2: "Taking-objects",
    3: "Open-bag-pocket",
    4: "Close-bag-pocket",
    5: "Pointing",
    6: "Using-phones",
    7: "Put-sth-into-bag-pocket",
    8: "Walking",
    9: "Running",
    10: "Standing"
}

_CLASSES = {}
for k in CLASSES:
    _CLASSES[CLASSES[k]] = k
_STATES = {}
for k in STATES:
    _STATES[STATES[k]] = k

CLASS_TO_STATE = {
    0: [0,1],
    1: [2,3,4,5,6,7],
    2: [2,3,4,5,6,7],
    3: [8,9,10]
}
STATE_TO_CLASS = {
    0: 0,
    1: 0,
    2: [1,2],
    3: [1,2],
    4: [1,2],
    5: [1,2],
    6: [1,2],
    7: [1,2],
    8: 3,
    9: 3,
    10: 3
}