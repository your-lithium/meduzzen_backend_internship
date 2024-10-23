import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import bcrypt
import jwt
import requests
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError
from jwt.algorithms import RSAAlgorithm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.core.security import auth_scheme
from app.db.database import get_session
from app.db.models import User
from app.db.repo.user import UserRepo
from app.schemas.user_schemas import SignInRequest, SignUpRequest
from app.services.exceptions import (
    InactiveUserError,
    IncorrectPasswordError,
    UnauthorizedError,
    UserNotFoundError,
)


def get_auth_service():
    return AuthService()


async def get_current_user(
    token: HTTPAuthorizationCredentials = Depends(auth_scheme),
    auth_service=Depends(get_auth_service),
    session: AsyncSession = Depends(get_session),
) -> User:
    current_user: User = await auth_service.get_current_active_user(
        token=token.credentials,
        session=session,
    )
    return current_user


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: EmailStr | None = None


class AuthService:
    """Represents a service for handling authentication requests."""

    def create_access_token(
        self,
        data: dict,
        secret_key: str,
        algorithm: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a JWT access token.

        Args:
            data (dict): The data that the token should contain.
            secret_key (str): The secret key for encoding.
            algorithm (str): The encoding algorithm.
            expires_delta (timedelta | None, optional):
                How fast the token should expire. Defaults to None.

        Returns:
            str: The JWT access token.
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(ZoneInfo("Europe/Kyiv")) + expires_delta
        else:
            expire = datetime.now(ZoneInfo("Europe/Kyiv")) + timedelta(minutes=15)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)

        return encoded_jwt

    async def get_current_user(
        self,
        token: str,
        oauth2_secret_key: str,
        oauth2_algorithm: str,
        auth0_domain: str,
        auth0_algorithms: list[str],
        auth0_audience: str,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        """Decode a token to authenticate a User.

        Args:
            token (str): The JWT token to decode.
            oauth2_secret_key (str): The OAuth2 secret key for decoding.
            oauth2_algorithm (str): The OAuth2 algorithm for decoding.
            auth0_domain (str): The Auth0 domain for decoding.
            auth0_algorithms (list[str]): The Auth0 algorithms for decoding.
            auth0_audience (str): The Auth0 audience for decoding.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Raises:
            UserNotFoundError:
                If the user OAuth2 token hasn't returned an existing user.

        Returns:
            User: The authenticated user.
        """
        try:
            token_data = self.verify_email_password_token(
                secret_key=oauth2_secret_key, algorithm=oauth2_algorithm, token=token
            )
        except UnauthorizedError:
            token_data = self.verify_auth0_token(
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

    async def get_current_active_user(
        self,
        token: str,
        oauth2_secret_key: str = config.oauth2_secret_key,
        oauth2_algorithm: str = config.oauth2_algorithm,
        auth0_domain: str = config.auth0_domain,
        auth0_algorithms: list[str] = config.auth0_algorithms,
        auth0_audience: str = config.auth0_audience,
        session: AsyncSession = Depends(get_session),
    ) -> User:
        """Decode a token to authenticate an active User.

        Args:
            token (str): The JWT token to decode.
            oauth2_secret_key (str, optional):
                The OAuth2 secret key for decoding.
                Defaults to config.oauth2_secret_key.
            oauth2_algorithm (str, optional):
                The OAuth2 algorithm for decoding.
                Defaults to config.oauth2_algorithm.
            auth0_domain (str, optional):
                The Auth0 domain for decoding.
                Defaults to config.auth0_domain.
            auth0_algorithms (list[str], optional):
                The Auth0 algorithms for decoding.
                Defaults to config.auth0_algorithms.
            auth0_audience (str, optional):
                The Auth0 audience for decoding.
                Defaults to config.auth0_audience.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Raises:
            InactiveUserError: If the user found is inactive.

        Returns:
            User: The authenticated user.
        """
        current_user: User = await self.get_current_user(
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

    def verify_email_password_token(
        self,
        token: str,
        secret_key: str,
        algorithm: str,
    ) -> TokenData:
        """Decode an email-password OAuth2 JWT token.

        Args:
            token (str): The JWT token to decode.
            secret_key (str): The OAuth2 secret key for decoding.
            algorithm (str): The OAuth2 algorithm for decoding.

        Raises:
            UnauthorizedError:
                If the token contains no email, has expired, is invalid
                or has failed to decode.

        Returns:
            TokenData: The decoded token data.
        """
        try:
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            email: str | None = payload.get("sub")
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

    def verify_auth0_token(
        self,
        token: str,
        domain: str,
        algorithms: list[str],
        audience: str,
    ) -> TokenData:
        """Decode a third-party Auth0 JWT token.

        Args:
            token (str): The JWT token to decode.
            domain (str): The Auth0 domain for decoding.
            algorithms (list[str]): The Auth0 algorithms for decoding.
            audience (str): The Auth0 audience for decoding.

        Raises:
            UnauthorizedError:
                If the token has expired, has failed to decode, has incorrect
                claims or no matching decoding key.

        Returns:
            TokenData: The decoded token data.
        """
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
                raise UnauthorizedError(f"Unable to parse token: {e}")
        else:
            raise UnauthorizedError("Unable to find appropriate key")

    async def signin(
        self,
        request: SignInRequest,
        session: AsyncSession = Depends(get_session),
    ) -> str:
        """Handle a sign in request to give out a token.

        Args:
            request (SignInRequest): The request to handle.
            session (AsyncSession):
                The database session used for querying users.
                Defaults to the session obtained through get_session.

        Raises:
            UserNotFoundError: If there's no user found with the given email.
            IncorrectPasswordError: If the password provided doesn't match.

        Returns:
            str: The JWT token for OAuth2 email-password authentication.
        """
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
        access_token = self.create_access_token(
            data={"sub": user.email},
            secret_key=config.oauth2_secret_key,
            algorithm=config.oauth2_algorithm,
            expires_delta=access_token_expires,
        )

        return access_token
