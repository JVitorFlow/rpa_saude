from PIL import Image
import tempfile
from pathlib import Path

def converter_tif_para_jpg(caminho_tif: Path) -> Path:
    """
    Converte um arquivo .tif para .jpg e retorna o caminho temporário do novo arquivo.
    """
    if not caminho_tif.exists() or not caminho_tif.suffix.lower() in [".tif", ".tiff"]:
        raise ValueError("Arquivo inválido ou extensão não suportada para conversão.")

    with Image.open(caminho_tif) as img:
        img = img.convert('RGB')  # Garante que a imagem esteja no modo correto
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            img.save(tmp.name, format="JPEG")
            return Path(tmp.name)
