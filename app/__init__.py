from glob import glob

from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.plugins.htmx import HTMXPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.template.config import TemplateConfig

from app.db import sqlalchemy_config
from app.session import session_auth


app = Litestar(
    route_handlers=[],
    on_app_init=[session_auth.on_app_init],
    plugins=[HTMXPlugin(), SQLAlchemyPlugin(config=sqlalchemy_config)],
    template_config=TemplateConfig(
        directory=glob("app/**/templates", recursive=True),
        engine=JinjaTemplateEngine,
    ),
)
