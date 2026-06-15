from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Importa tus modelos de SQLAlchemy (Usuario, Perfil, etc.)
from .models import Usuario, Perfil, NivelCategoria, SesionEjercicio, Logro, ResultadoEjercicio, Feedback, TutorIA
from .schemas import TokenJWT, UserCreate, UserLogin, ResumenProgreso, FeedbackResponse

app = FastAPI()

# Configura el motor de base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    scopes=["profile", "write"],
)

@app.post("/register/", response_model=UserCreate)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = Usuario(
        email=user.email,
        passwordHash=hash_password(user.password),
        creadoEn=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return user

@app.post("/login/", response_model=TokenJWT, summary="Obtiene un token de autenticación.")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/me/", response_model=UserCreate, summary="Información del usuario autenticado.")
async def read_user_me(current_user: Usuario = Depends(get_current_user)):
    return current_user

# Define tus endpoints de ejercicio
@app.post("/api/ejercicio/siguiente/", response_model=Ejercicio, summary="Genera un nuevo ejercicio para el usuario.")
async def generar_siguiente_ejercicio(perfil: Perfil, db: Session = Depends(get_db)):
    # Lógica para generar el siguiente ejercicio basado en el perfil y la dificultad
    pass

@app.post("/api/ejercicio/responder/", response_model=ResultadoEjercicio, summary="Valida una respuesta del usuario a un ejercicio.")
async def responder_ejercicio(ejercicio_id: int, respuesta: str, db: Session = Depends(get_db)):
    # Lógica para validar la respuesta y calcular feedback
    pass

# Define tus endpoints de tutoria y dificultad adaptativa
@app.get("/api/tutoria/", response_model=ResultadoEjercicio, summary="Obtiene el siguiente ejercicio basado en las respuestas del usuario.")
async def obtener_siguiente_ejercicio(perfil: Perfil, db: Session = Depends(get_db)):
    # Lógica para generar el siguiente ejercicio basado en la dificultad adaptativa
    pass

@app.get("/api/dificultad/", response_model=FeedbackResponse, summary="Obtiene el feedback sobre una respuesta.")
async def obtener_feedback(resultado_ejercicio: ResultadoEjercicio, db: Session = Depends(get_db)):
    # Lógica para calcular y retornar el feedback
    pass

@app.get("/api/progreso/", response_model=ResumenProgreso, summary="Obtiene el progreso del usuario.")
async def obtener_progreso(user_id: int, db: Session = Depends(get_db)):
    # Lógica para obtener el resumen de progreso del usuario
    pass

# Funciones auxiliares (hash_password, authenticate_user, create_access_token, get_current_user)
from fastapi.security import OAuth2PasswordBearer, SecurityScopes, OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from jose import JWTError, jwt
from pydantic import BaseModel
from passlib.context import CryptContext

crypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return crypt_context.hash(password)

def authenticate_user(db: Session, email: str, password: str) -> Usuario:
    user = db.query(Usuario).filter_by(email=email).first()
    if not user or not crypt_context.verify(password, user.passwordHash):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), security_scopes: SecurityScopes = SecurityScopes([])) -> Usuario:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Acceso no autorizado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_scopes = payload.get("scopes", [])
        user = db.query(Usuario).filter_by(email=email).first()
        if user is None:
            raise credentials_exception

        for scope in security_scopes.scopes:
            if scope not in token_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Acceso no autorizado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        return user
    except JWTError:
        raise credentials_exception

# Configura tus rutas de Swagger
from fastapi.openapi.models import OpenAPI, PathItem
from fastapi.openapi.utils import get_openapi_schema_from_url

@app.get("/docs", tags=["Documentación"])
async def read_docs():
    open_api = await get_openapi_schema_from_url("http://localhost:8000/docs.json")
    return OpenAPI(**open_api)

app.include_router(router, prefix="/api")

# Ejemplo de estructura de carpetas