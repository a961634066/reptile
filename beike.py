# -*-coding:utf-8 -*-
'''
@Time: 2021/6/21 17:12
@desc: 
'''
import time
import traceback
import urllib2
import random
import sys
import chardet
import xlwt as xlwt

reload(sys)
sys.setdefaultencoding('utf-8')

from bs4 import BeautifulSoup



# Some User Agents
hds = [{'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'},
       {
           'User-Agent': 'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'},
       {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'},
       {
           'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'}]

area_dict = {
    u"yanta": u"雁塔",
    u"xixianxinquxian": u"西咸",
    u"beilin": u"碑林",
    u"weiyang": u"未央",
    u"baqiao": u"灞桥",
    u"xinchengqu": u"新城",
    u"lintong": u"临潼",
    u"changan4": u"长安",
    u"lianhu": u"莲湖",
    u"gaoling1": u"高陵",
    u"lantian": u"蓝田",
    u"huyiqu": u"鄠邑",
    u"zhouzhi": u"周至",
    u"qinduqu": u"秦都"
}

sleep_time = random.random() * 4 if 1 <= random.random() * 4 <= 3 else 1.5


def run(area_list):
    wb = xlwt.Workbook()
    for area in area_list:
        print u"***"*20 + area_dict[area] + u"***"*20
        # 获取每个地区的数据
        data = get_data(area)
        # 写入表格
        write_excel(data, area, wb)
    wb.save(r"D:\123.xls")


def get_data(area):
    data = list()
    page = 1
    while True:
        try:
            url = "https://xa.fang.ke.com/loupan/{0}/pg{1}/#{0}".format(area, page)
            print "爬取地址：%s" % url
            print "当前页：%s" % page
            re = urllib2.Request(url, headers=random.choice(hds))
            response = urllib2.urlopen(re)
            if response.code == 200:
                content = response.read().strip()
                # 有个bug，总页数返回的不对，直接写死，不取页面的
                if area == u"yanta":
                    pages = 23
                elif area == u"weiyang":
                    pages = 18
                else:
                    pages = get_page_numbers(content)
                    pages = 1 if pages == 0 else pages
                # 解析这页的数据
                field_data = parse_html(content, area)
                data.extend(field_data)
                page += 1
                if page > pages:
                    break
            time.sleep(sleep_time)
        except Exception:
            print traceback.format_exc()
            break
    return data


def parse_html(html_str, _area):
    soup = BeautifulSoup(html_str, features="html.parser")
    # 获取页数
    li_list = soup.find("ul", {"class": "resblock-list-wrapper"}).find_all("li", attrs={
        "class": ["resblock-list", "post_ulog_exposure_scroll"]})
    parse_data = []
    name_set = []
    for item in li_list:
        # 在售状态
        status = item.find("span", {"class": "resblock-type"})
        status = status.get_text() if status else "--"
        # 建筑面积
        area = item.find("span", {"class": "area"})
        area = area.get_text() if area else "--"
        # 均价/总价
        avg = item.find("span", {"class": "number"})
        # 价格单位
        util = item.find("span", {"class": "desc"}).get_text() if item.find("span", {"class": "desc"}) else "--"
        total = item.find("div", {"class": "second"})
        # 如果有总价、单价，正常取值
        if avg and total:
            avg = avg.get_text().strip()
            total = total.get_text().strip()
        # 缺少一个时，判断下单位
        else:
            if u"总价" in util:
                total = avg.get_text().strip()
                avg = u"价格待定"
            else:
                avg = avg.get_text().strip()
                total = "--"
        # 小区名称
        name = item.find("a", {"class": "name"}).get_text()
        # 地理位置
        geo = item.find("a", {"class": "resblock-location"}).get_text().strip()
        # 房屋性质
        nature = item.find_all("span")[1].get_text()
        # 小区户型
        house_type = "--"
        for v in item.find_all("span"):
            if u"户型" in v.get_text():
                house_type = item.find_all("span")[3].get_text()
        # 因猜你喜欢会推荐其他区的，根据名称去重
        if area_dict[_area] in geo and name not in name_set:
            parse_data.append([name, status, avg, total, area, geo, nature, house_type])
            name_set.append(name)
    return parse_data
    # print u"小区名称：%s" % name
    # print u"在售状态：%s" % status.get_text() if status else "--"
    # print u"建筑面积：%s" % area.get_text() if area else "--"
    # print u"地理位置：%s" % geo
    # print u"小区均价：%s" % avg
    # print u"小区总价：%s" % total
    # print u"房屋性质：%s" % nature
    # print u"小区户型：%s" % house_type
    # print u"新房顾问：%s" % adviser


def get_page_numbers(html_str):
    soup = BeautifulSoup(html_str, features="html.parser")
    # 获取页数
    pages = soup.find_all("div", {"class": "se-link-container"})[1].find_all("a")[-1].text
    print u"总页数为：%s" % pages
    return int(pages)


def write_excel(data, area, wb):
    # 数据按照均价从低到高排序
    data = sorted(data, key=lambda data:data[2])
    sheet1 = wb.add_sheet(area_dict[str(area)])
    # 格式化宽度
    rafe_width(sheet1)
    title = [u"小区名称", u"在售状态", u"均价（元/m²）", u"总价（万元）", u"建筑面积", u"地理位置", u"房屋性质", u"小区户型"]
    row = 0
    # 写入表头
    for ind, value in enumerate(title):
        sheet1.write(row, ind, value)
    # 写入数据
    for index, va in enumerate(data):
        for i in range(len(va)):
            sheet1.write(row+1, i, va[i])
        row += 1

def rafe_width(sheet):
    sheet.col(0).width = 256 * 20
    sheet.col(2).width = 256 * 14
    sheet.col(3).width = 256 * 20
    sheet.col(4).width = 256 * 17
    sheet.col(5).width = 256 * 62
    sheet.col(7).width = 256 * 13


if __name__ == '__main__':
    print "开始爬取"
    # area_str = "yanta-xixianxinquxian-beilin-weiyang-baqiao-xinchengqu-lintong-yanliang-changan4-lianhu-gaoling1-lantian-huyiqu-zhouzhi-qinduqu"
    # area_list = area_str.split("-")
    area_list = area_dict.keys()
    print area_list
    run(area_list)
    print "爬取完成"
