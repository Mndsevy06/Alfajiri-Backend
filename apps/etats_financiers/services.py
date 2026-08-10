from django.db.models import Sum, F, Q, Count
from django.db.models.functions import Coalesce
from decimal import Decimal
from apps.plan_comptable.models import CompteComptable
from apps.saisie.models import LigneEcriture, Ecriture
from apps.parametres.models import Dossier

def get_balance(date_debut=None, date_fin=None, compte_debut=None, compte_fin=None, journal=None, entite_id=None):
    """
    Retourne la balance de tous les comptes ayant eu un mouvement, avec solde d'ouverture,
    mouvements de la période et solde de clôture basés sur l'exercice comptable.
    """
    if entite_id:
        try:
            dossier = Dossier.objects.get(id=entite_id)
            if not date_debut:
                date_debut = dossier.dateDebut
            if not date_fin:
                date_fin = dossier.dateFin
        except Dossier.DoesNotExist:
            pass

    # Lignes avant la date de début (Solde d'ouverture)
    lignes_ouv = LigneEcriture.objects.filter(ecriture__statut=Ecriture.Statut.VALIDE)
    if entite_id:
        lignes_ouv = lignes_ouv.filter(dossier_id=entite_id)
    if date_debut:
        lignes_ouv = lignes_ouv.filter(date__lt=date_debut)
    if compte_debut:
        lignes_ouv = lignes_ouv.filter(compte__numero__gte=compte_debut)
    if compte_fin:
        lignes_ouv = lignes_ouv.filter(compte__numero__lte=compte_fin)

    ouv_data = lignes_ouv.values(
        'compte__numero', 'compte__libelle', 'compte__sens_normal', 'compte__code_poste_etats_financiers'
    ).annotate(
        total_debit=Coalesce(Sum('debit'), Decimal('0.00')),
        total_credit=Coalesce(Sum('credit'), Decimal('0.00')),
    )

    # Lignes dans la période (Mouvements)
    lignes_mvt = LigneEcriture.objects.filter(ecriture__statut=Ecriture.Statut.VALIDE)
    if entite_id:
        lignes_mvt = lignes_mvt.filter(dossier_id=entite_id)
    if date_debut:
        lignes_mvt = lignes_mvt.filter(date__gte=date_debut)
    if date_fin:
        lignes_mvt = lignes_mvt.filter(date__lte=date_fin)
    if compte_debut:
        lignes_mvt = lignes_mvt.filter(compte__numero__gte=compte_debut)
    if compte_fin:
        lignes_mvt = lignes_mvt.filter(compte__numero__lte=compte_fin)
    if journal:
        lignes_mvt = lignes_mvt.filter(ecriture__journal__code=journal)

    mvt_data = lignes_mvt.values(
        'compte__numero', 'compte__libelle', 'compte__sens_normal', 'compte__code_poste_etats_financiers'
    ).annotate(
        total_debit=Coalesce(Sum('debit'), Decimal('0.00')),
        total_credit=Coalesce(Sum('credit'), Decimal('0.00')),
    )

    comptes_dict = {}

    for row in ouv_data:
        c_num = row['compte__numero']
        diff = row['total_debit'] - row['total_credit']
        sd = diff if diff > 0 else Decimal('0.00')
        sc = abs(diff) if diff < 0 else Decimal('0.00')

        comptes_dict[c_num] = {
            'compte': c_num,
            'libelle': row['compte__libelle'],
            'sens_normal': row['compte__sens_normal'],
            'code_afs': row.get('compte__code_poste_etats_financiers') or '',
            'solde_ouv_debit': sd,
            'solde_ouv_credit': sc,
            'mvt_debit': Decimal('0.00'),
            'mvt_credit': Decimal('0.00'),
        }

    for row in mvt_data:
        c_num = row['compte__numero']
        if c_num not in comptes_dict:
            comptes_dict[c_num] = {
                'compte': c_num,
                'libelle': row['compte__libelle'],
                'sens_normal': row['compte__sens_normal'],
                'code_afs': row.get('compte__code_poste_etats_financiers') or '',
                'solde_ouv_debit': Decimal('0.00'),
                'solde_ouv_credit': Decimal('0.00'),
                'mvt_debit': Decimal('0.00'),
                'mvt_credit': Decimal('0.00'),
            }
        comptes_dict[c_num]['mvt_debit'] = row['total_debit']
        comptes_dict[c_num]['mvt_credit'] = row['total_credit']

    balance = []
    for c_num in sorted(comptes_dict.keys()):
        c = comptes_dict[c_num]

        total_debit_fin = c['solde_ouv_debit'] + c['mvt_debit']
        total_credit_fin = c['solde_ouv_credit'] + c['mvt_credit']
        diff = total_debit_fin - total_credit_fin

        solde_fin_debit = diff if diff > 0 else Decimal('0.00')
        solde_fin_credit = abs(diff) if diff < 0 else Decimal('0.00')

        c['solde_fin_debit'] = solde_fin_debit
        c['solde_fin_credit'] = solde_fin_credit
        c['debit'] = c['mvt_debit']
        c['credit'] = c['mvt_credit']
        c['solde_debit'] = solde_fin_debit
        c['solde_credit'] = solde_fin_credit

        balance.append(c)

    # ─── Sauvegarde des mouvements BRUTS avant roll-up ─────────────────────────
    # Ces valeurs représentent les mouvements DIRECTS de chaque compte,
    # sans agrégation des enfants. Leur somme sur tous les comptes
    # est garantie équilibrée (D = C) car toutes les écritures sont validées.
    for c_num in comptes_dict:
        c = comptes_dict[c_num]
        c['own_mvt_debit']     = c['mvt_debit']
        c['own_mvt_credit']    = c['mvt_credit']
        c['own_solde_ouv_debit']  = c['solde_ouv_debit']
        c['own_solde_ouv_credit'] = c['solde_ouv_credit']

    # ─── Roll-up : agrégation des enfants vers les parents ──────────────────────
    # On charge la carte parent une seule fois depuis la DB.
    all_comptes = CompteComptable.objects.all().select_related('parent')
    compte_objs = {c.numero: c for c in all_comptes}

    parent_map = {}
    for c in all_comptes:
        if c.parent:
            parent_map[c.numero] = c.parent.numero

    def get_parent_num(c_num):
        """Retourne le numéro du parent direct, ou None."""
        parent = parent_map.get(c_num)
        if not parent and len(c_num) > 4:
            # Fallback préfixe : 411101 → 4111, puis 411, etc.
            for length in range(len(c_num) - 1, 1, -1):
                candidate = c_num[:length]
                if candidate in compte_objs and candidate != c_num:
                    return candidate
        return parent

    # Trier les comptes du plus long au plus court (feuilles en premier)
    # pour garantir un seul passage sans récursion ni double-comptage.
    all_keys_sorted = sorted(comptes_dict.keys(), key=lambda x: -len(x))

    for c_num in all_keys_sorted:
        child = comptes_dict[c_num]
        parent_num = get_parent_num(c_num)
        if not parent_num:
            continue

        # Créer le parent à la volée s'il n'existe pas encore
        if parent_num not in comptes_dict:
            parent_obj = compte_objs.get(parent_num)
            comptes_dict[parent_num] = {
                'compte': parent_num,
                'libelle': parent_obj.libelle if parent_obj else parent_num,
                'sens_normal': parent_obj.sens_normal if parent_obj else 'aucun',
                'code_afs': (parent_obj.code_poste_etats_financiers or '') if parent_obj else '',
                'solde_ouv_debit': Decimal('0.00'),
                'solde_ouv_credit': Decimal('0.00'),
                'mvt_debit': Decimal('0.00'),
                'mvt_credit': Decimal('0.00'),
                'solde_fin_debit': Decimal('0.00'),
                'solde_fin_credit': Decimal('0.00'),
                'debit': Decimal('0.00'),
                'credit': Decimal('0.00'),
                'solde_debit': Decimal('0.00'),
                'solde_credit': Decimal('0.00'),
                'is_parent': True,
            }

        p = comptes_dict[parent_num]
        p.setdefault('is_parent', True)
        p['solde_ouv_debit'] += child['solde_ouv_debit']
        p['solde_ouv_credit'] += child['solde_ouv_credit']
        p['mvt_debit']  += child['mvt_debit']
        p['mvt_credit'] += child['mvt_credit']
        p['debit']  += child['debit']
        p['credit'] += child['credit']

        # Recalcul du solde de clôture du parent
        diff = (p['solde_ouv_debit'] + p['mvt_debit']) - (p['solde_ouv_credit'] + p['mvt_credit'])
        p['solde_fin_debit']  = diff if diff > 0 else Decimal('0.00')
        p['solde_fin_credit'] = abs(diff) if diff < 0 else Decimal('0.00')
        p['solde_debit']  = p['solde_fin_debit']
        p['solde_credit'] = p['solde_fin_credit']

    balance = list(comptes_dict.values())
    balance.sort(key=lambda x: x['compte'])
    return balance

