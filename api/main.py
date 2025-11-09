from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "You've reached the Kind-To-Homeless API"}


@app.get("/nearby")
async def nearby(lat: float, lon: float, radius: float):
    return {
        "latitude": lat,
        "longitude": lon,

    }

