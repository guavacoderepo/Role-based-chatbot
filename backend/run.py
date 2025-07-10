from fastapi import FastAPI
from contextlib import asynccontextmanager
from .app.routes.authRoute import auth_router
from .app.routes.chatRoute import chat_router
from .app.routes.ragRoute import rag_router

from .app.middlewares.errorHandler import register_global_exception_handlers
from .app.db.db_init import create_tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    create_tables()
    yield
    # Optional shutdown logic
    print("App is shutting down")

# Initialize FastAPI app with lifespan context manager
app = FastAPI(lifespan=lifespan)

# Register custom global error handler middleware
register_global_exception_handlers(app)

# Register routers with prefixes and tags
app.include_router(router=chat_router, prefix='/api/v1/chat', tags=['chat'])
app.include_router(router=auth_router, prefix='/api/v1/auth', tags=['auth'])
app.include_router(router=rag_router, prefix='/api/v1/rag', tags=['rag'])