def get_grand_livre(date_debut=None, date_fin=None, compte_debut=None, compte_fin=None, journal=None, entite_id=None):
    """
    Retourne le détail des écritures groupé par compte.
    """
    lignes = LigneEcriture.objects.filter(ecriture__statut=Ecriture.Statut.VALIDE).select_related(
        'ecriture', 'ecriture__journal', 'compte', 'ecriture__saisiePar', 'tiers_auxiliaire'
    ).order_by('compte__numero', 'date', 'ecriture__numero')
    
    if entite_id:
        lignes = lignes.filter(dossier_id=entite_id)
    else:
        lignes = lignes.none()
        
    if date_debut:
        lignes = lignes.filter(date__gte=date_debut)
    if date_fin:
        lignes = lignes.filter(date__lte=date_fin)
    if compte_debut:
        lignes = lignes.filter(compte__numero__gte=compte_debut)
    if compte_fin:
        lignes = lignes.filter(compte__numero__lte=compte_fin)
    if journal:
        lignes = lignes.filter(ecriture__journal__code=journal)
        
    grand_livre = {}
    for ligne in lignes:
        c_num = ligne.compte.numero
        if c_num not in grand_livre:
            grand_livre[c_num] = {
                'compte': c_num,
                'libelle': ligne.compte.libelle,
                'code_afs': ligne.compte.code_poste_etats_financiers or '',
                'total_debit': Decimal('0.00'),
                'total_credit': Decimal('0.00'),
                'ecritures': []
            }
            
        grand_livre[c_num]['ecritures'].append({
            'date': ligne.date,
            'journal': ligne.ecriture.journal.code,
            'piece': ligne.ecriture.piece or ligne.ecriture.numero,
            'batch_number': ligne.ecriture.numero,
            'numero_facture': ligne.ecriture.numero_facture,
            'libelle': ligne.libelle,
            'tiers_nom': ligne.tiers_auxiliaire.nom if ligne.tiers_auxiliaire else '',
            'tiers_code': ligne.tiers_auxiliaire.code if ligne.tiers_auxiliaire else '',
            'code_afs': ligne.compte.code_poste_etats_financiers or '',
            'debit': ligne.debit,
            'credit': ligne.credit,
            'devise_origine': ligne.devise_origine,
            'taux_change': ligne.taux_change,
            'montant_debit_origine': ligne.montant_debit_origine,
            'montant_credit_origine': ligne.montant_credit_origine,
            'saisi_par': ligne.ecriture.saisiePar.username if ligne.ecriture.saisiePar else 'Système',
            'saisi_le': ligne.ecriture.created_at.isoformat() if ligne.ecriture.created_at else None,
            'valide_le': ligne.ecriture.validated_at.isoformat() if ligne.ecriture.validated_at else None,
        })
        grand_livre[c_num]['total_debit'] += ligne.debit
        grand_livre[c_num]['total_credit'] += ligne.credit
        
    # Transformer en liste
    return list(grand_livre.values())

