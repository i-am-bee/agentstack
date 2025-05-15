#!/bin/bash

python -c "
from cryptography.fernet import Fernet;
print(Fernet.generate_key().decode())
"
