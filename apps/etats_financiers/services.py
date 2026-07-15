from django.db.models import Sum, F, Q, Count
from django.db.models.functions import Coalesce
from decimal import Decimal
from apps.plan_comptable.models import CompteComptable
from apps.saisie.models import LigneEcriture, Ecriture

def get_balance(date_debut=None, date_fin=None):
    """
    Retourne la balance de tous les comptes ayant eu un mouvement.
    """
    lignes = LigneEcriture.objects.filter(ecriture__statut=Ecriture.Statut.VALIDE)
    
    if date_debut:
        lignes = lignes.filter(date__gte=date_debut)
    if date_fin:
        lignes = lignes.filter(date__lte=date_fin)
        
    comptes_mouvements = lignes.values(
        'compte__numero', 'compte__libelle', 'compte__sens_normal'
    ).annotate(
        total_debit=Coalesce(Sum('debit'), Decimal('0.00')),
        total_credit=Coalesce(Sum('credit'), Decimal('0.00')),
    ).order_by('compte__numero')

    balance = []
    for c in comptes_mouvements:
        solde_debit = Decimal('0.00')
        solde_credit = Decimal('0.00')
        
        diff = c['total_debit'] - c['total_credit']
        if diff > 0:
            solde_debit = diff
        elif diff < 0:
            solde_credit = abs(diff)

        balance.append({
            'compte': c['compte__numero'],
            'libelle': c['compte__libelle'],
            'sens_normal': c['compte__sens_normal'],
            'debit': c['total_debit'],
            'credit': c['total_credit'],
            'solde_debit': solde_debit,
            'solde_credit': solde_credit,
        })
        
    return balance

def get_grand_livre(date_debut=None, date_fin=None, compte_numero=None):
    """
    Retourne le détail des écritures groupé par compte.
    """
    lignes = LigneEcriture.objects.filter(ecriture__statut=Ecriture.Statut.VALIDE).select_related(
        'ecriture', 'ecriture__journal', 'compte'
    ).order_by('compte__numero', 'date', 'ecriture__numero')
    
    if date_debut:
        lignes = lignes.filter(date__gte=date_debut)
    if date_fin:
        lignes = lignes.filter(date__lte=date_fin)
    if compte_numero:
        lignes = lignes.filter(compte__numero__startswith=compte_numero)
        
    grand_livre = {}
    for ligne in lignes:
        c_num = ligne.compte.numero
        if c_num not in grand_livre:
            grand_livre[c_num] = {
                'compte': c_num,
                'libelle': ligne.compte.libelle,
                'total_debit': Decimal('0.00'),
                'total_credit': Decimal('0.00'),
                'ecritures': []
            }
            
        grand_livre[c_num]['ecritures'].append({
            'date': ligne.date,
            'journal': ligne.ecriture.journal.code,
            'piece': ligne.ecriture.piece or ligne.ecriture.numero,
            'libelle': ligne.libelle,
            'debit': ligne.debit,
            'credit': ligne.credit,
        })
        grand_livre[c_num]['total_debit'] += ligne.debit
        grand_livre[c_num]['total_credit'] += ligne.credit
        
    # Transformer en liste
    return list(grand_livre.values())