def get_balance_auxiliaire(date_debut=None, date_fin=None, compte_debut=None, compte_fin=None, journal=None, entite_id=None):
    """
    Balance auxiliaire générale : ventilation des mouvements par Tiers (fournisseurs, clients, etc.).
    Chaque ligne = un tiers × un compte général.
    Structure identique à la balance générale mais groupée par tiers_auxiliaire.
    Correspond à la 'Balance Auxiliaire' des fichiers EDC/IKO de référence.
    """
    from apps.plan_comptable.models import Tiers
    
    lignes = LigneEcriture.objects.filter(
        ecriture__statut=Ecriture.Statut.VALIDE,
        tiers_auxiliaire__isnull=False  # seulement les lignes avec un tiers
    ).select_related('ecriture', 'compte', 'tiers_auxiliaire', 'ecriture__journal')
    
    if entite_id:
        lignes = lignes.filter(dossier_id=entite_id)
    else:
        lignes = lignes.none()
    if date_debut:
        lignes = lignes.filter(date__gte=date_debut)
    if date_fin:
        lignes = lignes.filter(date__lte=date_fin)
    if compte_debut:
        lignes = lignes.filter(compte__numero__gte=compte_debut)
    if compte_fin:
        lignes = lignes.filter(compte__numero__lte=compte_fin)
    if journal:
        lignes = lignes.filter(ecriture__journal__code=journal)

    tiers_dict = {}
    for ligne in lignes:
        tiers = ligne.tiers_auxiliaire
        cle = f"{tiers.code}|{ligne.compte.numero}"
        
        if cle not in tiers_dict:
            tiers_dict[cle] = {
                'tiers_code': tiers.code,
                'tiers_nom': tiers.nom,
                'tiers_type': tiers.type,
                'compte': ligne.compte.numero,
                'libelle_compte': ligne.compte.libelle,
                'code_afs': ligne.compte.code_poste_etats_financiers or '',
                'mvt_debit': Decimal('0.00'),
                'mvt_credit': Decimal('0.00'),
            }
        
        tiers_dict[cle]['mvt_debit'] += ligne.debit
        tiers_dict[cle]['mvt_credit'] += ligne.credit

    result = []
    for item in tiers_dict.values():
        diff = item['mvt_debit'] - item['mvt_credit']
        item['solde_debit'] = diff if diff > 0 else Decimal('0.00')
        item['solde_credit'] = abs(diff) if diff < 0 else Decimal('0.00')
        result.append(item)
    
    # Tri par type de tiers, puis par code tiers, puis par compte
    result.sort(key=lambda x: (x['tiers_type'], x['tiers_code'], x['compte']))
    return result

