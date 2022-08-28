import smtplib
import ssl
import os
from dotenv import load_dotenv

from email.mime.text import MIMEText


# ! use the .env file more
def send_mail(
    mail_text,
    port=465,
    sender='miguel.antoons@gmail.com',
    receiver='he201801@students.ephec.be',
    smtp_server='smtp.gmail.com',
    password=None
):
    """
    Function sends a given message to a given mail address

    Parameters
    ----------
    f : str
        text to send by mail
    port : int, optional
        port of the sender mail server, by default 465
    sender : str, optional
        sender e-mail address, by default miguel.antoons@gmail.com
    receiver : str, optional
        receiver e-mail address, by default he201801@students.ephec.be
    smtp_server : str, optional
        url of the sender mail server, by default smtp.gmail.com
    password : str, optional
        sender password, by default None
    """
    if password is None:
        # check if there is a password in the dotenv file
        load_dotenv()
        password = os.getenv('MAIL_PSWD')

    mail_text['From'] = sender
    mail_text['To'] = receiver

    # create a secure SSL context
    context = ssl.create_default_context()

    # send the mail
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        try:
            server.login(sender, password)
        except smtplib.SMTPAuthenticationError as e:
            print(e)
            print("""
                The server didn't accept the username/password combination.
            """)
        except smtplib.SMTPHeloError:
            print("""
                The server didn't reply properly to the HELO greeting.
            """)

        try:
            server.sendmail(sender, [receiver], mail_text.as_string())
        except smtplib.SMTPRecipientsRefused:
            print("""
                All recipients were refused. Nobody got the mail. The
                recipients attribute of the exception object is a dictionary
                with information about the refused recipients (like the one
                returned when at least one recipient was accepted).
            """)
        except smtplib.SMTPHeloError:
            print("""
                The server didn't reply properly to the HELO greeting.
            """)
        except smtplib.SMTPSenderRefused:
            print("""
                The server didn't accept the sender address.
            """)
        except smtplib.SMTPDataError:
            print("""
                The server replied with an unexpected error code (other than a
                refusal of a recipient).
            """)


if __name__ == '__main__':
    mail_text = MIMEText("Hi there, how are you?")
    mail_text['Subject'] = 'Test'

    send_mail(mail_text)
