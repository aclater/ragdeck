from fastapi import FastAPI

app = FastAPI(title="ragdeck", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}


def main():
    import uvicorn

    uvicorn.run("ragdeck.main:app", host="0.0.0.0", port=8095)
