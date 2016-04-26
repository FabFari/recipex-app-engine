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
from google.appengine.api import oauth
from google.appengine.ext.ndb import Key
from protorpc import messages
from protorpc import message_types
from protorpc import remote

from google.appengine.ext import ndb

from datetime import datetime

import logging

# TODO Controlla bene tutti i set: quando inserisci devi prima controllare... e non lo fai quasi mai!!!

# CONSTANTS

MEASUREMENTS_KIND = ["BP", "HR", "RR", "SpO2", "HGT", "TMP", "PAIN", "CHL"]
REQUEST_KIND = ["RELATIVE", "CAREGIVER", "PC_PHYSICIAN", "V_NURSE"]
ROLE_TYPE =["PATIENT", "CAREGIVER"]
WEB_CLIENT_ID = "1077668244667-v42n91q6av4tlub6rh3dffbdqa0pncj0.apps.googleusercontent.com"
ANDROID_CLIENT_ID = "1077668244667-j63dkcsh53g86cgul3vcv5afn1d0m6np.apps.googleusercontent.com"
ANDROID_AUDIENCE = "1077668244667-j63dkcsh53g86cgul3vcv5afn1d0m6np.apps.googleusercontent.com"


'''
# DATASTORE SUBCLASSES
class DictPickleProperty(ndb.PickleProperty):
    def __init__(self, **kwds):
        kwds['default'] = kwds.get('default', {})
        super(DictPickleProperty, self).__init__(**kwds)
'''

# DATASTORE CLASSES
class User(ndb.Model):
    email = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    surname = ndb.StringProperty(required=True)
    birth = ndb.DateProperty(required=True)
    sex = ndb.StringProperty()
    city = ndb.StringProperty()
    address = ndb.StringProperty()
    relatives = ndb.PickleProperty(compressed=True, default={})
    pc_physician = ndb.KeyProperty()
    visiting_nurse = ndb.KeyProperty()
    caregivers = ndb.PickleProperty(compressed=True, default={})


class Caregiver(ndb.Model):
    field = ndb.StringProperty(required=True)
    years_exp = ndb.IntegerProperty()
    place = ndb.StringProperty()
    patients = ndb.PickleProperty(compressed=True, default={})


# TODO Aggiungere tabella Terapia?
class Measurement(ndb.Model):
    date_time = ndb.DateTimeProperty(auto_now_add=True)
    kind = ndb.StringProperty(required=True)
    note = ndb.StringProperty()
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


class Message(ndb.Model):
    sender = ndb.KeyProperty(required=True)
    receiver = ndb.KeyProperty(required=True)
    message = ndb.StringProperty(required=True)
    hasRead = ndb.BooleanProperty(required=True)
    measurement = ndb.KeyProperty()


class Request(ndb.Model):
    sender = ndb.KeyProperty(required=True)
    receiver = ndb.KeyProperty(required=True)
    kind = ndb.StringProperty(required=True)
    role = ndb.StringProperty()
    caregiver = ndb.KeyProperty()
    message = ndb.StringProperty()


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
    place = messages.StringField(10)


class UpdateUserMessage(messages.Message):
    # id = messages.IntegerField(1, required=True)
    name = messages.StringField(1)
    surname = messages.StringField(2)
    birth = messages.StringField(3)
    sex = messages.StringField(4)
    city = messages.StringField(5)
    address = messages.StringField(6)
    field = messages.StringField(7)
    years_exp = messages.IntegerField(8)
    place = messages.StringField(9)


UPDATE_USER_MESSAGE = endpoints.ResourceContainer(UpdateUserMessage,
                                                  id=messages.IntegerField(2, required=True))

'''
class UserIdMessage(messages.Message):
    id = messages.IntegerField(1, required=True)
    kind = messages.StringField(2)
'''

USER_ID_MESSAGE = endpoints.ResourceContainer(message_types.VoidMessage,
                                              id=messages.IntegerField(2, required=True),
                                              kind=messages.StringField(3))


class UserInfoMessage(messages.Message):
    email = messages.StringField(1)
    name = messages.StringField(2)
    surname = messages.StringField(3)
    birth = messages.StringField(4)
    sex = messages.StringField(5)
    city = messages.StringField(6)
    address = messages.StringField(7)
    relatives = messages.IntegerField(8, repeated=True)
    pc_physician = messages.IntegerField(9)
    visiting_nurse = messages.IntegerField(10)
    caregivers = messages.IntegerField(11, repeated=True)
    field = messages.StringField(12)
    place = messages.StringField(13)
    years_exp = messages.IntegerField(14)
    patients = messages.IntegerField(15, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 16)


class AddMeasurementMessage(messages.Message):
    # user_id = messages.IntegerField(1, required=True)
    date_time = messages.StringField(1, required=True)
    kind = messages.StringField(2, required=True)
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
    note = messages.StringField(12)


