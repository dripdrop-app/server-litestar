from pathlib import Path

from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig

template_config = TemplateConfig(
    directory=Path("app/templates"), engine=JinjaTemplateEngine
)
