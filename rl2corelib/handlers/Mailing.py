import boto3
from botocore.exceptions import ClientError
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

__version__ = "1.0"


class Mailing:
    def __init__(self, email_sender, aws_access_key_id=None, aws_secret_access_key=None, aws_region=None):
        self.email_sender = email_sender
        self.ses_client = boto3.client('ses', region_name=aws_region, aws_access_key_id=aws_access_key_id,
                                       aws_secret_access_key=aws_secret_access_key)

    @staticmethod
    def _prepare_email(email):
        if isinstance(email, str):
            return [email]
        return email

    def send_mail(self, email_to, subject, body, email_cc=None, email_bcc=None, html=True):
        destinations = {
            'ToAddresses': self._prepare_email(email_to)
        }
        if email_cc:
            destinations['CcAddresses'] = self._prepare_email(email_cc)
        if email_bcc:
            destinations['BccAddresses'] = self._prepare_email(email_bcc)

        if html:
            ses_body = {
                'Html': {
                    'Data': body,
                    'Charset': "UTF-8"
                },
            }
        else:
            ses_body = {
                'Text': {
                    'Data': body,
                    'Charset': "UTF-8"
                },
            }

        try:
            self.ses_client.send_email(
                Destination=destinations,
                Message={
                    'Body': ses_body,
                    'Subject': {
                        'Charset': "UTF-8",
                        'Data': subject
                    },
                },
                Source=self.email_sender
            )
        except ClientError as e:
            raise Exception(e.response['Error']['Message'] + ' ' + ','.join(destinations['ToAddresses']))

    def send_mail_with_attach(self, email_to_arg, subject, body, attach_data: str, attach_filename,
                              email_cc=None, email_bcc=None, html=True):
        email_to = self._prepare_email(email_to_arg)
        email_type = 'html' if html else 'plain'

        msg = MIMEMultipart()
        msg['From'] = self.email_sender
        msg['Subject'] = subject
        msg['Body'] = body

        msg['To'] = ','.join(email_to)
        if email_cc:
            msg['Cc'] = email_cc
        if email_bcc:
            msg['Bcc'] = email_bcc

        part = MIMEText(body, email_type)
        msg.attach(part)

        part = MIMEApplication(attach_data)
        part.add_header('Content-Disposition', 'attachment', filename=attach_filename)
        part.add_header('Content-Type', 'application/vnd.ms-excel; charset=UTF-8')
        msg.attach(part)

        self.ses_client.send_raw_email(
            Source=self.email_sender,
            RawMessage={
                'Data': msg.as_string(),
            }
        )