def get_bilan():
    """
    Construit le bilan à partir de la balance (comptes 1 à 5).
    """
    balance = get_balance()
    
    bilan = {
        'actif': {
            'actif_immobilise': [],
            'actif_circulant': [],
            'tresorerie_actif': [],
            'total': Decimal('0.00')
        },
        'passif': {
            'capitaux_propres': [],
            'dettes_financieres': [],
            'passif_circulant': [],
            'tresorerie_passif': [],
            'total': Decimal('0.00')
        },
        'resultat_net': Decimal('0.00')
    }

    comptes_db = {c.numero: c for c in CompteComptable.objects.all()}

    for ligne in balance:
        c_num = ligne['compte']
        # Ne traiter que les classes 1 à 5 pour le bilan
        if not c_num or c_num[0] not in ['1', '2', '3', '4', '5']:
            continue
            
        compte = comptes_db.get(c_num)
        poste_brut = compte.code_poste_etats_financiers if compte else None
        solde = ligne['solde_debit'] if ligne['solde_debit'] > 0 else -ligne['solde_credit']
        if solde == 0:
            continue
            
        item = {
            'poste': c_num,
            'libelle': compte.libelle if compte else 'Compte inconnu',
            'montant': solde,
            'is_debit': ligne['solde_debit'] > 0
        }

        # Mapping des catégories JSON vers notre dictionnaire
        if poste_brut == 'Actif - Immobilisations':
            bilan['actif']['actif_immobilise'].append(item)
            bilan['actif']['total'] += solde
        elif poste_brut == 'Actif - Stocks':
            bilan['actif']['actif_circulant'].append(item)
            bilan['actif']['total'] += solde
        elif poste_brut == 'Passif - Capitaux propres et Dettes':
            if c_num.startswith('16'):
                bilan['passif']['dettes_financieres'].append(item)
            else:
                bilan['passif']['capitaux_propres'].append(item)
            bilan['passif']['total'] += solde
        elif poste_brut == 'Actif/Passif - Tiers':
            if solde > 0:
                bilan['actif']['actif_circulant'].append(item)
                bilan['actif']['total'] += solde
            else:
                item['montant'] = -solde
                bilan['passif']['passif_circulant'].append(item)
                bilan['passif']['total'] += -solde
        elif poste_brut == 'Actif/Passif - Trésorerie' or 'Trésorerie' in str(poste_brut):
            if solde > 0:
                bilan['actif']['tresorerie_actif'].append(item)
                bilan['actif']['total'] += solde
            else:
                item['montant'] = -solde
                bilan['passif']['tresorerie_passif'].append(item)
                bilan['passif']['total'] += -solde
        else:
            # Fallback based on class number if parsing failed
            if c_num[0] == '2':
                bilan['actif']['actif_immobilise'].append(item)
                bilan['actif']['total'] += solde
            elif c_num[0] == '3':
                bilan['actif']['actif_circulant'].append(item)
                bilan['actif']['total'] += solde
            elif c_num[0] == '4':
                if solde > 0:
                    bilan['actif']['actif_circulant'].append(item)
                    bilan['actif']['total'] += solde
                else:
                    item['montant'] = -solde
                    bilan['passif']['passif_circulant'].append(item)
                    bilan['passif']['total'] += -solde
            elif c_num[0] == '5':
                if solde > 0:
                    bilan['actif']['tresorerie_actif'].append(item)
                    bilan['actif']['total'] += solde
                else:
                    item['montant'] = -solde
                    bilan['passif']['tresorerie_passif'].append(item)
                    bilan['passif']['total'] += -solde
            elif c_num[0] == '1':
                if c_num.startswith('16'):
                    bilan['passif']['dettes_financieres'].append(item)
                else:
                    bilan['passif']['capitaux_propres'].append(item)
                bilan['passif']['total'] += solde

    # Les provisions/amortissements réduisent l'actif
    for k in ['actif_immobilise', 'actif_circulant', 'tresorerie_actif']:
        for i in bilan['actif'][k]:
            if i['poste'].startswith('28') or i['poste'].startswith('29') or i['poste'].startswith('39') or i['poste'].startswith('49') or i['poste'].startswith('59'):
                pass

    # Note: L'ajustement amortissement est déjà géré par le solde de la balance (créditeur -> montant négatif ajouté à l'actif)
    
    resultat = bilan['actif']['total'] - bilan['passif']['total']
    bilan['resultat_net'] = resultat

    return bilan

def get_compte_resultat():
    """
    Construit le compte de résultat (comptes 6 et 7).
    """
    balance = get_balance()
    
    cr = {
        'produits': {
            'produits_exploitation': [],
            'produits_financiers': [],
            'total': Decimal('0.00')
        },
        'charges': {
            'charges_exploitation': [],
            'charges_financieres': [],
            'total': Decimal('0.00')
        },
        'resultat_net': Decimal('0.00')
    }

    comptes_db = {c.numero: c for c in CompteComptable.objects.all()}

    for ligne in balance:
        c_num = ligne['compte']
        # Ne traiter que les classes 6 et 7 pour le compte de résultat
        if not c_num or c_num[0] not in ['6', '7', '8']:
            continue
            
        compte = comptes_db.get(c_num)
        poste_brut = compte.code_poste_etats_financiers if compte else None
        # Charges augmentent au débit, Produits au crédit
        if c_num[0] == '6':
            solde = ligne['solde_debit'] if ligne['solde_debit'] > 0 else -ligne['solde_credit']
        else: # 7 et 8
            solde = ligne['solde_credit'] if ligne['solde_credit'] > 0 else -ligne['solde_debit']
            
        if solde == 0:
            continue
            
        item = {
            'poste': c_num,
            'libelle': compte.libelle if compte else 'Compte inconnu',
            'montant': solde,
        }

        # Mapping des catégories JSON
        if poste_brut == 'Compte de résultat - Produits' or c_num[0] == '7':
            if c_num.startswith('77'):
                cr['produits']['produits_financiers'].append(item)
            else:
                cr['produits']['produits_exploitation'].append(item)
            cr['produits']['total'] += solde
        elif poste_brut == 'Compte de résultat - Charges' or c_num[0] == '6':
            if c_num.startswith('67'):
                cr['charges']['charges_financieres'].append(item)
            else:
                cr['charges']['charges_exploitation'].append(item)
            cr['charges']['total'] += solde

    cr['resultat_net'] = cr['produits']['total'] - cr['charges']['total']
    
    return cr

