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
import pytz

import logging
import credentials

# TODO Controlla bene tutti i set: quando inserisci devi prima controllare... e non lo fai quasi mai!!!

# CONSTANTS
MEASUREMENTS_KIND = ["BP", "HR", "RR", "SpO2", "HGT", "TMP", "PAIN", "CHL"]
REQUEST_KIND = ["RELATIVE", "CAREGIVER", "PC_PHYSICIAN", "V_NURSE"]
ROLE_TYPE = ["PATIENT", "CAREGIVER"]
PRESCRIPTION_KIND = ["PILL", "SACHET", "VIAL", "CREAM" "OTHER"]

# HTTP CODES
OK = "200 OK"
CREATED = "201 Created"
NOT_FOUND = "404 Not Found"
PRECONDITION_FAILED = "412 Precondition Failed"
BAD_REQUEST = "400 Bad Request"

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
    pic = ndb.StringProperty(required=True)
    sex = ndb.StringProperty(required=True)
    city = ndb.StringProperty()
    address = ndb.StringProperty()
    personal_num = ndb.StringProperty()
    relatives = ndb.PickleProperty(compressed=True, default={})
    pc_physician = ndb.KeyProperty()
    visiting_nurse = ndb.KeyProperty()
    caregivers = ndb.PickleProperty(compressed=True, default={})


class Caregiver(ndb.Model):
    field = ndb.StringProperty(required=True)
    years_exp = ndb.IntegerProperty()
    place = ndb.StringProperty()
    business_num = ndb.StringProperty()
    bio = ndb.StringProperty()
    available = ndb.StringProperty()
    patients = ndb.PickleProperty(compressed=True, default={})


class Measurement(ndb.Model):
    date_time = ndb.DateTimeProperty(required=True)
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
    chl_level = ndb.FloatProperty()


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
    calendarId = ndb.StringProperty()
    role = ndb.StringProperty()
    caregiver = ndb.KeyProperty()
    isPending = ndb.BooleanProperty()
    message = ndb.StringProperty()


class ActiveIngredient(ndb.Model):
    name = ndb.StringProperty(required=True)


# TODO Aggiungere Orario e Giorni di assunzione su Google Calendar
class Prescription(ndb.Model):
    name = ndb.StringProperty(required=True)
    active_ingr_key = ndb.KeyProperty(required=True)
    active_ingr_name = ndb.StringProperty(required=True)
    kind = ndb.StringProperty(required=True)
    dose = ndb.IntegerProperty(required=True)
    units = ndb.StringProperty(required=True)
    quantity = ndb.IntegerProperty(required=True)
    recipe = ndb.BooleanProperty(required=True)
    pil = ndb.StringProperty()
    caregiver = ndb.KeyProperty()
    seen = ndb.BooleanProperty()


# MESSAGE CLASSES

class RegisterUserMessage(messages.Message):
    email = messages.StringField(1, required=True)
    name = messages.StringField(2, required=True)
    surname = messages.StringField(3, required=True)
    birth = messages.StringField(4, required=True)
    pic = messages.StringField(5, required=True)
    sex = messages.StringField(6, required=True)
    city = messages.StringField(7)
    address = messages.StringField(8)
    personal_num = messages.StringField(9)
    field = messages.StringField(10)
    years_exp = messages.IntegerField(11)
    place = messages.StringField(12)
    business_num = messages.StringField(13)
    bio = messages.StringField(14)
    available = messages.StringField(15)


class DefaultResponseMessage(messages.Message):
    code = messages.StringField(1)
    message = messages.StringField(2)
    payload = messages.StringField(3)
    user = messages.MessageField(RegisterUserMessage, 4)


class UpdateUserMessage(messages.Message):
    # id = messages.IntegerField(1, required=True)
    name = messages.StringField(1)
    surname = messages.StringField(2)
    birth = messages.StringField(3)
    sex = messages.StringField(4)
    city = messages.StringField(5)
    address = messages.StringField(6)
    personal_num = messages.StringField(7)
    field = messages.StringField(8)
    years_exp = messages.IntegerField(9)
    place = messages.StringField(10)
    business_num = messages.StringField(11)
    bio = messages.StringField(12)
    available = messages.StringField(13)


UPDATE_USER_MESSAGE = endpoints.ResourceContainer(UpdateUserMessage,
                                                  id=messages.IntegerField(2, required=True))

'''
class UserIdMessage(messages.Message):
    # id = messages.IntegerField(1, required=True)
    kind = messages.StringField(1)
    date_time = messages.StringField(2)
'''

USER_ID_MESSAGE = endpoints.ResourceContainer(message_types.VoidMessage,
                                              id=messages.IntegerField(2, required=True),
                                              # is_caregiver=messages.BooleanField(3),
                                              profile_id=messages.IntegerField(3),
                                              fetch=messages.IntegerField(4),
                                              kind=messages.StringField(5),
                                              date_time=messages.StringField(6))


USER_UPDATE_RELATION_INFO = endpoints.ResourceContainer(message_types.VoidMessage,
                                                        id=messages.IntegerField(2, required=True),
                                                        relation_id=messages.IntegerField(3, required=True),
                                                        kind=messages.StringField(4, required=True),
                                                        role=messages.StringField(5))


class UserMainInfoMessage(messages.Message):
    id = messages.IntegerField(1)
    caregiver_id = messages.IntegerField(2)
    name = messages.StringField(3)
    surname = messages.StringField(4)
    email = messages.StringField(5)
    pic = messages.StringField(6)
    field = messages.StringField(7)


class UserListOfUsersMessage(messages.Message):
    users = messages.MessageField(UserMainInfoMessage, 1, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 2)


class UserInfoMessage(messages.Message):
    id = messages.IntegerField(1)
    email = messages.StringField(2)
    name = messages.StringField(3)
    surname = messages.StringField(4)
    birth = messages.StringField(5)
    pic = messages.StringField(6)
    sex = messages.StringField(7)
    city = messages.StringField(8)
    address = messages.StringField(9)
    personal_num = messages.StringField(10)
    # relatives = messages.IntegerField(11, repeated=True)
    relatives = messages.MessageField(UserMainInfoMessage, 11, repeated=True)
    # pc_physician = messages.IntegerField(12)
    pc_physician = messages.MessageField(UserMainInfoMessage, 12)
    # visiting_nurse = messages.IntegerField(13)
    visiting_nurse = messages.MessageField(UserMainInfoMessage, 13)
    # caregivers = messages.IntegerField(14, repeated=True)
    caregivers = messages.MessageField(UserMainInfoMessage, 14, repeated=True)
    field = messages.StringField(15)
    place = messages.StringField(16)
    years_exp = messages.IntegerField(17)
    business_num = messages.StringField(18)
    bio = messages.StringField(19)
    available = messages.StringField(20)
    # patients = messages.IntegerField(21, repeated=True)
    patients = messages.MessageField(UserMainInfoMessage, 21, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 22)


class UserRelationsMessage(messages.Message):
    is_relative = messages.BooleanField(1)
    is_relative_request = messages.BooleanField(2)
    is_pc_physician = messages.BooleanField(3)
    is_pc_physician_request = messages.BooleanField(4)
    is_visiting_nurse = messages.BooleanField(5)
    is_visiting_nurse_request = messages.BooleanField(6)
    is_caregiver = messages.BooleanField(7)
    is_caregiver_request = messages.BooleanField(8)
    is_patient = messages.BooleanField(9)
    is_patient_request = messages.BooleanField(10)
    response = messages.MessageField(DefaultResponseMessage, 11)


class AddMeasurementMessage(messages.Message):
    # user_id = messages.IntegerField(1, required=True)
    # date_time = messages.StringField(1, required=True)
    kind = messages.StringField(1, required=True)
    # Blood Pressure (BP)
    systolic = messages.IntegerField(2)
    diastolic = messages.IntegerField(3)
    # Heart Rate (HR)
    bpm = messages.IntegerField(4)
    # Respiratory Rate (RR)
    respirations = messages.IntegerField(5)
    # Pulse Oximetry (SpO2)
    spo2 = messages.FloatField(6)
    # Blood Sugar (HGT)
    hgt = messages.FloatField(7)
    # Body Temperature (T)
    degrees = messages.FloatField(8)
    # Pain (P)
    nrs = messages.IntegerField(9)
    # Cholesterol
    chl_level = messages.FloatField(10)
    note = messages.StringField(11)


ADD_MEASUREMENT_MESSAGE = endpoints.ResourceContainer(AddMeasurementMessage,
                                                      user_id=messages.IntegerField(2, required=True))


class UpdateMeasurementMessage(messages.Message):
    # id = messages.IntegerField(1, required=True)
    # user_id = messages.IntegerField(2, required=True)
    # date_time = messages.StringField(3)
    kind = messages.StringField(1, required=True)
    # Blood Pressure (BP)
    systolic = messages.IntegerField(2)
    diastolic = messages.IntegerField(3)
    # Heart Rate (HR)
    bpm = messages.IntegerField(4)
    # Respiratory Rate (RR)
    respirations = messages.IntegerField(5)
    # Pulse Oximetry (SpO2)
    spo2 = messages.FloatField(6)
    # Blood Sugar (HGT)
    hgt = messages.FloatField(7)
    # Body Temperature (T)
    degrees = messages.FloatField(8)
    # Pain (P)
    nrs = messages.IntegerField(9)
    # Cholesterol
    chl_level = messages.FloatField(10)
    note = messages.StringField(11)


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
    chl_level = messages.FloatField(12)
    note = messages.StringField(13)
    response = messages.MessageField(DefaultResponseMessage, 14)


class UserMeasurementsMessage(messages.Message):
    measurements = messages.MessageField(MeasurementInfoMessage, 1, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 2)


