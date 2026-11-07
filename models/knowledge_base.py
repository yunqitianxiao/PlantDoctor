# models/knowledge_base.py
# PlantVillage 数据集 38 类病害知识库
 
ALL_DISEASES = {
    0: {"name": "苹果黑星病", "category": "苹果", "symptoms": "叶片出现黑色圆形病斑，边缘清晰，后期病斑连片，叶片卷曲脱落", "causes": "真菌 Venturia inaequalis 侵染，高湿环境易发", "treatment": "喷洒戊唑醇或嘧菌酯，每7-10天一次，连续2-3次；清除落叶", "prevention": "选择抗病品种，冬季修剪通风透光，萌芽前喷石硫合剂"},
    1: {"name": "苹果黑腐病", "category": "苹果", "symptoms": "果实和叶片出现黑褐色腐烂斑，有轮纹，后期病部干枯开裂", "causes": "真菌 Botryosphaeria obtusa 侵染", "treatment": "剪除病枝，喷施苯醚甲环唑，加强树体营养", "prevention": "清除果园病残体，春季喷保护性杀菌剂"},
    2: {"name": "苹果雪松赤星病", "category": "苹果", "symptoms": "叶片产生橙黄色圆形病斑，后期长出黑色小点", "causes": "真菌 Gymnosporangium juniperi-virginianae", "treatment": "喷施三唑酮或腈菌唑", "prevention": "铲除果园周围雪松，避免混栽"},
    3: {"name": "苹果健康", "category": "苹果", "symptoms": "叶片绿色健康，无病斑", "causes": "无", "treatment": "正常管理，注意预防", "prevention": "常规水肥管理"},
    4: {"name": "蓝莓健康", "category": "蓝莓", "symptoms": "植株生长旺盛", "causes": "无", "treatment": "正常管理", "prevention": "保持酸性土壤"},
    5: {"name": "樱桃白粉病", "category": "樱桃", "symptoms": "叶片表面覆盖白色粉状霉层，后期变灰", "causes": "真菌 Podosphaera clandestina", "treatment": "喷施硫磺悬浮剂或戊唑醇", "prevention": "合理修剪，增强通风"},
    6: {"name": "樱桃健康", "category": "樱桃", "symptoms": "叶片健康", "causes": "无", "treatment": "正常管理", "prevention": "常规管理"},
    7: {"name": "玉米灰斑病", "category": "玉米", "symptoms": "叶片产生灰色长条形病斑，平行于叶脉", "causes": "真菌 Cercospora zeae-maydis", "treatment": "喷施吡唑醚菌酯或嘧菌酯", "prevention": "选用抗病品种，合理密植"},
    8: {"name": "玉米锈病", "category": "玉米", "symptoms": "叶片出现黄褐色粉末状孢子堆", "causes": "真菌 Puccinia sorghi", "treatment": "喷施三唑酮或戊唑醇", "prevention": "避免偏施氮肥"},
    9: {"name": "玉米大斑病", "category": "玉米", "symptoms": "叶片产生梭形大斑，灰绿色至褐色", "causes": "真菌 Exserohilum turcicum", "treatment": "喷施嘧菌酯或苯醚甲环唑", "prevention": "种植抗病品种"},
    10: {"name": "玉米健康", "category": "玉米", "symptoms": "健康", "causes": "无", "treatment": "正常", "prevention": "常规"},
    11: {"name": "葡萄黑腐病", "category": "葡萄", "symptoms": "果实变黑腐烂，叶片产生褐色病斑", "causes": "真菌 Guignardia bidwellii", "treatment": "喷施代森锰锌或嘧菌酯", "prevention": "冬季清园"},
    12: {"name": "葡萄轮斑病", "category": "葡萄", "symptoms": "叶片产生同心轮纹状病斑", "causes": "真菌 Pseudocercospora vitis", "treatment": "喷施苯醚甲环唑", "prevention": "增强树势"},
    13: {"name": "葡萄褐斑病", "category": "葡萄", "symptoms": "叶片产生褐色角状病斑", "causes": "真菌 Pseudocercospora vitis", "treatment": "喷施戊唑醇", "prevention": "及时摘除病叶"},
    14: {"name": "葡萄健康", "category": "葡萄", "symptoms": "健康", "causes": "无", "treatment": "正常", "prevention": "常规"},
    15: {"name": "柑橘黄龙病", "category": "柑橘", "symptoms": "叶片斑驳黄化，果实畸形，红鼻子果", "causes": "细菌 Candidatus Liberibacter asiaticus", "treatment": "砍除病树，防治木虱，喷施四环素类药剂", "prevention": "使用无病苗木，统防统治木虱"},
    16: {"name": "桃穿孔病", "category": "桃", "symptoms": "叶片产生紫色小点，后穿孔", "causes": "细菌 Xanthomonas campestris", "treatment": "喷施春雷霉素或噻唑锌", "prevention": "加强通风"},
    17: {"name": "桃健康", "category": "桃", "symptoms": "健康", "causes": "无", "treatment": "正常", "prevention": "常规"},
    18: {"name": "辣椒细菌性斑点病", "category": "辣椒", "symptoms": "叶片水渍状小斑，后期变褐坏死", "causes": "细菌 Xanthomonas campestris", "treatment": "喷施中生菌素或噻菌铜", "prevention": "种子消毒"},
    19: {"name": "辣椒健康", "category": "辣椒", "symptoms": "健康", "causes": "无", "treatment": "正常", "prevention": "常规"},
    20: {"name": "马铃薯早疫病", "category": "马铃薯", "symptoms": "叶片产生褐色同心轮纹病斑", "causes": "真菌 Alternaria solani", "treatment": "喷施代森锰锌或嘧菌酯", "prevention": "轮作"},
    21: {"name": "马铃薯晚疫病", "category": "马铃薯", "symptoms": "叶片水渍状暗绿色斑，背面生白霉", "causes": "真菌 Phytophthora infestans", "treatment": "喷施烯酰吗啉或霜脲氰", "prevention": "选用抗病品种"},
    22: {"name": "马铃薯健康", "category": "马铃薯", "symptoms": "健康", "causes": "无", "treatment": "正常", "prevention": "常规"},
    23: {"name": "覆盆子健康", "category": "覆盆子", "symptoms": "健康", "causes": "无", "treatment": "正常", "prevention": "常规"},
    24: {"name": "大豆健康", "category": "大豆", "symptoms": "健康", "causes": "无", "treatment": "正常", "prevention": "常规"},
    25: {"name": "南瓜白粉病", "category": "南瓜", "symptoms": "叶片白色粉状霉层", "causes": "真菌 Sphaerotheca fuliginea", "treatment": "喷施硫磺或戊唑醇", "prevention": "加强通风"},
    26: {"name": "草莓叶焦病", "category": "草莓", "symptoms": "叶缘干枯焦灼", "causes": "生理性病害或细菌", "treatment": "补充钙肥，控制盐分", "prevention": "合理施肥"},
    27: {"name": "草莓健康", "category": "草莓", "symptoms": "健康", "causes": "无", "treatment": "正常", "prevention": "常规"},
    28: {"name": "番茄细菌性斑点病", "category": "番茄", "symptoms": "叶片出现黑色小斑点", "causes": "细菌 Pseudomonas syringae", "treatment": "喷施铜制剂或噻唑锌", "prevention": "种子处理"},
    29: {"name": "番茄早疫病", "category": "番茄", "symptoms": "叶片同心轮纹病斑", "causes": "真菌 Alternaria solani", "treatment": "喷施嘧菌酯或苯醚甲环唑", "prevention": "轮作"},
    30: {"name": "番茄晚疫病", "category": "番茄", "symptoms": "叶片暗绿色水渍状，茎部黑褐", "causes": "真菌 Phytophthora infestans", "treatment": "喷施烯酰吗啉·霜脲氰", "prevention": "降低湿度"},
    31: {"name": "番茄叶霉病", "category": "番茄", "symptoms": "叶片背面生灰紫色霉层", "causes": "真菌 Fulvia fulva", "treatment": "喷施嘧菌酯或春雷霉素", "prevention": "加强通风"},
    32: {"name": "番茄隔斑病", "category": "番茄", "symptoms": "叶片产生褐色斑点，边缘黄色", "causes": "真菌 Septoria lycopersici", "treatment": "喷施苯醚甲环唑", "prevention": "及时清除病叶"},
    33: {"name": "番茄红蜘蛛损伤", "category": "番茄", "symptoms": "叶片失绿有白色小点，背面有细网", "causes": "叶螨 Tetranychus urticae", "treatment": "喷施阿维菌素或哒螨灵", "prevention": "增加湿度"},
    34: {"name": "番茄靶斑病", "category": "番茄", "symptoms": "叶片圆形褐色斑，有靶心", "causes": "真菌 Corynespora cassiicola", "treatment": "喷施啶酰菌胺或氟吡菌酰胺", "prevention": "避免密植"},
    35: {"name": "番茄黄化曲叶病毒", "category": "番茄", "symptoms": "叶片黄化卷曲，植株矮化", "causes": "番茄黄化曲叶病毒", "treatment": "无特效药，防治烟粉虱，拔除病株", "prevention": "防虫网隔离"},
    36: {"name": "番茄花叶病毒", "category": "番茄", "symptoms": "叶片花叶，皱缩", "causes": "烟草花叶病毒", "treatment": "喷施病毒抑制剂，增强抗性", "prevention": "种子消毒"},
    37: {"name": "番茄健康", "category": "番茄", "symptoms": "健康", "causes": "无", "treatment": "正常", "prevention": "常规"},
}
def get_disease_by_code(code):
    """根据分类索引（0-37）获取病害信息"""
    return ALL_DISEASES.get(code, {"name": "未知病害", "category": "未知", "symptoms": "无", "causes": "无", "treatment": "请重新诊断", "prevention": "无"})
 
def get_disease_by_name(name):
    """根据病害名称获取信息（精确匹配 + 模糊匹配）"""
    for code, info in ALL_DISEASES.items():
        if info["name"] == name:
            return {"code": code, **info}
    for code, info in ALL_DISEASES.items():
        if name in info["name"] or info["name"] in name:
            return {"code": code, **info}
    return None
 
def get_all_diseases(page=1, per_page=20, category=None):
    """分页获取所有病害"""
    results = []
    for code, info in ALL_DISEASES.items():
        if category and info["category"] != category:
            continue
        results.append({"code": code, **info})
    start = (page - 1) * per_page
    end = start + per_page
    return results[start:end], len(results)
 
def get_categories():
    """获取所有作物分类"""
    cats = set()
    for info in ALL_DISEASES.values():
        cats.add(info["category"])
    return sorted(list(cats))
