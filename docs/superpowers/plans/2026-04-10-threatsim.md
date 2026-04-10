# ThreatSim Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build ThreatSim — a 2D real-time battlefield awareness simulator in Python with pygame, configurable JSON scenarios, a threat state machine, and a full pytest suite.

**Architecture:** Class hierarchy with a central `Simulation` class. Entity types (Aircraft, RadarEmitter, SAMSite, NoFlyZone) inherit from `BaseEntity`/`ThreatEntity`. `Renderer` is a pure display consumer. `config.py` is the only JSON-touching code.

**Tech Stack:** Python 3.10+, pygame 2.5+, pytest 7+, pyproject.toml (setuptools)

---

## File Map

```
threatsim/
  __init__.py
  cli.py
  simulation.py
  renderer.py
  config.py
  entities/
    __init__.py
    base.py
    threat_state.py
    aircraft.py
    radar.py
    sam.py
    noflyzone.py

scenarios/
  default.json

tests/
  __init__.py
  test_aircraft.py
  test_radar.py
  test_sam.py
  test_noflyzone.py
  test_config.py
  test_simulation.py

pyproject.toml
README.md
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `threatsim/__init__.py`
- Create: `threatsim/entities/__init__.py`
- Create: `tests/__init__.py`
- Create: `scenarios/` (empty dir placeholder)

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "threatsim"
version = "0.1.0"
description = "2D real-time threat environment simulator"
readme = "README.md"
requires-python = ">=3.10"
dependencies = ["pygame>=2.5"]

[project.scripts]
threatsim = "threatsim.cli:main"

[project.optional-dependencies]
dev = ["pytest>=7"]

[tool.setuptools.packages.find]
where = ["."]
include = ["threatsim*"]
```

- [ ] **Step 2: Create empty package init files**

`threatsim/__init__.py` — empty file.

`threatsim/entities/__init__.py` — empty file.

`tests/__init__.py` — empty file.

- [ ] **Step 3: Install package in editable mode**

Run: `pip install -e ".[dev]"`

Expected: installs `threatsim` and `pytest` with no errors.

- [ ] **Step 4: Verify pytest can discover the package**

Run: `pytest --collect-only`

