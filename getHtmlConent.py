import os
import argparse
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import sys
import re
import htmlmin

standard_html_tags = {
    'html', 'head', 'title', 'base', 'link', 'meta', 'style', 'script', 'noscript',
    'body', 'section', 'nav', 'article', 'aside', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'hgroup', 'header', 'footer', 'address', 'p', 'hr', 'pre', 'blockquote', 'ol',
    'ul', 'li', 'dl', 'dt', 'dd', 'figure', 'figcaption', 'main', 'div', 'a', 'em',
    'strong', 'small', 's', 'cite', 'q', 'dfn', 'abbr', 'data', 'time', 'code', 'var',
    'samp', 'kbd', 'sub', 'sup', 'i', 'b', 'u', 'mark', 'ruby', 'rt', 'rp', 'bdi', 'bdo',
    'span', 'br', 'wbr', 'ins', 'del', 'img', 'iframe', 'embed', 'object', 'param',
    'video', 'audio', 'source', 'track', 'canvas', 'map', 'area', 'svg', 'math',
    'table', 'caption', 'colgroup', 'col', 'tbody', 'thead', 'tfoot', 'tr', 'td', 'th',
    'form', 'fieldset', 'legend', 'label', 'input', 'button', 'select', 'datalist',
    'optgroup', 'option', 'textarea', 'output', 'progress', 'meter', 'details',
    'summary', 'menu', 'menuitem', 'applet', 'acronym', 'bgsound', 'dir', 'frame',
    'frameset', 'noframes', 'isindex', 'listing', 'xmp', 'nextid', 'noembed', 'plaintext',
    'rb', 'strike', 'basefont', 'big', 'blink', 'center', 'font', 'marquee', 'multicol',
    'spacer', 'tt', 'frame', 'frameset'
}

html4_tags = {
    'a', 'abbr', 'acronym', 'address', 'applet', 'area', 'b', 'base', 'basefont', 'bdo',
    'big', 'blockquote', 'body', 'br', 'button', 'caption', 'center', 'cite', 'code',
    'col', 'colgroup', 'dd', 'del', 'dfn', 'dir', 'div', 'dl', 'dt', 'em', 'fieldset',
    'font', 'form', 'frame', 'frameset', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'head',
    'hr', 'html', 'i', 'iframe', 'img', 'input', 'ins', 'isindex', 'kbd', 'label', 'legend',
    'li', 'link', 'map', 'menu', 'meta', 'noframes', 'noscript', 'object', 'ol', 'optgroup',
    'option', 'p', 'param', 'pre', 'q', 's', 'samp', 'script', 'select', 'small', 'span',
    'strike', 'strong', 'style', 'sub', 'sup', 'table', 'tbody', 'td', 'textarea', 'tfoot',
    'th', 'thead', 'title', 'tr', 'tt', 'u', 'ul', 'var'
}

standard_html_tags = standard_html_tags.union(html4_tags)

