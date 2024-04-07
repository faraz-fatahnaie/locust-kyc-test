from locust import HttpUser, task, between, SequentialTaskSet
import json
import time


class MyUser(SequentialTaskSet):
    # wait_time = between(3, 4)  # wait time between tasks

    def on_start(self):
        self.user_data = {}
        self.private_key = "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlCT3dJQkFBSkJBSXZrdklTWUtZMS9FMHcyL2V0Q09GV3FaNzVMblIrUEV6K0Q0bDkvcTlBL0JvSmJ4bmVlCmg0N3JoSkdMaVZFWEs4cGM5dTBaMmZlMzU4R0YrVUJFTUhFQ0F3RUFBUUpBT2VpbzVSWjc5UGZLakQwalpWU1gKTDFjSDlPMG1FSjlRYjNWdnF1cVZaS2h6cjB6YlVFMnBYcSswb29TLzJ2UWQvNE9hQnNRM084Wm5kTi9wVWtNVQoxUUlqQU5MY2phcWRtQTZteTJQdllJRjA3MHphbHRRSmJyTnpaOEtrTnRKRFl5SnJIeXNDSHdDcDF3NUl2K1JhClVDWEhhR21HOWNPbHJpZngrWnc2eGtid2kyVXNnTk1DSW5abFBHNDJPckRQV3Boc1NpV21RTTlJVlRRTmI4ajIKM2FYZWlxR1pFTXE4bHkwQ0hua2o3SXRWVzdKVFFtOFYrVmNMQ3U2czVzOEFSRC9qMXd1UjBhdEpnd0lpTjdJQwpaR1duM3B3T3lzd0VtTFNHODUwRlpBbHBzbUk2WkwycVlRcThOQ0hQWmc9PQotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQo="
        self.public_key = "LS0tLS1CRUdJTiBSU0EgUFVCTElDIEtFWS0tLS0tCk1FZ0NRUUNMNUx5RW1DbU5meE5NTnYzclFqaFZxbWUrUzUwZmp4TS9nK0pmZjZ2UVB3YUNXOFozbm9lTzY0U1IKaTRsUkZ5dktYUGJ0R2RuM3QrZkJoZmxBUkRCeEFnTUJBQUU9Ci0tLS0tRU5EIFJTQSBQVUJMSUMgS0VZLS0tLS0K"
        self.customer_id = "2d2b50ce-0889-4165-9714-0b835fd7cf2f"
        self.request_count = 0

    @task
    def create_and_stop_session(self):
        try:
            print('==============================================')

            # POST request to create session
            url_post = '/sessions/'
            headers_post = {'Content-Type': 'application/json'}
            data_post = {
                "customer_id": self.customer_id,
                "service_codename": "liveness-verification-001",
                "national_code": "0021219958",
                "birth_date": "1377-04-24"
            }

            response = self.client.post(url_post, headers=headers_post, data=json.dumps(data_post))

            if response.status_code == 201:
                self.register_variable(response)
                session_token = self.user_data.get('token')

                # GET request to verify session creation
                url_get = f'/sessions/verify?token={session_token}'
                response = self.client.get(url_get)

                if response.status_code == 200:
                    self.register_variable(response)
                    session_id = self.user_data.get('session_id')

                    # PATCH request to send the image/video content
                    url_patch = f'/sessions/session/{session_id}/'
                    files = {
                        'query_face': open(str('/home/faraz/Downloads/faraz.jpg'), 'rb'),
                        'video_file': open(str('/home/faraz/Downloads/faraz.webm'), 'rb')
                    }


                    data_patch = {
                        'public_key': str(self.public_key)
                    }

                    response = self.client.patch(url_patch, files=files, data=data_patch, stream=True)

                    if response.status_code == 200:
                        self.register_variable(response)

                        # Wait for 5 seconds before stopping the session
                        time.sleep(5)
                        self.stop_session()

                    else:
                        print(f"Error in PATCH request: {response.status_code}")
                else:
                    print(f"Error in GET request for session verification: {response.status_code}")

        except Exception as e:
            print(f"An error occurred: {e}")

    def stop_session(self):
        print('++++++++++++++++++++++++++++++++++++++=')
        try:
            validation_token = self.user_data.get('validation_token')
            if validation_token:
                url_post = '/sessions/vamr/?timeout=30'
                headers_post = {'Content-Type': 'application/json'}
                data_post = {
                    "validation_token": validation_token,
                    "private_key": self.private_key
                }

                result_response = self.client.post(url_post, headers=headers_post, data=json.dumps(data_post))
                if result_response.status_code == 200:
                    self.register_variable(result_response)
                    print("Process completed successfully.")
                else:
                    print(f"Error in POST request for result: {result_response.status_code}")
        except Exception as e:
            print(f"An error occurred in on_stop: {e}")

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


class UserBehaviour(SequentialTaskSet):
    tasks = [MyUser]


class LoggedInUser(HttpUser):
    host = "http://localhost"
    # wait_time = between(4, 5)
    tasks = [UserBehaviour]
    # max_requests = 5
