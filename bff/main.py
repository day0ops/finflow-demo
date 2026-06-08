from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat import router as chat_router
from routes.health import router as health_router
from routes.me import router as me_router
from routes.news import router as news_router
from routes.policies import router as policies_router
from routes.portfolio import router as portfolio_router
from routes.tickers import router as tickers_router

app = FastAPI(title="finflow-bff")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(tickers_router)
app.include_router(portfolio_router)
app.include_router(policies_router)
app.include_router(chat_router)
app.include_router(news_router)
app.include_router(me_router)
