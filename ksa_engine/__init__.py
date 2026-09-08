"""KSA Engine Beta: a modular runtime for developer-authored scenes."""

from .core import Engine, EngineConfig, Entity, GameWorld, Scene, Transform, Vector3
from .events import Event, EventBus, InputState
from .physics import PhysicsBody, PhysicsSystem
from .resources import ResourceManager
from .scene_io import load_scene, save_scene
from .systems import Camera, CameraSystem, InputMovementSystem, LightingSystem

__all__ = [
    "Camera", "CameraSystem", "Engine", "EngineConfig", "Entity", "Event", "EventBus",
    "GameWorld", "InputMovementSystem", "InputState", "LightingSystem", "PhysicsBody",
    "PhysicsSystem", "ResourceManager", "Scene", "Transform", "Vector3", "load_scene", "save_scene",
]
