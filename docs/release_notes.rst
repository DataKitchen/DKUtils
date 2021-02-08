Release Notes
=============

v1.4.1
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
