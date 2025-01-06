from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends

from typing import List
from functions import *
from datetime import datetime,timedelta
import os



app = FastAPI()

# Global configuration
SHEET_ID = os.getenv("SHEET_ID")


current_value = {"show_progress": get_spreadsheet_target(SHEET_ID)}
items = {}
target_amount = 2000
current_amount = 0
current_page = 0

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
        print(pledge)
        passdict = {pledge["id"]:({pledge["name"]: pledge["amount"]})}
        await update_items(passdict,True,donorid)
        if get_spreadsheet_target(SHEET_ID) == 'TRUE':
            await increment_progress()
    except Exception as e:
        print(f"Error processing donor ID: {e}")
    return {"message": "Donor ID received"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint to manage real-time updates."""
    await manager.connect(websocket)
    try:
        
        await update_value()
        await increment_progress()
        
        await total_donation()
        if get_spreadsheet_target(SHEET_ID)=='TRUE':
            await set_target()
            await increment_progress()
        
        pledges = get_all_pledges()
        if pledges:
    
            item_data = {pledge["id"]:({pledge["name"]: pledge["amount"]}) for pledge in pledges}
            print(item_data)
            
            await update_items(item_data)

        else:
            item_data = {}
            await update_items(item_data)
       
        while True:
            try:
                await websocket.receive_text()
            except RuntimeError:
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.get("/trigger_confetti")
@app.post("/trigger_confetti")
async def trigger_confetti():
    """Trigger confetti on the frontend."""
    await manager.broadcast({"action": "confetti"})
    
    return {"message": "Confetti triggered"}

@app.get("/get_current_page")
async def get_current_page():
    """Get the current page number."""
    global current_page
    return {"current_page": current_page}

@app.post("/set_current_page")
async def set_current_page(page: int):
    """Set the current page number."""
    global current_page
    current_page = page
    await manager.broadcast({"action": "update_page", "current_page": current_page})
    return {"message": f"Current page set to {current_page}"}


@app.get("/trigger_fireworks")
@app.post("/trigger_fireworks")
async def trigger_fireworks():
    """Trigger fireworks on the frontend."""
    await manager.broadcast({"action": "fireworks"})
    
    return {"message": "Fireworks triggered"}


@app.get("/update_progress")
@app.post("/update_progress")
async def update_value():
    """Update progress value and notify clients."""
    global current_value
    current_value["show_progress"] = get_spreadsheet_target(SHEET_ID)
    
    if get_spreadsheet_target(SHEET_ID)=="TRUE":
        goal = extract_number(gettargetnumber(SHEET_ID, get_spreadsheet_goalnumber(SHEET_ID)))
        add_or_update_donation(1,0, goal,True)
        await set_target()
        await increment_progress()
        # print(f"Progress updated: {current_value}")
        await manager.broadcast({"action": "update_p", "cur": current_value})
        return {"message": "Progress updated"}
    else:
       
        await total_donation()
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
    if total is None:
        total=0
    # print("dxfgchjklfgh",total)
    message= {
  "action": "totaldonation",
    "total": total
}
    await manager.broadcast(message)
    return {"total": total}

@app.post("/update_items")
async def update_items(item: dict,switch=None,donorid=None):
    """Broadcast item updates and calculate pagination."""
    global items
    if not switch:
        if item=={}:
            message = {
            "action": "update_items",
            "item": None,
           
        }
            await manager.broadcast(message)
            return {"message": "Item updates broadcasted"}
        items.update(item)
        # print(items)

        items_per_page = 9
        total_items = len(items)
        
        total_pages = 0
        if total_items//items_per_page and total_items%items_per_page==0:
            total_pages = total_items//items_per_page-1
        else:
            total_pages = total_items//items_per_page
        
       

        

        if get_spreadsheet_target(SHEET_ID)=='TRUE':

            await increment_progress()
            
        else:
            await total_donation()
                

        message = {
            "action": "update_items",
            "item": item,
            "page":total_pages
        }
        # print(f"Updated item: {item}, Page: {current_page}, Total Pages: {total_pages}")
        await manager.broadcast(message)
        return {"message": "Item updates broadcasted"}
    else:
        items.update(item)
        print("SINGLE ITEM",item)
        itemammount=float(list(item[int(donorid)].values())[0])
        print(itemammount)
        items_per_page = 9
        total_items = len(items)
        
        total_pages = 0
        if total_items//items_per_page and total_items%items_per_page==0:
            total_pages = total_items//items_per_page-1
        else:
            total_pages = total_items//items_per_page
        

        message = {
            "action": "update_items",
            "item": item,
            "page":total_pages
        }
        # print(f"Updated item: {item}, Page: {current_page}, Total Pages: {total_pages}")
        await manager.broadcast(message)
        


        spreadshhetfireworks=clean_text_to_int(get_pledgeconfetti(SHEET_ID))
        spreadshhetconfetti=clean_text_to_int(get_pledgefirework(SHEET_ID))
        
    
        
        if itemammount>=spreadshhetconfetti and itemammount>spreadshhetfireworks:
            
            await trigger_confetti()
        elif itemammount>=spreadshhetfireworks and itemammount<spreadshhetconfetti:
            
            await trigger_fireworks()
        # print(items)

        
       
        print("spreadsheettarget",get_spreadsheet_target(SHEET_ID))

        if get_spreadsheet_target(SHEET_ID)=='TRUE':
            

            await increment_progress()
            print("i am here")
            confetti_target_bool=checktarget(1)
            print("confetti_target_bool",confetti_target_bool)
            print("getcelebrationnumber(SHEET_ID,get_spreadsheet_goalnumber(SHEET_ID))",getcelebrationnumber(SHEET_ID,get_spreadsheet_goalnumber(SHEET_ID)))
        
            # print(getcelebrationnumber(SHEET_ID,get_spreadsheet_goalnumber(SHEET_ID)))
            if getcelebrationnumber(SHEET_ID,get_spreadsheet_goalnumber(SHEET_ID)).lower()=='confetti':
                if confetti_target_bool:
                    await trigger_confetti()
                
            elif getcelebrationnumber(SHEET_ID,get_spreadsheet_goalnumber(SHEET_ID)).lower()=='fireworks':
                if confetti_target_bool:
                    await trigger_fireworks()
        else:
            
            await total_donation()
                

        
        return {"message": "Item updates broadcasted"}