def run(url, save_dir, element_id=None, tag_class=None
    , s_ids=None, s_classes=None):
    # 获取网页内容
    response = requests.get(url)
    response.raise_for_status()  # 确保请求成功

    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)

    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    last_saved_path = None

    # Remove specified IDs
    if s_ids:
        for s_id in s_ids:
            for elem in soup.find_all(id=s_id):
                elem.decompose()

    # Remove specified classes
    if s_classes:
        for s_class in s_classes:
            for elem in soup.find_all(class_=s_class):
                elem.decompose()

    # 查找特定id的元素并处理其下的图片

    # 查找特定class的元素并处理其下的图片
    if tag_class:
        tags = soup.find_all(class_=tag_class)
        for i, tag in enumerate(tags):
            classes = tag.get('class', [])  # 获取element的所有类名称
            if set(classes) == set(tag_class):
                print(f"element_class={tag_class} , classes={classes}")
                last_saved_path = process_tag_images(tag, url, save_dir, 'temp.html')

    print(f"last_saved_path={last_saved_path}")
    with open(last_saved_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # print(f"html_content={html_content}")
    soup = BeautifulSoup(html_content, 'lxml')

    # 寻找具有指定类的元素
    target_element = soup.find(class_=tag_class)

    if target_element:
        handle(target_element)

    # 指定输出文件的路径，输出文件名基于输入文件名
    output_file_path = os.path.join(save_dir, 'index.html')

    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(str(target_element))
    print(f"HTML has been saved to {output_file_path}")
    # os.remove(last_saved_path)
        
def handle(target_element):
    target_element.attrs = {}  # 清除所有其他标签的属性
    # 只在该元素中移除所有script和style标签
    for tag in target_element(["script", "style"]):
        tag.decompose()

    # 删除所有非标准 HTML 标签，并处理 <a> 标签
    for tag in target_element.find_all():
        if tag.name == 'a':
            tag.unwrap()  # 移除 <a> 标签，但保留其内容
        elif tag.name not in standard_html_tags:
            tag.decompose()  # 如果标签不在标准列表中，则删除

    # 找到所有的 HTML 元素并清除属性
    for tag in target_element.find_all():
        if tag.name == 'img':
            continue
        else:
            tag.attrs = {}  # 清除所有其他标签的属性

    # remove_empty_tags(target_element)

    # 删除文本中的嵌套标签
    for tag in target_element.find_all():
        if tag.name == 'pre':
            continue
        if not tag.string:
            if tag.find() and tag.text:  # 检查标签是否含有子标签和文本
                    direct_text = "".join(tag.find_all(text=True, recursive=False)).strip()
                    if direct_text:  # 确保直接包含的文本非空
                        clean_and_set_class(tag)
        else:
            clean_and_set_class(tag)

def clean_and_set_class(tag):
    text = tag.get_text(strip=True)
    cleaned_text = re.sub(r'\s+', ' ', text).strip()
    tag.clear()
    tag.append(cleaned_text)

def process_tag_images(element, base_url, save_dir, file_name):
    local_images = element.find_all('img')
    for img in local_images:
        original_src = img['src']
        src_url = urljoin(base_url, original_src)
        file_name_img = os.path.basename(src_url)
        local_path = file_name_img  # Only use the image file name
        img['src'] = local_path  # Modify src to local path
        img.attrs = {'src': local_path}  # 重新设置标签属性，仅保留src

        save_image(src_url, os.path.join(save_dir, local_path))  # Separate function to download images

    html_file_path = os.path.join(save_dir, file_name)
    with open(html_file_path, 'w', encoding='utf-8') as file:
        print(f"html_file_path = {html_file_path}")
        file.write(str(element))

    return html_file_path

def save_image(src_url, local_path):
    try:
        response = requests.get(src_url, stream=True)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved image {src_url} to {local_path}")
    except Exception as e:
        print(f"Failed to save image from {src_url} to {local_path}: {e}")

def remove_empty_tags(soup):
    for tag in soup.find_all():
        if tag.name == 'img':
            continue
        text = tag.get_text(strip=True)
        if len(text) == 0 and not text.find('<img>'):
            tag.decompose()
        if not tag.contents or all(isinstance(c, str) and not c.strip() for c in tag.contents):
            # 移除只包含空字符串或无实质内容的标签
            tag.decompose()
        else:
            # 递归检查当前标签的子标签
            remove_empty_tags(tag)

def minify_html(html):
    return htmlmin.minify(html, remove_empty_space=True, remove_all_empty_space=True, remove_comments=True, keep_pre=True)

def main():
    parser = argparse.ArgumentParser(description="Download and clean specific elements from a webpage")
    parser.add_argument('url', type=str, help="URL of the webpage")
    parser.add_argument('save_dir', type=str, help="Directory to save the content")
    parser.add_argument('--element_id', type=str, help="ID of the HTML element to save")
    parser.add_argument('--element_class', nargs='*', help="Class of the HTML elements to save")
    parser.add_argument('--s_id', nargs='*', help="IDs of the HTML elements to remove")
    parser.add_argument('--s_class', nargs='*', help="Classes of the HTML elements to remove")
    args = parser.parse_args()

    run(
        args.url, args.save_dir, args.element_id, args.element_class, args.s_id, args.s_class
    )

if __name__ == "__main__":
    main()
