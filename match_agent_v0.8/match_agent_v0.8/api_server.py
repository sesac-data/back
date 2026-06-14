from json import JSONDecodeError

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.demo_recommendation_orchestrator import (
    DEMO_META,
    run_demo_recommendation_pipeline,
)


LOCAL_DEV_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]


app = FastAPI(
    title="Incentdoc Demo Recommendation API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=LOCAL_DEV_ORIGINS,
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],
    allow_headers=[
        "Content-Type",
    ],
)


@app.get("/health")
def health():

    return {
        "status":
            "ok",
    }


@app.post("/api/demo/recommendations/calculate")
async def calculate_demo_recommendations(
    request: Request
):

    try:

        payload = await request.json()

    except JSONDecodeError as exc:

        return JSONResponse(
            status_code=400,
            content={
                "recommended_combination":
                    None,
                "alternative_combinations":
                    [],
                "rejected_combinations":
                    [],
                "errors":
                    [
                        {
                            "field":
                                "body",
                            "reason":
                                "invalid_json",
                            "details":
                                str(
                                    exc
                                ),
                        }
                    ],
                "meta":
                    DEMO_META,
            },
        )

    return run_demo_recommendation_pipeline(
        payload
    )
