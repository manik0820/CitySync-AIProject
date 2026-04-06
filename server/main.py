from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from ml_model import get_priority_score

from database import supabase
from nlp_module import analyse_complaint

load_dotenv()

app = FastAPI(title="CitySync API", version="1.0.0")

# ---------------------------------------------------------------------------
# CORS — allows the React frontend (localhost:5173) to talk to this server
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic schemas
# These define the shape of data coming IN and going OUT of the API.
# ---------------------------------------------------------------------------

class ComplaintInput(BaseModel):
    """Shape of the JSON body React sends when filing a complaint."""
    description:    str
    category:       str                  # e.g. "road", "water", "sanitation"
    location_text:  str                  # human-readable address
    latitude:       Optional[float] = None
    longitude:      Optional[float] = None


class StatusUpdate(BaseModel):
    """Shape of the body React sends when an officer updates complaint status."""
    status: str                          # "pending" | "in-progress" | "resolved"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """
    Simple health check.
    Visit http://localhost:8000/health to confirm the server is running.
    """
    return {"status": "ok", "message": "CitySync API is running"}


# ------ CREATE a complaint --------------------------------------------------

@app.post("/complaints")
def create_complaint(data: ComplaintInput):
    """
    Main endpoint. Called when a citizen submits a complaint on the frontend.

    Flow:
      1. Run NLP on the description → severity label + urgency score + entities
      2. Compute a basic priority score (ML model will replace this later)
      3. Save everything to Supabase
      4. Return the saved record to the frontend
    """

    # Step 1 — NLP analysis
    nlp_result = analyse_complaint(data.description)
    severity_label = nlp_result["severity_label"]
    urgency_score  = nlp_result["urgency_score"]

    # Step 2 — Temporary priority score based on urgency only
    priority_score = get_priority_score(
    severity_label   = severity_label,
    urgency_score    = urgency_score,
    category         = data.category,
    )
    # priority_score is now in range [10, 100] approximately

    # Step 3 — Build the record to insert into Supabase
    record = {
        "description":      data.description,
        "category":         data.category,
        "location_text":    data.location_text,
        "latitude":         data.latitude,
        "longitude":        data.longitude,
        "severity_label":   severity_label,
        "urgency_score":    urgency_score,
        "priority_score":   priority_score,
        "status":           "pending",
    }

    # Step 4 — Insert into Supabase
    response = supabase.table("complaints").insert(record).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to save complaint to database")

    return {
        "message": "Complaint submitted successfully",
        "data":    response.data[0],
    }


# ------ READ all complaints (officer dashboard) ----------------------------

@app.get("/complaints")
def get_complaints(status: Optional[str] = None, category: Optional[str] = None):
    """
    Returns all complaints sorted by priority score (highest first).
    Officers use this for the dashboard.

    Optional query params:
      ?status=pending
      ?category=road
      ?status=pending&category=water

    Example: GET /complaints?status=pending
    """
    query = supabase.table("complaints").select("*").order("priority_score", desc=True)

    if status:
        query = query.eq("status", status)
    if category:
        query = query.eq("category", category)

    response = query.execute()

    return {
        "count": len(response.data),
        "data":  response.data,
    }


# ------ READ a single complaint --------------------------------------------

@app.get("/complaints/{complaint_id}")
def get_complaint(complaint_id: str):
    """
    Returns one complaint by its UUID.
    """
    response = supabase.table("complaints").select("*").eq("id", complaint_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return response.data[0]


# ------ UPDATE complaint status (officer action) ---------------------------

@app.patch("/complaints/{complaint_id}/status")
def update_status(complaint_id: str, body: StatusUpdate):
    """
    Lets an officer update the status of a complaint.
    Valid statuses: "pending", "in-progress", "resolved"

    Example: PATCH /complaints/<uuid>/status
    Body: { "status": "in-progress" }
    """
    valid_statuses = {"pending", "in-progress", "resolved"}
    if body.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    response = (
        supabase.table("complaints")
        .update({"status": body.status})
        .eq("id", complaint_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return {
        "message": f"Status updated to '{body.status}'",
        "data":    response.data[0],
    }


# ------ DELETE a complaint (admin only, optional) --------------------------

@app.delete("/complaints/{complaint_id}")
def delete_complaint(complaint_id: str):
    """
    Deletes a complaint. Useful for removing spam/fake complaints.
    """
    response = supabase.table("complaints").delete().eq("id", complaint_id).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return {"message": "Complaint deleted successfully"}