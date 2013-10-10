#coding=utf-8
from django.shortcuts import render_to_response, get_object_or_404
from django.core import serializers
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import RequestContext
import feedparser
import json
import time
import threading
import xml.dom.minidom
from models import *
from forms import UploadFileForm


thread_count_dic = {'update_thread_count': 0, 'import_thread_count': 0}
update_thread_count = 0
#线程限制数
thread_count_max = 10


def index(request):
    """
    主页
    :param request:
    :return:
    """
    return render_to_response('index.html')


def get_all_feed_list(request):
    """
    获取所有订阅列表

    :param request:
    """
    feeds = get_feed_list()

    return HttpResponse(feeds)


def get_feed_content(request):
    """
    获取指定订阅的文章
    :param request:
    :return:
    """
    feed_id = int(request.GET.get('id'))
    unread_count = request.GET.get('unreadCount')
    if unread_count is None:
        unread_count = 0

    page_size = 10
    start = int(unread_count)
    end = int(unread_count) + page_size - 1

    if feed_id != 0:
        item_list = Item.objects.select_related().filter(feed_id=feed_id).order_by('-pub_date')[start:end]
    else:
        item_list = Item.objects.select_related().all().order_by('-pub_date')[start:end]
    list_temp = []

    for item in item_list:
        dicItem = {'id': item.id, 'title': item.title, 'content': item.content, 'url': item.url,
                   'feed_title': item.feed.title,
                   'feed_url': item.feed.url}
        list_temp.append(dicItem)

    items_json = json.dumps(list_temp)

    return HttpResponse(items_json)


def add_feed(request):
    """
    添加订阅
    :param request:
    """
    url = request.GET.get('url')
    d = feedparser.parse(url)

    feed_list = Feed.objects.filter(feed_url=url)
    if feed_list.count() == 0:
        home_url = get_home_url(d.feed.link)

        feed = Feed(title=d.feed.title, url=d.feed.link, feed_url=url, icon=home_url + '/favicon.ico')
        feed.save()
        if len(d.entries) > 0:
            insert_to_item(d, feed)

    return HttpResponse('success')


def get_feed_list():
    """
    获取订阅列表

    :return:
    """
    feed_list = Feed.objects.all()
    feeds_json = serializers.serialize("json", feed_list)

    return feeds_json


def get_home_url(link):
    """
    获取主页url
    :param link:
    """
    index = link.find('/', 8)
    if index == -1:
        index = link.find('?', 8)
        if index == -1:
            home_url = link[0:]
        else:
            home_url = link[0:index]
    else:
        home_url = link[0:index]

    return home_url


def del_item(request):
    """
    删除文章
    """
    msg = 'success'
    item_id = request.GET.get('id')
    if item_id and int(item_id) > 0:
        try:
            item = get_object_or_404(Item, pk=int(item_id))
            item.delete()
        except Http404 as e:
            msg = ''
    else:
        item = Item.objects.all()
        item.delete()

    return HttpResponse(msg)


def update_content(request):
    feed_list = Feed.objects.all()
    th_list = []
    for feed in feed_list:
        while int(thread_count_dic['update_thread_count']) == thread_count_max:
            continue
        th = threading.Thread(target=thread_handler, args=(feed, 'update',))
        th_list.append(th)
        thread_count_dic['update_thread_count'] = int(thread_count_dic['update_thread_count']) + 1
        th.start()


    #等待线程结束
    #for th in th_list:
    #    while th.isAlive():
    #        continue

    return HttpResponse('success')


def thread_handler(feed, ops):
    url = feed.feed_url
    d = feedparser.parse(url)
    if len(d.entries) > 0:
        insert_to_item(d, feed)

    thread_count = int(thread_count_dic[ops + '_thread_count'])
    thread_count_dic[ops + '_thread_count'] = thread_count - 1


def insert_to_item(d, feed):
    local_date = feed.update_date
    if hasattr(d.entries[0], 'published_parsed'):
        pub_date = time.strftime('%Y-%m-%d %X', d.entries[0].published_parsed)
    else:
        pub_date = time.strftime('%Y-%m-%d %X', d.entries[0].updated_parsed)

    if local_date is None or pub_date > local_date:
        feed.update_date = pub_date
        feed.save()

        for entry in d.entries:
            if hasattr(entry, 'published_parsed'):
                pub_date = time.strftime('%Y-%m-%d %X', entry.published_parsed)
            else:
                pub_date = time.strftime('%Y-%m-%d %X', entry.updated_parsed)

            item = Item(title=entry.title, url=entry.link, content=entry.description, pub_date=pub_date,
                        feed_id=feed.id, user_id=1, state=0)
            item.save()


def setting(request):
    return render_to_response('setting.html', context_instance=RequestContext(request))


def about(request):
    return render_to_response('about.html')


def app(request):
    return render_to_response('app.html')


def import_opml(request):
    """

    @param request:
    @return:
    """
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_opml(request.FILES['file'])
    return HttpResponseRedirect('/')


def handle_opml(f):
    try:
        xml_str = f.read()
        doc = xml.dom.minidom.parseString(xml_str)
        th_list = []
        for node in doc.getElementsByTagName('outline'):
            feed_list = Feed.objects.filter(feed_url=node.getAttribute('xmlUrl'))
            if feed_list.count() == 0:
                home_url = get_home_url(node.getAttribute('htmlUrl'))

                feed = Feed(title=node.getAttribute('title'), url=home_url, feed_url=node.getAttribute('xmlUrl'),
                            icon=home_url + '/favicon.ico')
                feed.save()

                while int(thread_count_dic['import_thread_count']) == thread_count_max:
                    continue
                th = threading.Thread(target=thread_handler, args=(feed, 'import'))
                th_list.append(th)
                thread_count_dic['update_thread_count'] = int(thread_count_dic['import_thread_count']) + 1
                th.start()

        for th in th_list:
            while th.isAlive():
                continue
    except Exception as e:
        return