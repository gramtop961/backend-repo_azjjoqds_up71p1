from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Any, Dict, List, Optional

from database import db, create_document, get_documents
import importlib
import schemas as app_schemas

app = FastAPI(title="SEO Expert API", version="1.0.0")

# CORS - allow all origins for dev preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LeadIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    service_interest: Optional[str] = None
    budget: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = "website"


@app.get("/")
def root() -> Dict[str, str]:
    return {"status": "ok", "service": "seo-expert-api"}


@app.get("/test")
def test_database() -> Dict[str, Any]:
    try:
        # Attempt a lightweight list collections operation
        if db is None:
            raise Exception("Database not configured")
        collections = db.list_collection_names()
        return {"database": "connected", "collections": collections}
    except Exception as e:
        return {"database": "unavailable", "error": str(e)}


@app.get("/schema")
def get_schema() -> Dict[str, Any]:
    # Introspect Pydantic models defined in schemas.py
    schema_info: Dict[str, Any] = {}
    for name in dir(app_schemas):
        obj = getattr(app_schemas, name)
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj is not BaseModel:
            try:
                schema_info[name] = obj.model_json_schema()
            except Exception:
                # Fallback minimal info
                schema_info[name] = {"title": name}
    return schema_info


@app.post("/lead")
def create_lead(lead: LeadIn) -> Dict[str, str]:
    try:
        # Ensure schema exists and collection name is derived from class name
        # We'll use the Lead schema defined in schemas.py for collection naming consistency
        collection_name = "lead"
        inserted_id = create_document(collection_name, lead)
        return {"status": "success", "id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/leads")
def list_leads(limit: int = 10) -> List[Dict[str, Any]]:
    try:
        docs = get_documents("lead", {}, limit)
        # Convert ObjectId to string for JSON serialization
        for d in docs:
            if "_id" in d:
                d["_id"] = str(d["_id"])
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
