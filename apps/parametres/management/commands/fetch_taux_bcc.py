import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal, InvalidOperation
from apps.parametres.models import TauxChange
import re

class Command(BaseCommand):
    help = "Récupère le taux de change du jour depuis le site de la BCC (bcc.cd)"

    def handle(self, *args, **options):
        url = "https://www.bcc.cd/"
        self.stdout.write(f"Connexion à {url}...")
        
        try:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, timeout=10, verify=False)
            response.raise_for_status()
        except requests.RequestException as e:
            self.stderr.write(f"Erreur de connexion : {e}")
            return
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Le taux est souvent affiché dans un bloc spécifique sur le site de la BCC.
        # En l'absence de l'API officielle, on cherche un texte du genre "1 USD = XXXX CDF"
        # ou on parse un tableau de taux indicatifs.
        
        # Stratégie générique : chercher le texte "USD" et extraire le chiffre proche
        texte_page = soup.get_text()
        
        # Regex pour trouver "1 USD = 2800.50 CDF" ou "USD/CDF : 2800"
        match = re.search(r'1?\s*USD\s*[=:-]?\s*([0-9\s,\.]+)\s*CDF', texte_page, re.IGNORECASE)
        
        taux_str = None
        if match:
            taux_str = match.group(1).replace(' ', '').replace(',', '.')
        else:
            # Chercher dans un format de tableau classique
            tds = soup.find_all('td')
            for i, td in enumerate(tds):
                if 'USD' in td.text.upper():
                    # Le taux est souvent dans la colonne suivante
                    if i + 1 < len(tds):
                        taux_str = tds[i+1].text.strip().replace(' ', '').replace(',', '.')
                        break
        
        if not taux_str:
            self.stderr.write("Impossible de trouver le taux USD/CDF sur la page.")
            return
            
        try:
            taux = Decimal(taux_str)
        except InvalidOperation:
            self.stderr.write(f"Valeur de taux invalide trouvée : {taux_str}")
            return
            
        date_jour = timezone.now().date()
        
        obj, created = TauxChange.objects.update_or_create(
            devise='CDF',
            date=date_jour,
            defaults={'taux': taux}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Taux du jour enregistré : 1 USD = {taux} CDF (Date: {date_jour})"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Taux du jour mis à jour : 1 USD = {taux} CDF (Date: {date_jour})"))
