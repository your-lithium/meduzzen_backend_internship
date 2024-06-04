import bcrypt
import jwt
import requests
import secrets
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from jwt import ExpiredSignatureError, InvalidTokenError, DecodeError
from jwt.algorithms import RSAAlgorithm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone

from app.db.user_model import User
from app.schemas.user_schemas import SignInRequest, SignUpRequest
from app.db.repo.user import UserRepo
from app.services.exceptions import (
    UserNotFoundError,
    IncorrectPasswordError,
    UnauthorizedError,
    InactiveUserError,
)
from app.db.database import get_session
from app.core.config import config


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: EmailStr | None = None


class AuthService:
    """Represents a service for handling authentication requests."""

    @staticmethod
    def create_access_token(
        data: dict,
        secret_key: str,
        algorithm: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)

        return encoded_jwt

    @staticmethod
    async def get_current_user(
        token: str,
        oauth2_secret_key: str,
        oauth2_algorithm: str,
        auth0_domain: str,
        auth0_algorithms: list[str],
        auth0_audience: str,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        try:
            token_data = AuthService.verify_email_password_token(
                secret_key=oauth2_secret_key, algorithm=oauth2_algorithm, token=token
            )
        except UnauthorizedError:
            token_data = AuthService.verify_auth0_token(
                token=token,
                domain=auth0_domain,
                algorithms=auth0_algorithms,
                audience=auth0_audience,
            )
            auth_method = "auth0"

        user = await UserRepo.get_user_by_email(
            user_email=token_data.email, session=session
        )
        if user is None:
            if auth_method != "auth0":
                raise UserNotFoundError(identifier=token_data.email)
            else:
                sign_up_request = SignUpRequest(
                    name="John Doe",
                    username=token_data.email,
                    email=token_data.email,
                    password=secrets.token_hex(12),
                )
                user = await UserRepo.create_user(user=sign_up_request, session=session)

        return user

    @staticmethod
    async def get_current_active_user(
        token: str,
        oauth2_secret_key: str = config.oauth2_secret_key,
        oauth2_algorithm: str = config.oauth2_algorithm,
        auth0_domain: str = config.auth0_domain,
        auth0_algorithms: list[str] = config.auth0_algorithms,
        auth0_audience: str = config.auth0_audience,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        current_user: User = await AuthService.get_current_user(
            token=token,
            oauth2_secret_key=oauth2_secret_key,
            oauth2_algorithm=oauth2_algorithm,
            auth0_domain=auth0_domain,
            auth0_algorithms=auth0_algorithms,
            auth0_audience=auth0_audience,
            session=session,
        )

        if current_user.disabled:
            raise InactiveUserError

        return current_user

    @staticmethod
    def verify_email_password_token(
        secret_key: str,
        algorithm: str,
        token: str,
    ) -> TokenData:
        try:
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            email: str = payload.get("sub")
            if email is None:
                raise UnauthorizedError
            token_data = TokenData(email=email)
            return token_data
        except ExpiredSignatureError:
            raise UnauthorizedError("Token has expired")
        except DecodeError:
            raise UnauthorizedError("Error decoding token")
        except InvalidTokenError:
            raise UnauthorizedError("Invalid token")

    @staticmethod
    def verify_auth0_token(
        token: str,
        domain: str,
        algorithms: list[str],
        audience: str,
    ) -> TokenData:
        json_url = f"https://{domain}/.well-known/jwks.json"
        response = requests.get(json_url)
        jwks = response.json()

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == jwt.get_unverified_header(token)["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }

        if rsa_key:
            public_key = RSAAlgorithm.from_jwk(rsa_key)
            try:
                decoded = jwt.decode(
                    token,
                    public_key,
                    algorithms=algorithms,
                    audience=audience,
                    issuer=f"https://{domain}/",
                )

                email = decoded.get(audience + "/email", "Email not found in token")
                token_data = TokenData(email=email)
                return token_data
            except jwt.ExpiredSignatureError:
                raise UnauthorizedError("Token has expired")
            except jwt.JWTClaimsError:
                raise UnauthorizedError(
                    "Incorrect claims, please check the audience and issuer"
                )
            except Exception as e:
                return UnauthorizedError(f"Unable to parse token: {e}")
        else:
            return UnauthorizedError("Unable to find appropriate key")

    @staticmethod
    async def signin(
        request: SignInRequest,
        session: AsyncSession = Depends(get_session),
    ) -> str:

        user = await UserRepo.get_user_by_email(
            user_email=request.email, session=session
        )
        if user is None:
            raise UserNotFoundError(identifier=request.email)

        if not bcrypt.checkpw(
            request.password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            raise IncorrectPasswordError

        access_token_expires = timedelta(days=config.oauth2_access_token_expire_days)
        access_token = AuthService.create_access_token(
            data={"sub": user.email},
            secret_key=config.oauth2_secret_key,
            algorithm=config.oauth2_algorithm,
            expires_delta=access_token_expires,
        )

        return access_token
