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
