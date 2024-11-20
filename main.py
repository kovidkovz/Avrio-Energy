from fastapi import FastAPI, Request
import api_routes
from fastapi.responses import JSONResponse
import os
import uvicorn

from services import list_tasks_logic, create_task_logic, update_task_logic, delete_task_logic, order_tasks_logic



app = FastAPI()


@app.get(api_routes.LIST_TASKS)
async def list_tasks(request: Request):
    payload, status_code = await list_tasks_logic(request)
    return JSONResponse(content=payload, status_code=status_code)

@app.post(api_routes.CREATE_TASK)
async def create_task(request: Request):
    payload, status_code = await create_task_logic(request)
    return JSONResponse(content=payload, status_code=status_code)

@app.put(api_routes.UPDATE_TASK)
async def update_task(request: Request):
    payload, status_code = await update_task_logic(request)
    return JSONResponse(content=payload, status_code=status_code)

@app.delete(api_routes.DELETE_TASK)
async def delete_task(request: Request):
    payload, status_code = await delete_task_logic(request)
    return JSONResponse(content=payload, status_code=status_code)

@app.get(api_routes.ORDER_TASKS)
async def order_tasks(request: Request, order_by: str):
    payload, status_code = await order_tasks_logic(request, order_by)
    return JSONResponse(content=payload, status_code=status_code)


if __name__ == "__main__":
    is_debug = os.getenv("DEBUG", "0") == "1"
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=is_debug)