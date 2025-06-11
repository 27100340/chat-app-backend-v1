
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.api import router

app = FastAPI(
    title="Baqir's Chat app backend",
    description="apis for chat app to allow all chat app features",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    # Update to allow your production frontend domain
    allow_origins=["http://127.0.0.1:5500", "https://your-frontend-domain.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["todos"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Baqir's Chat app, please use an authenticated front end application to use this service!"}

# Remove the __main__ block as Vercel handles the server