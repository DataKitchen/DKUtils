import pandas as pd
from sqlalchemy import create_engine

from dkutils.util import FileNameGenerator


class DataFrameWrapper:
    """
    Class that facilitates running a query in a database via a Pandas Dataframe and then writing the data to files.
     A number of formats are supported including png, html and text files.
    """

    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.file_name_generator = FileNameGenerator()

    @classmethod
    def snowflake(
        cls, username: str, password: str, snowflake_account: str, database: str, warehouse: str
    ):
        """
        Create a DataFrame with a connection to a Snowflake database
        Parameters
        ----------
        username: str
            Snowflake username
        password: str
            Snowflake password
        snowflake_account: str
            Snowflake account name
        database: str
            Snowflake database name
        warehouse
            Snowflake warehouse name

        Returns
        -------
        DataFrameWrapper
            a DataFramewrapper that can be used to execute queries against a snowflake database

        """
        connection_string = f"snowflake://{username}:{password}@{snowflake_account}/{database}?warehouse={warehouse}"
        return DataFrameWrapper(connection_string)

    @classmethod
    def postgresql(
        cls, username: str, password: str, hostname: str, database: str, port: int = 5432
    ):
        """
       Create a DataFrame with a connection to a postgreSQL database
       Parameters
       ----------
       username: str
           PostgreSQL username
       password: str
           PostgreSQL password
       hostname: str
           PostgreSQL host name
       database: str
           PostgreSQL database name
       port: int, optional
           PostgreSQL port

       Returns
       -------
       DataFrameWrapper
           a DataFramewrapper that can be used to execute queries against a PostgreSQL database

       """
        connection_string = f"postgresql://{username}:{password}@{hostname}:{port}/{database}"
        return DataFrameWrapper(connection_string)

    @classmethod
    def mssql(cls, username: str, password: str, hostname: str, database: str, port: int = 1433):
        """
        Create a DataFrame with a connection to a mssql database
        Parameters
        ----------
        username: str
          mssql username
        password: str
          mssql password
        hostname: str
          mssql host name
        database: str
          mssql database name
        port: int, optional
          mssql port

        Returns
        -------
        DataFrameWrapper
          a DataFramewrapper that can be used to execute queries against a PostgreSQL database

        """
        connection_string = f"mssql+pymssql://{username}:{password}@{hostname}:{port}/{database}"
        return DataFrameWrapper(connection_string)

    def create_report(self, query: str, query_type: str, filename=None, additional_parms=None):
        """
        This method will execute the given query and then write out the results as an html, png or txt file depending on
        the given query_type. The file will named with the given filename. If the the filename parameter then the file
        will be named file_ddd.ext. Where ddd will be a three digit number with two leading zeros that is incremented
        for each time this method is called with a particular file type. The extension will be determined by the
        query_type as follows:
            html = html
            plot = png
            text = txt
        Parameters
        ----------
        query: str
            A string containing the query to be executed
        query_type: str
            A string containing the type of file to be created. Must be either html, ping or text
        filename: str, optional
            The filename to be assigned when saving the query results
        additional_parms: dict, optional
            A dictionary containing additional the will be passed to the either to to_html, plot or to_string
            methods of the dataframe

        Returns
        -------
        int
            A integer containing the number of rows returned by the query
        str
            A string containing the name of the file created
        """

        def handle_html(file_name):
            if not file_name:
                file_name = self.file_name_generator.getFileName('html')
            if additional_parms:
                df.to_html(file_name, **additional_parms)
            else:
                df.to_html(file_name)
            return file_name

        def handle_plot(file_name):
            if not file_name:
                file_name = self.file_name_generator.getFileName('png')
            if additional_parms:
                fig = df.plot(**additional_parms).get_figure()
            else:
                fig = df.plot().get_figure()
            fig.savefig(file_name)
            return file_name

        def handle_text(file_name):
            if not file_name:
                file_name = self.file_name_generator.getFileName('txt')
            if additional_parms:
                df.to_string(file_name, **additional_parms)
            else:
                df.to_string(file_name)
            return file_name

        handlers = {'html': handle_html, 'plot': handle_plot, 'text': handle_text}
        if query_type not in handlers.keys():
            raise TypeError(f"query_type must be one of {[*handlers]} but was: {query_type}")
        df = pd.read_sql(query, self.engine)
        total_rows = len(df.index)
        return (total_rows, handlers[query_type](filename))
