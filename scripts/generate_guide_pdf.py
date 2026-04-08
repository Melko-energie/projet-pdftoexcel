"""Genere un guide d'utilisation PDF design et professionnel pour Melko Energie.

Usage :
    venv\\Scripts\\python.exe scripts\\generate_guide_pdf.py

Produit le fichier "Guide_Utilisation_Melko.pdf" a la racine du projet.
"""

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable

# ========================================================================
# CHARTE GRAPHIQUE MELKO
# ========================================================================

PRIMARY = colors.HexColor("#0E5C5E")        # Teal/petroleum profond
PRIMARY_DARK = colors.HexColor("#073538")   # Teal tres fonce
ACCENT = colors.HexColor("#A4D65E")         # Lime energique
ACCENT_DARK = colors.HexColor("#7BAA3D")    # Lime fonce
DARK = colors.HexColor("#1A1A1A")           # Noir doux
GRAY = colors.HexColor("#666666")           # Gris moyen
LIGHT_GRAY = colors.HexColor("#F5F5F5")     # Gris tres clair
MEDIUM_GRAY = colors.HexColor("#E0E0E0")    # Gris moyen-clair
WHITE = colors.HexColor("#FFFFFF")
WARNING_BG = colors.HexColor("#FFF8E7")     # Fond orange tres clair (callout)
WARNING_BORDER = colors.HexColor("#E8A317") # Orange (callout border)
INFO_BG = colors.HexColor("#E8F4F4")        # Fond teal clair (info)
INFO_BORDER = PRIMARY                       # Border info

PAGE_MARGIN = 2 * cm

# ========================================================================
# STYLES
# ========================================================================

styles = getSampleStyleSheet()

style_cover_title = ParagraphStyle(
    "CoverTitle",
    parent=styles["Title"],
    fontSize=42,
    leading=50,
    textColor=PRIMARY,
    alignment=TA_LEFT,
    fontName="Helvetica-Bold",
    spaceAfter=10,
)

style_cover_subtitle = ParagraphStyle(
    "CoverSubtitle",
    parent=styles["Normal"],
    fontSize=18,
    leading=24,
    textColor=DARK,
    alignment=TA_LEFT,
    fontName="Helvetica",
    spaceAfter=30,
)

style_cover_brand = ParagraphStyle(
    "CoverBrand",
    parent=styles["Normal"],
    fontSize=14,
    leading=18,
    textColor=GRAY,
    alignment=TA_LEFT,
    fontName="Helvetica-Bold",
)

style_cover_meta = ParagraphStyle(
    "CoverMeta",
    parent=styles["Normal"],
    fontSize=10,
    leading=14,
    textColor=GRAY,
    alignment=TA_LEFT,
    fontName="Helvetica",
)

style_h1 = ParagraphStyle(
    "H1",
    parent=styles["Heading1"],
    fontSize=22,
    leading=28,
    textColor=PRIMARY,
    fontName="Helvetica-Bold",
    spaceBefore=18,
    spaceAfter=10,
    keepWithNext=True,
)

style_h2 = ParagraphStyle(
    "H2",
    parent=styles["Heading2"],
    fontSize=16,
    leading=22,
    textColor=PRIMARY_DARK,
    fontName="Helvetica-Bold",
    spaceBefore=14,
    spaceAfter=6,
    keepWithNext=True,
)

style_h3 = ParagraphStyle(
    "H3",
    parent=styles["Heading3"],
    fontSize=12,
    leading=16,
    textColor=DARK,
    fontName="Helvetica-Bold",
    spaceBefore=10,
    spaceAfter=4,
    keepWithNext=True,
)

style_body = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontSize=10,
    leading=15,
    textColor=DARK,
    fontName="Helvetica",
    alignment=TA_JUSTIFY,
    spaceAfter=8,
)

style_body_left = ParagraphStyle(
    "BodyLeft",
    parent=style_body,
    alignment=TA_LEFT,
)

style_bullet = ParagraphStyle(
    "Bullet",
    parent=style_body,
    leftIndent=15,
    bulletIndent=5,
    spaceAfter=4,
    alignment=TA_LEFT,
)

style_callout_title = ParagraphStyle(
    "CalloutTitle",
    parent=style_body,
    fontSize=10,
    fontName="Helvetica-Bold",
    textColor=PRIMARY_DARK,
    spaceAfter=4,
    alignment=TA_LEFT,
)

style_callout_body = ParagraphStyle(
    "CalloutBody",
    parent=style_body,
    fontSize=9.5,
    leading=14,
    alignment=TA_LEFT,
    spaceAfter=2,
)

style_code = ParagraphStyle(
    "Code",
    parent=styles["Code"],
    fontSize=9,
    leading=13,
    textColor=DARK,
    fontName="Courier",
    backColor=LIGHT_GRAY,
    borderColor=MEDIUM_GRAY,
    borderWidth=0.5,
    borderPadding=8,
    leftIndent=0,
    rightIndent=0,
    spaceBefore=6,
    spaceAfter=10,
)

style_table_header = ParagraphStyle(
    "TableHeader",
    parent=style_body,
    fontSize=9.5,
    fontName="Helvetica-Bold",
    textColor=WHITE,
    alignment=TA_LEFT,
    spaceAfter=0,
    leading=12,
)

