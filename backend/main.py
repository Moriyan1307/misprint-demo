
import os
import asyncpg
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
import logging
import asyncio


#  for the sake of the demo, i am exposing the credentials in the docker-compose.yml file
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "misprint_db")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# real-time Update Mechanism (SSE)
# this is the point where in future we can use redis pub/sub to broadcast the updates to the frontend
sse_connections = []

# database connection pool
db_pool = None

async def get_db_pool():
    if db_pool is None:
        raise HTTPException(status_code=503, detail="Database connection is not available.")
    return db_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool
    logger.info("Application starting up...")
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
        logger.info("Database connection pool created.")
        async with db_pool.acquire() as connection:
            await setup_database(connection)
        yield
    finally:
        if db_pool:
            await db_pool.close()
            logger.info("Database connection pool closed.")
        logger.info("Application shutting down.")

async def setup_database(connection):
    logger.info("Setting up database schema...")
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT,
            image_url TEXT, quantity INTEGER NOT NULL CHECK (quantity >= 0)
        );
    """)
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY, item_id TEXT NOT NULL, timestamp TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    await connection.execute("""
        INSERT INTO items (id, name, description, image_url, quantity)
        VALUES ('charizard-1st-ed', '1st Edition Charizard', 'The holy grail of Pokémon cards. PSA 10 Gem Mint.', 'https://placehold.co/400x600/2D3748/E2E8F0?text=Card', 1)
        ON CONFLICT (id) DO NOTHING;
    """)
    logger.info("Database setup complete.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

class Item(BaseModel):
    id: str; name: str; description: str; image_url: str; quantity: int

class OrderResponse(BaseModel):
    message: str; item_id: str

# this function is used to broadcast the update to the frontend
async def broadcast_update(item_id: str):
    if not sse_connections: return
    logger.info(f"Broadcasting update for item '{item_id}' to {len(sse_connections)} clients.")
    async with db_pool.acquire() as connection:
        row = await connection.fetchrow("SELECT * FROM items WHERE id = $1", item_id)
        if row:
            item_data = Item(**dict(row)).model_dump_json()
            message = f"data: {item_data}\n\n"
            for queue in sse_connections:
                await queue.put(message)

@app.get("/events")
async def sse_endpoint(request: Request):
    # this is the endpoint that the frontend will connect to for live updates
    from starlette.responses import StreamingResponse
    queue = asyncio.Queue()
    sse_connections.append(queue)
    logger.info(f"New frontend client connected. Total clients: {len(sse_connections)}")
    async def event_stream():
        try:
            while True:
                message = await queue.get()
                yield message
        except asyncio.CancelledError:
            logger.info("Client disconnected.")
        finally:
            sse_connections.remove(queue)
            logger.info(f"Client connection removed. Total clients: {len(sse_connections)}")
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.get("/status/{item_id}", response_model=Item)
async def get_item_status(item_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    async with pool.acquire() as connection:
        row = await connection.fetchrow("SELECT * FROM items WHERE id = $1", item_id)
        if not row: raise HTTPException(status_code=404, detail="Item not found")
        return Item(**dict(row))


@app.post("/buy/{item_id}", response_model=OrderResponse)
async def buy_item(item_id: str, pool: asyncpg.Pool = Depends(get_db_pool)):
    purchase_succeeded = False
    async with pool.acquire() as connection:
        # the transaction ensures atomicity. It either all succeeds or all fails.
        async with connection.transaction():
            try:
                item = await connection.fetchrow("SELECT quantity FROM items WHERE id = $1 FOR UPDATE", item_id)
                if not item:
                    raise HTTPException(status_code=404, detail="Item not found")

                if item['quantity'] > 0:
                    await connection.execute("UPDATE items SET quantity = quantity - 1 WHERE id = $1", item_id)
                    await connection.execute("INSERT INTO orders (item_id) VALUES ($1)", item_id)
                    # Set a flag that the purchase was successful inside the transaction
                    purchase_succeeded = True
                else:
                    # If quantity is 0, we raise an error which rolls back the transaction
                    raise HTTPException(status_code=409, detail="Item is sold out")
            except asyncpg.exceptions.LockNotAvailableError:
                raise HTTPException(status_code=503, detail="Server is busy, please try again.")
    
    
    # THE FIX IS HERE
    # we only broadcast the update AFTER the transaction is successfully committed and the lock is released.
    if purchase_succeeded:
        await broadcast_update(item_id)
        return OrderResponse(message="Purchase successful!", item_id=item_id)
    
    raise HTTPException(status_code=500, detail="An unexpected error occurred during purchase.")


@app.post("/reset")
async def reset_demo(pool: asyncpg.Pool = Depends(get_db_pool)):
    item_id = 'charizard-1st-ed'
    async with pool.acquire() as connection:
        async with connection.transaction():
            await connection.execute("UPDATE items SET quantity = 1 WHERE id = $1", item_id)
            await connection.execute("TRUNCATE TABLE orders")
    
    await broadcast_update(item_id)
    return {"message": "Demo has been reset successfully."}
