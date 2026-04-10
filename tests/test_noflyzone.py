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
