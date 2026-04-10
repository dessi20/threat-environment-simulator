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


def test_simulation_accumulator_carries_remainder():
    sim = _make_sim()
    # After a large wall_dt that hits the cap, accumulator should still hold unspent time
    sim.update(wall_dt=10.0)
    assert sim._accumulator > 0.0
