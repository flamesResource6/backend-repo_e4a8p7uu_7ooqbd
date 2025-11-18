import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Student, Assessment

app = FastAPI(title="Student Performance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Student Performance Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Helpers
class StudentCreate(Student):
    pass

class AssessmentCreate(Assessment):
    pass


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


def compute_stats(assessments: List[Dict[str, Any]]):
    # compute per-subject average, overall average, best/worst, total assessments
    subject_scores: Dict[str, List[float]] = {}
    overall_scores: List[float] = []
    for a in assessments:
        score = float(a.get("score", 0))
        total = float(a.get("total", 0)) or 1
        pct = (score / total) * 100.0
        overall_scores.append(pct)
        subject = a.get("subject", "Unknown")
        subject_scores.setdefault(subject, []).append(pct)
    per_subject = {s: sum(v)/len(v) for s, v in subject_scores.items()} if subject_scores else {}
    overall_avg = sum(overall_scores)/len(overall_scores) if overall_scores else 0.0
    best_subject = max(per_subject, key=per_subject.get) if per_subject else None
    worst_subject = min(per_subject, key=per_subject.get) if per_subject else None
    return {
        "overall_average": round(overall_avg, 2),
        "per_subject_average": {k: round(v, 2) for k, v in per_subject.items()},
        "best_subject": best_subject,
        "worst_subject": worst_subject,
        "assessments_count": len(assessments),
    }


# Routes
@app.post("/api/students", response_model=dict)
def create_student(student: StudentCreate):
    student_id = create_document("student", student)
    return {"id": student_id}


@app.get("/api/students", response_model=List[dict])
def list_students():
    docs = get_documents("student")
    # Convert ObjectId to string
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs


@app.post("/api/assessments", response_model=dict)
def create_assessment(assessment: AssessmentCreate):
    # validate student exists
    sid = assessment.student_id
    try:
        doc = db["student"].find_one({"_id": to_object_id(sid)})
    except Exception:
        doc = None
    if not doc:
        raise HTTPException(status_code=404, detail="Student not found")
    a_id = create_document("assessment", assessment)
    return {"id": a_id}


@app.get("/api/students/{student_id}/assessments")
def get_student_assessments(student_id: str):
    docs = get_documents("assessment", {"student_id": student_id})
    for d in docs:
        d["_id"] = str(d.get("_id"))
    return docs


@app.get("/api/students/{student_id}/stats")
def get_student_stats(student_id: str):
    assessments = get_documents("assessment", {"student_id": student_id})
    stats = compute_stats(assessments)
    return stats


@app.get("/api/overview")
def overall_overview():
    # overall stats across all students
    assessments = get_documents("assessment")
    stats = compute_stats(assessments)
    # add top students by average
    pipeline = [
        {"$addFields": {"pct": {"$multiply": [{"$divide": ["$score", {"$cond": [
            {"$gt": ["$total", 0]}, "$total", 1]}]}, 100]}}},
        {"$group": {"_id": "$student_id", "avgPct": {"$avg": "$pct"}, "count": {"$sum": 1}}},
        {"$sort": {"avgPct": -1}},
        {"$limit": 5}
    ]
    try:
        top = list(db["assessment"].aggregate(pipeline))
        for t in top:
            t["student_id"] = t.pop("_id")
            # attach student name
            sdoc = db["student"].find_one({"_id": to_object_id(t["student_id"])})
            t["student_name"] = sdoc.get("name") if sdoc else None
    except Exception:
        top = []
    stats["top_students"] = top
    return stats


# Expose schemas for viewer
@app.get("/schema")
def get_schema_info():
    # Minimal endpoint to indicate schemas exist; the viewer reads schemas.py directly
    return {"schemas": ["student", "assessment"]}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
