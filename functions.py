
import pandas as pd
import re
from datetime import datetime,timedelta

from supabase import create_client, Client
from datetime import datetime
from typing import Optional
import pytz


# Initialize Supabase client
supabase_url = "https://htjfvxtqbbwsdyupnosk.supabase.co"  # Replace with your Supabase URL
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh0amZ2eHRxYmJ3c2R5dXBub3NrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTczNjgyMiwiZXhwIjoyMDUxMzEyODIyfQ.lq-SHM1yd_TXehhUQOLGreYiD1f9s_4IUvdXwfNXkEc"  # Replace with your Supabase API Key
supabase: Client = create_client(supabase_url, supabase_key)

def add_or_update_donation(id: int, value: float, target: Optional[float] = None, reset_met_at: Optional[bool] = False):
    """
    Adds or updates a donation in the 'donations' table.
    
    - If the `id` exists, it updates the 'value' column by adding the `value` input.
    - If the `id` does not exist, it creates a new entry with the `value` and `target`.
    - If the updated 'value' equals or exceeds 'target', it updates the 'met_at' column with the current timestamp.
    - If no `target` is provided, only the `value` is updated.
    - If `reset_met_at` is True, the 'met_at' column will be set to `null`.

    :param id: The ID of the donation to update or create.
    :param value: The value to add to the donation or set to 0.
    :param target: The target value to compare against (optional).
    :param reset_met_at: Whether to reset the 'met_at' column to null (optional).
    :return: A success message or error.
    """
    try:
        # Check if the donation exists by ID
        result = supabase.table("donations").select("id", "value", "target", "met_at").eq("id", id).execute()
        
        data = result.data
        
        if not data:  # If no data is found, create a new donation
            # Create a new record if ID doesn't exist
            new_donation = {
                "id": id,
                "value": str(value),  # Store value as text
                "target": str(target) if target is not None else None,  # Store target as text (optional)
                "met_at": None
            }
            insert_result = supabase.table("donations").insert(new_donation).execute()
            return {"success": True, "data": insert_result.data}
        
        # If the record exists, update the 'value' column
        existing_value = float(data[0]["value"])  # Convert existing value to float
        updated_value = 0 if value == 0 else existing_value + value  # Update the value if not zero

        # Prepare the update data
        update_data = {"value": str(updated_value)}  # Save value as text

        # If a new target is provided, update the target as well
        if target is not None:
            update_data["target"] = str(target)  # Store target as text

        # If reset_met_at is True, reset the 'met_at' column to null
        if reset_met_at:
            update_data["met_at"] = None
        # If the updated value is greater than or equal to the target, set 'met_at' to the current timestamp
        elif updated_value >= (target if target is not None else float(data[0]["target"])):
            update_data["met_at"] = datetime.now().isoformat()

        # Update the donation record
        update_result = supabase.table("donations").update(update_data).eq("id", id).execute()
        
        return {"success": True, "data": update_result.data}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_met_at(id: int):
    """
    Checks if the 'met_at' value of the first row (based on the given ID) in the 'donations' table is None.

    :param id: The ID of the donation to check.
    :return: True if 'met_at' is not None, False if 'met_at' is None.
    """
    try:
        # Query the 'donations' table for the row with the given ID
        result = supabase.table("donations").select("met_at").eq("id", id).execute()
        
        
        # Extract the data
        data = result.data
        
        if not data:
            return 
        
        # Check the 'met_at' value
        met_at_value = data[0].get("met_at")
        
        
        if met_at_value is None:
            return 
        else:
            return met_at_value
        
    except Exception as e:
        return 
    

def check_time_period(timestamp_str, period_allowed):
    # Convert the timestamp string to a datetime object
    timestamp = datetime.fromisoformat(timestamp_str)
    
    # Get the current time in UTC
    current_time = datetime.now(pytz.UTC)
    
    # Calculate the time difference
    time_diff = current_time - timestamp
    
    # Compare the time difference with the allowed period
    return time_diff <= period_allowed



