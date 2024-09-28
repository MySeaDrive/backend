from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ..models import User
from supabase import create_client, Client
from ..models import User
from sqlmodel import Session, select
from ..helpers.db import engine
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv('./secrets/.env')

# Supabase setup
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
    
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Decode token
        response = supabase.auth.get_user(token)
        if response is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    
        with Session(engine) as session:
            query = select(User).where(User.id == response.user.id)
            user = session.exec(query).first()
        
        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")