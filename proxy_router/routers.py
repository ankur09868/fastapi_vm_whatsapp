from fastapi import APIRouter, HTTPException, Request
import requests

# Define the router
router = APIRouter()

@router.get("/get-qr")
async def proxy_get_qr(request: Request):
    """
    Proxy endpoint for fetching QR code from the VM.
    """
    try:
        # Get the request body from the frontend
        request_body = await request.json()
        
        # Forward the request to the VM
        response = requests.get("http://20.84.153.108:8000/qr_code/get_qr", json=request_body)
        
        # Check for response status
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/tracking/start")
async def proxy_start_tracking(request: Request):
    """
    Proxy endpoint for fetching QR code from the VM.
    """
    try:
        # Get the request body from the frontend
        request_body = await request.json()
        
        # Forward the request to the VM
        response = requests.post("http://20.84.153.108:8000/tracking/start", json=request_body)
        
        # Check for response status
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tracking/stop")
async def proxy_stop_tracking(request: Request):
    """
    Proxy endpoint for fetching QR code from the VM.
    """
    try:
        # Get the request body from the frontend
        request_body = await request.json()
        
        # Forward the request to the VM
        response = requests.post("http://20.84.153.108:8000/tracking/stop", json=request_body)
        
        # Check for response status
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/fetch_groups")
async def proxy_fetch_groups(request: Request):
    """
    Proxy endpoint for fetching QR code from the VM.
    """
    try:
        # Get the request body from the frontend
        request_body = await request.json()
        
        # Forward the request to the VM
        response = requests.get("http://20.84.153.108:8000/group_details/fetch_groups", json=request_body)
        
        # Check for response status
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/send")
async def proxy_send_message(request: Request):
    """
    Proxy endpoint for sending messages to the VM's messaging endpoint.
    """
    try:
        # Get the request body from the frontend
        request_body = await request.json()

        # Forward the request to the VM's messaging endpoint
        response = requests.post("http://20.84.153.108:8000/messaging/send", json=request_body)

        # Check for response status
        if response.status_code == 200:
            return response.json()
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))