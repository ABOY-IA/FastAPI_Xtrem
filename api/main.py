from .events import connect_to_db, disconnect_from_db

app.add_event_handler("startup", connect_to_db)
app.add_event_handler("shutdown", disconnect_from_db)
