"""Modern Emisyon Pro-inspired sidebar for Seher AUZEF.
All quizzes, question data, passwords and exam history use the original app.
"""
import base64
import hmac
import secrets
from pathlib import Path

import fitz
import streamlit as st
import streamlit.components.v1 as components
from pdf_notes import build_note_pdf
from remembered_login import issue_token, valid_token, password_tag

_device_store = components.declare_component(
    'seher_remembered_device', path=str(Path(__file__).resolve().parent / 'device_login')
)


def device_command(action, token=''):
    st.session_state['_device_command'] = {
        'action': action, 'token': token, 'revision': secrets.token_hex(16),
    }


def sync_device():
    if '_device_command' not in st.session_state:
        device_command('read')
    command = st.session_state['_device_command']
    result = _device_store(command=command, key='remembered_device', default=None)
    # Wait for the browser to acknowledge this specific read/write. An old
    # component value must never restore a login during logout or token changes.
    if not isinstance(result, dict) or result.get('revision') != command['revision']:
        st.caption('Cihaz giriş kaydı kontrol ediliyor…')
        st.stop()
    return result


def logout():
    st.session_state.clear()
    device_command('clear')
    st.rerun()

NAV = ['🏠 Ana Sayfa','📖 Notlar','✍️ Test','📊 Başarı Analizi','🕘 Sınav Geçmişi','⚙️ Ayarlar','ℹ️ Hakkında']
LABEL = {
    '🏠 Ana Sayfa':'🏠 Ana Sayfa',
    '📖 Notlar':'📖 Dersler ve Konu Anlatımları',
    '✍️ Test':'✍️ Test Çöz',
    '📊 Başarı Analizi':'📊 Başarı Analizi',
    '🕘 Sınav Geçmişi':'🕘 Sınav Geçmişi',
    '⚙️ Ayarlar':'⚙️ Ayarlar',
    'ℹ️ Hakkında':'ℹ️ Hakkında',
}
CSS = """<style>
.stApp {background:linear-gradient(155deg,#ecf2fa,#f6f8fb 45%,#edf3f9);}
header[data-testid="stHeader"] {background:transparent;}
.block-container {max-width:1280px !important;padding-top:1rem;padding-bottom:3rem;}
section[data-testid="stSidebar"] {background:#13243b!important;border-right:1px solid #365170!important;}
section[data-testid="stSidebar"] * {color:#eef5ff!important;}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  border-radius:10px;padding:.34rem .5rem;transition:background .15s;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {background:#245b92!important;}
section[data-testid="stSidebar"] button {background:#344765!important;border-color:#597696!important;}
.pro-hero {border:1px solid #37678e;border-radius:17px;
  background:linear-gradient(115deg,#13243b,#1e4c77 65%,#316c93);
  color:white!important;padding:1.1rem 1.35rem;margin-bottom:1.1rem;
  box-shadow:0 8px 23px #13264123;}
.pro-hero h1 {font-size:1.8rem;line-height:1.2;margin:.2rem 0 .45rem;color:white!important;}
.pro-hero p {margin:0;color:#dceafa!important;font-size:.91rem;}
.pro-kicker {font-size:.72rem;letter-spacing:.11em;color:#a1e0fd;font-weight:800;}
.pro-tag {margin-top:.75rem;border:1px solid #4c85a9;background:#153951;
  border-radius:999px;display:inline-block;color:#ddf7fe;font-size:.75rem;padding:.3rem .65rem;}
div[data-testid="stMetric"] {background:white;border:1px solid #dce4f0;border-radius:13px;
 padding:.65rem .8rem;box-shadow:0 2px 7px #1d304012;}
.stButton button,.stDownloadButton button {min-height:2.6rem;border-radius:10px;font-weight:650;}
@media(max-width:650px){.block-container{padding:1rem .65rem 3rem;}
 .pro-hero {padding:.9rem;} .pro-hero h1{font-size:1.35rem;}}
</style>"""