def get_all_pledges():
    """
    Retrieves all rows from the 'pledges' table and returns them as a list of dictionaries.

    :return: A list of dictionaries representing all pledges or an error message.
    """
    try:
        # Query the 'pledges' table for all rows
        result = supabase.table("pledges").select("*").execute()
        
        
        # Extract the data
        data = result.data
        if not data:
            
            return 
        
        return data
    
    except Exception as e:
        
        return 
    
def gettotal():
    k=get_all_pledges()
    totaldonations=sum([float(i['amount']) for i in k])
    return totaldonations

def get_pledge_by_id(id: int):
    """
    Retrieves a single pledge by its ID from the 'pledges' table.

    :param id: The ID of the pledge to retrieve.
    :return: A dictionary representing the pledge or an error message.
    """
    try:
        # Query the 'pledges' table for a row with the given ID
        result = supabase.table("pledges").select("*").eq("id", id).execute()
        
        # Extract the data
        data = result.data
        if not data:
            return 
        
        return  data[0]
        
    except Exception as e:
        return 

def get_donation_by_id(id: int):
    """
    Retrieves a single donation by its ID from the 'donations' table.

    :param id: The ID of the donation to retrieve.
    :return: A dictionary representing the donation or an error message.
    """
    try:
        # Query the 'donations' table for a row with the given ID
        result = supabase.table("donations").select("*").eq("id", id).execute()
        
        # Extract the data
        data = result.data
        if not data:
            return 
        
        return data[0]
        
    except Exception as e:
        return 

def extract_number(string):
    match = re.search(r'\d+(?:,\d+)*', string)  # Matches numbers with commas
    if match:
        return int(match.group().replace(',', ''))  # Remove commas and convert to int
    return None




def gettargetnumber(sheet_id,target):
    """
    Fetches the email from cell B2 of a public Google Sheet.
    
    Parameters:
        sheet_id (str): The ID of the Google Sheet (found in the sheet's URL).
    
    Returns:
        str: The email from cell k2.
    """
    # Construct the CSV URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    # Read the data into a DataFrame
    data = pd.read_csv(csv_url)
    
    
    if target=='1':
        targetvalue = data.iloc[0, 4]
    elif target=='2':
        targetvalue = data.iloc[1, 4]
    elif target=='3':
        targetvalue = data.iloc[2, 4]
    elif target=='4':
        targetvalue = data.iloc[3, 4]
    elif target=='5':
        targetvalue = data.iloc[4, 4]

    
    return targetvalue
def getcelebrationnumber(sheet_id,target):
    """
    Fetches the email from cell B2 of a public Google Sheet.
    
    Parameters:
        sheet_id (str): The ID of the Google Sheet (found in the sheet's URL).
    
    Returns:
        str: The email from cell k2.
    """
    # Construct the CSV URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    # Read the data into a DataFrame
    data = pd.read_csv(csv_url)
    
    
    if target=='1':
        targetvalue = data.iloc[0, 7]
    elif target=='2':
        targetvalue = data.iloc[1, 7]
    elif target=='3':
        targetvalue = data.iloc[2, 7]
    elif target=='4':
        targetvalue = data.iloc[3, 7]
    elif target=='5':
        targetvalue = data.iloc[4, 7]

    
    return targetvalue


def get_spreadsheet_goalnumber(sheet_id):
    """
    Fetches the email from cell B2 of a public Google Sheet.
    
    Parameters:
        sheet_id (str): The ID of the Google Sheet (found in the sheet's URL).
    
    Returns:
        str: The email from cell B2.
    """
    # Construct the CSV URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    # Read the data into a DataFrame
    data = pd.read_csv(csv_url)
    
    # Extract and return the email from the second column (B2)
    email = data.iloc[1, 10]  # Assuming B2 corresponds to index 0, column 1
    return email



def get_spreadsheet_target(sheet_id):
    """
    Fetches the email from cell B2 of a public Google Sheet.
    
    Parameters:
        sheet_id (str): The ID of the Google Sheet (found in the sheet's URL).
    
    Returns:
        str: The email from cell k2.
    """
    # Construct the CSV URL
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    # Read the data into a DataFrame
    data = pd.read_csv(csv_url)
    
    # Extract and return the email from the second column (B2)
    email = data.iloc[0, 10]  # Assuming B2 corresponds to index 0, column 1
    return email
