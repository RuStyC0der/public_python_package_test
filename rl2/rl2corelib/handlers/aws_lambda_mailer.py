import json
import base64
import logging
import requests


class AwsLambdaMailer:
    def __init__(self, api_key, url):
        self.api_key = api_key
        self.url = url

    def __post_request(self, params=None, data=None):
        data = json.dumps(data)
        headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 Safari/537.36",
            'x-api-key': self.api_key,
        }
        r = requests.post(self.url, params=params, data=data, headers=headers)
        error_text = r.text if hasattr(r, 'text') else None
        if r.status_code in [200, 201]:
            data = r.json()
            return data['result']
        elif r.status_code == 404:
            data = r.json()
            raise Exception(f'{data["result"]}. Status code={r.status_code}, text={error_text}')
        else:
            raise Exception(f'Status code {r.status_code}. POST {self.url}, text={error_text}')

    def send_email(self, email_to, subject, body, attach_params=None, email_cc=None, email_bcc=None, html=True,
                   debug=False):
        """
        "attach_params": [{"local_file_name": 'd:/1.sql', "attach_file_name": "test_file_name.csv", "fl_binary": False}]
        """

        params = {
            'mail_to': email_to,
            'subject': subject,
            'body': body,
            'email_cc': email_cc,
            'email_bcc': email_bcc,
            'html': html,
            'debug': debug
        }

        attachments = []
        if attach_params:
            # encode attachment(s)
            for item in attach_params:
                file_name = item['local_file_name']
                logging.info(f'Attach "{file_name}"')
                with open(file_name, "rb") as f:
                    curr_attachment = base64.b64encode(f.read())

                fl_binary = item['fl_binary'] if 'fl_binary' in item else False
                attachments.append({'file_name': item['attach_file_name'], 'fl_binary': fl_binary,
                                    'file_body': str(curr_attachment),
                                   })
            logging.info(f'POST request with attachments')
            params['attach_params'] = attachments
        else:
            logging.info(f'POST request')
        return self.__post_request(data=params)
