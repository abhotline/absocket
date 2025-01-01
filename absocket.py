from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends

from typing import List
from functions import *
from datetime import datetime,timedelta


app = FastAPI()

# Global configuration
SHEET_ID = "1EAl0Pb-ehUa8iX_f6O265Kdjkf0UIsRkZLEVNdW7bVo"

current_value = {"show_progress": get_spreadsheet_target(SHEET_ID)}
items = {}
target_amount = 2000
current_amount = 0

# Dependency for database session


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message to WebSocket: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

# Routes
@app.get("/")
async def read_root():
    return {"message": "Hello World"}

@app.get("/updateui")
async def update_ui(donorid: str):
    """Handle donor ID and update the UI."""

    try:
        pledge = get_pledge_by_id(int(donorid))
        passdict = {pledge["name"]: pledge["amount"]}
        await update_items(passdict)
        if get_spreadsheet_target(SHEET_ID):
            await increment_progress()
    except Exception as e:
        print(f"Error processing donor ID: {e}")
    return {"message": "Donor ID received"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to manage real-time updates."""
    await manager.connect(websocket)
    try:
        pledges = get_all_pledges()
        
        item_data = {pledge["name"]: pledge["amount"] for pledge in pledges}
        
        await update_items(item_data)
        await update_value()
        await increment_progress()
        await total_donation()
        if get_spreadsheet_target(SHEET_ID):
            await set_target()
            await increment_progress()

        while True:
            try:
                await websocket.receive_text()
            except RuntimeError:
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.post("/trigger_confetti")
async def trigger_confetti():
    """Trigger confetti on the frontend."""
    try:
        mettimestamp = check_met_at(1)
        if mettimestamp:
            if check_time_period(mettimestamp, timedelta(minutes=1)):

                await manager.broadcast({"action": "confetti"})

    except Exception as e:
            pass
    return {"message": "Confetti triggered"}

@app.post("/trigger_fireworks")
async def trigger_fireworks():
    """Trigger fireworks on the frontend."""
    if check_met_at(1):
        if check_time_period(check_met_at(1), timedelta(minutes=1)):

            await manager.broadcast({"action": "fireworks"})
    return {"message": "Fireworks triggered"}

@app.post("/update_progress")
async def update_value():
    """Update progress value and notify clients."""
    global current_value
    current_value["show_progress"] = get_spreadsheet_target(SHEET_ID)
    
    if get_spreadsheet_target(SHEET_ID):
        goal = extract_number(gettargetnumber(SHEET_ID, get_spreadsheet_goalnumber(SHEET_ID)))
        add_or_update_donation(1,0, goal,True)
        await set_target()
        print(f"Progress updated: {current_value}")
        await manager.broadcast({"action": "update_p", "cur": current_value})
        return {"message": "Progress updated"}
    else:
        await manager.broadcast({"action": "update_p", "cur": current_value})

@app.post("/set_target")
async def set_target():
    """Set the target amount for progress tracking."""
    global target_amount
    target_data = get_donation_by_id(1)
    target_amount = target_data["target"]
    await manager.broadcast({"action": "update_target", "target_amount": target_amount})
    return {"message": f"Target set to {target_amount}"}

@app.post("/increment_progress")
async def increment_progress():
    """Increment progress and notify clients."""
    global current_amount, target_amount
    progress_data = get_donation_by_id(1)
    current_amount = progress_data["value"]
    target_amount = progress_data["target"]
    await manager.broadcast({
        "action": "update_progress",
        "current_amount": current_amount,
        "target_amount": target_amount
    })
    return {"message": "Progress incremented"}


@app.post("/totaldonation")
async def total_donation():
    """Get the total donation amount."""
    total=gettotal()
    print("dxfgchjklfgh",total)
    message= {
  "action": "totaldonation",
    "total": total
}
    await manager.broadcast(message)
    return {"total": total}

@app.post("/update_items")
async def update_items(item: dict):
    """Broadcast item updates and calculate pagination."""
    global items
    items.update(item)

    items_per_page = 9
    total_items = len(items)
    
    total_pages = (total_items + items_per_page - 1) // items_per_page
    current_page = max(total_pages - 1, 0)

    

    if get_spreadsheet_target(SHEET_ID)==True:

        await increment_progress()
        # print(getcelebrationnumber(SHEET_ID,get_spreadsheet_goalnumber(SHEET_ID)))
        if getcelebrationnumber(SHEET_ID,get_spreadsheet_goalnumber(SHEET_ID)).lower()=='confetti':
            await trigger_confetti()
        elif getcelebrationnumber(SHEET_ID,get_spreadsheet_goalnumber(SHEET_ID)).lower()=='fireworks':
            await trigger_fireworks()
    else:
        await total_donation()
            

    message = {
        "action": "update_items",
        "item": item,
        "pagination": {
            "current_page": current_page,
            "total_pages": total_pages
        }
    }
    # print(f"Updated item: {item}, Page: {current_page}, Total Pages: {total_pages}")
    await manager.broadcast(message)
    return {"message": "Item updates broadcasted"}
