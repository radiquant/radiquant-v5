import re
import sys

def modify_validate_contracts():
    file_path = "/opt/radiquant-v5/scripts/validate_contracts.py"
    with open(file_path, "r") as f:
        content = f.read()
    
    # 1. remove "projection_builder_enabled" from list around line 2067
    content = re.sub(
        r'for flag in \["api_result_writes_enabled", "worker_jobs_enabled", "engine_execution_enabled", "projection_builder_enabled"\]:',
        'for flag in ["api_result_writes_enabled", "worker_jobs_enabled", "engine_execution_enabled"]:',
        content
    )
    
    # 2. worker_projection_materialization_enabled, materialized_projection_storage_enabled, worker_projection_builder_enabled (lines 551 and 560)
    # We remove these checks entirely or adapt them. 
    # ADR-0002 has unfrozen them.
    content = re.sub(
        r'for flag in \["worker_projection_materialization_enabled", "materialized_projection_storage_enabled", "worker_projection_builder_enabled"\]:\n\s+require\(runtime_scope\.get\(flag\) is False, f"Radi144 runtime_scope \{flag\} must remain false"\)',
        '# ADR-0002: worker_projection_materialization_enabled, materialized_projection_storage_enabled, worker_projection_builder_enabled are now unfrozen and can be True',
        content
    )
    content = re.sub(
        r'for flag in \["worker_projection_materialization_enabled", "materialized_projection_storage_enabled", "worker_projection_builder_enabled"\]:\n\s+require\(decision\.get\(flag\) is False and boundary\.get\(flag\) is False, f"Radi144 worker projection materialization \{flag\} must remain false"\)',
        '# ADR-0002: worker_projection_materialization_enabled etc. are now unfrozen',
        content
    )

    # 3. result_persistence_enabled is False check
    content = re.sub(
        r'require\(runtime_scope\.get\("result_persistence_enabled"\) is False, "Radi144 runtime result writes must remain disabled"\)',
        '# ADR-0002: result_persistence_enabled is now enabled',
        content
    )
    
    # 4. result_writer_enabled_in_worker, projection_builder_enabled_in_worker around line 446
    content = re.sub(
        r'for flag in \["engine_execution_enabled", "result_writer_enabled_in_worker", "projection_builder_enabled_in_worker", "external_queue_enabled"\]:',
        'for flag in ["engine_execution_enabled", "external_queue_enabled"]:',
        content
    )
    
    with open(file_path, "w") as f:
        f.write(content)
    print("validate_contracts.py updated.")

modify_validate_contracts()
