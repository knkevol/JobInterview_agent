from fastapi import FastAPI

app = FastAPI(title="AI Interviewer Agent")

@app.get("/health")
def health_check():
    return {"status": "ok"}
