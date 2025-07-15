from fastapi import FastAPI, Request
from fastapi import Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import register_user, login_user
from app.models import UserRegister, UserLogin

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
def handle_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    nom: str = Form(...)
):
    try:
        user = UserRegister(email=email, password=password, nom=nom,)
        register_user(user)
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("register.html", {"request": request, "error": str(e)})
    

@app.get("/login", response_class=HTMLResponse)
def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def handle_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    try:
        user = UserLogin(email=email, password=password)
        result = login_user(user)
        return templates.TemplateResponse("home.html", {"request": request, "user": result["user"]})
    except Exception as e:
        return templates.TemplateResponse("login.html", {"request": request, "error": str(e)})