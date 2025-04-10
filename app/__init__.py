from glob import glob

from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.plugins.htmx import HTMXPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.stores.redis import RedisStore
from litestar.stores.registry import StoreRegistry
from litestar.template.config import TemplateConfig

from app.db import sqlalchemy_config
from app.session import session_auth
from app.settings import settings

from app.controllers import AuthenticationController


app = Litestar(
    on_app_init=[session_auth.on_app_init],
    plugins=[HTMXPlugin(), SQLAlchemyPlugin(config=sqlalchemy_config)],
    route_handlers=[AuthenticationController],
    stores=StoreRegistry(
        default_factory=lambda name: RedisStore.with_client(url=settings.redis_url)
    ),
    template_config=TemplateConfig(
        directory=glob("app/**/templates", recursive=True),
        engine=JinjaTemplateEngine,
    ),
)
