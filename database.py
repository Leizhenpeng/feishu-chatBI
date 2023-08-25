import os
from sqlalchemy import create_engine
from sqlalchemy import DDL
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event
from sqlalchemy.sql import text
import psycopg2
from sqlalchemy import create_engine, MetaData, Table, text
import os

postgres_user=os.getenv('POSTGRES_USER')
postgres_password=os.getenv('POSTGRES_PASSWORD')
postgres_host=os.getenv('POSTGRES_HOST')
postgres_port=os.getenv('POSTGRES_PORT')
postgres_database=os.getenv('POSTGRES_DATABASE')

db_connection_string = ('postgresql://%s:%s@%s:%s/%s' %
                             (postgres_user, postgres_password,
                              postgres_host, postgres_port,
                              postgres_database))

engine = create_engine(db_connection_string, connect_args={'sslmode': 'prefer'},pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
event.listen(Base.metadata, 'before_create', DDL("CREATE SCHEMA IF NOT EXISTS shopee"))
print(db_connection_string)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_all_schemas():
    schema_list=[]
    engine = create_engine(db_connection_string)
    schemas= engine.connect().execute(text("SELECT schema_name FROM information_schema.schemata"))
    for row in schemas:
        schema_list.append(row[0])
    # print(schema_list)
    return schema_list

def get_all_tables(schema):
    metadata = MetaData()
    # 使用元数据对象反射特定schema中的表
    metadata.reflect(bind=engine, schema=schema)
    table_dict={}
    # 打印所有反射的表名
    for table in metadata.tables.values():
        column_metas = []
        for column in table.c:
            # print(f"Table {table.name}, Column {column.name}, Type {column.type}")
            column_metas.append(f"\nColumn {column.name}, Type {column.type}")
        table_dict[table.name] = column_metas
    return table_dict

def init_metadata(schemas):
    print("initializing schemas")
    metadata_dict={}
    for schema in schemas:
        metadata_dict[schema] = get_all_tables(schema)
    print("initialized")
    return metadata_dict


all_schemas=get_all_schemas()
schemas_should_ignore= [
    'public','pg_catalog','pg_toast_temp_1','pg_temp_1','pg_toast'
]
used_schemas = list(set(all_schemas) - set(schemas_should_ignore))
metadata_dict = init_metadata(used_schemas)
schema_prompt = "All schemas in the database: {" + ",".join(all_schemas) + "}"
schema_prompt += f"\nExcept for the system schemas, we use these schemas: {used_schemas}\n"

metadata_prompt = ""
for schema in metadata_dict.keys():
    table_dict = metadata_dict[schema]
    for key in table_dict.keys():
        metadata_prompt+= f"\n\nTable {schema}.{key}: {''.join(table_dict[key])}"