ADD_MEASUREMENT_MESSAGE = endpoints.ResourceContainer(AddMeasurementMessage,
                                                      user_id=messages.IntegerField(2, required=True))


class UpdateMeasurementMessage(messages.Message):
    id = messages.IntegerField(1, required=True)
    user_id = messages.IntegerField(2, required=True)
    date_time = messages.StringField(3)
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
    note = messages.StringField(14)


UPDATE_MEASUREMENT_MESSAGE = endpoints.ResourceContainer(UpdateMeasurementMessage,
                                                         id=messages.IntegerField(2, required=True),
                                                         user_id=messages.IntegerField(3, required=True))


'''
class MeasurementIdMessage(messages.Message):
    user_id = messages.IntegerField(1, required=True)
    id = messages.IntegerField(2, required=True)
'''


MEASUREMENT_ID_MESSAGE = endpoints.ResourceContainer(message_types.VoidMessage,
                                                     id=messages.IntegerField(2, required=True),
                                                     user_id=messages.IntegerField(3, required=True))


class MeasurementInfoMessage(messages.Message):
    id = messages.IntegerField(1)
    date_time = messages.StringField(2)
    kind = messages.StringField(3)
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
    note = messages.StringField(13)
    response = messages.MessageField(DefaultResponseMessage, 14)


class UserMeasurementsMessage(messages.Message):
    measurements = messages.MessageField(MeasurementInfoMessage, 1, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 2)


class UserRelativeCaregiverMessage(messages.Message):
    id = messages.IntegerField(1, required=True)
    to_add = messages.IntegerField(2, repeated=True)
    to_del = messages.IntegerField(3, repeated=True)


class UserFirstAidInfoMessage(messages.Message):
    id = messages.IntegerField(1, required=True)
    pc_physician = messages.IntegerField(2)
    visiting_nurse = messages.IntegerField(3)


class MessageSendMessage(messages.Message):
    sender = messages.IntegerField(1, required=True)
    # receiver = messages.IntegerField(2, required=True)
    message = messages.StringField(2, required=True)
    measurement = messages.IntegerField(3)


MESSAGE_SEND_MESSAGE = endpoints.ResourceContainer(MessageSendMessage,
                                                   receiver=messages.IntegerField(2, required=True))

'''
class MessageIdMessage(messages.Message):
    user_id = messages.IntegerField(1, required=True)
    id = messages.IntegerField(2, required=True)
'''

MESSAGE_ID_MESSAGE = endpoints.ResourceContainer(message_types.VoidMessage,
                                                 user_id=messages.IntegerField(2, required=True),
                                                 id=messages.IntegerField(3, required=True))


class MessageInfoMessage(messages.Message):
    id = messages.IntegerField(1)
    sender = messages.IntegerField(2)
    receiver = messages.IntegerField(3)
    hasRead = messages.BooleanField(4)
    message = messages.StringField(5)
    measurement = messages.IntegerField(6)
    response = messages.MessageField(DefaultResponseMessage, 7)


class UserMessagesMessage(messages.Message):
    user_messages = messages.MessageField(MessageInfoMessage, 1, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 2)


class RequestSendMessage(messages.Message):
    sender = messages.IntegerField(1, required=True)
    # receiver = messages.IntegerField(2, required=True)
    kind = messages.StringField(2, required=True)
    role = messages.StringField(3)
    message = messages.StringField(4)


REQUEST_SEND_MESSAGE = endpoints.ResourceContainer(RequestSendMessage,
                                                   receiver=messages.IntegerField(2, required=True))

'''
class RequestIdMessage(messages.Message):
    # user_id = messages.IntegerField(1, required=True)
    # id = messages.IntegerField(2, required=True)
    sender = messages.IntegerField(1, required=True)
    # kind = messages.StringField(4)
'''

REQUEST_ID_MESSAGE = endpoints.ResourceContainer(message_types.VoidMessage,
                                                 user_id=messages.IntegerField(2, required=True),
                                                 id=messages.IntegerField(3, required=True),
                                                 sender=messages.IntegerField(4, required=True))

'''
class RequestAnswerMessage(messages.Message):
    user_id = messages.IntegerField(1, required=True)
    id = messages.IntegerField(2, required=True)
    answer = messages.BooleanField(3, required=True)
'''

REQUEST_ANSWER_MESSAGE = endpoints.ResourceContainer(message_types.VoidMessage,
                                                     user_id=messages.IntegerField(2, required=True),
                                                     id=messages.IntegerField(3, required=True),
                                                     answer=messages.BooleanField(4, required=True))


class RequestInfoMessage(messages.Message):
    id = messages.IntegerField(1)
    sender = messages.IntegerField(2)
    receiver = messages.IntegerField(3)
    kind = messages.StringField(4)
    role = messages.StringField(5)
    caregiver = messages.IntegerField(6)
    message = messages.StringField(7)
    response = messages.MessageField(DefaultResponseMessage, 8)


