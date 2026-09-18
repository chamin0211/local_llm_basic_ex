from fastapi import FastAPI, Form, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles\

from sqlalchemy.orm import Session
import uvicorn
import os


from database import engine, SessionLocal, Base
import models

# models에 정의한 모든 클래스, 연결한 DB엔진에 테이블로 생성
Base.metadata.create_all(bind=engine)

# FastAPI() 객체 생성
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        # 마지막에 무조건 닫음
        db.close()

abs_path = os.path.dirname(os.path.realpath(__file__))

# templates/ 폴더 식별 객체 변수
templates = Jinja2Templates(directory=f"{abs_path}/templates")

# static/ 폴더를 fastapi에서 인식할 수 있도록 마운트시킴
app.mount("/static", StaticFiles(directory=f"{abs_path}/static"), name="static")

# localhost:8000/
@app.get("/")
async def home(request: Request, 
				db_ss: Session = Depends(get_db)):
    # db 객체 생성, 세션연결하기 <- 의존성 주임으로 처리
    # 테이블 조회
    todos = db_ss.query(models.Todo).order_by(models.Todo.id.desc()).all()
    
    print(type(todos))
    # db 조회한 결과를 출력함
    for todo in todos:
        print(todo.id, todo.task, todo.completed)

    return templates.TemplateResponse(
        request = request,
        name = "index.html",
        context={ "todos": todos}
        )

# todo 데이터를 받아서 db 테이블에 저장하기
@app.post("/add")
def add(request: Request, 
        task: str = Form(...), 
        db_ss : Session = Depends(get_db)
    ):
    print(task)
    # task 데이터를 받고, Todo 클래스를 통해서, 테이블과 연결된 객체 생성
    todo = models.Todo(task=task)
    # todos 테이블에 task 추가
    db_ss.add(todo)

    # 테이블에 반영
    db_ss.commit()

    # 엔드포인트 함수 home으로 redirect
    return RedirectResponse(url=app.url_path_for("home"),
                            status_code=status.HTTP_303_SEE_OTHER)

# todo 수정할 레코드 조회
@app.get("/edit/{todo_id}")
def edit(request: Request, todo_id: int,
         db_ss : Session = Depends(get_db)
         ):
    # todo_id 조회
    # edit 폼에 랜더링 -> 리턴
    todo = db_ss.query(models.Todo).filter(models.Todo.id==todo_id).first()
    print(todo.task)

    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    return templates.TemplateResponse(
        request=request,
        name = "edit.html",
        context = {"todo": todo}
    )

# todo 수정 내용 반영
@app.post("/edit/{todo_id}")
def update(request: Request, 
           todo_id: int, 
           task: str = Form(...), 
           completed: bool = Form(False), 
           db: Session = Depends(get_db)):
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    todo.task = task
    todo.completed = completed
    db.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)

# 삭제 확인 화면 보여주기
@app.get("/delete/{todo_id}")
def delete_confirm(todo_id: int, request: Request, db: Session = Depends(get_db)):
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()

    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    return templates.TemplateResponse(
        request=request,
        name="delete.html",
        context={"todo": todo}
    )

# 실제 삭제 처리
@app.post("/delete/{todo_id}")
def delete(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()

    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(todo)
    db.commit()

    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)

# main.py
@app.post("/toggle/{todo_id}")
def toggle(todo_id: int, db: Session = Depends(get_db)):
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    if todo is None:
        raise HTTPException(status_code=404, detail="Todo not found")
    todo.completed = not todo.completed
    db.commit()
    return RedirectResponse(url=app.url_path_for("home"), status_code=status.HTTP_303_SEE_OTHER)

# uv run fastapi dev
if __name__ == "__main__":
    # uvicorn.run("현재_파일이름:FastAPI 객체 식별자", reload=True)
    #reload=True : 개발자 모드
    uvicorn.run("main:app", reload=True)