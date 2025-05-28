from PIL import Image, ImageEnhance, ImageFilter


def preparar_imagem_para_ocr(imagem: Image.Image) -> Image.Image:
    """
    Prepara a imagem para OCR:
      - Converte para escala de cinza,
      - Aumenta o contraste,
      - Aplica filtro de nitidez.
    """
    imagem = imagem.convert("L")
    enhancer = ImageEnhance.Contrast(imagem)
    imagem = enhancer.enhance(2)
    imagem = imagem.filter(ImageFilter.SHARPEN)
    return imagem
