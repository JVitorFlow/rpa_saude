import base64
import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
)


import json

from langchain.schema.messages import HumanMessage
from langchain_openai import ChatOpenAI

from src.config.config import Config
from src.config.logger import logger


class ImageAnalyzer:
    """
    Classe responsável por analisar imagens utilizando OpenAI GPT-4 Vision.
    """

    def __init__(self):

        """Inicializa a instância do analisador de imagens."""

        self.chat = ChatOpenAI(
            model='gpt-4o',
            max_tokens=512,
            api_key=Config.OPENAI_API_KEY,
        )

    def _encode_image(self, image_path):
        """
        Codifica a imagem para base64.

        Args:
            image_path (str): Caminho do arquivo da imagem.

        Returns:
            str: String base64 da imagem.
        """
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except FileNotFoundError:
            logger.error(f'Arquivo não encontrado: {image_path}')
            return None
        except Exception as e:
            logger.error(f'Erro ao codificar a imagem: {str(e)}')
            return None

    def analyze_image(self, image_path):
        """
        Analisa uma imagem de formulário médico e identifica campos marcados.

        Args:
            image_path (str): Caminho do arquivo da imagem.

        Returns:
            dict | str: JSON com as informações extraídas ou uma mensagem de erro.
        """
        base64_image = self._encode_image(image_path)
        if not base64_image:
            return 'Erro ao processar a imagem.'

        prompt = (
            "Você é um assistente especialista em análise de formulários médicos. "
            "Sua tarefa é analisar uma imagem de um formulário e extrair as marcações feitas na seção intitulada 'dados clínicos'.\n\n"
            "- Considere como marcação válida qualquer sinal manual visível, como um 'X', uma bolinha preenchida, traço ou outra marca dentro de caixas de seleção. "
            "- Para cada item marcado, transcreva exatamente como aparece no formulário: incluindo o nome da seção (ex: 'LNP - Biópsia de Lesão Não Palpável (Orientada)'), os códigos, descrições e observações adicionais (como 'NO POTE').\n"
            "- Agrupe os itens sob os títulos das seções correspondentes. "
            "- A saída deve ser simples: sem negrito, sem marcadores, sem numeração, sem formatação extra. "
            "- Não inclua frases introdutórias ou explicações. "
            "- Se nenhuma marcação for identificada, responda apenas com: 'Nenhuma marcação encontrada no formulário'."
        )

        human_message = [
            HumanMessage(content=prompt),
            HumanMessage(
                content=[
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/png;base64,{base64_image}',
                            'detail': 'auto',
                        },
                    }
                ]
            ),
        ]

        try:
            output = self.chat.invoke(human_message)
            result_data = output.content.strip()

            
            try:
                return json.loads(result_data)
            except json.JSONDecodeError:
                return {'response': result_data}

        except Exception as e:
            logger.error(f'Erro ao processar a imagem na OpenAI: {str(e)}')
            return 'Erro ao processar a imagem na OpenAI.'


if __name__ == '__main__':
    image_analyzer = ImageAnalyzer()
    resultado = image_analyzer.analyze_image('caminho/para/imagem.png')
    print(resultado)
