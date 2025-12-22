import random
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn


app = FastAPI(title="Mock SMS Operator API", version="1.0.0")


class SMSRequest(BaseModel):
    phone_number: str = Field(..., min_length=10, max_length=20)
    message: str = Field(..., min_length=1, max_length=70)


class SMSResponse(BaseModel):
    status: str
    message_id: str
    error: str = None


@app.post("/send", response_model=SMSResponse)
async def send_sms(request: SMSRequest) -> SMSResponse:
    # Simulate network delay (50-200ms)
    time.sleep(random.uniform(0.05, 0.2))

    # 95% success rate, 5% failure
    success = random.random() < 0.95

    if success:
        message_id = f"msg_{int(time.time())}_{random.randint(1000, 9999)}"
        print(f"✓ SMS sent to {request.phone_number}: {request.message[:30]}... [ID: {message_id}]")
        return SMSResponse(
            status="sent",
            message_id=message_id
        )
    else:
        error_msg = random.choice([
            "Network timeout",
            "Invalid phone number",
            "Service temporarily unavailable",
            "Rate limit exceeded"
        ])
        print(f"✗ SMS failed to {request.phone_number}: {error_msg}")
        return SMSResponse(
            status="failed",
            message_id="",
            error=error_msg
        )


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mock_operator"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
