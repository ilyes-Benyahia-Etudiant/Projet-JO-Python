import qrcode
import base64
from io import BytesIO

def generate_qr_code(data: str, box_size: int = 10, border: int = 4) -> str:
    """
    Génère un QR code à partir d'une chaîne de caractères et le retourne en base64.
    
    Args:
        data: La chaîne de caractères à encoder dans le QR code (généralement un token)
        box_size: La taille de chaque boîte du QR code
        border: La taille de la bordure du QR code
        
    Returns:
        Une chaîne de caractères représentant l'image du QR code encodée en base64
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir l'image en base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return f"data:image/png;base64,{img_str}"