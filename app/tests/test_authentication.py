from app.tests import BaseTestCase
from litestar import status_codes


class AuthenticationTestCase(BaseTestCase):
    async def test_login_with_non_existent_user(self):
        response = await self.client.post(
            "/auth/login",
            json={"email": self.faker.email(), "password": self.faker.password()},
        )
        self.assertEqual(response.status_code, status_codes.HTTP_404_NOT_FOUND)

    async def test_login_with_incorrect_password(self):
        # user = await self.create_user(password="password123")
        response = await self.client.post(
            "/auth/login", json={"email": self.faker.email(), "password": "password123"}
        )
        self.assertEqual(response.status_code, status_codes.HTTP_400_BAD_REQUEST)
