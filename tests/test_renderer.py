# tests/test_renderer.py
"""
Test template rendering
"""

from vyte.core.renderer import TemplateRegistry


def test_renderer_initialization(renderer):
    """Test renderer initialization"""
    assert renderer.env is not None
    assert renderer.template_dir.exists()


def test_template_filters(renderer):
    """Test custom filters"""
    # Test filters through the Jinja environment instead of direct method access
    env = renderer.env

    cases = [
        ("pascal_case", "my_project", "MyProject"),
        ("snake_case", "MyProject", "my_project"),
        ("kebab_case", "my_project", "my-project"),
        ("title_case", "my_project", "My Project"),
    ]

    for fname, inp, expected in cases:
        assert fname in env.filters
        assert env.filters[fname](inp) == expected


def test_render_simple_template(renderer, temp_dir):
    """Test rendering a simple template"""
    # Create a simple template
    template_content = "Hello {{ name }}!"
    template_path = temp_dir / "test.j2"
    template_path.write_text(template_content)

    # Render (would need actual template in templates/)
    # This is just to test the method exists
    assert hasattr(renderer, "render")
    assert hasattr(renderer, "render_to_file")


def test_template_registry():
    """Test template registry"""
    templates = TemplateRegistry.get_templates_for_config(
        framework="Flask-Restx", orm="SQLAlchemy", auth_enabled=True, testing_suite=True
    )

    assert len(templates) > 0
    assert "init" in templates or "init_auth" in templates
    assert "models" in templates
