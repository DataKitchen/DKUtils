.. DKUtils documentation master file, created by
   sphinx-quickstart on Fri Apr 17 13:09:19 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

DKUtils documentation
=====================

This documentation describes the DKUtils python package. It is current as of release |release|.

DKUtils serves 2 main purposes: (1) provide a client for interacting with the DataKitchen platform's REST API
(i.e. DataKitchenClient) and (2) provide utility classes and methods for interacting with tools commonly orchestrated in
recipes in the DataKitchen Platform (e.g. Alteryx, JIRA, GMail, etc.). Here is the list of clients presently offered by
this package including a brief description of each.

:ref:`Alteryx Gallery Client <dkutils.alteryx\\_api.gallery\\_client module>`
-----------------------------------------------------------------------------
Client object for invoking calls to the Alteryx Gallery API. See the
`Alteryx API Documentation <https://gallery.alteryx.com/api-docs/>`_ for more information.

:ref:`Streamsets DataCollectorClient <dkutils.streamsets\\_api.datacollector\\_client module>`
----------------------------------------------------------------------------------------------
Client object for invoking StreamSets Data Collector REST API.

:ref:`DataKitchen Client <dkutils.datakitchen\\_api.datakitchen\\_client module>`
---------------------------------------------------------------------------------
Client object for invoking DataKitchen API calls. If the API call requires a kitchen, recipe, and/or variation, you must
set those fields on the client instance prior to invoking those methods (or set them via the constructor when a class
instance is created).

Python scripts in recipe variations often require interactions with the DataKitchen Platform REST API. For instance, a
recipe variation may want to submit order runs, monitor them, and report their status. This client facilitates
those interactions in a user friendly manner.

:ref:`GMailClient <dkutils.gmail\\_api.gmail\\_client module>`
--------------------------------------------------------------
Client object for access the GMail API. The create_base64_encoded_token function can be used to initially create a set
of credentials which are base64 encoded in a file that can be looded into vault. This value from vault can then be used
as an environment variable in a variation. The get_object_from_environment can be used to reconstitute the credentials
from the environment variable.

:ref:`JiraClient <dkutils.jira\\_api.jira\\_client module>`
-----------------------------------------------------------
Client object for invoking JIRA Python API.

:ref:`RemoteClient <dkutils.ssh.remote\\_client module>`
--------------------------------------------------------
Client to interact with a remote host via SSH & SCP.

:ref:`VeevaNetworkClient <dkutils.veeva\\_network\\_api.veeva\\_network\\_client module>`
-----------------------------------------------------------------------------------------
Create a client for accessing Veeva Network. This class should not be instantiated directly. You should use either
VeevaSourceSubscriptionClient or VeevaTargetSubscriptionClient.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   Code Documentation <apidoc/modules>
   guide
   release_notes



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
