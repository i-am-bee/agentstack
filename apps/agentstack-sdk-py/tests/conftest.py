# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import async_lru

# Disable async_lru event loop check in tests
async_lru._LRUCacheWrapper._check_loop = lambda self, loop: None