'''
class UserRelativeCaregiverMessage(messages.Message):
    id = messages.IntegerField(1, required=True)
    to_add = messages.IntegerField(2, repeated=True)
    to_del = messages.IntegerField(3, repeated=True)


class UserFirstAidInfoMessage(messages.Message):
    id = messages.IntegerField(1, required=True)
    pc_physician = messages.IntegerField(2)
    visiting_nurse = messages.IntegerField(3)
'''


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
    sender_pic = messages.StringField(7)
    response = messages.MessageField(DefaultResponseMessage, 8)


class UserMessagesMessage(messages.Message):
    user_messages = messages.MessageField(MessageInfoMessage, 1, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 2)


class RequestSendMessage(messages.Message):
    sender = messages.IntegerField(1, required=True)
    # receiver = messages.IntegerField(2, required=True)
    kind = messages.StringField(2, required=True)
    role = messages.StringField(3)
    calendarId = messages.StringField(4)
    message = messages.StringField(5)


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
    pending = messages.BooleanField(8)
    sender_pic = messages.StringField(9)
    sender_name = messages.StringField(10)
    sender_surname = messages.StringField(11)
    calendarId = messages.StringField(12)
    response = messages.MessageField(DefaultResponseMessage, 13)


class UserRequestsMessage(messages.Message):
    requests = messages.MessageField(RequestInfoMessage, 1, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 2)


class ActiveIngredientMessage(messages.Message):
    name = messages.StringField(1, required=True)
    id = messages.IntegerField(2)
    response = messages.MessageField(DefaultResponseMessage, 3)


ACTIVE_INGREDIENT_ID_MESSAGE = endpoints.ResourceContainer(message_types.VoidMessage,
                                                           id=messages.StringField(1, required=True))


class ActiveIngredientsMessage(messages.Message):
    active_ingredients = messages.MessageField(ActiveIngredientMessage, 1, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 2)


class AddPrescriptionMessage(messages.Message):
    name = messages.StringField(1, required=True)
    active_ingredient = messages.IntegerField(2, required=True)
    kind = messages.StringField(3, required=True)
    dose = messages.IntegerField(4, required=True)
    units = messages.StringField(5, required=True)
    quantity = messages.IntegerField(6, required=True)
    recipe = messages.BooleanField(7, required=True)
    pil = messages.StringField(8)
    caregiver = messages.IntegerField(9)


ADD_PRESCRIPTION_MESSAGE = endpoints.ResourceContainer(AddPrescriptionMessage,
                                                       id=messages.IntegerField(2, required=True))


PRESCRIPTION_ID_MESSAGE = endpoints.ResourceContainer(message_types.VoidMessage,
                                                      id=messages.IntegerField(2, required=True),
                                                      user_id=messages.IntegerField(3, required=True))


class PrescriptionInfoMessage(messages.Message):
    id = messages.IntegerField(1)
    name = messages.StringField(2)
    active_ingr_key = messages.IntegerField(3)
    active_ingr_name = messages.StringField(4)
    kind = messages.StringField(5)
    dose = messages.IntegerField(6)
    units = messages.StringField(7)
    quantity = messages.IntegerField(8)
    recipe = messages.BooleanField(9)
    pil = messages.StringField(10)
    caregiver_id = messages.IntegerField(11)
    caregiver_user_id = messages.IntegerField(12)
    caregiver_name = messages.StringField(13)
    caregiver_surname = messages.StringField(14)
    caregiver_mail = messages.StringField(15)
    caregiver_job = messages.StringField(16)
    seen = messages.BooleanField(17)
    response = messages.MessageField(DefaultResponseMessage, 18)


class UserPrescriptionsMessage(messages.Message):
    prescriptions = messages.MessageField(PrescriptionInfoMessage, 1, repeated=True)
    response = messages.MessageField(DefaultResponseMessage, 2)


class UserUnseenInfoMessage(messages.Message):
    num_messages = messages.IntegerField(1)
    num_requests = messages.IntegerField(2)
    num_prescriptions = messages.IntegerField(3)
    response = messages.MessageField(DefaultResponseMessage, 4)


@endpoints.api(name="recipexServerApi", version="v1",
               hostname="recipex-1281.appspot.com",
               allowed_client_ids=[credentials.WEB_CLIENT_ID,
                                   credentials.ANDROID_CLIENT_ID,
                                   credentials.DEBUG_ID,
                                   credentials.DEBUG_FAB_ID,
                                   credentials.DEBUG_SARA_ID,
                                   endpoints.API_EXPLORER_CLIENT_ID],
               audiences=[credentials.ANDROID_AUDIENCE],
               scopes=[endpoints.EMAIL_SCOPE])
