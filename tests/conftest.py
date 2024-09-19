import bcrypt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import config
from app.db.database import Base, get_session
from app.db.models import Company, Membership, User
from app.db.repo.company import CompanyRepo
from app.db.repo.user import UserRepo
from app.main import app
from app.services.auth import AuthService, get_current_user
from tests import payload


def assert_real_matches_expected(real: dict, expected: dict):
    for key, value in expected.items():
        assert real[key] == value


async def get_user_and_company_ids(
    session: AsyncSession,
    user_email: EmailStr | None = None,
    company_name: str | None = None,
) -> tuple[str | None, str | None]:
    user = None
    company = None

    if user_email:
        user = await UserRepo.get_user_by_email(user_email=user_email, session=session)

    if company_name:
        company = await CompanyRepo.get_company_by_name(
            company_name=company_name, session=session
        )

    user_id = str(user.id) if user else None
    company_id = str(company.id) if company else None

    return user_id, company_id


@pytest_asyncio.fixture(scope="session")
async def prepare_db():
    create_async_engine(
        config.postgres_test_url, echo=True, future=True, isolation_level="AUTOCOMMIT"
    )


@pytest.fixture(scope="function")
def engine():
    engine = create_async_engine(config.postgres_test_url)
    yield engine
    engine.sync_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(prepare_db, engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestingSessionLocal = async_sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine,
        class_=AsyncSession,
    )

    async with TestingSessionLocal() as test_session:
        yield test_session
        await test_session.flush()
        await test_session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def override_get_session(test_session):
    async def _override_get_session():
        yield test_session

    return _override_get_session


@pytest_asyncio.fixture(scope="function")
async def override_get_current_user(test_session):
    auth_service = AuthService()

    token = await auth_service.signin(payload.test_user_1_signin, session=test_session)

    async def _override_get_current_user():
        user = await auth_service.get_current_active_user(
            token=token, session=test_session
        )
        return user

    return _override_get_current_user


@pytest_asyncio.fixture(scope="function")
async def client(override_get_session, override_get_current_user):
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def fill_db_with_users(test_session: AsyncSession):
    users = [payload.test_user_1.model_dump(), payload.test_user_2.model_dump()]

    for user in users:
        hashed_password = bcrypt.hashpw(
            user["password"].encode("utf-8"), bcrypt.gensalt()
        )
        user["password_hash"] = hashed_password.decode("utf-8")
        user.pop("password")

        db_user = User(**user)
        test_session.add(db_user)

        await test_session.commit()


@pytest_asyncio.fixture(scope="function")
async def fill_db_with_companies(fill_db_with_users, test_session: AsyncSession):
    companies = [
        payload.test_company_1.model_dump(),
        payload.test_company_2.model_dump(),
    ]
    owner_emails = [payload.test_user_1.email, payload.test_user_2.email]

    for company, owner_email in zip(companies, owner_emails):
        company["owner_id"], _ = await get_user_and_company_ids(
            user_email=owner_email, session=test_session
        )

        db_company = Company(**company)
        test_session.add(db_company)

        await test_session.commit()


@pytest_asyncio.fixture(scope="function")
async def fill_db_with_memberships(
    request, fill_db_with_companies, test_session: AsyncSession
):
    status = request.param
    user_emails = [payload.test_user_2.email, payload.test_user_1.email]
    company_names = [payload.test_company_1.name, payload.test_company_2.name]

    for user_email, company_name in zip(user_emails, company_names):
        user_id, company_id = await get_user_and_company_ids(
            user_email=user_email, company_name=company_name, session=test_session
        )
        membership = Membership(company_id=company_id, user_id=user_id, status=status)
        test_session.add(membership)

    await test_session.commit()
