.. line-block::

	**University of Rome "La Sapienza"**
	*Master of Science in Engineering in Computer Science*
	*Pervasive Systems, a.y. 2015-16*
	Pervasive Systems Group Project by Fabrizio Farinacci and Sara Veterini

Recipex - Backend
=======
.. image:: https://github.com/FabFari/recipex/blob/master/app/screenshot/logo_wide.jpg
   :align: center

This is the *Backend* used by the mobile application.
It's made up of two main parts:

- A Google App Engine (GAE) application, written in Python
- A Google Cloud Endpoints API, offering RPC-like methods to the *Frontend*

Google App Engine Application
=============================

`Google Cloud Platform <https://cloud.google.com/>`_ infrastructure allows to develop and deploy apps on it's distributed web-server network in a very simple and practical way.
This can be done by writing a Google App Engine Application in your preferred language (i.e. Python)
giving also the possibility to manage your application by means of a very practical `Google API Console <https://console.developers.google.com/>`_, 
a web interface offering all the basic tools needed by a developer to control your application.
It also offers a free storage (up to a limit of some GB of space) with the `Google Cloud Datastore <https://cloud.google.com/datastore/>`_, 
a highly-scalable NoSQL database integrated within the GAE framework and easily accessible (in the case of Python) with a simple and powerful client library (`Python NDB CLient library <https://cloud.google.com/appengine/docs/python/ndb/>`_).

Application Schema
==================

Even if the Google Cloud Datastore is a NoSQL database, it is possible to give some structure to the data 
(it's not a pure Key-Value database). So data can be quite well structured still preserving the high-scalability 
advantages that a pure NoSQL database offers. The ER Diagram of the data stored for the application is the following:

.. image:: https://github.com/FabFari/recipex-app-engine/blob/master/images/recipex_er_diagram.png
   :align: center

Google Cloud Endpoints API
=========================

Google Cloud Platform offers also a very simple and practical way to develop a API Backend for a mobile application.
This is possible using `Google Cloud Endpoints <https://cloud.google.com/endpoints/>`_ that is a Google App Engine feature that simplifies
the API development and management for your applications. All you have to do to turn your Google App Engine application into a very 
practical RESTful API is to properly annotate your class and it's methods with the annotations defined into GCE client library and creating
specific messages to be exchanged between the backend and the mobile application.
Then all you have to do is to generate automatically the client libraries to be used by the application (in a middleware-like fashion); in the 
case of an android application the specific command line command to run is the following:

.. code-block:: bash

	$ google_appengine/endpointscfg.py get_client_lib java -bs gradle main.RecipexServerApi
	
That will generate a zip file containing the libraries to be used in your Android project.

Application's API
-----------------

Like any GAE application using Google Cloud Endpoints, the Endpoints API offered by the backen is publicly accessible 
(even if the access to the remote methods can be restricted using specific OAuth 2.0 checks).
The Endpoints API for the application is accessible at the following address:
https://apis-explorer.appspot.com/apis-explorer/?base=https://recipex-1281.appspot.com/_ah/api#p/
Within the API all the avaivable RPCs methods available are listed along with a brief description on the method capabilities.

Info & Contacts
===============

**Team**:

- `Fabrizio Farinacci <https://it.linkedin.com/in/fabrizio-farinacci-496679116/>`_
- `Sara Veterini <https://it.linkedin.com/in/sara-veterini-667684116/>`_

The project was developed and has been presented within the course of "Pervasive Systems", 
held by Prof. Ioannis Chatzigiannakis within the Master of Science in Computer Science (MSE-CS),
at University of Rome "La Sapienza". Informations about the course are available in the following page:
http://ichatz.me/index.php/Site/PervasiveSystems2016.

Additional informations about the project can be found in the following Slideshare presentations:

- http://www.slideshare.net/FabrizioFarinacci1/recipex-your-personal-caregiver-and-lifestyle-makeover
- http://www.slideshare.net/FabrizioFarinacci1/recipex-your-personal-caregiver-and-lifestyle-makeover-62091050


