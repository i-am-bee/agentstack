# Copyright 2025 © BeeAI a Series of LF Projects, LLC
# SPDX-License-Identifier: Apache-2.0

import binascii
import hashlib
import os
import platform


def generate_stable_id(length=16) -> str:
    try:
        # Use os.uname() for Unix-like systems
        uname_info = os.uname()
        # Only use stable attributes: sysname, nodename, machine to make it more stable
        base_info = "".join([uname_info.sysname, uname_info.nodename, uname_info.machine])
    except AttributeError:
        # Fallback for Windows
        system_info = [
            platform.system(),  # OS name
            platform.node(),  # Hostname
            platform.machine(),  # Machine type
        ]
        base_info = "".join(system_info)

    derived_key = hashlib.pbkdf2_hmac("sha256", base_info.encode("utf-8"), b"x", 1000, dklen=length)

    return binascii.hexlify(derived_key).decode("utf-8")[: length * 2]  # 2 hex chars per byte