Expected: `no tests ran` (collection succeeds with zero tests found — that's correct at this stage).

---

## Task 2: ThreatState Enum

**Files:**
- Create: `threatsim/entities/threat_state.py`
- Create: `tests/test_radar.py` (first test written here)

- [ ] **Step 1: Write the failing test**

`tests/test_radar.py`:
```python
from threatsim.entities.threat_state import ThreatState


def test_threat_state_members():
    assert ThreatState.SEARCHING is not None
    assert ThreatState.TRACKING is not None
    assert ThreatState.ENGAGING is not None


def test_threat_state_ordering():
    # States have a natural severity order
    states = [ThreatState.SEARCHING, ThreatState.TRACKING, ThreatState.ENGAGING]
    assert states[0].value < states[1].value < states[2].value
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_radar.py -v`

Expected: `ModuleNotFoundError` — `threat_state` not yet defined.

- [ ] **Step 3: Create `threatsim/entities/threat_state.py`**

```python
from enum import IntEnum


class ThreatState(IntEnum):
    SEARCHING = 0
    TRACKING = 1
    ENGAGING = 2
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_radar.py::test_threat_state_members tests/test_radar.py::test_threat_state_ordering -v`

Expected: 2 passed.

---

## Task 3: BaseEntity

**Files:**
- Create: `threatsim/entities/base.py`

No standalone tests — BaseEntity is abstract. Covered by subclass tests.

- [ ] **Step 1: Create `threatsim/entities/base.py`**

```python
from abc import ABC, abstractmethod


class BaseEntity(ABC):
    def __init__(self, id: str, position: tuple[float, float]) -> None:
        self.id = id
        self.position = position

    @abstractmethod
    def update(self, dt: float) -> None:
        ...
```

- [ ] **Step 2: Verify import works**

Run: `python -c "from threatsim.entities.base import BaseEntity; print('ok')" `

Expected: `ok`

---

## Task 4: ThreatEntity and RadarEmitter

**Files:**
- Create: `threatsim/entities/radar.py`
- Modify: `tests/test_radar.py`

`update_state(aircraft_pos)` is the interface used everywhere — ThreatEntity computes distance internally; NoFlyZone will override with polygon logic.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_radar.py`:
```python
import math
from threatsim.entities.radar import RadarEmitter
from threatsim.entities.threat_state import ThreatState


def _make_radar(pos=(500, 500), detection=150, engagement=75):
    return RadarEmitter(
        id="r1", name="TEST RADAR", position=pos,
        detection_radius=detection, engagement_radius=engagement,
    )


def test_radar_initial_state_is_searching():
    r = _make_radar()
    assert r.state == ThreatState.SEARCHING


def test_radar_transitions_to_tracking():
    r = _make_radar(pos=(500, 500), detection=150, engagement=75)
    # Place aircraft just inside detection radius
    aircraft_pos = (500 + 140, 500)
    r.update_state(aircraft_pos)
    assert r.state == ThreatState.TRACKING


def test_radar_transitions_to_engaging():
    r = _make_radar(pos=(500, 500), detection=150, engagement=75)
    aircraft_pos = (500 + 50, 500)
    r.update_state(aircraft_pos)
    assert r.state == ThreatState.ENGAGING


def test_radar_reverts_to_searching():
    r = _make_radar(pos=(500, 500), detection=150, engagement=75)
    r.update_state((500 + 50, 500))   # ENGAGING
    assert r.state == ThreatState.ENGAGING
    r.update_state((500 + 200, 500))  # outside detection — back to SEARCHING
    assert r.state == ThreatState.SEARCHING


def test_radar_boundary_exactly_at_detection_radius():
    r = _make_radar(pos=(0, 0), detection=100, engagement=50)
    # Exactly at boundary: dist == detection_radius → TRACKING
    r.update_state((100.0, 0.0))
    assert r.state == ThreatState.TRACKING


def test_radar_update_does_not_move():
    r = _make_radar(pos=(500, 500))
    r.update(dt=1.0)
    assert r.position == (500, 500)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_radar.py -v`

Expected: `ModuleNotFoundError` for `radar`.

- [ ] **Step 3: Create `threatsim/entities/radar.py`**

```python
import math
from threatsim.entities.base import BaseEntity
from threatsim.entities.threat_state import ThreatState


class ThreatEntity(BaseEntity):
    """Base for all stationary threat entities."""

    def __init__(self, id: str, name: str, position: tuple[float, float]) -> None:
        super().__init__(id=id, position=position)
        self.name = name
        self.state: ThreatState = ThreatState.SEARCHING

    def update_state(self, aircraft_pos: tuple[float, float]) -> None:
        """Recompute threat state based on aircraft position. Override for non-radial threats."""
        raise NotImplementedError

    def update(self, dt: float) -> None:
        # Stationary — no position update needed.
        pass


class RadarEmitter(ThreatEntity):
    def __init__(
        self,
        id: str,
        name: str,
        position: tuple[float, float],
        detection_radius: float,
        engagement_radius: float,
    ) -> None:
        super().__init__(id=id, name=name, position=position)
        self.detection_radius = detection_radius
        self.engagement_radius = engagement_radius

    def update_state(self, aircraft_pos: tuple[float, float]) -> None:
        dist = math.hypot(
            aircraft_pos[0] - self.position[0],
            aircraft_pos[1] - self.position[1],
        )
        if dist <= self.engagement_radius:
            self.state = ThreatState.ENGAGING
        elif dist <= self.detection_radius:
            self.state = ThreatState.TRACKING
        else:
            self.state = ThreatState.SEARCHING
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_radar.py -v`

Expected: all 8 tests pass.

---

## Task 5: SAMSite

**Files:**
- Create: `threatsim/entities/sam.py`
- Create: `tests/test_sam.py`

SAMSite is identical to RadarEmitter in behaviour — differs only in visual. Reuse `RadarEmitter.update_state` via inheritance.

- [ ] **Step 1: Write the failing tests**

`tests/test_sam.py`:
```python
from threatsim.entities.sam import SAMSite
from threatsim.entities.threat_state import ThreatState


def _make_sam(pos=(400, 400), detection=200, engagement=100):
    return SAMSite(
        id="s1", name="SA-6", position=pos,
        detection_radius=detection, engagement_radius=engagement,
    )


def test_sam_initial_state():
    s = _make_sam()
    assert s.state == ThreatState.SEARCHING


def test_sam_tracking():
    s = _make_sam(pos=(400, 400), detection=200, engagement=100)
    s.update_state((400 + 150, 400))
    assert s.state == ThreatState.TRACKING


def test_sam_engaging():
    s = _make_sam(pos=(400, 400), detection=200, engagement=100)
    s.update_state((400 + 80, 400))
    assert s.state == ThreatState.ENGAGING


def test_sam_is_distinct_type_from_radar():
    from threatsim.entities.radar import RadarEmitter
    s = _make_sam()
    assert not isinstance(s, RadarEmitter)
    assert isinstance(s, SAMSite)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_sam.py -v`

Expected: `ModuleNotFoundError` for `sam`.

- [ ] **Step 3: Create `threatsim/entities/sam.py`**

```python
from threatsim.entities.radar import RadarEmitter


class SAMSite(RadarEmitter):
    """Surface-to-Air Missile site. Same state machine as RadarEmitter; different visual."""
    pass
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_sam.py -v`

Expected: 4 passed.

---

## Task 6: NoFlyZone

**Files:**
- Create: `threatsim/entities/noflyzone.py`
- Create: `tests/test_noflyzone.py`

Uses ray-casting point-in-polygon and minimum distance to polygon edge.

- [ ] **Step 1: Write the failing tests**

`tests/test_noflyzone.py`:
```python
from threatsim.entities.noflyzone import NoFlyZone
from threatsim.entities.threat_state import ThreatState

# Square polygon: (100,100) to (200,200)
SQUARE = [(100, 100), (200, 100), (200, 200), (100, 200)]


def _make_nfz(polygon=SQUARE, approach_radius=30):
    return NoFlyZone(
        id="nfz1", name="NFZ ALPHA",
        polygon=polygon, approach_radius=approach_radius,
    )


def test_nfz_initial_state():
    nfz = _make_nfz()
    assert nfz.state == ThreatState.SEARCHING


def test_nfz_searching_when_far():
    nfz = _make_nfz(approach_radius=30)
    nfz.update_state((0, 0))  # far from square
    assert nfz.state == ThreatState.SEARCHING


def test_nfz_tracking_when_near_boundary():
    nfz = _make_nfz(approach_radius=30)
    # Aircraft 15 units outside the left edge (x=100), well within approach_radius
    nfz.update_state((85, 150))
    assert nfz.state == ThreatState.TRACKING


def test_nfz_engaging_when_inside():
    nfz = _make_nfz()
    nfz.update_state((150, 150))  # centre of square
    assert nfz.state == ThreatState.ENGAGING


def test_nfz_reverts_to_tracking_when_exits_polygon():
    nfz = _make_nfz(approach_radius=30)
    nfz.update_state((150, 150))   # inside → ENGAGING
    assert nfz.state == ThreatState.ENGAGING
    nfz.update_state((85, 150))    # outside but within approach → TRACKING
    assert nfz.state == ThreatState.TRACKING


def test_nfz_reverts_to_searching():
    nfz = _make_nfz(approach_radius=30)
    nfz.update_state((150, 150))   # ENGAGING
    nfz.update_state((0, 0))       # far away → SEARCHING
    assert nfz.state == ThreatState.SEARCHING


def test_nfz_position_is_centroid():
    nfz = _make_nfz()
    # centroid of (100,100)-(200,200) square is (150,150)
    assert nfz.position == (150.0, 150.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_noflyzone.py -v`

Expected: `ModuleNotFoundError` for `noflyzone`.

- [ ] **Step 3: Create `threatsim/entities/noflyzone.py`**

```python
import math
from threatsim.entities.radar import ThreatEntity
from threatsim.entities.threat_state import ThreatState


def _point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Ray-casting algorithm. Returns True if point is inside polygon."""
    x, y = point
    inside = False
    n = len(polygon)
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def _dist_to_segment(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Minimum distance from point p to line segment ab."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _min_dist_to_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> float:
    """Minimum distance from point to any edge of polygon."""
    n = len(polygon)
    return min(
        _dist_to_segment(point, polygon[i], polygon[(i + 1) % n])
        for i in range(n)
    )


def _centroid(polygon: list[tuple[float, float]]) -> tuple[float, float]:
    n = len(polygon)
    cx = sum(p[0] for p in polygon) / n
    cy = sum(p[1] for p in polygon) / n
    return (cx, cy)


class NoFlyZone(ThreatEntity):
    def __init__(
        self,
        id: str,
        name: str,
        polygon: list[tuple[float, float]],
        approach_radius: float,
    ) -> None:
        super().__init__(id=id, name=name, position=_centroid(polygon))
        self.polygon = polygon
        self.approach_radius = approach_radius

    def update_state(self, aircraft_pos: tuple[float, float]) -> None:
        if _point_in_polygon(aircraft_pos, self.polygon):
            self.state = ThreatState.ENGAGING
        elif _min_dist_to_polygon(aircraft_pos, self.polygon) <= self.approach_radius:
            self.state = ThreatState.TRACKING
        else:
            self.state = ThreatState.SEARCHING
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_noflyzone.py -v`

Expected: 7 passed.

---

## Task 7: Aircraft — Basic Movement

**Files:**
- Create: `threatsim/entities/aircraft.py`
- Create: `tests/test_aircraft.py`

Build movement mechanics first (position update, heading, turn rate), then waypoint logic in Task 8.

- [ ] **Step 1: Write the failing tests**

`tests/test_aircraft.py`:
```python
import math
from threatsim.entities.aircraft import Aircraft


def _make_aircraft(**kwargs):
    defaults = dict(
        id="ac1",
        name="VIPER 01",
        start_position=(0.0, 0.0),
        speed=100.0,
        heading=0.0,
        turn_rate=90.0,
        waypoints=[(1000.0, 0.0)],
        hold_radius=30.0,
        arrival_threshold=10.0,
    )
    defaults.update(kwargs)
    return Aircraft(**defaults)


def test_aircraft_initial_position():
    ac = _make_aircraft(start_position=(50.0, 100.0))
    assert ac.position == (50.0, 100.0)


def test_aircraft_moves_in_heading_direction():
    ac = _make_aircraft(start_position=(0.0, 0.0), speed=100.0, heading=0.0)
    ac.update(dt=1.0)
    x, y = ac.position
    assert abs(x - 100.0) < 0.01
    assert abs(y) < 0.01


def test_aircraft_heading_90_moves_down():
    # heading=90 → +y direction (clockwise convention, y-axis pointing down in screen coords)
    ac = _make_aircraft(start_position=(0.0, 0.0), speed=100.0, heading=90.0,
                        waypoints=[(0.0, 1000.0)])
    ac.update(dt=1.0)
    x, y = ac.position
    assert abs(x) < 0.01
    assert abs(y - 100.0) < 0.01


def test_turn_rate_is_clamped_per_tick():
    ac = _make_aircraft(heading=0.0, turn_rate=45.0, waypoints=[(0.0, 1000.0)])
    initial_heading = ac.heading
    ac.update(dt=1.0)
    delta = abs(ac.heading - initial_heading)
    # Should turn at most turn_rate * dt = 45 degrees in one second
    assert delta <= 45.0 + 1e-6


def test_turn_rate_clamped_small_dt():
    ac = _make_aircraft(heading=0.0, turn_rate=90.0, waypoints=[(0.0, 1000.0)])
    ac.update(dt=0.1)
    delta = abs(ac.heading - 0.0)
    assert delta <= 90.0 * 0.1 + 1e-6


def test_track_history_grows_each_tick():
    ac = _make_aircraft()
    assert len(ac.track_history) == 0
    ac.update(dt=0.1)
    assert len(ac.track_history) == 1
    ac.update(dt=0.1)
    assert len(ac.track_history) == 2


def test_track_history_capped_at_500():
    ac = _make_aircraft()
    for _ in range(600):
        ac.update(dt=0.016)
    assert len(ac.track_history) <= 500
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_aircraft.py -v`

Expected: `ModuleNotFoundError` for `aircraft`.

- [ ] **Step 3: Create `threatsim/entities/aircraft.py`**

```python
import math
from threatsim.entities.base import BaseEntity

_TRACK_MAX = 500


def _angle_diff(target: float, current: float) -> float:
    """Signed angular difference in degrees, normalised to [-180, 180]."""
    return (target - current + 180.0) % 360.0 - 180.0


class Aircraft(BaseEntity):
    def __init__(
        self,
        id: str,
        name: str,
        start_position: tuple[float, float],
        speed: float,
        heading: float,
        turn_rate: float,
        waypoints: list[tuple[float, float]],
        hold_radius: float = 30.0,
        arrival_threshold: float = 10.0,
    ) -> None:
        super().__init__(id=id, position=start_position)
        self.name = name
        self.speed = speed
        self.heading = heading
        self.turn_rate = turn_rate
        self.waypoints = waypoints
        self.hold_radius = hold_radius
        self.arrival_threshold = arrival_threshold
        self.current_waypoint_index: int = 0
        self.track_history: list[tuple[float, float]] = []
        self._in_hold: bool = False
        self._hold_center: tuple[float, float] | None = None
        self._hold_angle: float = 0.0  # radians

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bearing_to(self, target: tuple[float, float]) -> float:
        """Bearing in degrees from current position to target (clockwise from +x)."""
        dx = target[0] - self.position[0]
        dy = target[1] - self.position[1]
        return math.degrees(math.atan2(dy, dx)) % 360.0

    def _move(self, dt: float) -> None:
        rad = math.radians(self.heading)
        x, y = self.position
        self.position = (x + math.cos(rad) * self.speed * dt,
                         y + math.sin(rad) * self.speed * dt)

    def _enter_hold(self) -> None:
        self._in_hold = True
        self._hold_center = self.waypoints[-1]
        dx = self.position[0] - self._hold_center[0]
        dy = self.position[1] - self._hold_center[1]
        self._hold_angle = math.atan2(dy, dx)

    def _update_hold(self, dt: float) -> None:
        omega = self.speed / self.hold_radius  # rad/s
        self._hold_angle += omega * dt
        cx, cy = self._hold_center  # type: ignore[misc]
        self.position = (
            cx + self.hold_radius * math.cos(self._hold_angle),
            cy + self.hold_radius * math.sin(self._hold_angle),
        )
        self.heading = math.degrees(self._hold_angle + math.pi / 2) % 360.0

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if self._in_hold:
            self._update_hold(dt)
        else:
            target = self.waypoints[self.current_waypoint_index]
            bearing = self._bearing_to(target)
            error = _angle_diff(bearing, self.heading)
            max_turn = self.turn_rate * dt
            self.heading = (self.heading + max(-max_turn, min(max_turn, error))) % 360.0
            self._move(dt)
            dist = math.hypot(target[0] - self.position[0], target[1] - self.position[1])
            if dist < self.arrival_threshold:
                if self.current_waypoint_index < len(self.waypoints) - 1:
                    self.current_waypoint_index += 1
                else:
                    self._enter_hold()

        self.track_history.append(self.position)
        if len(self.track_history) > _TRACK_MAX:
            self.track_history.pop(0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_aircraft.py -v`

Expected: 7 passed.

---

## Task 8: Aircraft — Waypoint Navigation and Hold Orbit

**Files:**
- Modify: `tests/test_aircraft.py` (append tests)

- [ ] **Step 1: Append waypoint and hold orbit tests**

Append to `tests/test_aircraft.py`:
```python
def test_aircraft_advances_waypoint_on_arrival():
    ac = _make_aircraft(
        start_position=(0.0, 0.0),
        speed=200.0,
        heading=0.0,
        turn_rate=360.0,
        waypoints=[(5.0, 0.0), (1000.0, 0.0)],
        arrival_threshold=10.0,
    )
    # Run enough ticks to reach first waypoint (5 units away at 200 u/s)
    for _ in range(20):
        ac.update(dt=0.05)
    assert ac.current_waypoint_index == 1


def test_aircraft_reaches_final_waypoint_and_enters_hold():
    ac = _make_aircraft(
        start_position=(0.0, 0.0),
        speed=300.0,
        heading=0.0,
        turn_rate=360.0,
        waypoints=[(5.0, 0.0)],
        arrival_threshold=10.0,
        hold_radius=30.0,
    )
    for _ in range(30):
        ac.update(dt=0.05)
    assert ac._in_hold is True


def test_aircraft_hold_orbit_stays_near_center():
    ac = _make_aircraft(
        start_position=(0.0, 0.0),
        speed=100.0,
        heading=0.0,
        turn_rate=360.0,
        waypoints=[(5.0, 0.0)],
        arrival_threshold=10.0,
        hold_radius=30.0,
    )
    # Trigger hold by running until arrived
    for _ in range(50):
        ac.update(dt=0.05)
    assert ac._in_hold is True
    hold_center = ac.waypoints[-1]
    # Orbit for several full circles
    for _ in range(200):
        ac.update(dt=0.05)
        cx, cy = hold_center
        dist_from_center = math.hypot(ac.position[0] - cx, ac.position[1] - cy)
        assert abs(dist_from_center - ac.hold_radius) < 1.0, (
            f"Aircraft drifted: dist={dist_from_center:.2f}, hold_radius={ac.hold_radius}"
        )
```

- [ ] **Step 2: Run new tests to verify they fail or pass**

Run: `pytest tests/test_aircraft.py -v`

Expected: all 10 tests pass (the implementation already covers these).

If any fail, debug the hold orbit entry condition — the aircraft's arrival check fires when `dist < arrival_threshold` not `<=`, so ensure the approach speed and dt produce a step small enough to trigger it.

---

## Task 9: Config Loader

**Files:**
- Create: `threatsim/config.py`
- Create: `tests/test_config.py`
- Create: `scenarios/default.json`

- [ ] **Step 1: Write failing tests**

`tests/test_config.py`:
```python
import json
import pathlib
import tempfile
import pytest
from threatsim.config import load_scenario, ConfigError
from threatsim.entities.aircraft import Aircraft
from threatsim.entities.radar import RadarEmitter
from threatsim.entities.sam import SAMSite
from threatsim.entities.noflyzone import NoFlyZone

VALID_SCENARIO = {
    "window": {"width": 1200, "height": 800},
    "aircraft": {
        "id": "ac1",
        "name": "VIPER 01",
        "start_position": [100, 400],
        "speed": 120,
        "heading": 0,
        "turn_rate": 45,
        "hold_radius": 30,
        "arrival_threshold": 10,
        "waypoints": [[300, 200], [600, 350]],
    },
    "threats": [
        {"type": "radar", "id": "r1", "name": "EW RADAR",
         "position": [400, 300], "detection_radius": 150, "engagement_radius": 75},
        {"type": "sam", "id": "s1", "name": "SA-6",
         "position": [700, 250], "detection_radius": 200, "engagement_radius": 100},
        {"type": "noflyzone", "id": "nfz1", "name": "NFZ ALPHA",
         "polygon": [[500, 100], [650, 100], [650, 220], [500, 220]],
         "approach_radius": 50},
    ],
}


def _write_temp(data: dict) -> pathlib.Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(data, f)
    f.close()
    return pathlib.Path(f.name)


def test_load_valid_scenario():
    path = _write_temp(VALID_SCENARIO)
    result = load_scenario(path)
    assert isinstance(result["aircraft"], Aircraft)
    assert len(result["threats"]) == 3
    assert result["window"] == {"width": 1200, "height": 800}


def test_threat_types_are_correct():
    path = _write_temp(VALID_SCENARIO)
    result = load_scenario(path)
    threats = result["threats"]
    assert isinstance(threats[0], RadarEmitter)
    assert isinstance(threats[1], SAMSite)
    assert isinstance(threats[2], NoFlyZone)


def test_aircraft_fields_loaded_correctly():
    path = _write_temp(VALID_SCENARIO)
    ac = load_scenario(path)["aircraft"]
    assert ac.id == "ac1"
    assert ac.speed == 120
    assert ac.turn_rate == 45
    assert ac.waypoints == [(300, 200), (600, 350)]


def test_missing_aircraft_raises_config_error():
    data = {**VALID_SCENARIO}
    del data["aircraft"]
    path = _write_temp(data)
    with pytest.raises(ConfigError, match="aircraft"):
        load_scenario(path)


def test_missing_aircraft_field_raises_config_error():
    data = json.loads(json.dumps(VALID_SCENARIO))
    del data["aircraft"]["speed"]
    path = _write_temp(data)
    with pytest.raises(ConfigError, match="speed"):
        load_scenario(path)


def test_unknown_threat_type_raises_config_error():
    data = json.loads(json.dumps(VALID_SCENARIO))
    data["threats"][0]["type"] = "missile"
    path = _write_temp(data)
    with pytest.raises(ConfigError, match="missile"):
        load_scenario(path)


def test_missing_threat_required_field_raises_config_error():
    data = json.loads(json.dumps(VALID_SCENARIO))
    del data["threats"][0]["detection_radius"]
    path = _write_temp(data)
    with pytest.raises(ConfigError, match="detection_radius"):
        load_scenario(path)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`

Expected: `ModuleNotFoundError` for `config`.

- [ ] **Step 3: Create `threatsim/config.py`**

```python
import json
import pathlib
from threatsim.entities.aircraft import Aircraft
from threatsim.entities.radar import RadarEmitter
from threatsim.entities.sam import SAMSite
from threatsim.entities.noflyzone import NoFlyZone


class ConfigError(Exception):
    pass


_AIRCRAFT_REQUIRED = ["id", "start_position", "speed", "heading", "turn_rate", "waypoints"]
_RADAR_SAM_REQUIRED = ["id", "name", "position", "detection_radius", "engagement_radius"]
_NFZ_REQUIRED = ["id", "name", "polygon", "approach_radius"]
_THREAT_REQUIRED: dict[str, list[str]] = {
    "radar": _RADAR_SAM_REQUIRED,
    "sam": _RADAR_SAM_REQUIRED,
    "noflyzone": _NFZ_REQUIRED,
}
_THREAT_CLASSES = {"radar": RadarEmitter, "sam": SAMSite}


def _require(data: dict, fields: list[str], context: str) -> None:
    for f in fields:
        if f not in data:
            raise ConfigError(f"{context}: missing required field '{f}'")


def _build_aircraft(data: dict) -> Aircraft:
    _require(data, _AIRCRAFT_REQUIRED, "aircraft")
    return Aircraft(
        id=data["id"],
        name=data.get("name", data["id"]),
        start_position=tuple(data["start_position"]),
        speed=data["speed"],
        heading=data["heading"],
        turn_rate=data["turn_rate"],
        waypoints=[tuple(w) for w in data["waypoints"]],
        hold_radius=data.get("hold_radius", 30.0),
        arrival_threshold=data.get("arrival_threshold", 10.0),
    )


def _build_threat(data: dict):
    t_type = data.get("type")
    if t_type not in _THREAT_REQUIRED:
        raise ConfigError(f"Unknown threat type: '{t_type}'")
    _require(data, _THREAT_REQUIRED[t_type], f"threat '{data.get('id', '?')}'")

    if t_type in _THREAT_CLASSES:
        cls = _THREAT_CLASSES[t_type]
        return cls(
            id=data["id"],
            name=data["name"],
            position=tuple(data["position"]),
            detection_radius=data["detection_radius"],
            engagement_radius=data["engagement_radius"],
        )
    # noflyzone
    return NoFlyZone(
        id=data["id"],
        name=data["name"],
        polygon=[tuple(p) for p in data["polygon"]],
        approach_radius=data["approach_radius"],
    )


def load_scenario(path: str | pathlib.Path) -> dict:
    with open(path) as f:
        raw = json.load(f)

    aircraft_data = raw.get("aircraft")
    if not aircraft_data:
        raise ConfigError("Missing required section 'aircraft'")

    aircraft = _build_aircraft(aircraft_data)
    threats = [_build_threat(t) for t in raw.get("threats", [])]
    window = raw.get("window", {"width": 1200, "height": 800})

    return {"aircraft": aircraft, "threats": threats, "window": window}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`

Expected: 7 passed.

- [ ] **Step 5: Create `scenarios/default.json`**

```json
{
  "window": { "width": 1200, "height": 800 },
  "aircraft": {
    "id": "friendly-1",
    "name": "VIPER 01",
    "start_position": [60, 400],
    "speed": 80,
    "heading": 0,
    "turn_rate": 45,
    "hold_radius": 40,
    "arrival_threshold": 12,
    "waypoints": [
      [250, 200],
      [500, 320],
      [750, 150],
      [950, 350]
    ]
  },
  "threats": [
    {
      "type": "radar",
      "id": "radar-1",
      "name": "EW RADAR",
      "position": [320, 280],
      "detection_radius": 160,
      "engagement_radius": 80
    },
    {
      "type": "sam",
      "id": "sam-1",
      "name": "SA-6",
      "position": [620, 430],
      "detection_radius": 200,
      "engagement_radius": 100
    },
    {
      "type": "sam",
      "id": "sam-2",
      "name": "SA-10",
      "position": [820, 250],
      "detection_radius": 180,
      "engagement_radius": 90
    },
    {
      "type": "noflyzone",
      "id": "nfz-1",
      "name": "NFZ ALPHA",
      "polygon": [[430, 80], [600, 80], [600, 200], [430, 200]],
      "approach_radius": 40
    }
  ]
}
```

---

## Task 10: Simulation

**Files:**
- Create: `threatsim/simulation.py`
- Create: `tests/test_simulation.py`

- [ ] **Step 1: Write failing tests**

`tests/test_simulation.py`:
```python
import math
from threatsim.simulation import Simulation
from threatsim.entities.aircraft import Aircraft
from threatsim.entities.radar import RadarEmitter
from threatsim.entities.threat_state import ThreatState


def _make_sim(aircraft_pos=(0.0, 0.0), radar_pos=(500.0, 0.0),
              detection=150, engagement=75):
    aircraft = Aircraft(
        id="ac1", name="VIPER", start_position=aircraft_pos,
        speed=100.0, heading=0.0, turn_rate=360.0,
        waypoints=[(10000.0, 0.0)],
        hold_radius=30.0, arrival_threshold=10.0,
    )
    radar = RadarEmitter(
        id="r1", name="RADAR", position=radar_pos,
        detection_radius=detection, engagement_radius=engagement,
    )
    return Simulation(aircraft=aircraft, threats=[radar])


def test_simulation_step_moves_aircraft():
    sim = _make_sim()
    start = sim.aircraft.position
    sim.step(dt=1.0)
    assert sim.aircraft.position != start


def test_simulation_step_updates_threat_state():
    # Aircraft starts at (0,0), radar at (100,0), detection=150
    sim = _make_sim(aircraft_pos=(0.0, 0.0), radar_pos=(100.0, 0.0), detection=150)
    sim.step(dt=0.016)
    assert sim.threats[0].state == ThreatState.TRACKING


def test_simulation_tick_count_increments():
    sim = _make_sim()
    assert sim.tick_count == 0
    sim.step(dt=0.016)
    assert sim.tick_count == 1
    sim.step(dt=0.016)
    assert sim.tick_count == 2


def test_simulation_update_runs_multiple_fixed_steps():
    sim = _make_sim()
    # wall_dt of 3 * FIXED_DT should produce 3 steps
    sim.update(wall_dt=Simulation.FIXED_DT * 3)
    assert sim.tick_count == 3


def test_simulation_update_caps_accumulator():
    sim = _make_sim()
    # Very large wall_dt — should not run thousands of steps (capped at MAX_STEPS_PER_FRAME)
    sim.update(wall_dt=10.0)
    assert sim.tick_count <= Simulation.MAX_STEPS_PER_FRAME


def test_headless_500_steps_no_error():
    sim = _make_sim()
    for _ in range(500):
        sim.step(Simulation.FIXED_DT)
    assert sim.tick_count == 500


def test_aircraft_moves_from_start_after_500_steps():
    sim = _make_sim(aircraft_pos=(0.0, 0.0))
    start = sim.aircraft.position
    for _ in range(500):
        sim.step(Simulation.FIXED_DT)
    assert sim.aircraft.position != start
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_simulation.py -v`

Expected: `ModuleNotFoundError` for `simulation`.

- [ ] **Step 3: Create `threatsim/simulation.py`**

```python
from threatsim.entities.aircraft import Aircraft
from threatsim.entities.radar import ThreatEntity


class Simulation:
    FIXED_DT: float = 1.0 / 60.0
    MAX_STEPS_PER_FRAME: int = 10  # prevent spiral-of-death on slow frames

    def __init__(self, aircraft: Aircraft, threats: list[ThreatEntity]) -> None:
        self.aircraft = aircraft
        self.threats = threats
        self._accumulator: float = 0.0
        self.tick_count: int = 0

    def step(self, dt: float) -> None:
        """Advance simulation by exactly one fixed step."""
        self.aircraft.update(dt)
        for threat in self.threats:
            threat.update_state(self.aircraft.position)
        self.tick_count += 1

    def update(self, wall_dt: float) -> None:
        """Consume wall-clock delta using fixed-timestep accumulator."""
        self._accumulator += wall_dt
        steps = 0
        while self._accumulator >= self.FIXED_DT and steps < self.MAX_STEPS_PER_FRAME:
            self.step(self.FIXED_DT)
            self._accumulator -= self.FIXED_DT
            steps += 1
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_simulation.py -v`

Expected: 7 passed.

---

## Task 11: Renderer

**Files:**
- Create: `threatsim/renderer.py`

No unit tests — pygame rendering cannot be headlessly tested. Smoke-tested by the CLI in Task 12.

- [ ] **Step 1: Create `threatsim/renderer.py`**

```python
import math
import pygame
from threatsim.entities.threat_state import ThreatState
from threatsim.entities.radar import RadarEmitter
from threatsim.entities.sam import SAMSite
from threatsim.entities.noflyzone import NoFlyZone
from threatsim.entities.aircraft import Aircraft

SIDEBAR_WIDTH = 200
BG_COLOR = (10, 22, 40)
GRID_COLOR = (15, 40, 70)
SIDEBAR_BG = (8, 13, 24)
SIDEBAR_BORDER = (30, 41, 59)
DIVIDER_COLOR = (30, 41, 59)
AIRCRAFT_COLOR = (96, 165, 250)
WAYPOINT_COLOR = (60, 100, 170)
WAYPOINT_ACTIVE_COLOR = (96, 165, 250)
RADAR_COLOR = (22, 163, 74)
SAM_COLOR = (220, 38, 38)
NFZ_COLOR = (217, 119, 6)
NFZ_FILL = (217, 119, 6, 30)

STATE_COLORS = {
    ThreatState.SEARCHING: (74, 222, 128),
    ThreatState.TRACKING: (251, 191, 36),
    ThreatState.ENGAGING: (248, 113, 113),
}


def _threat_base_color(threat) -> tuple[int, int, int]:
    if isinstance(threat, NoFlyZone):
        return NFZ_COLOR
    if isinstance(threat, SAMSite):
        return SAM_COLOR
    return RADAR_COLOR


def _draw_dashed_circle(
    surface: pygame.Surface,
    color: tuple[int, int, int],
    center: tuple[int, int],
    radius: int,
    dash_length: int = 12,
    width: int = 1,
) -> None:
    if radius <= 0:
        return
    circumference = 2 * math.pi * radius
    num_dashes = max(1, int(circumference / (dash_length * 2)))
    rect = pygame.Rect(center[0] - radius, center[1] - radius, radius * 2, radius * 2)
    for i in range(num_dashes):
        start_angle = 2 * math.pi * i / num_dashes
        end_angle = start_angle + math.pi / num_dashes
        try:
            pygame.draw.arc(surface, color, rect, start_angle, end_angle, width)
        except Exception:
            pass


class Renderer:
    def __init__(self, window_width: int, window_height: int) -> None:
        pygame.init()
        self.window_width = window_width
        self.window_height = window_height
        self.map_width = window_width - SIDEBAR_WIDTH
        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("ThreatSim")
        self.clock = pygame.time.Clock()
        self._font_sm = pygame.font.SysFont("monospace", 11)
        self._font_md = pygame.font.SysFont("monospace", 13)
        self._tick = 0

    def draw(self, aircraft: Aircraft, threats: list) -> None:
        self.screen.fill(BG_COLOR)
        self._draw_grid()
        self._draw_threats(threats, aircraft)
        self._draw_aircraft(aircraft)
        self._draw_hud(aircraft, threats)
        pygame.display.flip()
        self._tick += 1

    # ------------------------------------------------------------------
    # Grid
    # ------------------------------------------------------------------

    def _draw_grid(self) -> None:
        for x in range(0, self.map_width, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, self.window_height))
        for y in range(0, self.window_height, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (self.map_width, y))

    # ------------------------------------------------------------------
    # Threats
    # ------------------------------------------------------------------

    def _draw_threats(self, threats: list, aircraft: Aircraft) -> None:
        for threat in threats:
            color = _threat_base_color(threat)
            state_color = STATE_COLORS[threat.state]
            if isinstance(threat, NoFlyZone):
                self._draw_nfz(threat, color, state_color)
            else:
                self._draw_radial_threat(threat, color, state_color)

    def _draw_radial_threat(self, threat, color, state_color) -> None:
        cx, cy = int(threat.position[0]), int(threat.position[1])
        _draw_dashed_circle(self.screen, color, (cx, cy), int(threat.detection_radius))
        pygame.draw.circle(self.screen, color, (cx, cy), int(threat.engagement_radius), 2)
        # State indicator dot
        if threat.state == ThreatState.ENGAGING and self._tick % 20 < 10:
            pygame.draw.circle(self.screen, state_color, (cx, cy), 7)
        else:
            pygame.draw.circle(self.screen, state_color, (cx, cy), 5)
        # Label
        label = self._font_sm.render(threat.name, True, color)
        self.screen.blit(label, (cx + 8, cy - 8))

    def _draw_nfz(self, threat: NoFlyZone, color, state_color) -> None:
        pts = [(int(x), int(y)) for x, y in threat.polygon]
        # Translucent fill via a temporary surface
        fill_surf = pygame.Surface((self.map_width, self.window_height), pygame.SRCALPHA)
        pygame.draw.polygon(fill_surf, (*color, 40), pts)
        self.screen.blit(fill_surf, (0, 0))
        # Outline — flash when engaging
        outline_color = state_color if threat.state == ThreatState.ENGAGING and self._tick % 20 < 10 else color
        pygame.draw.polygon(self.screen, outline_color, pts, 2)
        # Label at centroid
        cx, cy = int(threat.position[0]), int(threat.position[1])
        label = self._font_sm.render(threat.name, True, color)
        self.screen.blit(label, (cx - label.get_width() // 2, cy - 8))

    # ------------------------------------------------------------------
    # Aircraft
    # ------------------------------------------------------------------

    def _draw_aircraft(self, aircraft: Aircraft) -> None:
        # Track history
        hist = aircraft.track_history
        if len(hist) > 1:
            for i in range(1, len(hist)):
                alpha = int(180 * i / len(hist))
                p1 = (int(hist[i - 1][0]), int(hist[i - 1][1]))
                p2 = (int(hist[i][0]), int(hist[i][1]))
                pygame.draw.line(self.screen, (alpha // 2, alpha // 2, alpha), p1, p2, 1)

        # Waypoints
        for i, wp in enumerate(aircraft.waypoints):
            c = WAYPOINT_ACTIVE_COLOR if i >= aircraft.current_waypoint_index else WAYPOINT_COLOR
            pygame.draw.circle(self.screen, c, (int(wp[0]), int(wp[1])), 4, 1)

        # Aircraft position
        ax, ay = int(aircraft.position[0]), int(aircraft.position[1])
        pygame.draw.circle(self.screen, AIRCRAFT_COLOR, (ax, ay), 7)
        pygame.draw.circle(self.screen, BG_COLOR, (ax, ay), 4)
        # Heading tick
        rad = math.radians(aircraft.heading)
        tip = (ax + int(math.cos(rad) * 14), ay + int(math.sin(rad) * 14))
        pygame.draw.line(self.screen, AIRCRAFT_COLOR, (ax, ay), tip, 2)

    # ------------------------------------------------------------------
    # HUD sidebar
    # ------------------------------------------------------------------

    def _draw_hud(self, aircraft: Aircraft, threats: list) -> None:
        x0 = self.map_width
        pygame.draw.rect(self.screen, SIDEBAR_BG,
                         pygame.Rect(x0, 0, SIDEBAR_WIDTH, self.window_height))
        pygame.draw.line(self.screen, SIDEBAR_BORDER,
                         (x0, 0), (x0, self.window_height))

        y = 10
        hdr = self._font_sm.render("THREAT STATUS", True, (100, 116, 139))
        self.screen.blit(hdr, (x0 + 10, y))
        y += 18
        pygame.draw.line(self.screen, DIVIDER_COLOR,
                         (x0 + 5, y), (self.window_width - 5, y))
        y += 8

        for threat in threats:
            state_color = STATE_COLORS[threat.state]
            # Flash name on ENGAGING
            if threat.state == ThreatState.ENGAGING and self._tick % 20 >= 10:
                name_color = (80, 30, 30)
            else:
                name_color = state_color

            name_surf = self._font_md.render(threat.name, True, name_color)
            self.screen.blit(name_surf, (x0 + 10, y))
            y += 17

            state_text = f"  {threat.state.name}"
            state_surf = self._font_sm.render(state_text, True, state_color)
            self.screen.blit(state_surf, (x0 + 10, y))
            y += 14

            dist = math.hypot(
                threat.position[0] - aircraft.position[0],
                threat.position[1] - aircraft.position[1],
            )
            dist_surf = self._font_sm.render(f"  DST {dist:6.0f}", True, (71, 85, 105))
            self.screen.blit(dist_surf, (x0 + 10, y))
            y += 20

        # Aircraft stats at bottom
        stats_y = self.window_height - 72
        pygame.draw.line(self.screen, DIVIDER_COLOR,
                         (x0 + 5, stats_y - 6), (self.window_width - 5, stats_y - 6))
        for line in [
            f"HDG  {aircraft.heading:6.1f}°",
            f"SPD  {aircraft.speed:6.0f}",
            f"WPT  {aircraft.current_waypoint_index + 1}/{len(aircraft.waypoints)}",
        ]:
            surf = self._font_sm.render(line, True, (100, 116, 139))
            self.screen.blit(surf, (x0 + 10, stats_y))
            stats_y += 16
```

- [ ] **Step 2: Verify import is clean**

Run: `python -c "from threatsim.renderer import Renderer; print('ok')"`

Expected: `ok` (pygame initialises and exits cleanly).

---

## Task 12: CLI and `__main__`

**Files:**
- Create: `threatsim/cli.py`
- Create: `threatsim/__main__.py`

- [ ] **Step 1: Create `threatsim/cli.py`**

```python
import argparse
import sys
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="ThreatSim — Threat Environment Simulator")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON file")
    parser.add_argument("--headless", action="store_true",
                        help="Run without display (useful for testing/CI)")
    parser.add_argument("--steps", type=int, default=1000,
                        help="Steps to run in headless mode (default: 1000)")
    args = parser.parse_args()

    from threatsim.config import load_scenario, ConfigError
    try:
        scenario = load_scenario(args.scenario)
    except ConfigError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Scenario file not found: {args.scenario}", file=sys.stderr)
        sys.exit(1)

    from threatsim.simulation import Simulation
    sim = Simulation(aircraft=scenario["aircraft"], threats=scenario["threats"])

    if args.headless:
        for _ in range(args.steps):
            sim.step(Simulation.FIXED_DT)
        return

    # Pygame display mode
    import pygame
    from threatsim.renderer import Renderer
    w = scenario["window"]
    renderer = Renderer(w["width"], w["height"])

    prev = time.monotonic()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        now = time.monotonic()
        wall_dt = min(now - prev, 0.1)
        prev = now

        sim.update(wall_dt)
        renderer.draw(sim.aircraft, sim.threats)
        renderer.clock.tick(60)

    pygame.quit()
```

- [ ] **Step 2: Create `threatsim/__main__.py`**

```python
from threatsim.cli import main

main()
```

- [ ] **Step 3: Smoke-test headless run**

Run: `python -m threatsim --scenario scenarios/default.json --headless --steps 300`

Expected: exits with no output and return code 0.

- [ ] **Step 4: Test CLI error handling**

Run: `python -m threatsim --scenario nonexistent.json --headless`

Expected: prints `Scenario file not found: nonexistent.json` to stderr, exits with code 1.

---

## Task 13: Full Test Suite Pass

**Files:** None new — run all tests together.

- [ ] **Step 1: Run complete suite**

Run: `pytest tests/ -v`

Expected: all tests pass. Typical output:
```
tests/test_aircraft.py::test_aircraft_initial_position PASSED
tests/test_aircraft.py::test_aircraft_moves_in_heading_direction PASSED
... (all tests)
PASSED
```

- [ ] **Step 2: Run with coverage (optional sanity check)**

Run: `pytest tests/ --tb=short -q`

Expected: no failures, no errors.

---

## Task 14: README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write README**

```markdown
# ThreatSim

A 2D real-time battlefield situational awareness simulator. A friendly aircraft
navigates a waypoint route through a threat environment of radar emitters, SAM
sites, and no-fly zones. Each threat cycles through three detection states as
the aircraft moves. Built for studying synthetic threat environment concepts
used in defense training systems.

## Install

```bash
pip install -e ".[dev]"
```

Requires Python 3.10+ and pygame 2.5+.

## Run

```bash
python -m threatsim --scenario scenarios/default.json
```

Press **ESC** or close the window to quit.

**Headless mode** (no display, useful for CI):

```bash
python -m threatsim --scenario scenarios/default.json --headless --steps 500
```

## Screenshot

*(Add screenshot here after first run)*

## Threat State Machine

Each threat entity independently cycles through three states based on aircraft proximity:

```
SEARCHING  →  TRACKING  →  ENGAGING
   ↑              ↑
   └──────────────┘  (reverts as aircraft moves away)
```

| State | Condition | HUD colour |
|---|---|---|
| SEARCHING | Aircraft outside detection radius | Green |
| TRACKING | Inside detection radius, outside engagement radius | Yellow |
| ENGAGING | Inside engagement radius (or no-fly zone polygon) | Red (flashing) |

For **no-fly zones**, TRACKING is triggered when the aircraft is within
`approach_radius` of any polygon edge; ENGAGING when the aircraft enters the polygon.

## Scenario Format

Scenarios are JSON files. See `scenarios/default.json` for a complete example.

Key fields:

```json
{
  "window": { "width": 1200, "height": 800 },
  "aircraft": {
    "start_position": [x, y],
    "speed": 80,
    "turn_rate": 45,
    "waypoints": [[x1,y1], [x2,y2]]
  },
  "threats": [
    { "type": "radar", "position": [x,y], "detection_radius": 150, "engagement_radius": 75, ... },
    { "type": "sam",   "position": [x,y], "detection_radius": 200, "engagement_radius": 100, ... },
    { "type": "noflyzone", "polygon": [[x,y],...], "approach_radius": 40, ... }
  ]
}
```

## Running Tests

```bash
pytest tests/ -v
```
```

---

## Self-Review Checklist

- [x] **Spec coverage**: package scaffold ✓, BaseEntity ✓, Aircraft (movement + waypoints + hold) ✓, ThreatState ✓, RadarEmitter ✓, SAMSite ✓, NoFlyZone ✓, Config loader ✓, Simulation loop ✓, Renderer (right sidebar HUD) ✓, CLI --scenario/--headless/--steps ✓, pytest suite ✓, README ✓, default.json ✓
- [x] **Placeholder scan**: no TBDs, all code blocks are complete
- [x] **Type consistency**: `update_state(aircraft_pos: tuple[float, float])` used throughout Tasks 4–10; `ThreatEntity` defined in `radar.py` and imported in `noflyzone.py`, `simulation.py` consistently; `Aircraft` fields match between Task 7 and Task 9 tests