class RecipexServerApi(remote.Service):
    @endpoints.method(message_types.VoidMessage, DefaultResponseMessage,
                      path='recipexServerApi/hello', http_method="GET", name="hello.helloWorld")
    def hello_world(self, request):
        RecipexServerApi.authentication_check()
        date = datetime.utcnow()
        local_tz = pytz.timezone('Europe/Rome')
        local_dt = date.replace(tzinfo=pytz.utc).astimezone(local_tz)
        logging.info(date)
        logging.info(local_dt)

        return DefaultResponseMessage(message="Hello World!")

    @endpoints.method(message_types.VoidMessage, UserListOfUsersMessage,
                      path="recipexServerApi/users", http_method="GET", name="user.getUsers")
    def get_users(self, request):
        RecipexServerApi.authentication_check()
        users = User.query()

        users_info = []
        for user in users:
            user_info = UserMainInfoMessage(id=user.key.id(),
                                            name=user.name,
                                            surname=user.surname,
                                            email=user.email,
                                            pic=user.pic)

            caregiver = Caregiver.query(ancestor=user.key).get()
            if caregiver:
                user_info.caregiver_id = caregiver.key.id()
                user_info.field = caregiver.field

            users_info.append(user_info)

        return RecipexServerApi.return_response(code=OK,
                                                message="Users info retrieved.",
                                                response=UserListOfUsersMessage(
                                                    users=users_info,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Users info retrieved.")))

    @endpoints.method(RegisterUserMessage, DefaultResponseMessage,
                      path="recipexServerApi/users", http_method="POST", name="user.registerUser")
    def register_user(self, request):
        RecipexServerApi.authentication_check()

        user_query = User.query(User.email == request.email).get()

        # if User.query(User.email == request.email).count() > 0:
        if user_query:
            user_body = RegisterUserMessage(email=user_query.email, name=user_query.name, surname=user_query.surname,
                                            pic=user_query.pic, birth=user_query.birth, sex=user_query.sex,
                                            city=user_query.city, address=user_query.address,
                                            personal_num=user_query.personal_num)
            caregiver_query = Caregiver.query(ancestor=user_query.key).get()
            if caregiver_query:
                user_body.field = caregiver_query.field
                user_body.years_exp = caregiver_query.years_exp
                user_body.place = caregiver_query.place
                user_body.business_num = caregiver_query.business_num
                user_body.bio = caregiver_query.bio
                user_body.available = caregiver_query.available
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="User already existent.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="User already existent.",
                                                                                    payload=str(user_query.key.id()),
                                                                                    user=user_body))

        if request.years_exp or request.place or request.business_num or request.bio or request.available:
            if not request.field:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Field is missing.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Field is missing."))

        try:
            birth = datetime.strptime(request.birth, "%Y-%m-%d")
        except ValueError:
            return RecipexServerApi.return_response(code=BAD_REQUEST,
                                                    message="Bad birth format.",
                                                    response=DefaultResponseMessage(code=BAD_REQUEST,
                                                                                    message="Bad birth format."))

        new_user = User(email=request.email, name=request.name, surname=request.surname, pic=request.pic,
                        birth=birth, sex=request.sex, city=request.city, address=request.address,
                        personal_num=request.personal_num, relatives={}, caregivers={})
        user_key = new_user.put()

        # Field is the required field to be a caregiver
        if request.field:
            new_caregiver = Caregiver(parent=user_key, field=request.field, years_exp=request.years_exp,
                                      place=request.place, business_num=request.business_num,
                                      bio=request.bio, available=request.available, patients={})
            new_caregiver.put()

        return RecipexServerApi.return_response(code=CREATED,
                                                message="User registered.",
                                                response=DefaultResponseMessage(code=CREATED,
                                                                                message="User registered.",
                                                                                payload=str(user_key.id())))

    @endpoints.method(UPDATE_USER_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}", http_method="PUT", name="user.updateUser")
    def update_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent."))

        if request.name:
            user.name = request.name
        if request.surname:
            user.surname = request.surname
        if request.birth:
            try:
                birth = datetime.strptime(request.birth, "%Y-%m-%d")
                user.birth = birth
            except ValueError:
                return RecipexServerApi.return_response(code=BAD_REQUEST,
                                                        message="Bad birth format.",
                                                        response=DefaultResponseMessage(code=BAD_REQUEST,
                                                                                        message="Bad birth format."))
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
        if request.personal_num is not None:
            if request.personal_num:
                user.personal_num = request.personal_num
            else:
                user.personal_num = None
        user.put()

        if request.field or request.years_exp or request.place or\
           request.business_num or request.bio or request.available:
            caregiver = Caregiver.query(ancestor=user.key).get()
            if not caregiver:
                return RecipexServerApi.return_response(code="412 Not Found",
                                                        message="User not a caregiver.",
                                                        response=DefaultResponseMessage(code="412 Not Found",
                                                                                        message="User not a caregiver."))
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
            if request.business_num is not None:
                if request.business_num:
                    caregiver.business_num = request.business_num
                else:
                    caregiver.business_num = None
            if request.bio is not None:
                if request.bio:
                    caregiver.bio = request.bio
                else:
                    caregiver.bio = None
            if request.available is not None:
                if request.available:
                    caregiver.available = request.available
                else:
                    caregiver.available = None
            caregiver.put()

        return RecipexServerApi.return_response(code=OK,
                                                message="User updated.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="User updated."))

    @endpoints.method(USER_ID_MESSAGE, UserInfoMessage,
                      path="recipexServerApi/users/{id}", http_method="GET", name="user.getUser")
    def get_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        birth = datetime.strftime(user.birth, "%Y-%m-%d")

        usr_info = UserInfoMessage(email=user.email, name=user.name, surname=user.surname,
                                   pic=user.pic, birth=birth, sex=user.sex, city=user.city,
                                   address=user.address, personal_num=user.personal_num,
                                   response=DefaultResponseMessage(code=OK,
                                                                   message="User info retrieved."))

        if user.pc_physician:
            pc_physician_entity = user.pc_physician.get()
            pc_physician_usr = pc_physician_entity.key.parent().get()
            # pc_physician_entity = Caregiver.query(ancestor=user.pc_physician).get()
            # pc_physician_usr = user.pc_physician.get()
            if pc_physician_entity and pc_physician_usr:
                usr_info.pc_physician = UserMainInfoMessage(id=pc_physician_usr.key.id(),
                                                            caregiver_id=pc_physician_entity.key.id(),
                                                            name=pc_physician_usr.name,
                                                            surname=pc_physician_usr.surname,
                                                            email=pc_physician_usr.email,
                                                            pic=pc_physician_usr.pic,
                                                            field=pc_physician_entity.field)

        if user.visiting_nurse:
            visiting_nurse_entity = user.visiting_nurse.get()
            visiting_nurse_usr = visiting_nurse_entity.key.parent().get()
            # visiting_nurse_entity = Caregiver.query(ancestor=user.visiting_nurse).get()
            # visiting_nurse_usr = user.visiting_nurse.get()
            if visiting_nurse_entity and visiting_nurse_usr:
                usr_info.visiting_nurse = UserMainInfoMessage(id=visiting_nurse_usr.key.id(),
                                                              caregiver_id=visiting_nurse_entity.key.id(),
                                                              name=visiting_nurse_usr.name,
                                                              surname=visiting_nurse_usr.surname,
                                                              email=visiting_nurse_usr.email,
                                                              pic=visiting_nurse_usr.pic,
                                                              field=visiting_nurse_entity.field)

        if user.relatives:
            user_relatives = []
            for relative in user.relatives.values():
                relative_entity = relative.get()
                if relative_entity:
                    user_relatives.append(UserMainInfoMessage(id=relative_entity.key.id(),
                                                              name=relative_entity.name,
                                                              surname=relative_entity.surname,
                                                              email=relative_entity.email,
                                                              pic=relative_entity.pic))
            usr_info.relatives = user_relatives

        if user.caregivers:
            user_caregivers = []
            for caregiver in user.caregivers.values():
                caregiver_entity = caregiver.get()
                caregiver_usr = caregiver_entity.key.parent().get()
                if caregiver_entity and caregiver_usr:
                    user_caregivers.append(UserMainInfoMessage(id=caregiver_usr.key.id(),
                                                               caregiver_id=caregiver_entity.key.id(),
                                                               name=caregiver_usr.name,
                                                               surname=caregiver_usr.surname,
                                                               email=caregiver_usr.email,
                                                               pic=caregiver_usr.pic,
                                                               field=caregiver_entity.field))
            usr_info.caregivers = user_caregivers

        caregiver = Caregiver.query(ancestor=user.key).get()
        if caregiver:
            usr_info.field = caregiver.field
            usr_info.years_exp = caregiver.years_exp
            usr_info.place = caregiver.place
            usr_info.business_num = caregiver.business_num
            usr_info.bio = caregiver.bio
            usr_info.available = caregiver.available
            if caregiver.patients:
                user_patients = []
                for patient in caregiver.patients.values():
                    patient_entity = patient.get()
                    if patient_entity:
                        user_patients.append(UserMainInfoMessage(id=patient_entity.key.id(),
                                                                 name=patient_entity.name,
                                                                 surname=patient_entity.surname,
                                                                 email=patient_entity.email,
                                                                 pic=patient_entity.pic))
                usr_info.patients = user_patients

        return RecipexServerApi.return_response(code=OK,
                                                message="User info retrieved.",
                                                response=usr_info)

    @endpoints.method(USER_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}", http_method="DELETE", name="user.deleteUser")
    def delete_user(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent."))
        # TODO Gestire le rimozioni in cascata (Misurazioni, Familiari, Caregiver, exc.)
        if user.pc_physician is not None:
            pc_physician = user.pc_physician.get()
            if pc_physician is not None:
                if user.key.id() in pc_physician.patients.keys():
                    del pc_physician.patients[user.key.id()]
                    pc_physician.put()
        if user.visiting_nurse is not None:
            visiting_nurse = user.visiting_nurse.get()
            if visiting_nurse is not None:
                if user.key.id() in visiting_nurse.patients.keys():
                    del visiting_nurse.patients[user.key.id()]
                    visiting_nurse.put()
        if user.caregivers:
            for caregiver_entity in user.caregivers.values():
                # caregiver = user.caregivers[caregiver_key].get()
                caregiver = caregiver_entity.get()
                if caregiver is not None:
                    if user.key.id() in caregiver.patients.keys():
                        del caregiver.patients[user.key.id()]
                        caregiver.put()
        if user.relatives:
            for relative_entity in user.relatives.keys():
                # relative = user.relatives[relative_key].get()
                relative = relative_entity.get()
                if relative is not None:
                    if user.key.id() in relative.relatives.keys():
                        del relative.relatives[user.key.id()]
                        relative.put()
        measurements = Measurement.query(ancestor=user.key)
        if measurements:
            for measurement in measurements:
                measurement.key.delete()
        usr_messages_rcvd = Message.query(ancestor=user.key)
        if usr_messages_rcvd:
            for message in usr_messages_rcvd:
                message.key.delete()
        usr_messages_sent = Message.query(Message.sender == user.key)
        if usr_messages_sent:
            for message in usr_messages_sent:
                message.key.delete()
        requests_rcvd = Request.query(ancestor=user.key)
        if requests_rcvd:
            for request in requests_rcvd:
                request.key.delete()
        requests_sent = Request.query(Request.sender == user.key)
        if requests_sent:
            for request in requests_sent:
                request.key.delete()
        prescriptions = Prescription.query(ancestor=user.key)
        if prescriptions:
            for prescription in prescriptions:
                prescription.key.delete()

        caregiver = Caregiver.query(ancestor=user.key).get()
        if caregiver is not None:
            if caregiver.patients:
                for patient_key in caregiver.patients.keys():
                    patient = caregiver.patients[patient_key].get()
                    if patient is not None:
                        if user.key.id() in patient.caregivers.keys():
                            del patient.caregivers[caregiver.key.id()]
                            patient.put()
            caregiver.key.delete()

        user.key.delete()
        return RecipexServerApi.return_response(code=OK,
                                                message="User deleted.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="User deleted."))

    '''
    @endpoints.method(UserRelativeCaregiverMessage, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/relatives", http_method="PATCH", name="user.updateRelatives")
    def update_relatives(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code=NOT_FOUND, message="User not existent.")

        relatives = {}
        if not user.relatives:
            relatives = user.relatives
        # TODO Gestire la responsabilita doppia sui dizionari (Paziente-Familiare)

        # for relative in range(len(request.set)):
        #     If already present, means remove
        #     if relative in relatives:
        #         del relatives[relative]
        #     If not present, means add
        #     else:
        #         relative_key = Key(User, relative)
        #         if not relative_key.get():
        #             return DefaultResponseMessage(code=NOT_FOUND, message="User(s) not existent.")
        #     relatives[relative] = relative_key

        for relative in range(len(request.to_add)):
            if relative not in relatives:
                relative_key = Key(User, relative)
                if not relative_key.get():
                    return DefaultResponseMessage(code=NOT_FOUND, message="User(s) not existent.")
                relatives[relative] = relative_key

        for relative in range(len(request.to_del)):
            if relative in relatives:
                del relatives[relative]

        user.relatives = relatives
        user.put()
        return DefaultResponseMessage(code=OK, message="Relatives updated.")

    @endpoints.method(UserRelativeCaregiverMessage, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/caregivers", http_method="PATCH", name="user.updateCaregivers")
    def update_caregivers(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code=NOT_FOUND, message="User not existent.")

        caregivers = {}
        if not user.caregivers:
            caregivers = user.caregivers
        # TODO Gestire la responsabilita doppia trai dizionari (Paziente-Caregiver)

        # for caregiver in range(len(request.set)):
        #     If already present, means remove
        #     if caregiver in caregivers:
        #         del caregivers[caregiver]
        #     If not present, means add
        #     else:
        #         caregiver_key = Key(User, caregiver)
        #         if not caregiver_key.get():
        #             return DefaultResponseMessage(code=NOT_FOUND, message="Caregiver(s) not existent.")
        #     caregivers[caregiver] = caregiver_key

        for caregiver in range(len(request.to_add)):
            if caregiver not in caregivers:
                caregiver_key = Key(Caregiver, caregiver)
                if not caregiver_key.get():
                    return DefaultResponseMessage(code=NOT_FOUND, message="Caregiver(s) not existent.")
                caregivers[caregiver] = caregiver_key

        for caregiver in range(len(request.to_del)):
            if caregiver in caregivers:
                del caregivers[caregiver]

        user.caregivers = caregivers
        user.put()
        return DefaultResponseMessage(code=OK, message="Caregivers updated.")

    @endpoints.method(UserRelativeCaregiverMessage, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/patients", http_method="PATCH", name="user.updatePatients")
    def update_patients(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code=NOT_FOUND, message="User not existent.")

        caregiver = Key(Caregiver, request.id).get()
        if not caregiver:
            return DefaultResponseMessage(code=NOT_FOUND, message="User not a caregiver.")

        patients = {}
        if not caregiver.patients:
            patients = caregiver.patients

        # TODO Gestire la responsabilita doppia trai dizionari (Paziente-Caregiver)
        # for caregiver in range(len(request.set)):
        #     If already present, means remove
        #     if caregiver in caregivers:
        #         del caregivers[caregiver]
        #     If not present, means add
        #    else:
        #        caregiver_key = Key(User, caregiver)
        #         if not caregiver_key.get():
        #             return DefaultResponseMessage(code=NOT_FOUND, message="Caregiver(s) not existent.")
        #    caregivers[caregiver] = caregiver_key

        for patient in range(len(request.to_add)):
            if patient not in patients:
                patient_key = Key(User, patient)
                if not patient_key.get():
                    return DefaultResponseMessage(code=NOT_FOUND, message="Patient(s) not existent.")
                patients[patient] = patient_key

        for patient in range(len(request.to_del)):
            if patient in patients:
                del patients[patient]

        user.patients = patients
        user.put()
        return DefaultResponseMessage(code=OK, message="Patients updated.")

    @endpoints.method(UserFirstAidInfoMessage, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/firstaidinfo", http_method="PATCH", name="user.updateFirstAidInfo")
    def update_first_aid_info(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return DefaultResponseMessage(code=NOT_FOUND, message="User not existent.")

        if not request.pc_physician:
            if user.pc_physician.id() == request.pc_physician:
                return DefaultResponseMessage(code=PRECONDITION_FAILED, message="PC physician already registered.")
            pc_physician_usr = Key(User, request.pc_physician).get()
            if not pc_physician_usr:
                return DefaultResponseMessage(code=NOT_FOUND, message="User not existent.")
            pc_physician_crgv = Caregiver.query(ancestor=pc_physician_usr.key).get()
            if not pc_physician_crgv:
                return DefaultResponseMessage(code=NOT_FOUND, message="User not a Caregiver.")
            user.pc_physician = pc_physician_usr.key
            pc_physician_crgv.patients[request.id] = user.key
            user.put()
            pc_physician_crgv.put()

        if not request.visiting_nurse:
            if user.visiting_nurse.id() == request.visiting_nurse:
                return DefaultResponseMessage(code=PRECONDITION_FAILED, message="Visiting nurse already registered.")
            visiting_nurse_usr = Key(User, request.visiting_nurse).get()
            if not visiting_nurse_usr:
                return DefaultResponseMessage(code=NOT_FOUND, message="User not existent.")
            visiting_nurse_crgv = Caregiver.query(ancestor=visiting_nurse_usr.key).get()
            if not visiting_nurse_crgv:
                return DefaultResponseMessage(code=NOT_FOUND, message="User not a Caregiver.")
            user.visiting_nurse = visiting_nurse_usr.key
            visiting_nurse_crgv.patients[request.id] = user.key
            user.put()
            visiting_nurse_crgv.put()
        return DefaultResponseMessage(code=OK, message="First aid info updated.")
    '''

    @endpoints.method(USER_UPDATE_RELATION_INFO, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/relations", http_method="PATCH", name="user.updateRelationInfo")
    def update_relation_info(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent."))

        if request.kind not in REQUEST_KIND:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Kind not existent.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Kind not existent."))

        if request.kind == "RELATIVE":
            relation_usr = Key(User, request.relation_id).get()
            if not relation_usr:
                return RecipexServerApi.return_response(code=NOT_FOUND,
                                                        message="Relation user not existent.",
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="Relation user not existent."))
            if user.key.id() in relation_usr.relatives.keys():
                del relation_usr.relatives[user.key.id()]
            if relation_usr.key.id() in user.relatives.keys():
                del user.relatives[relation_usr.key.id()]
            user.put()
            relation_usr.put()
        else:
            if request.kind not in REQUEST_KIND:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Role not existent.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Role not existent."))
            if request.role == "PATIENT":
                caregiver = Caregiver.query(ancestor=Key(User, request.relation_id)).get()
                if not caregiver:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Relation user not a caregiver.",
                                                            response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                            message="Relation user not a caregiver."))
                patient = user
            else:
                caregiver = Caregiver.query(ancestor=user.key).get()
                if not caregiver:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="User not a caregiver.",
                                                            response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                            message="User not a caregiver."))
                patient = Key(User, request.relation_id).get()

            if request.kind == "PC_PHYSICIAN":
                if patient.pc_physician == caregiver.key:
                    patient.pc_physician = None
                if patient.visiting_nurse != caregiver.key and\
                   caregiver.key.id() not in patient.caregivers.keys():
                    del caregiver.patients[patient.key.id()]
            elif request.kind == "V_NURSE":
                if patient.visiting_nurse == caregiver.key:
                    patient.visiting_nurse = None
                if patient.pc_physician != caregiver.key and \
                   caregiver.key.id() not in patient.caregivers.keys():
                    del caregiver.patients[patient.key.id()]
            else:
                if caregiver.key.id() in patient.caregivers.keys():
                    del patient.caregivers[caregiver.key.id()]
                if patient.pc_physician != caregiver.key and\
                   patient.visiting_nurse != caregiver.key:
                    del caregiver.patients[patient.key.id()]

            patient.put()
            caregiver.put()

        return RecipexServerApi.return_response(code=OK,
                                                message="Relation updated.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="Relation updated."))

    @endpoints.method(USER_ID_MESSAGE, UserMeasurementsMessage,
                      path="recipexServerApi/users/{id}/measurements", http_method="GET", name="user.getMeasurements")
    def get_measurements(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserMeasurementsMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        if request.kind:
            if request.kind not in MEASUREMENTS_KIND:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Kind not existent.",
                                                        response=UserMeasurementsMessage(
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Kind not existent.")))

            measurements = Measurement.query(ancestor=user.key)\
                                      .order(-Measurement.date_time)\
                                      .filter(Measurement.kind == request.kind)
        else:
            measurements = Measurement.query(ancestor=user.key)\
                                      .order((-Measurement.date_time))

        if request.date_time:
            try:
                date_time = datetime.strptime(request.date_time, "%Y-%m-%d %H:%M:%S.%f")
                measurements = measurements.filter(Measurement.date_time > date_time)
            except ValueError:
                return RecipexServerApi.return_response(code=BAD_REQUEST,
                                                        message="Bad date_time format.",
                                                        response=UserMeasurementsMessage(
                                                            response=DefaultResponseMessage(
                                                                code=BAD_REQUEST,
                                                                message="Bad date_time format.")))

        if request.fetch:
            measurements = measurements.fetch(request.fetch)

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

        return RecipexServerApi.return_response(code=OK,
                                                message="Measurements retrieved.",
                                                response=UserMeasurementsMessage(
                                                    measurements=user_measurements,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Measurements retrieved.")))

    @endpoints.method(USER_ID_MESSAGE, UserMessagesMessage,
                      path="recipexServerApi/users/{id}/messages", http_method="GET", name="user.getMessages")
    def get_messages(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserMessagesMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        messages_entities = Message.query(ancestor=user.key)

        user_messages = []

        for message in messages_entities:
            sender = message.sender.get()
            if sender:
                pic = sender.pic
            if message.measurement:
                user_messages.append(MessageInfoMessage(id=message.key.id(), sender=message.sender.id(),
                                                        receiver=message.receiver.id(), message=message.message,
                                                        hasRead=message.hasRead, sender_pic=pic,
                                                        measurement=message.measurement.id()))
            else:
                user_messages.append(MessageInfoMessage(id=message.key.id(), sender=message.sender.id(),
                                                        receiver=message.receiver.id(), message=message.message,
                                                        sender_pic=pic, hasRead=message.hasRead))

            if not message.hasRead:
                message.hasRead = True
                message.put()

        return RecipexServerApi.return_response(code=OK,
                                                message="Messages retrieved.",
                                                response=UserMessagesMessage(
                                                    user_messages=user_messages,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Messages retrieved.")))

    @endpoints.method(USER_ID_MESSAGE, UserMessagesMessage,
                      path="recipexServerApi/users/{id}/unread-messages", http_method="GET", name="user.getUnreadMessages")
    def get_unread_messages(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserMessagesMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        messages_entities = Message.query(ancestor=user.key)

        user_messages = []

        for message in messages_entities:
            if not message.hasRead:
                sender = message.sender.get()
                if sender:
                    pic = sender.pic
                if message.measurement:
                    user_messages.append(MessageInfoMessage(id=message.key.id(), sender=message.sender.id(),
                                                            receiver=message.receiver.id(), message=message.message,
                                                            hasRead=message.hasRead, sender_pic=pic,
                                                            measurement=message.measurement.id()))
                else:
                    user_messages.append(MessageInfoMessage(id=message.key.id(), sender=message.sender.id(),
                                                            receiver=message.receiver.id(), message=message.message,
                                                            sender_pic=pic, hasRead=message.hasRead))

        return RecipexServerApi.return_response(code=OK,
                                                message="Messages retrieved.",
                                                response=UserMessagesMessage(
                                                    user_messages=user_messages,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Messages retrieved.")))

    @endpoints.method(USER_ID_MESSAGE, UserRequestsMessage,
                      path="recipexServerApi/users/{id}/requests", http_method="GET", name="user.getRequests")
    def get_requests(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserRequestsMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        if request.kind:
            if request.kind not in REQUEST_KIND:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Kind not existent.",
                                                        response=UserRequestsMessage(
                                                            response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                            message="Kind not existent.")))

            request_entities = Request.query(ancestor=user.key).filter(Request.kind == request.kind)
        else:
            request_entities = Request.query(ancestor=user.key)

        user_requests = []

        for request in request_entities:
            sender = request.sender.get()
            if sender:
                pic = sender.pic
                name = sender.name
                surname = sender.surname
            if request.kind == "RELATIVE":
                user_requests.append(RequestInfoMessage(id=request.key.id(), receiver=request.receiver.id(),
                                                        sender=request.sender.id(), message=request.message,
                                                        kind=request.kind, role=request.role, sender_pic=pic,
                                                        sender_name=name, sender_surname=surname,
                                                        calendarId=request.calendarId, pending=request.isPending))
            else:
                user_requests.append(RequestInfoMessage(id=request.key.id(), receiver=request.receiver.id(),
                                                        sender=request.sender.id(), message=request.message,
                                                        kind=request.kind, role=request.role, sender_pic=pic,
                                                        sender_name=name, sender_surname=surname,
                                                        pending=request.isPending, calendarId=request.calendarId,
                                                        caregiver=request.caregiver.id()))
            if request.isPending:
                request.isPending = False
                request.put()

        return RecipexServerApi.return_response(code=OK,
                                                message="Requests retrieved.",
                                                response=UserRequestsMessage(
                                                    requests=user_requests,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Requests retrieved.")))

    @endpoints.method(USER_ID_MESSAGE, UserRequestsMessage,
                      path="recipexServerApi/users/{id}/requests-pending", http_method="GET", name="user.getRequestsPending")
    def get_requests_pending(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserRequestsMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        if request.kind:
            if request.kind not in REQUEST_KIND:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Kind not existent.",
                                                        response=UserRequestsMessage(
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Kind not existent.")))

            request_entities = Request.query(ndb.AND(Request.sender == user.key,
                                                     Request.kind == request.kind))
        else:
            request_entities = Request.query(Request.sender == user.key)

        user_requests = []

        for request in request_entities:
            sender = request.sender.get()
            if sender:
                pic = sender.pic
                name = sender.name
                surname = sender.surname
            if request.kind == "RELATIVE":
                user_requests.append(RequestInfoMessage(id=request.key.id(), receiver=request.receiver.id(),
                                                        sender=request.sender.id(), message=request.message,
                                                        kind=request.kind, role=request.role, sender_name=name,
                                                        sender_surname=surname, sender_pic=pic,
                                                        calendarId=request.calendarId, pending=request.isPending))
            else:
                user_requests.append(RequestInfoMessage(id=request.key.id(), receiver=request.receiver.id(),
                                                        sender=request.sender.id(), message=request.message,
                                                        kind=request.kind, role=request.role, sender_pic=pic,
                                                        sender_name=name, sender_surname=surname,
                                                        pending=request.isPending, calendarId=request.calendarId,
                                                        caregiver=request.caregiver.id()))

        return RecipexServerApi.return_response(code=OK,
                                                message="Requests retrieved.",
                                                response=UserRequestsMessage(
                                                    requests=user_requests,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Requests retrieved.")))

    @endpoints.method(USER_ID_MESSAGE, UserPrescriptionsMessage,
                      path="recipexServerApi/users/{id}/prescriptions", http_method="GET",
                      name="user.getPrescriptions")
    def get_prescriptions(self, request):
        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserPrescriptionsMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        user_prescriptions = []
        prescriptions = Prescription.query(ancestor=user.key)
        for prescription in prescriptions:
            prescription_info = PrescriptionInfoMessage(name=prescription.name,
                                                        active_ingr_key=prescription.active_ingr_key.id(),
                                                        active_ingr_name=prescription.active_ingr_name,
                                                        kind=prescription.kind,
                                                        dose=prescription.dose, units=prescription.units,
                                                        quantity=prescription.quantity, seen=prescription.seen,
                                                        recipe=prescription.recipe, pil=prescription.pil,
                                                        response=DefaultResponseMessage(code=OK,
                                                                                        message="Prescription info retrieved."))

            prescription.seen = True
            prescription.put()

            if prescription.caregiver is not None:
                user_caregiver = prescription.caregiver.parent().get()
                prescription_info.caregiver_user_id = user_caregiver.key.id()
                prescription_info.caregiver_id = prescription.caregiver.id()
                prescription_info.caregiver_name = user_caregiver.name
                prescription_info.caregiver_surname = user_caregiver.surname
                prescription_info.caregiver_mail = user_caregiver.email
                if user.pc_physician == prescription.caregiver:
                    prescription_info.caregiver_job = "PC_PHYSICIAN"
                elif user.visiting_nurse == prescription.caregiver:
                    prescription_info.caregiver_job = "V_NURSE"
                else:
                    prescription_info.caregiver_job = "CAREGIVER"

            user_prescriptions.append(prescription_info)

        return RecipexServerApi.return_response(code=OK,
                                                message="Prescriptions retrieved.",
                                                response=UserPrescriptionsMessage(
                                                    prescriptions=user_prescriptions,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Prescriptions retrieved.")))

    @endpoints.method(USER_ID_MESSAGE, UserPrescriptionsMessage,
                      path="recipexServerApi/users/{id}/unseen-prescriptions", http_method="GET",
                      name="user.getUnseenPrescriptions")
    def get_unseen_prescriptions(self, request):
        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserPrescriptionsMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        user_prescriptions = []
        prescriptions = Prescription.query(ancestor=user.key)
        for prescription in prescriptions:
            if not prescriptions.seen:
                prescription_info = PrescriptionInfoMessage(name=prescription.name,
                                                            active_ingr_key=prescription.active_ingr_key.id(),
                                                            active_ingr_name=prescription.active_ingr_name,
                                                            kind=prescription.kind,
                                                            dose=prescription.dose, units=prescription.units,
                                                            quantity=prescription.quantity,
                                                            recipe=prescription.recipe, pil=prescription.pil,
                                                            response=DefaultResponseMessage(code=OK,
                                                                                            message="Prescription info retrieved."))

                if prescription.caregiver is not None:
                    user_caregiver = prescription.caregiver.parent().get()
                    prescription_info.caregiver_user_id = user_caregiver.key.id()
                    prescription_info.caregiver_id = prescription.caregiver.id()
                    prescription_info.caregiver_name = user_caregiver.name
                    prescription_info.caregiver_surname = user_caregiver.surname
                    if user.pc_physician == prescription.caregiver:
                        prescription_info.caregiver_job = "PC_PHYSICIAN"
                    elif user.visiting_nurse == prescription.caregiver:
                        prescription_info.caregiver_job = "V_NURSE"
                    else:
                        prescription_info.caregiver_job = "CAREGIVER"

                user_prescriptions.append(prescription_info)

        return RecipexServerApi.return_response(code=OK,
                                                message="Unseen prescriptions retrieved.",
                                                response=UserPrescriptionsMessage(
                                                    prescriptions=user_prescriptions,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Unseen prescriptions retrieved.")))

    @endpoints.method(USER_ID_MESSAGE, UserRelationsMessage,
                      path="recipexServerApi/users/{id}/relations/{profile_id}", http_method="GET",
                      name="user.checkUserRelations")
    def check_user_relations(self, request):
        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserRelationsMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        profile_user = Key(User, request.profile_id).get()
        if not profile_user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Profile user not existent.",
                                                    response=UserRelationsMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="Profile user not existent.")))

        answer = UserRelationsMessage(is_relative_request=False, is_pc_physician=False, is_pc_physician_request=False,
                                      is_visiting_nurse=False, is_visiting_nurse_request=False, is_caregiver=False,
                                      is_caregiver_request=False, is_patient=False, is_patient_request=False)

        old_request_prof = Request.query(ancestor=profile_user.key).filter(Request.sender == user.key)
        old_request_user = Request.query(ancestor=user.key).filter(Request.sender == profile_user.key)

        if profile_user.key.id() in user.relatives.keys():
            answer.is_relative = True
        elif old_request_prof.filter(Request.kind == "RELATIVE").get() or\
                old_request_user.filter(Request.kind == "RELATIVE").get():
            answer.is_relative = True
            answer.is_relative_request = True
        else:
            answer.is_relative = False

        profile_caregiver = Caregiver.query(ancestor=profile_user.key).get()
        # TODO Per patients??
        if profile_caregiver is not None:
            if user.pc_physician == profile_caregiver.key:
                answer.is_pc_physician = True
            elif old_request_prof.filter(Request.kind == "PC_PHYSICIAN").get():
                answer.is_pc_physician = True
                answer.is_pc_physician_request = True

            if user.visiting_nurse == profile_caregiver.key:
                answer.is_visiting_nurse = True
            elif old_request_prof.filter(Request.kind == "V_NURSE").get():
                answer.is_visiting_nurse = True
                answer.is_visiting_nurse_request = True

            # if profile_caregiver.key.id() in user.caregivers.keys():
            if profile_user.key.id() in user.caregivers.keys():
                answer.is_caregiver = True
            elif old_request_prof.filter(Request.kind == "CAREGIVER").get():
                answer.is_caregiver = True
                answer.is_caregiver_request = True

        user_caregiver = Caregiver.query(ancestor=user.key).get()

        if user_caregiver is not None:
            if profile_user.pc_physician == user_caregiver.key:
                answer.is_pc_physician = True
            elif old_request_user.filter(Request.kind == "PC_PHYSICIAN").get():
                answer.is_pc_physician = True
                answer.is_pc_physician_request = True

            if profile_user.visiting_nurse == user_caregiver.key:
                answer.is_visiting_nurse = True
            elif old_request_user.filter(Request.kind == "V_NURSE").get():
                answer.is_visiting_nurse = True
                answer.is_visiting_nurse_request = True

            # if profile_caregiver.key.id() in user.caregivers.keys():
            if user.key.id() in profile_user.caregivers.keys():
                answer.is_caregiver = True
            elif old_request_user.filter(Request.kind == "CAREGIVER").get():
                answer.is_caregiver = True
                answer.is_caregiver_request = True
            '''
            if profile_user.key in user_caregiver.patients.keys():
                answer.is_patient = True
            elif is_patient_request_sent:
                answer.is_patient = True
                answer.is_patient_request = True

            if old_request_user.filter(Request.kind == "PC_PHYSICIAN").get():
                answer.is_pc_physician = True
                answer.is_pc_physician_request = True

            if old_request_user.filter(Request.kind == "V_NURSE").get():
                answer.is_visiting_nurse = True
                answer.is_visiting_nurse_request = True

            if old_request_user.filter(Request.kind == "CAREGIVER").get():
                answer.is_caregiver = True
                answer.is_caregiver_request = True
            '''

        answer.response = DefaultResponseMessage(code=OK, message="Relations info retrieved.")

        return RecipexServerApi.return_response(code=OK,
                                                message="Relations info retrieved.",
                                                response=answer)

    @endpoints.method(USER_ID_MESSAGE, UserUnseenInfoMessage,
                      path="recipexServerApi/users/{id}/has-unseen-info", http_method="GET",
                      name="user.hasUnseenInfo")
    def has_unseen_info(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=UserUnseenInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        messages_entities = Message.query(ancestor=user.key)
        num_messages = 0
        for message in messages_entities:
            if not message.hasRead:
                num_messages += 1

        requests_entities = Request.query(ancestor=user.key)
        num_requests = 0
        for request in requests_entities:
            if request.isPending:
                num_requests += 1

        prescriptions_entities = Message.query(ancestor=user.key)
        num_prescriptions = 0
        for prescription in prescriptions_entities:
            if not prescription.hasSeen:
                num_prescriptions += 1

        return RecipexServerApi.return_response(code=OK,
                                                message="Unread unseen info retrieved.",
                                                response=UserUnseenInfoMessage(
                                                    num_messages=num_messages,
                                                    num_requests=num_requests,
                                                    num_prescriptions=num_prescriptions,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Unread unseen info retrieved.")))

    @endpoints.method(ADD_MEASUREMENT_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/measurements", http_method="POST", name="measurement.addMeasurement")
    def add_measurement(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent."))
        '''
        try:
            date_time = datetime.strptime(request.date_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return DefaultResponseMessage(code=BAD_REQUEST, message="Bad date_time format.")
        '''

        date_time = datetime.utcnow()

        if request.kind not in MEASUREMENTS_KIND:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Wrong measurement kind.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Wrong measurement kind."))

        new_measurement = Measurement(parent=user.key, date_time=date_time, kind=request.kind, note=request.note)

        if request.kind == "BP":
            if request.systolic is None or request.diastolic is None:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter(s) missing.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter(s) missing."))
            if (request.systolic < 0 or request.systolic > 250) or (request.diastolic < 0 or request.diastolic > 250):
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter(s) out of range.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter(s) out of range."))
            new_measurement.systolic = request.systolic
            new_measurement.diastolic = request.diastolic
        elif request.kind == "HR":
            if request.bpm is None:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter missing.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter missing."))
            if request.bpm < 0 or request.bpm > 400:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter out of range.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter out of range."))
            new_measurement.bpm = request.bpm
        elif request.kind == "RR":
            if request.respirations is None:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter missing.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter missing."))
            if request.respirations < 0 or request.respirations > 200:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter out of range.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter out of range."))
            new_measurement.respirations = request.respirations
        elif request.kind == "SpO2":
            if request.spo2 is None:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter missing.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter missing."))
            if request.spo2 < 0 or request.spo2 > 100:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter out of range.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter out of range."))
            new_measurement.spo2 = request.spo2
        elif request.kind == "HGT":
            if request.hgt is None:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter missing.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter missing."))
            if request.hgt < 0 or request.hgt > 600:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter out of range.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter out of range."))
            new_measurement.hgt = request.hgt
        elif request.kind == "TMP":
            if request.degrees is None:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter missing.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter missing."))
            if request.degrees < 30 or request.degrees > 45:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter out of range.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter out of range."))
            new_measurement.degrees = request.degrees
        elif request.kind == "PAIN":
            if request.nrs is None:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter missing.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter missing."))
            if request.nrs < 0 or request.hgt > 10:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter out of range.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter out of range."))
            new_measurement.nrs = request.nrs
        else:
            if request.chl_level is None:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter missing.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter missing."))
            if request.chl_level < 0 or request.chl_level > 800:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Input parameter out of range.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Input parameter out of range."))
            new_measurement.chl_level = request.chl_level

        measurement_key = new_measurement.put()

        return RecipexServerApi.return_response(code=CREATED,
                                                message="Measurement added.",
                                                response=DefaultResponseMessage(code=CREATED,
                                                                                message="Measurement added.",
                                                                                payload=str(measurement_key.id())))

    @endpoints.method(UPDATE_MEASUREMENT_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/measurements/{id}", http_method="PUT", name="measurement.updateMeasurement")
    def update_measurement(self, request):
        RecipexServerApi.authentication_check()

        measurement = Key(User, request.user_id, Measurement, request.id).get()
        if not measurement:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Measurement not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Measurement not existent."))

        user_key = Key(User, request.user_id)
        if user_key != measurement.key.parent():
            return RecipexServerApi.return_response(code="401 Unauthorized",
                                                    message="User unauthorized.",
                                                    response=DefaultResponseMessage(code="401 Unauthorized",
                                                                                    message="User unauthorized."))

        '''
        if request.date_time:
            try:
                utc = datetime.strptime(request.date_time, "%Y-%m-%d %H:%M:%S")
                from_zone = pytz.timezone('Europe/Rome')
                to_zone = pytz.timezone('UTC')
                utc = utc.replace(tzinfo=from_zone)
                central = utc.astimezone(to_zone)
                measurement.date_time = central
            except ValueError:
                return DefaultResponseMessage(code=BAD_REQUEST, message="Bad date_time format.")
        '''

        if request.kind not in MEASUREMENTS_KIND:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Measurement kind not existent.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Measurement kind not existent."))

        if request.kind != measurement.kind:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Wrong measurement kind.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Wrong measurement kind."))

        if request.note is not None:
            if request.note:
                measurement.note = request.note
            else:
                measurement.note = None

        if measurement.kind == "BP":
            if request.systolic is not None:
                if request.systolic < 0 or request.systolic > 250:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Input parameter(s) out of range.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Input parameter(s) out of range."))
                measurement.systolic = request.systolic
            if request.diastolic is not None:
                if request.diastolic < 0 or request.diastolic > 250:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Input parameter out of range.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Input parameter out of range."))
                measurement.diastolic = request.diastolic
        elif request.kind == "HR":
            if request.bpm is not None:
                if request.bpm < 0 or request.bpm > 400:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Input parameter out of range.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Input parameter out of range."))
                measurement.bpm = request.bpm
        elif request.kind == "RR":
            if request.respirations is not None:
                if request.respirations < 0 or request.respirations > 200:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Input parameter out of range.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Input parameter out of range."))
                measurement.respirations = request.respirations
        elif request.kind == "SpO2":
            if request.spo2 is not None:
                if request.spo2 < 0 or request.spo2 > 100:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Input parameter out of range.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Input parameter out of range."))
                measurement.spo2 = request.spo2
        elif request.kind == "HGT":
            if request.hgt is not None:
                if request.hgt < 0 or request.hgt > 600:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Input parameter out of range.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Input parameter out of range."))
                measurement.hgt = request.hgt
        elif request.kind == "TMP":
            if request.degrees is not None:
                if request.degrees < 30 or request.degrees > 45:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Input parameter out of range.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Input parameter out of range."))
                measurement.degrees = request.degrees
        elif request.kind == "PAIN":
            if request.nrs is not None:
                if request.nrs < 0 or request.nrs > 10:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Input parameter out of range.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Input parameter out of range."))
                measurement.nrs = request.nrs
        else:
            if request.chl_level is not None:
                if request.chl_level < 0 or request.chl_level > 800:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Input parameter out of range.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Input parameter out of range."))
                measurement.chl_level = request.chl_level

        measurement.put()
        return RecipexServerApi.return_response(code=OK,
                                                message="Measurement updated.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="Measurement updated."))

    @endpoints.method(MEASUREMENT_ID_MESSAGE, MeasurementInfoMessage,
                      path="recipexServerApi/users/{user_id}/measurements/{id}", http_method="GET", name="measurement.getMeasurement")
    def get_measurement(self, request):
        RecipexServerApi.authentication_check()
        measurement = Key(User, request.user_id, Measurement, request.id).get()
        if not measurement:
            if not measurement:
                return RecipexServerApi.return_response(code=NOT_FOUND,
                                                        message="Measurement not existent.",
                                                        response=MeasurementInfoMessage(
                                                            response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                            message="Measurement not existent.")))

        user_key = Key(User, request.user_id)
        if user_key != measurement.key.parent():
            return RecipexServerApi.return_response(code="401 Unauthorized",
                                                    message="User unauthorized.",
                                                    response=MeasurementInfoMessage(
                                                        response=DefaultResponseMessage(code="401 Unauthorized",
                                                                                        message="User unauthorized.")))

        # date_time = datetime.strftime(measurement.date_time, "%Y-%m-%d %H:%M:%S")
        try:
            utc = measurement.date_time
            from_zone = pytz.timezone('UTC')
            to_zone = pytz.timezone('Europe/Rome')
            utc = utc.replace(tzinfo=from_zone)
            central = utc.astimezone(to_zone)
            date_time = datetime.strftime(central, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return RecipexServerApi.return_response(code=BAD_REQUEST,
                                                    message="Bad date_time format.",
                                                    response=MeasurementInfoMessage(
                                                        response=DefaultResponseMessage(code=BAD_REQUEST,
                                                                                        message="Bad date_time format.")))

        msr_info = MeasurementInfoMessage(date_time=date_time, kind=measurement.kind, systolic=measurement.systolic,
                                          diastolic=measurement.diastolic, bpm=measurement.bpm, spo2=measurement.spo2,
                                          respirations=measurement.respirations, degrees=measurement.degrees,
                                          hgt=measurement.hgt, nrs=measurement.nrs, chl_level=measurement.chl_level,
                                          note=measurement.note, response=DefaultResponseMessage(code=OK,
                                                                                                 message="Measurement info retrieved."))

        return RecipexServerApi.return_response(code=OK,
                                                message="Measurement info retrieved.",
                                                response=msr_info)

    @endpoints.method(MEASUREMENT_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/measurements/{id}", http_method="DELETE", name="measurement.deleteMeasurement")
    def delete_measurement(self, request):
        RecipexServerApi.authentication_check()
        measurement = Key(User, request.user_id, Measurement, request.id).get()
        if not measurement:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Measurement not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Measurement not existent."))
        user_key = Key(User, request.user_id)
        if user_key != measurement.key.parent():
            return RecipexServerApi.return_response(code="401 Unauthorized",
                                                    message="User unauthorized.",
                                                    response=DefaultResponseMessage(code="401 Unauthorized",
                                                                                    message="User unauthorized."))

        measurement.key.delete()
        return RecipexServerApi.return_response(code=OK,
                                                message="Measurement deleted.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="Measurement deleted."))

    @endpoints.method(MESSAGE_SEND_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{receiver}/messages", http_method="POST", name="message.sendMessage")
    def send_message(self, request):
        RecipexServerApi.authentication_check()

        sender = Key(User, request.sender).get()
        if not sender:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Sender not existent.",
                                                    response=UserMeasurementsMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="Sender not existent.")))

        receiver = Key(User, request.receiver).get()
        if not receiver:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Receiver not existent.",
                                                    response=UserMeasurementsMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="Receiver not existent.")))

        measurement_key = None
        if request.measurement:
            measurement_key = Key(User, receiver.key.id(), Measurement, request.measurement)
            measurement = measurement_key.get()
            if not measurement:
                return RecipexServerApi.return_response(code=NOT_FOUND,
                                                        message="Measurement not existent.",
                                                        response=UserMeasurementsMessage(
                                                            response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                            message="Measurement not existent.")))

        message = Message(parent=receiver.key, sender=sender.key, receiver=receiver.key, message=request.message,
                          hasRead=False, measurement=measurement_key)

        message.put()
        return RecipexServerApi.return_response(code=CREATED,
                                                message="Message sent.",
                                                response=UserMeasurementsMessage(
                                                    response=DefaultResponseMessage(code=CREATED,
                                                                                    message="Message sent.")))

    @endpoints.method(MESSAGE_ID_MESSAGE, MessageInfoMessage,
                      path="recipexServerApi/users/{user_id}/messages/{id}", http_method="GET", name="message.getMessage")
    def get_message(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=MessageInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        message = Key(User, request.user_id, Message, request.id).get()
        if not message:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Message not existent.",
                                                    response=MessageInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="Message not existent.")))

        if message.receiver != user.key:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="User not the receiver.",
                                                    response=MessageInfoMessage(
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="User not the receiver.")))

        message.hasRead = True
        message.put()

        sender = message.sender.get()
        if sender:
            pic = sender.pic
        msg_msg = MessageInfoMessage(sender=message.sender.id(), receiver=message.receiver.id(), message=message.message,
                                     hasRead=message.hasRead, measurement=message.measurement.id(), sender_pic=pic,
                                     response=DefaultResponseMessage(code=OK, message="Message info retrieved."))

        return RecipexServerApi.return_response(code=OK,
                                                message="Message info retrieved.",
                                                response=msg_msg)

    @endpoints.method(MESSAGE_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/messages/{id}", http_method="PUT", name="message.readMessage")
    def read_message(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent."))

        message = Key(User, request.user_id, Message, request.id).get()
        if not message:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Message not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Message not existent."))

        if message.receiver != user.key:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="User not the receiver.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="User not the receiver."))

        message.hasRead = True
        message.put()

        return RecipexServerApi.return_response(code=OK,
                                                message="Message read.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="Message read."))

    @endpoints.method(MESSAGE_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/messages/{id}", http_method="DELETE", name="message.deleteMessage")
    def delete_message(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent."))

        message = Key(User, request.user_id, Message, request.id).get()
        if not message:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Message not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Message not existent."))

        if message.receiver != user.key:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="User not the receiver.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="User not the receiver."))

        message.key.delete()

        return RecipexServerApi.return_response(code=OK,
                                                message="Message deleted.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="Message deleted."))

    @endpoints.method(REQUEST_SEND_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{receiver}/requests", http_method="POST", name="request.sendRequest")
    def send_request(self, request):
        RecipexServerApi.authentication_check()

        sender = Key(User, request.sender).get()
        if not sender:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Sender not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Sender not existent."))

        receiver = Key(User, request.receiver).get()
        if not receiver:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Receiver not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Receiver not existent."))

        if request.kind not in REQUEST_KIND:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Kind not existent.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Kind not existent."))

        old_request = Request.query(ancestor=receiver.key).filter(ndb.AND(Request.sender == sender.key,
                                                                          Request.kind == request.kind)).get()
        if old_request:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Request already existent.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Request already existent."))

        old_request = Request.query(ancestor=sender.key).filter(ndb.AND(Request.sender == receiver.key,
                                                                        Request.kind == request.kind)).get()

        if old_request:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Request already existent.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Request already existent."))

        caregiver_key = None
        if request.kind == "CAREGIVER" or request.kind == "PC_PHYSICIAN" or request.kind == "V_NURSE":
            if request.role not in ROLE_TYPE:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Role not existent.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Role not existent."))

            # Il paziente ha mandato la richiesta: il caregiver e' il receiver
            if request.role == "PATIENT":
                patient = sender
                caregiver_user = receiver
                caregiver = Caregiver.query(ancestor=receiver.key).get()
                if not caregiver:
                    return RecipexServerApi.return_response(code="412 Not Found",
                                                            message="Receiver not a caregiver.",
                                                            response=DefaultResponseMessage(code="412 Not Found",
                                                                                            message="Receiver not a caregiver."))
            else:
                patient = receiver
                caregiver_user = sender
                caregiver = Caregiver.query(ancestor=sender.key).get()
                if not caregiver:
                    return RecipexServerApi.return_response(code="412 Not Found",
                                                            message="Sender not a caregiver.",
                                                            response=DefaultResponseMessage(code="412 Not Found",
                                                                                            message="Sender not a caregiver."))
            # if caregiver.patients and patient.key.id() in caregiver.patients.keys():
            #     return DefaultResponseMessage(code=PRECONDITION_FAILED, message="Already a patient.")
            if request.kind == "CAREGIVER":
                # if caregiver.key.id() in patient.caregivers.keys():
                if caregiver_user.key.id() in patient.caregivers.keys():
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Already a caregiver.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Already a caregiver."))
            elif request.kind == "PC_PHYSICIAN":
                if patient.pc_physician == caregiver.key:
                    # if patient.pc_physician == caregiver_user.key:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Already the pc_physician.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Already the pc_physician."))
            else:
                if patient.visiting_nurse == caregiver.key:
                    # if patient.visiting_nurse == caregiver_user.key:
                    return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                            message="Already the visiting Nurse.",
                                                            response=DefaultResponseMessage(
                                                                code=PRECONDITION_FAILED,
                                                                message="Already the visiting Nurse."))
            caregiver_key = caregiver.key
        else:
            if receiver.relatives and sender.key.id() in receiver.relatives.keys():
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Already a relative.",
                                                        response=DefaultResponseMessage(
                                                            code=PRECONDITION_FAILED,
                                                            message="Already a relative."))

        new_request = Request(parent=receiver.key, sender=sender.key, receiver=receiver.key,
                              kind=request.kind, message=request.message, role=request.role,
                              isPending=True, caregiver=caregiver_key, calendarId=request.calendarId)

        new_request.put()

        return RecipexServerApi.return_response(code=CREATED,
                                                message="Request sent.",
                                                response=DefaultResponseMessage(code=CREATED,
                                                                                message="Request sent.",
                                                                                payload=str(new_request.key.id())))

    @endpoints.method(REQUEST_ID_MESSAGE, RequestInfoMessage,
                      path="recipexServerApi/users/{user_id}/requests/{id}", http_method="GET", name="request.getRequest")
    def get_request(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=RequestInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        usr_request = Key(User, request.user_id, Request, request.id).get()
        if not usr_request:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Request not existent.",
                                                    response=RequestInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="Request not existent.")))

        if usr_request.receiver != user.key:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="User not the receiver.",
                                                    response=RequestInfoMessage(
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="User not the receiver.")))

        usr_request.isPending = False
        usr_request.put()

        sender = usr_request.sender.get()
        if sender:
            pic = sender.pic
            name = sender.name
            surname = sender.surname
        rqst_msg = RequestInfoMessage(sender=usr_request.sender.id(), receiver=usr_request.receiver.id(),
                                      kind=usr_request.kind, message=usr_request.message, role=usr_request.role,
                                      sender_pic=pic, caregiver=usr_request.caregiver.id(), sender_name=name,
                                      sender_surname=surname, pending=request.isPending, calendarId=request.calendarId,
                                      response=DefaultResponseMessage(code=OK, message="Request info retrieved."))

        return RecipexServerApi.return_response(code=NOT_FOUND,
                                                message="User not existent.",
                                                response=rqst_msg)

    @endpoints.method(REQUEST_ANSWER_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/requests/{id}", http_method="PUT", name="request.answerRequest")
    def answer_request(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent."))

        usr_request = Key(User, request.user_id, Request, request.id).get()
        if not usr_request:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Request not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Request not existent."))

        if usr_request.receiver != user.key:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not the receiver.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not the receiver."))

        if request.answer:
            if usr_request.kind == "RELATIVE":
                sender = usr_request.sender.get()
                if not sender:
                    return RecipexServerApi.return_response(code=NOT_FOUND,
                                                            message="Sender not existent.",
                                                            response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                            message="Sender not existent."))
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
                    caregiver_user = usr_request.receiver.get()
                else:
                    patient = usr_request.receiver.get()
                    caregiver_user = usr_request.sender.get()
                if not patient:
                    return RecipexServerApi.return_response(code=NOT_FOUND,
                                                            message="Patient not existent.",
                                                            response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                            message="Patient not existent."))
                caregiver = usr_request.caregiver.get()
                if not caregiver:
                    return RecipexServerApi.return_response(code=NOT_FOUND,
                                                            message="Caregiver not existent.",
                                                            response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                            message="Caregiver not existent."))

                if usr_request.kind == "CAREGIVER":
                    # patient.caregivers[caregiver.key.id()] = caregiver.key
                    patient.caregivers[caregiver_user.key.id()] = caregiver.key
                elif usr_request.kind == "PC_PHYSICIAN":
                    patient.pc_physician = caregiver.key
                else:
                    patient.visiting_nurse = caregiver.key

                caregiver.patients[patient.key.id()] = patient.key

                patient.put()
                caregiver.put()

        calendarId = usr_request.calendarId
        usr_request.key.delete()

        return RecipexServerApi.return_response(code=OK,
                                                message="Answer received.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="Answer received.",
                                                                                payload=calendarId))

    @endpoints.method(REQUEST_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/requests/{id}", http_method="DELETE", name="request.deleteRequest")
    def delete_request(self, request):
        RecipexServerApi.authentication_check()

        user = Key(User, request.user_id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent."))

        usr_request = Key(User, request.user_id, Request, request.id).get()
        if not usr_request:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Request not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Request not existent."))

        sender = Key(User, request.sender).get()
        if not sender:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Sender not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Sender not existent."))

        if usr_request.sender != sender.key:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Sender not the sender.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Sender not the sender."))

        if usr_request.receiver != user.key:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="User not the receiver.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="User not the receiver."))

        usr_request.key.delete()

        return RecipexServerApi.return_response(code=OK,
                                                message="Request deleted.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="Request deleted."))

    @endpoints.method(ActiveIngredientMessage, DefaultResponseMessage,
                      path="recipexServerApi/active_ingredients", http_method="POST", name="activeIngredient.addActiveIngredient")
    def add_active_ingredient(self, request):
        RecipexServerApi.authentication_check()
        active_ingredient = ActiveIngredient.query(ActiveIngredient.name == request.name).get()
        if active_ingredient:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Active ingredient already existent.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Active ingredient already existent."))

        active_ingredient_key = ActiveIngredient(name=request.name).put()

        return RecipexServerApi.return_response(code=CREATED,
                                                message="Active ingredient added.",
                                                response=DefaultResponseMessage(code=CREATED,
                                                                                message="Active ingredient added.",
                                                                                payload=str(active_ingredient_key.id())))

    @endpoints.method(ACTIVE_INGREDIENT_ID_MESSAGE, ActiveIngredientMessage,
                      path="recipexServerApi/active_ingredients/{id}", http_method="GET", name="activeIngredient.getActiveIngredient")
    def get_active_ingredient(self, request):
        RecipexServerApi.authentication_check()
        active_ingredient = Key(ActiveIngredient, request.id).get()
        if not active_ingredient:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Active ingredient not existent.",
                                                    response=ActiveIngredientMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="Active ingredient not existent.")))

        return RecipexServerApi.return_response(code=OK,
                                                message="Active ingredient info retrieved.",
                                                response=ActiveIngredientMessage(
                                                    name = active_ingredient.name,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Active ingredient info retrieved.")))

    @endpoints.method(ACTIVE_INGREDIENT_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/active_ingredients/{id}", http_method="DELETE", name="activeIngredient.deleteActiveIngredient")
    def delete_active_ingredient(self, request):
        RecipexServerApi.authentication_check()
        active_ingredient = Key(ActiveIngredient, request.id).get()
        if not active_ingredient:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Active ingredient not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Active ingredient not existent."))

        active_ingredient.key.delete()

        return RecipexServerApi.return_response(code=OK,
                                                message="Active ingredient deleted.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="Active ingredient deleted."))

    @endpoints.method(message_types.VoidMessage, ActiveIngredientsMessage,
                      path="recipexServerApi/active_ingredients", http_method="GET", name="activeIngredient.getActiveIngredients")
    def get_active_ingredients(self, request):
        RecipexServerApi.authentication_check()

        active_ingredients_query = ActiveIngredient.query()

        active_ingredients = []
        for active_ingredient in active_ingredients_query:
            active_ingredients.append(ActiveIngredientMessage(id=active_ingredient.key.id(),
                                                              name=active_ingredient.name))

        return RecipexServerApi.return_response(code=OK,
                                                message="Active ingredients retrieved.",
                                                response=ActiveIngredientsMessage(
                                                    active_ingredients=active_ingredients,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Active ingredients retrieved.")))

    @endpoints.method(ADD_PRESCRIPTION_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{id}/prescriptions", http_method="POST", name="prescription.addPrescription")
    def add_prescription(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent."))

        active_ingredient = Key(ActiveIngredient, request.active_ingredient).get()
        if not active_ingredient:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Active ingredient not existent.",
                                                    response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="Active ingredient not existent."))

        if request.kind not in PRESCRIPTION_KIND:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Prescription kind not existent.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Prescription kind not existent."))

        if request.dose < 0 or request.quantity < 0:
            return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                    message="Input parameter(s) out of range.",
                                                    response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                    message="Input parameter(s) out of range."))

        prescription = Prescription(parent=user.key, name=request.name, active_ingr_key=active_ingredient.key,
                                    active_ingr_name=active_ingredient.name, kind=request.kind, dose=request.dose,
                                    units=request.units, quantity=request.quantity, recipe=request.recipe,
                                    pil=request.pil, seen=True)

        if request.caregiver:
            user_caregiver_key = Key(User, request.caregiver).get()
            caregiver_entity = Caregiver.query(ancestor=user_caregiver_key).get()
            if not caregiver_entity:
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="Caregiver not a caregiver",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="Caregiver not a caregiver."))

            if user.key.id() not in caregiver_entity.patients.keys():
                return RecipexServerApi.return_response(code=PRECONDITION_FAILED,
                                                        message="User not a patient.",
                                                        response=DefaultResponseMessage(code=PRECONDITION_FAILED,
                                                                                        message="User not a patient."))

            prescription.caregiver = caregiver_entity.key()
            prescription.seen = False

        prescription_key = prescription.put()
        return RecipexServerApi.return_response(code=CREATED,
                                                message="Prescription added.",
                                                response=DefaultResponseMessage(code=CREATED,
                                                                                message="Prescription added.",
                                                                                payload=str(prescription_key.id())))

    @endpoints.method(PRESCRIPTION_ID_MESSAGE, PrescriptionInfoMessage,
                      path="recipexServerApi/users/{user_id}/prescriptions/{id}", http_method="POST",
                      name="prescription.getPrescription")
    def get_prescription(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.user_id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=PrescriptionInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                    message="User not existent.")))

        prescription = Key(User, request.user_id, Prescription, request.id).get()
        if not prescription:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Prescription not existent.",
                                                    response=PrescriptionInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="Prescription not existent.")))

        prescription_info = PrescriptionInfoMessage(name=prescription.name, active_ingr_key=prescription.active_ingr_key.id(),
                                                    active_ingr_name=prescription.active_ingr_name, kind=prescription.kind,
                                                    dose=prescription.dose, units=prescription.units, quantity=prescription.quantity,
                                                    recipe=prescription.recipe, pil=prescription.pil, seen=prescription.seen,
                                                    response=DefaultResponseMessage(code=OK,
                                                                                    message="Prescription info retrieved."))

        if not prescription.seen:
            prescription.seen = True
            prescription.put()

        if prescription.caregiver is not None:
            user_caregiver = prescription.caregiver.parent().get()
            prescription_info.caregiver_user_id = user_caregiver.key.id()
            prescription_info.caregiver_id = prescription.caregiver.id()
            prescription_info.caregiver_name = user_caregiver.name
            prescription_info.caregiver_surname = user_caregiver.surname
            prescription_info.caregiver_mail = user_caregiver.email
            if user.pc_physician == prescription.caregiver:
                prescription_info.caregiver_job = "PC_PHYSICIAN"
            elif user.visiting_nurse == prescription.caregiver:
                prescription_info.caregiver_job = "V_NURSE"
            else:
                prescription_info.caregiver_job = "CAREGIVER"

        return RecipexServerApi.return_response(code=OK,
                                                message="Prescription info retrieved.",
                                                response=prescription_info)

    @endpoints.method(PRESCRIPTION_ID_MESSAGE, DefaultResponseMessage,
                      path="recipexServerApi/users/{user_id}/prescriptions/{id}", http_method="DELETE",
                      name="prescription.deletePrescription")
    def delete_prescription(self, request):
        RecipexServerApi.authentication_check()
        user = Key(User, request.user_id).get()
        if not user:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="User not existent.",
                                                    response=PrescriptionInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="User not existent.")))

        prescription = Key(User, request.user_id, Prescription, request.id).get()
        if not prescription:
            return RecipexServerApi.return_response(code=NOT_FOUND,
                                                    message="Prescription not existent.",
                                                    response=PrescriptionInfoMessage(
                                                        response=DefaultResponseMessage(code=NOT_FOUND,
                                                                                        message="Prescription not existent.")))

        prescription.key.delete()
        return RecipexServerApi.return_response(code=OK,
                                                message="Prescription deleted.",
                                                response=DefaultResponseMessage(code=OK,
                                                                                message="Prescription deleted."))

    @classmethod
    def authentication_check(cls):
        current_user = endpoints.get_current_user()
        if not current_user:
            raise endpoints.UnauthorizedException('Invalid token.')

        # current_user2 = oauth.get_current_user('https://www.googleapis.com/auth/userinfo.email')

        # logging.info(current_user.__dict__)
        # logging.info(current_user2.__dict__)
        # logging.info(endpoints.API_EXPLORER_CLIENT_ID)
        # logging.info(current_user.email())

        # if current_user.email().lower() not in ["recipex.app@gmail.com",
        #                                         "fabriziofarinacci@gmail.com",
        #                                         "saraveterini@gmail.com"]:
        #    raise endpoints.UnauthorizedException('User Unauthorized')

    @classmethod
    def return_response(cls, code, message, response):
        logging.info("CODE: %s " % code)
        logging.info("MESSAGE: %s " % message)
        return response


APPLICATION = endpoints.api_server([RecipexServerApi])
