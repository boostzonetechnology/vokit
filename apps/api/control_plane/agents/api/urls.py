from __future__ import annotations

from django.urls import path

from control_plane.agents.api.views import (
    AgencyAgentCloneView,
    AgencyAgentCollectionView,
    AgencyAgentDetailView,
    AgencyAgentPauseView,
    AgencyAgentPublishView,
    AgencyAgentResolvedView,
    AgencyAgentRoutingView,
    AgencyAgentTestSessionView,
    AgencyInstructionView,
    AgencyKnowledgeAttachView,
    AgencyKnowledgeView,
    AgencyTemplateCollectionView,
    CustomerAgentDetailView,
    CustomerKnowledgeView,
    PlatformAgentCollectionView,
    PlatformAgentPublishView,
    PlatformInstructionView,
    PlatformKnowledgeView,
    PlatformTemplateCollectionView,
)

urlpatterns = [
    path("platform/agents", PlatformAgentCollectionView.as_view(), name="platform-agents"),
    path(
        "platform/agents/<str:agent_id>/publish",
        PlatformAgentPublishView.as_view(),
        name="platform-agent-publish",
    ),
    path("platform/templates", PlatformTemplateCollectionView.as_view(), name="platform-templates"),
    path(
        "platform/instructions",
        PlatformInstructionView.as_view(),
        name="platform-instructions",
    ),
    path("platform/knowledge", PlatformKnowledgeView.as_view(), name="platform-knowledge"),
    path("agency/agents", AgencyAgentCollectionView.as_view(), name="agency-agents"),
    path(
        "agency/agents/<str:agent_id>",
        AgencyAgentDetailView.as_view(),
        name="agency-agent",
    ),
    path(
        "agency/agents/<str:agent_id>/publish",
        AgencyAgentPublishView.as_view(),
        name="agency-agent-publish",
    ),
    path(
        "agency/agents/<str:agent_id>/pause",
        AgencyAgentPauseView.as_view(),
        name="agency-agent-pause",
    ),
    path(
        "agency/agents/<str:agent_id>/clone",
        AgencyAgentCloneView.as_view(),
        name="agency-agent-clone",
    ),
    path(
        "agency/agents/<str:agent_id>/resolved-instructions",
        AgencyAgentResolvedView.as_view(),
        name="agency-agent-resolved",
    ),
    path(
        "agency/agents/<str:agent_id>/routing",
        AgencyAgentRoutingView.as_view(),
        name="agency-agent-routing",
    ),
    path(
        "agency/agents/<str:agent_id>/test-sessions",
        AgencyAgentTestSessionView.as_view(),
        name="agency-agent-test-sessions",
    ),
    path(
        "agency/agents/<str:agent_id>/knowledge",
        AgencyKnowledgeAttachView.as_view(),
        name="agency-agent-knowledge-attach",
    ),
    path("agency/templates", AgencyTemplateCollectionView.as_view(), name="agency-templates"),
    path("agency/instructions", AgencyInstructionView.as_view(), name="agency-instructions"),
    path("agency/knowledge", AgencyKnowledgeView.as_view(), name="agency-knowledge"),
    path(
        "customer/agents/<str:agent_id>",
        CustomerAgentDetailView.as_view(),
        name="customer-agent",
    ),
    path("customer/knowledge", CustomerKnowledgeView.as_view(), name="customer-knowledge"),
]
