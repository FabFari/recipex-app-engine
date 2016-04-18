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

import logging


# CONSTANTS

MEASUREMENTS_KIND = ["BP", "HR", "RR", "SpO2", "HGT", "TMP", "PAIN", "CHL"]


# DATASTORE CLASSES

class User(ndb.Model):
    email = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    surname = ndb.StringProperty(required=True)
    birth = ndb.DateProperty(required=True)
    sex = ndb.StringProperty()
    city = ndb.StringProperty()
    address = ndb.StringProperty()
    relatives = ndb.PickleProperty(compressed=True)
    pc_physician = ndb.KeyProperty()
    visiting_nurse = ndb.KeyProperty()
    caregivers = ndb.PickleProperty(compressed=True)


# TODO Mettere disponibilita con Google Calendar
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
    # Heart Rate (HR)
    bpm = ndb.IntegerProperty()
    # Respiratory Rate (RR)
    respirations = ndb.IntegerProperty()
    # Pulse Oximetry (SpO2)
    spo2 = ndb.FloatProperty()
    # Blood Sugar (HGT)
    hgt = ndb.FloatProperty()
    # Body Temperature (TMP)
    degrees = ndb.FloatProperty()
    # Pain (P)
    nrs = ndb.IntegerProperty()
    # Cholesterol (CHL)
    chl_level = ndb.IntegerProperty()


# MESSAGE CLASSES

class DefaultResponseMessage(messages.Message):
    code = messages.StringField(1)
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
    id = messages.IntegerField(1, required=True)
    name = messages.StringField(2)
    surname = messages.StringField(3)
    birth = messages.StringField(4)
    sex = messages.StringField(5)
    city = messages.StringField(6)
    address = messages.StringField(7)
    field = messages.StringField(8)
    years_exp = messages.IntegerField(9)


class UserIdMessage(messages.Message):
    id = messages.IntegerField(1, required=True)


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


class AddMeasurementMessage(messages.Message):
    user_id = messages.IntegerField(1, required=True)
    date_time = messages.StringField(2, required=True)
    kind = messages.StringField(3, required=True)
    # Blood Pressure (BP)
    systolic = messages.IntegerField(4)
    diastolic = messages.IntegerField(5)
    # Heart Rate (HR)
    bpm = messages.IntegerField(6)
    # Respiratory Rate (RR)
    respirations = messages.IntegerField(7)
    # Pulse Oximetry (SpO2)
    spo2 = messages.FloatField(8)
    # Blood Sugar (HGT)
    hgt = messages.FloatField(9)
    # Body Temperature (T)
    degrees = messages.FloatField(10)
    # Pain (P)
    nrs = messages.IntegerField(11)
    # Cholesterol
    chl_level = messages.IntegerField(12)

class UpdateMeasurementMessage(messages.Message):
    id = messages.IntegerField(1, required=True)
    user_id = messages.IntegerField(2, required=True)
    date_time = messages.StringField(3, required=True)
    kind = messages.StringField(4, required=True)
    # Blood Pressure (BP)
    systolic = messages.IntegerField(5)
    diastolic = messages.IntegerField(6)
    # Heart Rate (HR)
    bpm = messages.IntegerField(7)
    # Respiratory Rate (RR)
    respirations = messages.IntegerField(8)
    # Pulse Oximetry (SpO2)
    spo2 = messages.FloatField(9)
    # Blood Sugar (HGT)
    hgt = messages.FloatField(10)
    # Body Temperature (T)
    degrees = messages.FloatField(11)
    # Pain (P)
    nrs = messages.IntegerField(12)
    # Cholesterol
    chl_level = messages.IntegerField(13)

class MeasurementIdMessage(messages.Message):
    user_id = messages.IntegerField(1, required=True)
    id = messages.IntegerField(2, required=True)

