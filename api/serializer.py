import datetime
from random import randint
from django.core.cache import cache
from rest_framework import serializers
from .models import User, GbPerform, GbMethod, Sample, Sheet, SheetItem, Report, CODES
from profiles.models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    # username = serializers.CharField(source='user.username')
    # email = serializers.CharField(source='user.email')
    # owner_page = serializers.PrimaryKeyRelatedField(many=True, queryset=Page.objects.all())

    class Meta:
        model = UserProfile
        fields = ('nickname', 'phone', 'picture_file')


class UserSerializer(serializers.ModelSerializer):
    userprofile = UserProfileSerializer()
    # 如果使用了命名空间，fields中不能加url参数，不知道为什么
    #owner_chapter = serializers.PrimaryKeyRelatedField(many=True, queryset=Chapter.objects.all())
    # owner_blog = serializers.HyperlinkedRelatedField(many=True, view_name='api:blog-detail', read_only=True)

    class Meta:
        model = User
        # fields = ('id', 'username', 'password', 'email', 'userprofile', 'owner_chapter')
        fields = ('id', 'username', 'password', 'email', 'userprofile')

    def create(self, validated_data):
        """此处需设置密码，否则密码是明文"""
        user_profile_data = validated_data.pop('userprofile')
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        user_profile_data['picture_file'] = 'prof%s@2x.png' % str(randint(1, 49))
        UserProfile.objects.create(user=user, **user_profile_data)
        return user


class GbMethodSerializer(serializers.ModelSerializer):
    parent_name = serializers.ReadOnlyField(source='parent.name')

    class Meta:
        # 不能将children写进来，否则提交表单提示没有children
        model = GbMethod
        fields = ('id', 'no', 'name', 'unit', 'standard', 'parent', 'perform', 'parent_name')


class GbPerformSerializer(serializers.ModelSerializer):
    # 格式化时间
    created = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)
    methods = GbMethodSerializer(many=True, read_only=True)

    class Meta:
        model = GbPerform
        fields = ('methods', 'id', 'no', 'name', 'created')
        # fields = '__all__'


class SampleSerializer(serializers.ModelSerializer):
    prod_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, allow_null=True)
    send_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, allow_null=True)
    rec_date = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, allow_null=True)
    sheet_id = serializers.ReadOnlyField(source='sheet.id')

    class Meta:
        model = Sample
        fields = ('id', 'code', 'name', 'seq', 'type', 'brand', 'prod_date', 'spec', 'num', 'store', 'prop',
                  'source', 'prod_firm', 'agent_firm', 'agent_address', 'agent_user', 'agent_tell',
                  'accept_firm', 'accept_user', 'accept_tell', 'send_user', 'send_date', 'rec_user',
                  'rec_date', 'status', 'create_time', 'sheet_id', 'report')
    
    def create(self, validated_data):
        # 生成样品标识
        now = datetime.datetime.now().strftime('%Y%m')
        key = 'code_%s' % now
        no = cache.get(key, 0)+1
        cache.set(key, no, 86400*30)

        code = int(validated_data.get('code'))
        validated_data['code'] = 'STS/%s-%s-%04d' % (CODES.get(code), now, no)
        validated_data['seq'] = no

        return super(SampleSerializer, self).create(validated_data)


class SheetItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = SheetItem
        fields = ('sheet', 'id', 'no', 'name', 'parent', 'unit', 'standard', 'result', 'conclusion')


class SheetSerializer(serializers.ModelSerializer):
    # items = serializers.PrimaryKeyRelatedField(many=True, queryset=SheetItem.objects.all())
    sample_name = serializers.ReadOnlyField(source='sample.name')
    sample_code = serializers.ReadOnlyField(source='sample.code')
    sample_num = serializers.ReadOnlyField(source='sample.num')
    sample_prop = serializers.ReadOnlyField(source='sample.prop')
    sample_brand = serializers.ReadOnlyField(source='sample.brand')
    sample_send_user = serializers.ReadOnlyField(source='sample.send_user')
    sample_rec_user = serializers.ReadOnlyField(source='sample.rec_user')
    sample_send_date = serializers.ReadOnlyField(source='sample.send_date')
    sample_rec_date = serializers.ReadOnlyField(source='sample.rec_date')
    sample_create_time = serializers.ReadOnlyField(source='sample.create_time')
    perform_no = serializers.ReadOnlyField(source='perform.no')
    perform_name = serializers.ReadOnlyField(source='perform.name')
    items = SheetItemSerializer(many=True, read_only=True)

    class Meta:
        model = Sheet
        fields = ('items', 'sample', 'id', 'check_start_date', 'check_end_date', 'temperature_start',
                  'temperature_end', 'humidity_start', 'humidity_end', 'instrument', 'result', 'created', 'perform',
                  'sample_name', 'sample_code', 'sample_num', 'sample_prop', 'sample_brand',
                  'sample_create_time', 'sample_send_user', 'sample_rec_user', 'perform_no', 'perform_name',
                  'sample_send_date', 'sample_rec_date')


class ReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = ('sample', 'id', 'no', 'send_time', 'created')

    def create(self, validated_data):
        # 生成样品标识
        now = datetime.datetime.now().strftime('%Y%m')
        key = 'prod_%s' % now
        no = cache.get(key, 0)+1
        cache.set(key, no, 86400*30)

        validated_data['no'] = 'SZCJ%s%04d' % (now, no)

        return super(ReportSerializer, self).create(validated_data)


# class BookSerializer(serializers.ModelSerializer):
#     book_chapter = serializers.PrimaryKeyRelatedField(many=True, queryset=Chapter.objects.all())
#     # collect_page = serializers.HyperlinkedRelatedField(many=True, view_name='api:page-detail', read_only=True)
#
#     class Meta:
#         model = Book
#         fields = ('id', 'book_name', 'owner', 'book_chapter')
#
#
# class ChapterSerializer(serializers.ModelSerializer):
#     # 此类也可以继承超链接类，这样owner和group就会显示成外键链接了
#     # 定义blog关联的user和group要显示的字段，不能和models中的重复
#     # uid = serializers.ReadOnlyField(source='owner.id')
#     nickname = serializers.ReadOnlyField(source='owner.userprofile.nickname')
#     picture_file = serializers.ReadOnlyField(source='owner.userprofile.picture_file')
#     username = serializers.ReadOnlyField(source='owner.username')
#     book_name = serializers.ReadOnlyField(source='book.book_name')
#
#     class Meta:
#         model = Chapter
#         fields = ('id', 'title', 'content', 'owner', 'book', 'create_date'
#                   , 'username', 'nickname', 'picture_file', 'book_name')
