import datetime

import jwt

with open("private.pem", "r") as f:
    PRIVATE_KEY = f.read()

def generate_token(user, cameras):
    permissions = []
    
    permissions.append({"action": "api"})

    for cam in cameras:
        permissions.append({"action": "read", "path": cam.name})
        permissions.append({"action": "publish", "path": cam.name})

    payload = {
        "sub": user.username,
        "mediamtx_permissions": permissions,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2),
        "iat": datetime.datetime.utcnow(),
        "iss": "django-auth"
    }

    token = jwt.encode(
        payload,
        PRIVATE_KEY,
        algorithm="RS256",
        headers={"kid": "my-key-1"}
    )

    return token