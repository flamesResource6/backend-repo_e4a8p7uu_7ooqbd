"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# Example schemas (kept for reference; not used by the app but available to the DB viewer)
class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Student performance tracking schemas (used by this app)
class Student(BaseModel):
    """Students collection schema
    Collection name: "student"
    """
    name: str = Field(..., description="Student full name")
    email: Optional[str] = Field(None, description="Contact email")
    class_name: Optional[str] = Field(None, description="Class/Grade e.g., 10-A")
    roll_no: Optional[str] = Field(None, description="Roll number or ID")

class Assessment(BaseModel):
    """Assessments collection schema
    Collection name: "assessment"
    """
    student_id: str = Field(..., description="ID of the student (string ObjectId)")
    subject: str = Field(..., description="Subject name e.g., Mathematics")
    score: float = Field(..., ge=0, description="Obtained marks")
    total: float = Field(..., gt=0, description="Total marks")
    assessment_date: Optional[date] = Field(None, description="Date of assessment")
    assessment_type: Optional[str] = Field(None, description="Quiz/Test/Exam/Assignment")

# Add your own schemas here:
# --------------------------------------------------

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
