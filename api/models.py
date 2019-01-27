from django.db import models
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from profiles.models import UserProfile

# code类别
CODES = {
    0: 'SP',
    1: 'W',
    2: 'TR',
    3: 'QT',
}
# 检验检测类别
SAMPLE_TYPE = {
    0: '/',
    1: '委托检验',
    2: '未确定',
}
# 性状/包装状态
SAMPLE_PROP = {
    0: '/',
    10: '固态/散装',
    11: '固态/棉纸装',
    12: '固态/罐装',
    21: '液态/无菌生理盐水试管',
    22: '液态/瓶装',
    23: '液态/罐装',
    24: '液态/无菌瓶',
    31: '固液混合态/瓶装',
}
# 样品状态
SAMPLE_STATUS = {
    0: '已收样',
    1: '已生成流转单',
    2: '已生成报告',
    3: '已发放报告',
    9: '已删除',
}


class GbPerform(models.Model):
    """国标-产品执行标准"""

    no = models.CharField(max_length=32, unique=True)  # 执行标准编号
    name = models.CharField(max_length=64)  # 执行标准名称
    created = models.DateTimeField(auto_now_add=True)  # 创建时间

    def __str__(self):
        return self.name

    class Meta:
        ordering = ('-created',)


class GbMethod(models.Model):
    """国标-检测方法标准"""

    no = models.CharField(max_length=32)  # 检测方法标准编号
    name = models.CharField(max_length=64)  # 检测方法标准名称
    unit = models.CharField(max_length=16, blank=True, null=True)  # 单位
    standard = models.CharField(max_length=32, blank=True, null=True)  # 标准值

    parent = models.ForeignKey('self', related_name='children', on_delete=models.CASCADE, blank=True, null=True)
    perform = models.ForeignKey(GbPerform, related_name='methods', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Report(models.Model):
    """检测报告"""

    no = models.CharField(max_length=64, unique=True)  # 报告编号
    send_time = models.DateTimeField(blank=True, null=True)  # 发放时间
    created = models.DateTimeField(auto_now_add=True)  # 生成时间

    # sample = models.OneToOneField(Sample, related_name='report', on_delete=models.CASCADE, default=None, null=True)


class Sample(models.Model):
    """样品"""
    type_list = [(k, v) for k, v in SAMPLE_TYPE.items()]
    prop_list = [(k, v) for k, v in SAMPLE_PROP.items()]
    status_list = [(k, v) for k, v in SAMPLE_STATUS.items()]

    code = models.CharField(max_length=64, unique=True)  # 样品标识
    seq = models.IntegerField(default=1)  # 样品标识的序号
    name = models.CharField(max_length=64)  # 样品名称
    type = models.IntegerField(choices=type_list)  # 检验检测类别
    brand = models.CharField(max_length=32, blank=True, null=True)  # 商标
    prod_date = models.DateTimeField(blank=True, null=True)  # 批号/生产日期
    spec = models.CharField(max_length=32, blank=True, null=True)  # 规格
    num = models.CharField(max_length=32)  # 样品数量
    store = models.CharField(max_length=64)  # 保存方式
    prop = models.IntegerField(choices=prop_list)  # 性状/包装状态
    source = models.CharField(max_length=64)  # 样品来源
    prod_firm = models.CharField(max_length=64, blank=True, null=True)  # 生产单位

    agent_firm = models.CharField(max_length=64, blank=True, null=True)  # 委托单位
    agent_address = models.CharField(max_length=128, blank=True, null=True)  # 委托单位地址
    agent_user = models.CharField(max_length=32)  # 联系人
    agent_tell = models.CharField(max_length=32)  # 联系电话

    accept_firm = models.CharField(max_length=64, blank=True, null=True)  # 受检单位
    accept_user = models.CharField(max_length=32)  # 受检单位联系人
    accept_tell = models.CharField(max_length=32)  # 受检单位联系电话

    send_user = models.CharField(max_length=32)  # 送样人
    send_date = models.DateTimeField(auto_now_add=True)  # 送样日期
    rec_user = models.CharField(max_length=32)  # 收样人
    rec_date = models.DateTimeField(auto_now_add=True)  # 收样日期

    status = models.IntegerField(choices=status_list, default=0)  # 状态
    create_time = models.DateTimeField(auto_now_add=True)  # 生成时间
    state_time = models.DateTimeField(auto_now=True)  # 状态时间

    report = models.ForeignKey(Report, related_name='sample', on_delete=models.CASCADE, default=None, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('-create_time',)

    def get_prop(self):
        return SAMPLE_PROP[self.prop]

    def get_type(self):
        return SAMPLE_TYPE[self.type]

    def __str__(self):
        return self.name


class Sheet(models.Model):
    """流转单"""

    check_start_date = models.DateTimeField(auto_now_add=True)  # 检测开始日期
    check_end_date = models.DateTimeField(blank=True, null=True)  # 检测结束日期
    temperature_start = models.CharField(max_length=32, blank=True, null=True)  # 开始温度
    temperature_end = models.CharField(max_length=32, blank=True, null=True)  # 结束温度
    humidity_start = models.CharField(max_length=32, blank=True, null=True)  # 开始湿度
    humidity_end = models.CharField(max_length=32, blank=True, null=True)  # 结束湿度
    instrument = models.CharField(max_length=128)  # 主要仪器
    result = models.CharField(max_length=128, blank=True, null=True)  # 检测结果
    created = models.DateTimeField(auto_now_add=True)  # 生成时间

    sample = models.OneToOneField(Sample, related_name='sheet', on_delete=models.CASCADE, default=None)
    perform = models.ForeignKey(GbPerform, related_name='sheet', on_delete=models.CASCADE, blank=True, null=True)


class SheetItem(models.Model):
    """流转单检测项目，如果没有执行标准需要手动填"""

    no = models.CharField(max_length=32)  # 检测方法标准编号
    name = models.CharField(max_length=64)  # 检测方法标准名称
    parent = models.CharField(max_length=64, blank=True, null=True)  # 父级检测方法名称
    unit = models.CharField(max_length=16, blank=True, null=True)  # 单位
    standard = models.CharField(max_length=32, blank=True, null=True)  # 标准值
    result = models.CharField(max_length=32, blank=True, null=True)  # 检测结果值
    conclusion = models.CharField(max_length=32, blank=True, null=True)  # 结论(是否合格)

    # parent = models.ForeignKey('self', related_name='children', on_delete=models.CASCADE, blank=True, null=True)
    sheet = models.ForeignKey(Sheet, related_name='items', on_delete=models.CASCADE)


# class SealLog (models.Model):
#     """用章登记表"""
#
#     name = models.CharField(max_length=64)  # 用章名称
#     person = models.CharField(max_length=16)  # 用章人姓名
#     use_date = models.DateTimeField(auto_now_add=True)  # 用章日期
#
#     report = models.ForeignKey(Report, on_delete=models.CASCADE)
#
#
# class HoldSample(models.Model):
#     """留样处理表"""
#
#     # TODO：要记录什么？
#
#     sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=None)


# 创建用户时自动调用该函数生成token
