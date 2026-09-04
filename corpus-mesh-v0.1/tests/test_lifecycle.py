from corpus_mesh.blueprint import default_blueprint
from corpus_mesh.lifecycle import BlueprintController
from corpus_mesh.models import AgentProfile, AgentState, CorpusLink


def test_spawn_and_retire_updates_blueprint():
    ctl = BlueprintController(default_blueprint())
    ctl.spawn(
        AgentProfile("security_1", "security", ["security"], AgentState.PROBATION),
        [CorpusLink("architect", "security_1", "task_assignment")],
    )
    assert "security_1" in ctl.blueprint.agents
    assert ctl.blueprint.version.startswith("CM-0.1-G")

    ctl.retire("security_1", "failed probation")
    assert ctl.blueprint.agents["security_1"].state == AgentState.RETIRED
    assert not [l for l in ctl.blueprint.links if (l.source == "security_1" or l.destination == "security_1") and l.active]
