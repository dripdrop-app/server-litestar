from litestar import status_codes

from app.tests import BaseTestCase


class LogoutTestCase(BaseTestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.url = "/api/auth/logout"

    async def test_logout_when_not_logged_in(self):
        """
        Test logging out when not logged in. The endpoint should
        return a 401 error.
        """

        response = await self.client.get(self.url)
        self.assertEqual(response.status_code, status_codes.HTTP_401_UNAUTHORIZED)

    async def test_session_when_logged_in(self):
        """
        Test logging out when logged in. The endpoint should return a 200
        response but with cleared cookies.
        """

        password = self.faker.password()
        user = await self.create_user(password=password)
        await self.login_user(email=user.email, password=password)
        response = await self.client.get(self.url)
        self.assertEqual(response.status_code, status_codes.HTTP_200_OK)
        self.assertEqual(self.client.cookies.get("session"), "null")
