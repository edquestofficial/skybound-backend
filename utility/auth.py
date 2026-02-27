from fastapi import HTTPException,Depends
from fastapi.security import HTTPBearer
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from core.role import Role
from core.config import Settings
from typing import List

settings = Settings()

bearer = HTTPBearer()
def role_required(allowed_roles: List[Role]):

    def verify_jwt(auth = Depends(bearer)):
        
        try:
            token = auth.credentials
            # PyJWT decode
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.algorithm]
            )
            
            user_role = int(payload.get("role"))
            device_id = payload.get("device_id")    
            if not user_role:
                raise HTTPException(
                    status_code=403,
                    detail="Role missing in token"
                )

            # Compare Enum values properly
            allowed = [r.value for r in allowed_roles]
            if user_role not in allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access denied."
                )

            return {"id":payload.get("id"), "role":user_role, "device_id": device_id}

        except ExpiredSignatureError:
            raise HTTPException(
                status_code=401,
                detail="Token has expired"
            )

        except InvalidTokenError:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    return verify_jwt
