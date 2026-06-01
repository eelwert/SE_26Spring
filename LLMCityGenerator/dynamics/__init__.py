from .road_analyzer import RoadAnalyzer
from .car_system import CarManager
from .pedestrian_system import PedestrianManager
from .traffic_light import TrafficLightManager
from .simulation_manager import SimulationManager
from .function_api import (
    dispatch_blender_job,
    FUNCTION_REGISTRY,
    run_traffic_simulation,
    run_crowd_simulation,
    run_full_simulation,
    stop_simulation,
    set_traffic_light_timing,
    set_car_model,
    set_pedestrian_model,
    list_available_models,
    get_simulation_status,
)


def get_simulation_manager():
    """Returns the singleton SimulationManager, creating it if needed."""
    return SimulationManager.get_instance()