style_table_cell = ParagraphStyle(
    "TableCell",
    parent=style_body,
    fontSize=9,
    leading=12,
    alignment=TA_LEFT,
    spaceAfter=0,
)

style_toc_entry = ParagraphStyle(
    "TocEntry",
    parent=style_body,
    fontSize=11,
    leading=20,
    fontName="Helvetica",
    alignment=TA_LEFT,
    spaceAfter=2,
)


# ========================================================================
# COMPOSANTS REUTILISABLES
# ========================================================================

def make_callout(title: str, body: str, kind: str = "info") -> Table:
    """Cree un encadre type 'callout' avec titre et corps."""
    if kind == "warning":
        bg = WARNING_BG
        border = WARNING_BORDER
        icon = "&#9888;"  # warning symbol
    else:
        bg = INFO_BG
        border = INFO_BORDER
        icon = "&#9432;"  # info symbol

    title_para = Paragraph(f"<font color='{border.hexval()}'>{icon}</font> &nbsp;{title}", style_callout_title)
    body_para = Paragraph(body, style_callout_body)

    inner = [[title_para], [body_para]]
    t = Table(inner, colWidths=[16 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def make_data_table(headers: list[str], rows: list[list[str]], col_widths: list[float] = None) -> Table:
    """Cree un tableau de donnees stylise avec header colore et zebra rows."""
    # Construire les paragraphes pour wrap automatique
    head_paragraphs = [Paragraph(h, style_table_header) for h in headers]
    data = [head_paragraphs]
    for row in rows:
        data.append([Paragraph(c, style_table_cell) for c in row])

    if col_widths is None:
        col_widths = [16 * cm / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9.5),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        # Body
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("VALIGN", (0, 1), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, MEDIUM_GRAY),
    ]
    # Zebra rows
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), LIGHT_GRAY))
    t.setStyle(TableStyle(style_cmds))
    return t


def section_header(number: str, title: str) -> Table:
    """Cree un en-tete de section visuel : grosse pastille + titre."""
    num_para = Paragraph(f"<font color='white' size='20'><b>{number}</b></font>", ParagraphStyle("n", parent=style_body, alignment=TA_CENTER))
    title_para = Paragraph(f"<font size='20' color='{PRIMARY.hexval()}'><b>{title}</b></font>", ParagraphStyle("st", parent=style_body, alignment=TA_LEFT))
    t = Table([[num_para, title_para]], colWidths=[1.4 * cm, 14.6 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), PRIMARY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (0, 0), 0),
        ("RIGHTPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 0), (0, 0), 4),
        ("BOTTOMPADDING", (0, 0), (0, 0), 4),
        ("LEFTPADDING", (1, 0), (1, 0), 12),
        ("LINEBELOW", (0, 0), (-1, -1), 2, ACCENT),
    ]))
    return t


# ========================================================================
# PAGE TEMPLATES
# ========================================================================

def cover_page(canvas, doc):
    """Dessine la page de couverture en fond."""
    canvas.saveState()
    width, height = A4

    # Fond degrade simule par bandes
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, 0, width, height, stroke=0, fill=1)

    # Bande accent en bas
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 0, width, 1.2 * cm, stroke=0, fill=1)

    # Bande accent verticale a gauche
    canvas.setFillColor(ACCENT)
    canvas.rect(0, 1.2 * cm, 0.8 * cm, height - 1.2 * cm, stroke=0, fill=1)

    # Logo carre stylise (placeholder pour le logo Melko)
    canvas.setFillColor(WHITE)
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(3)
    logo_size = 3 * cm
    logo_x = width - logo_size - 2 * cm
    logo_y = height - logo_size - 2 * cm
    canvas.rect(logo_x, logo_y, logo_size, logo_size, stroke=1, fill=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 28)
    canvas.drawCentredString(logo_x + logo_size / 2, logo_y + logo_size / 2 - 10, "M")

    # Titre principal
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 48)
    canvas.drawString(2.5 * cm, height - 9 * cm, "Guide")
    canvas.drawString(2.5 * cm, height - 11.5 * cm, "d'utilisation")

    # Trait accent sous le titre
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(4)
    canvas.line(2.5 * cm, height - 12 * cm, 8 * cm, height - 12 * cm)

    # Sous-titre
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 18)
    canvas.drawString(2.5 * cm, height - 13.5 * cm, "PDF Table Extractor — TFPB")

    # Description
    canvas.setFont("Helvetica", 12)
    canvas.drawString(2.5 * cm, height - 14.5 * cm, "Outil d'extraction de donnees fiscales pour les")
    canvas.drawString(2.5 * cm, height - 15.1 * cm, "dossiers de degrevement de Taxe Fonciere.")

    # Bloc info en bas
    canvas.setFillColor(ACCENT)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(2.5 * cm, 4.5 * cm, "MELKO ENERGIE")

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica", 9)
    canvas.drawString(2.5 * cm, 3.9 * cm, "Document a destination de l'equipe metier")
    canvas.drawString(2.5 * cm, 3.4 * cm, f"Version d'avril {datetime.now().year}")
    canvas.drawString(2.5 * cm, 2.9 * cm, "Branche : fix/339-metadata-corrections")

    # Copyright
    canvas.setFillColor(ACCENT_DARK)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2.5 * cm, 1.6 * cm, f"(c) {datetime.now().year} Melko Energie - Document interne")

    canvas.restoreState()


