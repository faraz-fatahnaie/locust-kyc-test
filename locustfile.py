from locust import HttpUser, task, SequentialTaskSet
from dotenv import load_dotenv
import json
import time
import os

# Load environment variables from .env file
load_dotenv()


class KnowMeSequenceOfTasks(SequentialTaskSet):

    def on_start(self):
        self.user_data = {}
        self.private_key = os.getenv("PRIVATE_KEY")
        self.public_key = os.getenv("PUBLIC_KEY")
        self.customer_id = os.getenv("CUSTOMER_ID")
        self.request_count = 0

    @task
    def create_and_stop_session(self):
        try:
            print('================= NEW SESSION ===================')
            create_session_res = self.create_session()

            if create_session_res.status_code == 201:
                self.register_variable(create_session_res)

                session_verification_res = self.session_verification()
                if session_verification_res.status_code == 200:
                    self.register_variable(session_verification_res)

                    upload_asset_res = self.upload_asset()

                    if upload_asset_res.status_code == 200:

                        self.register_variable(upload_asset_res)

                        # Wait for 5 seconds before stopping the session
                        time.sleep(5)
                        validate_make_result_res = self.validate_make_result()

                        if validate_make_result_res.status_code == 200:
                            # TODO: check the format of the respone (in queue or finished)
                            self.register_variable(validate_make_result_res)
                            print('+++++++++++++ END SESSION +++++++++++++++')
                        else:
                            print(
                                f"Error in POST request - validate_make_result: {validate_make_result_res.status_code}")

                    else:
                        print(f"Error in PATCH request - upload_asset: {upload_asset_res.status_code}")
                else:
                    print(f"Error in GET request - session_verification: {session_verification_res.status_code}")
            else:
                print(f"Error in POST request - create_session: {create_session_res.status_code}")

        except Exception as e:
            print(f"An error occurred: {e}")

    def create_session(self):
        try:
            # POST request to create session
            url_post = '/sessions/'
            headers_post = {'Content-Type': 'application/json', 'CUSTOMER-ID': f'{self.customer_id}'}
            data_post = {
                "service_codename": "liveness-verification-001",
                "national_code": "0021219958",
                "birthdate": 900460800
            }
            response = self.client.post(url_post, headers=headers_post, data=json.dumps(data_post))
            return response

        except Exception as e:
            print(f"An error occurred in create_session: {e}")

    def session_verification(self):
        try:
            session_token = self.user_data.get('token')

            # GET request to verify session creation
            url_get = f'/sessions/verify?token={session_token}'
            headers_get = {'PRIVATE-KEY': str(self.private_key), 'CUSTOMER-ID': str(self.customer_id)}
            response = self.client.get(url_get, headers=headers_get)
            return response

        except Exception as e:
            print(f"An error occurred in session_verification: {e}")

    def upload_asset(self):
        try:
            session_id = self.user_data.get('session_id')

            # PATCH request to send the image/video content
            url_patch = f'/sessions/session/{session_id}/'
            files = {
                'video_file': open(str('file/0021219958.webm'), 'rb')
            }

            data_patch = {
                'public_key': str(self.public_key)
            }
            headers_patch = {'CUSTOMER-ID': f'{self.customer_id}'}

            response = self.client.patch(url_patch,
                                         headers=headers_patch,
                                         files=files,
                                         data=data_patch,
                                         stream=True)
            return response

        except Exception as e:
            print(f"An error occurred in upload_asset: {e}")

    def validate_make_result(self):
        try:
            validation_token = self.user_data.get('validation_token')

            url_post = '/sessions/vamr/?timeout=30'
            headers_post = {'Content-Type': 'application/json'}
            data_post = {
                "validation_token": validation_token,
                "private_key": self.private_key
            }

            result_response = self.client.post(url_post, headers=headers_post, data=json.dumps(data_post))
            return result_response

        except Exception as e:
            print(f"An error occurred in validate_make_result: {e}")

    def register_variable(self, response):
        try:
            request_method = response.request.method
            if response.content:
                try:
                    json_response = response.json()
                    print(f'({request_method}) {json_response}')
                    self.user_data.update(json_response)
                except ValueError:
                    print(f"({request_method}) Response is not valid JSON:", response.content)
            else:
                print(f"({request_method}) Response is empty")
        except Exception as e:
            print(f"An error occurred while processing response: {e}")

    @staticmethod
    def random_username():
        return "random_username"

    @staticmethod
    def random_email():
        return "random_email@example.com"

    @staticmethod
    def random_company_name():
        return "random_company"


class LoggedInUser(HttpUser):
    host = "https://api.face-kyc.ir"
    # host = "http://localhost"
    # wait_time = between(4, 5)
    tasks = [KnowMeSequenceOfTasks]
    # max_requests = 5
