from django.test import TestCase
from api_punts_carrega.models import ModelCotxe, TipusCarregador

class ModelCotxeTests(TestCase):
    def test_creacio_model_cotxe(self):
        carregador = TipusCarregador.objects.create(nom_tipus='Type 2')

        cotxe = ModelCotxe.objects.create(
            model='Model S',
            marca='Tesla',
            any_model=2022,
        )
        cotxe.tipus_carregador.add(carregador)

        self.assertEqual(cotxe.model, 'Model S')
        self.assertEqual(cotxe.marca, 'Tesla')
        self.assertEqual(cotxe.any_model, 2022)
        self.assertIn(carregador, cotxe.tipus_carregador.all())
        self.assertEqual(str(cotxe), "Model Tesla Model S (2022)")
