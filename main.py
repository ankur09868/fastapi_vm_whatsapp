from fastapi import FastAPI
from router import groups_details,bot_config as bot,schedule_message as sch_msg,dashboard
from fastapi.middleware.cors import CORSMiddleware


# Create the FastAPI app
app = FastAPI(title="WhatsApp Automation API")


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins; adjust this if you need more specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)


# Include routers
app.include_router(dashboard.dashboard_router)
app.include_router(groups_details.router,prefix="/group_details")
app.include_router(bot.router,prefix="/bot_details")
app.include_router(sch_msg.router,prefix="/schedule_message")


# Application startup event
@app.on_event("startup")
async def startup_event():
    print("Application starting...")

# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutting down...")
