import os
import gspread
from fastapi import APIRouter

router = APIRouter()

# Підключення до Google Sheets
CREDENTIALS_PATH = os.getenv("CREDENTIALS_FILE")
SHEET_SKLAD = os.getenv("SHEET_SKLAD")

gc = gspread.service_account(filename=CREDENTIALS_PATH)
sh = gc.open_by_key(SHEET_SKLAD)
worksheet_courses = sh.worksheet("dictionary")

@router.get("/get_courses")
def get_courses():
    """Отримує список курсів з Google Sheets"""
    rows = worksheet_courses.get_all_records()
    courses = [{"id": i+1, "name": row["course"], "description": row.get("description", ""), "price": row.get("price", 0)} for i, row in enumerate(rows)]
    return {"courses": courses}
