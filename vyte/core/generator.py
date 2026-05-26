"""
Project generator.

Walks the declarative spec for a given (framework, ORM) combination and
materializes the project on disk. There is exactly one rendering loop —
adding a new framework means adding a `FrameworkSpec`, not subclassing.
"""

import shutil
from pathlib import Path

from ..exceptions import FileSystemError, GenerationError
from ..strategies.registry import (
    COMMON_FILES,
    DOCKER_FILES,
    FileSpec,
    FrameworkSpec,
    all_template_paths,
    get_spec,
)
from .config import ProjectConfig
from .dependencies import DependencyManager
from .renderer import TemplateRenderer


class ProjectGenerator:
    """Generate a project from a `ProjectConfig` by following its spec."""

    def __init__(self, template_dir: Path | None = None):
        self.renderer = TemplateRenderer(template_dir)
        self.template_dir = template_dir

    def generate(self, config: ProjectConfig) -> Path:
        """Generate the project. Returns the project path on success.

        Raises:
            FileExistsError: target directory already exists.
            GenerationError: any other generation failure (the partial
                project directory is removed on failure).
        """
        project_path = config.get_output_path()
        if project_path.exists():
            raise FileExistsError(
                f"Directory already exists: {project_path}\n"
                "Please choose a different name or delete the existing directory."
            )

        spec = get_spec(config)
        context = config.model_dump_safe()

        project_path.mkdir(parents=True)
        try:
            self._create_dirs(project_path, spec, context, config)
            self._render_all(project_path, COMMON_FILES, config, context)
            if config.docker_support:
                self._render_all(project_path, DOCKER_FILES, config, context)
            self._render_all(project_path, spec.files, config, context)
            if config.testing_suite:
                self._render_all(project_path, spec.test_files, config, context)

            DependencyManager.write_requirements_txt(config, project_path)
            DependencyManager.write_requirements_dev_txt(project_path)

            if spec.post_generate is not None:
                spec.post_generate(project_path, config)

            return project_path

        except (OSError, PermissionError) as e:
            self._cleanup(project_path)
            raise FileSystemError(f"Failed to create project structure: {e}") from e
        except (GenerationError, FileSystemError):
            self._cleanup(project_path)
            raise
        except Exception as e:
            self._cleanup(project_path)
            raise GenerationError(f"Project generation failed: {e}") from e

    @staticmethod
    def _cleanup(project_path: Path) -> None:
        if project_path.exists():
            shutil.rmtree(project_path, ignore_errors=True)

    @staticmethod
    def _create_dirs(
        project_path: Path,
        spec: FrameworkSpec,
        context: dict,
        config: ProjectConfig,
    ) -> None:
        """Create the directories declared by the spec, plus tests/ if enabled."""
        for d in spec.dirs:
            (project_path / d.format(**context)).mkdir(parents=True, exist_ok=True)

        for d in spec.init_dirs:
            (project_path / d.format(**context) / "__init__.py").touch()

        if config.testing_suite:
            tests_dir = project_path / "tests"
            tests_dir.mkdir(exist_ok=True)
            (tests_dir / "__init__.py").touch()

    def _render_all(
        self,
        project_path: Path,
        files: tuple[FileSpec, ...],
        config: ProjectConfig,
        context: dict,
    ) -> None:
        for f in files:
            if not f.when(config):
                continue
            target = project_path / f.output.format(**context)
            self.renderer.render_to_file(f.template, target, context)
            if f.executable:
                target.chmod(0o755)

    def validate_before_generate(self, config: ProjectConfig) -> tuple[bool, list[str]]:
        """Check that every template the spec needs exists, and warn on dep conflicts."""
        errors: list[str] = []

        missing = [t for t in all_template_paths(config)
                   if not self.renderer.template_exists(t)]
        if missing:
            errors.append(
                f"Missing templates: {', '.join(missing)}\n"
                "Please ensure all required templates are present."
            )

        deps = DependencyManager.get_all_dependencies(config)
        warnings = DependencyManager.check_dependency_conflicts(deps)
        errors.extend(warnings)

        return len(errors) == 0, errors

    def get_generation_summary(self, config: ProjectConfig) -> dict:
        """Return a summary of what `generate()` will produce (for UX/dry-run)."""
        spec = get_spec(config)
        deps_info = DependencyManager.get_dependency_info(config)

        all_files = list(COMMON_FILES)
        if config.docker_support:
            all_files.extend(DOCKER_FILES)
        all_files.extend(spec.files)
        if config.testing_suite:
            all_files.extend(spec.test_files)

        applicable = [f for f in all_files if f.when(config)]

        return {
            "project_name": config.name,
            "framework": config.framework,
            "orm": config.orm,
            "database": config.database,
            "features": {
                "authentication": config.auth_enabled,
                "docker": config.docker_support,
                "testing": config.testing_suite,
                "git": config.git_init,
            },
            "dependencies": deps_info,
            "templates_count": len(applicable),
            "output_path": str(config.get_output_path()),
        }


def quick_generate(
    name: str,
    framework: str,
    orm: str,
    database: str,
    auth: bool = True,
    docker: bool = True,
    testing: bool = True,
    git: bool = True,
) -> Path:
    """Convenience function: build a `ProjectConfig` and generate in one call."""
    config = ProjectConfig(
        name=name,
        framework=framework,
        orm=orm,
        database=database,
        auth_enabled=auth,
        docker_support=docker,
        testing_suite=testing,
        git_init=git,
    )
    return ProjectGenerator().generate(config)
