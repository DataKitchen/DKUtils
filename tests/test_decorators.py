from requests.exceptions import HTTPError
from requests.models import Response
from unittest import TestCase
from unittest.mock import Mock

from dkutils.decorators import retry_50X_httperror

RESPONSE = Mock(spec=Response)
RESPONSE.json.return_value = {}
RESPONSE.status_code = 500


class TestDecorators(TestCase):
    num_attempts = 0

    def setUp(self) -> None:
        self.num_attempts = 0

    def test_retry_decorator(self) -> None:

        @retry_50X_httperror(tries=3, delay=1, backoff=1)
        def throw_500_httperror():
            if self.num_attempts < 2:
                self.num_attempts += 1
                raise HTTPError(response=RESPONSE)

        throw_500_httperror()

    def test_retry_decorator_throws_error(self) -> None:

        @retry_50X_httperror(tries=1)
        def throw_500_httperror():
            raise HTTPError(response=RESPONSE)

        with self.assertRaises(HTTPError):
            throw_500_httperror()
