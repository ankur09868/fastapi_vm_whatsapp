from fastapi import FastAPI
from router import groups_details,bot_config as bot,schedule_message as sch_msg,dashboard,contacts
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from modules.sentiment import get_groups_message,save_sentiment_data,analyze_topic_and_sentiment
from datetime import datetime, timedelta
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
app.include_router(bot.bot_config_router,prefix="/bot_details")
app.include_router(sch_msg.router,prefix="/schedule_message")
app.include_router(contacts.contactrouter,prefix="/contact")

print("Starting scheduler...")
# Scheduler to run the task at midnight every day
scheduler = BackgroundScheduler()
scheduler.add_job(get_groups_message, 'cron', hour=00, minute=00)  # Run at midnight
scheduler.start()

@app.get("/sentiment")
async def get_sentiment():
    grouped_messages = get_groups_message()  # Fetch messages grouped by group
    print("Grouped Messages in get_sentiment:", grouped_messages) 
    
    # Check if the return type is a dictionary
    if isinstance(grouped_messages, list):
        return {"error": "Expected a dictionary, but got a list. Check the get_groups_message function."}
    
    # Loop through grouped messages and process each group
    for (group_name, tenant_id), messages in grouped_messages.items():  # Unpack group_name and tenant_id correctly
        sentiment_data = {"Positive": 0, "Neutral": 0, "Negative": 0, "Commercial": 0}
        topic_data = {}
        print("Group:", group_name)
        print("Messages:", messages)

        # Directly analyze the entire list of messages for the group
        analysis = analyze_topic_and_sentiment(messages)
        if analysis:
            sentiment_data = analysis.get("sentiment_data", {"Positive": 0, "Neutral": 0, "Negative": 0, "Commercial": 0})
            topic_data = analysis.get("topic_data", {})

            # Get current timestamp for the time when the sentiment data is processed
            current_time = datetime.now()

            # Save the sentiment and topic data into the database
            save_sentiment_data(group_name, sentiment_data, topic_data, current_time, tenant_id)

    return {"status": "Sentiment analysis completed successfully"}

@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()