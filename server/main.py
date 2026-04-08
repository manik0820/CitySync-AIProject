from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from passlib.context import CryptContext

from database import supabase
from nlp_module import analyse_complaint
from ml_model import get_priority_score

load_dotenv()

app = FastAPI(title="CitySync API", version="1.0.0")

# ---------------------------------------------------------------------------
# CORS — allows React frontend (localhost:5173) to talk to this server
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ComplaintInput(BaseModel):
    description:   str
    category:      str
    location_text: str
    latitude:      Optional[float] = None
    longitude:     Optional[float] = None


class StatusUpdate(BaseModel):
    status: str   # "pending" | "in-progress" | "resolved"


class LoginInput(BaseModel):
    email:    str
    password: str


class OfficerCreate(BaseModel):
    email:    str
    password: str
    name:     str


# ---------------------------------------------------------------------------
# Cost lookup — estimated resolution cost in rupees per category
# Used in the priority-per-cost formula from the paper
# ---------------------------------------------------------------------------

COST_LOOKUP = {
    "road":          15000.0,
    "water":          8000.0,
    "sanitation":     6000.0,
    "lighting":       3000.0,
    "public_safety": 10000.0,
    "other":          5000.0,
}


# ---------------------------------------------------------------------------
# Helper — compute real feature values from DB before ML scoring
# ---------------------------------------------------------------------------

def compute_features(category: str) -> dict:
    """
    Queries Supabase to compute real feature values for a new complaint.

    Returns
    -------
    dict with:
      recurrence_count   : how many complaints of same category already exist
      population_density : fixed realistic urban default (no census API)
      days_since_filed   : 0.0 for a brand new complaint (correct by definition)
      estimated_cost     : looked up from COST_LOOKUP by category
    """
    try:
        response = (
            supabase.table("complaints")
            .select("id")
            .eq("category", category.lower())
            .execute()
        )
        recurrence_count = len(response.data) + 1  # +1 to include current one
    except Exception:
        recurrence_count = 1  # fallback if DB query fails

    return {
        "recurrence_count":   recurrence_count,
        "population_density": 1500.0,
        "days_since_filed":   0.0,
        "estimated_cost":     COST_LOOKUP.get(category.lower(), 5000.0),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "CitySync API is running"}


# ------ AUTH ---------------------------------------------------------------

@app.post("/auth/login")
def login(body: LoginInput):
    """Officer login. Returns a session token."""
    response = supabase.table("officers").select("*").eq("email", body.email).execute()

    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    officer = response.data[0]

    if not pwd_context.verify(body.password, officer["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_response = supabase.table("sessions").insert({
        "officer_id": officer["id"]
    }).execute()

    if not session_response.data:
        raise HTTPException(status_code=500, detail="Failed to create session")

    token = session_response.data[0]["id"]

    return {
        "message": "Login successful",
        "token":   token,
        "officer": {
            "id":    officer["id"],
            "name":  officer["name"],
            "email": officer["email"],
        }
    }


@app.post("/auth/register")
def register_officer(body: OfficerCreate):
    """Create a new officer account with a hashed password."""
    existing = supabase.table("officers").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = pwd_context.hash(body.password)

    response = supabase.table("officers").insert({
        "email":    body.email,
        "password": hashed_password,
        "name":     body.name,
    }).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create officer")

    officer = response.data[0]
    return {
        "message": "Officer created successfully",
        "officer": {
            "id":    officer["id"],
            "name":  officer["name"],
            "email": officer["email"],
        }
    }


# ------ COMPLAINTS ---------------------------------------------------------

@app.post("/complaints")
def create_complaint(data: ComplaintInput):
    """
    Main endpoint — called when a citizen submits a complaint.

    Flow:
      1. Run NLP  → severity_label + urgency_score
      2. Compute real features from DB (recurrence, cost, etc.)
      3. Run ML model → priority_score using full feature vector
      4. Save to Supabase
      5. Return saved record to React
    """

    # Step 1 — NLP
    nlp_result     = analyse_complaint(data.description)
    severity_label = nlp_result["severity_label"]
    urgency_score  = nlp_result["urgency_score"]

    # Step 2 — Real features from DB
    features = compute_features(data.category)

    # Step 3 — ML priority score
    priority_score = get_priority_score(
        severity_label     = severity_label,
        urgency_score      = urgency_score,
        category           = data.category,
        recurrence_count   = features["recurrence_count"],
        population_density = features["population_density"],
        days_since_filed   = features["days_since_filed"],
        estimated_cost     = features["estimated_cost"],
    )

    # Step 4 — Save to Supabase
    record = {
        "description":    data.description,
        "category":       data.category.lower(),
        "location_text":  data.location_text,
        "latitude":       data.latitude,
        "longitude":      data.longitude,
        "severity_label": severity_label,
        "urgency_score":  urgency_score,
        "priority_score": priority_score,
        "status":         "pending",
    }

    response = supabase.table("complaints").insert(record).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to save complaint to database")

    return {
        "message": "Complaint submitted successfully",
        "data":    response.data[0],
    }


@app.get("/complaints")
def get_complaints(
    status:   Optional[str] = None,
    category: Optional[str] = None,
):
    """Returns all complaints sorted by priority_score DESC."""
    query = (
        supabase.table("complaints")
        .select("*")
        .order("priority_score", desc=True)
    )

    if status:
        query = query.eq("status", status)
    if category:
        query = query.eq("category", category.lower())

    response = query.execute()

    return {
        "count": len(response.data),
        "data":  response.data,
    }


@app.get("/complaints/{complaint_id}")
def get_complaint(complaint_id: str):
    response = (
        supabase.table("complaints")
        .select("*")
        .eq("id", complaint_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return response.data[0]


@app.patch("/complaints/{complaint_id}/status")
def update_status(complaint_id: str, body: StatusUpdate):
    """Officer updates complaint status."""
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


@app.delete("/complaints/{complaint_id}")
def delete_complaint(complaint_id: str):
    """Deletes a complaint — useful for removing spam."""
    response = (
        supabase.table("complaints")
        .delete()
        .eq("id", complaint_id)
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return {"message": "Complaint deleted successfully"}