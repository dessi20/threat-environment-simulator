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
    if isinstance(threat, RadarEmitter):
        return RADAR_COLOR
    raise TypeError(f"Unknown threat type: {type(threat).__name__}")


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

    def _draw_grid(self) -> None:
        for x in range(0, self.map_width, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, self.window_height))
        for y in range(0, self.window_height, 50):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (self.map_width, y))

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
        if threat.state == ThreatState.ENGAGING and self._tick % 20 < 10:
            pygame.draw.circle(self.screen, state_color, (cx, cy), 7)
        else:
            pygame.draw.circle(self.screen, state_color, (cx, cy), 5)
        label = self._font_sm.render(threat.name, True, color)
        self.screen.blit(label, (cx + 8, cy - 8))

    def _draw_nfz(self, threat: NoFlyZone, color, state_color) -> None:
        pts = [(int(x), int(y)) for x, y in threat.polygon]
        fill_surf = pygame.Surface((self.map_width, self.window_height), pygame.SRCALPHA)
        pygame.draw.polygon(fill_surf, (*color, 40), pts)
        self.screen.blit(fill_surf, (0, 0))
        outline_color = state_color if threat.state == ThreatState.ENGAGING and self._tick % 20 < 10 else color
        pygame.draw.polygon(self.screen, outline_color, pts, 2)
        cx, cy = int(threat.position[0]), int(threat.position[1])
        label = self._font_sm.render(threat.name, True, color)
        self.screen.blit(label, (cx - label.get_width() // 2, cy - 8))

    def _draw_aircraft(self, aircraft: Aircraft) -> None:
        hist = list(aircraft.track_history)
        if len(hist) > 1:
            for i in range(1, len(hist)):
                alpha = int(180 * i / len(hist))
                p1 = (int(hist[i - 1][0]), int(hist[i - 1][1]))
                p2 = (int(hist[i][0]), int(hist[i][1]))
                pygame.draw.line(self.screen, (alpha // 2, alpha // 2, alpha), p1, p2, 1)
        for i, wp in enumerate(aircraft.waypoints):
            c = WAYPOINT_ACTIVE_COLOR if i >= aircraft.current_waypoint_index else WAYPOINT_COLOR
            pygame.draw.circle(self.screen, c, (int(wp[0]), int(wp[1])), 4, 1)
        ax, ay = int(aircraft.position[0]), int(aircraft.position[1])
        pygame.draw.circle(self.screen, AIRCRAFT_COLOR, (ax, ay), 7)
        pygame.draw.circle(self.screen, BG_COLOR, (ax, ay), 4)
        rad = math.radians(aircraft.heading)
        tip = (ax + int(math.cos(rad) * 14), ay + int(math.sin(rad) * 14))
        pygame.draw.line(self.screen, AIRCRAFT_COLOR, (ax, ay), tip, 2)

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
            if threat.state == ThreatState.ENGAGING and self._tick % 20 >= 10:
                name_color = (80, 30, 30)
            else:
                name_color = state_color
            name_surf = self._font_md.render(threat.name, True, name_color)
            self.screen.blit(name_surf, (x0 + 10, y))
            y += 17
            state_surf = self._font_sm.render(f"  {threat.state.name}", True, state_color)
            self.screen.blit(state_surf, (x0 + 10, y))
            y += 14
            dist = math.hypot(
                threat.position[0] - aircraft.position[0],
                threat.position[1] - aircraft.position[1],
            )
            dist_surf = self._font_sm.render(f"  DST {dist:6.0f}", True, (71, 85, 105))
            self.screen.blit(dist_surf, (x0 + 10, y))
            y += 20
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
