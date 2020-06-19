import pandas as pd

from jira import JIRA
from jira.exceptions import JIRAError

DEFAULT_FIELDS = [
    'created', 'creator', 'assignee', 'status', 'issuetype', 'priority', 'summary', 'description',
    'resolution', 'resolutiondate'
]


class JiraClient:

    def __init__(self, server, username, api_key):
        """
        Client object for invoking JIRA Python API "https://pypi.org/project/jira/"

        Parameters
        ----------
        server: str
            The server address and context path to use. Defaults to http://localhost:2990/jira
        username : str
            Username to establish a session via HTTP BASIC authentication.
        api_key : str
            API Key to establish a session via HTTP BASIC authentication.
        """
        options = {'server': server}
        self._client = JIRA(options, basic_auth=(username, api_key))

    def transition_issue(self, issue_key, status):
        """
        Perform a transition on an issue.

        Parameters
        ----------
        issue_key : str
            ID or key of the issue to add the comment to (e.g. IM-1)
        status : str
            Name of the transition to perform

        Raises
        ------
        JiraError
            If the issue does not exist or you do not have permission to see it.
        KeyError
            If transition does not exist for the issue.

        Returns
        ------
        None
        """
        try:
            issue = self._client.issue(issue_key)
            transition_id = self._client.find_transitionid_by_name(issue_key, status)
            if transition_id is None:
                raise KeyError(
                    f'Error: Transition "{status}" does not exist for Issue {issue_key}.'
                )
            self._client.transition_issue(issue, transition_id)
        except JIRAError:
            print(f'Error: Issue "{issue_key}" does not exist.')
            raise

    def add_comment(self, issue_key, comment):
        """
        Add a comment from the current authenticated user on the specified issue and return a Resource for it.

        Parameters
        ----------
        issue_key : str
            ID or key of the issue to add the comment to (e.g. IM-1)
        comment : str
            Text of the comment to add

        Raises
        ------
        JiraError
            If the issue does not exist or you do not have permission to see it.

        Returns
        ------
        Resource object of <class 'jira.resources.Comment'> with Comment ID.
        """
        try:
            return self._client.add_comment(issue_key, comment)
        except JIRAError:
            print(f'Error: Issue "{issue_key}" does not exist.')
            raise

    def get_issue_field(self, issue, field):
        """
        Helper function that returns the value of the requested value for an issue. This function is used in the
        get_issues() funtion to extract the fields of an issue.

        Parameters
        ----------
        issue : <class 'jira.resources.Issue'>
            Issue Object of class <class 'jira.resources.Issue'>.
        field : str
            Name of the expected field. (e.g status).
            Note: for a custom field, use the custom field id. (e.g. customfield_10028)

        Raises
        ------
        AttributeError
            If the Field does not exist for the issue.

        Returns
        ------
        str
            For a text field : returns a string with the value of the requested field. (e.g. 'Error')
            For a field with multiple options : returns a string of comma separated values from all the options
            available in the field. (for e.g 'User1,User2')
        """
        try:
            field_value = getattr(issue.fields, field)
            if isinstance(field_value, list):
                return (','.join(map(str, field_value)))
            else:
                return str(field_value)
        except AttributeError:
            print(f'Field "{field}" does not exist for issue "{issue}."')
            raise

    def get_issues(self, project, fields=DEFAULT_FIELDS):
        """
        Returns a Pandas DataFrame of all JIRA Issues for the requested project with values for
        all requested fields.

        Parameters
        ----------
        project : str
            Project name or key to pull issues from.
        fields : list, optional
            A list of fields to be extracted for each issue in the project.
            (default is ['created', 'creator', 'assignee', 'status', 'issuetype', 'priority',
            'summary', 'description', 'resolution', 'resolutiondate'])

            Note: for a custom field, use the custom field id. (e.g. customfield_10028)

        Raises
        ------
        AttributeError
            If the Field does not exist for the issue.

        Returns
        ------
        pandas DataFrame
            A pandas DataFrame of all issues for the requested project with values for all the
            requested fields.

            The column header of the resulting DataFrame is of the form:

                If "fields" is defined: ['project', 'key', field1, field2 , field3....]
                (default) If "fields" is not defined: ['project', 'key' ,'created', 'creator',
                'assignee','status', 'issuetype', 'priority', 'summary', 'description',
                'resolution', 'resolutiondate']

        """
        block_num = 0
        block_size = 1000

        # define base header list
        header_list = ['project', 'key']
        # extend the base header list to include requested fields
        header_list.extend(fields)

        # initialize lists
        all_issues = []
        issues_list = []

        # Retrieve all issues from JIRA Project
        issues = self._client.search_issues(f'project={project}', 0, block_size)
        while len(issues) > 0:
            all_issues.extend(issues)
            block_num += 1
            issues = self._client.search_issues(
                f'project={project}', block_num * block_size, block_size
            )

        # Loop over all issues and extract project, issue and requested fields defined by the
        # parameter fields
        for issue in all_issues:
            issue_details = [project, issue.key]
            extract_fields = list(map(lambda n: self.get_issue_field(issue, n), fields))
            issue_details.extend(extract_fields)
            issues_list.append(issue_details)
        df_issues = pd.DataFrame(issues_list, columns=header_list, index=None)
        return df_issues
