from litestar import status_codes

from app.tests import BaseTestCase


class LoginTestCase(BaseTestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.url = "/api/auth/login"

    async def test_login_with_non_existent_user(self):
        """
        Test logging in with a user email that does not exist. The endpoint should
        return a 404 error.
        """

        response = await self.client.post(
            self.url,
            json={"email": self.faker.email(), "password": self.faker.password()},
        )
        self.assertEqual(response.status_code, status_codes.HTTP_404_NOT_FOUND)

    async def test_login_with_incorrect_password(self):
        """
        Test logging in with an incorrect password. The endpoint should return a
        401 status.
        """

        user = await self.create_user(password=self.faker.password())
        response = await self.client.post(
            self.url, json={"email": user.email, "password": self.faker.password()}
        )
        self.assertEqual(response.status_code, status_codes.HTTP_401_UNAUTHORIZED)

    async def test_login_with_unverified_user(self):
        """
        Test logging in with a user that is not verified. The endpoint should return a
        401 status.
        """

        password = self.faker.password()
        user = await self.create_user(password=password, verified=False)
        response = await self.client.post(
            self.url, json={"email": user.email, "password": password}
        )
        self.assertEqual(response.status_code, status_codes.HTTP_401_UNAUTHORIZED)

    async def test_login_with_correct_credentials(self):
        """
        Test logging in with correct credentials. The endpoint should return a 200 status
        and the session should be set with the correct user_id.
        """

        password = self.faker.password()
        user = await self.create_user(password=password)
        response = await self.client.post(
            self.url, json={"email": user.email, "password": password}
        )
        self.assertEqual(response.status_code, status_codes.HTTP_200_OK)
        self.assertIsNotNone(self.client.cookies.get("session"))
