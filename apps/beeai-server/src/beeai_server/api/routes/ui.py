# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import fastapi

from beeai_server.api.dependencies import ConfigurationDependency
from beeai_server.configuration import UIFeatureFlags

router = fastapi.APIRouter()


@router.get("/config")
def get_ui_config(config: ConfigurationDependency) -> UIFeatureFlags:
    return config.feature_flags.ui
