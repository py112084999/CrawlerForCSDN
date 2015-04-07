#!/usr/bin/env python
#encoding=utf-8

import urllib2  
import urllib
import cookielib  
import re
import time
import json
import requests
import pymongo

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0

class Crawler(object):
    """docstring for Crawler"""
    def __init__(self,username,arg):
        super(Crawler, self).__init__()
        self.arg = arg
        if checkRepeatability(username)==0:
        	Info=startMyClawler(username)


    def startMyClawler():
        pass

    def sendDataToDB():
        pass

    def getTaskFromQueue():
        pass

    def showUserInfo():
    	pass

    def checkRepeatability():
    	pass


    
    

def startMyClawler(username):  
      
    
    try:  
        
        #通过username得到用户相关页面url
        
        user_blog_url="http://blog.csdn.net/"+str(username)
        user_profile_url="http://my.csdn.net/"+str(username)
        #user_article_url_with_pagenumber="http://blog.csdn.net/"+str(username)+"/article/list/"+pagenumber

        #通过url获取页面的soup
        user_blog_soup=url2soup(user_blog_url)
        user_profile_soup=url2soup(user_profile_url)
        #user+article_page_soup=url2soup(user_article_url_with_pagenumber)

        #博客主页信息
        

        html_data_blog_rank=user_blog_soup.find('ul',id='blog_rank')
        html_data_blog_rank_in_str=str(html_data_blog_rank)
        if html_data_blog_rank:
            print 'html_data_blog_rank got,begin to get rank data...'
            visitCount=getVisitCount(html_data_blog_rank_in_str)
            score=getScore(html_data_blog_rank_in_str)
            rank=getRank(html_data_blog_rank_in_str)
            
        else:
            print 'failed to get html_data_blog_rank '

        #博客统计信息
        html_data_blog_statistics=user_blog_soup.find('ul',id='blog_statistics')
        html_data_blog_statistics_in_str=str(html_data_blog_statistics)
        if html_data_blog_statistics:
            print 'html_data_blog_statistics got,begin to get statistics data...'
            originalPost=getOriginalPost(html_data_blog_statistics_in_str)
            forwardPost=getForwardPost(html_data_blog_statistics_in_str)
            translatePost=getTranslatePost(html_data_blog_statistics_in_str)
            comment=getComment(html_data_blog_statistics_in_str)
        else:
            print 'failed to get html_data_blog_statistics'


        html_data_article_category=user_blog_soup.find('div',id='panel_Category')
        html_data_article_category_in_str=str(html_data_article_category)
        if html_data_article_category:
            print 'html_data_article_category got,begin to get category data...'
            getCategory(html_data_article_category_in_str)
        else:
            print 'failed to get html_data_article_category'
       # print soup.find(id={'panel_Category'}
        #个人资料页面信息

        skill,education,workExp,contact=getDynamicLoadedInfo(username)
        


        

        result={'username':username,'personInfo':{'skill':skill,'edu':education,'workExp':workExp,'contact':contact},'blogInfo':{'visit':visitCount,'score':score,'rank':rank,'originalPost':originalPost,'forwardPost':forwardPost,'translatePost':translatePost,'comment':comment},'areticleTags':None}
        print result

       
       

    except Exception,e:  
        print str(e)

    finally:
        print 'final...Crawler end'


def url2soup(url,dynamic=False):    
    """这个函数输入url返回它的soup,可选参数dynamic判断是否为动态页面
    并默认设置为否，若url为动态网页，则等待某个元素加载完毕后再获取
    html源码并转换成soup并返回""" 
    
    try:
        if dynamic==False:
            print 'open '+url+' with dynamic==False...'

            cj = cookielib.CookieJar()

            opener=urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

            opener.addheaders = [('User-agent','Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')]

            op=opener.open(url)

            soup=BeautifulSoup(op.read())

        elif dynamic==True:
        	
            '''这个分支中将打开一个FireFox浏览器页面来读取信息，通过判断元素eduid的出现来判断页面加载完毕，
            由于这个元素的确定是根据测试页面实际加载的情况选定的，所以将来需要添加更通用的判断页面加载完毕的方法。'''

            print url+' is dynamic web..wait for it to load and return soup of the page..'

            driver=webdriver.Firefox()

            driver.get(url)

            element=WebDriverWait(driver,10).until(EC.presence_of_element_located((By.XPATH,"//div[@eduid]")))

            soup=BeautifulSoup(driver.page_source)

            driver.quit()
        
    except Exception,e:
        print str(e)

    finally:
    	return soup
        print 'url2soup end'
        

