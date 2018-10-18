from requests_html import HTMLSession
from queue import Queue
import requests
import random

import threading
CARWL_EXIT = False
DOWN_EXIT = False

session = HTMLSession()

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
]


# 获取图书下载链接的线程类
class ThreadCrawl(threading.Thread):


    def __init__(self,thread_name,page_queue,data_queue):

        super(ThreadCrawl,self).__init__()
        self.thread_name = thread_name
        self.page_queue = page_queue
        self.data_queue = data_queue
        self.page_url = "http://www.allitebooks.com/page/{}"

    def run(self):
        print(self.thread_name+" 启动*********")

        while not CARWL_EXIT:
            try:
                page = self.page_queue.get(block=False)
                page_url = self.page_url.format(page)
                self.get_list(page_url)

            except Exception as e:
                print(e)
                break


    # 获取当前列表页所有图书链接
    def get_list(self,url):

        try:
            response = session.get(url)
        except Exception as e:
            print(e)
            raise e

        all_link = response.html.find('.entry-title>a') # 获取页面所有图书详情链接


        for link in all_link:
            self.get_book_url(link.attrs['href'])

    # 获取图书下载链接
    def get_book_url(self,url):
        try:
            response = session.get(url)

        except Exception as e:
            print(e)
            raise e

        download_url = response.html.find('.download-links a', first=True)

        if download_url is not None: # 如果下载链接存在，那么继续下面的爬取工作
            link = download_url.attrs['href']
            self.data_queue.put(link)
            print("抓取到{}".format(link))


class ThreadDown(threading.Thread):
    def __init__(self, thread_name, data_queue):
        super(ThreadDown, self).__init__()
        self.thread_name = thread_name
        self.data_queue = data_queue

    def run(self):
        print(self.thread_name + ' 启动************')
        while not DOWN_EXIT:
            try:
                book_link = self.data_queue.get(block=False)
                self.download(book_link)
            except Exception as e:
                pass



    def download(self,url):
        # 随机浏览器User-Agent
        headers = {"User-Agent":random.choice(USER_AGENTS)}

        # 获取文件名字
        filename = url.split('/')[-1]

        # 如果url里面包含pdf
        if '.pdf' in url or '.epub' in url:

            file = 'book/'+filename  # 文件路径已经写死，请在跟目录先创建好一个book文件夹

            with open(file,'wb') as f:  # 开始二进制写文件

                print("正在下载 {}".format(filename))

                response = requests.get(url,stream=True,headers=headers)

                # 获取文件大小
                totle_length = response.headers.get("content-length")

                # 如果文件大小不存在，则直接写入返回的文本
                if totle_length is None:
                    f.write(response.content)

                else:

                    for data in response.iter_content(chunk_size=4096):
                        f.write(data)
                    else:
                        f.close()

                print("{}下载完成".format(filename))

if __name__ == '__main__':

    page_queue = Queue(5)
    for i in range(1,6):
        page_queue.put(i)  # 把页码存储到page_queue里面

    # 采集结果
    data_queue = Queue()

    # 记录线程列表
    thread_crawl = []
    # 每次开启5个线程
    craw_list = ["采集线程1号","采集线程2号","采集线程3号","采集线程4号","采集线程5号"]

    for thread_name in craw_list:
        c_thread = ThreadCrawl(thread_name,page_queue,data_queue)
        c_thread.start()
        thread_crawl.append(c_thread)

    while not page_queue.empty():
        pass

    # 如果page_queue为空，采集线程退出循环
    CARWL_EXIT = True

    for thread in thread_crawl:
        thread.join()
        print("抓取线程结束")

    thread_image = []
    image_list = ['下载线程1号', '下载线程2号', '下载线程3号', '下载线程4号']
    for thread_name in image_list:
        d_thread = ThreadDown(thread_name, data_queue)
        d_thread.start()
        thread_image.append(d_thread)



    while not data_queue.empty():
        pass


    DOWN_EXIT = True

    for thread in thread_image:
        thread.join()
        print("下载线程结束")




