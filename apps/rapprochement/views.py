from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import transaction
from django.db.models import Sum
import csv
import io
import datetime

from .models import LigneReleve, Rapprochement
from apps.saisie.models import LigneEcriture, Ecriture
from apps.plan_comptable.models import CompteComptable, Journal
from .serializers import LigneReleveSerializer, LigneEcritureRapprochementSerializer

class LigneReleveView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        # Lignes non pointées
        lignes = LigneReleve.objects.filter(rapprochement__isnull=True)
        if entite_id:
            lignes = lignes.filter(dossier_id=entite_id)
        else:
            lignes = lignes.none()
        lignes = lignes.order_by('date')
        serializer = LigneReleveSerializer(lignes, many=True)
        return Response(serializer.data)

class LigneComptaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        compte = request.query_params.get('compte', '521')
        lignes = LigneEcriture.objects.filter(
            compte__numero__startswith=compte[:2],
            rapprochement__isnull=True
        )
        if entite_id:
            lignes = lignes.filter(dossier_id=entite_id)
        else:
            lignes = lignes.none()
        lignes = lignes.order_by('date')
        serializer = LigneEcritureRapprochementSerializer(lignes, many=True)
        return Response(serializer.data)

class ImportReleveView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'Aucun fichier fourni'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            decoded_file = file_obj.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string, delimiter=';')
            
            lignes_creees = 0
            for row in reader:
                date_str = row.get('Date', row.get('date'))
                libelle = row.get('Libelle', row.get('libelle', row.get('Description', '')))
                montant_str = row.get('Montant', row.get('montant', '0')).replace(',', '.')
                reference = row.get('Reference', row.get('reference', ''))
                
                try:
                    montant = float(montant_str)
                    sens = LigneReleve.Sens.CREDIT if montant > 0 else LigneReleve.Sens.DEBIT
                    date_obj = datetime.datetime.strptime(date_str, '%d/%m/%Y').date() if '/' in date_str else datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    LigneReleve.objects.create(
                        dossier_id=entite_id,
                        date=date_obj,
                        libelle=libelle,
                        reference=reference,
                        montant=abs(montant),
                        sens=sens
                    )
                    lignes_creees += 1
                except Exception as e:
                    print(f"Erreur sur la ligne {row}: {e}")
                    continue
                    
            return Response({'message': f'{lignes_creees} lignes importées avec succès.'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LettrageManuelView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        releve_ids = request.data.get('releve_ids', [])
        compta_ids = request.data.get('compta_ids', [])

        if not releve_ids and not compta_ids:
            return Response({'error': 'Sélectionnez au moins une ligne.'}, status=status.HTTP_400_BAD_REQUEST)

        releves = LigneReleve.objects.filter(id__in=releve_ids, rapprochement__isnull=True)
        comptas = LigneEcriture.objects.filter(id__in=compta_ids, rapprochement__isnull=True)
        if entite_id:
            releves = releves.filter(dossier_id=entite_id)
            comptas = comptas.filter(dossier_id=entite_id)
        else:
            releves = releves.none()
            comptas = comptas.none()

        if len(releves) != len(releve_ids) or len(comptas) != len(compta_ids):
            return Response({'error': 'Certaines lignes sont déjà lettrées ou introuvables.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate totals
        total_releve = sum([r.montant if r.sens == 'credit' else -r.montant for r in releves])
        total_compta = sum([c.debit - c.credit for c in comptas]) # Debit in compta is + for bank

        if abs(float(total_releve) - float(total_compta)) > 0.01:
            return Response({'error': f'Écart non nul. Relevé: {total_releve}, Compta: {total_compta}'}, status=status.HTTP_400_BAD_REQUEST)

        # Create Rapprochement
        rapprochement = Rapprochement.objects.create(valide_par=request.user, dossier_id=entite_id)
        
        for r in releves:
            r.rapprochement = rapprochement
            r.pointe = True
            r.save()
            
        for c in comptas:
            c.rapprochement = rapprochement
            # c.pointe = True # if we add pointe to LigneEcriture, else just foreign key is enough
            c.save()

        return Response({'message': 'Lettrage effectué avec succès.', 'id': rapprochement.id}, status=status.HTTP_200_OK)

class LettrageAutoView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        releves = LigneReleve.objects.filter(rapprochement__isnull=True)
        comptas = LigneEcriture.objects.filter(compte__numero__startswith='52', rapprochement__isnull=True)
        if entite_id:
            releves = releves.filter(dossier_id=entite_id)
            comptas = comptas.filter(dossier_id=entite_id)
        else:
            releves = releves.none()
            comptas = comptas.none()
        
        matched_count = 0
        for r in releves:
            # Look for exact amount match within +/- 3 days
            # Note: bank debit means compta credit. bank credit means compta debit.
            target_amount = r.montant
            
            match = None
            for c in comptas:
                if c.rapprochement is not None:
                    continue
                
                c_amount = c.debit if r.sens == 'credit' else c.credit
                if abs(float(c_amount) - float(target_amount)) < 0.01:
                    # check date +/- 5 days
                    diff = (r.date - c.date).days
                    if -5 <= diff <= 5:
                        match = c
                        break
            
            if match:
                rapprochement = Rapprochement.objects.create(valide_par=request.user, dossier_id=entite_id)
                r.rapprochement = rapprochement
                r.pointe = True
                r.save()
                match.rapprochement = rapprochement
                match.save()
                matched_count += 1

        return Response({'message': f'Lettrage automatique terminé. {matched_count} correspondances trouvées.'}, status=status.HTTP_200_OK)

class GenererODView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        entite_id = request.headers.get('X-Entite-ID')
        releve_id = request.data.get('releve_id')
        compte_od_numero = request.data.get('compte_od') # e.g. '627'
        compte_banque_numero = request.data.get('compte_banque', '521')
        
        try:
            releve = LigneReleve.objects.get(id=releve_id, rapprochement__isnull=True)
            if entite_id and str(releve.dossier_id) != str(entite_id):
                return Response({'error': 'Ligne de relevé introuvable ou déjà rapprochée.'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                compte_od = CompteComptable.objects.get(numero=compte_od_numero)
            except CompteComptable.DoesNotExist:
                return Response({'error': f"Le compte OD spécifié '{compte_od_numero}' n'existe pas dans le plan comptable."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                compte_banque = CompteComptable.objects.get(numero=compte_banque_numero)
            except CompteComptable.DoesNotExist:
                return Response({'error': f"Le compte de banque '{compte_banque_numero}' n'existe pas."}, status=status.HTTP_400_BAD_REQUEST)

            journal = Journal.objects.filter(type='banque').first()
            if not journal:
                journal = Journal.objects.first()
                if not journal:
                    return Response({'error': "Aucun journal n'existe dans le système."}, status=status.HTTP_400_BAD_REQUEST)
        except LigneReleve.DoesNotExist:
            return Response({'error': 'Ligne de relevé introuvable ou déjà rapprochée.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Create Ecriture
        ecriture = Ecriture.objects.create(
            dossier_id=entite_id,
            numero=f"OD-{datetime.date.today().strftime('%Y%m')}-{releve.id.hex[:6].upper()}",
            journal=journal,
            date=releve.date,
            libelle=releve.libelle,
            statut='valide',
            saisiePar=request.user,
            validePar=request.user
        )

        # Create Lignes
        if releve.sens == 'debit':
            # Bank took money: OD is debited, Bank is credited
            debit_cpt = compte_od
            credit_cpt = compte_banque
        else:
            # Bank received money: Bank is debited, OD is credited
            debit_cpt = compte_banque
            credit_cpt = compte_od

        LigneEcriture.objects.create(
            dossier_id=entite_id,
            ecriture=ecriture,
            date=releve.date,
            compte=debit_cpt,
            libelle=releve.libelle,
            debit=releve.montant,
            credit=0
        )
        
        ligne_banque = LigneEcriture.objects.create(
            dossier_id=entite_id,
            ecriture=ecriture,
            date=releve.date,
            compte=credit_cpt,
            libelle=releve.libelle,
            debit=0,
            credit=releve.montant
        )

        # Rapprochement
        rapprochement = Rapprochement.objects.create(valide_par=request.user, dossier_id=entite_id)
        releve.rapprochement = rapprochement
        releve.pointe = True
        releve.save()
        
        ligne_banque.rapprochement = rapprochement
        ligne_banque.save()

        return Response({'message': 'OD générée avec succès.', 'ecriture_numero': ecriture.numero}, status=status.HTTP_201_CREATED)