class MeasurementInfoMessage(messages.Message):
    date_time = messages.StringField(1)
    kind = messages.StringField(2)
    # Blood Pressure (BP)
    systolic = messages.IntegerField(3)
    diastolic = messages.IntegerField(4)
    # Heart Rate (HR)
    bpm = messages.IntegerField(5)
    # Respiratory Rate (RR)
    respirations = messages.IntegerField(6)
    # Pulse Oximetry (SpO2)
    spo2 = messages.FloatField(7)
    # Blood Sugar (HGT)
    hgt = messages.FloatField(8)
    # Body Temperature (T)
    degrees = messages.FloatField(9)
    # Pain (P)
    nrs = messages.IntegerField(10)
    # Cholesterol
    chl_level = messages.IntegerField(11)
    response = messages.MessageField(DefaultResponseMessage, 12)


class UserRelativeCaregiverMessage(messages.Message):
    id = messages.IntegerField(1, required=True)
    set = messages.IntegerField(2, required=True, repeated=True)


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

        try:
            birth = datetime.strptime(request.birth, "%Y-%m-%d")
        except ValueError:
            return DefaultResponseMessage(code="400 Bad Request", message="Bad birth format.")

        new_user = User(email=request.email, name=request.name, surname=request.surname, birth=birth,
                        sex=request.sex, city=request.city, address=request.address)
        user_key = new_user.put()

        if request.field:
            new_caregiver = Caregiver(parent=user_key, field=request.field, years_exp=request.years_exp)
            new_caregiver.put()

        return DefaultResponseMessage(code="201 Created", message="User registered.", payload=user_key.id())

    @endpoints.method(UpdateUserMessage, DefaultResponseMessage,
                      path="users/{id}", http_method="PUT", name="user.updateUser")
    def update_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="Failed to update user info.")

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
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        birth = datetime.strftime(user.birth, "%Y-%m-%d")
        # TODO Aggiungere ritorno parametri mancanti
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
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")
        # TODO Gestire le rimozioni in cascata (Misurazioni, Familiari, Caregiver, exc.)
        user.key.delete()
        return DefaultResponseMessage(code="200 OK", message="User deleted.")

    @endpoints.method(UserRelativeCaregiverMessage, DefaultResponseMessage,
                      path="users/{id}/relatives", http_method="PATCH", name="user.addRelatives")
    def update_relatives(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        relatives = {}
        if not user.relatives:
            relatives = user.relatives
        # TODO Gestire la responsabilità doppia sui dizionari (Paziente-Familiare)
        for relative in range(len(request.set)):
            # If already present, means remove
            if relative in relatives:
                del relatives[relative]
            # If not present, means add
            else:
                relative_key = Key(User, relative)
                if not relative_key.get():
                    return DefaultResponseMessage(code="404 Not Found", message="User(s) not existent.")
                relatives[relative] = relative_key

        user.relatives = relatives
        return DefaultResponseMessage(code="200 OK", message="Relatives updated.")

    @endpoints.method(UserRelativeCaregiverMessage, DefaultResponseMessage,
                      path="users/{id}/relatives", http_method="PATCH", name="user.addRelatives")
    def update_caregivers(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        caregivers = {}
        if not user.caregivers:
            caregivers = user.caregivers
        # TODO Gestire la responsabilità doppia trai dizionari (Paziente-Caregiver)
        for caregiver in range(len(request.set)):
            # If already present, means remove
            if caregiver in caregivers:
                del caregivers[caregiver]
            # If not present, means add
            else:
                caregiver_key = Key(User, caregiver)
                if not caregiver_key.get():
                    return DefaultResponseMessage(code="404 Not Found", message="Caregiver(s) not existent.")
            caregivers[caregiver] = caregiver_key

        user.caregivers = caregivers
        return DefaultResponseMessage(code="200 OK", message="Relatives updated.")

    @endpoints.method(AddMeasurementMessage, DefaultResponseMessage,
                      path="users/{user_id}/measurements", http_method="POST", name="measurements.addMeasurement")
    def add_measurement(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        try:
            date_time = datetime.strptime(request.date_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return DefaultResponseMessage(code="400 Bad Request", message="Bad date_time format.")

        if request.kind not in MEASUREMENTS_KIND:
            return DefaultResponseMessage(code="412 Precondition Failed", message="Wrong measurement kind.")

        new_measurement = Measurement(parent=user.key, date_time=date_time, kind=request.kind)

        if request.kind == "BP":
            if not request.systolic or not request.diastolic:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Input parameter(s) missing.")
            if (request.systolic < 0 or request.systolic > 250) or (request.diastolic < 0 or request.diastolic > 250):
                return DefaultResponseMessage(code="412 Precondition Failed",
                                              message="Input parameter(s) out of range.")
            new_measurement.systolic = request.systolic
            new_measurement.diastolic = request.diastolic
        elif request.kind == "HR":
            if not request.bpm:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Input parameter missing.")
            if request.bpm < 0 or request.bpm > 400:
                return DefaultResponseMessage(code="412 Precondition Failed",
                                              message="Input parameter out of range.")
            new_measurement.bpm = request.bpm
        elif request.kind == "RR":
            if not request.respirations:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Input parameter missing.")
            if request.respirations < 0 or request.respirations > 200:
                return DefaultResponseMessage(code="412 Precondition Failed",
                                              message="Input parameter out of range.")
            new_measurement.respirations = request.respirations
        elif request.kind == "SpO2":
            if not request.spo2:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Input parameter missing.")
            if request.spo2 < 0 or request.spo2 > 100:
                return DefaultResponseMessage(code="412 Precondition Failed",
                                              message="Input parameter out of range.")
            new_measurement.spo2 = request.spo2
        elif request.kind == "HGT":
            if not request.hgt:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Input parameter missing.")
            if request.hgt < 0 or request.hgt > 600:
                return DefaultResponseMessage(code="412 Precondition Failed",
                                              message="Input parameter out of range.")
            new_measurement.hgt = request.hgt
        elif request.kind == "TMP":
            if not request.degrees:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Input parameter missing.")
            if request.degrees < 30 or request.degrees > 45:
                return DefaultResponseMessage(code="412 Precondition Failed",
                                              message="Input parameter out of range.")
            new_measurement.degrees = request.degrees
        elif request.kind == "PAIN":
            if not request.nrs:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Input parameter missing.")
            if request.nrs < 0 or request.hgt > 10:
                return DefaultResponseMessage(code="412 Precondition Failed",
                                              message="Input parameter out of range.")
            new_measurement.nrs = request.nrs
        else:
            if not request.chl_level:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Input parameter missing.")
            if request.chl_level < 0 or request.chl_level > 800:
                return DefaultResponseMessage(code="412 Precondition Failed",
                                              message="Input parameter out of range.")
            new_measurement.chl_level = request.chl_level

        measurement_key = new_measurement.put()

        return DefaultResponseMessage(code="201 Created", message="Measurement added.", payload=measurement_key.id())

    @endpoints.method(UpdateMeasurementMessage, DefaultResponseMessage,
                      path="users/{user_id}/measurements/{id}", http_method="PUT", name="measurement.updateMeasurement")
    def update_measurement(self, request):
        RecipexServerApi.authentication_check()
        measurement = Key(Measurement, request.id).get()
        if not measurement:
            return DefaultResponseMessage(code="404 Not Found", message="Measurement not existent.")
        user_key = Key(User, request.user_id)
        if user_key != measurement.parent:
            return DefaultResponseMessage(code="401 Unauthorized", message="User unauthorized.")

        try:
            date_time = datetime.strptime(request.date_time, "%Y-%m-%d %H:%M:%S")
            measurement.date_time = date_time
        except ValueError:
            return DefaultResponseMessage(code="400 Bad Request", message="Bad date_time format.")

        if request.kind not in MEASUREMENTS_KIND:
            return DefaultResponseMessage(code="412 Precondition Failed", message="Wrong measurement kind.")

        if measurement.kind == "BP":
            if request.systolic:
                if request.systolic < 0 or request.systolic > 250:
                    return DefaultResponseMessage(code="412 Precondition Failed",
                                                  message="Input parameter out of range.")
                measurement.systolic = request.systolic
            if request.diastolic:
                if request.diastolic < 0 or request.diastolic > 250:
                    return DefaultResponseMessage(code="412 Precondition Failed",
                                                  message="Input parameter out of range.")
                measurement.diastolic = request.diastolic
        elif request.kind == "HR":
            if request.bpm:
                if request.bpm < 0 or request.bpm > 400:
                    return DefaultResponseMessage(code="412 Precondition Failed",
                                                  message="Input parameter out of range.")
                measurement.bpm = request.bpm
        elif request.kind == "RR":
            if request.respirations:
                if request.respirations < 0 or request.respirations > 200:
                    return DefaultResponseMessage(code="412 Precondition Failed",
                                                  message="Input parameter out of range.")
                measurement.respirations = request.respirations
        elif request.kind == "SpO2":
            if request.spo2:
                if request.spo2 < 0 or request.spo2 > 100:
                    return DefaultResponseMessage(code="412 Precondition Failed",
                                                  message="Input parameter out of range.")
                measurement.spo2 = request.spo2
        elif request.kind == "HGT":
            if request.hgt:
                if request.hgt < 0 or request.hgt > 600:
                    return DefaultResponseMessage(code="412 Precondition Failed",
                                                  message="Input parameter out of range.")
                measurement.hgt = request.hgt
        elif request.kind == "TMP":
            if request.degrees:
                if request.degrees < 30 or request.degrees > 45:
                    return DefaultResponseMessage(code="412 Precondition Failed",
                                                  message="Input parameter out of range.")
                measurement.degrees = request.degrees
        elif request.kind == "PAIN":
            if request.nrs:
                if request.nrs < 0 or request.nrs > 10:
                    return DefaultResponseMessage(code="412 Precondition Failed",
                                                  message="Input parameter out of range.")
                measurement.nrs = request.nrs
        else:
            if request.chl_level:
                if request.chl_level < 0 or request.chl_level > 800:
                    return DefaultResponseMessage(code="412 Precondition Failed",
                                                  message="Input parameter out of range.")
                measurement.chl_level = request.ch_level

        measurement.put()
        return DefaultResponseMessage(code="200 OK", message="Measurement updated.")

    @endpoints.method(MeasurementIdMessage, MeasurementInfoMessage,
                      path="users/{user_id}/measurements/{id}", http_method="GET", name="measurement.getMeasurement")
    def get_measurement(self, request):
        RecipexServerApi.authentication_check()
        measurement = Key(Measurement, request.id).get()
        if not measurement:
            return MeasurementInfoMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                          message="Measurement not existent."))
        user_key = Key(User, request.user_id)
        if user_key != measurement.parent:
            return MeasurementInfoMessage(response=DefaultResponseMessage(code="401 Unauthorized",
                                                                          message="User unauthorized."))

        date_time = datetime.strftime(measurement.date_time)

        return MeasurementInfoMessage(date_time=date_time, kind=measurement.kind, systolic=measurement.systolic,
                                      diastolic=measurement.diastolic, bpm=measurement.bpm, spo2=measurement.spo2,
                                      respirations=measurement.respirations, degrees=measurement.degrees,
                                      hgt=measurement.hgt, nrs=measurement.nrs, ch_level=measurement.ch_level,
                                      response=DefaultResponseMessage(code="200 OK",
                                                                      message="Measurement info retrieved."))

    @endpoints.method(MeasurementIdMessage, DefaultResponseMessage,
                      path="users/{user_id}/measurements/{id}", http_method="DELETE", name="measurement.deleteMeasurement")
    def delete_measurement(self, request):
        RecipexServerApi.authentication_check()
        measurement = Key(Measurement, request.id).get()
        if not measurement:
            return DefaultResponseMessage(code="404 Not Found", message="Measurement not existent.")
        user_key = Key(User, request.user_id)
        if user_key != measurement.parent:
            return DefaultResponseMessage(code="401 Unauthorized", message="User unauthorized.")

        measurement.key.delete()
        return DefaultResponseMessage(code="200 OK", message="Measurement deleted.")

    @classmethod
    def authentication_check(cls):
        current_user = endpoints.get_current_user()
        if current_user is None:
            raise endpoints.UnauthorizedException('Invalid token.')

        if current_user.email() != "recipex.app@gmail.com":
            raise endpoints.UnauthorizedException('User Unauthorized')

APPLICATION = endpoints.api_server([RecipexServerApi])
