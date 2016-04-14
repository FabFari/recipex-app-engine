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
