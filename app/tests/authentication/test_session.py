from litestar import status_codes

from app.tests import BaseTestCase


class SessionTestCase(BaseTestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.url = "/api/auth/session"

    async def test_session_when_not_logged_in(self):
        """
        Test getting user details from session when not logged in. The endpoint should
        return a 401 error.
        """

        response = await self.client.get(self.url)
        self.assertEqual(response.status_code, status_codes.HTTP_401_UNAUTHORIZED)

    async def test_session_when_logged_in(self):
        """
        Test getting user details from session when logged in. The endpoint should return a 200
        response with a json object containing the user email and not an admin.
        """

        password = self.faker.password()
        user = await self.create_user(password=password)
        await self.login_user(email=user.email, password=password)
        response = await self.client.get(self.url)
        self.assertEqual(response.status_code, status_codes.HTTP_200_OK)
        self.assertEqual(response.json(), {"email": user.email, "admin": user.admin})

    async def test_session_when_logged_in_as_admin(self):
        """
        Test getting user details from session when logged in. The endpoint should return a 200
        response with a json object containing the user email and an admin.
        """

        password = self.faker.password()
        user = await self.create_user(password=password, admin=True)
        await self.login_user(email=user.email, password=password)
        response = await self.client.get(self.url)
        self.assertEqual(response.status_code, status_codes.HTTP_200_OK)
        self.assertEqual(response.json(), {"email": user.email, "admin": user.admin})
