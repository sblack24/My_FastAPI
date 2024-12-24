from typing import Annotated
from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy import select, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uvicorn  # wsgi сервер, с которым работает FastAPI

app = FastAPI()

engine = create_async_engine("sqlite+aiosqlite:///library.db", echo=True)
# with engine.connect() as conn:
#     conn.execute('''CREATE TABLE IF NOT EXIST)
# Создаем новую сессию на движке engine
# Сессия - это транзакция в базе данных
new_async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with new_async_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]

# Класс базовая модель. На его основе создаем классы для книг, авторов и выдач
class Base(DeclarativeBase):
    pass

# Функция создания в базе данных таблицы books
@app.post("/create")
async def create_database():
    async with engine.begin() as conn:  # Открываем соединение с базой данных
        await conn.run_sync(Base.metadata.drop_all)  # полностью очищаем таблицу
        await conn.run_sync(Base.metadata.create_all)  # создаем заново
    return {"OK":True}
# Author (Автор): id, имя, фамилия, дата рождения
# Объявление таблицы
class AuthorModel(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    surname: Mapped[str]
    birthday: Mapped[str]


class AuthorSchema(BaseModel):
    name: str
    surname: str
    birthday: str


class AuthorGetSchema(BaseModel):
    id: int
    name: str
    surname: str
    birthday: str

# Эндпоинты для авторов:
# Создание автора (POST /authors)
@app.post("/author")
async def add_author(author: AuthorSchema, session: SessionDep) -> AuthorSchema:
    new_autor = AuthorModel(
        name=author.name,
        surname=author.surname,
        birthday=author.birthday
    )
    session.add(new_autor)
    await session.commit()
    return author
# Получение списка авторов (GET /authors)
@app.get("/authors")
async def get_authors(session: SessionDep) -> list[AuthorGetSchema]:
    query = select(AuthorModel)
    result = await session.execute(query)
    authors = result.scalars().all()
    print(f"{authors}")
    return authors
# Получение информации об авторе по id (GET /authors/{id})
@app.get("/author/{id}")
async def get_author_id(author_id: int, session: SessionDep) -> list[AuthorGetSchema]:
    query = select(AuthorModel).where( AuthorModel.id == author_id)
    result = await session.execute(query)
    author = result.scalars().all()
    if author:
        print(f"{author}")
        return author
    return {"Нет такого автора":False}
# Обновление информации об авторе (PUT /authors/{id})
@app.put("/author/{id}")
async def put_author_id(author_id: int, update_author: AuthorSchema, session: SessionDep): #-> list[AuthorGetSchema]:
    author = await session.get(AuthorModel,author_id)
    if author:
        author.name = update_author.name
        author.surname = update_author.surname
        author.birthday = update_author.birthday
        await session.commit()
        return author
    return {"Нет такого автора":False}
# Удаление автора (DELETE /authors/{id})
@app.delete("/author/{id}")
async def del_author_id(author_id: int, session: SessionDep):
    author = await session.get(AuthorModel, author_id)
    if author:
        await session.delete(author)
        await session.commit()
        return {"OK":True}
    return {"Нет такого автора":False}

# Book (Книга): id, название, описание, id автора, количество доступных экземпляров.
# Объявление таблицы
class BookModel(Base):
    __tablename__ = "books"  # название таблицы в базе данных
    # Mapped[type] - транслирует тип данных Python в тип данных SQL (К примеру int в INTEGER, str в VARCHAR)
    id: Mapped[int] = mapped_column(primary_key=True)
    # mapped_colum - позволяет задать валидацию данных (к примеру, максимальная длина строки String(30)),
    # определить первичный ключ, т.е. id или uuid (primary_key=True), который будет определяться автоматически,
    # при занесении в таблицу, а также определить взаимоотношения
    title: Mapped[str]
    description: Mapped[str]
    author: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    copies: Mapped[int]

class BookSchema(BaseModel):
    title: str
    description: str
    author: int
    copies: int

class BookGetSchema(BaseModel):
    id: int
    title: str
    description: str
    author: int
    copies: int

# Эндпоинты для книг:
# Добавление книги (POST /books)
@app.post("/book")
async def add_book(book: BookSchema, session: SessionDep) -> BookSchema:
    new_book = BookModel(
        title=book.title,
        description=book.description,
        author=book.author,
        copies=book.copies,
    )
    session.add(new_book)
    await session.commit()
    return book
# Получение списка книг (GET /books)
@app.get("/books")
async def get_books(session: SessionDep) -> list[BookGetSchema]:
    query = select(BookModel)
    result = await session.execute(query)
    books = result.scalars().all()
    print(f"{books}")
    return books
# Получение информации о книге по id (GET /books/{id})
@app.get("/book/{id}")
async def get_book_id(book_id: int, session: SessionDep) -> list[BookGetSchema]:
    query = select(BookModel).where( BookModel.id == book_id)
    result = await session.execute(query)
    book = result.scalars().all()
    if book:
        print(f"{book}")
        return book
    return {"Нет такой книги":False}
# Обновление информации о книге (PUT /books/{id})
@app.put("/book/{id}")
async def put_book_id(book_id: int, update_book: BookSchema, session: SessionDep):
    book = await session.get(BookModel,book_id)
    if book:
        book.title = update_book.title
        book.description = update_book.description
        book.author = update_book.author
        book.copies = update_book.copies
        await session.commit()
        return book
    return {"Нет такой книги":False}
# Удаление книги (DELETE /books/{id})
@app.delete("/book/{id}")
async def del_book_id(book_id: int, session: SessionDep):
    book = await session.get(BookModel, book_id)
    if book:
        await session.delete(book)
        await session.commit()
        return {"OK":True}
    return {"Нет такой книги":False}

# Borrow (Выдача): id, id книги, имя читателя, дата выдачи, дата возврата.
# Объявление таблицы
class BorrowModel(Base):
    __tablename__ = "borrow"  # название таблицы в базе данных
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    name_reader: Mapped[str]
    get_date:Mapped[str]
    return_date:Mapped[str]
# Класс для SQLAlchemy для оформления выдачи книги
class BorrowGetSchema(BaseModel):
    book_id: int
    name_reader: str
    get_date: str
    return_date: str
# Класс для SQLAlchemy для оформления возврата книги
class BorrowReturnSchema(BaseModel):
    id: int
    book_id: int
    name_reader: str
    get_date: str
    return_date: str
# Бизнес-логика:
# Проверять наличие доступных экземпляров книги при создании записи о выдаче.
# Уменьшать количество доступных экземпляров книги при выдаче и увеличивать при возврате.
# При попытке выдать недоступную книгу возвращать соответствующую ошибку
# Эндпоинты для выдачи:
# Создание записи о выдаче книги (POST /borrows)
@app.post("/borrow")
async def borrow_book(borrow: BorrowGetSchema, session: SessionDep):# -> BorrowGetSchema:
    new_borrow = BorrowModel(
        book_id =  borrow.book_id,
        name_reader = borrow.name_reader,
        get_date = borrow.get_date,
        return_date = "" # borrow.return_date
    )
    book = await session.get(BookModel, borrow.book_id)
    if book.copies > 0:
        book.copies = book.copies - 1
        session.add(book)
        session.add(new_borrow)
        await session.commit()
        return borrow
    elif book.copies == 0:
        return {"Все экземпляры такой книги уже выданы": False}
    else:
        return False
# Получение списка всех выдач (GET /borrows)
@app.get("/borrows")
async def get_borrows(session: SessionDep) -> list[BorrowReturnSchema]:
    query = select(BorrowModel)
    result = await session.execute(query)
    borrows = result.scalars().all()
    print(f"{borrows}")
    return borrows
# Получение информации о выдаче по id (GET /borrows/{id})
@app.get("/borrow/{id}")
async def get_borrow_id(borrow_id: int, session: SessionDep) -> list[BorrowGetSchema]:
    query = select(BorrowModel).where( BorrowModel.id == borrow_id)
    result = await session.execute(query)
    borrow = result.scalars().all()
    if borrow:
        print(f"{borrow}")
        return borrow
    return {"Нет такой выдачи":False}
# Завершение выдачи (PATCH /borrows/{id}/return) с указанием даты возврата
@app.patch("/borrow/{id}/return")
async def return_borrow_id(borrow_id: int, return_date: str, session: SessionDep):#-> list[BorrowReturnSchema]:
    borrow = await session.get(BorrowModel,borrow_id)
    if borrow:
        if borrow.return_date:
            return {"Книга уже возвращена": FastAPI}
        borrow.return_date = return_date
        session.add(borrow)
        book = await session.get(BookModel, borrow.book_id)
        book.copies = book.copies + 1
        session.add(book)
        await session.commit()
        return borrow
    return {"Нет такой выдачи":False}

# запуск wsgi сервера и приложения под именем app.py на нём
if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8080, reload=True)
