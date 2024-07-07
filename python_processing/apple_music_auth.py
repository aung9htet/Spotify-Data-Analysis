import glob, os
import datetime
import jwt
import sys
sys.path.append('..')
import authentication.get_apple_api_key as apple_auth

class AppleMusicAuth(object):

    def __init__(self):
        # Apple Music supports only developer tokens that are signed with the ES256 algorithm
        self.alg = 'ES256'
        self.private_key = self.getPrivateKey()
        self.iss = apple_auth.iss
        self.kid = apple_auth.kid
        issuedAt = datetime.datetime.now()
        maxExpTime = 15777000
        expirationTime = datetime.datetime.now() + datetime.timedelta(seconds=maxExpTime)
        self.start_time = issuedAt.strftime("%s")
        self.exp_time = expirationTime.strftime("%s")
    
    def createAuthToken(self):
        """
        Create an Apple Music JSON Web Token
        """
        secret = self.getPrivateKey()
        print(self.kid)
        headers = {
            "alg": self.alg,
            "kid": self.kid
        }
        payload = {
            "iss": self.iss,
            "exp": int(self.start_time),
            "iat": int(self.exp_time)
        }
        return jwt.encode(payload, secret, algorithm=self.alg, headers=headers)

    def getPrivateKey(self):
        """
        Read the user's Music Kit Private Key
        The *.p8 file should be placed in the same directory as this script
        """
        for f in glob.glob("../authentication/*.p8"):
            privateKeyFile = open(f, "r")
            privateKeyString = privateKeyFile.read()
            return privateKeyString

        raise ValueError('Please place your AuthKey_*.p8 file in the current working directory')