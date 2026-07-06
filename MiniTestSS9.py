from fastapi import FastAPI, status, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from fastapi.responses import JSONResponse
class BaseResponse(BaseModel):
    status_code: int
    message: str
    data: Optional[Any]
    error: Optional[Any]
    time_stamp: str
    path: str
def create_response(req,status_code, message, data = None, error = None):
    return BaseResponse(
        status_code=status_code,
        message=message,
        data=data,
        error=error,
        time_stamp=datetime.now().isoformat(),
        path=req.url.path
    )
class BaseTicket(BaseModel):
    movie_name: str = Field(min_length=1)
    room_code: str = Field(min_length=1)
    quantity: int = Field(ge=1,le=10)
app = FastAPI()
@app.exception_handler(HTTPException)
def http_exception(req: Request, exc: HTTPException):
    response = create_response(req,exc.status_code,"Failed",exc.detail)
    return JSONResponse (
        status_code=exc.status_code,
        content=response.model_dump()
    )
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    response = BaseResponse(
        status_code=500,
        message="Internal Server Error",
        data=None,
        error=str(exc),
        time_stamp=datetime.now().isoformat(),
        path=request.url.path
    )
    return JSONResponse(
        status_code=500,
        content=response.model_dump()
    )
tickets_db = [
    {"id": 1, "movie_name": "Doctor Strange 3", "room_code": "IMAX-01", "quantity": 2, "status": "confirmed", "created_at": "2026-07-01T19:00:00Z"},
    {"id": 2, "movie_name": "Avatar 3", "room_code": "PREMIUM-02", "quantity": 1, "status": "confirmed", "created_at": "2026-07-01T20:15:00Z"}
]
@app.get("/tickets")
def get_tickets(req: Request):
    return create_response(req,status.HTTP_200_OK,"Lấy danh sách vé thành công",tickets_db)
@app.post("/tickets")
def add_tickets(req: Request, tickets_in: BaseTicket):
    if tickets_in.movie_name.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Tên phim không được để trống")
    if tickets_in.room_code.strip() == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="Mã phòng không được để trống")
    check = next((film for film in tickets_db if film["movie_name"] == tickets_in.movie_name and film["room_code"] == tickets_in.room_code),None)
    if check:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="ERR-CINE-01: Ticket conflict for movie and room combination.")
    else:
        new_tickets = {
            "id": max((film["id"] for film in tickets_db),default=0)+1,
            **tickets_in.dict(),
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        tickets_db.append(new_tickets)
        return create_response(req,status.HTTP_201_CREATED,"Đặt vé thành công",new_tickets)
@app.delete("/tickets/{ticket_id}")
def delete_tickets(req: Request, ticket_id: int):
    check_id = next((film for film in tickets_db if film["id"] == ticket_id),None)
    if check_id:
        tickets_db.remove(check_id)
        return create_response(req,status.HTTP_200_OK,"Hủy vé thành công")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ERR-CINE-02: Ticket ID does not exist."
        )