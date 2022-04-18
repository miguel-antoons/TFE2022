import smtplib
import ssl
import os


def send_mail(
    mail_text,
    port=465,
    sender='miguel.antoons@gmail.com',
    receiver='he201801@students.ephec.be',
    smtp_server='smtp.gmail.com',
    password=None
):
    if password is None:
        password = os.getenv('MAIL_PSWD')

    # create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        try:
            server.login(sender, password)
        except smtplib.SMTPAuthenticationError:
            print("""
                The server didn't accept the username/password combination.
            """)
        except smtplib.SMTPHeloError:
            print("""
                The server didn't reply properly to the HELO greeting.
            """)

        try:
            server.sendmail(sender, receiver, mail_text)
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
