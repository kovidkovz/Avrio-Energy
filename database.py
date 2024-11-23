import asyncpg
import config
import logging

# Global variable for the asyncpg connection pool
pool = None

# Function to create and return the asyncpg connection pool
async def create_pool():
    global pool
    if pool is None:  # Check if the pool is already created
        pool = await asyncpg.create_pool(
            user= config.PG_USER,
            password= config.PG_PASSWORD,
            host= config.PG_HOST,
            port= config.PG_PORT,
            database= config.PG_NAME,
            min_size= 16,
            max_size= 32,
            statement_cache_size= 0
        )
        logging.info("PostgreSQL connection pool initialized")

async def get_connection():
    try:
        await create_pool()  # Ensure the pool is created
        conn = await pool.acquire()
        
        # Check if the connection is alive
        try:
            await conn.execute('SELECT 1')
        except Exception as e:
            logging.warning(f"Connection lost, acquiring a new connection: {e}")
            await pool.release(conn)  # Release the old connection
            conn = await pool.acquire()  # Acquire a new connection

        return conn
    except Exception as e:
        logging.error(f"Error getting connection: {e}")
        return None


async def execute_query(query: str, params = (), flag="get"):
    conn = await get_connection()
    if conn is None:
        logging.error("Failed to get a connection from the pool.")
        return None
    
    try:
        if flag.lower() == "get":
            # For SELECT queries, fetch results
            data = []
            result = await conn.fetch(query, *params)  # Use *params for positional parameters
            if result:
                data = [dict(row) for row in result]  # Use dict() to convert RowProxy objects to dictionaries
            return data

        elif flag.lower() in ("insert", "update", "delete"):
            
            result = await conn.fetchrow(query, *params)
            if result:
                return dict(result)  # Return the inserted row (or ID)
            return None  # No result means insertion failed or no RETURNING clause

        else:
            raise ValueError("Invalid flag provided. Use 'get', 'insert', 'update', or 'delete'.")

    except ValueError as ve:
        logging.error(f"Error executing query: {ve}")
        return None
    
    except Exception as e:
        logging.error(f"Error executing query: {e}")
        return None
    
    finally:
        await pool.release(conn)
