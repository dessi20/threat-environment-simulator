# ThreatSim Design Spec
**Date:** 2026-04-10
**Status:** Approved

---

## Overview

ThreatSim is a 2D real-time battlefield situational awareness simulator. A friendly aircraft navigates a configurable route through a threat environment containing radar emitters, SAM sites, and no-fly zones. Each threat cycles through three states based on aircraft proximity. The tool is purely visual — no damage or game-over mechanics. It is designed for studying synthetic threat environment concepts used in defense training systems.

---

## Architecture

**Approach:** Class hierarchy with a central Simulation class (Option A).  
Entity types are fixed and known; hierarchy is shallow and clean; maps naturally to the JSON config; easily tested with pytest.

### Package structure

```
threatsim/
  __init__.py
  cli.py              # Entry point — --scenario, --headless
  simulation.py       # Fixed-timestep loop, owns all entities, calls update(dt)
  renderer.py         # Pygame drawing — radii, track history, HUD panel (no logic)
  config.py           # Loads/validates JSON, constructs entity objects
  entities/
    __init__.py
    base.py           # BaseEntity: id, position, abstract update(dt)
    aircraft.py       # Waypoint nav, turn rate, hold orbit, track history
    radar.py          # RadarEmitter: detection/engagement radii, ThreatState machine
    sam.py            # SAMSite: same as radar, different visual
    noflyzone.py      # NoFlyZone: polygon corners, point-in-polygon, ThreatState
    threat_state.py   # ThreatState enum (SEARCHING / TRACKING / ENGAGING)

scenarios/            # JSON scenario files
  default.json
tests/                # pytest suite
pyproject.toml
README.md
```

---

## Entities

### BaseEntity
- `id: str`
- `position: tuple[float, float]` (x, y in world units)
- `update(dt: float) -> None` — abstract, called each simulation tick

### Aircraft(BaseEntity)
- `speed: float` — world units per second
- `heading: float` — degrees, 0 = right, clockwise
- `turn_rate: float` — max degrees per second
- `waypoints: list[tuple[float, float]]`
- `current_waypoint_index: int`
- `hold_radius: float` — orbit radius at final waypoint (world units)
- `arrival_threshold: float` — distance at which a waypoint is considered reached (default 10)
- `track_history: list[tuple[float, float]]` — recorded positions for trail rendering

**Navigation logic:**
- Each tick: compute bearing to current target waypoint
- `heading += clamp(bearing_error, -turn_rate * dt, +turn_rate * dt)`
- Advance waypoint when `distance < arrival_threshold`
- On final waypoint: enter hold orbit — fly a circle of `hold_radius` centred on the waypoint; angular velocity `ω = speed / hold_radius` (radians/s)

### ThreatEntity(BaseEntity)
Shared base for RadarEmitter and SAMSite.
- `name: str`
- `state: ThreatState`
- `update_state(aircraft_distance: float) -> None` — transitions state based on distance thresholds

### RadarEmitter(ThreatEntity)
- `detection_radius: float`
- `engagement_radius: float`

### SAMSite(ThreatEntity)
- `detection_radius: float`
- `engagement_radius: float`
- Identical behaviour to RadarEmitter; differs only in renderer visual (icon/colour)

### NoFlyZone(ThreatEntity)
- `polygon: list[tuple[float, float]]` — ordered corner coordinates
- `approach_radius: float` — perimeter buffer that triggers TRACKING state
- Inherits `name` and `state` from ThreatEntity
- Uses point-in-polygon test for ENGAGING; minimum distance to any polygon edge for TRACKING

---

## Threat State Machine

States: `SEARCHING`, `TRACKING`, `ENGAGING`

**RadarEmitter / SAMSite:**
| Condition | State |
|---|---|
| `dist > detection_radius` | SEARCHING |
| `engagement_radius < dist ≤ detection_radius` | TRACKING |
| `dist ≤ engagement_radius` | ENGAGING |

Transitions are purely distance-based (no hysteresis). State is recomputed each tick.

**NoFlyZone:**
| Condition | State |
|---|---|
| Outside polygon AND outside `approach_radius` buffer | SEARCHING |
| Within `approach_radius` of polygon boundary | TRACKING |
| Inside polygon (point-in-polygon test) | ENGAGING |