class UserRequestsMessage(messages.Message):
    requests = messages.MessageField(RequestInfoMessage, 1, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 2)


@endpoints.api(name="recipexServerApi", version="v1",
               hostname="recipex-1281.appspot.com",
               allowed_client_ids=[endpoints.API_EXPLORER_CLIENT_ID, WEB_CLIENT_ID, ANDROID_CLIENT_ID],
               audiences=[ANDROID_AUDIENCE],
               scopes=[endpoints.EMAIL_SCOPE])
class RecipexServerApi(remote.Service):
    @endpoints.method(message_types.VoidMessage, DefaultResponseMessage,
                      path='recipexServerApi/hello', http_method="GET", name="hello.helloWorld")
    def hello_world(self, request):
        RecipexServerApi.authentication_check()
        return DefaultResponseMessage(message="Hello World!")

    @endpoints.method(RegisterUserMessage, DefaultResponseMessage,
                      path="recipexServerApi/users", http_method="POST", name="user.registerUser")
    def register_user(self, request):
        RecipexServerApi.authentication_check()

        if User.query(User.email == request.email).count() > 0:
            return DefaultResponseMessage(code="412 Precondition Failed", message="User already existent.")

        try:
            birth = datetime.strptime(request.birth, "%Y-%m-%d")
        except ValueError:
            return DefaultResponseMessage(code="400 Bad Request", message="Bad birth format.")

        new_user = User(email=request.email, name=request.name, surname=request.surname, birth=birth,
                        sex=request.sex, city=request.city, address=request.address, relatives={}, caregivers={})
        user_key = new_user.put()

        if request.field:
            new_caregiver = Caregiver(parent=user_key, field=request.field, years_exp=request.years_exp,
                                      place=request.place, patients={})
            new_caregiver.put()

        return DefaultResponseMessage(code="201 Created", message="User registered.", payload=str(user_key.id()))

    @endpoints.method(UPDATE_USER_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}", http_method="PUT", name="user.updateUser")
    def update_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        if request.name:
            user.name = request.name
        if request.surname:
            user.surname = request.surname
        if request.birth:
            try:
                birth = datetime.strptime(request.birth, "%Y-%m-%d")
                user.birth = birth
            except ValueError:
                return DefaultResponseMessage(code="400 Bad Request", message="Bad birth format.")
        if request.sex is not None:
            if request.sex:
                user.sex = request.sex
            else:
                user.sex = None
        if request.city is not None:
            if request.city:
                user.city = request.city
            else:
                user.city = None
        if request.address is not None:
            if request.address:
                user.address = request.address
            else:
                user.address = None
        user.put()

        if request.field or request.years_exp:
            caregiver = Caregiver.query(ancestor=user.key).get()
            if not caregiver:
                return DefaultResponseMessage(code="412 Not Found", message="User not a caregiver.")
            if request.field is not None:
                if request.field:
                    caregiver.field = request.field
                else:
                    caregiver.field = None
            if request.years_exp is not None:
                if request.years_exp >= 0:
                    caregiver.years_exp = request.years_exp
                else:
                    caregiver.years_exp = None
            if request.place is not None:
                if request.place:
                    caregiver.place = request.place
                else:
                    caregiver.place = None
            caregiver.put()

        return DefaultResponseMessage(code="200 OK", message="User updated.")

    @endpoints.method(USER_ID_MESSAGE, UserInfoMessage,
                      path="recipexServerApi/users/{id}", http_method="GET", name="user.getUser")
    def get_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        birth = datetime.strftime(user.birth, "%Y-%m-%d")

        usr_info = UserInfoMessage(email=user.email, name=user.name, surname=user.surname,
                                   birth=birth, sex=user.sex, city=user.city, address=user.address,
                                   response=DefaultResponseMessage(code="200 OK",
                                                                   message="User info retrived."))

        if user.pc_physician:
            usr_info.pc_physician = user.pc_physician.id()

        if user.visiting_nurse:
            usr_info.visiting_nurse = user.visiting_nurse.id()

        if user.relatives:
            user_relatives = []
            for relative in user.relatives.keys():
                user_relatives.append(relative)
            usr_info.relatives = user_relatives

        if user.caregivers:
            user_caregivers = []
            for caregiver in user.caregivers.keys():
                user_caregivers.append(caregiver)
            usr_info.caregivers = user_caregivers

        caregiver = Caregiver.query(ancestor=user.key).get()
        if caregiver:
            usr_info.field = caregiver.field
            usr_info.years_exp = caregiver.years_exp
            usr_info.place = caregiver.place
            if caregiver.patients:
                user_patients = []
                for patient in caregiver.patients.keys():
                    user_patients.append(patient)
                usr_info.patients = user_patients

        return usr_info

    @endpoints.method(USER_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}", http_method="DELETE", name="user.deleteUser")
    def delete_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")
        # TODO Gestire le rimozioni in cascata (Misurazioni, Familiari, Caregiver, exc.)
        if user.pc_physician is not None:
            pc_physician = user.pc_physician.get()
            if pc_physician is not None:
                del pc_physician.patients[user.key]
        if user.visiting_nurse is not None:
            visiting_nurse = user.visiting_nurse.get()
            if visiting_nurse is not None:
                del visiting_nurse.patients[user.key]
        if user.caregivers:
            for caregiver_key in user.caregivers:
                caregiver = caregiver_key.get()
                if caregiver is not None:
                    del caregiver.patients[user.key]
        if user.relatives:
            for relative_key in user.relatives:
                relative = relative_key.get()
                if relative is not None:
                    del relative.relatives[user.key]
        measurements = Measurement.query(ancestor=user.key)
        if not measurements:
            for measurement in measurements:
                measurement.key.delete()
        usr_messages = Message.query(ancestor=user.key)
        if not usr_messages:
            for message in usr_messages:
                message.key.delete()
        requests = Request.query(ancestor=user.key)
        if not requests:
            for request in requests:
                request.key.delete()

        caregiver = Caregiver.query(ancestor=user.key).get()
        if caregiver is not None:
            if caregiver.patients:
                for patient_key in user.patients:
                    patient = patient_key.get()
                    if patient is not None:
                        del patient.caregiver[caregiver.key]
            caregiver.key.delete()

        user.key.delete()
        return DefaultResponseMessage(code="200 OK", message="User deleted.")

    @endpoints.method(UserRelativeCaregiverMessage, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/relatives", http_method="PATCH", name="user.updateRelatives")
    def update_relatives(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        relatives = {}
        if not user.relatives:
            relatives = user.relatives
        # TODO Gestire la responsabilita doppia sui dizionari (Paziente-Familiare)
        '''
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
        '''
        for relative in range(len(request.to_add)):
            if relative not in relatives:
                relative_key = Key(User, relative)
                if not relative_key.get():
                    return DefaultResponseMessage(code="404 Not Found", message="User(s) not existent.")
                relatives[relative] = relative_key

        for relative in range(len(request.to_del)):
            if relative in relatives:
                del relatives[relative]

        user.relatives = relatives
        user.put()
        return DefaultResponseMessage(code="200 OK", message="Relatives updated.")

    @endpoints.method(UserRelativeCaregiverMessage, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/caregivers", http_method="PATCH", name="user.updateCaregivers")
    def update_caregivers(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        caregivers = {}
        if not user.caregivers:
            caregivers = user.caregivers
        # TODO Gestire la responsabilita doppia trai dizionari (Paziente-Caregiver)
        '''
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
        '''
        for caregiver in range(len(request.to_add)):
            if caregiver not in caregivers:
                caregiver_key = Key(Caregiver, caregiver)
                if not caregiver_key.get():
                    return DefaultResponseMessage(code="404 Not Found", message="Caregiver(s) not existent.")
                caregivers[caregiver] = caregiver_key

        for caregiver in range(len(request.to_del)):
            if caregiver in caregivers:
                del caregivers[caregiver]

        user.caregivers = caregivers
        user.put()
        return DefaultResponseMessage(code="200 OK", message="Caregivers updated.")

    @endpoints.method(UserRelativeCaregiverMessage, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/patients", http_method="PATCH", name="user.updatePatients")
    def update_patients(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        caregiver = Key(Caregiver, request.id).get()
        if not caregiver:
            return DefaultResponseMessage(code="404 Not Found", message="User not a caregiver.")

        patients = {}
        if not caregiver.patients:
            patients = caregiver.patients
        # TODO Gestire la responsabilita doppia trai dizionari (Paziente-Caregiver)
        '''
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
        '''
        for patient in range(len(request.to_add)):
            if patient not in patients:
                patient_key = Key(User, patient)
                if not patient_key.get():
                    return DefaultResponseMessage(code="404 Not Found", message="Patient(s) not existent.")
                patients[patient] = patient_key

        for patient in range(len(request.to_del)):
            if patient in patients:
                del patients[patient]

        user.patients = patients
        user.put()
        return DefaultResponseMessage(code="200 OK", message="Patients updated.")

    @endpoints.method(UserFirstAidInfoMessage, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/firstaidinfo", http_method="PATCH", name="user.updateFirstAidInfo")
    def update_first_aid_info(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        if not request.pc_physician:
            if user.pc_physician.id() == request.pc_physician:
                return DefaultResponseMessage(code="412 Precondition Failed", message="PC physician already registered.")
            pc_physician_usr = Key(User, request.pc_physician).get()
            if not pc_physician_usr:
                return DefaultResponseMessage(code="404 Not Found", message="User not existent.")
            pc_physician_crgv = Caregiver.query(ancestor=pc_physician_usr.key).get()
            if not pc_physician_crgv:
                return DefaultResponseMessage(code="404 Not Found", message="User not a Caregiver.")
            user.pc_physician = pc_physician_usr.key
            pc_physician_crgv.patients[request.id] = user.key
            user.put()
            pc_physician_crgv.put()

        if not request.visiting_nurse:
            if user.visiting_nurse.id() == request.visiting_nurse:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Visiting nurse already registered.")
            visiting_nurse_usr = Key(User, request.visiting_nurse).get()
            if not visiting_nurse_usr:
                return DefaultResponseMessage(code="404 Not Found", message="User not existent.")
            visiting_nurse_crgv = Caregiver.query(ancestor=visiting_nurse_usr.key).get()
            if not visiting_nurse_crgv:
                return DefaultResponseMessage(code="404 Not Found", message="User not a Caregiver.")
            user.visiting_nurse = visiting_nurse_usr.key
            visiting_nurse_crgv.patients[request.id] = user.key
            user.put()
            visiting_nurse_crgv.put()
        return DefaultResponseMessage(code="200 OK", message="First aid info updated.")

    @endpoints.method(USER_ID_MESSAGE, UserMeasurementsMessage,
                      path="recipexServerApi/users/{id}/measurements", http_method="GET", name="user.getMeasurements")
    def get_measurements(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return UserMeasurementsMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                           message="User not existent."))
        if request.kind:
            if request.kind not in MEASUREMENTS_KIND:
                return UserMeasurementsMessage(response=DefaultResponseMessage(code="412 Precondition Failed",
                                                                               message="Kind not existent."))
            measurements = Measurement.query(ancestor=user.key).filter(Measurement.kind == request.kind)
        else:
            measurements = Measurement.query(ancestor=user.key)

        user_measurements = []

        for measurement in measurements:
            try:
                user_measurements.append(MeasurementInfoMessage(id=measurement.key.id(), kind=measurement.kind,
                                                                date_time=datetime.strftime(measurement.date_time, "%Y-%m-%d %H:%M:%S"),
                                                                systolic=measurement.systolic,
                                                                diastolic=measurement.diastolic, bpm=measurement.bpm,
                                                                spo2=measurement.spo2, respirations=measurement.respirations,
                                                                degrees=measurement.degrees, hgt=measurement.hgt,
                                                                nrs=measurement.nrs, chl_level=measurement.chl_level,
                                                                note=measurement.note))
            except ValueError:
                pass

        return UserMeasurementsMessage(measurements=user_measurements,
                                       response=DefaultResponseMessage(code="200 OK", message="Measurements retrieved."))

    @endpoints.method(USER_ID_MESSAGE, UserMessagesMessage,
                      path="recipexServerApi/users/{id}/messages", http_method="GET", name="user.getMessages")
    def get_messages(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return UserMessagesMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                       message="User not existent."))

        messages_entities = Message.query(ancestor=user.key)

        user_messages = []

        for message in messages_entities:
            user_messages.append(MessageInfoMessage(id=message.key.id(), sender=message.sender,
                                                    receiver=message.receiver, message=message.message,
                                                    hasRead=message.hasRead, measurement=message.measurement))

        return UserMessagesMessage(user_messages=user_messages,
                                   response=DefaultResponseMessage(code="200 OK", message="Messages retrieved."))

    @endpoints.method(USER_ID_MESSAGE, UserMessagesMessage,
                      path="recipexServerApi/users/{id}/unread-messages", http_method="GET", name="user.hasUnreadMessages")
    def get_unread_messages(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return UserMessagesMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                       message="User not existent."))

        messages_entities = Message.query(ancestor=user.key)

        user_messages = []

        for message in messages_entities:
            if not message.hasRead:
                user_messages.append(MessageInfoMessage(id=message.key.id(), sender=message.sender,
                                                        receiver=message.receiver, message=message.message,
                                                        hasRead=message.hasRead, measurement=message.measurement))

        return UserMessagesMessage(user_messages=user_messages,
                                   response=DefaultResponseMessage(code="200 OK", message="Messages retrieved."))

    @endpoints.method(USER_ID_MESSAGE, UserRequestsMessage,
                      path="recipexServerApi/users/{id}/requests", http_method="GET", name="user.getRequests")
    def get_requests(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return UserRequestsMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                       message="User not existent."))

        if request.kind:
            if request.kind not in REQUEST_KIND:
                return UserRequestsMessage(response=DefaultResponseMessage(code="412 Precondition Failed",
                                                                           message="Kind not existent."))
            request_entities = Request.query(ancestor=user.key).filter(Request.kind == request.kind)
        else:
            request_entities = Request.query(ancestor=user.key)

        user_requests = []

        for request in request_entities:
            if request.kind == "RELATIVE":
                user_requests.append(RequestInfoMessage(id=request.key.id(), receiver=request.receiver.id(),
                                                        sender=request.sender.id(), message=request.message,
                                                        kind=request.kind, role=request.role))
            else:
                user_requests.append(RequestInfoMessage(id=request.key.id(), receiver=request.receiver.id(),
                                                        sender=request.sender.id(), message=request.message,
                                                        kind=request.kind, role=request.role,
                                                        caregiver=request.caregiver.id()))

        return UserRequestsMessage(requests=user_requests,
                                   response=DefaultResponseMessage(code="200 OK", message="Requests retrieved."))

    @endpoints.method(USER_ID_MESSAGE, UserRequestsMessage,
                      path="recipexServerApi/users/{id}/requests-pending", http_method="GET", name="user.getRequestsPending")
    def get_requests_pending(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return UserRequestsMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                       message="User not existent."))

        if request.kind:
            if request.kind not in REQUEST_KIND:
                return UserRequestsMessage(response=DefaultResponseMessage(code="412 Precondition Failed",
                                                                           message="Kind not existent."))
            request_entities = Request.query(ndb.AND(Request.sender == user.key,
                                                     Request.kind == request.kind))
        else:
            request_entities = Request.query(Request.sender == user.key)

        user_requests = []

        for request in request_entities:
            if request.kind == "RELATIVE":
                user_requests.append(RequestInfoMessage(id=request.key.id(), receiver=request.receiver.id(),
                                                        sender=request.sender.id(), message=request.message,
                                                        kind=request.kind, role=request.role))
            else:
                user_requests.append(RequestInfoMessage(id=request.key.id(), receiver=request.receiver.id(),
                                                        sender=request.sender.id(), message=request.message,
                                                        kind=request.kind, role=request.role,
                                                        caregiver=request.caregiver.id()))

        return UserRequestsMessage(requests=user_requests,
                                   response=DefaultResponseMessage(code="200 OK", message="Requests retrieved."))

    @endpoints.method(ADD_MEASUREMENT_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/measurements", http_method="POST", name="measurements.addMeasurement")
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

        new_measurement = Measurement(parent=user.key, date_time=date_time, kind=request.kind, note=request.note)

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

        return DefaultResponseMessage(code="201 Created", message="Measurement added.", payload=str(measurement_key.id()))

    @endpoints.method(UPDATE_MEASUREMENT_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/measurements/{id}", http_method="PUT", name="measurement.updateMeasurement")
    def update_measurement(self, request):
        RecipexServerApi.authentication_check()

        measurement = Key(User, request.user_id, Measurement, request.id).get()
        if not measurement:
            return DefaultResponseMessage(code="404 Not Found", message="Measurement not existent.")
        '''
        user_key = Key(User, request.user_id)
        if user_key != measurement.key.parent():
            return DefaultResponseMessage(code="401 Unauthorized", message="User unauthorized.")
        '''

        if request.date_time:
            try:
                date_time = datetime.strptime(request.date_time, "%Y-%m-%d %H:%M:%S")
                measurement.date_time = date_time
            except ValueError:
                return DefaultResponseMessage(code="400 Bad Request", message="Bad date_time format.")

        if request.kind not in MEASUREMENTS_KIND:
            return DefaultResponseMessage(code="412 Precondition Failed", message="Measurement kind not existent.")

        if request.kind != measurement.kind:
            return DefaultResponseMessage(code="412 Precondition Failed", message="Wrong measurement kind.")

        if request.note is not None:
            if request.note:
                measurement.note = request.note
            else:
                measurement.note = None

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
                measurement.chl_level = request.chl_level

        measurement.put()
        return DefaultResponseMessage(code="200 OK", message="Measurement updated.")

    @endpoints.method(MEASUREMENT_ID_MESSAGE, MeasurementInfoMessage,
                      path="recipexServerApi/users/{user_id}/measurements/{id}", http_method="GET", name="measurement.getMeasurement")
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

        date_time = datetime.strftime(measurement.date_time, "%Y-%m-%d %H:%M:%S")

        return MeasurementInfoMessage(date_time=date_time, kind=measurement.kind, systolic=measurement.systolic,
                                      diastolic=measurement.diastolic, bpm=measurement.bpm, spo2=measurement.spo2,
                                      respirations=measurement.respirations, degrees=measurement.degrees,
                                      hgt=measurement.hgt, nrs=measurement.nrs, chl_level=measurement.chl_level,
                                      note=measurement.note, response=DefaultResponseMessage(code="200 OK",
                                                                                             message="Measurement info retrieved."))

    @endpoints.method(MEASUREMENT_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/measurements/{id}", http_method="DELETE", name="measurement.deleteMeasurement")
    def delete_measurement(self, request):
        RecipexServerApi.authentication_check()
        measurement = Key(User, request.user_id, Measurement, request.id).get()
        if not measurement:
            return DefaultResponseMessage(code="404 Not Found", message="Measurement not existent.")
        user_key = Key(User, request.user_id)
        if user_key != measurement.key.parent():
            return DefaultResponseMessage(code="401 Unauthorized", message="User unauthorized.")

        measurement.key.delete()
        return DefaultResponseMessage(code="200 OK", message="Measurement deleted.")

    @endpoints.method(MESSAGE_SEND_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{receiver}/messages", http_method="POST", name="message.sendMessage")
    def send_message(self, request):
        RecipexServerApi.authentication_check()

        sender = Key(User, request.sender).get()
        if not sender:
            return DefaultResponseMessage(code="404 Not Found", message="Sender not existent.")

        receiver = Key(User, request.receiver).get()
        if not receiver:
            return DefaultResponseMessage(code="404 Not Found", message="Receiver not existent.")

        measurement_key = None
        if not request.measurement:
            measurement_key = Key(Measurement, request.measurement)
            measurement = measurement_key.get()
            if not measurement:
                return DefaultResponseMessage(code="404 Not Found", message="Measurement not existent.")

        message = Message(father=receiver.key, sender=sender.key, receiver=receiver.key, message=request.message,
                          hasRead=False, measurement=measurement_key)

        message.put()
        return DefaultResponseMessage(code="201 Created", message="Message sent.", payload=str(message.key.id()))

    @endpoints.method(MESSAGE_ID_MESSAGE, MessageInfoMessage,
                      path="recipexServerApi/users/{user_id}/messages/{id}", http_method="GET", name="message.getMessage")
    def get_message(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return MessageInfoMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                      message="User not existent."))

        message = Key(User, request.id).get()
        if not message:
            return MessageInfoMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                      message="Message not existent."))

        if message.receiver != user.key:
            return MessageInfoMessage(response=DefaultResponseMessage(code="412 Precondition Failed",
                                                                      message="User not the receiver."))

        return MessageInfoMessage(sender=message.sender, receiver=message.receiver,
                                  message=message.message, hasRead=message.hasRead, measurement=message.measurement,
                                  response=DefaultResponseMessage(code="200 OK", message="Message info retrieved."))

    @endpoints.method(MESSAGE_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/messages/{id}", http_method="PUT", name="message.readMessage")
    def read_message(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        message = Key(User, request.id).get()
        if not message:
            return DefaultResponseMessage(code="404 Not Found", message="Message not existent.")

        if message.receiver != user.key:
            return DefaultResponseMessage(code="412 Precondition Failed", message="User not the receiver.")

        message.hasRead = True
        message.put()
        return DefaultResponseMessage(code="200 OK", message="Message read.")

    @endpoints.method(MESSAGE_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/messages/{id}", http_method="DELETE", name="message.deleteMessage")
    def delete_message(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        message = Key(User, request.id).get()
        if not message:
            return DefaultResponseMessage(code="404 Not Found", message="Message not existent.")

        if message.receiver != user.key:
            return DefaultResponseMessage(code="412 Precondition Failed", message="User not the receiver.")

        message.key.delete()
        return DefaultResponseMessage(code="200 OK", message="Message deleted.")

    @endpoints.method(REQUEST_SEND_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{receiver}/requests", http_method="POST", name="request.sendRequest")
    def send_request(self, request):
        RecipexServerApi.authentication_check()

        sender = Key(User, request.sender).get()
        if not sender:
            return DefaultResponseMessage(code="404 Not Found", message="Sender not existent.")

        receiver = Key(User, request.receiver).get()
        if not receiver:
            return DefaultResponseMessage(code="404 Not Found", message="Receiver not existent.")

        if request.kind not in REQUEST_KIND:
            return DefaultResponseMessage(code="412 Precondition Failed", message="Kind not existent.")

        old_request = Request.query(ancestor=receiver.key).filter(ndb.AND(Request.sender == sender.key,
                                                                          Request.kind == request.kind)).get()
        if old_request:
            return DefaultResponseMessage(code="412 Precondition Failed", message="Request already existent.")

        caregiver_key = None
        if request.kind == "CAREGIVER" or request.kind == "PC_PHYSICIAN" or request.kind == "V_NURSE":
            if request.role not in ROLE_TYPE:
                return DefaultResponseMessage(code="412 Precondition Failed", message="Role not existent.")
            # Il paziente ha mandato la richiesta: il caregiver e' il receiver
            if request.role == "PATIENT":
                patient_key = sender.key
                caregiver = Caregiver.query(ancestor=receiver.key).get()
                if not caregiver:
                    return DefaultResponseMessage(code="412 Precondition Failed", message="Receiver not a caregiver.")
            else:
                patient_key = receiver.key
                caregiver = Caregiver.query(ancestor=sender.key).get()
                if not caregiver:
                    return DefaultResponseMessage(code="412 Precondition Failed", message="Sender not a caregiver.")
            if caregiver.patients and patient_key.id() in caregiver.patients.keys():
                return DefaultResponseMessage(code="412 Precondition Failed", message="Already a patient.")
            caregiver_key = caregiver.key
        else:
            if receiver.relatives and sender.key.id() in receiver.relatives.keys():
                return DefaultResponseMessage(code="412 Precondition Failed", message="Already a relative.")

        new_request = Request(parent=receiver.key, sender=sender.key, receiver=receiver.key,
                              kind=request.kind, message=request.message, role=request.role, caregiver=caregiver_key)

        new_request.put()
        return DefaultResponseMessage(code="201 Created", message="Request sent.", payload=str(new_request.key.id()))

    @endpoints.method(REQUEST_ID_MESSAGE, RequestInfoMessage,
                      path="recipexServerApi/users/{user_id}/requests/{id}", http_method="GET", name="request.getRequest")
    def get_request(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return RequestInfoMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                      message="User not existent."))
        usr_request = Key(User, request.user_id, Request, request.id).get()
        if not usr_request:
            return RequestInfoMessage(response=DefaultResponseMessage(code="404 Not Found",
                                                                      message="Request not existent."))

        if usr_request.receiver != user.key:
            return RequestInfoMessage(response=DefaultResponseMessage(code="412 Precondition Failed",
                                                                      message="User not the receiver."))

        return RequestInfoMessage(sender=usr_request.sender.id(), receiver=usr_request.receiver.id(),
                                  kind=usr_request.kind, message=usr_request.message,
                                  role=usr_request.role, caregiver=usr_request.caregiver.id(),
                                  response=DefaultResponseMessage(code="200 OK", message="Request info retrieved."))

    @endpoints.method(REQUEST_ANSWER_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/requests/{id}", http_method="PUT", name="request.answerRequest")
    def answer_request(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        usr_request = Key(User, request.user_id, Request, request.id).get()
        if not usr_request:
            return DefaultResponseMessage(code="404 Not Found", message="Request not existent.")

        if usr_request.receiver != user.key:
            return DefaultResponseMessage(code="412 Precondition Failed", message="User not the receiver.")

        if request.answer:
            if usr_request.kind == "RELATIVE":
                sender = usr_request.sender.get()
                if not sender:
                    return DefaultResponseMessage(code="412 Precondition Failed", message="Sender not existent.")
                if not user.relatives:
                    user.relatives = {sender.key.id(): sender.key}
                else:
                    user.relatives[sender.key.id()] = sender.key
                if not sender.relatives:
                    sender.relatives = {user.key.id(): user.key}
                else:
                    sender.relatives[user.key.id()] = user.key
                user.put()
                sender.put()
            else:
                if usr_request.role == "PATIENT":
                    patient = usr_request.sender.get()
                else:
                    patient = usr_request.receiver.get()
                if not patient:
                    return DefaultResponseMessage(code="412 Precondition Failed", message="Patient not existent.")
                caregiver = usr_request.caregiver.get()
                if not caregiver:
                    return DefaultResponseMessage(code="412 Precondition Failed", message="Caregiver not existent.")

                if usr_request.kind == "CAREGIVER":
                    patient.caregivers[caregiver.key.id()] = caregiver.key
                elif usr_request.kind == "PC_PHYSICIAN":
                    patient.pc_physician = caregiver.key
                else:
                    patient.visiting_nurse = caregiver.key

                caregiver.patients[patient.key.id()] = patient.key

                patient.put()
                caregiver.put()

        usr_request.key.delete()
        return DefaultResponseMessage(code="200 OK", message="Answer received.")

    @endpoints.method(REQUEST_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/requests/{id}", http_method="DELETE", name="request.deleteRequest")
    def delete_request(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return DefaultResponseMessage(code="404 Not Found", message="User not existent.")

        usr_request = Key(User, request.user_id, Request, request.id).get()
        if not usr_request:
            return DefaultResponseMessage(code="404 Not Found", message="Request not existent.")

        sender = Key(User, request.sender).get()
        if not sender:
            return DefaultResponseMessage(code="404 Not Found", message="Sender not existent.")
        if usr_request.sender != sender.key:
            return DefaultResponseMessage(code="412 Precondition Failed", message="Sender not the sender.")

        if usr_request.receiver != user.key:
            return DefaultResponseMessage(code="412 Precondition Failed", message="User not the receiver.")

        usr_request.key.delete()
        return DefaultResponseMessage(code="200 OK", message="Request deleted.")

    @classmethod
    def authentication_check(cls):
        current_user = endpoints.get_current_user()
        if not current_user:
            raise endpoints.UnauthorizedException('Invalid token.')

        # current_user2 = oauth.get_current_user('https://www.googleapis.com/auth/userinfo.email')

        # logging.info(current_user.__dict__)
        # logging.info(current_user2.__dict__)
        # logging.info(endpoints.API_EXPLORER_CLIENT_ID)

        if current_user.email() != "recipex.app@gmail.com":
            raise endpoints.UnauthorizedException('User Unauthorized')

APPLICATION = endpoints.api_server([RecipexServerApi])
