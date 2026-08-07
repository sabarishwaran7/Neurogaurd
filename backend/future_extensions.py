"""Reserved extension points for upcoming product modules.

This file intentionally contains no runtime behavior so production imports stay lightweight.
Product teams can grow capabilities here without rewriting the core platform.

Planned domains (roadmap):
- Multi-agent orchestration and supervisor graphs
- Voice agents (streaming STT/TTS, telephony bridges)
- Vision agents (image/video tools, multimodal message formats)
- Browser agents (headless automation, policy sandboxes)
- Agent marketplace (templates, versioning, publishing)
- Team collaboration (workspaces, RBAC, audit trails)
"""

EXTENSION_ROADMAP = [
    "multi_agent_systems",
    "voice_agents",
    "vision_agents",
    "browser_agents",
    "agent_marketplace",
    "team_collaboration",
]
