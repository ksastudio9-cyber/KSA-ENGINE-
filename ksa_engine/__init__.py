"""KSA Engine Beta: a modular runtime for developer-authored scenes."""

from .core import Engine, EngineConfig, EngineStats, Entity, GameWorld, Scene, SceneManager, Transform, Vector3
from .events import Event, EventBus, InputState
from .physics import PhysicsBody, PhysicsSystem
from .resources import ResourceManager
from .scene_io import load_scene, save_scene
from .systems import Camera, CameraSystem, InputMovementSystem, LightingSystem

__all__ = [
    "Camera", "CameraSystem", "Engine", "EngineConfig", "EngineStats", "Entity", "Event", "EventBus",
    "GameWorld", "InputMovementSystem", "InputState", "LightingSystem", "PhysicsBody", "SceneManager",
    "PhysicsSystem", "ResourceManager", "Scene", "Transform", "Vector3", "load_scene", "save_scene",
]
