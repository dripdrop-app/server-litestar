from unittest.mock import MagicMock, patch

from litestar import status_codes

from app.tests import BaseTestCase, test_enqueue_task


class CreateTestCase(BaseTestCase):
    def __init__(self, methodName="runTest"):
        super().__init__(methodName)
        self.url = "/api/auth/create"

    async def test_create_when_user_exists(self):
        """
        Test creating a user when an account with the email exists. The endpoint should
        return a 400 error.
        """

        user = await self.create_user()
        response = await self.client.post(
            self.url, json={"email": user.email, "password": self.faker.password()}
        )
        self.assertEqual(response.status_code, status_codes.HTTP_400_BAD_REQUEST)

    @patch("app.controllers.authentication.enqueue_task", test_enqueue_task)
    @patch("app.clients.smtp2go.send_email")
    async def test_create(self, mock_send_email: MagicMock):
        """
        Test creating an account. The endpoint should return a 200
        response and the user should not be verified.
        """

        email = self.faker.email()
        response = await self.client.post(
            self.url, json={"email": email, "password": self.faker.password()}
        )
        self.assertEqual(response.status_code, status_codes.HTTP_200_OK)
        mock_send_email.assert_called_once()
        kwargs = mock_send_email.call_args.kwargs
        self.assertEqual(kwargs["sender"], "app@dripdrop.pro")
        self.assertEqual(kwargs["recipient"], email)
        self.assertEqual(kwargs["subject"], "Verification")
