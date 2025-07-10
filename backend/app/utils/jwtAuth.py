from typing import Any, Dict, Optional
from fastapi import Request, status, Depends
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .accessUtils import decode_token
from ..services.usersServices import UsersServices
from ..db.base import get_db

class AccessTokenBearer(HTTPBearer):
    def __init__(self, auto_error=True):
        # Initialize the HTTPBearer with optional auto error handling
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request, db=Depends(get_db)) -> Optional[Dict]:
        # Extract credentials (token) from the Authorization header
        creds = await super().__call__(request)

        # Extract the token string from credentials
        token = creds.credentials

        # Decode the JWT token to get payload data
        token_data = decode_token(token)

        # Verify the token payload and retrieve the user from DB
        user = self.verify_token_data(token_data, db)

        return user

    def verify_token_data(self, token_data: Dict, db: Any) -> Optional[Dict]:
        # Use the UsersServices to get user info by id from token data
        user_service = UsersServices(db)
        user = user_service.get_user_by_id(token_data.get('id'))
        return user
