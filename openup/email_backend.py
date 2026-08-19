from django.core.mail.backends.smtp import EmailBackend as DjangoSMTPBackend
from django.core.mail.utils import DNS_NAME


class EmailBackend(DjangoSMTPBackend):
    """
    Django 4.1's SMTP backend calls smtplib's starttls(keyfile=..., certfile=...),
    which Python 3.12 removed. Override open() to call starttls() the way
    Python 3.12's smtplib expects.
    """

    def open(self):
        if self.connection:
            return False

        connection_params = {"local_hostname": DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            connection_params["timeout"] = self.timeout
        if self.use_ssl:
            connection_params.update(
                {"keyfile": self.ssl_keyfile, "certfile": self.ssl_certfile}
            )
        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )
            if not self.use_ssl and self.use_tls:
                self.connection.starttls()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except OSError:
            if not self.fail_silently:
                raise
