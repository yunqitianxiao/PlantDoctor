# -*- coding: utf-8 -*-
"""
无权重验证脚本：用 stub 顶掉 torch/transformers/cv2 等重库，
在系统 python(flask) 下跑通 登录/注册/全部页面/API 兜底。
用法：cd 项目根 && python verify_stub.py
"""
import sys, types, os, io, base64

def _m(name):
    m = types.ModuleType(name)
    sys.modules[name] = m
    return m

# ---- torch ----
torch = _m('torch')
torch.device = lambda *a, **k: 'cpu'
torch.cuda = types.SimpleNamespace(is_available=lambda: False)
torch.load = lambda *a, **k: None
torch.no_grad = lambda *a, **k: (lambda f: f)
torch.Tensor = type('Tensor', (), {})
torch.from_numpy = lambda x: x
torch.argmax = lambda *a, **k: 0
torch.softmax = lambda *a, **k: None
torch.einsum = lambda *a, **k: None
torch.nn = _m('torch.nn')
torch.nn.Linear = lambda *a, **k: None
torch.nn.functional = _m('torch.nn.functional')
# ---- torchvision ----
tv = _m('torchvision'); tvm = _m('torchvision.models')
tvm.efficientnet_v2_s = lambda *a, **k: None
# ---- transformers ----
tr = _m('transformers')
tr.AutoImageProcessor = type('AutoImageProcessor', (), {'from_pretrained': lambda *a, **k: None})
tr.Mask2FormerForUniversalSegmentation = type('M', (), {'from_pretrained': lambda *a, **k: None})
# ---- langchain_openai ----
lc = _m('langchain_openai'); lc.ChatOpenAI = lambda *a, **k: None
# ---- cv2 ----
cv2 = _m('cv2')
cv2.IMREAD_COLOR = 1
cv2.COLOR_BGR2RGB = 4
cv2.imdecode = lambda *a, **k: None
cv2.resize = lambda *a, **k: None
cv2.cvtColor = lambda *a, **k: None
cv2.imencode = lambda *a, **k: (True, None)
cv2.addWeighted = lambda *a, **k: None
# ---- PIL ----
PIL = _m('PIL'); PIL.Image = _m('PIL.Image'); PIL.Image.open = lambda *a, **k: None
# ---- numpy ----
np_ = _m('numpy'); np_.uint8 = int; np_.frombuffer = lambda *a, **k: object()
# ---- sklearn / matplotlib（训练脚本才用，无需真实功能）----
_m('sklearn'); _m('matplotlib')

# ---- 导入应用 ----
from app import app

def _tiny_png():
    # 1x1 PNG（base64）
    b64 = ('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC')
    return base64.b64decode(b64)

passed, failed = 0, 0
def check(label, cond):
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        print(f"  FAIL  {label}")

with app.test_client() as c:
    # 注册
    r = c.post('/register', data={'username': 'tester', 'password': '123456'})
    check('POST /register (200/302)', r.status_code in (200, 302))
    # 登录
    r = c.post('/login', data={'username': 'tester', 'password': '123456'})
    check('POST /login 后跳转', r.status_code in (200, 302))
    # 公开/受保护页面
    for path, tag in [('/', '仪表盘'), ('/diagnose', '智能诊断'),
                      ('/knowledge', '知识百科'), ('/history', '诊断档案'),
                      ('/plants', '我的植物'), ('/detect-batch', '批量检测'),
                      ('/about', '关于')]:
        r = c.get(path)
        check(f'GET {path} ({tag}) -> 200',
              r.status_code == 200)
    # 静态资源
    for path in ['/static/css/style.css', '/static/js/main.js', '/static/js/diagnose.js']:
        r = c.get(path)
        check(f'GET {path} -> 200', r.status_code == 200)
    # 数据接口
    for path in ['/api/dashboard/stats', '/api/user/history_records', '/api/user/plants',
                 '/api/diseases?page=1&per_page=5', '/api/disease/29', '/api/disease/search?q=番茄']:
        r = c.get(path)
        check(f'GET {path} -> 200', r.status_code == 200)
    # 诊断兜底（无权重演示模式）
    r = c.post('/api/predict', data={'image': (io.BytesIO(_tiny_png()), 'test.png')},
               content_type='multipart/form-data')
    j = r.get_json()
    check('POST /api/predict -> success', r.status_code == 200 and j.get('success'))
    check('POST /api/predict 返回病害名', j.get('success') and j.get('disease_name'))

print("=" * 46)
print(f"通过 {passed}  失败 {failed}")
sys.exit(0 if failed == 0 else 1)