def get_journaux_centralisation(date_debut=None, date_fin=None):
    """
    Retourne la centralisation des écritures par journal.
    """
    lignes = LigneEcriture.objects.filter(ecriture__statut=Ecriture.Statut.VALIDE)
    
    if date_debut:
        lignes = lignes.filter(date__gte=date_debut)
    if date_fin:
        lignes = lignes.filter(date__lte=date_fin)
        
    journaux_data = lignes.values(
        'ecriture__journal__code', 'ecriture__journal__libelle'
    ).annotate(
        total_mouvement=Coalesce(Sum('debit'), Decimal('0.00')),
        nombre_ecritures=Count('ecriture', distinct=True)
    ).order_by('ecriture__journal__code')
    
    return list(journaux_data)

def get_tafire():
    """
    Calcule le TAFIRE (Soldes Intermédiaires de Gestion simplifiés OHADA).
    """
    cr = get_compte_resultat()
    balance = {ligne['compte']: ligne for ligne in get_balance()}
    
    def sum_comptes(prefix, is_charge=False):
        total = Decimal('0.00')
        for c, data in balance.items():
            if c.startswith(prefix):
                solde = data['solde_debit'] if is_charge else data['solde_credit']
                total += solde
        return total

    ventes = sum_comptes('70')
    achats = sum_comptes('60', is_charge=True)
    marge_brute = ventes - achats
    
    consommations = sum_comptes('61', is_charge=True) + sum_comptes('62', is_charge=True)
    valeur_ajoutee = marge_brute - consommations
    
    impots = sum_comptes('64', is_charge=True)
    personnel = sum_comptes('63', is_charge=True)
    ebe = valeur_ajoutee - impots - personnel
    
    autres_produits = sum_comptes('75')
    autres_charges = sum_comptes('65', is_charge=True)
    resultat_exploitation = ebe + autres_produits - autres_charges
    
    produits_fin = sum_comptes('76') + sum_comptes('77')
    charges_fin = sum_comptes('66', is_charge=True) + sum_comptes('67', is_charge=True)
    resultat_financier = produits_fin - charges_fin
    
    resultat_net = resultat_exploitation + resultat_financier
    
    return [
        { "rubrique": "Marge brute sur marchandises", "calcul": "Ventes (70) - Achats (60)", "montant": marge_brute },
        { "rubrique": "Consommations en provenance de tiers", "calcul": "Transports (61) + Services ext. (62)", "montant": consommations },
        { "rubrique": "Valeur ajoutée", "calcul": "Marge brute - Consommations", "montant": valeur_ajoutee },
        { "rubrique": "Impôts et taxes", "calcul": "Classe 64", "montant": impots },
        { "rubrique": "Charges de personnel", "calcul": "Classe 63", "montant": personnel },
        { "rubrique": "Excédent brut d'exploitation (EBE)", "calcul": "VA - Impôts - Personnel", "montant": ebe },
        { "rubrique": "Autres produits", "calcul": "Classe 75", "montant": autres_produits },
        { "rubrique": "Autres charges", "calcul": "Classe 65", "montant": autres_charges },
        { "rubrique": "Résultat d'exploitation", "calcul": "EBE + Autres", "montant": resultat_exploitation },
        { "rubrique": "Produits financiers", "calcul": "Classes 76 + 77", "montant": produits_fin },
        { "rubrique": "Charges financières", "calcul": "Classes 66 + 67", "montant": charges_fin },
        { "rubrique": "Résultat financier", "calcul": "Produits fin. - Charges fin.", "montant": resultat_financier },
        { "rubrique": "Résultat net de l'exercice", "calcul": "Résultat exploitation + financier", "montant": resultat_net }
    ]
