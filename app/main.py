from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, tenants, users, players, teams, matches, messages

app = FastAPI(title="Fantacalcio Multi-Tenant API", root_path="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(users.router)
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(matches.router)
app.include_router(messages.router)


@app.get("/")
def root():
    return {"message": "Welcome to Fantacalcio Multi-Tenant API"}