def get_bilan(entite_id=None):
    """
    Construit le bilan à partir de la balance (comptes 1 à 5).
    """
    balance = get_balance(entite_id=entite_id)
    
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
        if poste_brut == 'Actif - Immobilisations' or poste_brut in ['AM', 'AN', 'AS']:
            bilan['actif']['actif_immobilise'].append(item)
            bilan['actif']['total'] += solde
        elif poste_brut == 'Actif - Stocks' or poste_brut == 'BB':
            bilan['actif']['actif_circulant'].append(item)
            bilan['actif']['total'] += solde
        elif poste_brut == 'Passif - Capitaux propres et Dettes' or poste_brut in ['CA', 'CE', 'CF', 'CH', 'CI', 'DA', 'DF']:
            if c_num.startswith('16') or poste_brut in ['DA', 'DF']:
                bilan['passif']['dettes_financieres'].append(item)
            else:
                bilan['passif']['capitaux_propres'].append(item)
            bilan['passif']['total'] += solde
        elif poste_brut == 'Actif/Passif - Tiers' or poste_brut in ['DK', 'DH', 'BH', 'BI', 'DI', 'DJ']:
            if solde > 0:
                bilan['actif']['actif_circulant'].append(item)
                bilan['actif']['total'] += solde
            else:
                item['montant'] = -solde
                bilan['passif']['passif_circulant'].append(item)
                bilan['passif']['total'] += -solde
        elif poste_brut == 'Actif/Passif - Trésorerie' or 'Trésorerie' in str(poste_brut) or poste_brut in ['BS', 'DQ']:
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

def get_compte_resultat(entite_id=None):
    """
    Construit le compte de résultat (comptes 6 et 7).
    """
    balance = get_balance(entite_id=entite_id)
    
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
        is_produit = (
            poste_brut == 'Compte de résultat - Produits' or 
            (isinstance(poste_brut, str) and (poste_brut.startswith('T') or poste_brut == 'RS')) or 
            c_num[0] == '7'
        )
        is_charge = (
            poste_brut == 'Compte de résultat - Charges' or 
            poste_brut == 'Compte de résultat - HAO' or
            (isinstance(poste_brut, str) and (poste_brut.startswith('R') or poste_brut in ['RP', 'TO'])) or 
            c_num[0] == '6' or c_num[0] == '8'
        )

        if is_produit:
            if c_num.startswith('77') or poste_brut == 'TK':
                cr['produits']['produits_financiers'].append(item)
            else:
                cr['produits']['produits_exploitation'].append(item)
            cr['produits']['total'] += solde
        elif is_charge:
            if c_num.startswith('67') or poste_brut == 'RK':
                cr['charges']['charges_financieres'].append(item)
            else:
                cr['charges']['charges_exploitation'].append(item)
            cr['charges']['total'] += solde

    cr['resultat_net'] = cr['produits']['total'] - cr['charges']['total']
    
    return cr

def get_journaux_centralisation(date_debut=None, date_fin=None, entite_id=None):
    """
    Retourne la centralisation des écritures par journal.
    """
    lignes = LigneEcriture.objects.filter(ecriture__statut=Ecriture.Statut.VALIDE)
    
    if entite_id:
        lignes = lignes.filter(dossier_id=entite_id)
    else:
        lignes = lignes.none()
        
    if date_debut:
        lignes = lignes.filter(date__gte=date_debut)
    if date_fin:
        lignes = lignes.filter(date__lte=date_fin)
        
    journaux_data = lignes.values(
        'ecriture__journal__code', 'ecriture__journal__libelle'
    ).annotate(
        # Bug #5 corrigé : total_mouvement = débit + crédit (volume total)
        total_mouvement=Coalesce(Sum('debit'), Decimal('0.00')) + Coalesce(Sum('credit'), Decimal('0.00')),
        nombre_ecritures=Count('ecriture', distinct=True)
    ).order_by('ecriture__journal__code')
    
    return list(journaux_data)

def get_tafire(entite_id=None):
    """
    Calcule le TAFIRE (Soldes Intermédiaires de Gestion simplifiés OHADA).
    """
    cr = get_compte_resultat(entite_id=entite_id)
    balance = {ligne['compte']: ligne for ligne in get_balance(entite_id=entite_id)}
    
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
