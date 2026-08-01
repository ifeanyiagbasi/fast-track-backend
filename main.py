import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from auth import create_access_token, get_current_user, hash_password, verify_password
from database import Base, engine, get_db
from models import ProductModel, User
from schemas import (
    AIDescriptionRequest,
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    Token,
    UserCreate,
    UserResponse,
)


# 1. Lifespan event: Automatically create database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Production-Grade API", lifespan=lifespan)

# 2. Add CORS Middleware (allowing both localhost and 127.0.0.1)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 🔐 AUTHENTICATION ENDPOINTS
# ==========================================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    # Hash password and create user
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@app.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve user by email (OAuth2Form uses username field for email)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    # Validate password
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Issue JWT Token
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}


# ==========================================
# 📦 INVENTORY ENDPOINTS
# ==========================================

# PUBLIC: Anyone can fetch the product list
@app.get("/products", response_model=list[ProductResponse])
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductModel))
    products = result.scalars().all()
    return products


# PROTECTED: Requires valid JWT token header
@app.post("/products", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_product = ProductModel(
        productname=product.productname,
        price=product.price,
        in_stock=product.in_stock,
    )
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


# PROTECTED: Requires valid JWT token header
@app.patch("/products/{id}", response_model=ProductResponse)
async def update_product(
    id: int,
    update_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ProductModel).where(ProductModel.id == id))
    product = result.scalars().first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if update_data.productname is not None:
        product.productname = update_data.productname
    if update_data.price is not None:
        product.price = update_data.price
    if update_data.in_stock is not None:
        product.in_stock = update_data.in_stock

    await db.commit()
    await db.refresh(product)
    return product


# PROTECTED: Requires valid JWT token header
@app.delete("/products/{id}")
async def delete_product(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ProductModel).where(ProductModel.id == id))
    product = result.scalars().first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    await db.delete(product)
    await db.commit()
    return {"status": "Success", "message": f"Product {id} deleted successfully"}


# ==========================================
# 🤖 AI GENERATION
# ==========================================

async def mock_llm_stream(productname: str, price: float):
    prompt_response = (
        f"Introducing the all-new {productname}! "
        f"Priced at just ${price:.2f}, this premium product delivers exceptional performance, "
        f"unmatched quality, and incredible value. Upgrade your setup today!"
    )
    for word in prompt_response.split(" "):
        yield f"{word} "
        await asyncio.sleep(0.08)


@app.post("/ai/generate-description")
async def generate_ai_description(request: AIDescriptionRequest):
    return StreamingResponse(
        mock_llm_stream(request.productname, request.price),
        media_type="text/plain",
    )