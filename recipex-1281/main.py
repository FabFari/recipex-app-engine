#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import endpoints
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb

# Datastore Classes
class User(ndb.Model):
    email = ndb.StringProperty(1, required=True)
    name = ndb.StringProperty(2, required=True)
    surname = ndb.StringProperty(3, required=True)
    birth = ndb.DateProperty(4, auto_now_add=True)
    city = ndb.StringProperty(5)

class Caregiver(ndb.Model):
    field = ndb.StringProperty(1, required=True)
    years_exp = ndb.StringProperty(2)

class Measurement(ndb.Model):
    id = ndb.StringProperty(1)
    date_time = ndb.DateTimeProperty(2, auto_now_add=True)
    kind = ndb.StringProperty(3, required=True)
    # Blood Pressure (BP)
    systolic = ndb.IntegerProperty(4)
    diastolic = ndb.IntegerProperty(5)
    pulse = ndb.IntegerProperty(6)
    # Heart Rate (HR)
    bpm = ndb.IntegerProperty(7)
    # Respiratory Rate
    respirations = ndb.IntegerProperty(8)
    # Pulse Oximetry (SpO2)
    spo2 = ndb.FloatProperty(9)
    # Blood Sugar (HGT)
    hgt = ndb.FloatProperty(10)
    # Body Temperature
    degrees = ndb.FloatProperty(11)
    # Pain
    nrs = ndb.IntegerProperty(12)


# Message Classes
class DefaultResponseMessage(messages.Message):
    message = messages.StringField(1)


@endpoints.api(name="recipexServerApi", version="v1",
               hostname="recipex-1281.appspot.com",
               allowed_client_ids=[endpoints.API_EXPLORER_CLIENT_ID],
               scopes=[endpoints.EMAIL_SCOPE])
class RecipexServerApi(remote.Service):
    @endpoints.method(message_types.VoidMessage, DefaultResponseMessage,
                      path='hello', http_method="GET", name="hello.helloWorld")
    def hello_world(self, request):
        return DefaultResponseMessage(message="Hello World!")

APPLICATION = endpoints.api_server([RecipexServerApi])
