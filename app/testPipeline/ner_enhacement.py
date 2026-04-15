# ner_enhancement.py

import spacy
from typing import Dict, List

class NEREnhancer:
    """Улучшение извлечения через NER"""
    
    def __init__(self):
        self.nlp = spacy.load("ru_core_news_sm")
    
    def extract_entities(self, text: str) -> Dict:
        """Извлечение сущностей"""
        doc = self.nlp(text)
        
        entities = {
            'organizations': [],
            'locations': [],
            'dates': [],
        }
        
        for ent in doc.ents:
            if ent.label_ == 'ORG':
                entities['organizations'].append(ent.text)
            elif ent.label_ == 'LOC':
                entities['locations'].append(ent.text)
            elif ent.label_ == 'DATE':
                entities['dates'].append(ent.text)
        
        return entities
    
    def enhance_data(self, extracted_data: Dict, text: str) -> Dict:
        """Дополнение данных через NER"""
        entities = self.extract_entities(text)
        
        # Если не нашли производителя регулярками
        if not extracted_data.get('manufacturer', {}).get('name'):
            # Берем первую найденную организацию
            if entities['organizations']:
                extracted_data['manufacturer']['name'] = entities['organizations'][0]
        
        return extracted_data