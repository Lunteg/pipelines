class BaseTask:
    """Base Pipeline Task"""
    
    def load_env(self) -> None:
        load_dotenv()
        self.DB_NAME = os.getenv('DB_NAME')
        self.DB_USER = os.getenv('DB_USER')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD')
        self.DB_HOST = os.getenv('DB_HOST')

    def run(self):
        raise RuntimeError('Do not run BaseTask!')

    def short_description(self):
        pass
    
    def create_engine(self):
        self.load_env()
        url_object = URL.create(
            "postgresql",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            database=self.DB_NAME,
        )
        engine = create_engine(url_object)

        return engine

    def __str__(self):
        task_type = self.__class__.__name__
        return f'{task_type}: {self.short_description()}'


class CopyToFile(BaseTask):
    """Copy table data to CSV file"""

    def __init__(self, table, output_file):
        self.table = table
        self.output_file = output_file

    def short_description(self):
        return f'{self.table} -> {self.output_file}'

    def run(self):
        engine = self.create_engine()
        with engine.connect() as con:
            query = text("""SELECT * FROM %s""" % (self.table))
            pd.read_sql_query(query, con).to_csv(self.output_file, sep=',')
        
        print(f"Copy table `{self.table}` to file `{self.output_file}`")


import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy.engine import URL
from sqlalchemy import create_engine, text, select


class LoadFile(BaseTask):
    """Load file to table"""

    def __init__(self, table, input_file):
        self.table = table
        self.input_file = input_file

    def short_description(self):
        return f'{self.input_file} -> {self.table}'
        
    
    def read_df(self, input):
        return pd.read_csv(input)

    def run(self):
        con = self.create_engine()
        df = self.read_df(self.input_file)
        df.to_sql(con=con, name=self.table, if_exists='replace')
        
        print(f"Load file `{self.input_file}` to table `{self.table}`")


class RunSQL(BaseTask):
    """Run custom SQL query"""

    def __init__(self, sql_query, title=None):
        self.title = title
        self.sql_query = sql_query

    def short_description(self):
        return f'{self.title}'

    def run(self):
        engine = self.create_engine()
        with engine.connect() as con:
            con.execute(text(self.sql_query))
            con.commit()
        
        print(f"Run SQL ({self.title}):\n{self.sql_query}")



class CTAS(BaseTask):
    """SQL Create Table As Select"""

    def __init__(self, table, sql_query, title=None):
        self.table = table
        self.sql_query = sql_query
        self.title = title or table

    def short_description(self):
        return f'{self.title}'
    
    def create_fun_domain_of_url(self, con):
            query = text("drop function if exists domain_of_url;")
            con.execute(query)
            con.commit()
            
            query = text("""
                    create or replace function domain_of_url(url text)
                    returns text
                    language plpgsql
                    as
                    $$
                    declare
                    domain_of_url text;
                    begin
                    select (regexp_matches(url, '\/\/(.*?)\/', 'g'))[1]
                    into domain_of_url;
                    return domain_of_url;
                    end;
                    $$;
                    """)
            con.execute(query)
            con.commit()

    def run(self):
        engine = self.create_engine()
        with engine.connect() as con:
            self.create_fun_domain_of_url(con)
            
            sql0 = text("DROP TABLE IF EXISTS %s" % (self.table))
            con.execute(sql0)
            sql1 = text("CREATE TABLE %s AS %s" % (self.table, self.sql_query))
            con.execute(sql1)
            con.commit()
            con.close()
        
        print(f"Create table `{self.table}` as SELECT:\n{self.sql_query}")
