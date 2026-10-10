from pathlib import Path
from html import escape
import json

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'mobile-guide-data.json').read_text())
OUT = ROOT / 'output' / 'pdf' / 'bbq-mobile-checklist.pdf'
OUT.parent.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(TTFont('Korean', '/System/Library/Fonts/Supplemental/AppleGothic.ttf'))
pdfmetrics.registerFontFamily('Korean', normal='Korean', bold='Korean')
W, H, M = 390, 844, 25
BG, INK, MUTED = HexColor('#FCFAF5'), HexColor('#222D28'), HexColor('#56635B')
ACCENT, SOFT = HexColor('#306451'), HexColor('#E7EDE4')
styles = {
    'title': ParagraphStyle('title', fontName='Korean', fontSize=25, leading=33, textColor=INK, wordWrap='CJK'),
    'subtitle': ParagraphStyle('subtitle', fontName='Korean', fontSize=11.5, leading=18, textColor=MUTED, wordWrap='CJK'),
    'label': ParagraphStyle('label', fontName='Korean', fontSize=16, leading=23, textColor=INK, wordWrap='CJK'),
    'body': ParagraphStyle('body', fontName='Korean', fontSize=14.2, leading=22, textColor=MUTED, wordWrap='CJK'),
    'note': ParagraphStyle('note', fontName='Korean', fontSize=12.8, leading=19.5, textColor=INK, wordWrap='CJK'),
}
URLS = {
    'cadac': ('CADAC 공식 설명서', 'https://www.cadacinternational.com/amfile/file/download/file/52/'),
    'thaw': ('USDA 해동 안내', 'https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/meat-catfish/lamb-farm-table'),
    'grill-safety': ('USDA 야외 조리 안내', 'https://www.fsis.usda.gov/food-safety/safe-food-handling-and-preparation/food-safety-basics/grilling-and-food-safety'),
    'corn': ('Weber 옥수수 조리법', 'https://www.weber.com/US/en/blog/tips-techniques/top-tips-for-grilling-vegetables/weber-48939.html'),
    'temp': ('USDA 익힘 기준', 'https://www.fsis.usda.gov/food-safety/food-safety-basics/steps-keep-food-safe'),
}


def paragraph(c, text, style, x, y, width):
    p = Paragraph(escape(text), styles[style])
    _, height = p.wrap(width, H)
    p.drawOn(c, x, y - height)
    return y - height


c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle('세준의 10월 11일 루프탑 바베큐 체크리스트')
c.setAuthor('세준의 루프탑 바베큐 준비')
for i, page in enumerate(DATA['pages'], 1):
    c.setFillColor(BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.bookmarkPage(f'page-{i}')
    c.addOutlineEntry(page['title'], f'page-{i}', level=0)
    c.setFillColor(ACCENT)
    c.setFont('Korean', 10)
    c.drawString(M, H - 31, DATA['date'])
    c.setFont('Helvetica-Bold', 10)
    c.drawRightString(W - M, H - 31, f'{i:02d} / 07')
    y = paragraph(c, page['title'], 'title', M, H - 52, W - M * 2)
    y = paragraph(c, page['subtitle'], 'subtitle', M, y - 7, W - M * 2) - 23
    for label, detail in page['items']:
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1)
        c.roundRect(M, y - 17, 12, 12, 2, stroke=1, fill=0)
        y = paragraph(c, label, 'label', M + 23, y, W - 2 * M - 23)
        y = paragraph(c, detail, 'body', M + 23, y - 3, W - 2 * M - 23) - 16
    p = Paragraph(escape(page['note']), styles['note'])
    _, note_height = p.wrap(W - 2 * M - 24, H)
    note_bottom = y - note_height - 24
    assert note_bottom > 55, (i, page['title'], note_bottom)
    c.setFillColor(SOFT)
    c.roundRect(M, note_bottom, W - 2 * M, note_height + 24, 8, stroke=0, fill=1)
    p.drawOn(c, M + 12, note_bottom + 12)
    c.setFillColor(MUTED)
    c.setFont('Korean', 9)
    source = page['source']
    if source == 'all':
        source_keys = ['temp', 'grill-safety', 'cadac']
        x = M
        for key in source_keys:
            label, url = URLS[key]
            c.drawString(x, 30, label)
            sw = pdfmetrics.stringWidth(label, 'Korean', 9)
            c.linkURL(url, (x, 27, x + sw, 40), relative=0)
            x += sw + 14
    elif source:
        label, url = URLS[source]
        c.drawString(M, 30, label)
        c.linkURL(url, (M, 27, W - M, 40), relative=0)
    else:
        c.drawString(M, 30, '현재 준비 목록 기준 · 2026.10.10 정리')
    c.showPage()
c.save()

reader = PdfReader(OUT)
assert len(reader.pages) == 7
for i, page in enumerate(reader.pages):
    t = page.extract_text()
    assert DATA['pages'][i]['title'] in t
    assert float(page.mediabox.width) == W
assert '맥주 8캔' in '\n'.join(p.extract_text() for p in reader.pages)

lines = ['# 10월 11일 바베큐 휴대폰 체크리스트', '', DATA['date'], '',
         '음식 순서: 양·소고기 + 가니시 → 마약 옥수수 → 남은 양·소고기 → 목살.', '',
         'PDF는 보기용이며 아래 체크리스트는 메모앱에 복사해 사용할 수 있다.', '']
for i, page in enumerate(DATA['pages'], 1):
    lines.extend([f'## {i}. {page["title"]}', '', page['subtitle'], ''])
    for label, detail in page['items']:
        lines.extend([f'- [ ] **{label}**', f'  {detail}', ''])
    lines.extend([page['note'], ''])
    source = page['source']
    keys = ['temp', 'grill-safety', 'cadac'] if source == 'all' else ([source] if source else [])
    if keys:
        lines.extend(['참고: ' + ' · '.join(f'[{URLS[k][0]}]({URLS[k][1]})' for k in keys), ''])
(ROOT / 'BBQ_MOBILE_CHECKLIST.md').write_text('\n'.join(lines), encoding='utf-8')
print('PDF:', OUT)
print('Pages:', len(reader.pages))
print('Markdown: BBQ_MOBILE_CHECKLIST.md')
