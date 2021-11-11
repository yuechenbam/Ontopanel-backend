from django.http import response
from rest_framework.test import APITestCase
from django.urls import reverse
from django.core import mail
from rest_framework import status


class TestSetUp(APITestCase):
    def setUp(self):
        self.user_data = {
            "email": "email@gmail.com",
            "password": "username1234",
        }
        return super().setUp()

    def tearDown(self):
        return super().tearDown()


class TestViews(TestSetUp):

    def test_user_register(self):
        response = self.client.post(reverse("register"), self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_login(self):
        self.client.post(reverse("register"), self.user_data)
        response = self.client.post(reverse("login"), {
                                    'username': self.user_data['email'], 'password': self.user_data['password']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_logout(self):
        self.client.post(reverse("register"), self.user_data)
        login_response = self.client.post(reverse("login"), {
                                          'username': self.user_data['email'], 'password': self.user_data['password']})
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {login_response.data['token']}"
        )
        logout_response = self.client.get(reverse("logout"))
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # try get
        onto_response = self.client.get(
            reverse("onto_lists"))
        self.assertEqual(onto_response.status_code,
                         status.HTTP_401_UNAUTHORIZED)

    def test_user_reset_password(self):
        self.client.post(reverse("register"), self.user_data)

        with self.settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            # email exist
            self.client.post(reverse("reset_password"), {
                             "email": self.user_data["email"]})

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject, "Verfiy your email")

            email_body = mail.outbox[0].body
            secret_key = email_body[
                email_body.index("corresponding form:")
                + len("corresponding form:"): email_body.index("Thanks for")
            ]

            # right secret key

            confirm_response = self.client.patch(
                reverse("reset_confirm"),
                {"secret_key": secret_key, "password": "1234username"},
            )
            self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)

            # wrong secret key

            wrong_confirm_response = self.client.patch(
                reverse("reset_confirm"),
                {"secret_key": secret_key + "a", "password": "1234username"},
            )
            self.assertEqual(
                wrong_confirm_response.status_code, status.HTTP_401_UNAUTHORIZED
            )

            # email does not exist
            reset_response = self.client.post(
                reverse("reset_password"), {"email": "noexist@gmail.com"}
            )
            self.assertEqual(
                reset_response.status_code,
                status.HTTP_400_BAD_REQUEST,
            )