def getUserInfoWithTypeOfJson(username,method):
    '''这个函数模拟jQuery+Ajax的方式向服务器请求数据，返回json格式数据
       使用Request框架,参考www.python-requests.org
       username即用户名
       method分别为getSkill，getContact,getEduExp,getWorkExp
       服务器返回格式为{"err":err,"msg":msg,"result":result}
       正常返回信息时为{"err":0,"msg":"ok","result":[]}
       注意：jQuery+Ajax会将data转换成url编码格式进行传送
       不设置User-Agent则会被403，Content-Type必须设置为'application/x-www-form-urlencoded',否则返回err:1
       '''
    headers={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36','Content-Type':'application/x-www-form-urlencoded'}

    payload='params=%7B%22username%22%3A%22'+username+'%22%2C%22method%22%3A%22'+method+'%22%7D'

    r=requests.post('http://my.csdn.net/service/main/uc',data=payload,headers=headers)

    data=r.json()
    return data['result']

def getDynamicLoadedInfo(username,enableSeleniumMode=False):
    '''获取用户信息中动态加载的部分，可选项可以手动选择是否启用selenium强行获取页面，
    这是一个备用手段，使用selenium会真实打开一个Firefox浏览器页面并获取soup来读取信息'''

    if enableSeleniumMode==False:
        
        
        skill=getUserInfoWithTypeOfJson(username,'getSkill')
        contact=getUserInfoWithTypeOfJson(username,'getContact')
        education=getUserInfoWithTypeOfJson(username,'getEduExp')
        workExp=getUserInfoWithTypeOfJson(username,'getWorkExp')
        return (skill,education,workExp,contact)

    elif enableSeleniumMode==True:

        user_profile_soup=url2soup(user_profile_url,dynamic=True)

        field=user_profile_soup.find("div","field")
        field_list=field.find_all("div","tag")
        print 'field found:'
        for everyfield in field_list:
            print removeTag(soup2str(everyfield.span))
        skill=user_profile_soup.find("div","skill")
        skill_list=skill.find_all("div","tag")
        print 'skill found:'
        for everyskill in skill_list:
            print removeTag(soup2str(everyskill.span))

        education=user_profile_soup.find("div","person_education")
        print 'education info found:'
        major=education.div.dl.dt.span
        print 'major: ',removeTag(soup2str(major))
        university=education.div.dl.dd.span
        print 'university: ',removeTag(soup2str(university))
        degree=education.div.dl.dd.b
        print 'degree: ',removeTag(soup2str(degree))

        workExp=user_profile_soup.find("div","person_job")

        contact=user_profile_soup.find("div","mod_contact")
        email=contact.find("span","email")
        mobile=contact.find("span","modile")
        qq=contact.find("span","qq")
        weixin=contact.find("span","weixin")
        print 'email: ',removeTag(soup2str(email))
        print 'mobile: ',removeTag(soup2str(mobile))
        print 'qq: ',removeTag(soup2str(qq))
        print 'weixin: ',removeTag(soup2str(weixin))



def getVisitCount(str):
    blog_visit_count=re.compile(r'(?<=<li>访问：<span>)\d+(?=次</span></li>)').search(str)
    if blog_visit_count:
        print 'visit count got'
        return blog_visit_count.group()
    else:
        print 'failed to get visit count'


def getScore(str):
    blog_score=re.compile(r'(?<=<li>积分：<span>)\d+(?=</span> </li>)').search(str)
    if blog_score:
        print 'score got'
        return blog_score.group()
    else:
        print 'failed to get score'

def getRank(str):
    blog_rank=re.compile(r'(?<=<li>排名：<span>第)\d+(?=名</span></li>)').search(str)
    if blog_rank:
        print 'rank got'
        return blog_rank.group()
    else:
        print 'failed to get score'
    
def getOriginalPost(str):
    blog_original_post=re.compile(r'(?<=<li>原创：<span>)\d+(?=篇</span></li>)').search(str)
    if blog_original_post:
        print 'original post got'
        return blog_original_post.group()
    else:
        print 'failed to get original post'

def getForwardPost(str):
    blog_forward_post=re.compile(r'(?<=<li>转载：<span>)\d+(?=篇</span></li>)').search(str)
    if blog_forward_post:
        print 'blog forward post got'
        return blog_forward_post.group()
    else:
        print 'failed to get forward post'

def getTranslatePost(str):
    blog_translate_post=re.compile(r'(?<=<li>译文：<span>)\d+(?=篇</span></li>)').search(str)
    if blog_translate_post:
        print 'blog translate post got'
        return blog_translate_post.group()
    else:
        print 'failed to get translate post'

def getComment(str):
    blog_comment=re.compile(r'(?<=<li>评论：<span>)\d+(?=条</span></li>)').search(str)
    if blog_comment:
        print 'comment got'
        return blog_comment.group()
    else:
        print 'failed to get comment'

def getCategory(str):
    pass



def soup2str(input):
    return str(input)

    
def removeTag(input):
    result=re.compile(r'(?<=>).+(?=</)').search(input)
    if result:
        
        return result.group()
    else:
        return False


startMyClawler("arui319")  

#test