def hero():
    st.markdown(
        '<div class="pro-hero"><div class="pro-kicker">AUZEF · ÇOCUK GELİŞİMİ</div>'
        '<h1>🎓 Seher’in AUZEF Çalışma Asistanı Pro</h1>'
        '<p>Ders notları · Ünite testleri · Başarı takibi</p>'
        '<span class="pro-tag">● Çalışma alanı aktif</span></div>',
        unsafe_allow_html=True,
    )

def login(app):
    pwd = app['get_secret']()
    if not pwd:
        st.error('APP_PASSWORD şifresi tanımlı değil. Streamlit Cloud → Settings → Secrets alanından eklenmelidir.')
        st.stop()
    device = sync_device()
    tag = password_tag(pwd)
    if valid_token(device.get('token'), pwd):
        st.session_state['authenticated'] = True
        st.session_state['_auth_password_tag'] = tag
        return
    if (st.session_state.get('authenticated') and
            st.session_state.get('_auth_password_tag', tag) == tag):
        # Also remember already-open sessions after this update.
        st.session_state['_auth_password_tag'] = tag
        if not device.get('error'):
            device_command('save', issue_token(pwd))
            st.rerun()
        st.caption('Tarayıcı cihaz kaydına izin vermiyor; bu oturum açık kalacak.')
        return
    st.session_state.pop('authenticated', None)
    hero()
    st.markdown('### 🔐 Giriş Yap')
    st.caption('Şifreyi bir kez girmen yeterli. Bu tarayıcıdaki sonraki girişlerin otomatik açılır.')
    with st.form('seher_pro_login'):
        entered = st.text_input('Çalışma alanı şifresi',type='password')
        go = st.form_submit_button('Giriş Yap',type='primary',use_container_width=True)
    if go:
        if hmac.compare_digest(entered.encode('utf-8'),str(pwd).encode('utf-8')):
            st.session_state['authenticated']=True
            st.session_state['_auth_password_tag'] = tag
            device_command('save', issue_token(pwd))
            st.rerun()
        else:
            st.error('Şifre eşleşmedi.')
    st.stop()

def dashboard(app):
    courses=app['COURSES']
    banks=app['all_banks']()
    attempts=app['list_attempts']()
    top=st.columns(2)
    top[0].metric('Ders sayısı',len(courses))
    top[1].metric('Ünite sayısı',sum(c['units'] for c in courses))
    bottom=st.columns(2)
    bottom[0].metric('Test sorusu',f"{sum(map(len,banks.values())):,}".replace(',','.'))
    bottom[1].metric('Çözülen test',len(attempts))
    st.markdown('### 📚 Derslerim')
    columns=st.columns(2)
    for i,c in enumerate(courses):
        with columns[i%2]:
            with st.container(border=True):
                st.markdown(f"#### {c['icon']} {c['name']}")
                st.caption(c['description'])
                st.caption(f"{c['units']} ünite · {len(banks[c['id']])} açıklamalı soru")
                l,r=st.columns(2)
                l.button('📖 Notları Aç',key=f"dash_pdf_{c['id']}",use_container_width=True,
                         on_click=app['goto'],args=('📖 Notlar',c['id']))
                r.button('✍️ Test Çöz',key=f"dash_test_{c['id']}",use_container_width=True,
                         on_click=app['goto'],args=('✍️ Test',c['id']))
    st.info('Not PDF’lerinde yalnızca konu anlatımları bulunur. Testler ayrı Test Çöz alanındadır.')

@st.cache_data(show_spinner=False)
def _make_notes(path,slug,unit,version):
    return build_note_pdf(Path(path),slug,unit)

