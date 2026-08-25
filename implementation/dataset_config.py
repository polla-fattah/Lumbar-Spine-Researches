# AMOG-Net Dataset Configuration & Dynamic Path Resolver
# Author: Dr. Polla Fattah / Selar's PhD Research Team

import os
import sys

DEFAULT_HINTS_RSNA = [
    r'C:\Users\polla\Drives\Locals\Data\lumbar-spine-degenerative-classification',
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "rsna")),
    r'./rsna-lumbar-spine-degenerative-classification'
]

DEFAULT_HINTS_HOSPITAL = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Data", "cases")),
    r'C:\Users\polla\Drives\PollaFattah\UNi\Research\Students\Selar\Project\Data\cases',
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "hospital_cases"))
]

def resolve_dataset_dir(cli_arg, env_var_name, hint_list, dataset_name):
    if cli_arg and os.path.exists(cli_arg):
        print(f"[{dataset_name}] Using CLI specified directory: {cli_arg}")
        return os.path.abspath(cli_arg), True

    env_val = os.environ.get(env_var_name)
    if env_val and os.path.exists(env_val):
        print(f"[{dataset_name}] Using Environment Variable ({env_var_name}): {env_val}")
        return os.path.abspath(env_val), True

    for hint in hint_list:
        if os.path.exists(hint):
            print(f"[{dataset_name}] Auto-discovered dataset at hint location: {hint}")
            return os.path.abspath(hint), True

    print(f"\n💡 [NOTICE - {dataset_name} PATH NOT FOUND]")
    print(f"   Please provide the {dataset_name} location via CLI argument or Environment Variable:")
    print(f"     Option A (CLI) : python <script>.py --{dataset_name.lower()}_dir \"/path/to/{dataset_name.lower()}\"")
    print(f"     Option B (ENV) : set {env_var_name}=/path/to/{dataset_name.lower()}")
    return None, False
