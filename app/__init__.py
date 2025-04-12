from pathlib import Path

from litestar import Litestar, Router
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.di import Provide
from litestar.plugins.htmx import HTMXPlugin
from litestar.plugins.sqlalchemy import SQLAlchemyPlugin
from litestar.stores.redis import RedisStore
from litestar.template.config import TemplateConfig
from litestar_saq import SAQPlugin

from app.controllers import AuthenticationController
from app.db import sqlalchemy_config
from app.dependencies import provide_redis
from app.queue import saq_config
from app.session import session_auth
from app.settings import ENV, settings

api_router = Router(path="/api", route_handlers=[AuthenticationController])

template_config = TemplateConfig(
    directory=Path("app/templates"), engine=JinjaTemplateEngine
)

app = Litestar(
    debug=settings.env != ENV.PRODUCTION,
    dependencies={"redis": Provide(provide_redis, sync_to_thread=False)},
    on_app_init=[session_auth.on_app_init],
    plugins=[
        HTMXPlugin(),
        SQLAlchemyPlugin(config=sqlalchemy_config),
        SAQPlugin(config=saq_config),
    ],
    route_handlers=[api_router],
    stores={"sessions": RedisStore.with_client(url=settings.redis_url)},
    template_config=template_config,
)
