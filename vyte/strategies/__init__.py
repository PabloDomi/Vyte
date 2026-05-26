"""
Declarative framework specs.

A single module-level `FRAMEWORK_REGISTRY` maps each (framework, ORM) pair to
its `FrameworkSpec` (directories, files, post-generate hook). Adding a new
combination means adding one entry, not subclassing.
"""

from .registry import (
    COMMON_FILES,
    DOCKER_FILES,
    FRAMEWORK_REGISTRY,
    FileSpec,
    FrameworkSpec,
    all_template_paths,
    get_spec,
)

__all__ = [
    "FRAMEWORK_REGISTRY",
    "FileSpec",
    "FrameworkSpec",
    "COMMON_FILES",
    "DOCKER_FILES",
    "all_template_paths",
    "get_spec",
]
