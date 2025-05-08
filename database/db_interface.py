from typing import Any, Iterable

from sqlalchemy import ColumnExpressionArgument, text, update, func, desc, asc, \
    select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, Query, joinedload, selectinload
from database.exceptions import CustomDBExceptions
from database.models import *
from loguru import logger


class BaseInterface:
    def __init__(self, db_url: str = None, session_ = None):
        """
        Класс-интерфейс для работы с БД. Держит сессию и предоставляет методы для работы с БД.

        :param db_url: Путь к БД формата: "database+driver://name:password@host/db_name"
        self.base базовый класс моделей с которыми будете работать.
        """
        if not session_:
            if not db_url:
                raise ValueError('db_url is required for Class DBInterface if session_ is None')
            self.engine = create_async_engine(db_url, pool_timeout=60, pool_size=900, max_overflow=100)
            self.async_ses = async_sessionmaker(bind=self.engine, class_=AsyncSession, expire_on_commit=False)
        else:
            self.async_ses = session_  
            
        self.base = Base
        

    async def initial(self):
        """
        Метод иницилизирует соеденение с БД.
        :return:
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.create_all)

    async def _drop_all(self):
        """
        Метод для удаления всех таблиц текущей БД.
        :return:
        """
        async with self.engine.begin() as conn:
            await conn.run_sync(self.base.metadata.drop_all)

    async def del_has_rows(self, rows_object):
        async with self.async_ses() as session:
            for rec in rows_object:
                await session.delete(rec)
            # await session.delete(records)
            await session.commit()


    async def delete_rows(self, model: Base, **filter_by):
        async with self.async_ses() as session:
            records = await session.execute(Query(model).filter_by(**filter_by))
            records = records.scalars().all()
            
            # Если результаты найдены пробуем удалить
            if not records:
                raise CustomDBExceptions(message=f'In table "{model.__tablename__}" Row is not defind with filter: {filter_by}')
            for record in records:
                await session.delete(record)
            # await session.delete(records)
            await session.commit()
            return True


    async def get_rows_count(
        self,
        model: Base,
        filters: list = None,
        **kwargs
    ):
        '''
        Метод принимает класс модели и параметры по которым фильтровать и отдает кол-во строк
        :param model: Класс модели
        :param kwargs: Поля и их значения
        :return:int
        '''
        async with self.async_ses() as session:
            query = select(func.count()).select_from(model).filter_by(**kwargs)
            if filters:
                for filter in filters:
                    query = query.filter(filter)
            return await session.scalar(query)

    
    async def get_row(
        self, 
        model: Base,
        order_by='id',
        order_direction="asc",
        filter: dict=None,
        load_relations: tuple[InstrumentedAttribute] | None=None,
        offset: int | None = None,
        limit: int | None = None,
        **kwargs
    ):
        """
        Метод принимает класс модели и имена полей со значениями,
        и если такая строка есть в БД - возвращает ее.
        :param to_many: Флаг для возврата одного или нескольких значений
        :param model: Класс модели
        :param kwargs: Поля и их значения
        :param load_relations: Список связанных сущностей для загрузки (например, ['auctiones', 'images'])
        :return:
        """
        async with self.async_ses() as session:
            # Строим основной запрос с фильтрацией по полям из kwargs
            query = select(model).filter_by(**kwargs)
            
            # Добавление фильтрации, если передано
            if filter:
                query = query.filter(filter['filter'])
            
            # Добавление сортировки
            if order_by:
                query = query.order_by(asc(order_by) if order_direction == 'asc' else desc(order_by))
            
            # Загрузка связанных данных, если указаны
            if load_relations:
                for relation in load_relations:
                    query = query.options(joinedload(relation))  # Используется joinedload для предварительной загрузки
            
            if offset:
                query=query.offset(offset)
            if limit:
                query=query.limit(limit)
            # Выполнение запроса
            result = await session.execute(query)
            
            return result.scalars().first()  # Возвращаем первый элемент или None, если не найдено
    
    
    async def get_rows(
        self,
        model: Base | tuple[InstrumentedAttribute],
        order_by='id',
        order_direction="asc",
        filter: ColumnExpressionArgument = None,
        load_relations: tuple[InstrumentedAttribute] | None = None,
        offset: int | None = None,
        limit: int | None = None,
        session: AsyncSession | None = None,
        **kwargs
    ):
        async with session if session else self.async_ses() as session:
            # Строим основной запрос с фильтрацией по полям из kwargs
            if isinstance(model, tuple):
                query = select(*model).filter_by(**kwargs)
            else:
                query = select(model).filter_by(**kwargs)
            
            # Добавление фильтрации, если передано
            if filter:
                query = query.filter(filter)
            
            # Добавление сортировки
            if order_by:
                query = query.order_by(asc(order_by) if order_direction == 'asc' else desc(order_by))
            
            # Загрузка связанных данных, если указаны
            if load_relations:
                for relation in load_relations:
                    query = query.options(selectinload(relation))
            
            if offset:
                query=query.offset(offset)
            if limit:
                query=query.limit(limit)
            # Выполнение запроса
            result = await session.execute(query)
            
            return result.scalars().all() if not isinstance(model, Iterable) else result.mappings().all()
    
        
    async def get_or_create_row(self, model: Any, filter_by=None, **kwargs):
        """
        Метод находит в БД запись, и возвращает ее. Если записи нет - создает и возвращает.
        :param model: Класс модели
        :param filter_by: Параметры для поиска записи. По умолчанию поиск идет по **kwargs
        :param kwargs: Поля и их значения
        :return:
        """
        if not filter_by:
            filter_by = kwargs

        async with self.async_ses() as session:
            # async with self.locks.get(model, asyncio.Lock()):
            row = await session.execute(Query(model).filter_by(**filter_by))
            res = row.scalar()
            if res is None:
                res = model(**kwargs)
                session.add(res)
                try:
                    await session.commit()
                except Exception as ex:
                    logger.warning(f'COMMIT FAILED: {model.__name__}, {kwargs=} {ex}')
                    # print(ex)
            return res


    async def update_rows(
        self, 
        model: Base, 
        filter_by: dict, 
        session: AsyncSession | None = None,
        **kwargs
    ):

        async with session if session else self.async_ses() as session:
            # async with self.locks.get(model, asyncio.Lock()):
            row = await session.execute(
                update(model)\
                .filter_by(**filter_by)\
                .values(**kwargs)\
                .returning(model)
            )

            try:
                await session.commit()
                return row.scalar_one()
            except Exception as ex:
                print(f'failed update {model.__tablename__}')
                raise ex
                       
            
    async def add_row(self, model: Base, **kwargs) -> Base:
        """
        Метод принимает класс модели и поля со значениями,
        и создает в таблице данной модели запись с переданными аргументами.
        :param model: Класс модели
        :param kwargs: Поля и их значения
        :return:
        """

        async with self.async_ses() as session:
            row = model(**kwargs)
            session.add(row)
            try:
                await session.commit()
                return row
            except Exception as ex:
                logger.warning(f'FAILED ADD ROW, {model.__name__}, {kwargs=}')
                raise ex
            
    async def get_row_num(
        self, 
        model_column: InstrumentedAttribute,
        model_column_value: Any,
        where_ = None, 
        desc_=False, 
    ) -> int | None:
        order_by_func = asc if not desc_ else desc
        
        subquery = select(
                model_column,  # Добавляем model_column в подзапрос
                func.row_number().over(order_by=order_by_func(model_column)).label("row_num")
            )
        
        if where_ is not None:
            subquery = subquery.where(where_)
            
        subquery = subquery.subquery()    
        stmt = select(subquery.c.row_num).where(subquery.c[model_column.name] == model_column_value)
        async with self.async_ses() as session:
            try:
                result = await session.execute(stmt)
                return result.scalar()
            except Exception as ex:
                logger.warning(f'FAILED ADD ROW, {model_column.__name__}')
                return
        
        
    async def truncate_table(self, model: Base):
        async with self.async_ses() as session:
            await session.execute(text(f"TRUNCATE TABLE {model.__tablename__} RESTART IDENTITY CASCADE"))
            await session.commit()


    async def add_rows(self, models: list[Base]) -> list[Base] | None:
        async with self.async_ses() as session:
            session.add_all(models)
            try:
                await session.flush()
                await session.commit()
                return models
            except Exception as ex:
                logger.warning(f"FAILED ADD ROWS")
                logger.exception(ex)
                return
