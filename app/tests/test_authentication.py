from app.tests import BaseTestCase
from litestar import status_codes


class AuthenticationTestCase(BaseTestCase):
    async def test_login_with_non_existent_user(self):
        response = await self.client.post(
            "/auth/login", json={"email": "user@gmail.com", "password": "password"}
        )
        self.assertEqual(response.status_code, status_codes.HTTP_404_NOT_FOUND)
