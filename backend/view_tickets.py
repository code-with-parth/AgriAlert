import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "agrialert.db")

def view_tickets():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM escalations WHERE status = 'Open' ORDER BY timestamp DESC").fetchall()
        if not rows:
            print("No open tickets found.")
            return
            
        print("--- Open Escalation Tickets ---")
        for row in rows:
            print(f"Ticket ID: {row['ticket_id']}")
            print(f"User ID:   {row['user_id']}")
            print(f"Urgency:   {row['urgency_level']}")
            print(f"Time:      {row['timestamp']}")
            print(f"Summary:   {row['issue_summary']}")
            print("-" * 30)
    finally:
        conn.close()

if __name__ == "__main__":
    view_tickets()