**Visual indicators:**
- SEARCHING — green pulse
- TRACKING — yellow steady
- ENGAGING — red flash

---

## Renderer

Pygame window with a **right sidebar HUD** layout:
- **Battlefield canvas** (left, fills remaining width): dark background grid, threat detection radii (dashed), engagement radii (solid), no-fly zone polygon outlines, aircraft position (glowing dot), track history trail, waypoint markers
- **HUD sidebar** (right, fixed width ~180px): one row per threat showing name, state indicator, distance from aircraft; aircraft stats at bottom (heading, speed, waypoint index)

Renderer is a pure consumer of simulation state — it holds no logic, calls no `update()`. Headless mode skips renderer entirely.

**Colour coding:**
- Radar emitter: green
- SAM site: red
- No-fly zone: amber
- Aircraft / track: blue

---

## Simulation Loop

Fixed timestep of `1/60s` internally. Pygame display targets 60 FPS (30 FPS minimum acceptable). Accumulator pattern: wall-clock delta is accumulated; fixed steps are consumed until < one timestep remains.

```
accumulator += wall_delta
while accumulator >= FIXED_DT:
    simulation.step(FIXED_DT)
    accumulator -= FIXED_DT
renderer.draw(simulation.state)
```

In `--headless` mode: no accumulator, no frame cap — steps run as fast as possible for a configured number of ticks, then exit.

---

## Scenario JSON Format

```json
{
  "window": { "width": 1200, "height": 800 },
  "aircraft": {
    "id": "friendly-1",
    "name": "VIPER 01",
    "start_position": [100, 400],
    "speed": 120,
    "heading": 0,
    "turn_rate": 45,
    "hold_radius": 30,
    "arrival_threshold": 10,
    "waypoints": [[300, 200], [600, 350], [900, 200]]
  },
  "threats": [
    {
      "type": "radar",
      "id": "radar-1",
      "name": "EW RADAR",
      "position": [400, 300],
      "detection_radius": 150,
      "engagement_radius": 75
    },
    {
      "type": "sam",
      "id": "sam-1",
      "name": "SA-6",
      "position": [700, 250],
      "detection_radius": 200,
      "engagement_radius": 100
    },
    {
      "type": "noflyzone",
      "id": "nfz-1",
      "name": "NFZ ALPHA",
      "polygon": [[500, 100], [650, 100], [650, 220], [500, 220]],
      "approach_radius": 50
    }
  ]
}
```

`config.py` validates all required fields and raises `ConfigError` (a custom exception) on missing fields or unknown threat types.

---

## CLI

```
python -m threatsim --scenario scenarios/default.json
python -m threatsim --scenario scenarios/default.json --headless
```

- `--scenario` — path to JSON scenario file (required)
- `--headless` — run without pygame window; runs for `--steps N` ticks then exits (default 1000; useful for CI/pytest)

---

## Testing (pytest)

### Entity logic
- Aircraft reaches each waypoint within expected step count given speed and turn rate
- Heading clamp never exceeds `turn_rate * dt` per tick
- Aircraft enters hold orbit at final waypoint and stays within `hold_radius + arrival_threshold`
- Track history grows by one entry per tick

### Threat state transitions
- RadarEmitter: SEARCHING → TRACKING at `detection_radius`, TRACKING → ENGAGING at `engagement_radius`
- State reverts correctly as aircraft moves back out
- NoFlyZone: SEARCHING → TRACKING at `approach_radius`, ENGAGING on point-in-polygon
- NoFlyZone: ENGAGING → TRACKING when aircraft exits polygon

### Config loader
- Valid JSON produces correct entity types and counts
- Missing required field raises `ConfigError` with descriptive message
- Unknown `type` value raises `ConfigError`

### Headless integration
- Full sim runs 500 steps without raising an exception
- Aircraft position has changed from start after 500 steps
- Threat states match expected values after a deterministic scenario runs to completion

---

## README Sections

1. Project overview and purpose
2. Install (`pip install -e .` or `pip install -r requirements.txt`)
3. Run (`python -m threatsim --scenario ...`)
4. Screenshot / demo GIF
5. Threat state machine explanation (diagram or description)
6. Scenario JSON format reference