def notes(app,reader_template):
    slug=st.session_state['course']
    course=app['COURSE_BY_ID'][slug]
    st.subheader(f"{course['icon']} {course['name']} — Konu Anlatımı")
    st.caption('Test soruları ve cevap anahtarları PDF’den çıkarılmıştır. Ünite testleri Test Çöz bölümünde kalır.')
    note_navigation('top')
    titles=app['unit_titles']()[slug]
    unit=st.selectbox(
        'Okuyacağın ünite',
        options=[None]+list(range(1,course['units']+1)),
        format_func=lambda n:'📚 Tüm üniteler' if n is None else f'{n}. Ünite — {titles[str(n)]}',
        key=f'notes_unit_{slug}',
    )
    path=app['get_pdf_path'](slug)
    try:
        data=_make_notes(str(path),slug,unit,f'{path.stat().st_size}:{path.stat().st_mtime_ns}')
        with fitz.open(stream=data,filetype='pdf') as doc:
            pages=len(doc)
    except Exception as exc:
        st.error(f'Not PDF’si hazırlanamadı. Orijinal dosyalar korunuyor. Ayrıntı: {exc}')
        return
    st.caption(f'📄 {pages} sayfa · ⛶ Tam ekran · + / − yakınlaştırma · İki parmakla büyütme')
    html=reader_template.replace('__PDF_BASE64__',base64.b64encode(data).decode('ascii'))
    height=st.session_state.get('pdf_height',700)
    components.html(html,height=height,scrolling=False)
    st.download_button('📥 Konu anlatımı PDF’sini telefona indir',data,
        file_name=f"Seher_{slug}_{'tum_notlar' if unit is None else 'unite_'+str(unit)}.pdf",
        mime='application/pdf',use_container_width=True)
    note_navigation('bottom')


def navigate(destination):
    # Callback runs before the sidebar radio is created on the next rerun.
    st.session_state['nav'] = destination


def note_navigation(position):
    home, test = st.columns(2)
    home.button('← Ana Sayfa', key=f'notes_home_{position}',
                use_container_width=True, on_click=navigate, args=(NAV[0],))
    test.button('✍️ Bu Dersten Test Çöz', key=f'notes_test_{position}',
                type='primary', use_container_width=True,
                on_click=navigate, args=(NAV[2],))


_DRAWER_HTML = r'''<script>
(() => {
  const host = window.parent, doc = host.document;
  if (host.__seherDrawer) host.__seherDrawer.abort();
  const control = new host.AbortController();
  host.__seherDrawer = control;
  const options = {passive:true, signal:control.signal};
  let start = null;
  const sidebar = () => doc.querySelector('[data-testid="stSidebar"]');
  function expanded() {
    const side = sidebar();
    if (!side) return false;
    if (side.hasAttribute('aria-expanded')) return side.getAttribute('aria-expanded') === 'true';
    const rect = side.getBoundingClientRect();
    return rect.width > 0 && rect.left >= -1 && rect.right > 0;
  }
  doc.addEventListener('touchstart', e => {
    start = null;
    if (e.touches.length !== 1) return;
    const t = e.touches[0], side = sidebar();
    if ((!expanded() && t.clientX <= 40) ||
        (expanded() && side && side.contains(e.target)))
      start = {x:t.clientX, y:t.clientY, open:expanded()};
  }, options);
  doc.addEventListener('touchend', e => {
    const first = start; start = null;
    if (!first || !e.changedTouches.length || e.touches.length) return;
    const t = e.changedTouches[0], dx = t.clientX-first.x, dy = t.clientY-first.y;
    if (Math.abs(dx) < 65 || Math.abs(dx) < Math.abs(dy)*1.6) return;
    if (first.open && dx < 0 && expanded()) {
      const side = sidebar();
      side?.querySelector('[data-testid="stSidebarCollapseButton"] button, button[data-testid="stSidebarCollapseButton"]')?.click();
    } else if (!first.open && dx > 0 && !expanded()) {
      doc.querySelector('[data-testid="stSidebarCollapsedControl"] button, button[data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"] button')?.click();
    }
  }, options);
  doc.addEventListener('touchcancel', () => {start = null;}, options);
})();
</script>'''


def quick_navigation():
    st.radio('Hızlı geçiş', NAV[:3], format_func=lambda name: LABEL[name],
             index=NAV[:3].index(st.session_state['nav']) if st.session_state['nav'] in NAV[:3] else None,
             horizontal=True, key='quick_nav', on_change=_quick_changed)


def _quick_changed():
    navigate(st.session_state['quick_nav'])

