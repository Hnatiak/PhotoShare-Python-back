import io
import qrcode
from src.conf.config import settings


class QRCodeGenerator:
    """
    Generates QR code images for URLs.
    This class provides a method to generate QR code images representing the provided URLs.
    """
    def generate_qrcode(self, url: str):
        """
        Generates a QR code image for the given URL.

        This method creates a QR code object using the error correction level, box size, and border
        settings configured in the application settings. The provided URL is encoded as data in the QR code.
        Finally, an image is generated using the specified fill color and background color settings.

        Args:
            url (str): The URL to encode in the QR code.
        Returns:
            bytes: The QR code image data in bytes format.
        """
        qr_code = qrcode.QRCode(
            error_correction=settings.qr_error_correction,
            box_size=settings.qr_box_size,
            border=settings.qr_border,
        )
        qr_code.add_data(url)
        qr_code.make(fit=True)
        img = qr_code.make_image(fill_color=settings.qr_fill_color, back_color=settings.qr_back_color)
        output = io.BytesIO()
        img.save(output)
        output.seek(0)

        return output
    
qrcode_service = QRCodeGenerator() 
