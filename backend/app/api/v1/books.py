from app.core.database import get_db
from app.models.book import BookCreate, BookResponse
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


@router.post("/", response_model=BookResponse)
async def create_book(book: BookCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    book_dict = book.model_dump()
    result = await db.books.insert_one(book_dict)
    created_book = await db.books.find_one({"_id": result.inserted_id})
    created_book["id"] = str(created_book.pop("_id"))
    return BookResponse(**created_book)


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        object_id = ObjectId(book_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid book ID format")

    book = await db.books.find_one({"_id": object_id})
    if book:
        book["id"] = str(book.pop("_id"))
        return BookResponse(**book)
    raise HTTPException(status_code=404, detail=f"Book {book_id} not found")


@router.get("/", response_model=list[BookResponse])
async def list_books(limit: int = 10, db: AsyncIOMotorDatabase = Depends(get_db)):
    books = await db.books.find().to_list(limit)
    for book in books:
        book["id"] = str(book.pop("_id"))
    return [BookResponse(**book) for book in books]
