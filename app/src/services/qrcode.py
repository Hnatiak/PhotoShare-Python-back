import io
import qrcode
from src.conf.config import settings


class QRCodeGenerator:
    def generate_qrcode(self, url: str):
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
