"""Create study-only PDF copies. Original PDFs and all quiz JSON remain intact."""
from pathlib import Path
import re
import fitz

UNITS = {
    'anatomi': ([1,13,40,64,86,110,134,161], [9,28,52,74,96,119,146,169]),
    'bilimsel': ([3,8,13,18,24,30,36,42], [5,10,15,21,27,33,39,45]),
    'ingilizce': ([3+6*i for i in range(14)], [5+6*i for i in range(14)]),
    'psikoloji': ([3,9,19,28,38,47,55,65,73,82,91,98], [5,14,23,33,42,50,61,68,77,86,93,103]),
    'sosyoloji': ([3,11,19,29,41,49,59,67,75,83,91,99,107,115], [6,14,23,34,44,53,62,70,78,86,94,102,110,118]),
    'turk_dili': ([3,10,16,22,28,35,40,46,53,60,68,76,86,92], [5,12,17,24,30,36,41,48,55,62,70,80,87,94]),
    'ataturk': ([3,10,16,23,29,35,42,49,55,63,71,79,87,94], [6,12,19,25,31,38,45,52,59,67,74,82,90,98])
}
RECAPS = {
 'anatomi':{1:[39],2:[63],3:[85],4:[109],6:[160]},
 'psikoloji':{j:[pg] for j,pg in enumerate([8,18,27,37,46,54,64,72,81,90,97,107])},
 'bilimsel':{7:[48,49]},
 'sosyoloji':{13:[123]}
}
HEADINGS = {
 'anatomi': re.compile(r'(?:\bÖZGÜN\b.{0,80}(?:SORU|TEST)|DENEME SINAVI|SINAV TARZI|SINAV SORUSU|DENEME TESTİ)',re.I),
 'bilimsel': re.compile(r'^\s*\d{2}\s*\|\s*TEST SORULARI',re.I),
 'ingilizce': re.compile(r'\b15 SORULUK ALIŞTIRMA TESTİ',re.I),
 'psikoloji': re.compile(r'^\s*ÜNİTE SONU\s*-\s*10 KAYNAK TEST SORUSU',re.I),
 'sosyoloji': re.compile(r'^\s*\d{2}\. ÜNİTE\s*\|\s*ÖZGÜN TEST SORULARI',re.I),
 'turk_dili': re.compile(r'^\s*\d+\s+ÖZGÜN ÇOKTAN SEÇMELİ SORU',re.I),
 'ataturk': re.compile(r'^\s*4\s*\|\s*ÇOKTAN SEÇMELİ ÜNİTE TESTİ',re.I)
}

def _test_y(page, slug):
    hits=[]
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            text=''.join(span['text'] for span in line['spans']).strip()
            if HEADINGS[slug].search(text):
                hits.append(line['bbox'][1])
    if not hits:
        raise RuntimeError(f'{slug}: test başlığı bulunamadı; kaynak değişmiş olabilir')
    return min(hits)

def build_note_pdf(source: Path, slug: str, unit: int | None = None) -> bytes:
    if slug not in UNITS:
        raise ValueError('Bilinmeyen ders')
    starts, tests = UNITS[slug]
    with fitz.open(source) as original:
        if len(starts)!=len(tests) or len(original)<max(tests):
            raise ValueError(f'{slug}: kaynak sayfaları uyuşmuyor')
        if unit is not None and not 1<=unit<=len(starts):
            raise ValueError(f'{slug}: geçersiz ünite')
        with fitz.open() as clean:
            if unit is None:
                for pg in range(1,starts[0]):
                    clean.insert_pdf(original,from_page=pg-1,to_page=pg-1)
            indices=range(len(starts)) if unit is None else [unit-1]
            for j in indices:
                first,test=starts[j],tests[j]
                if not first<test:
                    raise ValueError(f'{slug}: sayfa sırası tutarsız')
                for pg in range(first,test):
                    clean.insert_pdf(original,from_page=pg-1,to_page=pg-1)
                # A quiz can start at the bottom of the final study page.
                # Redact the quiz area permanently before cropping the page.
                y=_test_y(original[test-1],slug)
                if y>=150:
                    clean.insert_pdf(original,from_page=test-1,to_page=test-1)
                    page=clean[-1]
                    boundary=max(0,y-12)
                    page.add_redact_annot(fitz.Rect(0,boundary,page.rect.width,page.rect.height),fill=(1,1,1))
                    page.apply_redactions(images=2,graphics=1,text=0)
                    page.set_cropbox(fitz.Rect(0,0,page.rect.width,boundary))
                for pg in RECAPS.get(slug,{}).get(j,[]):
                    if not 1<=pg<=len(original):
                        raise ValueError(f'{slug}: tekrar sayfası yok')
                    clean.insert_pdf(original,from_page=pg-1,to_page=pg-1)
            clean.set_metadata({'title':f'{slug} - Konu Anlatımı','subject':'Seher AUZEF - testlerden arındırılmış notlar'})
            return clean.tobytes(garbage=4,deflate=True)
