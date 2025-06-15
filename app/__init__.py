from litestar import Litestar, Router
from litestar.di import Provide
from litestar.plugins import htmx, pydantic, sqlalchemy
from litestar.stores.redis import RedisStore

from app.db import sqlalchemy_config
from app.dependencies import provide_redis
from app.routes import authentication, music
from app.session import session_auth
from app.settings import ENV, settings
from app.templates import template_config

api_router = Router(path="/api", route_handlers=[authentication.router, music.router])


app = Litestar(
    debug=settings.env != ENV.PRODUCTION,
    dependencies={"redis": Provide(provide_redis)},
    on_app_init=[session_auth.on_app_init],
    plugins=[
        htmx.HTMXPlugin(),
        pydantic.PydanticPlugin(prefer_alias=True),
        sqlalchemy.SQLAlchemyPlugin(config=sqlalchemy_config),
    ],
    route_handlers=[api_router],
    stores={"sessions": RedisStore.with_client(url=settings.redis_url)},
    template_config=template_config,
)
