from http.server import HTTPServer, BaseHTTPRequestHandler
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.x509.oid import NameOID
from toolbox.pylog import pylog
from cryptography import x509
import mimetypes
import datetime
import ssl
import os

logging = pylog("logs/rose_%TIMENOW%.log")

# Fallback for if Certbot is not installed or a domain is not owned
def make_selfsigned_ssl(certfile_dir, keyfile_dir, hostname="localhost", expire_after=128):
    """
    Generates a self-signed SSL certificate and key if they do not exist.

    This function checks if the certificate and key files exist at the provided paths.
    If they do not exist, it generates a new RSA private key and a self-signed certificate,
    and writes them to the provided paths.

    Parameters:
    certfile_dir (str): The directory path where the certificate file will be stored.
    keyfile_dir (str): The directory path where the key file will be stored.
    hostname (str, optional): The common name to be used in the certificate. Defaults to "localhost".
    expire_after (int, optional): The number of days after which the certificate will expire. Defaults to 128.

    Returns:
    None
    """
    # Generate a self-signed certificate if it doesn't exist
    if not os.path.isfile(certfile_dir) or not os.path.isfile(keyfile_dir):
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        os.makedirs(os.path.dirname(certfile_dir), exist_ok=True)

        name = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"{}".format(hostname)),
        ])

        cert = x509.CertificateBuilder().subject_name(
            name
        ).issuer_name(
            name
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.now()
        ).not_valid_after(
            datetime.datetime.now() + datetime.timedelta(days=expire_after)
        ).sign(key, hashes.SHA256())

        # Write our certificate out to disk.
        with open(certfile_dir, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Write our key out to disk
        with open(keyfile_dir, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))

class webserver:
    def main(use_ssl: bool, content_dir: str):
        content_dir = os.path.abspath(content_dir)
        class HTTPRequestHandler(BaseHTTPRequestHandler):
            def log_message(self, _format, *args):
                message = f"{self.address_string()} - - [{self.log_date_time_string()}] {_format % args}"
                logging.info(message)

            def do_GET(self):
                path = self.path
                # Gets the abs path of the file requested
                target_file = os.path.join(content_dir, path[1:])

                if path == '/':
                    # If the path is just a slash, serve the index file
                    target_file = os.path.join(content_dir, 'index.html')

                # Assert that the file is within the content directory
                if not os.path.abspath(target_file).startswith(content_dir):
                    self.send_response(403)
                    self.end_headers()
                    self.wfile.write(b"403 - Forbidden")
                    return

                if os.path.exists(target_file):
                    with open(target_file, 'rb') as file:
                        self.send_response(200)
                        # Determine the MIME type of the file based on its extension
                        mime_type, _ = mimetypes.guess_type(target_file)
                        self.send_header('Content-type', mime_type or 'application/octet-stream')
                        self.end_headers()
                        self.wfile.write(file.read())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b"404 - Not Found")

        httpd = HTTPServer(('0.0.0.0', 8000), HTTPRequestHandler)

        if use_ssl:
            # Generate SSL certificate and key
            certfile_dir = 'toolbox/certificate.pem'
            keyfile_dir = 'toolbox/private.key'
            make_selfsigned_ssl(certfile_dir, keyfile_dir)

            # Load the certificate and key
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile_dir, keyfile_dir)

            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            httpd.server_close()
