from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.api import router  # Change here to import router correct location

app = FastAPI(
    title="Baqir's Chat app backend",
    description="apis for chat app to allow all chat app features",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],  # allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["todos"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Baqir's Chat app, please use an authenticated front end application to use this service!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)