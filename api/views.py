import os
import pdfkit
from rest_framework.pagination import *
from rest_framework import viewsets, views
from rest_framework.decorators import list_route, detail_route
from rest_framework.reverse import reverse
from rest_framework.filters import SearchFilter
from rest_framework.permissions import *
from rest_framework.renderers import *
from rest_framework.authentication import TokenAuthentication, exceptions
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.shortcuts import render, reverse
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponseNotFound, FileResponse
from datetime import datetime, timedelta
from django.contrib.auth.forms import PasswordChangeForm
from .serializer import *
from .permissions import *


class SmallPageNumberPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('page_size', self.page_size),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class MyObtainAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        data = {}
        try:
            serializer = self.serializer_class(data=request.data,
                                               context={'request': request})
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            data = {
                'token': token.key,
                # 'picture_file': '%s' % user.userprofile.picture_file,
                'uid': user.id,
                'username': user.username,
                # 'nickname': user.userprofile.nickname
            }
        except Exception as ex:
            data = {'token': ''}
        finally:
            return Response(data)


class ObtainAuthTokenCookie(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data,
                                               context={'request': request})
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']

            # 每次登陆需要获取token，每次都需要将token重置，否则token将存在将永远被盗用的风险
            token = Token.objects.get(user=user)
            token.delete()
            token, created = Token.objects.get_or_create(user=user)

            # response = Response({'token': token.key})
            response = HttpResponseRedirect(reverse('api:blogs-list'))
            expire = datetime.now() + timedelta(minutes=1)
            response.set_cookie(key='token', value=token.key, expires=expire)
            response.set_cookie(key='username', value=user)
        except Exception as ex:
            print(ex.args)
            response = HttpResponseNotFound()

        return response


class ExpireTokenAuthentication(TokenAuthentication):
    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        # 设置token失效时间
        if timezone.now() > (token.created + timedelta(days=1)):
            raise exceptions.AuthenticationFailed(_('Token has expired'))

        return (token.user, token)


