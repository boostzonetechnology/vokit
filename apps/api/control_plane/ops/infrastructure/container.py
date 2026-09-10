from __future__ import annotations

import os

from control_plane.ops.application.gate import ProductionReadiness, repo_root
from control_plane.ops.application.smoke import PostDeploySmoke


def production_readiness() -> ProductionReadiness:
    return ProductionReadiness(repo_root(), dict(os.environ))


def post_deploy_smoke() -> PostDeploySmoke:
    return PostDeploySmoke()
