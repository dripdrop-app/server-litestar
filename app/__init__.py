from glob import glob

from litestar import Litestar, Router
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.plugins.htmx import HTMXPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.stores.redis import RedisStore
from litestar.template.config import TemplateConfig

from app.controllers import AuthenticationController
from app.db import sqlalchemy_config
from app.session import session_auth
from app.settings import ENV, settings

api_router = Router(path="/api", route_handlers=[AuthenticationController])

app = Litestar(
    on_app_init=[session_auth.on_app_init],
    plugins=[HTMXPlugin(), SQLAlchemyPlugin(config=sqlalchemy_config)],
    route_handlers=[api_router],
    stores={"sessions": RedisStore.with_client(url=settings.redis_url)},
    template_config=TemplateConfig(
        directory=glob("app/**/templates", recursive=True),
        engine=JinjaTemplateEngine,
    ),
    debug=settings.env != ENV.PRODUCTION,
)
