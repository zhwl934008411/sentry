from __future__ import absolute_import

import StringIO

from PIL import Image

from rest_framework import status
from rest_framework.response import Response

from sentry.api.bases.user import UserEndpoint
from sentry.api.serializers import serialize
from sentry.models import UserAvatar, File


MIN_DIMENSION = 256

MAX_DIMENSION = 1024

class UserAvatarEndpoint(UserEndpoint):
    FILE_TYPE = 'avatar.file'

    def get(self, request, user):
        return Response(serialize(user, request.user))

    def is_valid_size(self, width, height):
        if width != height:
            return False
        if width < MIN_DIMENSION:
            return False
        if width > MAX_DIMENSION:
            return False
        return True

    def put(self, request, user):
        if user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        photo_string = request.DATA.get('avatar_photo')
        photo = None
        if photo_string:
            photo_string = photo_string.decode('base64')
            with Image.open(StringIO.StringIO(photo_string)) as img:
                width, height = img.size
                if not self.is_valid_size(width, height):
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            file_name = '%s.png' % user.id
            photo = File.objects.create(name=file_name, type=self.FILE_TYPE)
            photo.putfile(StringIO.StringIO(photo_string))

        avatar, _ = UserAvatar.objects.get_or_create(user=user)
        if avatar.file and photo:
            avatar.file.delete()
            avatar.clear_cached_photos()
        if photo:
            avatar.file = photo

        avatar_type = request.DATA.get('avatar_type')
        if avatar_type:
            avatar.avatar_type = avatar_type

        avatar.save()
        return Response(serialize(user, request.user))
