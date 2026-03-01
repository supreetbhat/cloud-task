from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to my Cloud Hosting API!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "server": "running"}

