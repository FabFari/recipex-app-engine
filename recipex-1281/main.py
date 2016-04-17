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
from google.appengine.ext.ndb import Key
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb

from datetime import datetime


# Datastore Classes
class User(ndb.Model):
    email = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    surname = ndb.StringProperty(required=True)
    birth = ndb.DateProperty(required=True)
    sex = ndb.StringProperty()
    city = ndb.StringProperty()
    address = ndb.StringProperty()
    relatives = ndb.KeyProperty(repeated=True)
    pc_phycian = ndb.KeyProperty()
    visiting_nurse = ndb.KeyProperty()
    caregivers = ndb.KeyProperty(repeated=True)


# Mettere disponibilita con Google Calendar
class Caregiver(ndb.Model):
    field = ndb.StringProperty(required=True)
    years_exp = ndb.StringProperty()
    patients = ndb.KeyProperty()


class Measurement(ndb.Model):
    date_time = ndb.DateTimeProperty(auto_now_add=True)
    kind = ndb.StringProperty(required=True)
    # Blood Pressure (BP)
    systolic = ndb.IntegerProperty()
    diastolic = ndb.IntegerProperty()
    pulse = ndb.IntegerProperty()
    # Heart Rate (HR)
    bpm = ndb.IntegerProperty()
    # Respiratory Rate (RR)
    respirations = ndb.IntegerProperty()
    # Pulse Oximetry (SpO2)
    spo2 = ndb.FloatProperty()
    # Blood Sugar (HGT)
    hgt = ndb.FloatProperty()
    # Body Temperature (T)
    degrees = ndb.FloatProperty()
    # Pain (P)
    nrs = ndb.IntegerProperty()
    # Cholesterol
    level = ndb.IntegerProperty()


# Message Classes
class DefaultResponseMessage(messages.Message):
    code = messages.IntegerField(1)
    message = messages.StringField(2)
    payload = messages.StringField(3)


class RegisterUserMessage(messages.Message):
    email = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    surname = messages.StringField(3, required=True)
    birth = messages.StringField(4, required=True)
    sex = messages.StringField(5)
    city = messages.StringField(6)
    address = messages.StringField(7)
    field = messages.StringField(8)
    years_exp = messages.IntegerField(9)


class UpdateUserMessage(messages.Message):
    id = messages.StringField(1, required=True)
    name = messages.StringField(2)
    surname = messages.StringField(3)
    birth = messages.StringField(4)
    sex = messages.StringField(5)
    city = messages.StringField(6)
    address = messages.StringField(7)
    field = messages.StringField(8)
    years_exp = messages.IntegerField(9)


class UserIdMessage(messages.Message):
    id = messages.StringField(1, required=True)


class UserInfoMessage(messages.Message):
    email = messages.StringField(1)
    name = messages.StringField(2)
    surname = messages.StringField(3)
    birth = messages.StringField(4)
    sex = messages.StringField(5)
    city = messages.StringField(6)
    address = messages.StringField(7)
    field = messages.StringField(8)
    years_exp = messages.IntegerField(9)
    response = messages.MessageField(DefaultResponseMessage, 10)


@endpoints.api(name="recipexServerApi", version="v1",
               hostname="recipex-1281.appspot.com",
               allowed_client_ids=[endpoints.API_EXPLORER_CLIENT_ID],
               scopes=[endpoints.EMAIL_SCOPE])
class RecipexServerApi(remote.Service):
    @endpoints.method(message_types.VoidMessage, DefaultResponseMessage,
                      path='hello', http_method="GET", name="hello.helloWorld")
    def hello_world(self, request):
        RecipexServerApi.authentication_check()
        return DefaultResponseMessage(message="Hello World!")

    @endpoints.method(RegisterUserMessage, DefaultResponseMessage,
                      path="users", http_method="POST", name="users.registerUser")
    def register_user(self, request):
        RecipexServerApi.authentication_check()

        if User.query(User.email == request.email).count() > 0:
            return DefaultResponseMessage(code="412 Precondition Failed", message="User already existent.")

        birth = datetime.strptime(request.birth, "%Y-%m-%d")
        new_user = User(email=request.email, name=request.name, surname=request.surname, birth=birth,
                        sex=request.sex, city=request.city, address=request.address)
        user_key = new_user.put()

        if request.field:
            new_caregiver = Caregiver(parent=user_key, field=request.field, years_exp=request.years_exp)
            new_caregiver.put()

        return DefaultResponseMessage(code="201 Created", message="User registered.", payload=user_key.urlsafe())

    @endpoints.method(UpdateUserMessage, DefaultResponseMessage,
                      path="users/{id}", http_method="PUT", name="user.updateUser")
    def update_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(urlsafe=request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="Failed to update user info.")

        '''
            relatives = request.relatives
            relative_keys = []
            if relatives:
                for rel_key in range(len(relatives)):
                    relative = Key(urlsafe=rel_key).get()
                    if relative is not None:
                        relative_keys.append(relative.key)
        '''

        if request.name:
            user.name = request.name
        if request.surname:
            user.surname = request.surname
        if request.birth:
            birth = datetime.strptime(request.birth, "%Y-%m-%d")
            user.birth = birth
        if request.sex:
            user.sex = request.sex
        if request.city:
            user.city = request.city
        if request.address:
            user.address = request.address
        user.put()

        if request.field or request.years_exp:
            caregiver = Caregiver.query(ancestor=user.key).get()
            if caregiver is None:
                return DefaultResponseMessage(code="404 Not Found", message="Failed to update caregiver info.")
            if request.field:
                caregiver.field = request.field
            if request.years_exp:
                caregiver.years_exp = request.years_exp
            caregiver.put()

        return DefaultResponseMessage(code="200 OK", message="User updated.")

    @endpoints.method(UserIdMessage, UserInfoMessage,
                      path="users/{id}", http_method="GET", name="user.getUser")
    def get_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(urlsafe=request.id).get()
        if not user:
            return UserInfoMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                   message="Failed to get user info."))
        birth = datetime.strftime(user.birth, "%Y-%m-%d")

        usr_info = UserInfoMessage(email=user.email, name=user.name, surname=user.surname,
                                   birth=birth, sex=user.sex, city=user.city, address=user.address,
                                   response=DefaultResponseMessage(code="200 OK",
                                                                   message="User info retrived."))

        caregiver = Caregiver.query(ancestor=user.key).get()
        if caregiver:
            usr_info.field = caregiver.field
            usr_info.years_exp = caregiver.years_exp

        return usr_info

    @endpoints.method(UserIdMessage, DefaultResponseMessage,
                      path="users/{id}", http_method="DELETE", name="user.deleteUser")
    def delete_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(urlsafe=request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")
        user.key.delete()
        return DefaultResponseMessage(code="200 OK", message="User deleted.")

    @classmethod
    def authentication_check(cls):
        current_user = endpoints.get_current_user()
        if current_user is None:
            raise endpoints.UnauthorizedException('Invalid token.')

        if current_user.email() != "recipex.app@gmail.com":
            raise endpoints.UnauthorizedException('User Unauthorized')

APPLICATION = endpoints.api_server([RecipexServerApi])
