from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from database import get_db
from models.student import Student
from schemas.student import StudentCreate, StudentResponse
from dependencies import get_current_user

router = APIRouter()


# ✅ GET ALL STUDENTS
@router.get("/", response_model=List[StudentResponse])
def get_students(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    return db.query(Student).all()


# ✅ GET SINGLE STUDENT
@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return student


# ✅ CREATE STUDENT
@router.post("/", status_code=201, response_model=StudentResponse)
def create_student(
    data: StudentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    student = Student(**data.dict())
    db.add(student)

    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")

    return student


# ✅ UPDATE STUDENT
@router.put("/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    data: StudentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # ✅ Check duplicate email BEFORE updating
    existing = db.query(Student).filter(Student.email == data.email).first()
    if existing and existing.id != student_id:
        raise HTTPException(status_code=400, detail="Email already exists")

    # update fields
    student.name = data.name
    student.age = data.age
    student.email = data.email
    student.city = data.city

    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")

    return student


# ✅ DELETE STUDENT
@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    db.delete(student)
    db.commit()

    return {"message": f"Student '{student.name}' deleted"}