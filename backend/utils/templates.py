from fastapi.templating import Jinja2Templates
from backend.config import TEMPLATES_DIR

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))