def content_page(canvas, doc):
    """Header et footer pour les pages de contenu."""
    canvas.saveState()
    width, height = A4

    # Header
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, height - 1.5 * cm, width, 1.5 * cm, stroke=0, fill=1)

    canvas.setFillColor(ACCENT)
    canvas.rect(0, height - 1.6 * cm, width, 0.1 * cm, stroke=0, fill=1)

    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(2 * cm, height - 1 * cm, "MELKO ENERGIE")
    canvas.setFont("Helvetica", 9)
    canvas.drawString(5.5 * cm, height - 1 * cm, "|  Guide d'utilisation - PDF Table Extractor")

    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(width - 2 * cm, height - 1 * cm, "TFPB Degrevement")

    # Footer
    canvas.setFillColor(LIGHT_GRAY)
    canvas.rect(0, 0, width, 1.2 * cm, stroke=0, fill=1)

    canvas.setFillColor(ACCENT)
    canvas.rect(0, 1.2 * cm, width, 0.08 * cm, stroke=0, fill=1)

    canvas.setFillColor(GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 0.45 * cm, f"(c) {datetime.now().year} Melko Energie - Document interne - Confidentiel")
    canvas.drawRightString(width - 2 * cm, 0.45 * cm, f"Page {doc.page - 1}")

    canvas.restoreState()


# ========================================================================
# CONTENU DU GUIDE
# ========================================================================

