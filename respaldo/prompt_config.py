# src/models/prompt_config.py
from src.extensions import db

class PromptConfig(db.Model):
    __tablename__ = 'prompt_configs'
    id = db.Column(db.String(50), primary_key=True) # ej: 'openai_kpi_finance'
    api_provider = db.Column(db.String(50), nullable=False) # ej: 'OpenAI'
    api_key = db.Column(db.String(255), nullable=False)
    prompt_template = db.Column(db.Text, nullable=False)
    model_name = db.Column(db.String(100), default='gpt-3.5-turbo')

    def to_dict(self):
        return {
            'id': self.id,
            'api_provider': self.api_provider,
            'prompt_template': self.prompt_template,
            'model_name': self.model_name
            # La API Key no se expone por seguridad
        }