# class UserProfileViewSet(viewsets.ModelViewSet):
class UserViewSet(viewsets.ModelViewSet):
    # queryset = UserProfile.objects.all()
    queryset = User.objects.all()
    # serializer_class = UserProfileSerializer
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    authentication_classes = (TokenAuthentication,)
    pagination_class = SmallPageNumberPagination

    def retrieve(self, request, *args, **kwargs):
        # 取该用户下所有文章
        instance = self.get_object()
        # queryset = Chapter.objects.filter(owner=instance.pk)
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     pages_serializer = ChapterSerializer(page, many=True)
        #     response = self.get_paginated_response(pages_serializer.data)
        # else:
        #     pages_serializer = ChapterSerializer(queryset, many=True)
        #     response = Response(pages_serializer.data)
        #
        # pages = get_page_data(response.data)
        #
        # return Response(pages)

    @detail_route(methods=['patch'])
    def set_password(self, request, pk=None):
        """自定义修改密码方法"""
        user = self.get_object()
        # user = request.user
        form = PasswordChangeForm(user, data=request.data)
        if form.is_valid():
            # 这里要传加密前的密码
            if form.data['new_password1'] == form.data['new_password2']:
                user.set_password(form.data['new_password2'])
                user.save()
                return Response({'status': 200})
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(form.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @list_route(methods=['post'], permission_classes=[], authentication_classes=[])
    def register(self, request, *args, **kwargs):
        """自定义注册方法"""
        serializer = self.get_serializer(data=request.data)
        # serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GbPerformViewSet(viewsets.ModelViewSet):
    queryset = GbPerform.objects.all()
    serializer_class = GbPerformSerializer
    pagination_class = SmallPageNumberPagination
    filter_backends = (SearchFilter,)
    search_fields = ('$no', '$name')


class GbMethodViewSet(viewsets.ModelViewSet):
    queryset = GbMethod.objects.all()
    serializer_class = GbMethodSerializer


class SampleViewSet(viewsets.ModelViewSet):
    queryset = Sample.objects.all()
    serializer_class = SampleSerializer
    pagination_class = SmallPageNumberPagination
    filter_backends = (SearchFilter,)
    search_fields = ('$code', '$name')
    # permission_classes = (IsAuthenticatedOrReadOnly, IsAdminUserOrReadOnly)
    # authentication_classes = (TokenAuthentication,)

    # 前端：https://github.com/taylorchen709/vue-admin

    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            user = self.request.user
        else:
            user = User.objects.get(id=1)
        serializer.save(owner=user)


class SheetViewSet(viewsets.ModelViewSet):
    queryset = Sheet.objects.all()
    serializer_class = SheetSerializer


class SheetItemViewSet(viewsets.ModelViewSet):
    queryset = SheetItem.objects.all()
    serializer_class = SheetItemSerializer


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer


class SheetHeader(views.APIView):
    def get(self, request):
        params = request.query_params.dict()
        page = int(params.get('page', 0))
        pages = int(params.get('sitepages', 0))
        return render(request, 'sheet_header.html', {'page': page, 'pages': pages})


class SheetView(views.APIView):
    @staticmethod
    def get_object(pk):
        try:
            return Sample.objects.get(pk=pk)
        except Sample.DoesNotExist:
            raise Http404

    def get(self, request, sample_id):
        sample = self.get_object(sample_id)
        sample_serializer = SampleSerializer(sample)
        sheet_serializer = SheetSerializer(sample.sheet)

        sheet_items = []
        for item in sheet_serializer.data.get('items'):
            if not item.get('parent'):
                sheet_items.append(item)

        data = sample_serializer.data
        data['prop'] = sample.get_prop()
        data['send_date'] = sample.send_date.strftime('%Y.%m.%d')
        data['rec_date'] = sample.rec_date.strftime('%Y.%m.%d')
        data['perform_no'] = sheet_serializer.data.get('perform_no')
        data['sheet_items'] = sheet_items
        data['sheet_items_len'] = len(data['sheet_items'])

        return render(request, 'sheet.html', data)


class DownloadSheet(views.APIView):
    @staticmethod
    def get_object(pk):
        try:
            return Sample.objects.get(pk=pk)
        except Sample.DoesNotExist:
            raise Http404

    def get(self, request, sample_id):
        sample = self.get_object(sample_id)
        sample_serializer = SampleSerializer(sample)

        filename = ''.join([sample_serializer.data.get('code')[4:], '.pdf'])
        file_path = os.path.join(
            os.path.dirname(os.path.realpath('__file__')), 'sheet_file/%s' % filename
        )

        options = {
            'page-size': 'A4',
            'margin-top': '30mm',
            'margin-right': '20mm',
            'margin-left': '20mm',
            'header-html': ''.join(['http://127.0.0.1:8000', reverse('api:sheet_header')]),
        }
        url = 'http://localhost:8000%s' % reverse('api:sheet_view', kwargs={'sample_id': sample_id})
        pdfkit.from_url(url, file_path, options=options)

        sample.status = 1
        sample.save()

        file = open(file_path, 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="%s"' % filename
        return response


class ReportFooter(views.APIView):
    def get(self, request):
        params = request.query_params.dict()
        page = int(params.get('page', 0)) - 2
        pages = int(params.get('sitepages', 0)) - 2
        return render(request, 'report_footer.html', {'page': page, 'pages': pages})


class ReportView(views.APIView):
    @staticmethod
    def get_object(pk):
        try:
            return Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            raise Http404

    def get(self, request, report_id):
        report = self.get_object(report_id)
        report_serializer = ReportSerializer(report)
        sample = report.sample.get()
        sample_serializer = SampleSerializer(sample)
        sheet_serializer = SheetSerializer(sample.sheet)
        perform_serializer = GbPerformSerializer(sample.sheet.perform)

        items_no_group = {'count': 0, 'items': []}
        items_group = {'items': []}
        group_name = ''
        for item in sheet_serializer.data.get('items'):
            if item.get('parent'):
                group_name = item.get('parent')
                items_group['items'].append(item)
            else:
                items_no_group['items'].append(item)

        items_group['count'] = len(items_group['items'])
        items_group['group_name'] = group_name

        context = {
            'report': report_serializer.data,
            'sample': sample_serializer.data,
            'sheet': sheet_serializer.data,
            'perform': perform_serializer.data,
            'items_group': items_group,
            'items_group_len': len(items_group),
            'items_no_group': items_no_group,
            'items_no_group_len': len(items_no_group),
        }
        context['sample']['type'] = sample.get_type()
        context['sample']['prop'] = sample.get_prop()
        return render(request, 'report.html', context=context)


class DownloadReport(views.APIView):
    @staticmethod
    def get_object(pk):
        try:
            return Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            raise Http404

    def get(self, request, report_id):
        report = self.get_object(report_id)
        report_serializer = ReportSerializer(report)

        filename = '%s.pdf' % report_serializer.data.get('no')
        file_path = os.path.join(os.path.dirname(os.path.realpath('__file__')),
                                 'report_file/%s' % filename)

        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'footer-html': ''.join(['http://127.0.0.1:8000', reverse('api:report_footer')]),
        }
        url = 'http://localhost:8000%s' % reverse('api:report_view', kwargs={'report_id': report_id})
        pdfkit.from_url(url, file_path, options=options)

        file = open(file_path, 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="%s"' % filename
        return response


# class BookViewSet(viewsets.ModelViewSet):
#     queryset = Book.objects.all()
#     serializer_class = BookSerializer
#     # #permission_classes = (IsAuthenticatedOrReadOnly, IsAdminUserOrReadOnly)
#     # #authentication_classes = (TokenAuthentication, )
#     pagination_class = SmallPageNumberPagination
#
#     def list(self, request, *args, **kwargs):
#         print(reverse('api:token'))
#         """获取所有用户所有组发表的文章"""
#         obj = super(BookViewSet, self).list(request, *args, **kwargs)
#
#         # 重新构建返回对象，否则不能被js识别
#         collect_list = []
#         for s in obj.data.get('results', []):
#             item = {}
#             for k, v in s.items():
#                 if k == 'collect_id':
#                     item[k] = v
#                     item['collect_detail_url'] = reverse('web:collect-detail', args={v})
#                 else:
#                     item[k] = v
#             collect_list.append(item)
#
#         return Response(collect_list)
#
#     def retrieve(self, request, *args, **kwargs):
#         # 取该分组下所有文章
#         instance = self.get_object()
#         queryset = Chapter.objects.filter(owner=instance.pk)
#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             pages_serializer = ChapterSerializer(page, many=True)
#             response = self.get_paginated_response(pages_serializer.data)
#         else:
#             pages_serializer = ChapterSerializer(queryset, many=True)
#             response = Response(pages_serializer.data)
#
#         pages = get_page_data(response.data)
#
#         return Response(pages)
#
#
# class ChapterViewSet(viewsets.ModelViewSet):
#     queryset = Chapter.objects.all()
#     serializer_class = ChapterSerializer
#     # #permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly,)
#     # #authentication_classes = (TokenAuthentication,)
#     pagination_class = SmallPageNumberPagination
#     filter_backends = (SearchFilter,)
#     search_fields = ('$content', '$title')
#
#     '''
#     def list(self, request, *args, **kwargs):
#         """获取所有用户所有组发表的文章"""
#         response = super(ChapterViewSet, self).list(request, *args, **kwargs)
#         pages = get_page_data(response.data)
#
#         return Response(pages)
#     '''
