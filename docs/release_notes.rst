Release Notes
=============

v2.10.0
-------
* Nodes now always publish a STARTED task event in the OrderRunMonitor
* Nodes now report correct elapsed run time in the OrderRunMonitor

v2.9.6
------
* Node start_time was not being updated properly in the OrderRunMonitor

v2.9.5
------
* Handle a platform bug where start_time may be None in the OrderRunMonitor

v2.9.4
------
* Bugfix start_time must be an int, not a string in the OrderRunMonitor

v2.9.3
------
* Bugfix to handle a start_time of 0 (i.e. 01/01/1970) in the OrderRunMonitor

v2.9.2
------
* Bugfix event timestamp in OrderRunMonitor

v2.9.1
------
* Bugfix to add setter to Node status in OrderRunMonitor

v2.9.0
------
* OrderRunMonitor now uses the node's start_time for the event_timestamp (previously it used datetime.now())
* OrderRunMonitor now publishes WARNING, ERROR, and CRITICAL log messages
* OrderRunMonitor now publishes test results

v2.8.0
------
* Added testing and docstrings to OrderRunMonitor class
* Order run id being used as the run_tag to events ingestion API requests in OrderRunMonitor
* Added get_node_files method to Recipe class
* Exposed events-ingestion-api host parameter in OrderRunMonitor class constructor

v2.7.0
------
* Added OrderRunMonitor class that publishes order run events to the Events Ingestion API.

v2.6.0
------
* Added DataKitchen API class for performing CRUD operations on vault.

v2.5.0
------
* Add retry decorator for retrying API requests that return an HTTP 50X error
* Expose optional arguments in the DK Client get_order_run_details method
* Add parent kitchen name and is ingredient kitchen methods to Kitchen class

v2.4.1
------
* Downgrade sqlalchemy dependency to 1.4.27 to resolve conflict when installing DKUtils in Google Composer.

v2.4.0
------
* Add get/add/delete/update kitchen staff/roles functions to DataKitchenClient.
* Update docstrings in Recipe class.

v2.3.1
------
* Update paramiko package to v2.10.4 to address vulnerability found in versions <=2.10.1

v2.3.0
------
* Added new Recipe class to DataKitchenClient
* Added create and delete recipes to Recipe class
* Added get, update, and delete recipe files to Recipe class

v2.2.0
-------
* Added new Kitchen class to DataKitchenClient
* Added create and delete kitchens to Kitchen class
* Added get, create, and delete alerts to Kitchen class

v2.1.0
-------
* Add additional parameter to constructor for DataKitchenClient to indicate username and password are API Token

v2.0.0
-------
* Add DataFrameWrapper Class that facilitates running a query in a database via a Pandas Dataframe and then writing the data to files.

v1.12.1
-------
* Add filename and cid when creating message with attachments

v1.12.0
-------
* Add function create_message in sender module for creating email messages
* Add SMTP_Sender class for sending email messages via SMTP

v1.11.0
-------
* Updated Documentation and added a Jupyter notebook with DataKitchenClient examples
* Added delete_order_run and get_kitchens to DataKitchenClient

v1.10.0
-------
* Added stop_on_error argument to DataKitchenClient's create_and_monitor_orders and resume_and_monitor_orders methods.

v1.9.0
------
* Add DataKitchenClient methods to get and delete orders in a kitchen.
* Add DataKitchenClient method to get recipe contents.
* Add functions for extracting tests and test metadata from recipes.

v1.8.2
------
* Fix a problem in the GMailClient that was causing excel spreadsheets sent as attachments to be corrupted.

v1.8.1
------
* Update setup.py and docs in preparation for move to public repository

v1.8.0
------
* Add gmail_api

v1.7.1
------
* Standardize logging
* Remove redundant log message in DataKithenClient _api_request
* Do not log response content when validating or refreshing a token - these exceptions are already handled properly

v1.7.0
------
* Log response content when a request to the DataKitchen REST API fails

v1.6.0
-------
* Add run_subscription_job function

v1.5.0
-------
* Add create_veeva_network_subscription_client function

v1.4.0
-------
* Add api for veeva network

v1.3.3
-------
* Upgrade pandas requirement to >=1.1.2 to fix test failure

v1.3.2
-------
* Fix bug in add_kitchen_staff

v1.3.1
-------
* Properly add dependencies to setup.py so they are installed when this package is pip installed

v1.3.0
-------
* Added set_logging_level function

v1.2.0
-------
* Added get_globals_config function

v1.1.0
-------
* Added Alteryx Gallery API client

v1.0.1
------
* Bugfix RemoteClient bulk upload to resolve remote path issue

v1.0.0
------
* Add bulk download method to RemoteClient
* Move remote path from RemoteClient constructor to bulk upload & download methods

v0.16.0
-------
* Add option to stream logs to RemoteClient commands execution

v0.15.0
-------
* Change URL used by get_recipes function

v0.14.0
-------
* Added RemoteClient module which can be used execute commands and upload files to a server using ssh

v0.13.0
-------
* Add DataKitchenClient function get_variations

v0.12.0
-------
* Add DataKitchenClient function get_order_status

v0.11.0
-------
* Add additional check to validate kitchen, recipe, orders combination
* Add function get_recipes

v0.10.2
-------
* Added additional check to validate_globals to check that values that should be changed have been

v0.10.1
-------
* Added JIRA API client

v0.10.0
-------
* PACKAGE REMOVED FROM PYPI - DUPLICATE OF v0.9.0

v0.9.0
------
* Add function get_override_names_that_do_not_exist
* Add function get_override_names_that_exist
* Added parameter to get_overrides to facilitate the retrieval of a subset of overrides

v0.8.2
------
* Explicitly invoke tilde expansion when deriving the path to a user's dk context

v0.8.1
------
* Fixed incorrect formatting in release notes below for v0.8.0

v0.8.0
------
* Added function to support updating kitchen staff
* Added factory method to create DataKitchenClient using context created by DKCloudCommand

v0.7.1
------
* Made some minor documentation changes
* Added __str__ method to DictionaryComparator

v0.7.0
------
* Added functions to support retrieving, updating and comparing kitchen overrides

v0.6.1
------
* Documented development process for updating and deploying this DKUtils library

v0.6.0
------
* Added StreamSets DataCollector client

v0.5.0
------
* Added create/resume and monitor orders methods to DataKitchen API Client

  * Waits for the orders to complete or for a specified timeout duration (whichever comes first)
  * Number of maximum concurrently running orders can be specified


v0.4.0
------
* Added generalized API request method to DataKitchen API Client
* Added skip_token_verification function to validations
* Updated existing API methods to use new generalized API Request method

v0.3.0
------
* Added update kitchen vault method to DataKitchen API Client
* Added get_utc_timestamp function to return current UTC time in milliseconds since
  epoch which is the same format used for order run timings field

v0.2.0
------
* Add resume order run method to DataKitchen API Client

v0.1.0
------
* Added DataKitchen API Client
* Added get order run status
* Added monitor order runs
* Added get order run details function

v0.0.4
------
* Add function for retrieving order runs details
* Update documentation with release notes and a guide

v0.0.3
------
* Bugfix global variable validation

v0.0.2
------
* Update WaitLoop to input a max duration as opposed to a datetime

v0.0.1
------
* Initial release
