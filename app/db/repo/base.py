from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, Type, TypeVar
from uuid import UUID

from fastapi import Depends
from sqlalchemy import insert, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.core.logger import logger
from app.db.database import get_session
from app.db.models import BaseId
from app.services.exceptions import InvalidPaginationParameterError

T = TypeVar("T", bound="BaseId")


class BaseRepo(ABC, Generic[T]):
    """Represents a base repository pattern to perform CRUD on models."""

    @classmethod
    @abstractmethod
    def get_model(cls) -> Type[T]:
        """Get the model to perform CRUD on."""
        pass

    @staticmethod
    async def check_pagination_parameters(
        limit: int | None,
        offset: int,
    ) -> None:
        if limit is not None and limit < 0:
            raise InvalidPaginationParameterError("Limit cannot be negative")
        if offset < 0:
            raise InvalidPaginationParameterError("Offset cannot be negative")

    @classmethod
    async def get_all(
        cls,
        limit: int | None = 10,
        offset: int = 0,
        session: AsyncSession = Depends(get_session),
    ) -> list[T]:
        """Get a list of entities for one model.

        Args:
            limit (int | None, optional):
                How many entities to get. Defaults to 10.
                If None, retrieve all records.
            offset (int, optional):
                Where to start getting entities.
                Defaults to 0.
            session (AsyncSession, optional):
                The database session used for querying entities.
                Defaults to Depends(get_session).

        Returns:
            list[T]: The list of retrieved entities.
        """
        await cls.check_pagination_parameters(limit=limit, offset=offset)

        model: Type[T] = cls.get_model()
        query = select(model).offset(offset)

        if limit is not None:
            query = query.limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def get_all_by_fields(
        cls,
        fields: list[InstrumentedAttribute],
        values: Sequence[object],
        limit: int | None = 10,
        offset: int = 0,
        or_flag: bool = False,
        session: AsyncSession = Depends(get_session),
    ) -> list[T]:
        """Get a list of entities of a model via one or more of its fields.

        Args:
            fields (list[InstrumentedAttribute]): The fields to check.
            value (Sequence[object]): The values to check.
            limit (int | None, optional):
                How many entities to get. Defaults to 10.
                If None, retrieve all records.
            offset (int, optional):
                Where to start getting entities.
                Defaults to 0.
            or_flag (bool, optional):
                Whether or not the conditions should be joined by OR.
                Defaults to False (the conditions joined by AND).
            session (AsyncSession, optional):
                The database session used for querying entities.
                Defaults to Depends(get_session).

        Returns:
            list[T]: The list of retrieved entities.
        """
        await cls.check_pagination_parameters(limit=limit, offset=offset)
        model: Type[T] = cls.get_model()

        where_clause = [cond == val for cond, val in zip(fields, values)]

        if or_flag:
            query = select(model).where(or_(*where_clause)).offset(offset)
        else:
            query = select(model).where(*where_clause).offset(offset)

        if limit is not None:
            query = query.limit(limit)

        result = await session.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(
        cls, record_id: UUID, session: AsyncSession = Depends(get_session)
    ) -> T | None:
        """Get one entity of a model via its ID.

        Args:
            record_id (UUID): The ID to check.
            session (AsyncSession, optional):
                The database session used for querying entities.
                Defaults to Depends(get_session).

        Returns:
            T | None: The retrieved entity, if any.
        """
        model: Type[T] = cls.get_model()
        query = select(model).where(model.id == record_id)
        result = await session.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_by_fields(
        cls,
        fields: list[InstrumentedAttribute],
        values: Sequence[object],
        session: AsyncSession = Depends(get_session),
    ) -> T | None:
        """Get one entity of a model via one or more of its fields.

        Args:
            fields (list[InstrumentedAttribute]): The fields to check.
            values (Sequence[object]): The values to check.
            session (AsyncSession, optional):
                The database session used for querying entities.
                Defaults to Depends(get_session).

        Returns:
            T | None: The retrieved entity, if any.
        """
        model: Type[T] = cls.get_model()

        where_clause = [cond == val for cond, val in zip(fields, values)]
        query = select(model).where(*where_clause)

        result = await session.execute(query)
        entity: T | None = result.scalars().first()
        return entity

    @staticmethod
    async def create(entity: T, session: AsyncSession = Depends(get_session)) -> T:
        """Create a new entity of a model

        Args:
            entity (T): The entity to create.
            session (AsyncSession, optional):
                The database session used for querying entities.
                Defaults to Depends(get_session).

        Returns:
            object: The newly created entity.
        """
        logger.info(f"Received a request to create a new {entity.__class__.__name__}")
        session.add(entity)
        await session.commit()
        await session.refresh(entity)
        logger.info(f"New {entity.__class__.__name__} created successfully")
        return entity

    @classmethod
    async def bulk_create(
        cls,
        entities: list[dict[str, Any]],
        session: AsyncSession = Depends(get_session),
    ) -> list[T]:
        """Bulk create new entities of a model

        Args:
            entities (list[dict[str, any]]): The info of entities to create.
            session (AsyncSession, optional):
                The database session used for querying entities.
                Defaults to Depends(get_session).

        Returns:
            list[T]: The newly created entities.
        """
        model: Type[T] = cls.get_model()
        logger.info(
            f"Received a request to bulk create {len(entities)} "
            "entities of {model.__name__}"
        )

        result = await session.execute(insert(model).values(entities).returning(model))
        await session.commit()

        created_entities = list(result.scalars().all())
        logger.info(
            f"{len(created_entities)} {model.__name__} "
            "entities bulk created successfully"
        )
        return created_entities

    @staticmethod
    async def update(
        entity: T,
        update_data: dict,
        session: AsyncSession = Depends(get_session),
    ) -> T:
        """Update an existing entity of a model.

        Args:
            existing_entity (object): The entity to update.
            update_data (dict): The data with which to perform the update.
            session (AsyncSession, optional):
                The database session used for querying entities.
                Defaults to Depends(get_session).

        Returns:
            object: The newly updated entity.
        """
        logger.info(
            f"Received request to update {entity.__class__.__name__} "
            f"with ID {entity.id}"
        )
        for attr, value in update_data.items():
            if value is not None:
                setattr(entity, attr, value)
        await session.commit()
        await session.refresh(entity)
        logger.info(
            f"{entity.__class__.__name__} with ID {entity.id} updated successfully"
        )
        return entity

    @staticmethod
    async def delete(entity: T, session: AsyncSession = Depends(get_session)) -> None:
        """Delete an existing entity of a model.

        Args:
            entity (object): The entity to delete.
            session (AsyncSession, optional):
                The database session used for querying entities.
                Defaults to Depends(get_session).
        """
        logger.info(
            f"Received request to delete {entity.__class__.__name__} "
            f"with ID {entity.id}"
        )
        await session.delete(entity)
        await session.commit()
        logger.info(
            f"{entity.__class__.__name__} with ID {entity.id} deleted successfully"
        )
