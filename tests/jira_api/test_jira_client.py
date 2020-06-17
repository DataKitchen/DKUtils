from jira.exceptions import JIRAError
from unittest import TestCase
from unittest.mock import patch

from dkutils.jira_api.jira_client import JiraClient

DUMMY_API_KEY = 'dummy_api_key'
DUMMY_COMMENT = 'dummy_comment'
DUMMY_ISSUE = 'dummy_issue'
DUMMY_ISSUE_KEY = 'dummy_issue_key'
DUMMY_SERVER = 'dummy_server'
DUMMY_STATUS = 'dummy_status'
DUMMY_TRANSITION_ID = 'dummy_transition_id'
DUMMY_USERNAME = 'dummy_username'


class MockFields:

    @property
    def string_field(self):
        return 'string_field'

    @property
    def list_field(self):
        return ['list', 'field']


class MockIssue:

    @property
    def fields(self):
        return MockFields()


class TestJiraClient(TestCase):

    def setUp(self):
        jira_patcher = patch('dkutils.jira_api.jira_client.JIRA')
        self.addCleanup(jira_patcher.stop)
        self.mock_jira = jira_patcher.start()
        self.mock_jira_instance = self.mock_jira.return_value
        self.client = JiraClient(DUMMY_SERVER, DUMMY_USERNAME, DUMMY_API_KEY)

    def test_init(self):
        options = {'server': DUMMY_SERVER}
        basic_auth = (DUMMY_USERNAME, DUMMY_API_KEY)
        self.mock_jira.assert_called_once_with(options, basic_auth=basic_auth)

    def test_transition_issue(self):
        self.mock_jira_instance.issue.return_value = DUMMY_ISSUE
        self.mock_jira_instance.find_transitionid_by_name.return_value = DUMMY_TRANSITION_ID

        self.client.transition_issue(DUMMY_ISSUE_KEY, DUMMY_STATUS)

        self.mock_jira_instance.issue.assert_called_with(DUMMY_ISSUE_KEY)
        self.mock_jira_instance.find_transitionid_by_name.assert_called_with(
            DUMMY_ISSUE_KEY, DUMMY_STATUS
        )
        self.mock_jira_instance.transition_issue.assert_called_with(
            DUMMY_ISSUE, DUMMY_TRANSITION_ID
        )

    def test_transition_issue_raises_key_error(self):
        self.mock_jira_instance.find_transitionid_by_name.return_value = None
        with self.assertRaises(KeyError):
            self.client.transition_issue(DUMMY_ISSUE_KEY, DUMMY_STATUS)

    def test_transition_issue_raises_jira_error(self):
        self.mock_jira_instance.transition_issue.side_effect = JIRAError()
        with self.assertRaises(JIRAError):
            self.client.transition_issue(DUMMY_ISSUE_KEY, DUMMY_STATUS)

    def test_add_comment(self):
        self.client.add_comment(DUMMY_ISSUE_KEY, DUMMY_COMMENT)
        self.mock_jira_instance.add_comment.assert_called_once_with(DUMMY_ISSUE_KEY, DUMMY_COMMENT)

    def test_add_comment_raises_jira_error(self):
        self.mock_jira_instance.add_comment.side_effect = JIRAError()
        with self.assertRaises(JIRAError):
            self.client.add_comment(DUMMY_ISSUE_KEY, DUMMY_COMMENT)

    def test_get_issue_field_string(self):
        issue_field_value = self.client.get_issue_field(MockIssue(), 'string_field')
        self.assertEqual('string_field', issue_field_value)

    def test_get_issue_field_list(self):
        issue_field_value = self.client.get_issue_field(MockIssue(), 'list_field')
        self.assertEqual('list,field', issue_field_value)

    def test_get_issue_field_missing(self):
        with self.assertRaises(AttributeError):
            self.client.get_issue_field(MockIssue(), 'foo')
