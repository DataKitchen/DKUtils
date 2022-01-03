from unittest import TestCase
from unittest.mock import patch

from dkutils.reporting.dataframe_wrapper import DataFrameWrapper

USERNAME = 'username'
PASSWORD = 'password'
SNOWFLAKE_ACCOUNT = "anaccount"
DATABASE = 'somedatabase'
WAREHOSE = 'awarehouse'
HOSTNAME = 'somehost'
PORT = 123
QUERY = "select this from that"
TYPE_HTML = 'html'
TYPE_PLOT = 'plot'
TYPE_TEXT = 'text'


class TestDataFrameWrapper(TestCase):

    @patch('dkutils.reporting.dataframe_wrapper.create_engine')
    def test_snowflake(self, create_engine):
        DataFrameWrapper.snowflake(USERNAME, PASSWORD, SNOWFLAKE_ACCOUNT, DATABASE, WAREHOSE)

        create_engine.assert_called_with(
            f"snowflake://{USERNAME}:{PASSWORD}@{SNOWFLAKE_ACCOUNT}"
            f"/{DATABASE}?warehouse={WAREHOSE}"
        )

    @patch('dkutils.reporting.dataframe_wrapper.create_engine')
    def test_postgresql(self, mock_create_engine):
        DataFrameWrapper.postgresql(USERNAME, PASSWORD, HOSTNAME, DATABASE, PORT)

        mock_create_engine.assert_called_with(
            f"postgresql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"
        )

    @patch('dkutils.reporting.dataframe_wrapper.create_engine')
    def test_mssql(self, mock_create_engine):
        DataFrameWrapper.mssql(USERNAME, PASSWORD, HOSTNAME, DATABASE, PORT)

        mock_create_engine.assert_called_with(
            f"mssql+pymssql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"
        )

    @patch('dkutils.reporting.dataframe_wrapper.create_engine')
    def setUp(self, mock_create_engine) -> None:
        self.sut = DataFrameWrapper("")
        self.mock_engine = mock_create_engine.return_value

    @patch('dkutils.reporting.dataframe_wrapper.pd')
    def test_create_report_without_query_type_raises_exception(self, mock_pd):
        with self.assertRaises(TypeError) as cm:
            self.sut.create_report(QUERY)
        self.assertEqual(
            "create_report() missing 1 required positional argument: 'query_type'",
            cm.exception.args[0]
        )

    @patch('dkutils.reporting.dataframe_wrapper.pd')
    def test_create_report_without_bad_query_type_raises_exception(self, mock_pd):
        bad_type = 'bogus'
        with self.assertRaises(TypeError) as cm:
            self.sut.create_report(QUERY, bad_type)
        self.assertEqual(
            f"query_type must be one of ['html', 'plot', 'text'] but was: {bad_type}",
            cm.exception.args[0]
        )

    @patch('dkutils.reporting.dataframe_wrapper.pd')
    def test_create_report_with_query_type_html(self, mock_pd):
        self.sut.create_report(QUERY, TYPE_HTML)

        mock_pd.read_sql.assert_called_with(QUERY, self.mock_engine)
        mock_pd.read_sql.return_value.to_html.assert_called_with('file_000.html')

    @patch('dkutils.reporting.dataframe_wrapper.pd')
    def test_create_report_with_query_type_html_and_filename(self, mock_pd):
        filename = 'myfile.html'
        self.sut.create_report(QUERY, TYPE_HTML, filename)

        mock_pd.read_sql.assert_called_with(QUERY, self.mock_engine)
        mock_pd.read_sql.return_value.to_html.assert_called_with(filename)

    @patch('dkutils.reporting.dataframe_wrapper.pd')
    def test_create_report_with_query_type_html_with_additional_parms(self, mock_pd):
        additional_parms = {"header": False}
        filename = self.sut.create_report(QUERY, TYPE_HTML, additional_parms=additional_parms)

        self.assertEqual("file_000.html", filename)
        mock_pd.read_sql.assert_called_with(QUERY, self.mock_engine)
        mock_pd.read_sql.return_value.to_html.assert_called_with(
            'file_000.html', **additional_parms
        )

    @patch('dkutils.reporting.dataframe_wrapper.pd')
    def test_create_report_with_query_type_ping_with_additional_parms(self, mock_pd):
        additional_parms = {"header": False}
        filename = self.sut.create_report(QUERY, TYPE_PLOT, additional_parms=additional_parms)

        self.assertEqual("file_000.png", filename)
        mock_pd.read_sql.assert_called_with(QUERY, self.mock_engine)
        mock_dataframe = mock_pd.read_sql.return_value
        mock_dataframe.plot.assert_called_with(**additional_parms)
        mock_figure = mock_dataframe.plot.return_value.get_figure.return_value
        mock_figure.savefig.assert_called_with('file_000.png')

    @patch('dkutils.reporting.dataframe_wrapper.pd')
    def test_create_report_with_query_type_text_with_additional_parms(self, mock_pd):
        additional_parms = {"header": False}
        filename = self.sut.create_report(QUERY, TYPE_TEXT, additional_parms=additional_parms)

        self.assertEqual("file_000.txt", filename)
        mock_pd.read_sql.assert_called_with(QUERY, self.mock_engine)
        mock_pd.read_sql.return_value.to_string.assert_called_with(
            'file_000.txt', **additional_parms
        )