def build_story():
    story = []

    # ----------------------------------------------------------------
    # COVER PAGE (gere par cover_page())
    # ----------------------------------------------------------------
    story.append(NextPageTemplate("Content"))
    story.append(PageBreak())

    # ----------------------------------------------------------------
    # PAGE 2 : SOMMAIRE
    # ----------------------------------------------------------------
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("Sommaire", style_h1))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceBefore=0, spaceAfter=20))

    toc_items = [
        ("1.", "A propos de cet outil", "3"),
        ("2.", "Lancer un traitement", "4"),
        ("3.", "Preparer les fichiers d'entree", "5"),
        ("4.", "Le contenu des Excel produits", "6"),
        ("5.", "Detail des colonnes de metadonnees", "7"),
        ("    5.1", "Identifiants", "7"),
        ("    5.2", "Classification", "7"),
        ("    5.3", "Montants", "8"),
        ("    5.4", "Entreprise et travaux", "9"),
        ("    5.5", "References et adresses", "9"),
        ("    5.6", "Envoi", "11"),
        ("    5.7", "Interlocuteur et divers", "11"),
        ("6.", "Controles automatiques", "12"),
        ("7.", "Erreurs courantes et solutions", "12"),
        ("8.", "Ou viennent les donnees - schema", "14"),
        ("9.", "Contact et support", "15"),
    ]

    for num, title, page in toc_items:
        line = f'<font color="{PRIMARY.hexval()}"><b>{num}</b></font> &nbsp;&nbsp;{title}' + \
               f' <font color="{GRAY.hexval()}">' + ' .' * 80 + f'</font> <b>{page}</b>'
        story.append(Paragraph(line, style_toc_entry))

    story.append(Spacer(1, 1 * cm))

    story.append(make_callout(
        "Comment lire ce guide",
        "Ce document est destine a l'equipe metier. Chaque section explique comment "
        "utiliser l'outil et comment interpreter les donnees produites. Les sections 4 "
        "et 5 sont les plus importantes pour comprendre le contenu des fichiers Excel "
        "generes apres traitement.",
        kind="info",
    ))

    story.append(PageBreak())

    # ----------------------------------------------------------------
    # SECTION 1 : A propos
    # ----------------------------------------------------------------
    story.append(section_header("1", "A propos de cet outil"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "<b>PDF Table Extractor</b> est un outil interne developpe pour Melko Energie "
        "afin d'automatiser le traitement des dossiers de degrevement fiscal "
        "<b>TFPB</b> (Taxe Fonciere sur les Proprietes Baties).",
        style_body,
    ))

    story.append(Paragraph(
        "L'outil prend en entree un fichier <b>ZIP</b> contenant un ou plusieurs "
        "dossiers de demandes. Chaque dossier regroupe trois PDF : le courrier "
        "principal, l'accuse de reception et la preuve de depot postal. Le programme "
        "lit automatiquement le contenu des PDF, extrait les tableaux et les metadonnees, "
        "puis produit un ZIP de sortie structure contenant pour chaque dossier les fichiers "
        "Excel pretes a l'emploi.",
        style_body,
    ))

    story.append(Paragraph("Ce que fait l'outil", style_h3))
    bullets = [
        "Lit automatiquement les PDF d'un dossier de demande",
        "Detecte et extrait les tableaux de l'annexe (factures detaillees)",
        "Identifie les metadonnees clefs (n&deg; demande, montants, adresses, dates...)",
        "Calcule le Montant TTC sur la base de HT &times; (1 + TVA) ligne par ligne",
        "Applique automatiquement les abreviations de libelles de voie (ex: Avenue &rarr; AV)",
        "Genere des fichiers Excel professionnels formates pour l'equipe metier",
        "Construit un recapitulatif global de toutes les demandes traitees",
    ]
    for b in bullets:
        story.append(Paragraph(f"&bull; &nbsp;{b}", style_bullet))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Ce que l'outil ne fait PAS", style_h3))
    bullets_neg = [
        "L'outil ne lit pas les PDF scannes (images) - seuls les PDF textuels sont supportes",
        "L'outil ne corrige pas les erreurs de saisie dans les PDF source",
        "L'outil ne se substitue pas a une verification humaine des dossiers complexes",
    ]
    for b in bullets_neg:
        story.append(Paragraph(f"&bull; &nbsp;{b}", style_bullet))

    story.append(PageBreak())

    # ----------------------------------------------------------------
    # SECTION 2 : Lancer un traitement
    # ----------------------------------------------------------------
    story.append(section_header("2", "Lancer un traitement"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Methode recommandee : interface web", style_h2))
    story.append(Paragraph(
        "L'interface web Streamlit est la facon la plus simple d'utiliser l'outil. "
        "Elle ne necessite aucune connaissance technique.",
        style_body,
    ))

    story.append(Paragraph("&bull; &nbsp;<b>Etape 1</b> &mdash; Ouvrir un terminal dans le dossier du projet", style_bullet))
    story.append(Paragraph("&bull; &nbsp;<b>Etape 2</b> &mdash; Activer l'environnement virtuel", style_bullet))
    story.append(Paragraph(".\\venv\\Scripts\\Activate.ps1", style_code))

    story.append(Paragraph("&bull; &nbsp;<b>Etape 3</b> &mdash; Lancer l'interface", style_bullet))
    story.append(Paragraph("streamlit run app.py", style_code))

    story.append(Paragraph("&bull; &nbsp;<b>Etape 4</b> &mdash; Le navigateur s'ouvre sur <b>http://localhost:8501</b>", style_bullet))
    story.append(Paragraph("&bull; &nbsp;<b>Etape 5</b> &mdash; Glisser-deposer le ZIP contenant les dossiers de demandes", style_bullet))
    story.append(Paragraph("&bull; &nbsp;<b>Etape 6</b> &mdash; Attendre la fin du traitement (barre de progression)", style_bullet))
    story.append(Paragraph("&bull; &nbsp;<b>Etape 7</b> &mdash; Cliquer sur <b>Telecharger le ZIP de resultats</b>", style_bullet))
    story.append(Paragraph("&bull; &nbsp;<b>Etape 8</b> &mdash; Pour traiter un nouveau dossier, cliquer sur <b>Nouveau courrier</b>", style_bullet))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Methode avancee : ligne de commande", style_h2))
    story.append(Paragraph(
        "Pour les utilisateurs techniques, l'outil dispose aussi d'une interface en "
        "ligne de commande. Trois sous-commandes sont disponibles :",
        style_body,
    ))
    story.append(Paragraph("python extractor.py scan mon_courrier.pdf", style_code))
    story.append(Paragraph("python extractor.py extract mon_courrier.pdf --output sortie.xlsx", style_code))
    story.append(Paragraph("python extractor.py batch ./dossier/ --output-dir ./resultats/", style_code))

    story.append(PageBreak())

    # ----------------------------------------------------------------
    # SECTION 3 : Preparer les fichiers d'entree
    # ----------------------------------------------------------------
    story.append(section_header("3", "Preparer les fichiers d'entree"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Structure d'un dossier de demande", style_h2))
    story.append(Paragraph(
        "Chaque demande doit contenir <b>trois fichiers PDF</b> portant un <b>prefixe "
        "numerique commun</b> en debut de nom. Ce prefixe permet a l'outil de regrouper "
        "automatiquement les fichiers d'une meme demande.",
        style_body,
    ))

    story.append(Spacer(1, 0.2 * cm))
    headers = ["Type", "Convention de nom", "Contenu attendu"]
    rows = [
        ["Courrier principal", "<b>336</b>-Courrier_xxx.pdf", "Lettre, motif, adresses, montants"],
        ["Preuve de depot", "<b>336</b>-Preuve_de_Depot_xxx.pdf", "N&deg; LR de depot postal"],
        ["Accuse de reception", "<b>336</b>-AR_n_xxx.pdf", "N&deg; recommande, dates de presentation/distribution"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[4 * cm, 6 * cm, 6 * cm]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(make_callout(
        "Important : convention de nommage",
        "Le prefixe numerique <b>336</b> (ou tout autre numero) doit etre identique "
        "sur les trois fichiers et place en debut de nom. Sans ce prefixe, l'outil "
        "ne peut pas regrouper les fichiers correctement.",
        kind="warning",
    ))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Mots-cles dans le nom de fichier", style_h2))
    story.append(Paragraph(
        "Pour identifier le type de chaque PDF, l'outil cherche les mots-cles suivants "
        "dans le nom de fichier (sans tenir compte de la casse) :",
        style_body,
    ))
    story.append(Paragraph("&bull; &nbsp;<b>Courrier</b> : le nom contient le mot <i>Courrier</i>", style_bullet))
    story.append(Paragraph("&bull; &nbsp;<b>Preuve de depot</b> : le nom contient <i>Preuve</i> ou <i>depot</i>/<i>depot</i>", style_bullet))
    story.append(Paragraph("&bull; &nbsp;<b>Accuse de reception</b> : le nom contient <i>AR_n</i> ou commence par <i>AR_</i>", style_bullet))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Format du ZIP", style_h2))
    story.append(Paragraph(
        "Le ZIP peut etre <b>plat</b> (tous les PDF a la racine) ou <b>organise</b> en "
        "sous-dossiers <b>mails/</b> (pour les courriers) et <b>proof/</b> (pour les "
        "AR et les preuves de depot). Les deux structures sont supportees.",
        style_body,
    ))

    story.append(PageBreak())

    # ----------------------------------------------------------------
    # SECTION 4 : Contenu des Excel produits
    # ----------------------------------------------------------------
    story.append(section_header("4", "Le contenu des Excel produits"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "A chaque traitement, l'outil genere un ZIP de sortie structure comme suit :",
        style_body,
    ))

    tree = (
        "Resultats.zip<br/>"
        "&nbsp;|<br/>"
        "&nbsp;+-- Demande_336/<br/>"
        "&nbsp;|&nbsp;&nbsp;&nbsp;+-- 336-Courrier_xxx.pdf <font color='#666666'>(PDF original)</font><br/>"
        "&nbsp;|&nbsp;&nbsp;&nbsp;+-- 336-AR_n_xxx.pdf <font color='#666666'>(PDF original)</font><br/>"
        "&nbsp;|&nbsp;&nbsp;&nbsp;+-- 336-Preuve_de_Depot_xxx.pdf <font color='#666666'>(PDF original)</font><br/>"
        "&nbsp;|&nbsp;&nbsp;&nbsp;+-- <b>336_Annexe_Tableaux.xlsx</b> <font color='#666666'>(tableaux extraits)</font><br/>"
        "&nbsp;|&nbsp;&nbsp;&nbsp;+-- <b>336_Metadonnees.xlsx</b> <font color='#666666'>(metadonnees)</font><br/>"
        "&nbsp;+-- Demande_338/<br/>"
        "&nbsp;|&nbsp;&nbsp;&nbsp;+-- ...<br/>"
        "&nbsp;+-- <b>Recapitulatif_Metadonnees.xlsx</b> <font color='#666666'>(vue d'ensemble)</font>"
    )
    story.append(Paragraph(tree, style_code))

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Les trois types de fichiers Excel", style_h2))

    story.append(Paragraph("A. Annexe des tableaux", style_h3))
    story.append(Paragraph(
        "Le fichier <b>XXX_Annexe_Tableaux.xlsx</b> contient une feuille par tableau "
        "extrait du courrier (generalement la liste detaillee des factures par adresse). "
        "Les colonnes sont issues directement du PDF, nettoyees et formatees : montants "
        "en euros, dates en format <i>jj/mm/aaaa</i>, valeurs alignees.",
        style_body,
    ))

    story.append(Paragraph("B. Metadonnees du dossier", style_h3))
    story.append(Paragraph(
        "Le fichier <b>XXX_Metadonnees.xlsx</b> contient une seule feuille en disposition "
        "horizontale : la <b>ligne 1</b> contient les noms de colonnes, la <b>ligne 2</b> "
        "contient les valeurs pour cette demande. C'est ce fichier qui sera detaille "
        "dans la section suivante.",
        style_body,
    ))

    story.append(Paragraph("C. Recapitulatif global", style_h3))
    story.append(Paragraph(
        "Le fichier <b>Recapitulatif_Metadonnees.xlsx</b> est place a la racine du ZIP "
        "de sortie. Il contient une <b>ligne par demande</b> traitee, avec toutes les "
        "colonnes des fichiers de metadonnees. Il permet une vue d'ensemble facile a "
        "filtrer dans Excel.",
        style_body,
    ))

    story.append(PageBreak())

    # ----------------------------------------------------------------
    # SECTION 5 : Detail des colonnes
    # ----------------------------------------------------------------
    story.append(section_header("5", "Detail des colonnes de metadonnees"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "Cette section decrit chaque colonne des fichiers de metadonnees : son origine "
        "(d'ou vient la donnee), comment elle est calculee, et son format. Les colonnes "
        "sont presentees dans l'ordre ou elles apparaissent dans le fichier Excel.",
        style_body,
    ))

    # 5.1 Identifiants
    story.append(Paragraph("5.1 &nbsp; Identifiants", style_h2))
    headers = ["Colonne", "Origine", "Description"]
    rows = [
        ["<b>N&deg; Dossier</b>", "Prefixe numerique du nom de fichier (ex: 336)", "Identifiant unique de la demande"],
        ["<b>Libelle de la Demande</b>", "Calcule a partir de plusieurs champs", "Annee + Categorie + N&deg; Programme + Commune"],
        ["<b>Responsable</b>", "Valeur fixe", "<i>Amaury MONGONGU</i>"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[4 * cm, 6 * cm, 6 * cm]))

    # 5.2 Classification
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("5.2 &nbsp; Classification", style_h2))
    rows = [
        ["<b>Type</b>", "Deduit du contenu du courrier", "Type de demande detecte automatiquement"],
        ["<b>Categorie</b>", "Deduit du contenu du courrier", "Categorie principale (ex: Travaux)"],
        ["<b>Sous-categorie</b>", "Deduit du contenu du courrier", "Sous-categorie - peut etre vide"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[4 * cm, 6 * cm, 6 * cm]))

    story.append(PageBreak())

    # 5.3 Montants
    story.append(Paragraph("5.3 &nbsp; Montants", style_h2))
    headers = ["Colonne", "Origine", "Calcul / Format"]
    rows = [
        ["<b>Montant HT</b>", "Colonne <i>Montant HT facture</i> du tableau de l'annexe", "Somme de toutes les lignes (en euros)"],
        ["<b>Taux de TVA</b>", "Colonne <i>Taux TVA</i> du tableau", "Une seule valeur : <b>20%</b><br/>Plusieurs valeurs : <b>5,5%;10%;20%</b>"],
        ["<b>Montant TTC</b>", "Recalcule depuis les colonnes HT et TVA", "Somme de HT &times; (1 + TVA) ligne par ligne"],
        ["<b>Montant subvention</b>", "Colonne <i>Montant subvention</i>", "Somme en euros"],
        ["<b>Montant de la demande</b>", "Identique au Montant HT", "En euros"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[4 * cm, 6 * cm, 6 * cm]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(make_callout(
        "Changement recent : calcul du Montant TTC",
        "Le Montant TTC n'est plus la somme directe de la colonne TTC du PDF. Il est "
        "desormais <b>recalcule</b> a partir de HT &times; (1 + TVA) ligne par ligne, "
        "ce qui permet de detecter les eventuelles incoherences dans les factures. "
        "Les lignes sans taux TVA renseigne sont ignorees du calcul. La verification "
        "automatique (cellule rouge) a ete desactivee : pour comparer manuellement, "
        "ouvrir l'annexe et faire la somme.",
        kind="warning",
    ))

    story.append(PageBreak())

    # 5.4 Entreprise et travaux
    story.append(Paragraph("5.4 &nbsp; Entreprise et travaux", style_h2))
    rows = [
        ["<b>Nom de l'entreprise</b>", "Colonne <i>Installateur</i>", "Liste des entreprises distinctes, separees par <b>;</b>"],
        ["<b>Nature des travaux</b>", "Colonne <i>Nature travaux</i>", "Liste des natures distinctes, separees par <b>;</b>"],
        ["<b>Nature de depenses</b>", "Valeur fixe", "<i>Degrevement taxe fonciere</i>"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[4 * cm, 6 * cm, 6 * cm]))

    # 5.5 References et adresses
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("5.5 &nbsp; References et adresses", style_h2))
    rows = [
        ["<b>Reference(s) Avis</b>", "Colonne <i>Reference avis</i> (13 chiffres)", "Sans espaces, separees par <b>;</b> si multiples"],
        ["<b>Adresse</b>", "Colonne <i>Adresse des travaux</i> ou texte du courrier", "Voir regle de mise en forme ci-dessous"],
        ["<b>N&deg; Programme</b>", "Colonne <i>Programme</i> ou texte du courrier", "N&deg; de programme immobilier"],
        ["<b>Nombre de logements</b>", "Texte du courrier", "Entier"],
        ["<b>N&deg; d'operation</b>", "Colonne <i>N&deg; operation</i>", "Operation associee"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[4 * cm, 6 * cm, 6 * cm]))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Regle de mise en forme speciale de la colonne Adresse", style_h3))
    story.append(Paragraph(
        "L'adresse est dedoublee par numero et par voie, dedupliquee, puis mise en "
        "forme selon la <b>parite des numeros</b> :",
        style_body,
    ))

    headers = ["Cas", "Format produit", "Exemple"]
    rows = [
        ["<b>Tous pairs</b>", "Une seule ligne, separes par <b>;</b>",
         "2 RUE DU PARC;4 RUE DU PARC;6 RUE DU PARC"],
        ["<b>Tous impairs</b>", "Chaque adresse sur sa propre ligne",
         "1 RUE DU PARC;<br/>3 RUE DU PARC;<br/>5 RUE DU PARC"],
        ["<b>Mixte</b>", "Pairs sur une ligne, puis impairs ligne par ligne",
         "2 RUE X;4 RUE X;<br/>3 RUE X;<br/>5 RUE X"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[3 * cm, 6 * cm, 7 * cm]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(make_callout(
        "Abreviations automatiques de libelles de voie",
        "Les libelles de voie sont automatiquement abreges via le fichier "
        "<b>abbreviations.json</b>. Quelques exemples : <b>Avenue</b> ou <b>Av.</b> "
        "&rarr; <b>AV</b>, <b>Boulevard</b> &rarr; <b>BD</b>, <b>Allee</b> &rarr; "
        "<b>ALL</b>, <b>Rue</b> &rarr; <b>RUE</b>, <b>Place</b> &rarr; <b>PL</b>. "
        "Au total, 62 abreviations sont definies. Pour en ajouter une nouvelle, "
        "modifier <b>abbreviations.json</b> a la racine du projet.",
        kind="info",
    ))

    story.append(PageBreak())

    # 5.6 Envoi
    story.append(Paragraph("5.6 &nbsp; Envoi", style_h2))
    rows = [
        ["<b>Date limite d'envoi</b>", "Extrait de la phrase <i>Fait a Paris, le ...</i>",
         "Format jj/mm/aaaa &mdash; ex: 30/12/2025"],
        ["<b>Type d'envoi</b>", "Valeur fixe", "<i>RecommandeAvecAR</i>"],
        ["<b>Numero de recommande</b>", "Extrait du PDF AR (XXX-AR_n_xxx.pdf)", "N&deg; de la lettre recommandee (15 chiffres)"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[4 * cm, 6 * cm, 6 * cm]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(make_callout(
        "Changement recent : Date limite d'envoi",
        "La date limite d'envoi n'est plus calculee comme <b>31/12/(annee+2)</b>. "
        "Elle est maintenant <b>extraite directement du courrier</b> a partir de la "
        "phrase <i>Fait a Paris, le [jour] [date]</i>. Si cette phrase est introuvable "
        "dans le PDF, la cellule sera vide.",
        kind="warning",
    ))

    # 5.7 Interlocuteur et divers
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("5.7 &nbsp; Interlocuteur et divers", style_h2))
    story.append(Paragraph(
        "Les informations d'interlocuteur sont des <b>valeurs fixes</b> codees dans "
        "l'outil. Si elles changent un jour, il faudra mettre a jour le code.",
        style_body,
    ))

    headers = ["Colonne", "Valeur"]
    rows = [
        ["<b>Nom interlocuteur</b>", "JOUHANNET"],
        ["<b>Prenom interlocuteur</b>", "Alexis"],
        ["<b>Mail interlocuteur</b>", "alexis.jouhannet@dgfip.finances.gouv.fr"],
        ["<b>Tel interlocuteur</b>", "0322468319"],
        ["<b>Commentaire</b>", "Vide par defaut, a completer manuellement"],
        ["<b>Lien escale</b>", "Vide par defaut"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[5 * cm, 11 * cm]))

    story.append(PageBreak())

    # ----------------------------------------------------------------
    # SECTION 6 : Controles automatiques
    # ----------------------------------------------------------------
    story.append(section_header("6", "Controles automatiques"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "Actuellement, <b>aucune cellule n'est coloree en rouge</b> dans les fichiers "
        "de metadonnees. La verification automatique du Montant TTC a ete desactivee a "
        "la demande de l'equipe metier.",
        style_body,
    ))
    story.append(make_callout(
        "Note technique",
        "Le code conserve l'infrastructure pour ajouter de futurs controles. Si un "
        "nouveau controle est demande, il pourra etre ajoute dans la fonction "
        "<i>computed_metadata_red_keys</i> de <b>scripts/metadata_transformer.py</b>.",
        kind="info",
    ))

    # ----------------------------------------------------------------
    # SECTION 7 : Erreurs courantes
    # ----------------------------------------------------------------
    story.append(Spacer(1, 0.5 * cm))
    story.append(section_header("7", "Erreurs courantes et solutions"))
    story.append(Spacer(1, 0.4 * cm))

    errors = [
        ("Aucune demande trouvee dans le ZIP",
         "<b>Cause :</b> les PDF n'ont pas de prefixe numerique en debut de nom, "
         "ou le ZIP est vide.<br/><b>Solution :</b> verifier que chaque fichier commence "
         "par un nombre suivi d'un tiret (ex: <i>336-Courrier_xxx.pdf</i>)."),

        ("Une cellule de metadonnee est vide alors que l'info est dans le PDF",
         "<b>Causes possibles :</b> le pattern regex ne correspond pas exactement a la "
         "formulation du PDF, le PDF est scanne (image) au lieu d'etre textuel, ou la "
         "colonne du tableau a un nom different de ce qui est attendu.<br/>"
         "<b>Solution :</b> signaler le numero du dossier et la colonne concernee a l'equipe technique."),

        ("Le N&deg; de recommande est vide",
         "<b>Causes possibles :</b> le fichier AR n'est pas nomme selon la convention "
         "<i>XXX-AR_n_xxx.pdf</i>, le N&deg; dans le PDF ne fait pas exactement 15 chiffres "
         "consecutifs, ou le PDF AR n'est pas dans le ZIP.<br/>"
         "<b>Solution :</b> verifier le nom du fichier AR et son contenu."),

        ("Adresse mal formee ou abreviation non appliquee",
         "<b>Cause :</b> le libelle de voie n'est pas dans <b>abbreviations.json</b>, "
         "ou il a une variante orthographique non prevue.<br/>"
         "<b>Solution :</b> ajouter la variante dans <b>abbreviations.json</b>."),
    ]
    for title, body in errors:
        story.append(Paragraph(title, style_h3))
        story.append(Paragraph(body, style_body))
        story.append(Spacer(1, 0.15 * cm))

    story.append(PageBreak())

    errors_tech = [
        ("Streamlit ne demarre pas - erreur DLL load failed",
         "<b>Cause :</b> version de pandas incompatible avec Windows Smart App Control.<br/>"
         "<b>Solution :</b>"),
    ]
    for title, body in errors_tech:
        story.append(Paragraph(title, style_h3))
        story.append(Paragraph(body, style_body))
        story.append(Paragraph('pip install "pandas<3.0"', style_code))

    story.append(Paragraph("Le venv ne s'active pas sous PowerShell", style_h3))
    story.append(Paragraph(
        "<b>Cause :</b> la strategie d'execution PowerShell bloque les scripts.<br/>"
        "<b>Solution</b> (une seule fois) :",
        style_body,
    ))
    story.append(Paragraph("Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned", style_code))

    # ----------------------------------------------------------------
    # SECTION 8 : Schema d'origine des donnees
    # ----------------------------------------------------------------
    story.append(Spacer(1, 0.3 * cm))
    story.append(section_header("8", "D'ou viennent les donnees - schema"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "Le schema ci-dessous resume l'origine de chaque donnee dans les fichiers de "
        "metadonnees :",
        style_body,
    ))

    # Tableau d'origine des donnees - look "fiche technique"
    headers = ["Source", "Donnees extraites"]
    rows = [
        ["<b>Courrier PDF<br/>(texte)</b>",
         "&bull; N&deg; demande, date, motif<br/>"
         "&bull; Montants globaux, nombre de logements<br/>"
         "&bull; Phrase <i>Fait a Paris, le ...</i> &rarr; Date limite d'envoi"],
        ["<b>Courrier PDF<br/>(tableau annexe)</b>",
         "&bull; Colonne HT &rarr; Montant HT (somme)<br/>"
         "&bull; Colonne TVA &rarr; Taux de TVA (uniques)<br/>"
         "&bull; Colonnes HT et TVA &rarr; Montant TTC (recalcule)<br/>"
         "&bull; Colonne adresse &rarr; Adresse (formatee selon parite)<br/>"
         "&bull; Colonne installateur &rarr; Nom de l'entreprise<br/>"
         "&bull; Colonne nature &rarr; Nature des travaux"],
        ["<b>AR PDF</b><br/>(XXX-AR_n_xxx.pdf)",
         "&bull; 15 chiffres consecutifs &rarr; Numero de recommande<br/>"
         "&bull; <i>Presentee le ...</i> &rarr; Date de presentation<br/>"
         "&bull; <i>Distribuee le ...</i> &rarr; Date de distribution"],
        ["<b>Preuve de depot</b>",
         "&bull; 15 chiffres consecutifs &rarr; N&deg; LR Depot"],
        ["<b>Valeurs fixes<br/>(codees en dur)</b>",
         "&bull; Responsable &rarr; Amaury MONGONGU<br/>"
         "&bull; Type d'envoi &rarr; RecommandeAvecAR<br/>"
         "&bull; Nature de depenses &rarr; Degrevement taxe fonciere<br/>"
         "&bull; Interlocuteur &rarr; JOUHANNET Alexis (DGFiP)"],
    ]
    story.append(make_data_table(headers, rows, col_widths=[4 * cm, 12 * cm]))

    story.append(PageBreak())

    # ----------------------------------------------------------------
    # SECTION 9 : Contact
    # ----------------------------------------------------------------
    story.append(section_header("9", "Contact et support"))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(
        "Pour toute question, bug, ou demande d'evolution, contacter l'equipe technique :",
        style_body,
    ))

    story.append(Paragraph("Bug ou valeur incorrecte", style_h3))
    story.append(Paragraph(
        "Ouvrir une issue GitHub ou contacter l'equipe technique en precisant le "
        "<b>numero de dossier concerne</b> et la <b>colonne</b> qui pose probleme. "
        "Joindre si possible le ZIP source pour reproduire le probleme.",
        style_body,
    ))

    story.append(Paragraph("Nouvelle abreviation", style_h3))
    story.append(Paragraph(
        "Modifier directement le fichier <b>abbreviations.json</b> a la racine du projet, "
        "puis pousser le changement sur la branche en cours. La cle doit etre en "
        "MAJUSCULES (ex: <i>NOUVEAU TYPE</i>) et la valeur est l'abreviation desiree "
        "(ex: <i>NTYP</i>).",
        style_body,
    ))

    story.append(Paragraph("Evolution fonctionnelle", style_h3))
    story.append(Paragraph(
        "Decrire le besoin metier en precisant : (1) la colonne concernee, (2) la "
        "regle attendue, (3) un ou plusieurs exemples concrets d'entree/sortie. "
        "Plus la description est precise, plus l'evolution sera rapide a implementer.",
        style_body,
    ))

    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceBefore=0, spaceAfter=20))

    story.append(Paragraph(
        f"<font color='{GRAY.hexval()}'><i>Document genere automatiquement le "
        f"{datetime.now().strftime('%d/%m/%Y')} pour Melko Energie. "
        f"Version basee sur la branche fix/339-metadata-corrections.</i></font>",
        ParagraphStyle("center", parent=style_body, alignment=TA_CENTER, fontSize=9),
    ))

    return story


# ========================================================================
# GENERATION DU PDF
# ========================================================================

def generate_pdf(output_path: Path) -> Path:
    doc = BaseDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.2 * cm,
        bottomMargin=1.8 * cm,
        title="Guide d'utilisation - PDF Table Extractor",
        author="Melko Energie",
        subject="Guide metier pour l'extraction de donnees TFPB",
        creator="PDF Table Extractor",
    )

    cover_frame = Frame(0, 0, A4[0], A4[1], id="cover", showBoundary=0,
                        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    content_frame = Frame(2 * cm, 1.6 * cm, A4[0] - 4 * cm, A4[1] - 3.5 * cm,
                          id="content", showBoundary=0,
                          leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)

    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame], onPage=cover_page),
        PageTemplate(id="Content", frames=[content_frame], onPage=content_page),
    ])

    story = build_story()
    doc.build(story)
    return output_path


if __name__ == "__main__":
    output = Path(__file__).resolve().parent.parent / "Guide_Utilisation_Melko.pdf"
    result = generate_pdf(output)
    print(f"PDF genere : {result}")
    print(f"Taille : {result.stat().st_size / 1024:.1f} KB")
