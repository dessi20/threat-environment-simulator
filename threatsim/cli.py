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

    # Pygame display mode — only imported here, not at module top
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
