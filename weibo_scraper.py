import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import os
from urllib.parse import urlencode

class WeiboScraper:
    def __init__(self):
        self.base_url = 'https://weibo.com/ajax/statuses/mymblog'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://weibo.com/u/1592054367',
            'Origin': 'https://weibo.com'
        }
        # Cookie需要在运行时设置
        self.cookies = {}
        self.user_id = '1592054367'
        self.output_dir = 'weibo_content'
        
    def set_cookies(self, cookie_string):
        """设置cookies"""
        cookie_dict = {}
        for item in cookie_string.split('; '):
            if '=' in item:
                key, value = item.split('=', 1)
                cookie_dict[key] = value
        self.cookies = cookie_dict

    def get_weibo_posts(self, page=1):
        """获取微博内容"""
        params = {
            'uid': self.user_id,
            'page': page,
            'feature': 0
        }
        try:
            response = requests.get(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                params=params
            )
            print(f'API响应状态码: {response.status_code}')
            if response.status_code != 200:
                print(f'API响应内容: {response.text}')
                return None
            try:
                data = response.json()
                posts_count = len(data.get("data", {}).get("list", []))
                print(f'获取到的微博数量: {posts_count}条')
                if posts_count == 0:
                    print(f'完整的API响应: {data}')
                return data
            except json.JSONDecodeError as e:
                print(f'JSON解析失败: {str(e)}')
                print(f'响应内容: {response.text}')
                return None
        except Exception as e:
            print(f'获取微博内容失败: {str(e)}')
            return None

    def download_image(self, url, filename):
        """下载图片"""
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f'下载图片失败: {str(e)}')
        return False

    def generate_markdown(self, posts):
        """生成Markdown格式的内容"""
        markdown_content = '# 神农投资陈营长的微博内容\n\n'
        
        for post in posts:
            created_at = datetime.strptime(post['created_at'], '%a %b %d %H:%M:%S %z %Y')
            markdown_content += f'## {created_at.strftime("%Y-%m-%d %H:%M:%S")}\n\n'
            
            # 添加文本内容
            markdown_content += f'{post["text"]}\n\n'
            
            # 处理图片
            if 'pic_ids' in post and post['pic_ids']:
                markdown_content += '### 图片\n\n'
                for pic_id in post['pic_ids']:
                    image_path = f'images/{pic_id}.jpg'
                    image_url = f'https://wx1.sinaimg.cn/large/{pic_id}.jpg'
                    if self.download_image(image_url, os.path.join(self.output_dir, image_path)):
                        markdown_content += f'![{pic_id}]({image_path})\n\n'
            
            markdown_content += '---\n\n'
        
        return markdown_content

    def save_markdown(self, content):
        """保存Markdown文件"""
        os.makedirs(self.output_dir, exist_ok=True)
        with open(os.path.join(self.output_dir, 'weibo_content.md'), 'w', encoding='utf-8') as f:
            f.write(content)

    def run(self, cookie_string):
        """运行爬虫"""
        print('开始设置Cookie...')
        self.set_cookies(cookie_string)
        all_posts = []
        page = 1
        
        while True:
            print(f'\n正在获取第{page}页的微博内容...')
            data = self.get_weibo_posts(page)
            if not data:
                print('获取数据失败，请检查Cookie是否有效。')
                return
            if 'data' not in data:
                print(f'API响应格式异常: {data}')
                return
            if not data['data']['list']:
                print('没有更多微博内容。')
                break
                
            posts = data['data']['list']
            # 检查是否到达2024年1月1日
            last_post = posts[-1]
            last_post_time = datetime.strptime(last_post['created_at'], '%a %b %d %H:%M:%S %z %Y')
            target_date = datetime(2024, 1, 1, tzinfo=last_post_time.tzinfo)
            if last_post_time < target_date:
                # 只保留2024年1月1日之后的内容
                posts = [p for p in posts if datetime.strptime(p['created_at'], '%a %b %d %H:%M:%S %z %Y') >= target_date]
                if posts:  # 只有在有符合条件的帖子时才添加
                    all_posts.extend(posts)
                break
            
            all_posts.extend(posts)
            page += 1
            time.sleep(2)  # 防止请求过于频繁
        
        # 按时间倒序排序
        all_posts.sort(key=lambda x: datetime.strptime(x['created_at'], '%a %b %d %H:%M:%S %z %Y'), reverse=True)
        
        # 生成并保存Markdown内容
        markdown_content = self.generate_markdown(all_posts)
        self.save_markdown(markdown_content)

if __name__ == '__main__':
    # 使用示例
    cookie_string = input('请输入最新的Cookie字符串：')  # 从用户输入获取最新的Cookie
    scraper = WeiboScraper()
    scraper.run(cookie_string)