def success(app):
    st.subheader('📊 Başarı Analizi')
    rows=app['list_attempts']()
    if not rows:
        st.info('Henüz tamamlanmış test bulunmuyor. İlk testi bitirince başarı yüzdeleri burada görünecek.')
        return
    cols=st.columns(2)
    cols[0].metric('Tamamlanan test',len(rows))
    cols[1].metric('Ortalama başarı',f"%{sum(r['percent'] for r in rows)/len(rows):.1f}")
    st.metric('Cevaplanan soru',sum(r['correct']+r['wrong'] for r in rows))
    st.markdown('#### Derslere göre ilerleme')
    for c in app['COURSES']:
        items=[r for r in rows if r['course']==c['id']]
        if not items:
            continue
        pct=sum(r['percent'] for r in items)/len(items)
        st.markdown(f"**{c['icon']} {c['name']}** — %{pct:.1f} · {len(items)} test")
        st.progress(min(1,max(0,pct/100)))
    st.caption('Bu oranlar çalışma testlerinden hesaplanır; resmî AUZEF notu değildir.')

def settings():
    st.subheader('⚙️ Okuma Ayarları')
    current=st.session_state.get('pdf_height',700)
    st.slider('PDF okuyucu yüksekliği',min_value=500,max_value=900,value=current,step=50,key='pdf_height')
    st.info('⛶ Tam ekran düğmesine basabilir, sayfayı iki parmakla yakınlaştırabilirsin.')
    st.caption('PDF’nin test bölümleri görüntüleme sürümünden ayıklanır; orijinal kaynaklar yedek pakette kalır.')

def about(app):
    st.subheader('ℹ️ Hakkında')
    total=sum(len(bank) for bank in app['all_banks']().values())
    st.markdown(f"**Seher’in AUZEF Çalışma Asistanı Pro** — 7 ders, {total:,} soru".replace(',','.'))
    st.write('Emisyon Saha Asistanı Pro düzeninden esinlenen mobil uyumlu çalışma ortamı.')
    st.write('Şifreyle giriş, ayrı konu notları ve ünite testleri, açıklamalı cevaplar, başarı analizi ve sınav geçmişi içerir.')
    st.warning('Streamlit Community Cloud yeniden başlarsa yerel test geçmişi silinebilir. Sonuçlarını CSV olarak indirip sakla.')

def render(app,reader_template):
    st.markdown(CSS,unsafe_allow_html=True)
    login(app)
    if st.session_state.get('nav') not in NAV:
        st.session_state['nav']=NAV[0]
    if st.session_state.get('course') not in app['COURSE_BY_ID']:
        st.session_state['course']='anatomi'
    with st.sidebar:
        st.markdown(
            '<div style="font-weight:800;font-size:1.26rem;padding:.25rem 0">🎓 Seher AUZEF Pro</div>'
            '<div style="font-size:.85rem;margin-bottom:1rem">📚 Çalışma ve Sınav Merkezi</div>',
            unsafe_allow_html=True,
        )
        st.radio('Menü',NAV,format_func=lambda name:LABEL[name],key='nav',label_visibility='collapsed')
        if st.session_state['nav'] in ('📖 Notlar','✍️ Test'):
            st.selectbox('Ders Seç',options=[c['id'] for c in app['COURSES']],
                format_func=lambda slug:f"{app['COURSE_BY_ID'][slug]['icon']} {app['COURSE_BY_ID'][slug]['name']}",
                key='course')
        st.divider()
        st.caption('🔒 Oturum açık')
        if st.button('🚪 Çıkış Yap',use_container_width=True,key='seher_pro_logout'):
            logout()
    hero()
    current=st.session_state['nav']
    # Recreate the quick selector from authoritative navigation each rerun.
    st.session_state['quick_nav'] = current if current in NAV[:3] else None
    quick_navigation()
    components.html(_DRAWER_HTML, height=0, scrolling=False)
    if current==NAV[0]:dashboard(app)
    elif current==NAV[1]:notes(app,reader_template)
    elif current==NAV[2]:app['show_quiz']()
    elif current==NAV[3]:success(app)
    elif current==NAV[4]:app['show_history']()
    elif current==NAV[5]:settings()
    elif current==NAV[6]:about(app)
    st.divider()
    st.caption('Seher AUZEF Pro · Özel çalışma materyali · Resmî sınav uygulaması değildir.')

