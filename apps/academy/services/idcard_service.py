import io
from django.core.files.base import ContentFile
from django.utils import timezone


def _generate_qr_image(data: str) -> bytes:
    """
    Generate QR code PNG bytes.
    Requires: pip install qrcode[pil]
    If not available, returns a placeholder 1x1 white PNG.
    """
    try:
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()
    except ImportError:
        # Minimal 1×1 white PNG (fallback until qrcode is installed)
        import base64
        return base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI6QAAAABJRU5ErkJggg=='
        )


class IDCardService:

    @staticmethod
    def generate_qr(data: str) -> ContentFile:
        """Return QR code image as Django ContentFile."""
        return ContentFile(_generate_qr_image(data))

    @staticmethod
    def generate_card_number(student_id: int) -> str:
        year = timezone.now().year
        return f"AAA-{year}-{student_id:06d}"

    @staticmethod
    def issue_card(student, verification_url: str):
        """
        Issue (or re-issue) an ID card for a student.
        Generates QR code pointing to the verification URL.
        Returns the StudentIDCard instance.
        """
        from ..models import StudentIDCard

        card_number = IDCardService.generate_card_number(student.id)

        card, _ = StudentIDCard.objects.get_or_create(
            student=student,
            defaults={'card_number': card_number, 'is_valid': True},
        )
        card.card_number = card_number
        card.is_valid = True

        qr_data = IDCardService.generate_qr(verification_url)
        card.qr_code.save(f"idcards/qr_{student.id}.png", qr_data, save=False)
        card.save()
        return card
