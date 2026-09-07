from ksa_engine import Engine, TextToWorldGenerator
from ksa_engine.systems import AnimationSystem, AudioSystem, CameraController, LightingSystem, SceneComposer
from ksa_engine.systems import NarrativeSystem
from ksa_engine.llm import LLMNarrativeAI


def test_text_generates_complete_scene_deterministically():
    description = "مدينة صحراوية ليلية فيها واحة ومعركة"
    first = TextToWorldGenerator().generate(description, seed=42)
    second = TextToWorldGenerator().generate(description, seed=42)

    assert first.seed == second.seed == 42
    assert len(first.entities) == len(second.entities)
    assert first.metadata["audio"]["music"] == "battle_theme"
    assert first.find_by_kind("camera")[0].components["target_id"] is not None
    assert first.find_by_kind("light")


def test_engine_updates_camera_animation_and_audio():
    world = TextToWorldGenerator().generate("desert combat", seed=5)
    engine = Engine()
    engine.add_system(CameraController())
    engine.add_system(SceneComposer())
    engine.add_system(LightingSystem())
    engine.add_system(AudioSystem())
    engine.add_system(AnimationSystem())
    engine.load_world(world)

    engine.run_for(0.5)

    assert world.elapsed_time == 0.5
    assert world.metadata["audio"]["last_update"] == world.elapsed_time
    assert world.find_by_kind("character")[0].components["animation"]["time"] > 0


def test_narrative_ai_adds_hostage_and_answers_player():
    world = TextToWorldGenerator().generate("رجل مخطوف داخل قلعة", seed=4)
    narrative_system = NarrativeSystem()

    narrative_system.start(world)
    response = narrative_system.say(world, "سأساعدك وأنقذك")

    assert world.metadata["narrative"]["intent"] == "rescue_hostage"
    assert world.find_by_kind("npc")[0].components["dialogue"][0] == "تكفى ساعدني!"
    assert "المفتاح" in response


def test_llm_response_can_drive_world_actions_without_network():
    payload = '{"reply":"وجدت لك حليفًا.","world_actions":[{"action":"spawn_entity","name":"Ally","kind":"npc","role":"ally","dialogue":"أنا معك."}]}'
    response = LLMNarrativeAI._decode(payload)
    assert response["reply"] == "وجدت لك حليفًا."
    assert response["world_actions"][0]["name"] == "Ally"
