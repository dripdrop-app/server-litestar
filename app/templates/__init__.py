from pathlib import Path

from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig


def engine_callback(template_engine: JinjaTemplateEngine):
    template_engine.engine.is_async = True


template_config = TemplateConfig(
    directory=Path("app/templates"),
    engine=JinjaTemplateEngine,
    engine_callback=engine_callback,
)
